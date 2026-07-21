"""The state machine.

One row in `clients` per phone number. `clients.state` holds the key of the
question we are currently waiting on, or 'complete'. Because state lives in
the database and not in memory, a client can walk away mid-intake and pick up
days later, and the service can restart without losing anyone.
"""

import logging

from . import db, llm, logs, questions
from .questions import BY_KEY

log = logging.getLogger(__name__)

STATE_COMPLETE = "complete"


def handle(phone: str, body: str) -> list[str]:
    """Process one inbound message. Returns the messages to send back, in order."""
    text = body.strip()
    client = db.get_client(phone)

    # --- first contact ---------------------------------------------------
    if client is None:
        db.create_client(phone, state=questions.first_question().key)
        return [llm.opening_message()]

    if not text:
        return []

    # --- already finished ------------------------------------------------
    if client["state"] == STATE_COMPLETE:
        return _handle_followup(client, text)

    # --- mid-intake ------------------------------------------------------
    question = BY_KEY.get(client["state"])
    if question is None:
        # State got corrupted somehow. Restart rather than dead-end the client.
        log.error("Unknown state %r for %s - restarting intake", client["state"], phone)
        db.update_client(phone, state=questions.first_question().key)
        return [llm.opening_message()]

    next_q = questions.next_question(question.key)
    turn = llm.take_turn(question, text, next_q, client["name"])

    # Not understood: hold position and re-ask.
    if not turn.understood:
        return [turn.reply]

    db.save_answer(
        client_id=client["id"],
        question_key=question.key,
        question_text=question.text,
        raw_answer=text,
        parsed_value=turn.value,
    )

    # The two gate fields are promoted onto the client record so administrators
    # can see who this is without opening the answers table.
    if question.key == "client_name":
        db.update_client(phone, name=turn.value or text)
    elif question.key == "plan_title":
        db.update_client(phone, plan_title=turn.value or text)

    # --- finished --------------------------------------------------------
    if next_q is None:
        return _complete(phone)

    db.update_client(phone, state=next_q.key)
    return [turn.reply]


def _complete(phone: str) -> list[str]:
    client = db.get_client(phone)
    assert client is not None

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
    return [llm.closing_message(refreshed["plan_title"])]


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
