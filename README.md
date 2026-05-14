# nldate

A zero-dependency Python library that turns natural-language date strings into `datetime.date` objects.

## Installation

```bash
pip install nldate
```

## Usage

```python
from datetime import date
from nldate import parse

# Absolute dates
parse("December 1, 2025")          # date(2025, 12, 1)
parse("2025-12-01")                # date(2025, 12, 1)
parse("12/01/2025")                # date(2025, 12, 1)

# Relative dates (pass `today` for deterministic results)
ref = date(2025, 6, 11)
parse("today", today=ref)          # date(2025, 6, 11)
parse("tomorrow", today=ref)       # date(2025, 6, 12)
parse("in 5 days", today=ref)      # date(2025, 6, 16)
parse("3 weeks ago", today=ref)    # date(2025, 5, 21)

# Weekday references
parse("next Tuesday", today=ref)   # date(2025, 6, 17)
parse("last Friday", today=ref)    # date(2025, 6, 6)

# Offsets from an anchor
parse("5 days before December 1st, 2025")  # date(2025, 11, 26)
parse("2 weeks after January 1, 2026")     # date(2026, 1, 15)
```

## Supported formats

| Category | Examples |
|---|---|
| Keywords | `today`, `tomorrow`, `yesterday` |
| Relative | `in 5 days`, `3 weeks ago`, `1 month ago`, `in 2 years` |
| Before/after | `5 days before Dec 1st, 2025`, `2 weeks after Jan 1, 2026` |
| Weekday | `next Tuesday`, `last Friday`, `this Monday` |
| Absolute | `December 1, 2025`, `1 December 2025`, `2025-12-01`, `12/01/2025` |

## Development

```bash
uv sync
uv run pytest
uv run mypy src/ tests/
uv run ruff check src/ tests/
```
