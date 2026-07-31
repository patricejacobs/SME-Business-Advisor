"""The state machine.

One row in `clients` per phone number, holding identity only (name, phone,
last-seen bookkeeping). A client can have many `engagements` over time - one
per business plan - so a completed client asking for a second, different
plan gets a fresh engagement instead of colliding with the first one's
answers. `engagements.state` holds the key of the question that engagement is
currently waiting on, or 'complete'. Because everything lives in the
database and not in memory, a client can walk away mid-intake and pick up
days later, and the service can restart without losing anyone.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

from . import config, db, hours, llm, logs, questions, shifts, whatsapp
from .questions import BY_KEY

log = logging.getLogger(__name__)

STATE_COMPLETE = "complete"
STATE_NORMAL = "normal"
STATE_CONFIRMING_IDENTITY = "confirming_identity"
STATE_CONFIRMING_NAME_UPDATE = "confirming_name_update"
STATE_COLLECTING_NEW_NAME = "collecting_new_name"
STATE_CONFIRMING_SERVICE_CONTACT = "confirming_service_contact"
STATE_CONFIRMING_RESUME_PLAN = "confirming_resume_plan"
STATE_PLAN_PAUSED = "plan_paused"

_IDENTITY_STATES = (STATE_CONFIRMING_IDENTITY, STATE_CONFIRMING_NAME_UPDATE, STATE_COLLECTING_NEW_NAME)

# Every state with its own dedicated text-only sub-conversation (a yes/no
# question, a name to type, a welcome-back trigger) - none of these can be
# meaningfully answered with a photo, so handle_image() falls back to asking
# for text instead of misreading the image as an attempted answer to
# whatever business-plan question the engagement happens to be sitting on.
_TEXT_ONLY_STATES = _IDENTITY_STATES + (
    STATE_CONFIRMING_SERVICE_CONTACT,
    STATE_CONFIRMING_RESUME_PLAN,
    STATE_PLAN_PAUSED,
)

_RESUME_PLAN_QUESTION = "Would you like to continue with your business plan?"


def handle(phone: str, body: str) -> list[str]:
    """Process one inbound message. Returns the messages to send back, in order.

    The bot itself runs continuously, every day, across three rotating 8-hour
    shifts (see shifts.py) - there is no "closed" state. Office hours
    (hours.py) still exist, but only govern when a *human* advisor is
    available; a message outside that window is still fully processed here,
    just also logged for the advisor's callback list.
    """
    text = body.strip()
    client = db.get_client(phone)

    if not hours.is_within_working_hours():
        db.log_off_hours_contact(phone, client["name"] if client else None)

    # --- first contact ---------------------------------------------------
    if client is None:
        persona = shifts.current_persona()
        client = db.create_client(phone)
        db.create_engagement(client["id"], state=questions.first_question().key)
        db.update_client(phone, last_seen_at=db.now(), last_persona=persona)
        return [llm.opening_message(persona)]

    if not text:
        return []

    persona, handover = _resolve_persona(phone, client)

    # --- resolving an identity-check sub-conversation, if one is active --
    if client["state"] == STATE_CONFIRMING_IDENTITY:
        result = _handle_identity_confirmation(client, text)
    elif client["state"] == STATE_CONFIRMING_NAME_UPDATE:
        result = _handle_name_update_confirmation(client, text)
    elif client["state"] == STATE_COLLECTING_NEW_NAME:
        result = _handle_new_name(client, text)

    # --- resolving the other-service consent sub-conversation, if active --
    elif client["state"] == STATE_CONFIRMING_SERVICE_CONTACT:
        result = _handle_service_contact_confirmation(client, text)
    elif client["state"] == STATE_CONFIRMING_RESUME_PLAN:
        result = _handle_resume_plan_confirmation(client, text)
    elif client["state"] == STATE_PLAN_PAUSED:
        result = _handle_plan_paused_return(client, text)

    # --- returning after a gap: confirm identity before continuing -------
    elif client["name"] and _should_confirm_identity(client):
        db.update_client(phone, state=STATE_CONFIRMING_IDENTITY)
        result = [f"Welcome back! Just to confirm - is this still {client['name']}?"]

    # --- normal conversation: route to this client's active engagement ---
    else:
        engagement = db.get_active_engagement(client["id"])
        if engagement is None:
            # Shouldn't happen (every client gets one on creation) - recover safely.
            engagement = db.create_engagement(client["id"], state=questions.first_question().key)

        if engagement["state"] == STATE_COMPLETE:
            result = _handle_followup(client, engagement, text, persona, handover)
        else:
            result = _handle_question(client, engagement, text, persona, handover)

    db.update_client(phone, last_seen_at=db.now())
    return result


def _resolve_persona(phone: str, client) -> tuple[str, str | None]:
    """The persona on shift right now, and the prior persona if it just

    changed since this client's last message - for a one-time handover
    mention. Persists the new value immediately so the handover is only
    announced once, regardless of what the calling branch does with it.
    """
    persona = shifts.current_persona()
    prior_persona = client["last_persona"]
    handover = prior_persona if prior_persona and prior_persona != persona else None
    db.update_client(phone, last_persona=persona)
    return persona, handover


def _should_confirm_identity(client) -> bool:
    """True if this client has a name on file and hasn't been seen in a while."""
    last_seen_raw = client["last_seen_at"]
    if not last_seen_raw:
        return False
    last_seen = datetime.fromisoformat(last_seen_raw)
    now = datetime.fromisoformat(db.now())
    gap_hours = (now - last_seen).total_seconds() / 3600
    return gap_hours >= config.IDENTITY_CHECK_GAP_HOURS


