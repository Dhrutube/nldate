"""Core parsing logic for natural-language date expressions."""

from __future__ import annotations

import calendar
import re
from datetime import date, timedelta

_MONTHS: dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

_WEEKDAYS: dict[str, int] = {
    "monday": 0, "mon": 0,
    "tuesday": 1, "tue": 1, "tues": 1,
    "wednesday": 2, "wed": 2,
    "thursday": 3, "thu": 3, "thur": 3, "thurs": 3,
    "friday": 4, "fri": 4,
    "saturday": 5, "sat": 5,
    "sunday": 6, "sun": 6,
}

_ORDINAL_RE = re.compile(r"(\d+)(?:st|nd|rd|th)")

_UNITS: dict[str, str] = {
    "day": "days", "days": "days",
    "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months",
    "year": "years", "years": "years",
}


class ParseError(ValueError):
    """Raised when a date string cannot be parsed."""


def _month_number(name: str) -> int:
    key = name.lower().rstrip(".")
    if key in _MONTHS:
        return _MONTHS[key]
    raise ParseError(f"Unknown month: {name!r}")


def _weekday_number(name: str) -> int:
    key = name.lower().rstrip(".")
    if key in _WEEKDAYS:
        return _WEEKDAYS[key]
    raise ParseError(f"Unknown weekday: {name!r}")


def _add_months(d: date, months: int) -> date:
    """Add (or subtract) *months* months to *d*, clamping the day."""
    total = (d.year * 12 + d.month - 1) + months
    y, m = divmod(total, 12)
    m += 1
    max_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, max_day))


def _strip_ordinal(s: str) -> str:
    """Replace '1st', '2nd', etc. with plain digits."""
    return _ORDINAL_RE.sub(r"\1", s)


# ---------------------------------------------------------------------------
# Individual pattern matchers – each returns a date or None.
# ---------------------------------------------------------------------------


def _try_keyword(s: str, ref: date) -> date | None:
    """Handle 'today', 'tomorrow', 'yesterday'."""
    if s == "today":
        return ref
    if s == "tomorrow":
        return ref + timedelta(days=1)
    if s == "yesterday":
        return ref - timedelta(days=1)
    return None


_REL_FUTURE = re.compile(
    r"^in\s+(\d+)\s+(day|days|week|weeks|month|months|year|years)$"
)
_REL_PAST = re.compile(
    r"^(\d+)\s+(day|days|week|weeks|month|months|year|years)\s+ago$"
)


def _try_relative(s: str, ref: date) -> date | None:
    """Handle 'in 5 days', '3 weeks ago', etc."""
    m = _REL_FUTURE.match(s)
    if m:
        n, unit = int(m.group(1)), _UNITS[m.group(2)]
        return _apply_delta(ref, n, unit)

    m = _REL_PAST.match(s)
    if m:
        n, unit = int(m.group(1)), _UNITS[m.group(2)]
        return _apply_delta(ref, -n, unit)

    return None


def _apply_delta(ref: date, n: int, unit: str) -> date:
    if unit == "days":
        return ref + timedelta(days=n)
    if unit == "weeks":
        return ref + timedelta(weeks=n)
    if unit == "months":
        return _add_months(ref, n)
    if unit == "years":
        return _add_months(ref, n * 12)
    raise ParseError(f"Unknown unit: {unit!r}")  # pragma: no cover


_BEFORE_AFTER = re.compile(
    r"^(\d+)\s+(day|days|week|weeks|month|months|year|years)"
    r"\s+(before|after)\s+(.+)$"
)


def _try_before_after(s: str, ref: date) -> date | None:
    """Handle '5 days before December 1st, 2025'."""
    m = _BEFORE_AFTER.match(s)
    if not m:
        return None
    n = int(m.group(1))
    unit = _UNITS[m.group(2)]
    direction = -1 if m.group(3) == "before" else 1
    anchor = _parse_absolute(m.group(4).strip(), ref)
    return _apply_delta(anchor, direction * n, unit)


_NEXT_LAST_WD = re.compile(r"^(next|last|this)\s+(\w+)$")


def _try_next_last_weekday(s: str, ref: date) -> date | None:
    """Handle 'next Tuesday', 'last Friday', 'this Monday'."""
    m = _NEXT_LAST_WD.match(s)
    if not m:
        return None
    modifier = m.group(1)
    try:
        target_wd = _weekday_number(m.group(2))
    except ParseError:
        return None

    current_wd = ref.weekday()

    if modifier == "next":
        diff = (target_wd - current_wd) % 7
        if diff == 0:
            diff = 7
        return ref + timedelta(days=diff)

    if modifier == "last":
        diff = (current_wd - target_wd) % 7
        if diff == 0:
            diff = 7
        return ref - timedelta(days=diff)

    # "this" – the occurrence within the current week (Mon-Sun)
    diff = target_wd - current_wd
    return ref + timedelta(days=diff)


# ---------------------------------------------------------------------------
# Absolute date parsing (used standalone and as anchor for before/after)
# ---------------------------------------------------------------------------

# "December 1, 2025" / "Dec 1st, 2025" / "December 1 2025" / "December 1"
_MONTH_DAY_YEAR = re.compile(
    r"^(\w+)\s+(\d+)\s*,?\s*(\d{4})?$"
)

# "1 December 2025" / "1st December 2025"
_DAY_MONTH_YEAR = re.compile(
    r"^(\d+)\s+(\w+)\s*,?\s*(\d{4})?$"
)

# ISO-style: "2025-12-01"
_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")

# US-style: "12/01/2025" or "12/1/2025"
_US_SLASH = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")


def _parse_absolute(s: str, ref: date) -> date:
    """Parse an absolute date string, raising ParseError on failure."""
    s = _strip_ordinal(s).strip()

    m = _ISO.match(s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))

    m = _US_SLASH.match(s)
    if m:
        return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))

    m = _MONTH_DAY_YEAR.match(s)
    if m:
        month = _month_number(m.group(1))
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else ref.year
        return date(year, month, day)

    m = _DAY_MONTH_YEAR.match(s)
    if m:
        day = int(m.group(1))
        month = _month_number(m.group(2))
        year = int(m.group(3)) if m.group(3) else ref.year
        return date(year, month, day)

    raise ParseError(f"Cannot parse date: {s!r}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(s: str, today: date | None = None) -> date:
    """Parse a natural-language date string and return a `datetime.date`.

    Parameters
    ----------
    s:
        The date expression to parse.
    today:
        Reference date for relative expressions.  Defaults to the real
        current date.

    Raises
    ------
    ParseError
        If the string cannot be understood.
    """
    ref = today if today is not None else date.today()
    normalized = " ".join(s.strip().lower().split())

    # Try each pattern in order of specificity.
    for handler in (
        _try_keyword,
        _try_relative,
        _try_before_after,
        _try_next_last_weekday,
    ):
        result = handler(normalized, ref)
        if result is not None:
            return result

    # Fall through to absolute parsing.
    return _parse_absolute(normalized, ref)
