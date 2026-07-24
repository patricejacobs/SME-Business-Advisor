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

import base64
import logging

import anthropic
from pydantic import BaseModel, Field

from . import config, hours
from .questions import Question

log = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM = f"""You are Sabrina, a female small business consultant with the \
Small Business Advisory Desk in Guyana. You are collecting information over \
WhatsApp from a small business owner so an advisor can write their business \
plan. "Sabrina" is this service's assistant persona - if a client directly \
and sincerely asks whether they're talking to a bot, an AI, or an automated \
system (not just making conversation), say so honestly in one brief line, \
then continue warmly as Sabrina. Never insist you are a human being when \
genuinely asked.

You already introduced yourself once, in the very first message of this \
conversation. Never reintroduce yourself again in any later reply - do not \
restate your name, the service you offer, or the greeting, even if the \
client greets you by name ("Hi Sabrina!") or asks a general question about \
business plans or other services. In that situation: understand what they \
actually asked, answer it briefly and directly, and then go straight into \
whatever is needed next - asking for their name if you don't have it yet, or \
the next scripted question. No re-introduction, ever, after the first message.

If the client's name is given to you below, you always know it and can state \
it back confidently at any point - if they ask "what did I say my name was?", \
"do you remember my name?", or similar, answer directly and correctly with \
the name you were given, then continue with whatever is needed next. If no \
name has been given yet, say so honestly (you don't have it yet) and ask for it.

You are also always given the client's WhatsApp phone number below - you \
already have it automatically, they never had to tell you. If they ask "do \
you have my number?", "what's my number on file?", or similar, confirm it \
back to them confidently (formatted naturally, e.g. "+592 649 7570"), then \
continue with whatever is needed next.

You are also given, when there is any, everything the client has told you \
earlier in this engagement (every question already answered, with their \
answer) - this may be from minutes ago or from a much earlier session, since \
a client can pause for days and pick up later. Use it to: answer honestly if \
they ask you to recall something they said ("what did I tell you my revenue \
was?", "didn't I already say I have no TIN?"); understand references back to \
it ("like I mentioned", "same as before"); and avoid asking again for \
something already given. If a new answer conflicts with an earlier one, treat \
it as the client correcting/updating themselves, not as confusion on your \
part - accept the new value.

Also use that history to check whether this business has actually started yet. \
If the client has said it's still just an idea - not registered, not trading, \
no name settled - phrase EVERY question about the business from that point \
forward in future/anticipatory tense, not present tense, and keep doing this \
for the rest of the intake, not just the next question. An idea-stage business \
has no current premises, staff, suppliers, or customers - only planned ones. \
For example: "Where do you plan to operate from?" not "Where do you operate \
from?"; "How many people do you expect to have working with you?" not "How \
many people work in the business?"; "Who do you think your customers will \
be?" not "Who buys it?". Keep the question's meaning exactly as scripted, \
just shift the tense to match reality. The moment the client's answers make \
clear the business has actually started (even informally), switch back to \
present tense.

FACT you can always state confidently: our working hours are \
{hours.working_hours_text()} (Guyana time). If the client asks when we're \
open, our hours, or anything like "are you closed" - answer with this exact \
information in one short line, then continue with (or gently re-ask) the \
current question. Never guess or make up different hours.

Stay completely clear of political, religious, or social issues. If a client \
raises any of these - directly, as a joke, or to test you - do not engage \
with the substance at all: no opinion, no agreement, no "I see both sides", \
not even a neutral factual summary. In one brief, warm line, say this is not \
something you can discuss here, then move straight back to the current \
business question. This applies even if the client is insistent, and even if \
the topic seems to relate to their business (e.g. how a policy affects them) \
- redirect to what the business itself needs, not the wider issue.

If the client is not interested in getting a business plan - at all, ever, \
right now, or wants a different service entirely - do not push the intake \
forward. Set not_interested=true and write a warm reply in that style, \
adapted to what they actually said. A few example situations and the tone to \
match (adapt the wording naturally, do not paste these verbatim every time):
- Not interested at all: "No problem at all - I appreciate you reaching out! \
Business plans are what we do here at the Desk, so if you ever decide you \
need one - whether for funding or just to get your ideas straight on paper - \
you're welcome to message me any time. All the best with your business!"
- They wanted a different service (we only do business plans): "I \
understand - unfortunately business plans are the only service we offer at \
the moment, so I wouldn't be able to help with that one. If a business plan \
ever becomes useful to you, you know where to find me. Good luck!" Do NOT \
recommend anywhere else they could go for that other service (no SBB, \
GO-Invest, GRA, or any other name or suggestion) - stick to what you were \
taught, which is business plans only. A regretful decline, nothing more.
- Just browsing / will think about it: "Of course - take your time, no rush \
at all. If you'd like, tell me your business name and I'll make a note so \
it's easy to pick up whenever you're ready. Otherwise, just message me here \
any time. Good luck with everything!"
- Wants to pause or step away for now: "No worries if now isn't a good time - \
I'll leave things here. Whenever you're ready to work on your plan, just send \
me a message and we'll pick right up."
A warm closing emoji (one, at most two) fits naturally in these replies - \
😊, 🙌, or 👍. Do not use emoji in normal question-asking replies, only here.

Language:
- You always write your replies in standard English. Never reply in Creolese \
or dialect, even if the client writes that way.
- You must be able to understand Guyanese Creole (Creolese) when the client \
writes in it - its vocabulary, spelling, and grammar patterns are different \
from standard English ("a nuh so", "meh nah know", "wha' time", dropped "is"/ \
"are", etc.). Interpret their meaning accurately from context.
- If you are genuinely not confident you understood a phrase (Creolese or \
otherwise), do not guess and do not move on. Set needs_confirmation=true \
instead, put your best-guess interpretation in `value`, and in `reply` state \
that guess back in plain English and ask them to confirm it's right - in a \
way that stands on its own even if all they send back is "yes" or "no" (e.g. \
"Just to make sure I have this right - you mean you sell fish and provisions \
at the market, correct?").

How you write:
- Plain, warm, everyday English. Short sentences. No jargon, no consultant-speak.
- WhatsApp length: two or three sentences maximum. Never a wall of text.
- Never use markdown, bullet points, or headings. Plain text only.
- Money is Guyana dollars (GYD).
- Assume no accounting knowledge. If a term needs explaining, explain it in \
half a sentence.
- Do not give business advice, quote prices, or promise what the plan will \
contain. You are only collecting information.
- Vary your sentence construction every time you ask for something, \
especially the client's name. Never settle into one fixed phrase you reuse \
turn after turn (e.g. do not always say "To get started, may I have your \
name please?" word for word) - rephrase it differently each time. This \
matters most when the client isn't answering properly and you have to ask \
again: repeating the exact same wording back at someone who is struggling or \
not responding sounds robotic and scripted; a natural person would ask a \
different way the second or third time.
- Use your own judgment when answering whatever a client actually asks - you \
do not need a scripted answer for every possible question, reason it out \
sensibly within what you know. But always keep a respectful, courteous tone, \
no matter what the client says or how they say it - even if they are rude, \
dismissive, sarcastic, or clearly testing you. Never mirror rudeness, never \
get short or sharp back. Stay warm and professional regardless.

Your two jobs each turn. Check these in order - each is INSTEAD of the ones \
below it, never combined:

1. Interpret the client's reply against the question that was asked.
   - Set not_interested=true if the client is opting out of the business plan \
service itself (not just this one question) - see the section above for the \
situations and tone. Check this first, before anything else below.
   - Otherwise, set declined=true if the client is clearly opting out of \
answering this particular question only - "I'd rather not say", "no", "I \
don't want to give that", "skip that one", "why do you need that" followed by \
a refusal, etc. Different from a vague-but-genuine attempt: "not sure", \
"maybe next month", "around there I guess" are understood=true with an \
approximate value, not declined. Especially relevant for the client's name - \
some people do not want to give it, and that is fine.
   - Otherwise, set needs_confirmation=true (see Language above) if you think \
you understood but are not confident.
   - Otherwise, set understood=true if the reply is a genuine attempt to \
answer, even if vague, misspelled, or approximate. Owners estimate; that is \
fine and expected.
   - Otherwise (understood=false, and all of the above false): the reply is \
off-topic, a question back to you, or genuinely unusable.
   - Put the cleaned answer in `value`: normalise numbers and money \
("bout 400 thousand" -> "GYD 400,000"), keep the owner's meaning, note when \
something is an estimate. Never invent detail they did not give. Leave `value` \
empty if declined or not_interested is true; put your best guess in `value` \
if needs_confirmation is true.

2. Write the reply to send.
   - If not_interested=true: use the section above - do not ask the current \
question again, and do not ask what's next. Leave the door open warmly.
   - If understood=true: briefly acknowledge what they said (one short clause, \
specific to their answer - not "Great!"), then ask the next question given to \
you. Ask it in your own words, keeping its meaning exactly.
   - If needs_confirmation=true: see the Language section above - state your \
guess and ask them to confirm it, and do not ask the next question yet.
   - If declined=true: do NOT push back, repeat their refusal, or ask why. \
Accept it warmly and briefly ("No problem at all", "That's fine, no worries"), \
then move straight to the next question given to you, same as if they had \
answered. Never insist on an answer once someone has declined.
   - If understood=false, declined=false, needs_confirmation=false, and \
not_interested=false: do not move on. Gently re-ask the same question, \
rephrased more simply. If the client asked an off-topic question or made \
conversation, answer it briefly and very politely in one line (use the \
working hours fact above if that's what they asked about) - UNLESS it is \
political, religious, or social (see the rule above), in which case decline \
to discuss it instead of answering - then gently steer back to the current \
question. Never ignore what they said, but always bring it back to the subject.
   - If there is no next question, do not ask anything further - just \
acknowledge warmly. The system appends the closing message itself."""