def _should_welcome_back(client) -> bool:
    """True if this client went quiet mid-question for a while and is now replying.

    Independent of _should_confirm_identity (a much longer gap, with its own
    welcome-back framing) - this is the short-gap case: business as usual,
    just acknowledge the pause before resuming.
    """
    last_seen_raw = client["last_seen_at"]
    if not last_seen_raw:
        return False
    last_seen = datetime.fromisoformat(last_seen_raw)
    now = datetime.fromisoformat(db.now())
    gap_minutes = (now - last_seen).total_seconds() / 60
    return gap_minutes >= config.WELCOME_BACK_GAP_MINUTES


def _resume_prompt(client_id: int) -> list[str]:
    """After resolving identity, remind the client what we were waiting on -

    read straight from the active engagement's own current state, which the
    identity-check side-conversation never touches, so there's nothing to
    separately stash and restore.
    """
    engagement = db.get_active_engagement(client_id)
    if engagement is None or engagement["state"] == STATE_COMPLETE:
        return []
    question = BY_KEY.get(engagement["state"])
    return [question.text] if question else []


def _handle_identity_confirmation(client, text: str) -> list[str]:
    phone = client["phone"]
    confirmed = llm.interpret_yes_no(f"Is this still {client['name']}?", text)

    if confirmed:
        db.update_client(phone, state=STATE_NORMAL)
        return [f"Great, thanks {client['name']}!"] + _resume_prompt(client["id"])

    db.update_client(phone, state=STATE_CONFIRMING_NAME_UPDATE)
    return ["No problem - would you like me to update our file with your correct name?"]


def _handle_name_update_confirmation(client, text: str) -> list[str]:
    phone = client["phone"]
    wants_update = llm.interpret_yes_no(
        "Would you like me to update our file with your correct name?", text
    )

    if wants_update:
        db.update_client(phone, state=STATE_COLLECTING_NEW_NAME)
        return ["Sure - what's your full name?"]

    db.update_client(phone, state=STATE_NORMAL)
    return ["No problem, we'll leave the file as is."] + _resume_prompt(client["id"])


def _handle_new_name(client, text: str) -> list[str]:
    phone = client["phone"]
    new_name = text.strip()
    db.update_client(phone, name=new_name, state=STATE_NORMAL)
    return [f"Thank you, I've updated our records to {new_name}."] + _resume_prompt(client["id"])


