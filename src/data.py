"""Data loading: CBOE implied-correlation indices, dispersion index, sector ETFs, SPY.

.COR1M/.COR3M/.COR6M = Cboe S&P 500 Implied Correlation term structure (0-100 = corr %).
.DSPX = Cboe S&P 500 Dispersion Index. Sector ETFs = realized-correlation universe.
"""
from pathlib import Path
import pandas as pd

COR = ["COR1M", "COR3M", "COR6M", "DSPX"]
# 9 usable GICS sector ETFs (XLC/XLRE excluded — short/incomplete history) + weights
SECTORS = {"XLK": .32, "XLF": .13, "XLY": .11, "XLV": .10, "XLI": .09,
           "XLP": .06, "XLE": .04, "XLU": .025, "XLB": .02}


def _load(raw: Path, name: str) -> pd.Series:
    s = pd.read_csv(raw / f"{name}.csv", parse_dates=["Date"], index_col="Date").iloc[:, 0]
    return s.astype(float).sort_index()


def load(data_dir: Path):
    """Returns (cor_df, sector_df, spy)."""
    raw = Path(data_dir) / "raw_prices"
    cor = pd.concat({c: _load(raw, c) for c in COR}, axis=1)
    sectors = pd.concat({s: _load(raw, s) for s in SECTORS}, axis=1).dropna()
    spy = _load(raw, "SPY").rename("SPY")
    return cor, sectors, spy


def sector_weights() -> pd.Series:
    w = pd.Series(SECTORS)
    return w / w.sum()
