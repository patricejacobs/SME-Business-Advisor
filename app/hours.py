"""Guyana working-hours logic.

Open Monday-Saturday, WORKING_HOURS_START to WORKING_HOURS_END. Closed all
day Sunday. All times are America/Guyana (fixed UTC-4, no daylight saving).
"""

from datetime import date, datetime, time, timedelta
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


def working_hours_open_between(start: datetime, end: datetime) -> bool:
    """True if the working-hours window was open at any point in (start, end].

    Used to decide whether an off-hours conversation "session" has expired -
    if hours opened and closed again since we last messaged this client,
    the next off-hours contact should be treated as a fresh session.
    """
    if start >= end:
        return False
    day: date = start.date()
    last_day = end.date()
    while day <= last_day:
        if day.weekday() != SUNDAY:
            open_dt = datetime.combine(day, time(config.WORKING_HOURS_START, 0), tzinfo=TZ)
            close_dt = datetime.combine(day, time(config.WORKING_HOURS_END, 0), tzinfo=TZ)
            if open_dt < end and close_dt > start:
                return True
        day += timedelta(days=1)
    return False


def _fmt_hour(hour: int) -> str:
    suffix = "AM" if hour < 12 else "PM"
    hour12 = hour % 12 or 12
    return f"{hour12}:00 {suffix}"


def working_hours_text() -> str:
    return f"Monday to Saturday, {_fmt_hour(config.WORKING_HOURS_START)} to {_fmt_hour(config.WORKING_HOURS_END)}"


def time_of_day_greeting() -> str:
    """A closing wish, appropriate to the current Guyana time."""
    hour = now_guyana().hour
    if 12 <= hour < 17:
        return "Have a good afternoon!"
    if 17 <= hour < 21:
        return "Have a good evening!"
    return "Have a good rest of your day!"
