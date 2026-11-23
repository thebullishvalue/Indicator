# Anumaan hyperparameter optimisation: results

**Verdict: every default stays.** Three parts were tuned under the protocol in `PROTOCOL.md`: the risk
forecast, the cone and stops, and the exposure rule. None produced a change that both cleared the materiality
bar out of sample and kept Anumaan's calibration promises. The one candidate that passed validation did worse
on the sealed universe: its stops drift in trends and its hourly regime coverage slips outside tolerance. It
is reported here and does not ship.

All numbers below are medians or pooled means over 723 daily and 746 hourly instruments (research plus
fresh). Tuning data runs to 2015 on daily bars and covers the first half of the dates on hourly bars;
validation is the rest. The final test used the sealed universe, opened once: 1,111 daily and 1,237 hourly
stocks.

## 1. Risk forecast: the default stays

| | Tuning, daily | Validation, daily | Tuning, hourly | Validation, hourly |
|---|---|---|---|---|
| Default (5/22/252, 0.25/0.40/0.35, k ∈ [0.5, 2]) | 1.000 | 1.000 | 1.000 | 1.000 |
| Candidate (10/44/252, 0.3/0.2/0.5, k ∈ [0.25, 4]) | 1.000 | 1.0045 (worse) | 0.967 | 0.958 |

The table shows QLIKE relative to the default; lower is better. The candidate is the best of 3,618 configs by
mean tuning score over the two timeframes. It fails the rule that a change must be 1% better on every
timeframe it runs on: it is 0.45% worse on daily validation.

- **Daily is flat.** 999 of the 3,618 configs sit within 1% of the default on tuning. The best daily
  validation anywhere in the grid is 1.6% better.
- **Hourly wants a longer memory.** On hourly bars the long EMA's weight should be about 0.5 rather than 0.35;
  that is worth 4% to 6.6% QLIKE out of sample. A per-timeframe blend is the one lead worth pursuing, under a
  new, declared test.

**Amendment.** The first run's mean QLIKE was wrecked by a few glitched bars (it reached 10²⁶⁰). The
realised-to-forecast ratio is now clipped to [0.01, 100], declared in `PROTOCOL.md` before any candidate was
chosen.

## 2. Cone and stops: the default stays (the candidate is reported only)

The grid covers learning speed η ∈ {0.005 … 0.05} × regime adaptation on or off × trend adaptation on or off,
24 configs in all.

| | Interval score, validation, daily / hourly | Worst regime coverage error, validation | Short stop in downtrends, daily (target 20%) |
|---|---|---|---|
| Default (η 0.02, regimes on, trend on) | 1.000 / 1.000 | 0.6 / 0.3 points | 20.5% (research), 20.9% (fresh) |
| Candidate (η 0.02, regimes on, trend **off**) | 0.983 / 0.982 | 0.7 / 0.4 points | 26.8% (research), 28.9% (fresh) |
| Candidate, sealed universe | 0.985 / 0.984 | 2.4 / **3.2** points | **27.5%** daily, 24.7% hourly |

Under the protocol's declared checks the candidate passed validation. On the sealed universe it beat the
default's interval score again, but its hourly regime coverage error of 3.2 points breaks the 3-point
tolerance. **Verdict: reported only.**

- **Regime adaptation is load-bearing.** Every config with it off misses 80% coverage by 4 to 8 points in some
  risk regime.
- **Trend adaptation trades sharpness for honest stops.** Turning it off narrows the cone by about 1.7%, but
  the stops stop meaning what they say in trends.
  - In downtrends, the short stop is touched 27 to 29% of the time instead of 20%, and upside misses rise to 13
    to 14% instead of 10%.
  - In uptrends, the long stop is touched 22 to 24% of the time.
  - With trend adaptation on, every side in every trend state stays within 1 point of target.

  The pooled interval score cannot see this. Anumaan's stops are its product, so the trend term stays.
- **A slower η scores better, but warms up too slowly.** η ≤ 0.015 has a better interval score but breaks
  regime calibration on the tuning split (3.5 to 5 points). Among configs calibrated in every trend state,
  η = 0.015 gains less than 1% on validation.
- **The default's own hourly calibration is borderline.** Its worst regime error on the hourly tuning split is
  3.25 points, and 3.1 points on the sealed hourly set. That is the edge of the tolerance, and it is worth
  watching.

## 3. Exposure: the default stays

The grid covers floor × power × step band × trend lookbacks, 375 configs, on daily data. The objective is the
median net Sharpe uplift over buy and hold.

| | Uplift, tuning | Uplift, validation | Max drawdown ÷ hold's, validation |
|---|---|---|---|
| Default (floor 0.5, power 1.0, band 0.10, 63/126/252) | +0.044 | −0.038 | 0.74 |
| Candidate (floor 0.75, power 1.5, band 0.15, 63/126/252) | +0.057 | −0.024 | 0.79 |

The candidate gains +0.013 on validation, short of the +0.02 bar.

- **The trend tilt paid before 2016 and cost after it.** Validation uplift by floor:
  - floor 0: −0.11
  - floor 0.5: −0.04
  - floor 1 (no trend tilt): −0.003

  The lookbacks hardly matter; 63/126/252 is as good as either alternative.
- **What the exposure line actually delivers.** For the median stock after 2016 it does not beat buy and hold
  on Sharpe (−0.04). It beats hold on only 31% of names. Its job is the drawdown: it holds the median max
  drawdown to about three quarters of hold's. That is how the README should describe it, not as a return
  enhancer.

## Files

| File | What it is |
|---|---|
| `hpo_core.py` | `run_p`, `run()` with its constants as arguments (asserted equal to 1e-12); loaders; splits; `risk_regime` |
| `stage1_risk.py`, `select_risk.py` | Risk forecast grid and selection → `out/risk_*.csv`, `out/risk.json` |
| `stage2_cone.py`, `select_cone.py` | Cone grid and selection → `out/cone_*.csv`, `out/cone.json`; `out/cone_HD.csv`, `out/cone_HH.csv` are the final test |
| `stage3_exposure.py`, `select_exposure.py` | Exposure grid and selection → `out/exposure_*.csv`, `out/exposure_relative.csv` |

To reproduce, run each stage on RD, FD, RH and FH (stage 3 on RD and FD only), then its `select_*.py`. The
fresh and sealed data sets are the CSV caches the protocol names.
