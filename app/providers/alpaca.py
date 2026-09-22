"""Read-only Alpaca SDK provider. No trading client is imported or constructed."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient

from app.providers.base import Bar, MarketDataProvider, SUPPORTED_TIMEFRAMES, validate_bars

_TIMEFRAMES = {
    "1Min": TimeFrame.Minute, "5Min": TimeFrame(5, TimeFrameUnit.Minute),
    "15Min": TimeFrame(15, TimeFrameUnit.Minute), "30Min": TimeFrame(30, TimeFrameUnit.Minute),
    "1Hour": TimeFrame.Hour, "1Day": TimeFrame.Day,
}


class AlpacaMarketDataProvider(MarketDataProvider):
    def __init__(self, api_key: str | None, secret_key: str | None, *, paper: bool = True) -> None:
        if not api_key or not secret_key:
            raise ValueError("Missing ALPACA_API_KEY or ALPACA_SECRET_KEY")
        self._key, self._secret, self._paper = api_key, secret_key, paper

    def get_bars(self, symbol: str, timeframe: str, start: datetime, end: datetime,
                 *, feed: str | None = None, adjustment: str = "raw", limit: int = 10_000) -> list[Bar]:
        symbol = _validate_request(symbol, timeframe, start, end, limit)
        is_crypto = "/" in symbol
        if is_crypto:
            client = CryptoHistoricalDataClient(self._key, self._secret)
            request: Any = CryptoBarsRequest(symbol_or_symbols=symbol, timeframe=_TIMEFRAMES[timeframe],
                                             start=start, end=end, limit=limit)
        else:
            client = StockHistoricalDataClient(self._key, self._secret)
            try:
                request = StockBarsRequest(symbol_or_symbols=symbol, timeframe=_TIMEFRAMES[timeframe],
                                           start=start, end=end, limit=limit,
                                           adjustment=Adjustment(adjustment),
                                           feed=DataFeed(feed) if feed else None)
            except ValueError as exc:
                raise ValueError("invalid feed or adjustment") from exc
        try:
            raw = client.get_crypto_bars(request) if is_crypto else client.get_stock_bars(request)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 429:
                raise RuntimeError("Alpaca rate limit exceeded; retry later") from None
            raise RuntimeError("Alpaca market-data request failed") from None
        records = raw.data.get(symbol, [])
        bars = [Bar(timestamp=x.timestamp, open=float(x.open), high=float(x.high), low=float(x.low),
                    close=float(x.close), volume=float(x.volume), symbol=symbol) for x in records]
        validate_bars(bars)
        if not bars:
            raise ValueError("no market data found for the requested range")
        return bars

    def get_asset_info(self, symbol: str) -> dict[str, Any]:
        symbol = symbol.strip().upper()
        if not symbol:
            raise ValueError("symbol is required")
        try:
            # TradingClient is used only for its read-only get_asset endpoint.
            asset = TradingClient(self._key, self._secret, paper=self._paper).get_asset(symbol)
        except Exception:
            raise RuntimeError("Alpaca asset lookup failed") from None
        return {"symbol": asset.symbol, "name": asset.name, "asset_class": str(asset.asset_class),
                "exchange": str(asset.exchange), "status": str(asset.status),
                "tradable": asset.tradable, "fractionable": asset.fractionable}


def _validate_request(symbol: str, timeframe: str, start: datetime, end: datetime, limit: int) -> str:
    symbol = symbol.strip().upper()
    if not symbol or len(symbol) > 32:
        raise ValueError("invalid symbol")
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError(f"invalid timeframe; supported: {', '.join(SUPPORTED_TIMEFRAMES)}")
    if start >= end:
        raise ValueError("start must be earlier than end")
    if not 1 <= limit <= 10_000:
        raise ValueError("limit must be between 1 and 10000")
    return symbol
