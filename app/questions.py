"""The question script.

Order is load-bearing. GATE runs first and must complete before any business
questions - that is the requirement that we hold name, phone, and plan title
before doing anything else. Phone comes free from WhatsApp metadata.

The wave structure follows references/../.claude/skills/client-intake/SKILL.md
so the resulting log file maps onto the advisory workflow the rest of this
repo already uses.
"""

from dataclasses import dataclass
from typing import Literal, Optional

AnswerKind = Literal["text", "number", "money", "yesno", "duration"]


@dataclass(frozen=True)
class Question:
    key: str
    wave: str
    text: str
    kind: AnswerKind = "text"
    # Shown to the LLM so it can judge whether an answer is usable.
    expects: str = ""


GATE: list[Question] = [
    Question(
        key="client_name",
        wave="Gate",
        text="What is your name?",
        expects="A person's name. Any name is acceptable.",
    ),
    Question(
        key="plan_title",
        wave="Gate",
        text=(
            "What should we title this business plan? "
            "Most people use the business name, for example "
            "'Kaieteur Poultry Farm - Expansion Plan'."
        ),
        expects="A title for a business plan document. Any short phrase works.",
    ),
]

WAVES: list[Question] = [
    # Wave 1 - the business
    Question(
        key="what_you_sell",
        wave="The business",
        text="What exactly do you sell, and who buys it?",
        expects="A description of products or services and the customer type.",
    ),
    Question(
        key="years_trading",
        wave="The business",
        text=(
            "How long have you been trading, and is this full-time or "
            "alongside a job? If you haven't started yet, just say so."
        ),
        kind="duration",
        expects=(
            "A length of time plus full-time/part-time, OR a clear statement that "
            "trading hasn't started yet (this is still an idea)."
        ),
    ),
    # Asked after what_you_sell/years_trading, not before - registration only
    # makes sense once we know whether there is an actual operating business
    # (or even a settled name) to register in the first place. A business
    # that's still just an idea, with no name settled, has nothing to
    # register yet - that is a valid, expected answer here, not a gap.
    Question(
        key="business_registered",
        wave="The business",
        text=(
            "Is the business registered? Let me know if it is a registered "
            "business name, an incorporated company, or not registered yet - "
            "and if it's still just an idea with no name settled, that's fine too."
        ),
        expects=(
            "Registration status: business name, incorporated company, unregistered, "
            "or 'still just an idea, nothing to register yet' - all are valid."
        ),
    ),
    Question(
        key="location",
        wave="The business",
        text="Where do you operate from - Georgetown, another town, a region, or online only?",
        expects="A location in Guyana, or 'online'.",
    ),
    Question(
        key="staff_count",
        wave="The business",
        text=(
            "How many people work in the business? Count yourself and any "
            "family who help without pay."
        ),
        kind="number",
        expects="A count of people. A number, or a phrase like 'just me' (= 1).",
    ),
    Question(
        key="staff_roles",
        wave="The business",
        text=(
            "Does anyone have a specific role - like a manager, or someone "
            "who handles bookings - or does everyone do the same general work?"
        ),
        expects="A description of roles, or 'everyone does the same thing'.",
    ),
    Question(
        key="owner_experience",
        wave="The business",
        text=(
            "What's your background - have you worked in this line of "
            "business before, or done anything relevant before starting?"
        ),
        expects="A description of relevant experience, or 'none' / 'first time'.",
    ),
    Question(
        key="equipment_needed",
        wave="The business",
        text="What equipment or tools do you use, or still need, for the business?",
        expects="A list of equipment/tools, including 'none needed' if applicable.",
    ),
    # Wave 2 - money
    Question(
        key="monthly_revenue",
        wave="Money",
        text=(
            "Roughly how much do you sell in a typical month, in GYD? "
            "An estimate is fine - and tell me your best and worst months if you can."
        ),
        kind="money",
        expects="A monthly sales figure in Guyana dollars. Estimates and ranges are fine.",
    ),
    Question(
        key="cost_of_goods",
        wave="Money",
        text="What does it cost you to buy or make what you sell?",
        kind="money",
        expects="A cost figure or percentage. Estimates are fine.",
    ),
    Question(
        key="fixed_costs",
        wave="Money",
        text=(
            "What do you pay every month whether or not you sell anything - "
            "rent, salaries, electricity, loan payments?"
        ),
        kind="money",
        expects="A list of recurring monthly costs, with amounts if known.",
    ),
    Question(
        key="bank_account",
        wave="Money",
        text="Do you have a business bank account separate from your personal one?",
        kind="yesno",
        expects="Yes or no.",
    ),
    Question(
        key="record_keeping",
        wave="Money",
        text=(
            "Do you keep records of the business? Books, a spreadsheet, "
            "a notebook, or nothing yet - all answers are fine."
        ),
        expects="A description of record-keeping, including 'none'.",
    ),
    Question(
        key="customer_payment_terms",
        wave="Money",
        text="Do customers pay you immediately, or do you have to wait? How long?",
        expects="Payment timing - immediate, or a credit period.",
    ),
    Question(
        key="debts",
        wave="Money",
        text=(
            "Do you owe anyone right now - suppliers, a bank, family, or GRA? "
            "Roughly how much?"
        ),
        expects="Outstanding debts and amounts, or 'none'.",
    ),
    Question(
        key="startup_costs",
        wave="Money",
        text=(
            "If you need money for equipment, renovations, or setting up "
            "something new - not your day-to-day running costs - what would "
            "that cost, roughly, and what's it for?"
        ),
        kind="money",
        expects="A one-time cost figure and what it is for, or 'not applicable'.",
    ),
    Question(
        key="owner_contribution",
        wave="Money",
        text=(
            "Of that, how much could you cover yourself, and how much would "
            "you need to borrow or raise?"
        ),
        kind="money",
        expects="A split between owner's own funds and an amount to borrow/raise, or 'not applicable'.",
    ),
    # Wave 3 - the question behind the question
    Question(
        key="why_now",
        wave="Goals",
        text="What made you decide to get a business plan done now?",
        expects="A reason or trigger for seeking help.",
    ),
    Question(
        key="twelve_month_goal",
        wave="Goals",
        text="What would success look like twelve months from now?",
        expects="A description of goals.",
    ),
    Question(
        key="biggest_worry",
        wave="Goals",
        text="What is the one thing about the business that keeps you up at night?",
        expects="A concern or worry.",
    ),
    # Wave 4 - compliance
    Question(
        key="tin_vat",
        wave="Compliance",
        text="Do you have a TIN? And are you registered for VAT?",
        expects="TIN and VAT registration status.",
    ),
    Question(
        key="gra_returns",
        wave="Compliance",
        text="Are your GRA returns filed and up to date?",
        expects="Filing status, including 'not sure'.",
    ),
    Question(
        key="nis_paye",
        wave="Compliance",
        text=(
            "If you have staff - are they on NIS, and is PAYE being deducted? "
            "If you have no staff, just say so."
        ),
        expects="NIS and PAYE status, or confirmation of no staff.",
    ),
    Question(
        key="licences",
        wave="Compliance",
        text="Do you have a trade licence, and any licences specific to your line of work?",
        expects="Licence status.",
    ),
    # Wave 5 - market and operations
    Question(
        key="competition",
        wave="Market",
        text="Who else does what you do, and why do customers choose you over them?",
        expects="Competitors and a differentiator.",
    ),
    Question(
        key="how_customers_find_you",
        wave="Market",
        text="How do customers find you at the moment?",
        expects="Marketing or discovery channels.",
    ),
    Question(
        key="suppliers",
        wave="Market",
        text=(
            "Where do you buy from - local or imported? "
            "How long does it take to restock?"
        ),
        expects="Supplier locations and lead times.",
    ),
    Question(
        key="what_breaks",
        wave="Market",
        text="In a normal week, what goes wrong most often?",
        expects="Operational problems.",
    ),
    Question(
        key="funding_needed",
        wave="Market",
        text=(
            "Is this plan being used to raise money? "
            "If so, roughly how much and what for?"
        ),
        expects="A funding amount and purpose, or 'no'.",
    ),
    Question(
        key="funding_source",
        wave="Market",
        text=(
            "Last one. If you're looking to borrow, do you have a particular "
            "lender in mind - Small Business Bureau, IPED, a bank, a credit "
            "union - or would you like the plan to suggest options?"
        ),
        expects="A named lender/source, or 'suggest options', or 'not applicable'.",
    ),
]

ALL_QUESTIONS: list[Question] = GATE + WAVES
BY_KEY: dict[str, Question] = {q.key: q for q in ALL_QUESTIONS}


def first_question() -> Question:
    return ALL_QUESTIONS[0]


def next_question(current_key: str) -> Optional[Question]:
    """Returns the question after current_key, or None if the script is finished."""
    keys = [q.key for q in ALL_QUESTIONS]
    try:
        index = keys.index(current_key)
    except ValueError:
        return None
    if index + 1 >= len(ALL_QUESTIONS):
        return None
    return ALL_QUESTIONS[index + 1]


def progress(current_key: str) -> tuple[int, int]:
    """(answered_so_far, total) - used for the progress note in the greeting."""
    keys = [q.key for q in ALL_QUESTIONS]
    try:
        return keys.index(current_key), len(ALL_QUESTIONS)
    except ValueError:
        return 0, len(ALL_QUESTIONS)
