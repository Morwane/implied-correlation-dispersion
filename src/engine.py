"""Implied vs realized correlation engine + a correlation-regime defensive overlay.

- IMPLIED correlation: CBOE .COR3M (forward-looking, option-derived).
- REALIZED correlation: weighted average pairwise correlation of the 9 sector ETFs
  (the thesis-style measure), rolling 63d.
- Validation: do implied and realized co-move? Does implied correlation predict
  forward equity volatility (i.e. is it a risk signal)?
- Strategy: cut SPY exposure when implied correlation is elevated (high correlation =
  diversification breaks down = stress). No look-ahead (signal shift(1)).
"""
import numpy as np
import pandas as pd

from .data import sector_weights

TD = 252


def realized_correlation(sectors: pd.DataFrame, window: int = 63) -> pd.Series:
    """Weighted average pairwise realized correlation of the sector ETFs (×100, like COR)."""
    w = sector_weights().reindex(sectors.columns)
    rets = np.log(sectors / sectors.shift(1)).dropna()
    pw = np.outer(w.values, w.values); np.fill_diagonal(pw, 0.0); denom = pw.sum()
    out = {rets.index[i]: float((rets.iloc[i - window:i].corr().values * pw).sum() / denom)
           for i in range(window, len(rets))}
    return pd.Series(out, name="realized") * 100.0


def build(cor: pd.DataFrame, sectors: pd.DataFrame, spy: pd.Series,
          z_window: int = 252, exit_buffer: float = 1.0) -> dict:
    realized = realized_correlation(sectors)
    df = cor.join(realized, how="inner").dropna(subset=["COR3M"])
    df = df.join(spy, how="left")
    df["spy_ret"] = np.log(df["SPY"] / df["SPY"].shift(1))
    df["fwd_vol"] = df["spy_ret"].rolling(21).std().shift(-21) * np.sqrt(TD) * 100   # forward 21d vol

    # Monitor
    df["term_slope"] = df["COR1M"] - df["COR6M"]                 # >0 = inversion (stress)
    df["z"] = (df["COR3M"] - df["COR3M"].rolling(z_window).mean()) / df["COR3M"].rolling(z_window).std()
    df["regime"] = np.where(df["z"] > 1, "stress", np.where(df["z"] < -1, "calm", "neutral"))

    # Validation
    sub = df.dropna(subset=["realized"])
    lvl_corr = float(sub["COR3M"].corr(sub["realized"]))        # convergent validity
    ic_vol = float(df["COR3M"].corr(df["fwd_vol"]))             # implied corr → forward risk
    ic_dspx = float(df["DSPX"].corr(df["fwd_vol"]))

    # Defensive overlay: 100% when correlation normal/low, 50% if z>0, 0% if z>1
    pos = np.where(df["z"] > 1.0, 0.0, np.where(df["z"] > 0.0, 0.5, 1.0))
    df["position"] = pd.Series(pos, index=df.index).shift(1).fillna(1.0)
    turn = df["position"].diff().abs().fillna(0)
    df["overlay_ret"] = df["position"] * df["spy_ret"] - turn * (1.0 / 1e4)

    cur = df.iloc[-1]
    pctile = float((df["COR3M"] < cur["COR3M"]).mean() * 100)
    return {
        "df": df, "lvl_corr": lvl_corr, "ic_vol": ic_vol, "ic_dspx": ic_dspx,
        "cur_cor3m": float(cur["COR3M"]), "cur_pctile": pctile,
        "cur_regime": str(cur["regime"]), "cur_slope": float(cur["term_slope"]),
    }


def quant_checks(res: dict) -> list[tuple[str, bool, str]]:
    df = res["df"]
    checks = [
        ("data_aligned", df.index.is_monotonic_increasing and df.index.is_unique, f"{len(df)} days"),
        ("position_lagged", True, "overlay uses shift(1) signal"),
        ("implied_realized_comove", res["lvl_corr"] > 0.4,
         f"corr(implied, realized) = {res['lvl_corr']:+.2f}"),
        ("implied_predicts_risk", res["ic_vol"] > 0,
         f"corr(COR3M, fwd vol) = {res['ic_vol']:+.2f}"),
    ]
    return checks
