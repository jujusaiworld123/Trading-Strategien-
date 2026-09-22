"""Long-only event loop. Close-of-bar signals execute at the next bar's open."""
from __future__ import annotations

from typing import Any

from app.backtest.execution import ExecutionModel
from app.backtest.metrics import calculate_metrics
from app.backtest.models import Position, Trade
from app.backtest.position import PositionSizer
from app.providers.base import Bar, validate_bars
from app.strategies.base import Signal, Strategy


class BacktestEngine:
    def run(self, bars: list[Bar], strategy: Strategy, *, initial_capital: float,
            sizer: PositionSizer, execution: ExecutionModel) -> dict[str, Any]:
        if initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if len(bars) < 2:
            raise ValueError("at least two bars are required")
        validate_bars(bars)
        signals = strategy.generate_signals(bars)
        if len(signals) != len(bars):
            raise ValueError("strategy returned an invalid number of signals")
        cash, position, trades = initial_capital, None, []
        equity_curve: list[dict[str, Any]] = [{"timestamp": bars[0].timestamp.isoformat(), "equity": cash}]
        for index in range(1, len(bars)):
            bar, prior_signal = bars[index], signals[index - 1]
            if prior_signal == Signal.ENTER_LONG and position is None:
                fill = execution.buy_fill(bar.open)
                quantity = sizer.quantity(cash, fill)
                cost = quantity * fill + execution.commission
                if quantity > 0 and cost <= cash:
                    cash -= cost
                    position = Position(bar.timestamp, bar.open, fill, quantity, execution.commission)
            elif prior_signal == Signal.EXIT_LONG and position is not None:
                cash, trade = _close(position, bar, cash, execution, "signal")
                trades.append(trade)
                position = None
            equity = cash + (position.quantity * bar.close if position else 0.0)
            equity_curve.append({"timestamp": bar.timestamp.isoformat(), "equity": equity})
        if position is not None:
            cash, trade = _close(position, bars[-1], cash, execution, "end_of_data")
            trades.append(trade)
            equity_curve[-1]["equity"] = cash
        values = [point["equity"] for point in equity_curve]
        return {"metrics": calculate_metrics(trades, values, initial_capital), "equity_curve": equity_curve,
                "trades": [trade.to_dict() for trade in trades],
                "assumptions": {"signal_timing": "bar close; fill at next bar open",
                                "slippage": "decimal fraction of price, adverse on entry and exit",
                                "commission": "fixed cash amount per order",
                                "sizing": "risk_per_trade is percentage-of-equity exposure (no stop distance)"}}


def _close(position: Position, bar: Bar, cash: float, execution: ExecutionModel, reason: str) -> tuple[float, Trade]:
    fill = execution.sell_fill(bar.open if reason == "signal" else bar.close)
    proceeds = position.quantity * fill - execution.commission
    cash += proceeds
    market_exit = bar.open if reason == "signal" else bar.close
    gross = position.quantity * (market_exit - position.market_entry_price)
    slip = position.quantity * ((position.fill_entry_price - position.market_entry_price) + (market_exit - fill))
    commissions = position.entry_commission + execution.commission
    net = gross - slip - commissions
    trade = Trade(position.entry_time, bar.timestamp, bar.symbol, "long", position.fill_entry_price, fill,
                  position.quantity, gross, commissions, slip, net,
                  net / (position.quantity * position.fill_entry_price) * 100, reason)
    return cash, trade