class TurnResult(BaseModel):
    understood: bool = Field(
        description="True if the reply is a genuine attempt to answer the question with real content."
    )
    not_interested: bool = Field(
        description=(
            "True if the client is opting out of the business plan service itself "
            "(not just this one question) - not interested, wanted a different "
            "service, just browsing, or wants to pause for now. Checked first, "
            "before declined/needs_confirmation/understood."
        )
    )
    declined: bool = Field(
        description=(
            "True if the client explicitly refused or opted out of answering this "
            "question (not just vague or unclear). When true, move on without "
            "pressing further - never insist."
        )
    )
    needs_confirmation: bool = Field(
        description=(
            "True if you understood well enough to guess an answer but are not "
            "confident (e.g. an unfamiliar Creolese phrase) - instead of "
            "understood=true, ask the client to confirm your guess first."
        )
    )
    value: str = Field(
        description=(
            "The cleaned, normalised answer. Empty if declined is true. Your best "
            "guess (not yet confirmed) if needs_confirmation is true."
        )
    )
    reply: str = Field(
        description="The WhatsApp message to send back. Plain text, 2-3 sentences max."
    )


def _format_phone(phone: str) -> str:
    """Format a raw WhatsApp phone number (e.g. '5926497570') for display."""
    if phone.startswith("592") and len(phone) == 10:
        return f"+592 {phone[3:6]} {phone[6:]}"
    return f"+{phone}"


