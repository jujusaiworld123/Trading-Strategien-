"""MCP entry point. DataFrames are serialized to records at the protocol boundary."""
import importlib
from app.service import get_market_data as fetch_market_data, run_backtest as execute_backtest

mcp_server = importlib.import_module("mcp.server.fastmcp")
mcp = mcp_server.FastMCP("Multi-provider Backtesting")

@mcp.tool()
def get_market_data(symbol: str, timeframe: str, start: str, end: str, provider: str="auto", session: str|None=None, price_mode: str|None=None, continuous: bool=True, contract: str|None=None):
    bars=fetch_market_data(symbol,timeframe,start,end,provider,session,price_mode,continuous,contract)
    return {"metadata":dict(bars.attrs),"bars":bars.to_dict(orient="records")}

@mcp.tool()
def run_backtest(symbol: str, timeframe: str, start: str, end: str, strategy: str="moving_average", provider: str="auto", parameters: dict|None=None):
    result=execute_backtest(symbol,timeframe,start,end,strategy,provider,**(parameters or {}))
    return result.to_dict(orient="records")

if __name__ == "__main__": mcp.run()
