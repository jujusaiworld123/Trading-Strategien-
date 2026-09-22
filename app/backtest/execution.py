"""Deterministic next-bar execution with adverse percentage slippage."""
from __future__ import annotations


class ExecutionModel:
    def __init__(self, commission: float = 0.0, slippage: float = 0.0) -> None:
        if commission < 0:
            raise ValueError("commission must be non-negative")
        if not 0 <= slippage < 1:
            raise ValueError("slippage must be a decimal percentage in [0, 1)")
        self.commission, self.slippage = commission, slippage

    def buy_fill(self, market_price: float) -> float:
        return market_price * (1 + self.slippage)

    def sell_fill(self, market_price: float) -> float:
        return market_price * (1 - self.slippage)

