"""Figures for the implied-correlation & dispersion engine → docs/assets/*.png."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .metrics import vol_target, performance, subperiod_metrics

plt.rcParams.update({"figure.dpi": 130, "savefig.dpi": 130, "axes.grid": True,
                     "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 10, "figure.autolayout": True})
BLUE, RED, GREEN, GREY, ORANGE = "#1f5fa8", "#c0392b", "#27ae60", "#7f8c8d", "#e67e22"
SUBPERIODS = {"2010-2014": ("2010", "2014"), "2015-2019": ("2015", "2019"),
              "2020-2022": ("2020", "2022"), "2023-2026": ("2023", "2026")}


def make_all(res: dict, assets: Path):
    assets = Path(assets); assets.mkdir(parents=True, exist_ok=True)
    df = res["df"]

    # 1 — implied correlation term structure
    fig, ax = plt.subplots(figsize=(10, 4))
    for c, col, lab in [("COR1M", GREY, "1M"), ("COR3M", BLUE, "3M"), ("COR6M", GREEN, "6M")]:
        ax.plot(df.index, df[c], color=col, lw=.8, label=f"implied corr {lab}")
    ax.set_title("CBOE Implied Correlation — Term Structure (spikes = systemic stress)", fontweight="bold")
    ax.set_ylabel("implied correlation"); ax.legend(loc="upper right", fontsize=8)
    fig.savefig(assets / "implied_corr_term_structure.png"); plt.close(fig)

    # 2 — implied vs realized
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df["COR3M"], color=BLUE, lw=.9, label="implied (COR3M)")
    ax.plot(df.index, df["realized"], color=RED, lw=.9, label="realized (sectors, 63d)")
    ax.set_title(f"Implied vs Realized Correlation — they co-move (ρ = {res['lvl_corr']:+.2f})",
                 fontweight="bold"); ax.set_ylabel("correlation"); ax.legend(loc="upper right", fontsize=8)
    fig.savefig(assets / "implied_vs_realized.png"); plt.close(fig)

    # 3 — DSPX dispersion
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.plot(df.index, df["DSPX"], color=ORANGE, lw=.9)
    ax.set_title("Cboe Dispersion Index (DSPX) — high = stocks move idiosyncratically", fontweight="bold")
    ax.set_ylabel("DSPX")
    fig.savefig(assets / "dispersion_index.png"); plt.close(fig)

    # 4 — predictive: COR3M vs forward 21d SPY vol (binned)
    d = df.dropna(subset=["fwd_vol"])
    bins = pd.qcut(d["COR3M"], 5, labels=["Q1 low", "Q2", "Q3", "Q4", "Q5 high"])
    grp = d.groupby(bins, observed=True)["fwd_vol"].mean()
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    ax.bar(range(len(grp)), grp.values, color=BLUE, alpha=.85)
    ax.set_xticks(range(len(grp))); ax.set_xticklabels(grp.index)
    for i, v in enumerate(grp.values): ax.text(i, v + .3, f"{v:.0f}%", ha="center", fontsize=9)
    ax.set_title(f"Implied Correlation Predicts Forward Equity Vol  (corr {res['ic_vol']:+.2f})",
                 fontweight="bold"); ax.set_ylabel("avg forward 21d SPY vol (%)")
    ax.set_xlabel("COR3M quintile")
    fig.savefig(assets / "predictive_power.png"); plt.close(fig)

    # 5 — overlay equity vs buy&hold
    fig, ax = plt.subplots(figsize=(10, 4.4))
    for r, nm, c, w in [(df["spy_ret"], "Buy & Hold SPY", GREY, 1.0),
                        (df["overlay_ret"], "Correlation-regime overlay", BLUE, 1.6)]:
        eq = np.exp(r.cumsum())
        ax.plot(eq.index, (eq - 1) * 100, color=c, lw=w,
                label=f"{nm}  (Sharpe {performance(r)['sharpe']:+.2f}, maxDD {performance(r)['max_dd']:.0%})")
    ax.set_title("Correlation-Regime Defensive Overlay on SPY", fontweight="bold")
    ax.set_ylabel("cumulative return (%)"); ax.legend(loc="upper left", fontsize=9)
    fig.savefig(assets / "overlay_equity.png"); plt.close(fig)

    # 6 — performance table
    rows = {"Buy & Hold SPY": performance(df["spy_ret"]),
            "Correlation overlay": performance(df["overlay_ret"])}
    keys = [("sharpe", "Sharpe", "{:+.2f}"), ("cagr", "CAGR", "{:.1%}"), ("vol", "Vol", "{:.1%}"),
            ("max_dd", "Max DD", "{:.1%}"), ("calmar", "Calmar", "{:+.2f}"), ("hit", "Hit", "{:.0%}")]
    table = [[fmt.format(m.get(k, np.nan)) for k, _, fmt in keys] for m in rows.values()]
    fig, ax = plt.subplots(figsize=(8.5, 1.6)); ax.axis("off")
    t = ax.table(cellText=table, rowLabels=list(rows), colLabels=[l for _, l, _ in keys],
                 cellLoc="center", loc="center")
    t.auto_set_font_size(False); t.set_fontsize(9.5); t.scale(1, 1.5)
    ax.set_title("Defensive Overlay vs Buy & Hold", fontweight="bold", pad=12)
    fig.savefig(assets / "performance_summary_table.png", bbox_inches="tight"); plt.close(fig)