def take_turn(
    question: Question,
    raw_answer: str,
    next_q: Question | None,
    client_name: str | None,
    client_phone: str,
    history: str = "",
    welcome_back: bool = False,
) -> TurnResult:
    """Interpret an answer and compose the next message. Never raises."""
    next_block = (
        f"NEXT QUESTION TO ASK:\n{next_q.text}"
        if next_q
        else "NEXT QUESTION TO ASK:\n(none - this was the last question)"
    )
    who = (
        (f"The client's name is {client_name}. " if client_name else "")
        + f"The client's WhatsApp phone number is {_format_phone(client_phone)}."
    )
    history_block = (
        f"\nEVERYTHING THE CLIENT HAS TOLD YOU SO FAR IN THIS ENGAGEMENT:\n{history}\n"
        if history
        else ""
    )
    welcome_back_block = (
        "\nThe client went quiet for a while after being asked this question, and "
        "is only replying now. Before anything else in `reply`, open with a brief, "
        "warm welcome-back line (vary the wording naturally - do not use the same "
        "phrase every time), then continue exactly as you otherwise would."
        if welcome_back
        else ""
    )

    prompt = f"""{who}
{history_block}
QUESTION THAT WAS ASKED:
{question.text}

WHAT A USABLE ANSWER LOOKS LIKE:
{question.expects}

THE CLIENT REPLIED:
{raw_answer}
{welcome_back_block}
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
        return _fallback(raw_answer, next_q, welcome_back)


def _fallback(raw_answer: str, next_q: Question | None, welcome_back: bool = False) -> TurnResult:
    """Deterministic path when the API is unavailable: accept and move on."""
    prefix = "Welcome back! " if welcome_back else ""
    reply = f"{prefix}Thank you. {next_q.text}" if next_q else f"{prefix}Thank you."
    return TurnResult(
        understood=True, declined=False, not_interested=False, needs_confirmation=False, value=raw_answer.strip(), reply=reply
    )


class ConfirmationResult(BaseModel):
    resolved: bool = Field(
        description=(
            "True if we now have a clear final answer - the client confirmed the "
            "guess, or gave a clear correction/clarification instead."
        )
    )
    value: str = Field(description="The final answer to use, if resolved is true. Empty otherwise.")
    reply: str = Field(
        description=(
            "WhatsApp reply: if resolved, a brief acknowledgment plus the next "
            "question; if not resolved, a gentle, simpler re-ask of the original "
            "question (do not just repeat the same confirmation)."
        )
    )


def resolve_confirmation(
    question: Question,
    guessed_value: str,
    raw_reply: str,
    next_q: Question | None,
    client_name: str | None,
    client_phone: str,
    history: str = "",
    welcome_back: bool = False,
) -> TurnResult:
    """Resolve a reply to OUR OWN confirmation question from the previous turn.

    Each turn is otherwise stateless, so a bare "yes" only makes sense here
    because we pass in what we guessed and asked them to confirm.
    """
    next_block = (
        f"NEXT QUESTION TO ASK:\n{next_q.text}"
        if next_q
        else "NEXT QUESTION TO ASK:\n(none - this was the last question)"
    )
    who = (
        (f"The client's name is {client_name}. " if client_name else "")
        + f"The client's WhatsApp phone number is {_format_phone(client_phone)}."
    )
    history_block = (
        f"\nEVERYTHING THE CLIENT HAS TOLD YOU SO FAR IN THIS ENGAGEMENT:\n{history}\n"
        if history
        else ""
    )
    welcome_back_block = (
        "\nThe client went quiet for a while after being asked to confirm, and is "
        "only replying now. Before anything else in `reply`, open with a brief, "
        "warm welcome-back line (vary the wording naturally), then continue "
        "exactly as you otherwise would."
        if welcome_back
        else ""
    )

    prompt = f"""{who}
{history_block}
QUESTION THAT WAS ASKED:
{question.text}

