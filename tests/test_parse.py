"""Tests for nldate.parse()."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import pytest

from nldate import parse

REF = date.today()


def _add_months(d: date, months: int) -> date:
    """Mirror the library's month arithmetic for expected-value computation."""
    total = (d.year * 12 + d.month - 1) + months
    y, m = divmod(total, 12)
    m += 1
    max_day = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, max_day))


def _next_weekday(ref: date, target_wd: int) -> date:
    diff = (target_wd - ref.weekday()) % 7
    return ref + timedelta(days=diff if diff != 0 else 7)


def _last_weekday(ref: date, target_wd: int) -> date:
    diff = (ref.weekday() - target_wd) % 7
    return ref - timedelta(days=diff if diff != 0 else 7)


class TestKeywords:
    def test_today(self) -> None:
        assert parse("today", today=REF) == REF

    def test_tomorrow(self) -> None:
        assert parse("tomorrow", today=REF) == REF + timedelta(days=1)

    def test_yesterday(self) -> None:
        assert parse("yesterday", today=REF) == REF - timedelta(days=1)

    def test_the_day_after_tomorrow(self) -> None:
        assert parse("the day after tomorrow", today=REF) == REF + timedelta(days=2)

    def test_the_day_before_yesterday(self) -> None:
        assert parse("the day before yesterday", today=REF) == REF - timedelta(days=2)


class TestRelative:
    def test_in_n_days(self) -> None:
        assert parse("in 5 days", today=REF) == REF + timedelta(days=5)

    def test_n_days_ago(self) -> None:
        assert parse("3 days ago", today=REF) == REF - timedelta(days=3)

    def test_in_2_weeks(self) -> None:
        assert parse("in 2 weeks", today=REF) == REF + timedelta(weeks=2)

    def test_1_month_ago(self) -> None:
        assert parse("1 month ago", today=REF) == _add_months(REF, -1)

    def test_in_1_year(self) -> None:
        assert parse("in 1 year", today=REF) == _add_months(REF, 12)

    def test_a_week_ago(self) -> None:
        assert parse("a week ago", today=REF) == REF - timedelta(weeks=1)

    def test_two_weeks_ago(self) -> None:
        assert parse("two weeks ago", today=REF) == REF - timedelta(weeks=2)

    def test_in_three_days(self) -> None:
        assert parse("in three days", today=REF) == REF + timedelta(days=3)

    def test_2_weeks_from_now(self) -> None:
        assert parse("2 weeks from now", today=REF) == REF + timedelta(weeks=2)

    def test_a_month_from_today(self) -> None:
        assert parse("a month from today", today=REF) == _add_months(REF, 1)


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

    def test_compound_duration(self) -> None:
        assert parse("2 years, 3 months before Dec. 1, 2025", today=REF) == date(
            2023, 9, 1
        )

    def test_compound_with_and(self) -> None:
        assert parse(
            "1 year and 2 months after yesterday", today=REF
        ) == _add_months(_add_months(REF - timedelta(days=1), 12), 2)

    def test_relative_anchor_tomorrow(self) -> None:
        assert parse("3 days after tomorrow", today=REF) == REF + timedelta(days=4)

    def test_a_week_before_absolute(self) -> None:
        assert parse("a week before December 1, 2025", today=REF) == date(
            2025, 11, 24
        )


class TestNextLastWeekday:
    def test_next_tuesday(self) -> None:
        assert parse("next Tuesday", today=REF) == _next_weekday(REF, 1)

    def test_last_friday(self) -> None:
        assert parse("last Friday", today=REF) == _last_weekday(REF, 4)

    def test_next_same_weekday(self) -> None:
        weekday_name = REF.strftime("%A")
        assert parse(f"next {weekday_name}", today=REF) == REF + timedelta(days=7)

    def test_this_monday(self) -> None:
        diff = 0 - REF.weekday()  # Monday = 0
        assert parse("this Monday", today=REF) == REF + timedelta(days=diff)


class TestAbsolute:
    def test_month_day_year(self) -> None:
        assert parse("December 1, 2025") == date(2025, 12, 1)

    def test_month_day_no_year(self) -> None:
        assert parse("June 15", today=REF) == date(REF.year, 6, 15)

    def test_iso_format(self) -> None:
        assert parse("2025-12-01") == date(2025, 12, 1)

    def test_us_slash(self) -> None:
        assert parse("12/01/2025") == date(2025, 12, 1)

    def test_year_slash(self) -> None:
        assert parse("2025/12/04") == date(2025, 12, 4)

    def test_day_month_year(self) -> None:
        assert parse("1 December 2025") == date(2025, 12, 1)

    def test_ordinal_suffix(self) -> None:
        assert parse("January 3rd, 2025") == date(2025, 1, 3)

    def test_abbreviated_month(self) -> None:
        assert parse("Feb 14, 2025") == date(2025, 2, 14)

    def test_abbreviated_month_with_period(self) -> None:
        assert parse("Dec. 1, 2025") == date(2025, 12, 1)


class TestEdgeCases:
    def test_extra_whitespace(self) -> None:
        assert parse("  in   3   days  ", today=REF) == REF + timedelta(days=3)

    def test_mixed_case(self) -> None:
        assert parse("NEXT tuesday", today=REF) == _next_weekday(REF, 1)

    def test_unparseable_raises(self) -> None:
        with pytest.raises(ValueError):
            parse("not a date at all", today=REF)

    def test_hello_world_raises(self) -> None:
        with pytest.raises(ValueError):
            parse("hello world", today=REF)

    def test_today_defaults_to_real_today(self) -> None:
        result = parse("today")
        assert result == date.today()