import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.execution import ExecutionModel
from app.backtest.position import PercentageExposureSizer
from app.strategies.moving_average import MovingAverageCrossover
from conftest import make_bars


def test_entry_exit_next_open_and_costs() -> None:
    bars = make_bars([3, 2, 1, 2, 3, 2, 1, 1])
    result = BacktestEngine().run(bars, MovingAverageCrossover(2, 3), initial_capital=1000,
                                  sizer=PercentageExposureSizer(0.5),
                                  execution=ExecutionModel(commission=1, slippage=0.01))
    trade = result["trades"][0]
    # Entry signal is bar 4, hence execution is bar 5; exit signal 6, execution bar 7.
    assert trade["entry_time"] == bars[5].timestamp.isoformat()
    assert trade["exit_time"] == bars[7].timestamp.isoformat()
    assert trade["entry_price"] == pytest.approx(bars[5].open * 1.01)
    assert trade["exit_price"] == pytest.approx(bars[7].open * 0.99)
    assert trade["commission"] == 2
    expected_slippage = trade["quantity"] * (bars[5].open * .01 + bars[7].open * .01)
    assert trade["slippage_cost"] == pytest.approx(expected_slippage)
    assert trade["net_pnl"] == pytest.approx(trade["gross_pnl"] - expected_slippage - 2)


def test_signal_on_last_bar_never_fills() -> None:
    bars = make_bars([3, 2, 1, 2])
    result = BacktestEngine().run(bars, MovingAverageCrossover(2, 3), initial_capital=1000,
                                  sizer=PercentageExposureSizer(.5), execution=ExecutionModel())
    assert result["trades"] == []