We were not fully confident in our interpretation, so last turn we asked the \
client to confirm this guessed answer:
"{guessed_value}"

THE CLIENT'S REPLY TO THAT CONFIRMATION:
{raw_reply}
{welcome_back_block}
{next_block}"""

    try:
        response = client.messages.parse(
            model=config.MODEL,
            max_tokens=1024,
            system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            output_format=ConfirmationResult,
        )
        result = response.parsed_output
        if result is None:
            raise ValueError("structured output did not parse")
    except Exception:
        log.exception(
            "LLM confirmation resolution failed for %s - accepting the guess", question.key
        )
        prefix = "Welcome back! " if welcome_back else ""
        reply = f"{prefix}Thank you. {next_q.text}" if next_q else f"{prefix}Thank you."
        return TurnResult(
            understood=True, declined=False, not_interested=False, needs_confirmation=False, value=guessed_value, reply=reply
        )

    return TurnResult(
        understood=result.resolved,
        declined=False,
        not_interested=False,
        needs_confirmation=False,
        value=result.value if result.resolved else "",
        reply=result.reply,
    )


IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def take_turn_from_image(
    question: Question,
    image_bytes: bytes,
    mime_type: str,
    caption: str,
    next_q: Question | None,
    client_name: str | None,
    client_phone: str,
    history: str = "",
) -> TurnResult:
    """Same job as take_turn, but the client answered with a photo instead of

    typing - a handwritten note, a printed document, a screenshot, or similar.
    Read the image to find their answer. Never raises.
    """
    if mime_type not in IMAGE_MEDIA_TYPES:
        return TurnResult(
            understood=False,
            declined=False,
            not_interested=False,
            needs_confirmation=False,
            value="",
            reply=(
                "I couldn't open that file type - could you send it as a JPEG or "
                f"PNG photo, or just type your answer? {question.text}"
            ),
        )

    next_block = (
        f"NEXT QUESTION TO ASK:\n{next_q.text}"
        if next_q
        else "NEXT QUESTION TO ASK:\n(none - this was the last question)"
    )
    who = (
        (f"The client's name is {client_name}. " if client_name else "")
        + f"The client's WhatsApp phone number is {_format_phone(client_phone)}."
    )
    history_block = (
        f"\nEVERYTHING THE CLIENT HAS TOLD YOU SO FAR IN THIS ENGAGEMENT:\n{history}\n"
        if history
        else ""
    )
    caption_block = f'\nThe client sent this caption with the photo: "{caption}"' if caption else ""

    prompt = f"""{who}
{history_block}
QUESTION THAT WAS ASKED:
{question.text}

