from __future__ import annotations
import re
from app.models import SymbolResolution
from .base import MarketDataProvider, ProviderError

FUTURE_ALIASES = {"NQ": "NQ", "NQ1!": "NQ", "NQ FRONT": "NQ", "NASDAQ FUTURES": "NQ", "MES": "MES", "MES1!": "MES", "MES FRONT": "MES"}
METAL_ALIASES = {"XAUUSD": "XAU_USD", "XAU/USD": "XAU_USD", "XAU_USD": "XAU_USD", "GOLD": "XAU_USD"}
CONTRACT = re.compile(r"^(NQ|MES)[FGHJKMNQUVXZ]\d{1,2}$")


class MarketDataRouter:
    def __init__(self, providers: dict[str, MarketDataProvider]):
        self.providers = providers

    def resolve(self, symbol: str, provider: str = "auto", *, continuous: bool = True, contract: str | None = None) -> SymbolResolution:
        requested, key = symbol, " ".join(symbol.strip().upper().split())
        if contract:
            key, continuous = contract.upper(), False
        if key in METAL_ALIASES:
            resolved = SymbolResolution(requested, "XAU_USD", "XAU_USD", "oanda")
        elif key in FUTURE_ALIASES:
            root = FUTURE_ALIASES[key]
            # Databento continuous symbology: rank 0, calendar method (.c.0).
            resolved = SymbolResolution(requested, root, f"{root}.c.0" if continuous else root, "databento", continuous)
        elif CONTRACT.fullmatch(key):
            resolved = SymbolResolution(requested, key, key, "databento", False)
        elif re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", key):
            resolved = SymbolResolution(requested, key, key, "alpaca")
        else:
            raise ProviderError(f"Unknown or ambiguous symbol: {requested!r}")
        if provider != "auto" and provider.lower() != resolved.provider:
            raise ProviderError(f"{requested!r} routes to {resolved.provider}, not {provider}")
        if resolved.provider not in self.providers:
            raise ProviderError(f"Provider {resolved.provider} is not configured")
        return resolved

    def get_bars(self, symbol: str, timeframe: str, start: str, end: str, provider: str = "auto", **kwargs):
        resolution = self.resolve(symbol, provider, continuous=kwargs.pop("continuous", True), contract=kwargs.pop("contract", None))
        bars = self.providers[resolution.provider].get_bars(resolution.provider_symbol, timeframe, start, end, **kwargs)
        bars.attrs.update(requested_symbol=resolution.requested_symbol, normalized_symbol=resolution.normalized_symbol, provider_symbol=resolution.provider_symbol, continuous=resolution.continuous)
        return bars
