# Implied Correlation & Dispersion — Tearsheet

Period: **2010-04-07 → 2026-05-22** (4051 days).

## Executive summary
A monitor and signal engine built on CBOE implied-correlation indices (.COR1M/3M/6M) and the Cboe Dispersion Index (.DSPX). The implied correlation **co-moves with realized sector correlation (ρ = +0.80)** and **predicts forward equity volatility (corr +0.27)**. A correlation-regime defensive overlay on SPY cuts drawdown from -36% to -22%.

## Current reading (monitor)
- COR3M = **12.1** (1th percentile) — regime: **calm**.
- Term slope (1M−6M) = -2.5.

## Measures
- **Implied** correlation: CBOE .COR3M (option-derived, forward-looking).
- **Realized** correlation: weighted average pairwise correlation of 9 sector ETFs (63d).
- **Dispersion**: .DSPX.

![Term structure](../docs/assets/implied_corr_term_structure.png)
![Implied vs realized](../docs/assets/implied_vs_realized.png)

## Signal validation
- Convergent validity: corr(implied, realized) = **+0.80**.
- Risk prediction: corr(COR3M, forward 21d SPY vol) = **+0.27**; corr(DSPX, fwd vol) = +0.35.

![Predictive power](../docs/assets/predictive_power.png)

## Defensive overlay
Cut SPY exposure as implied correlation rises (z-score of COR3M): 100% normal, 50% if z>0, 0% if z>1.

| Strategy | Sharpe | CAGR | Vol | Max DD | Calmar |
|---|--:|--:|--:|--:|--:|
| Buy & Hold SPY | +0.66 | +10.5% | 17.3% | -36.1% | +0.29 |
| Correlation overlay | +0.53 | +5.2% | 10.5% | -21.6% | +0.24 |

![Overlay equity](../docs/assets/overlay_equity.png)

## Robustness — subperiods
| Period | Sharpe | CAGR | Max DD |
|---|--:|--:|--:|
| 2010-2014 | +0.48 | +5.3% | -16.3% |
| 2015-2019 | +0.18 | +1.1% | -19.0% |
| 2020-2022 | +0.10 | +0.5% | -19.2% |
| 2023-2026 | +1.39 | +16.0% | -9.9% |

## Honest read
The overlay is a **risk reducer**, not a return booster: in a long bull market staying invested wins, so it trades some return for a materially smaller drawdown. The strongest result is the **validation** — implied correlation tracks realized correlation and leads equity volatility, confirming it as a genuine systemic-risk gauge.

## Limitations
- Implied (top-50 single-stock) and realized (9 sectors) correlations differ in universe/level; the comparison is on dynamics.
- Overlay is daily, long-only equity scaling; research only, not investment advice.

## Link to research
This operationalizes a master's thesis on equity-correlation regimes: the realized Correlation Synchronicity Index there is the realized counterpart to CBOE's implied index.