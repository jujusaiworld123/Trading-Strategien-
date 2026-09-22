from app.strategies.base import Signal
from app.strategies.moving_average import MovingAverageCrossover
from conftest import make_bars


def test_ma_crossover_signals_use_only_current_and_past_closes() -> None:
    bars = make_bars([3, 2, 1, 2, 3, 2, 1])
    signals = MovingAverageCrossover(2, 3).generate_signals(bars)
    assert signals[4] == Signal.ENTER_LONG
    assert signals[6] == Signal.EXIT_LONG
    prefix = MovingAverageCrossover(2, 3).generate_signals(bars[:5])
    assert prefix == signals[:5]  # Appending future data cannot alter prior signals.
