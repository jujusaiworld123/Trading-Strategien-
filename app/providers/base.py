from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class ProviderError(RuntimeError):
    pass


class MarketDataProvider(ABC):
    name: str
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool: ...
    @abstractmethod
    def get_available_timeframes(self) -> tuple[str, ...]: ...
    @abstractmethod
    def get_instrument_info(self, symbol: str) -> Any: ...
    @abstractmethod
    def get_bars(self, symbol: str, timeframe: str, start: str, end: str, **kwargs: Any) -> pd.DataFrame: ...

    def get_trades(self, *args: Any, **kwargs: Any): raise NotImplementedError
    def get_quotes(self, *args: Any, **kwargs: Any): raise NotImplementedError
    def get_order_book(self, *args: Any, **kwargs: Any): raise NotImplementedError
    def get_calendar(self, *args: Any, **kwargs: Any): raise NotImplementedError
    def get_sessions(self, *args: Any, **kwargs: Any): raise NotImplementedError
