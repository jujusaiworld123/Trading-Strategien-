from __future__ import annotations
import os
import httpx
import pandas as pd
from app.models import INSTRUMENTS, normalize_bars
from .base import MarketDataProvider, ProviderError

GRANULARITIES = {"1Min":"M1", "5Min":"M5", "15Min":"M15", "30Min":"M30", "1Hour":"H1", "1Day":"D"}


class OandaMarketDataProvider(MarketDataProvider):
    name = "oanda"
    def __init__(self, token=None, account_id=None, environment=None):
        self.token, self.account_id = token or os.getenv("OANDA_API_TOKEN"), account_id or os.getenv("OANDA_ACCOUNT_ID")
        env = environment or os.getenv("OANDA_ENVIRONMENT", "practice")
        if env not in ("practice", "live"): raise ValueError("OANDA_ENVIRONMENT must be practice or live")
        self.base_url = f"https://api-fx{'practice' if env == 'practice' else 'trade'}.oanda.com"
    @property
    def headers(self): return {"Authorization": f"Bearer {self.token}"}
    def _configured(self):
        if not self.token or not self.account_id: raise ProviderError("OANDA_API_TOKEN and OANDA_ACCOUNT_ID are required")
    def validate_symbol(self, symbol):
        self._configured()
        response = httpx.get(f"{self.base_url}/v3/accounts/{self.account_id}/instruments", headers=self.headers, timeout=30)
        response.raise_for_status()
        return any(i["name"] == symbol for i in response.json()["instruments"])
    def get_available_timeframes(self): return tuple(GRANULARITIES)
    def get_instrument_info(self, symbol):
        if symbol != "XAU_USD": raise ProviderError(f"Unsupported metal: {symbol}")
        if not self.validate_symbol(symbol): raise ProviderError("XAU_USD is unavailable for the configured OANDA account/region")
        return INSTRUMENTS[symbol]
    def get_bars(self, symbol, timeframe, start, end, price_mode="bid_ask", **kwargs):
        self.get_instrument_info(symbol)
        if timeframe not in GRANULARITIES: raise ProviderError(f"Unsupported OANDA timeframe: {timeframe}")
        price = "MBA" if price_mode == "bid_ask" else "M"
        response = httpx.get(f"{self.base_url}/v3/instruments/{symbol}/candles", headers=self.headers, params={"from":start,"to":end,"granularity":GRANULARITIES[timeframe],"price":price}, timeout=30)
        response.raise_for_status()
        rows=[]
        for candle in response.json()["candles"]:
            if not candle.get("complete", True): continue
            mid = candle.get("mid") or {k: (float(candle["bid"][k])+float(candle["ask"][k]))/2 for k in "ohlc"}
            row={"timestamp":candle["time"],"open":float(mid["o"]),"high":float(mid["h"]),"low":float(mid["l"]),"close":float(mid["c"]),"volume":candle["volume"]}
            for side in ("bid", "ask"):
                if side in candle:
                    row.update({f"{side}_{name}":float(candle[side][letter]) for name,letter in (("open","o"),("high","h"),("low","l"),("close","c"))})
            rows.append(row)
        return normalize_bars(pd.DataFrame(rows), symbol=symbol, provider=self.name, asset_class="metal", metadata={"price_mode":price_mode,"synthetic_spread":False})
