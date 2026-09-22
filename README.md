# Multi-provider Backtesting MCP

A vendor-neutral research service that routes US equities to Alpaca, CME NQ/MES futures to Databento, and spot gold (`XAU_USD`) to OANDA. Providers emit one UTC, timezone-aware OHLCV schema and the backtest engine only consumes that schema.

## Configuration

Credentials are read only from the environment:

* `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`
* `DATABENTO_API_KEY`
* `OANDA_API_TOKEN`, `OANDA_ACCOUNT_ID`, and `OANDA_ENVIRONMENT` (`practice`, the default, or `live`)

Install with `pip install -e '.[test,mcp,alpaca,databento]'`, then run `python -m app.mcp_server`. The MCP tools are `get_market_data` and `run_backtest`; both use `provider="auto"` unless explicitly constrained.

## Futures continuity and sessions

Version 1 delegates continuous futures selection to Databento using its calendar continuous front-month, rank-zero symbol (`NQ.c.0` / `MES.c.0`). It does **not** locally stitch contracts. Every returned record retains the Databento instrument identifier in `underlying_contract`, and metadata records the methodology. Five-, fifteen-, and thirty-minute bars are deterministically aggregated from one-minute bars (first/max/min/last/sum), grouped by Chicago trading date and underlying contract so a bar cannot cross a contract or session-day boundary.

`Session` supports `ETH`, `RTH`, and overnight-aware `CUSTOM` windows. It converts UTC timestamps with IANA time zones (for example `America/New_York`), so DST is handled by the standard timezone database rather than fixed UTC offsets.

## Execution and risk assumptions

Central specifications define NQ as $20 per index point ($5 per 0.25 tick) and MES as $5 per point ($1.25 per tick). Futures PnL and integer-only risk sizing use these specifications. OANDA requests historical bid, ask, and midpoint candles by default. Longs enter at ask and exit at bid; shorts do the reverse. Midpoint-only metal bars require an explicit synthetic spread and such executions are flagged by the execution model.

OANDA access is market-data only: the provider exposes no order endpoint and validates `XAU_USD` against instruments enabled for the configured account.

The included strategies are moving-average crossover and an initial, timezone-aware Opening Range Breakout signal generator with range window, cutoff, direction, buffer, reward/risk configuration, and daily trade limit parameters.
