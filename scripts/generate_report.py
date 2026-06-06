"""Generate figures + tearsheet.  Usage: python scripts/generate_report.py"""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.data import load
from src.engine import build
from src.metrics import performance, subperiod_metrics
from src.plots import make_all, SUBPERIODS

DATA, ASSETS, REPORTS = REPO / "data", REPO / "docs" / "assets", REPO / "reports"


def main():
    cor, sectors, spy = load(DATA)
    res = build(cor, sectors, spy)
    make_all(res, ASSETS)
    print(f"Figures → {ASSETS}")
    df = res["df"]
    bh, ov = performance(df["spy_ret"]), performance(df["overlay_ret"])
    sp = subperiod_metrics(df["overlay_ret"], SUBPERIODS)

    L = [
        "# Implied Correlation & Dispersion — Tearsheet", "",
        f"Period: **{df.index[0].date()} → {df.index[-1].date()}** ({len(df)} days).", "",
        "## Executive summary",
        f"A monitor and signal engine built on CBOE implied-correlation indices (.COR1M/3M/6M) and "
        f"the Cboe Dispersion Index (.DSPX). The implied correlation **co-moves with realized sector "
        f"correlation (ρ = {res['lvl_corr']:+.2f})** and **predicts forward equity volatility "
        f"(corr {res['ic_vol']:+.2f})**. A correlation-regime defensive overlay on SPY cuts drawdown "
        f"from {bh['max_dd']:.0%} to {ov['max_dd']:.0%}.", "",
        "## Current reading (monitor)",
        f"- COR3M = **{res['cur_cor3m']:.1f}** ({res['cur_pctile']:.0f}th percentile) — regime: **{res['cur_regime']}**.",
        f"- Term slope (1M−6M) = {res['cur_slope']:+.1f}.", "",
        "## Measures",
        "- **Implied** correlation: CBOE .COR3M (option-derived, forward-looking).",
        "- **Realized** correlation: weighted average pairwise correlation of 9 sector ETFs (63d).",
        "- **Dispersion**: .DSPX.", "",
        "![Term structure](../docs/assets/implied_corr_term_structure.png)",
        "![Implied vs realized](../docs/assets/implied_vs_realized.png)", "",
        "## Signal validation",
        f"- Convergent validity: corr(implied, realized) = **{res['lvl_corr']:+.2f}**.",
        f"- Risk prediction: corr(COR3M, forward 21d SPY vol) = **{res['ic_vol']:+.2f}**; "
        f"corr(DSPX, fwd vol) = {res['ic_dspx']:+.2f}.", "",
        "![Predictive power](../docs/assets/predictive_power.png)", "",
        "## Defensive overlay",
        "Cut SPY exposure as implied correlation rises (z-score of COR3M): 100% normal, 50% if z>0, 0% if z>1.",
        "", "| Strategy | Sharpe | CAGR | Vol | Max DD | Calmar |",
        "|---|--:|--:|--:|--:|--:|",
        f"| Buy & Hold SPY | {bh['sharpe']:+.2f} | {bh['cagr']:+.1%} | {bh['vol']:.1%} | {bh['max_dd']:.1%} | {bh['calmar']:+.2f} |",
        f"| Correlation overlay | {ov['sharpe']:+.2f} | {ov['cagr']:+.1%} | {ov['vol']:.1%} | {ov['max_dd']:.1%} | {ov['calmar']:+.2f} |",
        "", "![Overlay equity](../docs/assets/overlay_equity.png)", "",
        "## Robustness — subperiods", "| Period | Sharpe | CAGR | Max DD |", "|---|--:|--:|--:|",
    ]
    for p, row in sp.iterrows():
        L.append(f"| {p} | {row['sharpe']:+.2f} | {row['cagr']:+.1%} | {row['max_dd']:.1%} |")
    L += ["", "## Honest read",
          "The overlay is a **risk reducer**, not a return booster: in a long bull market staying "
          "invested wins, so it trades some return for a materially smaller drawdown. The strongest "
          "result is the **validation** — implied correlation tracks realized correlation and leads "
          "equity volatility, confirming it as a genuine systemic-risk gauge.",
          "", "## Limitations",
          "- Implied (top-50 single-stock) and realized (9 sectors) correlations differ in universe/level; "
          "the comparison is on dynamics.",
          "- Overlay is daily, long-only equity scaling; research only, not investment advice.",
          "", "## Link to research",
          "This operationalizes a master's thesis on equity-correlation regimes: the realized "
          "Correlation Synchronicity Index there is the realized counterpart to CBOE's implied index."]
    (REPORTS / "tearsheet.md").write_text("\n".join(L), encoding="utf-8")
    print(f"Tearsheet → {REPORTS / 'tearsheet.md'}")


if __name__ == "__main__":
    main()
