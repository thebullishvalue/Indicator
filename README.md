# Indicator

| File | What it is |
|---|---|
| `kasauti.pine` | **Kasauti** — one self-contained TradingView indicator (Pine v6): calibrated risk, exposure, tapes, self-audit and volume profile. |
| `pragati.pine` | **Pragati** — the original multi-timeframe conviction oscillator. Unchanged; it was the direction of thought and the benchmark. |
| `research/` | The data fetch, the Python reference for Kasauti, and the study behind every number below. |

## Kasauti · कसौटी

*Kasauti* is the touchstone: the stone a goldsmith rubs metal on to see what it is.
It is **one script**. The pane, the tapes, the cone and stops, the volume profile and the table are all the same indicator.
The only data it requests is the chart symbol's own lower timeframe, for the profile.

It answers three questions for the chart it is on, and then tests its own answers:

1. **How far can it go?** A cone for the close 10 bars ahead that holds 80% of the time.
2. **Where am I wrong?** A stop level that is touched within 10 bars 20% of the time, and the position size that goes with it.
3. **How much should I hold?** An exposure dial between 0 and 1.

![Kasauti on Nifty 50](docs/preview_nsei.png)

*Rendered from the reference implementation (`research/kasauti.py`), not from TradingView.*

### Why it does not call direction

The first thing measured was whether anything on a single chart forecasts direction.
On 151 instruments (US and NSE stocks, indices, commodities, FX, bonds, crypto), daily bars, 2001–2026, in three eras:

- No state tried — trend, stretch, dips in uptrends, relative volume, overnight against session drift, close location, efficiency — led the next 10 bars in a way that held in all three eras (`research/direction_null.txt`).
- Deep dips paid in 2003–2019 and stopped after 2020.
- No simple long/flat rule beat a risk-scaled buy and hold on Sharpe.

Risk is different. The next 10 bars' variance is forecast out of sample with a log R² of 0.71.
So Kasauti forecasts risk, states it as probabilities, and turns it into size, stop and exposure.

### The tapes

Four bands frame the pane. A tape is there only because a number depends on it.
The two inner tapes are what the cone and the dial listen to; the two outer tapes say where each is heading.

| Tape | Reads | What it changes | Measured |
|---|---|---|---|
| **Trend** (inner, top) | the move over a quarter, half and year of bars, in σ | skews the cone and stops; throttles the dial | without it, a short stop in a downtrend was touched 27% of the time against a stated 20%; with it, 21% |
| **Stretch ladder** (outer, top) | how many of four horizons (5, 10, 20, 40 bars) closed outside their own learned cone | a caution on the stops | 3–4 rungs outside on about 4% of bars a side; after a break below, a long stop is touched about a quarter of the time, not a fifth; no direction in any era |
| **Risk** (inner, bottom) | where forecast risk stands in its last 500 bars: calm, normal, stressed | the cone's width; the dial's first factor | stressed risk fell over the next 10 bars (median −8%); calm risk did not rise |
| **Risk momentum** (outer, bottom) | the change in forecast risk over the last 10 bars | when the cone is at its widest | after a rise of more than 10%, risk was lower 10 bars later 74% of the time, in every era |

The ladder uses horizons on the chart's own bars instead of other timeframes. A 5-bar horizon on a daily chart is the weekly move, rolled forward every bar: no staircase, no repaint, no data request.

### What it measured

All figures are from `research/results.txt`, net of 5 bp costs (10 bp crypto), acting one bar late.

| Claim | Kasauti | Comparison |
|---|---|---|
| Cone holds 80% of the time | 79.9% realised; within 3 points in 99% of instrument-eras | fixed normal band: 61% of instrument-eras |
| Cone holds in calm / normal / stressed markets | 79% / 80% / 81% | fixed normal band: 80% / 83% / 85% |
| Long stop touched 20% of the time | 20.0% realised; within 3 points in 99% of instrument-eras | a 2 × ATR(14) stop: 17% to 44% depending on the instrument |
| Holds at other settings | horizons 5, 20, 40; cones 50% and 90%; stops 10% and 30%: every instrument within 3 points | — |
| Holds on other timeframes | weekly: 96% of instruments within 3 points; hourly: 100% | fixed normal band: 46% and 80% |
| Risk forecast error (QLIKE, 2013–2026) | 0.354 | 20-bar standard deviation: 0.509 |
| Exposure dial, daily (default) | Sharpe 0.55, mean worst drawdown −44% | buy and hold: 0.53, −62% |
| Exposure dial, weekly | Sharpe 0.49, mean worst drawdown −44% | buy and hold: 0.51, −57% |

