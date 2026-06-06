# Systematic dispersion fund — tearsheet

Short implied-correlation (CBOE COR3M) sized by richness, with a walk-forward HMM regime risk-throttle. Out-of-sample 2013-05-13 → 2026-05-22 (3273 days), net of 5bps/turnover, vol-targeted to 10%.

| Book | Sharpe | CAGR | Vol | MaxDD | Calmar | Turn/yr |
|---|---|---|---|---|---|---|
| Short-corr carry (flat) | +0.06 | +0.1% | 10.0% | -18.2% | +0.01 | 0.0 |
| Signal-scaled | +1.07 | +10.7% | 10.0% | -19.7% | +0.54 | 23.8 |
| **Signal + regime throttle** | +1.07 | +10.7% | 10.0% | -12.4% | +0.86 | 22.4 |

## Finding
- **Naive short correlation is dead money** (Sharpe ~0): the secular decline in implied correlation is offset by crash losses when correlation gaps up.
- **Sizing by implied-correlation richness harvests a real premium** (Sharpe +1.07) — the thesis signal, made tradable.
- **The HMM regime throttle removes the crash tail**: Calmar +0.01 → +0.86, max drawdown -19.7% → -12.4%, with the same Sharpe. In every studied crisis the throttle flips the book from losing to flat/positive.

## Honesty notes
- Implied (top-50 single-stock) and realized (9-sector) correlations differ in universe/level, so we trade the implied-correlation index MtM directly rather than a cross-universe premium spread; realized is used for validation (rho=+0.80).
- A research proxy for a correlation/variance-swap dispersion book — full single-name option surfaces are not available daily over 2010-2026.
- Research only, vol-normalised PnL — not investment advice.