def _handle_service_contact_confirmation(client, text: str) -> list[str]:
    """Resolve the client's yes/no to "would you like a business advisor to

    contact you about that?" - the consent question asked whenever
    other_service_interest was flagged. Only notifies the admin numbers on
    an actual yes; a decline here means the lead is simply not pursued. If
    the interest also interrupted an unanswered business-plan question (see
    _enter_service_contact_confirmation), moves on to ask about resuming it
    next; otherwise goes straight back to normal and shows whatever question
    is next in line, if any.
    """
    phone = client["phone"]
    service = client["pending_service_interest"] or "that"
    wants_contact = llm.interpret_yes_no(
        "Would you like a business advisor to contact you directly to better understand your needs?",
        text,
    )

    if wants_contact:
        _notify_admin_of_service_interest(client, service)
        ack = "Wonderful - a business advisor will be in touch with you directly to discuss that further."
    else:
        ack = "No problem at all - feel free to reach out any time if that changes."

    if client["pending_service_diversion"]:
        db.update_client(
            phone,
            state=STATE_CONFIRMING_RESUME_PLAN,
            pending_service_interest=None,
            pending_service_diversion=0,
        )
        return [ack, _RESUME_PLAN_QUESTION]

    db.update_client(phone, state=STATE_NORMAL, pending_service_interest=None, pending_service_diversion=0)
    return [ack] + _resume_prompt(client["id"])


def _resume_knowledge_answer(text: str) -> list[str]:
    """If this message contains a genuine factual question the Desk's

    reference material can answer, answer it - shared by both handlers
    below so a question never gets silently swallowed by the yes/no dance,
    wherever in the resume flow it happens to land.
    """
    topic = llm.classify_knowledge_topic(text)
    return [llm.answer_from_knowledge_base(topic, text)] if topic != "none" else []


def _handle_resume_plan_confirmation(client, text: str) -> list[str]:
    """Resolve the client's reply to "would you like to continue with your

    business plan?" - only reached when the other-service question genuinely
    interrupted an unanswered scripted question, or after a paused-return
    welcome-back (see _handle_plan_paused_return). Uses a three-way read
    (llm.interpret_resume_intent), NOT a strict yes/no: a client asking a
    question here ("is VAT paid in Guyana?") is not declining to resume, and
    must not be misread as "no" - that was a real bug (a question sent
    "no" straight into paused). Any embedded factual question gets answered
    regardless of which of the three branches fires.

    A clear "no" does NOT drop back to STATE_NORMAL - that would let the
    client's very next message, whatever it happens to say, fall straight
    into the scripted question as if it were an answer, with no re-check
    that they're actually ready now. Instead it pauses in STATE_PLAN_PAUSED,
    so the next message - whenever it comes - triggers a fresh
    welcome-back-and-ready-to-resume check before the intake continues.
    """
    phone = client["phone"]
    knowledge_answer = _resume_knowledge_answer(text)
    intent = llm.interpret_resume_intent(text)

    if intent == "no":
        db.update_client(phone, state=STATE_PLAN_PAUSED)
        return knowledge_answer + ["No problem - whenever you're ready to continue, just message me here."]

    if intent == "unclear":
        # Neither a clear yes nor no - most often a question (now answered
        # above) with no resume decision actually made yet. Stay right here
        # and ask again, rather than guessing either way.
        return knowledge_answer + [_RESUME_PLAN_QUESTION]

    # intent == "yes"
    db.update_client(phone, state=STATE_NORMAL)
    name_part = f", {client['name']}" if client["name"] else ""
    return (
        [f"Great{name_part}! Let's pick up right where we left off."]
        + knowledge_answer
        + _resume_prompt(client["id"])
    )


def _handle_plan_paused_return(client, text: str) -> list[str]:
    """A message from a client since they last said they weren't ready to

    continue their business plan (see _handle_resume_plan_confirmation).
    Whatever they said is not treated as a direct answer to anything - the
    point of STATE_PLAN_PAUSED is exactly to stop that from happening
    silently. But a bare closing acknowledgment ("ok", "will do") to the
    "message me when ready" line they were just given is not itself a
    genuine return either - stay paused and silent for that, rather than
    immediately welcoming them back for a reply that was only ever closing
    the previous exchange. Anything else triggers the welcome-back-and-ask
    cycle; their reply to THAT question is what actually gets interpreted,
    via _handle_resume_plan_confirmation above.

    Also answers any genuine factual question in THIS message (e.g. "How
    much is VAT in Guyana") rather than silently discarding it in favour of
    the generic welcome-back line - that was a real bug too.
    """
    if llm.interpret_bare_acknowledgment(text):
        return []

    knowledge_answer = _resume_knowledge_answer(text)

    db.update_client(client["phone"], state=STATE_CONFIRMING_RESUME_PLAN)
    name_part = f", {client['name']}" if client["name"] else ""
    return knowledge_answer + [f"Welcome back{name_part}! {_RESUME_PLAN_QUESTION}"]


