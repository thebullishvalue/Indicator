# Trail lab · holdout, run once (2026-11-02T17:38:45+00:00)

Frozen winner: **T126xTS** (freeze commit 62ce3c2, trail_lab.py sha256 d2808fae177a82b7…).

## HB · DEV markets, 2020-01-01 on (119 markets)

| Strategy | Sharpe | t | CAGR | Max DD | Timing SR (t) | Breadth | Turnover/yr |
|---|---|---|---|---|---|---|---|
| T126xTS | +1.21 | +3.70 | +1.9% | -2.5% | +0.72 (+2.2) | 80% | 1.6 |
| TSMOM | +1.13 | +3.39 | +2.2% | -3.5% | +0.56 (+1.7) | 77% | 2.3 |
| T-LS | +0.88 | +2.70 | +3.2% | -5.8% | +0.50 (+1.5) | 70% | 3.0 |
| BH | +0.91 | +2.64 | +26.2% | -56.5% | +nan (+nan) | 98% | 0.1 |
| T126xTS @2x cost | +1.11 | +3.39 | +1.7% | -2.8% | +0.72 (+2.2) | 77% | 1.6 |

Per class (T126xTS): commodity +0.47, crypto +0.29, etf +1.18, fx -0.17, index +0.98, nse_stock +1.02
Per class (TSMOM): commodity +0.17, crypto +0.37, etf +1.18, fx -0.39, index +0.89, nse_stock +0.90

- **Edge** (net Sharpe > 0, t ≥ 2; timing Sharpe > 0, t ≥ 2): **PASS**
- **Improves on TSMOM** (daily difference t ≥ 2): **FAIL** (t -1.12)

## HA · unseen markets, full history (411 markets)

| Strategy | Sharpe | t | CAGR | Max DD | Timing SR (t) | Breadth | Turnover/yr |
|---|---|---|---|---|---|---|---|
| T126xTS | +0.79 | +3.96 | +1.0% | -3.7% | +0.77 (+4.1) | 79% | 0.9 |
| TSMOM | +0.72 | +3.63 | +1.1% | -4.6% | +0.60 (+3.1) | 80% | 1.4 |
| T-LS | +0.60 | +3.02 | +1.6% | -9.3% | +0.51 (+2.5) | 77% | 1.9 |
| BH | +1.25 | +6.26 | +37.5% | -64.4% | +nan (+nan) | 98% | 0.0 |
| T126xTS @2x cost | +0.69 | +3.45 | +0.8% | -3.9% | +0.77 (+4.1) | 76% | 0.9 |

Per class (T126xTS): crypto -0.04, nse_stock +0.84
Per class (TSMOM): crypto +0.07, nse_stock +0.72

- **Edge** (net Sharpe > 0, t ≥ 2; timing Sharpe > 0, t ≥ 2): **PASS**
- **Improves on TSMOM** (daily difference t ≥ 2): **FAIL** (t -0.94)

## Verdict

- **T126xTS has an edge: YES** (needs HA and HB)
- **T126xTS improves on plain TSMOM: NO**
