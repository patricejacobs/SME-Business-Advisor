"""The state machine.

One row in `clients` per phone number. `clients.state` holds the key of the
question we are currently waiting on, a lifecycle marker ('complete'), or one
of the identity-check states below. Because state lives in the database and
not in memory, a client can walk away mid-intake and pick up days later, and
the service can restart without losing anyone.
"""

import logging
from datetime import datetime

from . import config, db, hours, llm, logs, questions, shifts
from .questions import BY_KEY

log = logging.getLogger(__name__)

STATE_COMPLETE = "complete"
STATE_CONFIRMING_IDENTITY = "confirming_identity"
STATE_CONFIRMING_NAME_UPDATE = "confirming_name_update"
STATE_COLLECTING_NEW_NAME = "collecting_new_name"

_IDENTITY_STATES = (STATE_CONFIRMING_IDENTITY, STATE_CONFIRMING_NAME_UPDATE, STATE_COLLECTING_NEW_NAME)


def handle(phone: str, body: str) -> list[str]:
    """Process one inbound message. Returns the messages to send back, in order.

    The bot itself now runs continuously, every day, across three rotating
    8-hour shifts (see shifts.py) - there is no more "closed" state. Office
    hours (hours.py) still exist, but only govern when a *human* advisor is
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
        db.create_client(phone, state=questions.first_question().key)
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

    # --- returning after a gap: confirm identity before continuing -------
    elif client["name"] and _should_confirm_identity(client):
        db.update_client(phone, state=STATE_CONFIRMING_IDENTITY, pending_state=client["state"])
        result = [f"Welcome back! Just to confirm - is this still {client['name']}?"]

    # --- already finished --------------------------------------------------
    elif client["state"] == STATE_COMPLETE:
        result = _handle_followup(client, text, persona, handover)

    # --- mid-intake --------------------------------------------------------
    else:
        result = _handle_question(client, text, persona, handover)

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


def _resume_prompt(pending_state: str | None) -> list[str]:
    """After resolving identity, remind the client what we were waiting on."""
    if not pending_state or pending_state == STATE_COMPLETE:
        return []
    question = BY_KEY.get(pending_state)
    return [question.text] if question else []


def _handle_identity_confirmation(client, text: str) -> list[str]:
    phone = client["phone"]
    confirmed = llm.interpret_yes_no(f"Is this still {client['name']}?", text)

    if confirmed:
        db.update_client(phone, state=client["pending_state"] or STATE_COMPLETE, pending_state=None)
        return [f"Great, thanks {client['name']}!"] + _resume_prompt(client["pending_state"])

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

    db.update_client(phone, state=client["pending_state"] or STATE_COMPLETE, pending_state=None)
    return ["No problem, we'll leave the file as is."] + _resume_prompt(client["pending_state"])


def _handle_new_name(client, text: str) -> list[str]:
    phone = client["phone"]
    new_name = text.strip()
    db.update_client(
        phone, name=new_name, state=client["pending_state"] or STATE_COMPLETE, pending_state=None
    )
    return [f"Thank you, I've updated our records to {new_name}."] + _resume_prompt(client["pending_state"])


def _format_history(client_id: int) -> str:
    """Everything the client has told us so far in this engagement, oldest first.

    Passed into every LLM call so it can accurately reference or reuse earlier
    answers - persists across the whole engagement, including if the client
    goes quiet for days and comes back, since it's read straight from the
    answers table rather than kept in memory.
    """
    answered = [row for row in db.get_answers(client_id) if row["question_key"] != "additional_notes"]
    if not answered:
        return ""
    lines = [f'- "{row["question_text"]}" -> {row["parsed_value"] or row["raw_answer"]}' for row in answered]
    return "\n".join(lines)


def _handle_question(client, text: str, persona: str, handover: str | None) -> list[str]:
    """Mid-intake: interpret the reply to whatever question this client is on."""
    phone = client["phone"]
    question = BY_KEY.get(client["state"])
    if question is None:
        # State got corrupted somehow. Restart rather than dead-end the client.
        log.error("Unknown state %r for %s - restarting intake", client["state"], phone)
        db.update_client(phone, state=questions.first_question().key)
        return [llm.opening_message(persona)]

    next_q = questions.next_question(question.key)
    welcome_back = _should_welcome_back(client)
    history = _format_history(client["id"])

    if client["pending_confirmation"]:
        # Last turn wasn't confident and asked the client to confirm a guess -
        # this reply (even a bare "yes") resolves that, not the original question.
        turn = llm.resolve_confirmation(
            question, client["pending_confirmation"], text, next_q, client["name"], phone,
            history, welcome_back, persona, handover,
        )
        db.update_client(phone, pending_confirmation=None)
    else:
        turn = llm.take_turn(
            question, text, next_q, client["name"], phone, history, welcome_back, persona, handover
        )

    return _apply_turn(client, question, next_q, turn, raw_answer=text)


def handle_image(phone: str, image_bytes: bytes, mime_type: str, caption: str) -> list[str]:
    """Process one inbound image, as a photo of a handwritten/typed answer.

    Only supported mid-intake, where there is an actual question to read the
    image against. Any other state (gate fields, identity checks, already
    complete) gets a simple, honest ask for text instead - those flows need a
    real yes/no/name reply, not a document to interpret.
    """
    client = db.get_client(phone)
    ask_for_text = [
        "Thanks for the photo! For this part, could you reply with the answer "
        "as text instead? I'll be able to help you better that way."
    ]

    if client is None or client["state"] in (STATE_COMPLETE,) + _IDENTITY_STATES:
        return ask_for_text

    question = BY_KEY.get(client["state"])
    if question is None:
        return ask_for_text

    if not hours.is_within_working_hours():
        db.log_off_hours_contact(phone, client["name"])

    persona, handover = _resolve_persona(phone, client)
    next_q = questions.next_question(question.key)
    history = _format_history(client["id"])
    turn = llm.take_turn_from_image(
        question, image_bytes, mime_type, caption, next_q, client["name"], phone,
        history, persona, handover,
    )
    raw_answer = caption or "(photo of a handwritten/typed answer)"
    return _apply_turn(client, question, next_q, turn, raw_answer=raw_answer)


def _apply_turn(client, question, next_q, turn, raw_answer: str) -> list[str]:
    """Shared by text and image answers: save the result and advance state."""
    phone = client["phone"]

    if turn.not_interested:
        # Opting out of the business plan service itself, not just this
        # question - hold position entirely (no saved answer, no state
        # change) so a later message gets a fair shot at the same question.
        return [turn.reply]

    if turn.needs_confirmation:
        # Hold the guess for next turn - even a bare "yes" reply needs it,
        # since each LLM call is otherwise stateless. Do not save an answer or
        # advance state until the client actually confirms.
        db.update_client(phone, pending_confirmation=turn.value)
        return [turn.reply]

    # Not understood and not a deliberate decline: hold position and re-ask.
    if not turn.understood and not turn.declined:
        return [turn.reply]

    if turn.declined:
        # Record that the client was asked but chose not to answer - never
        # push further, and never save a refusal as an actual field value
        # (in particular, never as the client's name).
        db.save_answer(
            client_id=client["id"],
            question_key=question.key,
            question_text=question.text,
            raw_answer=raw_answer,
            parsed_value="(client declined to answer)",
        )
    else:
        db.save_answer(
            client_id=client["id"],
            question_key=question.key,
            question_text=question.text,
            raw_answer=raw_answer,
            parsed_value=turn.value,
        )

        # The two gate fields are promoted onto the client record so administrators
        # can see who this is without opening the answers table.
        if question.key == "client_name":
            db.update_client(phone, name=turn.value or raw_answer)
        elif question.key == "plan_title":
            db.update_client(phone, plan_title=turn.value or raw_answer)

    # --- finished --------------------------------------------------------
    if next_q is None:
        return _complete(phone)

    db.update_client(phone, state=next_q.key)
    return [turn.reply]


def _complete(phone: str) -> list[str]:
    client = db.get_client(phone)
    assert client is not None

    has_skipped = any(
        row["parsed_value"] == "(client declined to answer)" for row in db.get_answers(client["id"])
    )

    # Mark complete BEFORE writing the log, so the log records the completion
    # timestamp rather than showing the client as still in progress.
    db.update_client(
        phone,
        state=STATE_COMPLETE,
        status="complete",
        completed_at=db.now(),
    )
    log_path = logs.write_log(client["id"])
    db.update_client(phone, log_path=str(log_path))

    refreshed = db.get_client(phone)
    assert refreshed is not None
    return [
        llm.closing_message(
            refreshed["plan_title"],
            has_skipped_questions=has_skipped,
            outside_office_hours=not hours.is_within_working_hours(),
        )
    ]


def _handle_followup(client, text: str, persona: str, handover: str | None) -> list[str]:
    """Anything sent after the intake is done gets appended to the file."""
    existing = ""
    for row in db.get_answers(client["id"]):
        if row["question_key"] == "additional_notes":
            existing = row["raw_answer"]
            break

    combined = f"{existing}\n\n---\n\n{text}" if existing else text
    db.save_answer(
        client_id=client["id"],
        question_key="additional_notes",
        question_text="Additional information sent after the intake was completed",
        raw_answer=combined,
        parsed_value=combined,
    )
    logs.write_log(client["id"])

    history = _format_history(client["id"])
    reply = llm.acknowledge_followup(text, client["name"], client["phone"], history, persona, handover)
    return [reply]
