from __future__ import annotations
from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo
import pandas as pd


@dataclass
class MovingAverageCross:
    fast: int = 10
    slow: int = 30
    def generate(self, bars: pd.DataFrame, **kwargs):
        out=bars.copy(); out["fast_ma"]=out.close.rolling(self.fast).mean(); out["slow_ma"]=out.close.rolling(self.slow).mean()
        out["signal"]=(out.fast_ma>out.slow_ma).astype(int).diff().fillna(0)
        return out


@dataclass
class OpeningRangeBreakout:
    opening_range_start: str = "09:30"
    opening_range_end: str = "09:45"
    entry_cutoff: str = "11:30"
    direction: str = "both"
    breakout_buffer: float = 0
    stop_mode: str = "opposite_range"
    take_profit_rr: float = 2
    max_trades_per_day: int = 1
    session_timezone: str = "America/New_York"

    def generate(self, bars: pd.DataFrame, **kwargs):
        if self.direction not in ("long","short","both"): raise ValueError("direction must be long, short, or both")
        out=bars.copy(); local=out.timestamp.dt.tz_convert(ZoneInfo(self.session_timezone)); out["session_date"]=local.dt.date; out["signal"]=0
        start,end,cut=(time.fromisoformat(x) for x in (self.opening_range_start,self.opening_range_end,self.entry_cutoff))
        local_times=local.dt.time
        for day, idx in out.groupby("session_date").groups.items():
            day_idx=list(idx); window=[i for i in day_idx if start <= local_times.iloc[i] < end]
            if not window: continue
            high,low=out.loc[window,"high"].max(),out.loc[window,"low"].min(); trades=0
            for i in day_idx:
                if not (end <= local_times.iloc[i] <= cut) or trades >= self.max_trades_per_day: continue
                if self.direction in ("long","both") and out.at[i,"high"] > high+self.breakout_buffer: out.at[i,"signal"],trades=1,trades+1
                elif self.direction in ("short","both") and out.at[i,"low"] < low-self.breakout_buffer: out.at[i,"signal"],trades=-1,trades+1
            out.loc[day_idx,"opening_range_high"],out.loc[day_idx,"opening_range_low"]=high,low
        return out
