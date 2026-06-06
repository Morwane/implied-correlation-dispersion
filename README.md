# Implied Correlation & Dispersion Engine

> A monitor and signal engine for **equity correlation risk**, built on CBOE implied-correlation indices (`.COR1M/3M/6M`) and the Cboe Dispersion Index (`.DSPX`). It validates implied correlation against realized sector correlation, shows it **leads equity volatility**, and turns it into a defensive overlay. LSEG data, 2010–2026.

![Implied vs realized](docs/assets/implied_vs_realized.png)

## Why this project matters

Diversification relies on assets *not* moving together — but correlation **spikes exactly in crises** (2008, 2020, 2022), precisely when diversification is needed most. The market prices this through **implied correlation**; this engine monitors it, validates it, and uses it as a systemic-risk signal.

It bridges a master's thesis on equity-correlation regimes (which builds a *realized* Correlation Synchronicity Index) with the market's *implied* counterpart.

## Key results (2010–2026)

**Validation — implied correlation is a genuine risk gauge**
- It **co-moves with realized** sector correlation: **ρ = +0.80** (convergent validity).
- It **predicts forward equity volatility**: corr(COR3M, next-21d SPY vol) = **+0.27**; DSPX = **+0.35**.

![Predictive power](docs/assets/predictive_power.png)

**Monitor (current)** — COR3M ≈ 12 (≈ 1st percentile, a record-low / dispersion regime), term structure in contango.

![Term structure](docs/assets/implied_corr_term_structure.png)
![Dispersion index](docs/assets/dispersion_index.png)

**Defensive overlay** — cut SPY exposure as implied correlation rises:

| Strategy | Sharpe | CAGR | Vol | Max DD | Calmar |
|----------|:------:|:----:|:---:|:------:|:------:|
| Buy & Hold SPY | +0.66 | +10.5% | 17.3% | −36.1% | +0.29 |
| Correlation-regime overlay | +0.53 | +5.2% | 10.5% | **−21.6%** | +0.24 |

![Overlay equity](docs/assets/overlay_equity.png)

> **Honest read:** the overlay is a **risk reducer**, not a return booster — in a long bull market, staying invested wins, so it trades some return for a materially smaller drawdown (−36% → −22%). The headline result is the **validation**: implied correlation tracks realized correlation and leads volatility, confirming it as a systemic-risk indicator.

## Method

- **Implied** correlation: CBOE `.COR3M` (option-derived, forward-looking).
- **Realized** correlation: weighted-average pairwise correlation of 9 GICS sector ETFs, rolling 63d (the thesis-style measure).
- **Signal**: z-score of COR3M (252d). Overlay position = 100% (z<0), 50% (0<z<1), 0% (z>1).
- **No look-ahead**: signals `shift(1)`; forward vol used only for *evaluation*, never as a feature.

## Risk controls & robustness

- Look-ahead-free; subperiod robustness across four regime eras; automated `quant_checks` + `pytest` (6 tests).

## Limitations

- Implied (top-50 single-stock) and realized (9-sector) correlations differ in universe and level — the comparison is on **dynamics**, not absolute level.
- Overlay is daily long-only equity scaling. Research only — **not investment advice**.

## Repository structure

```
implied-correlation-dispersion/
├── README.md · LICENSE · requirements.txt
├── data/raw_prices/   # .COR1M/3M/6M, .DSPX, 9 sector ETFs, SPY (LSEG)
├── src/
│   ├── data.py        # load indices + sectors + SPY
│   ├── engine.py      # realized corr, validation, overlay, quant_checks
│   ├── metrics.py     # performance/risk metrics
│   └── plots.py       # figures
├── scripts/
│   ├── run_analysis.py
│   └── generate_report.py
├── tests/test_engine.py
├── docs/assets/
└── reports/tearsheet.md
```

## How to run

```bash
pip install -r requirements.txt
python scripts/run_analysis.py        # monitor + validation + overlay + checks
python scripts/generate_report.py     # figures + tearsheet
pytest -q
```

*Built with Python (pandas, numpy, matplotlib). Data: LSEG / Refinitiv. Operationalizes a master's thesis on equity-correlation regimes.*
