from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import Enum
from typing import Any

import pandas as pd


class AssetClass(str, Enum):
    EQUITY = "equity"
    CRYPTO = "crypto"
    FUTURE = "future"
    METAL = "metal"


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str
    asset_class: AssetClass
    exchange: str
    currency: str
    tick_size: float
    tick_value: float
    point_value: float
    contract_multiplier: float
    timezone: str
    session_template: str
    sizing_semantics: str = "units"
    price_precision: int = 2
    minimum_units: float = 1


INSTRUMENTS = {
    # CME: NQ is $20/index point ($5 per 0.25 tick); MES is $5/point ($1.25/tick).
    "NQ": InstrumentSpec("NQ", AssetClass.FUTURE, "CME", "USD", .25, 5, 20, 20, "America/Chicago", "CME_EQUITY_INDEX", "contracts", 2, 1),
    "MES": InstrumentSpec("MES", AssetClass.FUTURE, "CME", "USD", .25, 1.25, 5, 5, "America/Chicago", "CME_EQUITY_INDEX", "contracts", 2, 1),
    "XAU_USD": InstrumentSpec("XAU_USD", AssetClass.METAL, "OANDA", "USD", .01, .01, 1, 1, "UTC", "FX_24X5", "units", 3, 1),
}


@dataclass(frozen=True)
class SymbolResolution:
    requested_symbol: str
    normalized_symbol: str
    provider_symbol: str
    provider: str
    continuous: bool = False


REQUIRED_BAR_COLUMNS = ("timestamp", "symbol", "open", "high", "low", "close", "volume", "provider", "asset_class")


def normalize_bars(frame: pd.DataFrame, *, symbol: str, provider: str, asset_class: str, metadata: dict[str, Any] | None = None) -> pd.DataFrame:
    """Return the canonical bar schema, rejecting naive timestamps."""
    result = frame.copy()
    if "timestamp" not in result and isinstance(result.index, pd.DatetimeIndex):
        result = result.reset_index(names="timestamp")
    result["timestamp"] = pd.to_datetime(result["timestamp"], utc=False)
    if result["timestamp"].dt.tz is None:
        raise ValueError("Market-data timestamps must be timezone-aware; provider returned naive values")
    result["timestamp"] = result["timestamp"].dt.tz_convert("UTC")
    result["symbol"], result["provider"], result["asset_class"] = symbol, provider, asset_class
    result.attrs.update(metadata or {})
    missing = set(REQUIRED_BAR_COLUMNS) - set(result.columns)
    if missing:
        raise ValueError(f"Missing normalized bar fields: {sorted(missing)}")
    return result.sort_values("timestamp").reset_index(drop=True)


@dataclass(frozen=True)
class Session:
    kind: str = "ETH"
    start: time | None = None
    end: time | None = None
    timezone: str = "America/New_York"

    def filter(self, bars: pd.DataFrame) -> pd.DataFrame:
        if self.kind.upper() == "ETH" and self.start is None:
            return bars
        start, end = (time(9, 30), time(16)) if self.kind.upper() == "RTH" else (self.start, self.end)
        if start is None or end is None:
            raise ValueError("CUSTOM session requires start and end")
        local = bars.timestamp.dt.tz_convert(self.timezone).dt.time
        mask = (local >= start) & (local < end) if start < end else ((local >= start) | (local < end))
        return bars.loc[mask].reset_index(drop=True)
