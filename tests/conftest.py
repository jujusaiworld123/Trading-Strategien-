from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.providers.base import Bar


def make_bars(closes: list[float]) -> list[Bar]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [Bar(start + timedelta(days=i), close, close + 1, close - 1, close, 1000, "TEST")
            for i, close in enumerate(closes)]