def _format_history(engagement_id: int) -> str:
    """Everything the client has told us so far in THIS engagement, oldest first.

    Passed into every LLM call so it can accurately reference or reuse earlier
    answers - persists across the whole engagement, including if the client
    goes quiet for days and comes back, since it's read straight from the
    answers table rather than kept in memory. Scoped to one engagement, not
    the client overall, so a second business plan starts with a clean slate
    instead of the first plan's answers bleeding into it.
    """
    answered = [row for row in db.get_answers(engagement_id) if row["question_key"] != "additional_notes"]
    if not answered:
        return ""
    lines = [f'- "{row["question_text"]}" -> {row["parsed_value"] or row["raw_answer"]}' for row in answered]
    return "\n".join(lines)


def _handle_question(client, engagement, text: str, persona: str, handover: str | None) -> list[str]:
    """Mid-intake: interpret the reply to whatever question this engagement is on."""
    phone = client["phone"]
    question = BY_KEY.get(engagement["state"])
    if question is None:
        # State got corrupted somehow. Restart this engagement rather than dead-end the client.
        log.error("Unknown engagement state %r for %s - restarting intake", engagement["state"], phone)
        db.update_engagement(engagement["id"], state=questions.first_question().key)
        return [llm.opening_message(persona)]

    next_q = questions.next_question(question.key)
    welcome_back = _should_welcome_back(client)
    history = _format_history(engagement["id"])

    if engagement["pending_confirmation"]:
        # Last turn wasn't confident and asked the client to confirm a guess -
        # this reply (even a bare "yes") resolves that, not the original question.
        turn = llm.resolve_confirmation(
            question, engagement["pending_confirmation"], text, next_q, client["name"], phone,
            history, welcome_back, persona, handover,
        )
        db.update_engagement(engagement["id"], pending_confirmation=None)
    else:
        turn = llm.take_turn(
            question, text, next_q, client["name"], phone, history, welcome_back, persona, handover
        )

    return _apply_turn(client, engagement, question, next_q, turn, raw_answer=text)


def handle_image(phone: str, image_bytes: bytes, mime_type: str, caption: str) -> list[str]:
    """Process one inbound image, as a photo of a handwritten/typed answer.

    Only supported mid-intake, where there is an actual question to read the
    image against. Any other state (identity checks, no active in-progress
    engagement) gets a simple, honest ask for text instead - those flows need
    a real yes/no/name reply, not a document to interpret.
    """
    client = db.get_client(phone)
    ask_for_text = [
        "Thanks for the photo! For this part, could you reply with the answer "
        "as text instead? I'll be able to help you better that way."
    ]

    if client is None or client["state"] in _TEXT_ONLY_STATES:
        return ask_for_text

    engagement = db.get_active_engagement(client["id"])
    if engagement is None or engagement["state"] == STATE_COMPLETE:
        return ask_for_text

    question = BY_KEY.get(engagement["state"])
    if question is None:
        return ask_for_text

    if not hours.is_within_working_hours():
        db.log_off_hours_contact(phone, client["name"])

    persona, handover = _resolve_persona(phone, client)
    next_q = questions.next_question(question.key)
    history = _format_history(engagement["id"])
    turn = llm.take_turn_from_image(
        question, image_bytes, mime_type, caption, next_q, client["name"], phone,
        history, persona, handover,
    )
    raw_answer = caption or "(photo of a handwritten/typed answer)"
    return _apply_turn(client, engagement, question, next_q, turn, raw_answer=raw_answer)


