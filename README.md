# Alpaca Backtesting MCP

A production-oriented, **read-only** Python 3.12 MCP server for validated Alpaca historical data and deterministic backtests. It exposes Streamable HTTP at `/mcp`. It contains no order, position-closing, transfer, or liquidation tool. The only use of Alpaca's trading client is the read-only asset metadata lookup.

## Architecture and security boundary

```text
ChatGPT / MCP client -> FastMCP /mcp -> tool service -> provider interface -> Alpaca APIs
                                             `-> strategy -> backtest engine
```

The backtester depends on `MarketDataProvider`, not Alpaca. CSV, Polygon, Databento, or IB providers can therefore be added without changing the engine. Strategies implement a small close-derived signal interface. Credentials are read only from environment variables, are never returned, and are not logged. Do not commit `.env`; rotate any credential accidentally disclosed. Paper mode defaults to true, although historical data does not execute trades.

## Installation and local operation

1. Create Alpaca API credentials in the Alpaca dashboard. Data entitlements and feed availability depend on the account.
2. Install Python 3.12+, then:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev]'
   cp .env.example .env
   ```

3. Export the values (the application deliberately does not auto-load `.env`):

   ```bash
   export ALPACA_API_KEY='...'
   export ALPACA_SECRET_KEY='...'
   export ALPACA_PAPER_TRADE=true
   export PORT=8000
   python -m app.server
   ```

The endpoint is `http://localhost:8000/mcp`; `/health` is a credential-free liveness endpoint. A GET in a browser is not a complete MCP exchange; use a Streamable HTTP MCP client.

### Environment variables

| Name | Required | Default | Meaning |
|---|---:|---|---|
| `ALPACA_API_KEY` | Yes for Alpaca calls | none | Alpaca key ID |
| `ALPACA_SECRET_KEY` | Yes for Alpaca calls | none | Alpaca secret |
| `ALPACA_PAPER_TRADE` | No | `true` | Select paper endpoint for read-only asset metadata |
| `PORT` | No | `8000` | HTTP listen port; host is always `0.0.0.0` |
| `LOG_LEVEL` | No | `INFO` | Python log level |

## Tools and example requests

Tools return plain JSON-compatible values:

* `get_supported_timeframes()` supports `1Min`, `5Min`, `15Min`, `30Min`, `1Hour`, and `1Day`.
* `get_market_data(symbol, timeframe, start, end, feed?, adjustment?, limit?)` returns ascending normalized `timestamp/open/high/low/close/volume/symbol` bars. `limit` is 1–10,000.
* `get_asset_info(symbol)` returns a safe subset of asset metadata.
* `run_backtest(...)` fetches bars and runs the moving-average crossover.

Illustrative MCP tool arguments:

```json
{"symbol":"AAPL","timeframe":"1Day","start":"2024-01-01T00:00:00Z","end":"2025-01-01T00:00:00Z","adjustment":"raw","limit":500}
```

```json
{
  "symbol":"AAPL", "timeframe":"1Day",
  "start":"2020-01-01T00:00:00Z", "end":"2025-01-01T00:00:00Z",
  "initial_capital":100000, "risk_per_trade":0.25,
  "commission":0, "slippage":0.0001,
  "strategy":{"name":"moving_average_crossover","fast_ma":20,"slow_ma":50}
}
```

In ChatGPT, add a custom remote MCP connector (availability depends on the ChatGPT plan/workspace), enter the HTTPS `/mcp` URL, and complete the connector prompts. Keep the server private or add an authenticated reverse proxy before exposing sensitive data entitlements; V1 does not implement client authentication.

## Backtesting and execution assumptions

* A strategy sees a completed candle and emits its signal at that candle's close. The engine fills at the **next candle open**, preventing same-bar look-ahead. A last-bar signal cannot fill.
* A remaining position is deterministically marked and liquidated at the final close with reason `end_of_data`.
* `slippage` is a decimal fraction of price (for example `0.0001` is 1 basis point) applied adversely: buys higher and sells lower.
* `commission` is a fixed cash amount **per order**, charged at both entry and exit.
* Because MA crossover has no stop distance, `risk_per_trade` is honestly treated as percentage-of-current-equity **exposure**, in `(0, 1]`; it is not claimed to be stop-risk. `PositionSizer` permits future stop/ATR/fixed sizing.
* Equity is marked at each bar close. Drawdown uses prior equity peaks. Sharpe is an unadjusted bar-return Sharpe annualized by `sqrt(252)`; it is most meaningful for daily bars.
* Missing candles are not invented. Bars must be strictly ascending, unique, valid OHLC, and nonnegative-volume.

## Docker

```bash
docker build -t alpaca-backtesting-mcp .
docker run --rm -p 8000:8000 \
  -e ALPACA_API_KEY='...' -e ALPACA_SECRET_KEY='...' \
  alpaca-backtesting-mcp
```

## Render deployment

1. Push this repository to a private Git host.
2. In Render, select **New > Blueprint** and connect the repository; `render.yaml` selects Docker.
3. Enter `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` as secret environment values when prompted. Never put their values in the YAML.
4. Deploy. Render supplies `PORT`; the process binds `0.0.0.0:$PORT`.
5. Configure the MCP client with `https://my-alpaca-mcp.onrender.com/mcp` (replace the hostname).
6. Add an authenticated gateway or Render access control before production exposure.

## Tests

`pytest` uses synthetic bars and needs no credentials. `ruff check .` and `mypy app` provide static checks.

## Known limitations

V1 is single-symbol and long-only, requests at most 10,000 bars, and has no pagination, cache, corporate-action model beyond Alpaca's requested adjustment, dividend handling, calendar gap classification, benchmark, portfolio backtest, walk-forward analysis, client authentication, or optimizer. Results inherit Alpaca data quality and survivorship selection: asking for today's symbols does not create a survivorship-bias-free historical universe. Crypto support uses symbols such as `BTC/USD`; asset metadata is primarily intended for Alpaca assets. Optimization is intentionally omitted rather than implying in-sample results predict future returns.

This software is research infrastructure, not investment advice. Backtests are hypothetical and do not predict future returns.
