"""Strategy interface: signals are decisions made only after a bar closes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import IntEnum

from app.providers.base import Bar


class Signal(IntEnum):
    HOLD = 0
    ENTER_LONG = 1
    EXIT_LONG = -1


class Strategy(ABC):
    @abstractmethod
    def generate_signals(self, bars: list[Bar]) -> list[Signal]:
        """Return one close-derived signal per input bar; never inspect future bars."""