def _stale_engagement_reply(client, engagement) -> list[str]:
    """Log full diagnostic detail and build a graceful recovery reply for a

    write that referenced an engagement no longer valid for this client.
    Re-asks whatever the client's actual current engagement is on, rather
    than leaving them stuck.
    """
    phone = client["phone"]
    fresh = db.get_engagement(engagement["id"])
    active = db.get_active_engagement(client["id"])
    log.error(
        "Stale engagement for %s: turn was computed against engagement %s (state=%r), "
        "but get_engagement=%r and get_active_engagement=%r - recovering with a re-ask "
        "instead of the write that just failed.",
        phone, engagement["id"], engagement["state"],
        dict(fresh) if fresh else None,
        dict(active) if active else None,
    )
    if active is not None:
        question_now = BY_KEY.get(active["state"])
        if question_now is not None:
            return [question_now.text]
    return ["Sorry, let's pick that back up - could you send your last answer again?"]


def _verify_still_active(client, engagement) -> Optional[list[str]]:
    """Cheap pre-check before a write that references engagement["id"] - a

    fast path that catches staleness that already existed before this turn
    started. NOT sufficient on its own: a check-then-act pattern can never
    fully close the window against a write that fails moments later (this
    happened in production - the check passed, and the very next save_answer
    call still hit a FOREIGN KEY violation). The try/except around each
    actual db.save_answer call is what actually guarantees no unhandled
    exception reaches the client; this is just an early exit.
    """
    engagement_id = engagement["id"]
    fresh = db.get_engagement(engagement_id)
    active = db.get_active_engagement(client["id"])
    if fresh is not None and active is not None and active["id"] == engagement_id:
        return None
    return _stale_engagement_reply(client, engagement)


def _notify_admin_of_service_interest(client, service_description: str) -> None:
    """Best-effort lead capture: the client was asked whether they'd like a

    business advisor to contact them about a Desk service other than
    business-plan writing (bookkeeping, licensing/compliance, funding,
    financial projections, growth advice), and said yes - see
    _handle_service_contact_confirmation, the only caller. Never fired on
    detection alone, only on explicit consent. A notification failure here
    must never surface to the client.
    """
    if not config.ADMIN_NOTIFY_PHONE_NUMBERS:
        return
    message = (
        f"Client interested in another service: {service_description}\n"
        f"Client: {client['name'] or '(name not given)'} - +{client['phone']}"
    )
    for admin_phone in config.ADMIN_NOTIFY_PHONE_NUMBERS:
        try:
            whatsapp.send_text(admin_phone, message)
        except Exception:
            log.exception("Failed to send service-interest notification to %s", admin_phone)


def _enter_service_contact_confirmation(client, service: str, diversion: bool) -> list[str]:
    """Pause for the client's consent before ever flagging a lead to a

    business advisor - never assert someone will be contacted without asking
    first (see _handle_service_contact_confirmation for how the answer is
    resolved). `diversion` marks whether this also interrupted an unanswered
    business-plan question, which needs its own resume-consent once this is
    settled (see _handle_resume_plan_confirmation) rather than silently
    dropping back into the intake or silently abandoning it.
    """
    db.update_client(
        client["phone"],
        state=STATE_CONFIRMING_SERVICE_CONTACT,
        pending_service_interest=service,
        pending_service_diversion=1 if diversion else 0,
    )
    return [
        f"Yes, we do help with that here at the Desk - {service}.",
        "Would you like a business advisor to contact you directly to better understand your needs?",
    ]


def _apply_turn(client, engagement, question, next_q, turn, raw_answer: str) -> list[str]:
    """Shared by text and image answers: save the result and advance state."""
    engagement_id = engagement["id"]

    guard = _verify_still_active(client, engagement)
    if guard is not None:
        return guard

    result = _resolve_turn(client, engagement, question, next_q, turn, raw_answer)

    if turn.other_service_interest:
        # Ground truth, not inferred from the turn's flags: did this question
        # actually get answered/declined (state moved on), or is it still
        # exactly where it was before this message? That's the real test for
        # whether a resume-consent step is needed once the service question
        # is settled - see _enter_service_contact_confirmation.
        fresh = db.get_engagement(engagement_id)
        diversion = fresh is not None and fresh["state"] == question.key
        return _enter_service_contact_confirmation(client, turn.other_service_interest, diversion)

    return result