### The midline observation (v2.2)

The observation tested: the average of the landing band's two edges divides trend. While price is below it, price tends to go lower until it gets back above, and the strongest runs start when risk is calm and the trend or the histogram flips.

The midline is close to where price stood 10 bars ago, so "above the midline" is close to "the surprise histogram is positive" (they agree on 91% of bars).

Measured on 151 instruments, daily bars 2001–2026 (`research/midline.txt`), it did not hold as a forward signal:

| Test | Result |
|---|---|
| Next bar's return per unit of risk, above against below the midline | 2.80 against 2.88 (σ × 100): the same, in every era, risk regime and trend state |
| Next 10 bars after a close across it | no different from any other 10 bars, on either side |
| Crosses made in calm risk | no different from normal or stressed |
| Crosses that came with a trend flip | no different |
| Rule: long above, flat below | Sharpe 0.24 against 0.48 for buy and hold |
| Rule: long above, short below | Sharpe −0.17 |
| Rule on hourly bars | every version lost after costs |

Why it looks true on a chart: a run below the midline lasts a long time only if price kept falling.
One run in eleven lasts 20 bars or more, and those average 7–10%. They are what the eye finds.
The other ten are over within a few bars (the median run is 4 bars), and only 37% of all runs end in profit.

A slower version behaves like the trend tape already in the script: long while the close is above the close 252 bars ago made a Sharpe of 0.41 against 0.49 for buy and hold, with a shallower drawdown.

So the midline is drawn as a line, with the chart's own record of it in the table (runs, share won, share lasting 20+ bars, and the long/flat rule against buy and hold). Its crossings are optional marks, not a signal.

### What it does not do

- **It does not call direction.** After 2013 the dial does not beat buy and hold on Sharpe. It is risk control: about the same return per unit of risk, with a drawdown roughly a quarter shallower.
- **The dial failed on hourly bars.** Sharpe 0.26 against 0.42 for buy and hold, after costs. Use the dial on daily and weekly charts; the cone and stops hold on any timeframe tested.
- **The ledger will usually say "unproven".** Each of nine states (trend × surprise) is scored on the chart's own history and shrunk toward "no edge". Pooled, no state reaches |t| = 1.3 outside crypto; on random walks it calls a state proven on 0.4% of bars.
- **Calibration is a long-run frequency.** Inside one shock the cone can miss several bars running.
- **The stocks are today's large caps.** That flatters buy and hold and the dial alike. Indices, commodities, FX and bonds carry no such bias.

### How to read it

| Where | What | Read it as |
|---|---|---|
| Price chart | Forward cone | where the close should be H bars from now |
| Price chart | Dashed lines across the cone | long and short stops at the stated touch probability |
| Price chart | Landing band | the cone drawn H bars ago; a close outside it is a surprise |
| Price chart | Volume profile | Pragati's, carried in whole: session histogram, POC, value area, VWAP, Initial Balance, prior-session levels, naked POCs. Display only; it sits to the right of the cone |
| Pane | Columns against two lines | the realised move ÷ the forecast made H bars ago, against the learned bands; coloured by trend |
| Pane | Four tapes | trend and stretch ladder above; risk and risk momentum below |
| Pane · Proof view | Two lines | following the dial against buy and hold on this chart |
| Table | Ten rows | risk, cone, stops and size, exposure, tapes, the state's record, calibration, proof |

Gold always means risk, never up or down.

### Status

- **v2.2** adds the midline and its record; **v2.1** added the volume profile. No engine number changed from v2.0. The preview image above predates it and does not show the profile.
- A later experiment ("Maryada": touch probabilities on profile levels, unified tapes, Pragati's palette) was set aside; it remains in the git history at commit `7c5340a`.
- The Pine script has **not been compiled in TradingView**. No Pine compiler is available here; it was checked by hand against the reference implementation. Expect to fix a syntax detail or two on first load.
- The Python reference and the Pine script were written to the same arithmetic but have not been compared bar for bar.

### Reproduce

```
cd research
python3 fetch.py                                   # ~150 symbols, daily, from Yahoo into data/
python3 fetch.py 1h                                # the same symbols, hourly, into data1h/
python3 study.py > results.txt                     # every figure above (about 40 minutes)
python3 direction_null.py > direction_null.txt     # the search that came back empty
python3 study_mid.py > midline.txt                 # the midline observation
python3 preview.py                                 # docs/preview_*.png
```
