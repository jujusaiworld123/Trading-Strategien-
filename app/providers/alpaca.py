from __future__ import annotations
import importlib
import os
from app.models import AssetClass, InstrumentSpec, normalize_bars
from .base import MarketDataProvider, ProviderError


class AlpacaMarketDataProvider(MarketDataProvider):
    name = "alpaca"
    def __init__(self, api_key=None, secret_key=None): self.api_key, self.secret_key = api_key or os.getenv("ALPACA_API_KEY"), secret_key or os.getenv("ALPACA_SECRET_KEY")
    def validate_symbol(self, symbol): return bool(symbol)
    def get_available_timeframes(self): return ("1Min","5Min","15Min","30Min","1Hour","1Day")
    def get_instrument_info(self, symbol): return InstrumentSpec(symbol, AssetClass.EQUITY, "US", "USD", .01, .01, 1, 1, "America/New_York", "US_EQUITY_RTH")
    def get_bars(self, symbol, timeframe, start, end, **kwargs):
        if not self.api_key or not self.secret_key: raise ProviderError("ALPACA_API_KEY and ALPACA_SECRET_KEY are required")
        hist = importlib.import_module("alpaca.data.historical")
        reqs = importlib.import_module("alpaca.data.requests")
        tf = importlib.import_module("alpaca.data.timeframe")
        mapping={"1Min":tf.TimeFrame.Minute,"5Min":tf.TimeFrame(5,tf.TimeFrameUnit.Minute),"15Min":tf.TimeFrame(15,tf.TimeFrameUnit.Minute),"30Min":tf.TimeFrame(30,tf.TimeFrameUnit.Minute),"1Hour":tf.TimeFrame.Hour,"1Day":tf.TimeFrame.Day}
        request=reqs.StockBarsRequest(symbol_or_symbols=symbol,timeframe=mapping[timeframe],start=start,end=end)
        frame=hist.StockHistoricalDataClient(self.api_key,self.secret_key).get_stock_bars(request).df.reset_index()
        return normalize_bars(frame, symbol=symbol, provider=self.name, asset_class="equity")
