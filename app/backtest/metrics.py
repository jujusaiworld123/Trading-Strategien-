from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any

from app.backtest.models import Trade


def calculate_metrics(trades: list[Trade], equity_values: list[float], initial_capital: float) -> dict[str, Any]:
    pnls = [t.net_pnl for t in trades]
    wins, losses = [x for x in pnls if x > 0], [x for x in pnls if x < 0]
    net = equity_values[-1] - initial_capital
    peak = equity_values[0]
    max_dd = max_dd_pct = 0.0
    for value in equity_values:
        peak = max(peak, value)
        drawdown = peak - value
        if drawdown > max_dd:
            max_dd, max_dd_pct = drawdown, (drawdown / peak * 100 if peak else 0.0)
    gross_profit, gross_loss = sum(wins), abs(sum(losses))
    profit_factor: float | None = gross_profit / gross_loss if gross_loss else (None if not wins else math.inf)
    returns = [(equity_values[i] / equity_values[i - 1] - 1) for i in range(1, len(equity_values))
               if equity_values[i - 1] != 0]
    sharpe = (fmean(returns) / pstdev(returns) * math.sqrt(252)) if len(returns) > 1 and pstdev(returns) else 0.0
    count = len(pnls)
    return {
        "net_profit": net, "net_profit_pct": net / initial_capital * 100,
        "total_trades": count, "winning_trades": len(wins), "losing_trades": len(losses),
        "win_rate": len(wins) / count * 100 if count else 0.0,
        "average_win": fmean(wins) if wins else 0.0, "average_loss": fmean(losses) if losses else 0.0,
        "profit_factor": profit_factor, "expectancy": fmean(pnls) if pnls else 0.0,
        "max_drawdown": max_dd, "max_drawdown_pct": max_dd_pct, "sharpe_ratio": sharpe,
        "average_trade": fmean(pnls) if pnls else 0.0, "largest_win": max(wins, default=0.0),
        "largest_loss": min(losses, default=0.0),
    }

