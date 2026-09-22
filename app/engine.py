from __future__ import annotations
from dataclasses import dataclass
import math
import pandas as pd
from app.models import AssetClass, InstrumentSpec


def futures_pnl(entry: float, exit: float, contracts: int, spec: InstrumentSpec, side: str = "long") -> float:
    if spec.asset_class != AssetClass.FUTURE: raise ValueError("futures_pnl requires a futures specification")
    if not isinstance(contracts, int) or contracts < 0: raise ValueError("contracts must be a non-negative integer")
    direction = 1 if side == "long" else -1
    return (exit - entry) * spec.point_value * contracts * direction


def size_futures(*, spec: InstrumentSpec, fixed_contracts: int | None = None, account_equity: float | None = None, risk_percentage: float | None = None, stop_distance: float | None = None) -> int:
    if fixed_contracts is not None:
        if not isinstance(fixed_contracts, int) or fixed_contracts < 0: raise ValueError("Futures contracts must be a non-negative integer")
        return fixed_contracts
    if any(v is None for v in (account_equity, risk_percentage, stop_distance)): raise ValueError("Risk sizing requires account_equity, risk_percentage, and stop_distance")
    if account_equity <= 0 or not 0 < risk_percentage <= 1 or stop_distance <= 0: raise ValueError("Invalid risk sizing inputs")
    return math.floor((account_equity * risk_percentage) / (stop_distance * spec.point_value))


@dataclass
class ExecutionModel:
    spec: InstrumentSpec
    synthetic_spread: float | None = None

    def prices(self, row: pd.Series, side: str, entering: bool) -> tuple[float, bool]:
        field = ("ask" if side == "long" else "bid") if entering else ("bid" if side == "long" else "ask")
        column = f"{field}_close"
        if column in row and pd.notna(row[column]): return float(row[column]), False
        mid = float(row["close"])
        if self.spec.asset_class == AssetClass.METAL:
            if self.synthetic_spread is None: raise ValueError("Bid/ask data absent; configure synthetic_spread explicitly")
            adjustment = self.synthetic_spread / 2
            return mid + adjustment if field == "ask" else mid - adjustment, True
        return mid, False

    def pnl(self, entry: float, exit: float, quantity: float, side: str) -> float:
        direction = 1 if side == "long" else -1
        multiplier = self.spec.point_value if self.spec.asset_class == AssetClass.FUTURE else self.spec.contract_multiplier
        return (exit-entry) * multiplier * quantity * direction


class BacktestEngine:
    """Provider-independent runner: strategies consume normalized bars only."""
    def run(self, bars: pd.DataFrame, strategy, spec: InstrumentSpec, **kwargs):
        required={"timestamp","open","high","low","close","volume"}
        if missing := required-set(bars): raise ValueError(f"Missing bars: {sorted(missing)}")
        return strategy.generate(bars, **kwargs)
