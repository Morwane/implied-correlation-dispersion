"""Run the implied-correlation analysis: monitor, validation, overlay, checks.
Usage: python scripts/run_analysis.py"""
import sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from src.data import load
from src.engine import build, quant_checks
from src.metrics import performance

DATA = REPO / "data"


def main():
    cor, sectors, spy = load(DATA)
    res = build(cor, sectors, spy)
    df = res["df"]
    print("=" * 74)
    print("IMPLIED CORRELATION & DISPERSION")
    print(f"Period: {df.index[0].date()} → {df.index[-1].date()} ({len(df)} days)")
    print("-" * 74)
    print("MONITOR")
    print(f"  COR3M = {res['cur_cor3m']:.1f}  ({res['cur_pctile']:.0f}th pctile) | "
          f"regime: {res['cur_regime']} | term slope (1M-6M): {res['cur_slope']:+.1f}")
    print("VALIDATION")
    print(f"  corr(implied COR3M, realized sector corr) = {res['lvl_corr']:+.2f}  (convergent validity)")
    print(f"  corr(COR3M, forward 21d SPY vol)          = {res['ic_vol']:+.2f}  (risk predictor)")
    print(f"  corr(DSPX,  forward 21d SPY vol)          = {res['ic_dspx']:+.2f}")
    print("OVERLAY (defensive)")
    for nm, r in [("Buy & Hold SPY", df["spy_ret"]), ("Correlation overlay", df["overlay_ret"])]:
        m = performance(r)
        print(f"  {nm:22} Sharpe {m['sharpe']:+.2f} | CAGR {m['cagr']:+.1%} | "
              f"vol {m['vol']:.1%} | maxDD {m['max_dd']:.1%}")
    print("-" * 74)
    ok = True
    for name, passed, detail in quant_checks(res):
        ok &= passed
        print(f"  [{'PASS' if passed else 'FAIL'}] {name:26} — {detail}")
    print("=" * 74); print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    df[["COR1M", "COR3M", "COR6M", "DSPX", "realized", "z", "regime",
        "position", "overlay_ret"]].to_csv(DATA / "results.csv")


if __name__ == "__main__":
    main()
