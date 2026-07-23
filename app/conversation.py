"""The state machine.

One row in `clients` per phone number. `clients.state` holds the key of the
question we are currently waiting on, a lifecycle marker ('complete'), or one
of the identity-check states below. Because state lives in the database and
not in memory, a client can walk away mid-intake and pick up days later, and
the service can restart without losing anyone.
"""

import logging
from datetime import datetime

from . import config, db, hours, llm, logs, questions
from .questions import BY_KEY

log = logging.getLogger(__name__)

STATE_COMPLETE = "complete"
STATE_CONFIRMING_IDENTITY = "confirming_identity"
STATE_CONFIRMING_NAME_UPDATE = "confirming_name_update"
STATE_COLLECTING_NEW_NAME = "collecting_new_name"

_IDENTITY_STATES = (STATE_CONFIRMING_IDENTITY, STATE_CONFIRMING_NAME_UPDATE, STATE_COLLECTING_NEW_NAME)


def handle(phone: str, body: str) -> list[str]:
    """Process one inbound message. Returns the messages to send back, in order."""
    text = body.strip()
    client = db.get_client(phone)

    # --- first contact ---------------------------------------------------
    if client is None:
        db.create_client(phone, state=questions.first_question().key)
        db.update_client(phone, last_seen_at=db.now())
        return [llm.opening_message()]

    if not text:
        return []

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
        result = _handle_followup(client, text)

    # --- mid-intake --------------------------------------------------------
    else:
        result = _handle_question(client, text)

    db.update_client(phone, last_seen_at=db.now())
    return result


def _should_confirm_identity(client) -> bool:
    """True if this client has a name on file and hasn't been seen in a while."""
    last_seen_raw = client["last_seen_at"]
    if not last_seen_raw:
        return False
    last_seen = datetime.fromisoformat(last_seen_raw)
    now = datetime.fromisoformat(db.now())
    gap_hours = (now - last_seen).total_seconds() / 3600
    return gap_hours >= config.IDENTITY_CHECK_GAP_HOURS


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


def _handle_question(client, text: str) -> list[str]:
    """Mid-intake: interpret the reply to whatever question this client is on."""
    phone = client["phone"]
    question = BY_KEY.get(client["state"])
    if question is None:
        # State got corrupted somehow. Restart rather than dead-end the client.
        log.error("Unknown state %r for %s - restarting intake", client["state"], phone)
        db.update_client(phone, state=questions.first_question().key)
        return [llm.opening_message()]

    next_q = questions.next_question(question.key)

    if client["pending_confirmation"]:
        # Last turn wasn't confident and asked the client to confirm a guess -
        # this reply (even a bare "yes") resolves that, not the original question.
        turn = llm.resolve_confirmation(
            question, client["pending_confirmation"], text, next_q, client["name"]
        )
        db.update_client(phone, pending_confirmation=None)
    else:
        turn = llm.take_turn(question, text, next_q, client["name"])

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

    next_q = questions.next_question(question.key)
    turn = llm.take_turn_from_image(question, image_bytes, mime_type, caption, next_q, client["name"])
    raw_answer = caption or "(photo of a handwritten/typed answer)"
    return _apply_turn(client, question, next_q, turn, raw_answer=raw_answer)


def _apply_turn(client, question, next_q, turn, raw_answer: str) -> list[str]:
    """Shared by text and image answers: save the result and advance state."""
    phone = client["phone"]

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


def handle_off_hours(phone: str) -> list[str]:
    """Process one inbound message received outside working hours.

    Deliberately does not touch intake state (question/answers) - a message
    received off-hours is not treated as an answer to whatever question the
    client was last on. First off-hours contact in a session: ask if they can
    reach out during hours. Their reply to that (whatever it is): a polite
    time-appropriate close. Anything further in that same off-hours session:
    silence. A new off-hours session (one where working hours opened and
    closed again in between) resets back to asking.

    Every off-hours contact is logged (phone number and name, if known) to
    the off_hours_contacts table for callback follow-up.
    """
    client = db.get_client(phone)
    if client is None:
        client = db.create_client(phone, state=questions.first_question().key)

    db.log_off_hours_contact(phone, client["name"])

    stage = client["off_hours_stage"] or "none"
    stage_at_raw = client["off_hours_stage_at"]

    if stage != "none" and stage_at_raw:
        stage_at = datetime.fromisoformat(stage_at_raw)
        if hours.working_hours_open_between(stage_at, hours.now_guyana()):
            stage = "none"

    if stage == "none":
        db.update_client(
            phone, off_hours_stage="asked", off_hours_stage_at=hours.now_guyana().isoformat()
        )
        return [
            f"Hello! Our working hours are {hours.working_hours_text()} (Guyana time), "
            "and we're closed right now. Would it be possible for you to reach out again "
            "during that time?"
        ]

    if stage == "asked":
        db.update_client(
            phone, off_hours_stage="closed", off_hours_stage_at=hours.now_guyana().isoformat()
        )
        return [hours.time_of_day_greeting()]

    # stage == "closed" - already asked and closed out this session, stay silent.
    return []


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
    return [llm.closing_message(refreshed["plan_title"], has_skipped_questions=has_skipped)]


def _handle_followup(client, text: str) -> list[str]:
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

    return [
        "Thank you - I have added that to your file. "
        "Our advisor will see it when they contact you."
    ]
