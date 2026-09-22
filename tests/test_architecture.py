import pandas as pd
import pytest
from app.engine import ExecutionModel, futures_pnl, size_futures
from app.models import INSTRUMENTS, normalize_bars
from app.providers.router import MarketDataRouter

class Stub: pass
def router(): return MarketDataRouter({"alpaca":Stub(),"databento":Stub(),"oanda":Stub()})

@pytest.mark.parametrize("symbol,provider,normalized", [("NQ","databento","NQ"),("NQZ6","databento","NQZ6"),("MES front","databento","MES"),("XAU/USD","oanda","XAU_USD"),("SPY","alpaca","SPY")])
def test_routing(symbol,provider,normalized):
    value=router().resolve(symbol); assert (value.provider,value.normalized_symbol)==(provider,normalized)

def test_futures_pnl_and_risk_sizing():
    assert futures_pnl(20000,20010,1,INSTRUMENTS["NQ"]) == 200
    assert futures_pnl(20000,20010,1,INSTRUMENTS["MES"]) == 50
    assert size_futures(spec=INSTRUMENTS["NQ"],account_equity=100_000,risk_percentage=.01,stop_distance=60) == 0
    assert size_futures(spec=INSTRUMENTS["MES"],account_equity=100_000,risk_percentage=.01,stop_distance=10) == 20

def test_timezone_is_required_and_converted():
    raw=pd.DataFrame([{"timestamp":"2025-01-01T01:00:00-05:00","open":1,"high":2,"low":.5,"close":1.5,"volume":2}])
    assert str(normalize_bars(raw,symbol="X",provider="p",asset_class="equity").timestamp.dt.tz)=="UTC"
    raw.timestamp="2025-01-01 01:00:00"
    with pytest.raises(ValueError,match="timezone-aware"): normalize_bars(raw,symbol="X",provider="p",asset_class="equity")

def test_metal_execution_uses_correct_side():
    row=pd.Series({"close":2000,"bid_close":1999.9,"ask_close":2000.1})
    model=ExecutionModel(INSTRUMENTS["XAU_USD"])
    assert model.prices(row,"long",True)==(2000.1,False)
    assert model.prices(row,"long",False)==(1999.9,False)
    assert model.prices(row,"short",True)==(1999.9,False)
