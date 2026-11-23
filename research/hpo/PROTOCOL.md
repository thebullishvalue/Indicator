# Pramana hyperparameter optimisation: protocol, declared before any trial

This file fixes, before any trial runs, what is tuned, what each part is judged by, how the data
is split, and when a change is accepted.

## What is tuned, and what is not

Every trial runs Pramana's reference implementation (`research/pramana.py`, the bar-for-bar
port), extended only so the hard-coded constants can be varied. With default settings it must
reproduce `run()` exactly; `hpo_core.py` asserts this.

| Part | Knobs | Default | Objective (lower or higher is better) |
|---|---|---|---|
| **Risk forecast** σ | spans of the three variance EMAs; their blend weights; the clip on the long-run rescale k | 5 / 22 / 252; 0.25 / 0.40 / 0.35; k ∈ [0.5, 2] | **QLIKE** loss of the H-bar variance forecast against the realised variance of the next H bars (sum of squared log returns). Lower is better. |
| **Cone and stops** | learning speed η; adapt to the risk regime (on/off); adapt to the trend state (on/off) | 0.02; on; on | **Interval score** of the H-bar cone at its 80% target: width plus 10 × any miss (α = 0.2). Lower is better. Subject to calibration: coverage within 3 points of 80% in each risk regime, and stop touches within 3 points of 20% on each side. |
| **Exposure** | trend floor; risk power; exposure step; trend lookbacks | 0.5; 1.0; 0.10; 63 / 126 / 252 | **Sharpe uplift**: the median across instruments of the exposure line's net annualised Sharpe minus buy-and-hold's (5 bp per unit change; 10 bp for crypto). Reported beside it: the median ratio of max drawdowns. Higher is better. |

**Not tuned, because they are preferences rather than errors:** the horizon H (10), the cone's
coverage (80%), the stop's touch probability (20%), risk per trade, and max exposure (above 1.0 is
leverage). The ledger's τ has no clean objective here and stays at 0.10. The parts are tuned in the
order above: each later part reads the earlier parts' chosen settings.

**Amendment, made before any candidate was chosen.** The first stage-1 run showed the mean
QLIKE on the tuning years dominated by a few glitched bars: a stale quote followed by a jump puts
a near-zero forecast against a large realised move, and the mean reached 10²⁶⁰. Each point's
realised-to-forecast ratio is now clipped to [0.01, 100] before the loss. The per-instrument median
QLIKE and the mean squared log error are reported beside it as checks.

## Data and splits

| Role | Data |
|---|---|
| **Tune** | Bars dated before 2016-01-01, on the 151 research instruments plus the 572 fresh daily stocks. Hourly: the first half of the dates on the research and fresh hourly sets (risk forecast and cone only; exposure is a daily / weekly rule). |
| **Validate** | Bars dated 2016-01-01 onward on the same instruments (hourly: the second half). |
| **Final test** | The sealed universe: S&P 400, S&P 600 and the Nifty 500 minus the Nifty 200, minus every name above. 1,111 stocks daily, 1,237 hourly. It has never been computed on. Opened once, for the settings that survive validation. |

## Search and acceptance

- **Search.** A grid per part, on the tuning split only. Every grid point's tune and validate
  scores are reported, so how flat each optimum is stays visible.
- **The candidate.** For each part, the grid point with the best tuning score.
- **Validation.** The candidate is kept only if it also beats the default on the validation split,
  on every timeframe that part runs on.
- **Final test.** On the sealed universe, a kept candidate must beat the default again, on the same
  objective and on every timeframe that part runs on.
  - **Ships:** passes validation and the final test.
  - **Reported only:** passes validation but not the final test.
  - **Default stays:** fails validation.
- **One more condition.** A change also has to be large enough to matter: at least 1% lower
  QLIKE, at least 1% lower interval score, or at least +0.02 Sharpe uplift. Smaller differences
  are noise, and the default stays.
