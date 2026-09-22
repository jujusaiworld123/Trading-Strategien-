from __future__ import annotations
from app.engine import BacktestEngine
from app.models import INSTRUMENTS
from app.providers import AlpacaMarketDataProvider, DatabentoMarketDataProvider, MarketDataRouter, OandaMarketDataProvider
from app.strategies import MovingAverageCross, OpeningRangeBreakout


def default_router(): return MarketDataRouter({"alpaca":AlpacaMarketDataProvider(),"databento":DatabentoMarketDataProvider(),"oanda":OandaMarketDataProvider()})


def get_market_data(symbol: str, timeframe: str, start: str, end: str, provider: str="auto", session: str|None=None, price_mode: str|None=None, continuous: bool=True, contract: str|None=None):
    kwargs={"continuous":continuous,"contract":contract}
    if price_mode is not None: kwargs["price_mode"]=price_mode
    return default_router().get_bars(symbol,timeframe,start,end,provider,**kwargs)


def run_backtest(symbol: str, timeframe: str, start: str, end: str, strategy: str="moving_average", provider: str="auto", **parameters):
    router=default_router(); resolution=router.resolve(symbol,provider,continuous=parameters.pop("continuous",True),contract=parameters.pop("contract",None))
    data_options={"continuous":resolution.continuous}
    if (price_mode := parameters.pop("price_mode", None)) is not None: data_options["price_mode"] = price_mode
    bars=router.get_bars(symbol,timeframe,start,end,provider,**data_options)
    root=resolution.normalized_symbol
    spec=INSTRUMENTS.get(root) or router.providers[resolution.provider].get_instrument_info(root)
    model=OpeningRangeBreakout(**parameters) if strategy == "orb" else MovingAverageCross(**parameters)
    return BacktestEngine().run(bars,model,spec)
