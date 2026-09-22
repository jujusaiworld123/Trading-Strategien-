from __future__ import annotations

from collections import deque

from app.providers.base import Bar
from app.strategies.base import Signal, Strategy


class MovingAverageCrossover(Strategy):
    def __init__(self, fast_ma: int, slow_ma: int) -> None:
        if fast_ma < 1 or slow_ma < 2 or fast_ma >= slow_ma:
            raise ValueError("moving-average periods must satisfy 1 <= fast_ma < slow_ma")
        self.fast_ma, self.slow_ma = fast_ma, slow_ma

    def generate_signals(self, bars: list[Bar]) -> list[Signal]:
        signals = [Signal.HOLD] * len(bars)
        fast_window: deque[float] = deque()
        slow_window: deque[float] = deque()
        fast_sum = slow_sum = 0.0
        previous_relation: int | None = None
        for index, bar in enumerate(bars):
            fast_window.append(bar.close)
            fast_sum += bar.close
            slow_window.append(bar.close)
            slow_sum += bar.close
            if len(fast_window) > self.fast_ma:
                fast_sum -= fast_window.popleft()
            if len(slow_window) > self.slow_ma:
                slow_sum -= slow_window.popleft()
            if len(slow_window) < self.slow_ma:
                continue
            relation = 1 if fast_sum / self.fast_ma > slow_sum / self.slow_ma else -1
            if previous_relation is not None:
                if previous_relation <= 0 < relation:
                    signals[index] = Signal.ENTER_LONG
                elif previous_relation > 0 >= relation:
                    signals[index] = Signal.EXIT_LONG
            previous_relation = relation
        return signals