def _resolve_turn(client, engagement, question, next_q, turn, raw_answer: str) -> list[str]:
    """The ordinary per-question save/advance logic - split out from

    _apply_turn so its side effects (saving an answer, advancing engagement
    state, completing the engagement) still happen even on a turn whose
    reply ends up overridden by the other-service consent flow above.
    """
    phone = client["phone"]
    engagement_id = engagement["id"]

    if turn.not_interested:
        # Opting out of the business plan service itself, not just this
        # question - hold position entirely (no saved answer, no state
        # change) so a later message gets a fair shot at the same question.
        return [turn.reply]

    if turn.needs_confirmation:
        # Hold the guess for next turn - even a bare "yes" reply needs it,
        # since each LLM call is otherwise stateless. Do not save an answer or
        # advance state until the client actually confirms.
        db.update_engagement(engagement_id, pending_confirmation=turn.value)
        return [turn.reply]

    # Not understood and not a deliberate decline: hold position and re-ask.
    if not turn.understood and not turn.declined:
        return [turn.reply]

    if turn.declined:
        # Record that the client was asked but chose not to answer - never
        # push further, and never save a refusal as an actual field value
        # (in particular, never as the client's name).
        try:
            db.save_answer(
                engagement_id=engagement_id,
                question_key=question.key,
                question_text=question.text,
                raw_answer=raw_answer,
                parsed_value="(client declined to answer)",
            )
        except sqlite3.IntegrityError:
            return _stale_engagement_reply(client, engagement)
    else:
        try:
            db.save_answer(
                engagement_id=engagement_id,
                question_key=question.key,
                question_text=question.text,
                raw_answer=raw_answer,
                parsed_value=turn.value,
            )
        except sqlite3.IntegrityError:
            return _stale_engagement_reply(client, engagement)

        # client_name lives on the client identity row (shared across every
        # engagement); plan_title is specific to this one engagement.
        if question.key == "client_name":
            db.update_client(phone, name=turn.value or raw_answer)
        elif question.key == "plan_title":
            db.update_engagement(engagement_id, plan_title=turn.value or raw_answer)

    # --- finished --------------------------------------------------------
    if next_q is None:
        return _complete(client, engagement)

    db.update_engagement(engagement_id, state=next_q.key)
    return [turn.reply]


def _complete(client, engagement) -> list[str]:
    engagement_id = engagement["id"]

    has_skipped = any(
        row["parsed_value"] == "(client declined to answer)" for row in db.get_answers(engagement_id)
    )

    # Mark complete BEFORE writing the log, so the log records the completion
    # timestamp rather than showing the engagement as still in progress.
    db.update_engagement(
        engagement_id,
        state=STATE_COMPLETE,
        status="complete",
        completed_at=db.now(),
    )
    log_path = logs.write_log(engagement_id)
    db.update_engagement(engagement_id, log_path=str(log_path))

    refreshed = db.get_engagement(engagement_id)
    assert refreshed is not None

    _notify_admin_of_completion(client, refreshed, has_skipped)

    return [
        llm.closing_message(
            refreshed["plan_title"],
            has_skipped_questions=has_skipped,
            outside_office_hours=not hours.is_within_working_hours(),
        )
    ]


