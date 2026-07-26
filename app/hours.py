"""Guyana office-hours logic - when a *human* advisor is available.

Monday-Saturday, WORKING_HOURS_START to WORKING_HOURS_END; closed all day
Sunday. All times are America/Guyana (fixed UTC-4, no daylight saving).

This is separate from the bot's own availability: the bot (see shifts.py)
now runs continuously, every day, across three rotating 8-hour shifts. This
module's `is_within_working_hours()` no longer gates the conversation - it
only governs the off-hours callback log and the "an advisor will be in touch
during office hours" note on a completed intake.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from . import config

TZ = ZoneInfo(config.TIMEZONE)

SUNDAY = 6


def now_guyana() -> datetime:
    return datetime.now(TZ)


def _is_open_at(dt: datetime) -> bool:
    if dt.weekday() == SUNDAY:
        return False
    return config.WORKING_HOURS_START <= dt.hour < config.WORKING_HOURS_END


def is_within_working_hours() -> bool:
    return _is_open_at(now_guyana())


def _fmt_hour(hour: int) -> str:
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:00 {suffix}"


def working_hours_text() -> str:
    return f"Monday to Saturday, {_fmt_hour(config.WORKING_HOURS_START)} to {_fmt_hour(config.WORKING_HOURS_END)}"


def greeting_for_time_of_day() -> str:
    """A simple opening greeting for the current Guyana time - used to open a
    fresh conversation. Now reachable at any hour (the bot runs 24/7 across
    three shifts, see shifts.py), so the deep-night hours need their own
    case - "Good morning" at 2am would be a giveaway that nobody is minding
    the clock."""
    hour = now_guyana().hour
    if hour < 5:
        return "Good evening"
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"
