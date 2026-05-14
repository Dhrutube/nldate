"""Tests for nldate.parse()."""

from __future__ import annotations

from datetime import date

import pytest

from nldate import ParseError, parse

# A fixed reference date so tests are deterministic.
REF = date(2025, 6, 11)  # A Wednesday


class TestKeywords:
    def test_today(self) -> None:
        assert parse("today", today=REF) == REF

    def test_tomorrow(self) -> None:
        assert parse("tomorrow", today=REF) == date(2025, 6, 12)

    def test_yesterday(self) -> None:
        assert parse("yesterday", today=REF) == date(2025, 6, 10)


class TestRelative:
    def test_in_n_days(self) -> None:
        assert parse("in 5 days", today=REF) == date(2025, 6, 16)

    def test_n_days_ago(self) -> None:
        assert parse("3 days ago", today=REF) == date(2025, 6, 8)

    def test_in_2_weeks(self) -> None:
        assert parse("in 2 weeks", today=REF) == date(2025, 6, 25)

    def test_1_month_ago(self) -> None:
        assert parse("1 month ago", today=REF) == date(2025, 5, 11)

    def test_in_1_year(self) -> None:
        assert parse("in 1 year", today=REF) == date(2026, 6, 11)


class TestBeforeAfter:
    def test_5_days_before(self) -> None:
        assert parse("5 days before December 1st, 2025", today=REF) == date(
            2025, 11, 26
        )

    def test_2_weeks_after(self) -> None:
        assert parse("2 weeks after January 1, 2026", today=REF) == date(
            2026, 1, 15
        )

    def test_1_month_before(self) -> None:
        assert parse("1 month before March 31, 2025", today=REF) == date(
            2025, 2, 28
        )


class TestNextLastWeekday:
    def test_next_tuesday(self) -> None:
        # REF is Wednesday → next Tuesday is 6 days later
        assert parse("next Tuesday", today=REF) == date(2025, 6, 17)

    def test_last_friday(self) -> None:
        # REF is Wednesday → last Friday is 5 days earlier
        assert parse("last Friday", today=REF) == date(2025, 6, 6)

    def test_next_wednesday(self) -> None:
        # "next Wednesday" when today is Wednesday → 7 days later
        assert parse("next Wednesday", today=REF) == date(2025, 6, 18)

    def test_this_monday(self) -> None:
        # "this Monday" when today is Wednesday → 2 days ago (same week)
        assert parse("this Monday", today=REF) == date(2025, 6, 9)


class TestAbsolute:
    def test_month_day_year(self) -> None:
        assert parse("December 1, 2025") == date(2025, 12, 1)

    def test_month_day_no_year(self) -> None:
        assert parse("June 15", today=REF) == date(2025, 6, 15)

    def test_iso_format(self) -> None:
        assert parse("2025-12-01") == date(2025, 12, 1)

    def test_us_slash(self) -> None:
        assert parse("12/01/2025") == date(2025, 12, 1)

    def test_day_month_year(self) -> None:
        assert parse("1 December 2025") == date(2025, 12, 1)

    def test_ordinal_suffix(self) -> None:
        assert parse("January 3rd, 2025") == date(2025, 1, 3)

    def test_abbreviated_month(self) -> None:
        assert parse("Feb 14, 2025") == date(2025, 2, 14)


class TestEdgeCases:
    def test_extra_whitespace(self) -> None:
        assert parse("  in   3   days  ", today=REF) == date(2025, 6, 14)

    def test_mixed_case(self) -> None:
        assert parse("NEXT tuesday", today=REF) == date(2025, 6, 17)

    def test_unparseable_raises(self) -> None:
        with pytest.raises(ParseError):
            parse("not a date at all", today=REF)

    def test_today_defaults_to_real_today(self) -> None:
        result = parse("today")
        assert result == date.today()
