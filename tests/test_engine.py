"""Unit tests — run with: pytest -q"""
import sys
from pathlib import Path
import numpy as np
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.data import load, sector_weights
from src.engine import build, realized_correlation, quant_checks

DATA = REPO / "data"


@pytest.fixture(scope="module")
def loaded():
    return load(DATA)


@pytest.fixture(scope="module")
def res(loaded):
    cor, sectors, spy = loaded
    return build(cor, sectors, spy)


def test_weights_normalized():
    assert np.isclose(sector_weights().sum(), 1.0)


def test_realized_in_range(loaded):
    _, sectors, _ = loaded
    rc = realized_correlation(sectors).dropna()
    assert (rc >= -100).all() and (rc <= 100).all()
    assert 0 < rc.mean() < 100        # sectors are positively correlated on average


def test_implied_realized_comove(res):
    # the core validation: implied tracks realized
    assert res["lvl_corr"] > 0.4


def test_implied_predicts_vol(res):
    # implied correlation should lead equity volatility (positive)
    assert res["ic_vol"] > 0


def test_overlay_reduces_drawdown(res):
    from src.metrics import performance
    df = res["df"]
    bh = performance(df["spy_ret"])["max_dd"]
    ov = performance(df["overlay_ret"])["max_dd"]
    assert ov >= bh                   # overlay drawdown is shallower (less negative)


def test_all_quant_checks_pass(res):
    assert all(p for _, p, _ in quant_checks(res))
