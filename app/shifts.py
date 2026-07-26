"""Three rotating 8-hour shifts, three rotating personas.

The bot now operates continuously, every day of the week - three 8-hour
shifts covering the full 24 hours (07:00-15:00, 15:00-23:00, 23:00-07:00,
Guyana time). A different persona staffs each shift. Across weeks the three
personas rotate through all three shifts on a standard 3-week rotating
roster, so nobody is permanently stuck on one shift and nobody ever works
more than a single 8-hour shift at a time:

    Week 1: Sabrina=Morning  Ken=Afternoon  Louise=Night
    Week 2: Ken=Morning      Louise=Afternoon  Sabrina=Night
    Week 3: Louise=Morning   Sabrina=Afternoon  Ken=Night
    (repeats)

This is entirely separate from "office hours" (hours.py) - the human
advisor's actual working hours, unchanged at Monday-Saturday 8am-5pm. The
bot itself now collects information around the clock; only the advisor
follow-up is bound to office hours.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

from . import hours

PERSONAS = ("Sabrina", "Ken", "Louise")

PERSONA_INFO: dict[str, dict[str, str]] = {
    "Sabrina": {"pronoun": "she", "gender_word": "female", "flavor": "warm and encouraging"},
    "Ken": {"pronoun": "he", "gender_word": "male", "flavor": "plain-spoken and efficient"},
    "Louise": {"pronoun": "she", "gender_word": "female", "flavor": "thorough and detail-oriented"},
}

# (name, start_hour) - each shift is exactly 8 hours; the night shift wraps
# past midnight into the next calendar day.
_SHIFTS = (("Morning", 7), ("Afternoon", 15), ("Night", 23))

# A fixed Monday used only to count how many whole weeks have elapsed, so the
# rotation is deterministic across restarts - not tied to ISO week numbers,
# which behave inconsistently across year boundaries.
_ANCHOR_MONDAY = datetime(2026, 1, 5).date()


@dataclass(frozen=True)
class Shift:
    name: str
    persona: str


def _shift_index_for_hour(hour: int) -> int:
    if 7 <= hour < 15:
        return 0  # Morning
    if 15 <= hour < 23:
        return 1  # Afternoon
    return 2  # Night: 23:00-06:59


def _week_index(dt: datetime) -> int:
    """Which of the 3 rotation weeks `dt` falls in.

    Based on the calendar date's own week, not the shift's start time - so
    the last few hours of a Sunday-night shift that spill past midnight into
    Monday are counted in the new week. A deliberate simplification: the
    rotation is a coarse weekly assignment, not something that needs
    minute-perfect precision around a single midnight crossover.
    """
    monday_this_week = dt.date() - timedelta(days=dt.weekday())
    weeks_elapsed = (monday_this_week - _ANCHOR_MONDAY).days // 7
    return weeks_elapsed % len(PERSONAS)


def current_shift(dt: datetime | None = None) -> Shift:
    dt = dt or hours.now_guyana()
    shift_i = _shift_index_for_hour(dt.hour)
    rotation = _week_index(dt)
    persona = PERSONAS[(shift_i + rotation) % len(PERSONAS)]
    return Shift(name=_SHIFTS[shift_i][0], persona=persona)


def current_persona(dt: datetime | None = None) -> str:
    return current_shift(dt).persona