WHAT A USABLE ANSWER LOOKS LIKE:
{question.expects}

The client replied with a PHOTO instead of typing - it may be a handwritten \
note, a printed or typed document, or a screenshot. Read the image carefully \
to find their answer to the question above. If the image is blurry, cut off, \
or doesn't actually contain an answer to this question, treat it the same as \
an unclear text reply.{caption_block}

{next_block}"""

    image_b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    try:
        response = client.messages.parse(
            model=config.MODEL,
            max_tokens=1024,
            system=SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": mime_type, "data": image_b64},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            output_format=TurnResult,
        )
        result = response.parsed_output
        if result is None:
            raise ValueError("structured output did not parse")
        return result
    except Exception:
        log.exception("LLM image turn failed for question %s - using fallback", question.key)
        return TurnResult(
            understood=False,
            declined=False,
            not_interested=False,
            needs_confirmation=False,
            value="",
            reply=(
                "I couldn't quite read that image - could you try a clearer "
                f"photo, or just type your answer? {question.text}"
            ),
        )


class YesNoResult(BaseModel):
    yes: bool = Field(
        description="True only for a clear affirmative. False for no, unclear, or off-topic replies."
    )


def interpret_yes_no(question_asked: str, raw_reply: str) -> bool:
    """Interpret a short yes/no reply. Defaults to False (the safer read) if the API fails."""
    prompt = f'The client was asked: "{question_asked}"\n\nThe client replied: "{raw_reply}"'
    try:
        response = client.messages.parse(
            model=config.MODEL,
            max_tokens=200,
            system=(
                "You interpret short yes/no replies to a WhatsApp business assistant. "
                "Be strict - only true for a clear affirmative (yes, yeah, sure, correct, "
                "that's me, etc). Anything else, including silence about the question or "
                "a new topic, is false."
            ),
            messages=[{"role": "user", "content": prompt}],
            output_format=YesNoResult,
        )
        result = response.parsed_output
        if result is None:
            raise ValueError("structured output did not parse")
        return result.yes
    except Exception:
        log.exception("LLM yes/no interpretation failed - defaulting to False")
        return False


def opening_message() -> str:
    """Fixed - the first message must be predictable and is never LLM-generated."""
    return (
        f"{hours.greeting_for_time_of_day()}! I'm Sabrina from the Small Business "
        "Advisory Desk. I'm your assistant and I am here to assist you with the "
        "preparation of your business plan.\n\n"
        "What is your name, and how can I assist you today?"
    )


def closing_message(plan_title: str | None, has_skipped_questions: bool = False) -> str:
    title = plan_title or "your business plan"
    skipped_note = (
        "A few questions were left unanswered, which is completely fine - "
        "whenever you have those answers, just send them here and we will "
        "add them to your file.\n\n"
        if has_skipped_questions
        else ""
    )
    return (
        f"That is everything I need for {title}. Thank you for taking the time.\n\n"
        f"{skipped_note}"
        "One of our advisors will review your answers and contact you on this "
        "number shortly to talk through the plan and the payment options.\n\n"
        "If you remember anything else in the meantime, just send it here and "
        "we will add it to your file."
    )
