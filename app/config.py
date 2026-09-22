"""Environment-only application configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    alpaca_api_key: str | None
    alpaca_secret_key: str | None
    paper_trade: bool
    host: str
    port: int
    log_level: str
    max_bars: int = 10_000

    @classmethod
    def from_env(cls) -> "Settings":
        try:
            port = int(os.getenv("PORT", "8000"))
        except ValueError as exc:
            raise ValueError("PORT must be an integer") from exc
        if not 1 <= port <= 65535:
            raise ValueError("PORT must be between 1 and 65535")
        return cls(
            alpaca_api_key=os.getenv("ALPACA_API_KEY") or None,
            alpaca_secret_key=os.getenv("ALPACA_SECRET_KEY") or None,
            paper_trade=os.getenv("ALPACA_PAPER_TRADE", "true").lower() in {"1", "true", "yes"},
            host="0.0.0.0",
            port=port,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

