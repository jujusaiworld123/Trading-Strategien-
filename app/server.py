"""Streamable HTTP MCP entrypoint exposing an intentionally small read-only surface."""
from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import Settings
from app.providers.alpaca import AlpacaMarketDataProvider
from app.providers.base import MarketDataProvider
from app.tools.backtest import run_backtest as execute_backtest
from app.tools.market_data import get_market_data as fetch_market_data
from app.tools.market_data import supported_timeframes

settings = Settings.from_env()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("alpaca_backtesting_mcp")
mcp = FastMCP("Alpaca Backtesting (Read Only)", host=settings.host, port=settings.port,
              streamable_http_path="/mcp", stateless_http=True, json_response=True)


def _provider() -> MarketDataProvider:
    return AlpacaMarketDataProvider(settings.alpaca_api_key, settings.alpaca_secret_key,
                                    paper=settings.paper_trade)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    """Unauthenticated liveness only; never reveal configuration or credentials."""
    return JSONResponse({"status": "ok", "service": "alpaca-backtesting-mcp", "read_only": True})


@mcp.tool(description="Fetch validated normalized historical OHLCV bars from Alpaca (maximum 10,000).")
def get_market_data(symbol: str, timeframe: str, start: str, end: str, feed: str | None = None,
                    adjustment: str = "raw", limit: int = 10_000) -> dict[str, Any]:
    logger.info("market_data_request symbol=%s timeframe=%s limit=%d", symbol, timeframe, limit)
    return fetch_market_data(_provider(), symbol, timeframe, start, end, feed, adjustment, limit)


@mcp.tool(description="List accepted bar timeframes.")
def get_supported_timeframes() -> dict[str, Any]:
    return supported_timeframes()


@mcp.tool(description="Fetch read-only Alpaca asset metadata. This tool cannot place orders.")
def get_asset_info(symbol: str) -> dict[str, Any]:
    logger.info("asset_info_request symbol=%s", symbol)
    return _provider().get_asset_info(symbol)


@mcp.tool(description="Run a deterministic long-only MA crossover backtest on Alpaca historical bars.")
def run_backtest(symbol: str, timeframe: str, start: str, end: str, initial_capital: float,
                 risk_per_trade: float, commission: float, slippage: float,
                 strategy: dict[str, Any], feed: str | None = None,
                 adjustment: str = "raw", limit: int = 10_000) -> dict[str, Any]:
    logger.info("backtest_start symbol=%s timeframe=%s", symbol, timeframe)
    result = execute_backtest(_provider(), symbol=symbol, timeframe=timeframe, start=start, end=end,
                              initial_capital=initial_capital, risk_per_trade=risk_per_trade,
                              commission=commission, slippage=slippage, strategy=strategy,
                              feed=feed, adjustment=adjustment, limit=limit)
    logger.info("backtest_complete symbol=%s trades=%d", symbol, result["metrics"]["total_trades"])
    return result


def main() -> None:
    logger.info("server_start host=%s port=%d transport=streamable-http read_only=true",
                settings.host, settings.port)
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
