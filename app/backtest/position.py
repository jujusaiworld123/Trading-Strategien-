"""Replaceable position-sizing policies."""
from __future__ import annotations

from abc import ABC, abstractmethod


class PositionSizer(ABC):
    @abstractmethod
    def quantity(self, equity: float, price: float) -> float: ...


class PercentageExposureSizer(PositionSizer):
    """Allocate a fraction of equity; this is exposure, not stop-risk sizing."""
    def __init__(self, exposure_fraction: float) -> None:
        if not 0 < exposure_fraction <= 1:
            raise ValueError("risk_per_trade must be in (0, 1]")
        self.exposure_fraction = exposure_fraction

    def quantity(self, equity: float, price: float) -> float:
        return equity * self.exposure_fraction / price

