"""nldate – Turn natural-language date strings into datetime.date objects."""

from nldate._parser import ParseError, parse

__all__ = ["ParseError", "parse"]
