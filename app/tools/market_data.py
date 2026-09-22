from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.providers.base import MarketDataProvider, SUPPORTED_TIMEFRAMES


def parse_datetime(value: str, field: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 datetime") from exc
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def get_market_data(provider: MarketDataProvider, symbol: str, timeframe: str, start: str, end: str,
                    feed: str | None = None, adjustment: str = "raw", limit: int = 10_000) -> dict[str, Any]:
    bars = provider.get_bars(symbol, timeframe, parse_datetime(start, "start"), parse_datetime(end, "end"),
                             feed=feed, adjustment=adjustment, limit=limit)
    return {"symbol": symbol.upper(), "timeframe": timeframe, "count": len(bars),
            "bars": [bar.to_dict() for bar in bars],
            "missing_candles": "not filled; provider output is returned as-is"}


def supported_timeframes() -> dict[str, Any]:
    return {"timeframes": list(SUPPORTED_TIMEFRAMES)}

