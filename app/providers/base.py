"""Provider-neutral normalized market-data contract."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

SUPPORTED_TIMEFRAMES = ("1Min", "5Min", "15Min", "30Min", "1Hour", "1Day")


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["timestamp"] = self.timestamp.isoformat()
        return value


def validate_bars(bars: list[Bar]) -> None:
    previous: datetime | None = None
    seen: set[datetime] = set()
    for bar in bars:
        if bar.timestamp in seen:
            raise ValueError(f"duplicate timestamp: {bar.timestamp.isoformat()}")
        if previous is not None and bar.timestamp <= previous:
            raise ValueError("bar timestamps must be strictly ascending")
        if not (bar.low <= bar.open <= bar.high and bar.low <= bar.close <= bar.high):
            raise ValueError(f"invalid OHLC values at {bar.timestamp.isoformat()}")
        if bar.volume < 0:
            raise ValueError(f"negative volume at {bar.timestamp.isoformat()}")
        seen.add(bar.timestamp)
        previous = bar.timestamp


class MarketDataProvider(ABC):
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, start: datetime, end: datetime,
                 *, feed: str | None = None, adjustment: str = "raw", limit: int = 10_000) -> list[Bar]:
        """Return validated, ascending, normalized bars without inventing missing candles."""

    @abstractmethod
    def get_asset_info(self, symbol: str) -> dict[str, Any]:
        """Return JSON-compatible read-only asset metadata."""

