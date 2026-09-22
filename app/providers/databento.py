from __future__ import annotations
import importlib
import os
import pandas as pd
from app.models import INSTRUMENTS, normalize_bars
from .base import MarketDataProvider, ProviderError

SCHEMAS = {"1Sec": "ohlcv-1s", "1Min": "ohlcv-1m", "1Hour": "ohlcv-1h", "1Day": "ohlcv-1d"}
RESAMPLE = {"5Min": "5min", "15Min": "15min", "30Min": "30min"}


class DatabentoMarketDataProvider(MarketDataProvider):
    name = "databento"
    def __init__(self, api_key: str | None = None): self.api_key = api_key or os.getenv("DATABENTO_API_KEY")
    def validate_symbol(self, symbol: str) -> bool: return symbol.split(".")[0][:3].rstrip("FGHJKMNQUVXZ0123456789") in INSTRUMENTS or symbol.startswith(("NQ", "MES"))
    def get_available_timeframes(self): return tuple(SCHEMAS | RESAMPLE)
    def get_instrument_info(self, symbol: str): return INSTRUMENTS[symbol.split(".")[0][:3].rstrip("FGHJKMNQUVXZ0123456789")]
    def get_bars(self, symbol, timeframe, start, end, **kwargs):
        if not self.api_key: raise ProviderError("DATABENTO_API_KEY is required")
        if timeframe not in self.get_available_timeframes(): raise ProviderError(f"Unsupported Databento timeframe: {timeframe}")
        databento = importlib.import_module("databento")
        schema = SCHEMAS.get(timeframe, "ohlcv-1m")
        data = databento.Historical(self.api_key).timeseries.get_range(dataset="GLBX.MDP3", symbols=[symbol], stype_in="continuous" if "." in symbol else "raw_symbol", schema=schema, start=start, end=end)
        frame = data.to_df().reset_index()
        frame = frame.rename(columns={"ts_event": "timestamp", "instrument_id": "underlying_contract"})
        root = symbol.split(".")[0]
        result = normalize_bars(frame, symbol=root, provider=self.name, asset_class="future", metadata={"continuous_methodology": "Databento calendar front-month rank 0; no local stitching"})
        if timeframe in RESAMPLE:
            result = self._resample(result, RESAMPLE[timeframe])
        return result
    @staticmethod
    def _resample(frame, rule):
        indexed = frame.set_index("timestamp")
        grouped = indexed.groupby([indexed.index.tz_convert("America/Chicago").date, "underlying_contract"], dropna=False)
        output = grouped.resample(rule, origin="start_day", label="left", closed="left").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"), volume=("volume", "sum")).dropna(subset=["open"]).reset_index()
        return normalize_bars(output, symbol=frame.symbol.iloc[0], provider="databento", asset_class="future", metadata=frame.attrs)
