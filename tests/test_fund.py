"""Dispersion fund tests — look-ahead-free + the throttle's drawdown benefit.
Run: pytest -q tests/test_fund.py
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.data import load
from src.metrics import vol_target, performance
from src.strategy import build_panel, signal_size, short_corr_pnl
from src.regime import walk_forward, confirm, CALM, NORMAL, STRESS

DATA = REPO / "data"
THROTTLE = {CALM: 1.0, NORMAL: 1.0, STRESS: 0.0}


@pytest.fixture(scope="module")
def ctx():
    cor, sectors, spy = load(DATA)
    df = build_panel(cor, sectors, spy)
    regime = confirm(walk_forward(df))
    return df, regime


def test_panel_built(ctx):
    df, _ = ctx
    assert {"COR3M", "realized", "z", "idx_rv20"} <= set(df.columns)
    assert len(df) > 2000


def test_validation_corr(ctx):
    df, _ = ctx
    assert df["COR3M"].corr(df["realized"]) > 0.4      # implied & realized co-move


def test_position_is_lagged(ctx):
    df, _ = ctx
    bk = short_corr_pnl(df, signal_size(df["z"]))
    assert bk["net"].isna().iloc[0]                    # size shift(1): no look-ahead


def test_regimes_out_of_sample(ctx):
    df, regime = ctx
    assert regime.index[0] > df.index[0]
    assert set(regime.unique()) <= {CALM, NORMAL, STRESS}


def test_throttle_reduces_drawdown(ctx):
    df, regime = ctx
    size = signal_size(df["z"])
    thr = size * regime.reindex(df.index).ffill().map(THROTTLE)
    valid = short_corr_pnl(df, thr)["net"].dropna().index.intersection(regime.index)
    dd_sig = performance(vol_target(short_corr_pnl(df, size)["net"].loc[valid]))["max_dd"]
    dd_thr = performance(vol_target(short_corr_pnl(df, thr)["net"].loc[valid]))["max_dd"]
    assert dd_thr > dd_sig                              # throttle shrinks max drawdown


def test_throttle_helps_in_covid(ctx):
    df, regime = ctx
    size = signal_size(df["z"])
    thr = size * regime.reindex(df.index).ffill().map(THROTTLE)
    flat = vol_target(short_corr_pnl(df, pd.Series(1.0, index=df.index))["net"]).loc["2020-02":"2020-04"]
    tro = vol_target(short_corr_pnl(df, thr)["net"]).loc["2020-02":"2020-04"]
    assert tro.sum() > flat.sum()                       # throttle beats naive carry in the crash
