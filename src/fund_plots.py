"""Figures for the systematic dispersion fund → docs/assets/fund_*.png."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.metrics import vol_target, performance
from src.regime import CALM, NORMAL, STRESS

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10,
                     "figure.autolayout": True})
BLUE, RED, GREEN, GREY, ORANGE = "#1f5fa8", "#c0392b", "#27ae60", "#7f8c8d", "#e67e22"
REG_COLOR = {CALM: "#27ae60", NORMAL: "#f1c40f", STRESS: "#c0392b"}


def _bands(ax, regime):
    reg = regime.dropna()
    for code, color in REG_COLOR.items():
        ax.fill_between(reg.index, 0, 1, where=(reg == code).values,
                        transform=ax.get_xaxis_transform(), color=color,
                        alpha=0.12, step="post", lw=0)


def make_fund_figures(df, regime, returns: dict, size_thr, stress_periods, assets: Path):
    assets = Path(assets); assets.mkdir(parents=True, exist_ok=True)
    valid = next(iter(returns.values())).index

    # 1 — implied correlation index with regime shading
    fig, ax = plt.subplots(figsize=(11, 4.0))
    c = df["COR3M"].reindex(regime.index)
    ax.plot(c.index, c.values, color="black", lw=0.9, label="COR3M (implied correlation)")
    _bands(ax, regime)
    ax.set_title("CBOE implied correlation (COR3M) with HMM regimes "
                 "(green calm · yellow normal · red stress)", fontweight="bold")
    ax.set_ylabel("implied correlation"); ax.legend(loc="upper right", fontsize=8)
    fig.savefig(assets / "fund_implied_corr_regimes.png"); plt.close(fig)

    # 2 — cumulative PnL of the three books
    styling = {"Short-corr carry (flat)": (GREY, 1.0),
               "Signal-scaled": (ORANGE, 1.2),
               "Signal + regime throttle": (GREEN, 1.9)}
    fig, ax = plt.subplots(figsize=(11, 4.6))
    for nm, (col, lw) in styling.items():
        if nm not in returns:
            continue
        eq = (1 + returns[nm]).cumprod()
        ax.plot(eq.index, (eq - 1) * 100, color=col, lw=lw,
                label=f"{nm}  (Sharpe {performance(returns[nm])['sharpe']:+.2f})")
    ax.set_title("Dispersion fund — cumulative return (vol-targeted 10%, net of costs)",
                 fontweight="bold")
    ax.set_ylabel("cumulative return (%)"); ax.legend(loc="upper left", fontsize=8.5)
    fig.savefig(assets / "fund_cumulative_pnl.png"); plt.close(fig)

    # 3 — drawdown: signal vs signal+throttle
    fig, ax = plt.subplots(figsize=(11, 3.4))
    for nm, col, lw in [("Signal-scaled", ORANGE, 1.3),
                        ("Signal + regime throttle", GREEN, 1.7)]:
        eq = (1 + returns[nm]).cumprod(); dd = (eq / eq.cummax() - 1) * 100
        ax.plot(dd.index, dd, color=col, lw=lw, label=nm)
    ax.set_title("Drawdown — the regime throttle cuts the short-correlation crash tail",
                 fontweight="bold")
    ax.set_ylabel("drawdown (%)"); ax.legend(loc="lower left", fontsize=8.5)
    fig.savefig(assets / "fund_drawdown.png"); plt.close(fig)

    # 4 — the tail test: crisis Sharpe, flat vs throttle
    labels, flat_s, thr_s = [], [], []
    for label, (a, b) in stress_periods.items():
        f = performance(vol_target(returns["Short-corr carry (flat)"]).loc[a:b])
        t = performance(vol_target(returns["Signal + regime throttle"]).loc[a:b])
        labels.append(label); flat_s.append(f.get("sharpe", np.nan)); thr_s.append(t.get("sharpe", np.nan))
    x = np.arange(len(labels)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(x - w/2, flat_s, w, color=GREY, label="naive carry")
    ax.bar(x + w/2, thr_s, w, color=GREEN, label="+ regime throttle")
    ax.axhline(0, color="black", lw=.7)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_title("The tail test — crisis Sharpe: throttle flips losses to gains",
                 fontweight="bold")
    ax.set_ylabel("Sharpe (period)"); ax.legend(fontsize=9)
    fig.savefig(assets / "fund_tail_test.png"); plt.close(fig)

    # 5 — rolling 1y Sharpe
    fig, ax = plt.subplots(figsize=(11, 3.2))
    for nm, col in [("Signal-scaled", ORANGE), ("Signal + regime throttle", GREEN)]:
        r = returns[nm]; rs = r.rolling(252).mean() / r.rolling(252).std() * np.sqrt(252)
        ax.plot(rs.index, rs, color=col, lw=1.2, label=nm)
    ax.axhline(0, color="black", lw=.7)
    ax.set_title("Rolling 1y Sharpe", fontweight="bold")
    ax.set_ylabel("Sharpe"); ax.legend(loc="upper left", fontsize=8.5)
    fig.savefig(assets / "fund_rolling_sharpe.png"); plt.close(fig)

    # 6 — performance table
    keys = [("sharpe", "Sharpe", "{:+.2f}"), ("cagr", "CAGR", "{:.1%}"),
            ("vol", "Vol", "{:.1%}"), ("max_dd", "Max DD", "{:.1%}"),
            ("calmar", "Calmar", "{:+.2f}"), ("hit", "Hit", "{:.0%}")]
    rows = {nm: performance(r) for nm, r in returns.items()}
    table = [[fmt.format(m.get(k, np.nan)) for k, _, fmt in keys] for m in rows.values()]
    fig, ax = plt.subplots(figsize=(10, 2.2)); ax.axis("off")
    t = ax.table(cellText=table, rowLabels=list(rows),
                 colLabels=[l for _, l, _ in keys], cellLoc="center", loc="center")
    t.auto_set_font_size(False); t.set_fontsize(9.5); t.scale(1, 1.5)
    ax.set_title("Dispersion fund — performance summary (vol-targeted 10%)",
                 fontweight="bold", pad=14)
    fig.savefig(assets / "fund_performance_table.png", bbox_inches="tight"); plt.close(fig)
