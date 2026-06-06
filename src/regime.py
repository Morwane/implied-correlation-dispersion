"""Compact walk-forward Gaussian HMM regime detector for the dispersion book.

Same look-ahead-free recipe as the multi-strategy regime overlay, specialised to
correlation/vol features: refit on an expanding past-only window, standardise on
the train window only, decode causally, and relabel states to fixed economic codes
(0 calm, 1 normal, 2 stress) from emission means so labels are stable across refits.

The stress flag is used to THROTTLE the short-correlation book before correlation
gaps to 1 — the strategy's tail risk.
"""
import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

CALM, NORMAL, STRESS = 0, 1, 2
FEATURES = ["idx_rv20", "COR3M", "cor3m_chg5", "term_slope"]


def _label_map(model: GaussianHMM, cols: list[str]) -> dict[int, int]:
    means = pd.DataFrame(model.means_, columns=cols)
    z = (means - means.mean()) / means.std(ddof=0).replace(0, 1.0)
    score = z.get("idx_rv20", 0) + z.get("COR3M", 0) + z.get("cor3m_chg5", 0) + z.get("term_slope", 0)
    order = score.sort_values().index.tolist()
    codes = [CALM, NORMAL, STRESS]
    return {raw: codes[rank] for rank, raw in enumerate(order)}


def walk_forward(df: pd.DataFrame, n_states: int = 3, train_min: int = 756,
                 refit_every: int = 63, decode_window: int = 504, seed: int = 42) -> pd.Series:
    X = df[FEATURES].dropna()
    idx = X.index
    out = pd.Series(index=idx, dtype="float")
    model = None
    label_map: dict[int, int] = {}
    mu = sd = None
    for i in range(train_min, len(idx)):
        if model is None or (i - train_min) % refit_every == 0:
            train = X.iloc[:i]
            mu, sd = train.mean(), train.std(ddof=0).replace(0, 1.0)
            model = GaussianHMM(n_components=n_states, covariance_type="full",
                                n_iter=200, tol=1e-3, random_state=seed)
            model.fit(((train - mu) / sd).values)
            label_map = _label_map(model, FEATURES)
        lo = max(0, i - decode_window + 1)
        Z = ((X.iloc[lo:i + 1] - mu) / sd).values
        out.iloc[i] = label_map[model.predict(Z)[-1]]
    return out.dropna().rename("regime")


def confirm(regime: pd.Series, min_hold: int = 10) -> pd.Series:
    """Minimum-holding hysteresis to damp whipsaw in the throttle."""
    out = regime.copy()
    cur, hold = regime.iloc[0], 0
    for i, r in enumerate(regime.values):
        if i and (r != cur and hold >= min_hold):
            cur, hold = r, 0
        else:
            hold += 1
        out.iloc[i] = cur
    return out