def _notify_admin_of_completion(client, engagement, has_skipped: bool, test: bool = False) -> None:
    """Sends a WhatsApp message to every configured admin number the moment

    an intake completes - reuses the same Meta connection the bot already
    talks to clients on, no separate notification channel needed. Never
    lets a notification failure affect the client's own closing message.
    `test=True` prefixes the message so a manually-triggered resend (see
    /admin/test-notify) is never mistaken for a brand new completion.
    """
    if not config.ADMIN_NOTIFY_PHONE_NUMBERS:
        return

    answered = len(
        [row for row in db.get_answers(engagement["id"]) if row["question_key"] != "additional_notes"]
    )
    total = len(questions.ALL_QUESTIONS)
    skipped_note = " (some questions skipped)" if has_skipped else ""
    prefix = "[TEST NOTIFICATION - resent from an existing completed plan]\n" if test else ""
    message = (
        f"{prefix}"
        f"Business plan intake complete: {engagement['plan_title'] or '(untitled)'}\n"
        f"Client: {client['name'] or '(name not given)'} - +{client['phone']}\n"
        f"{answered}/{total} questions answered{skipped_note}"
    )
    for phone in config.ADMIN_NOTIFY_PHONE_NUMBERS:
        try:
            whatsapp.send_text(phone, message)
        except Exception:
            log.exception("Failed to send admin completion notification to %s", phone)


def _handle_followup(client, engagement, text: str, persona: str, handover: str | None) -> list[str]:
    """This client's active (most recent) engagement is already complete.

    Figure out whether they want to start a genuinely new, separate business
    plan, are updating a DIFFERENT one of their existing plans by name, or
    are just adding a note to the currently active one - these need
    different handling. Conflating the first two is exactly what made the
    bot sound confused ("I already have that on file") when a client tried
    to start a second plan right after finishing their first; conflating the
    second two is what would silently attach one business's update to a
    different business's file for a client running more than one plan.
    """
    service_interest = llm.interpret_other_service_interest(text)
    if service_interest is not None:
        # No business-plan question is in play post-completion, so this is
        # never a "diversion" needing a resume step - straight to the
        # consent question and back to normal once it's answered.
        return _enter_service_contact_confirmation(client, service_interest, diversion=False)

    if llm.interpret_new_plan_intent(text):
        return _start_new_engagement(client, persona)

    target = _resolve_target_engagement(client, engagement, text)

    existing = ""
    for row in db.get_answers(target["id"]):
        if row["question_key"] == "additional_notes":
            existing = row["raw_answer"]
            break

    combined = f"{existing}\n\n---\n\n{text}" if existing else text
    try:
        db.save_answer(
            engagement_id=target["id"],
            question_key="additional_notes",
            question_text="Additional information sent after the intake was completed",
            raw_answer=combined,
            parsed_value=combined,
        )
    except sqlite3.IntegrityError:
        log.error(
            "Failed to save follow-up note for %s against engagement %s - it may no "
            "longer exist.", client["phone"], target["id"],
        )
        return ["Sorry, something went wrong saving that - please try again in a moment."]
    logs.write_log(target["id"])

    history = _format_history(target["id"])
    other_count = len(db.list_engagements(client["id"])) - 1
    reply = llm.acknowledge_followup(
        text, client["name"], client["phone"], history, persona, handover,
        plan_title=target["plan_title"], other_plan_count=other_count,
    )
    return [reply]


def _resolve_target_engagement(client, active_engagement, text: str):
    """Which of this client's plans a follow-up note actually belongs to.

    Defaults to the active (most recent) engagement - the safe, correct
    choice for a client with only one plan, or when the message doesn't
    clearly name a different one. Only redirects when the classifier is
    confident, and only among plans that still genuinely exist for this
    client (re-read fresh, not trusted from a stale list).
    """
    all_engagements = db.list_engagements(client["id"])
    if len(all_engagements) < 2:
        return active_engagement

    titled = [e for e in all_engagements if e["plan_title"]]
    titles = [e["plan_title"] for e in titled]
    matched_title = llm.identify_target_plan(text, titles)
    if matched_title is None:
        return active_engagement

    matched = next((e for e in titled if e["plan_title"] == matched_title), None)
    if matched is None:
        return active_engagement

    fresh = db.get_engagement(matched["id"])
    return fresh if fresh is not None else active_engagement


def _start_new_engagement(client, persona: str) -> list[str]:
    """Give this client (whose most recent plan is already complete) a fresh

    engagement for a new, separate business plan. Name is already known, so
    this skips straight to the plan-title question rather than re-asking who
    they are - the second gate question, not the first.
    """
    first_q = questions.first_question_for_returning_client()
    db.create_engagement(client["id"], state=first_q.key)
    return [llm.new_engagement_message(client["name"], first_q.text)]
