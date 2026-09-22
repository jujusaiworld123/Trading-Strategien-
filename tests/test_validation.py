from dataclasses import replace

import pytest

from app.providers.base import validate_bars
from conftest import make_bars


def test_rejects_duplicates_and_invalid_ohlc() -> None:
    bars = make_bars([2, 3])
    with pytest.raises(ValueError, match="duplicate"):
        validate_bars([bars[0], replace(bars[1], timestamp=bars[0].timestamp)])
    with pytest.raises(ValueError, match="OHLC"):
        validate_bars([replace(bars[0], low=3)])
