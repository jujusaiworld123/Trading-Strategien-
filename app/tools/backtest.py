from __future__ import annotations

from typing import Any

from app.backtest.engine import BacktestEngine
from app.backtest.execution import ExecutionModel
from app.backtest.position import PercentageExposureSizer
from app.providers.base import MarketDataProvider
from app.strategies.moving_average import MovingAverageCrossover
from app.tools.market_data import parse_datetime


def run_backtest(provider: MarketDataProvider, *, symbol: str, timeframe: str, start: str, end: str,
                 initial_capital: float, risk_per_trade: float, commission: float, slippage: float,
                 strategy: dict[str, Any], feed: str | None = None,
                 adjustment: str = "raw", limit: int = 10_000) -> dict[str, Any]:
    name = str(strategy.get("name", "")).lower()
    if name not in {"moving_average_crossover", "ma_crossover"}:
        raise ValueError("strategy.name must be 'moving_average_crossover'")
    try:
        implementation = MovingAverageCrossover(int(strategy["fast_ma"]), int(strategy["slow_ma"]))
    except KeyError as exc:
        raise ValueError(f"missing strategy parameter: {exc.args[0]}") from exc
    bars = provider.get_bars(symbol, timeframe, parse_datetime(start, "start"), parse_datetime(end, "end"),
                             feed=feed, adjustment=adjustment, limit=limit)
    result = BacktestEngine().run(bars, implementation, initial_capital=initial_capital,
                                  sizer=PercentageExposureSizer(risk_per_trade),
                                  execution=ExecutionModel(commission, slippage))
    result["request"] = {"symbol": symbol.upper(), "timeframe": timeframe, "start": start, "end": end,
                         "strategy": strategy}
    return result

