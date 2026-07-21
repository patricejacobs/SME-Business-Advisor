"""Claude does two jobs per turn, in a single call:

  1. Interpret the client's reply against the question we asked
     ("bout 400 thousand a month" -> "GYD 400,000/month, client's estimate")
  2. Write the outbound WhatsApp message - a short acknowledgement plus the
     next scripted question, in plain Guyanese-friendly English

Combining them keeps it to one API call per inbound message. The question
*sequence* stays under our control in questions.py; Claude only handles
language and interpretation, so every required field still gets filled.

Every call has a deterministic fallback. If the API is down the bot keeps
working - it just sounds like a form instead of a conversation.
"""

import logging

import anthropic
from pydantic import BaseModel, Field

from . import config
from .questions import Question

log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM = """You are the intake assistant for a business advisory service in \
Guyana. You are collecting information over WhatsApp from a small business \
owner so an advisor can write their business plan.

How you write:
- Plain, warm, everyday English. Short sentences. No jargon, no consultant-speak.
- WhatsApp length: two or three sentences maximum. Never a wall of text.
- Never use markdown, bullet points, or headings. Plain text only.
- Money is Guyana dollars (GYD).
- Assume no accounting knowledge. If a term needs explaining, explain it in \
half a sentence.
- Do not give business advice, quote prices, or promise what the plan will \
contain. You are only collecting information.

Your two jobs each turn:

1. Interpret the client's reply against the question that was asked.
   - Set understood=true if the reply is a genuine attempt to answer, even if \
vague, misspelled, or approximate. Owners estimate; that is fine and expected.
   - Set understood=false ONLY if the reply is off-topic, a question back to \
you, or genuinely unusable.
   - Put the cleaned answer in `value`: normalise numbers and money \
("bout 400 thousand" -> "GYD 400,000"), keep the owner's meaning, note when \
something is an estimate. Never invent detail they did not give.

2. Write the reply to send.
   - If understood=true: briefly acknowledge what they said (one short clause, \
specific to their answer - not "Great!"), then ask the next question given to \
you. Ask it in your own words, keeping its meaning exactly.
   - If understood=false: do not move on. Gently re-ask the same question, \
rephrased more simply, or answer their question in one line and then re-ask.
   - If there is no next question, do not ask anything further - just \
acknowledge warmly. The system appends the closing message itself."""


class TurnResult(BaseModel):
    understood: bool = Field(
        description="True if the reply is a genuine attempt to answer the question."
    )
    value: str = Field(
        description="The cleaned, normalised answer. Empty string if understood is false."
    )
    reply: str = Field(
        description="The WhatsApp message to send back. Plain text, 2-3 sentences max."
    )


def take_turn(
    question: Question,
    raw_answer: str,
    next_q: Question | None,
    client_name: str | None,
) -> TurnResult:
    """Interpret an answer and compose the next message. Never raises."""
    next_block = (
        f"NEXT QUESTION TO ASK:\n{next_q.text}"
        if next_q
        else "NEXT QUESTION TO ASK:\n(none - this was the last question)"
    )
    who = f"The client's name is {client_name}." if client_name else ""

    prompt = f"""{who}

QUESTION THAT WAS ASKED:
{question.text}

WHAT A USABLE ANSWER LOOKS LIKE:
{question.expects}

THE CLIENT REPLIED:
{raw_answer}

{next_block}"""

    try:
        response = client.messages.parse(
            model=config.MODEL,
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_format=TurnResult,
        )
        result = response.parsed_output
        if result is None:
            raise ValueError("structured output did not parse")
        return result
    except Exception:
        log.exception("LLM turn failed for question %s - using fallback", question.key)
        return _fallback(raw_answer, next_q)


def _fallback(raw_answer: str, next_q: Question | None) -> TurnResult:
    """Deterministic path when the API is unavailable: accept and move on."""
    reply = f"Thank you. {next_q.text}" if next_q else "Thank you."
    return TurnResult(understood=True, value=raw_answer.strip(), reply=reply)


def opening_message() -> str:
    """Fixed - the first message must be predictable and is never LLM-generated."""
    return (
        "Hello! I help small businesses in Guyana put together a business plan.\n\n"
        "I will ask you some questions about your business - it takes about "
        "15 minutes, and you can reply whenever you have a moment. Your answers "
        "are saved as you go, so you can stop and come back.\n\n"
        "To start: what is your name?"
    )


def closing_message(plan_title: str | None) -> str:
    title = plan_title or "your business plan"
    return (
        f"That is everything I need for {title}. Thank you for taking the time.\n\n"
        "One of our advisors will review your answers and contact you on this "
        "number shortly to talk through the plan and the payment options.\n\n"
        "If you remember anything else in the meantime, just send it here and "
        "we will add it to your file."
    )
