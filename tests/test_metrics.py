from datetime import datetime, timezone

import pytest

from app.backtest.metrics import calculate_metrics
from app.backtest.models import Trade


def trade(pnl: float) -> Trade:
    now = datetime.now(timezone.utc)
    return Trade(now, now, "T", "long", 1, 1, 1, pnl, 0, 0, pnl, pnl, "signal")


def test_drawdown_and_profit_factor() -> None:
    result = calculate_metrics([trade(20), trade(-10)], [100, 120, 90, 110], 100)
    assert result["profit_factor"] == 2
    assert result["max_drawdown"] == 30
    assert result["max_drawdown_pct"] == 25
    assert result["net_profit"] == 10


def test_no_losses_profit_factor_is_infinite() -> None:
    assert calculate_metrics([trade(1)], [100, 101], 100)["profit_factor"] == pytest.approx(float("inf"))

