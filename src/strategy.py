"""Systematic dispersion strategy — harvest the implied-correlation risk premium.

A dispersion trade is structurally SHORT correlation (short index vol / long the
components). It earns a premium because index options are dear (investors overpay
for correlation as crash insurance), but it suffers when correlation spikes to 1 in
a crisis — picking up pennies in front of a steamroller.

We CANNOT mark a clean cross-universe premium: CBOE implied correlation is built on
the top-50 single stocks, while our realized correlation is the 9 sector ETFs — they
live on different universes/levels, so (implied - realized) is not a tradable spread
(only the *dynamics* co-move, rho = +0.80). So we trade the tradable thing directly:
the mark-to-market of a SHORT position in the implied-correlation index,

    gross_t = size[t-1] * ( -(rho_imp[t] - rho_imp[t-1]) ) / 100   # COR in 0-100 pts

This captures the realised payoff of shorting correlation — the secular decline and
mean-reversion from rich levels — while taking the crash risk when correlation gaps
up. Size leans into richness (z of COR3M); the regime throttle cuts it in stress.
Realized correlation is retained for validation and as a regime feature.
"""
import numpy as np
import pandas as pd

from .engine import realized_correlation

TD = 252


def build_panel(cor: pd.DataFrame, sectors: pd.DataFrame, spy: pd.Series,
                z_window: int = 252) -> pd.DataFrame:
    """Aligned daily panel with implied/realized correlation, richness z, vol."""
    realized = realized_correlation(sectors)
    df = cor.join(realized, how="inner").dropna(subset=["COR3M"])
    df = df.join(spy, how="left")
    df["spy_ret"] = np.log(df["SPY"] / df["SPY"].shift(1))
    df["idx_rv20"] = df["spy_ret"].rolling(20).std() * np.sqrt(TD) * 100
    df["term_slope"] = df["COR1M"] - df["COR6M"]                  # >0 inversion (stress)
    df["cor3m_chg5"] = df["COR3M"].diff(5)
    mu = df["COR3M"].rolling(z_window).mean()
    sd = df["COR3M"].rolling(z_window).std()
    df["z"] = (df["COR3M"] - mu) / sd                            # richness of implied corr
    return df


def signal_size(z: pd.Series, base: float = 0.5, slope: float = 0.5,
                cap: float = 1.5) -> pd.Series:
    """Short-correlation size: lean in when implied correlation is rich (high z)."""
    return (base + slope * z).clip(lower=0.0, upper=cap)


def short_corr_pnl(df: pd.DataFrame, size: pd.Series,
                   cost_per_turnover: float = 5e-4) -> dict:
    """Daily P&L of a short implied-correlation (dispersion) book, net of costs."""
    rho_imp = df["COR3M"]
    s = size.reindex(df.index).shift(1)                          # decide on prior info
    gross = s * (-(rho_imp - rho_imp.shift(1))) / 100.0          # short correlation MtM
    turnover = s.diff().abs()
    net = gross - turnover * cost_per_turnover
    first = s.dropna().index[0]
    net.loc[:first] = np.nan
    return {"gross": gross.rename("disp_gross"), "net": net.rename("disp_net"),
            "size": s, "turnover": turnover,
            "avg_turnover_annual": float(turnover.dropna().mean() * TD)}
