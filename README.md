# Indicator

| File | What it is |
|---|---|
| `maryada.pine` | **Maryada** — one self-contained TradingView indicator (Pine v6): calibrated range, stops, touch probabilities, exposure, tapes and volume profile. |
| `pragati.pine` | **Pragati** — the original multi-timeframe conviction oscillator. Unchanged; it was the direction of thought, and the source of the palette and the volume profile. |
| `research/` | The data fetch, the Python reference for Maryada, and the study behind every number below. |

## Maryada · मर्यादा

*Maryada* is the boundary: the line a thing keeps within. (Earlier drafts were called Kasauti.)
It is **one script**. The pane, the tapes, the cone and stops, the volume profile and the table are all the same indicator.
The only data it requests is the chart symbol's own lower timeframe, for the profile.

It answers four questions for the chart it is on, and keeps the record of its own answers:

1. **How far can it go?** A cone for the close 10 bars ahead that holds 80% of the time.
2. **Where am I wrong?** A stop level that is touched within 10 bars 20% of the time, and the position size that goes with it.
3. **How likely is this level?** The probability that any price — a profile level, a target, your own stop — is traded at within 10 bars.
4. **How much should I hold?** An exposure dial between 0 and 1.

![Maryada on Nifty 50](docs/preview_nsei.png)

*Rendered from the reference implementation (`research/maryada.py`), not from TradingView. The profile in this render is built from daily bars.*

### Why it does not call direction

The first thing measured was whether anything on a single chart forecasts direction.
On 151 instruments (US and NSE stocks, indices, commodities, FX, bonds, crypto), daily bars, 2001–2026, in three eras:

- No state tried — trend, stretch, dips in uptrends, relative volume, overnight against session drift, close location, efficiency — led the next 10 bars in a way that held in all three eras (`research/direction_null.txt`).
- Deep dips paid in 2003–2019 and stopped after 2020.
- No simple long/flat rule beat a risk-scaled buy and hold on Sharpe.

Risk is different. The next 10 bars' variance is forecast out of sample with a log R² of 0.71.
So Maryada forecasts risk, states it as probabilities, and turns it into range, stop, level odds and exposure.

### What the third pass changed

| Change | Why |
|---|---|
| **Touch curve.** Four learned distances a side (touched 75, 50, 25, 10% of the time) instead of one stop. | Any level can now be given a probability. Read at probabilities it was not trained on: stated 15% → touched 14.7%; 35% → 34.5%; 62% → 61.9%; 85% → 84.4%. |
| **Volume profile**, ported whole from Pragati, with a touch probability on every level. | The profile says where the market traded; the curve says how likely price is to get there. |
| **Volume levels do not bend the curve.** | Tested because the profile is here: prior-session POC, VAH, VAL and naked POCs were touched within a point of what their distance alone implies (prior POC: stated 59%, touched 59%), in every era and class. |
| **The ledger is removed.** | It scored nine trend × surprise states for direction; none reached \|t\| = 1.3 and it read "unproven" nearly always. Its study stays in `research/`. |
| **Unified tapes** are the default; the four detailed tapes are an option. | One reading for price, one for risk. |
| **Pragati's colour language** throughout. | Green and red are direction, intensity is how far it has run, gold means read with caution and nothing else. |

### The tapes

| Mode | Tape | Reads | Colour |
|---|---|---|---|
| Unified | **Price** (top) | the trend, and whether the short horizons agree with it: running, holding, pullback, bounce | hue is the trend; near-solid when the ladder runs with it, moderate inside, pale against |
| Unified | **Risk** (bottom) | where forecast risk stands in its last 500 bars, a step up while rising, a step down while falling | gold only; solid gold is a spike |
| Detailed | **Trend**, **Stretch ladder** (top) | the move over a quarter, half and year of bars; how many of four horizons closed outside their own cone | green / red by side |
| Detailed | **Risk**, **Risk momentum** (bottom) | calm → stressed; the change in forecast risk over the last 10 bars | gold |

What each one changes, and what was measured:

- **Trend** skews the cone and stops and throttles the dial. Without it, a short stop in a downtrend was touched 27% of the time against a stated 20%; with it, 21%.
- **Stretch ladder**: 3–4 rungs outside on about 4% of bars a side. After a break below, a long stop is touched about a quarter of the time, not a fifth — the table's long-stop row turns gold. No direction in any era.
- **Risk** sets the cone's width and the dial's first factor. Stressed risk fell over the next 10 bars (median −8%); calm risk did not rise.
- **Risk momentum**: after a rise of more than 10%, risk was lower 10 bars later 74% of the time, in every era.

The ladder uses horizons on the chart's own bars instead of other timeframes. A 5-bar horizon on a daily chart is the weekly move, rolled forward every bar: no staircase, no repaint, no data request.

### What it measured

All figures are from `research/results.txt`, net of 5 bp costs (10 bp crypto), acting one bar late.

| Claim | Maryada | Comparison |
|---|---|---|
| Cone holds 80% of the time | 79.9% realised; within 3 points in 99% of instrument-eras | fixed normal band: 61% of instrument-eras |
| Cone holds in calm / normal / stressed markets | 79% / 80% / 81% | fixed normal band: 80% / 83% / 85% |
| Long stop touched 20% of the time | 20.0% realised; within 3 points in 99% of instrument-eras | a 2 × ATR(14) stop: 17% to 44% depending on the instrument |
| Touch curve at untrained probabilities | 5% → 5.9%; 15% → 14.7%; 35% → 34.5%; 62% → 61.9%; 85% → 84.4% | — |
| Holds at other settings | horizons 5, 20, 40; cones 50% and 90%; stops 10% and 30%: every instrument within 3 points | — |
| Holds on other timeframes | weekly: 96% of instruments within 3 points; hourly: 100% | fixed normal band: 46% and 80% |
| Risk forecast error (QLIKE, 2013–2026) | 0.354 | 20-bar standard deviation: 0.509 |
| Exposure dial, daily (default) | Sharpe 0.55, mean worst drawdown −44% | buy and hold: 0.53, −62% |
| Exposure dial, weekly | Sharpe 0.49, mean worst drawdown −44% | buy and hold: 0.51, −57% |

### What it does not do

- **It does not call direction.** After 2013 the dial does not beat buy and hold on Sharpe. It is risk control: about the same return per unit of risk, with a drawdown roughly a quarter shallower.
- **The dial failed on hourly bars.** Sharpe 0.26 against 0.42 for buy and hold, after costs. Use the dial on daily and weekly charts; the cone and stops hold on every timeframe tested.
- **A touch probability is not a close, and not a race.** It is the chance the level is traded at within the horizon — not of closing beyond it, and not of which of two levels comes first.
- **The curve runs a little low in the far tail.** Levels it calls 5% likely were touched about 6% of the time.
- **Calibration is a long-run frequency.** Inside one shock the cone can miss several bars running.
- **The stocks are today's large caps.** That flatters buy and hold and the dial alike. Indices, commodities, FX and bonds carry no such bias.

### How to read it

| Where | What | Read it as |
|---|---|---|
| Price chart | Forward cone | where the close should be H bars from now |
| Price chart | Dashed lines across the cone | long and short stops at the stated touch probability |
| Price chart | Landing band | the cone drawn H bars ago; a close outside it is a surprise |
| Price chart | Volume profile and its tags | where the market traded; each level with the chance it is traded at within H bars |
| Pane | Columns against two lines | the realised move ÷ the forecast made H bars ago; near-solid when the close left the cone |
| Pane | Tapes | price above, risk below |
| Pane · Proof view | Two lines | following the dial against buy and hold on this chart |
| Table | Range, position, context, record | cone, stops and size, your level, exposure, tapes, profile, calibration, proof |

### Status

- The Pine script has **not been compiled in TradingView**. No Pine compiler is available here; it was checked by hand and by static checks only. The profile block is Pragati's own code with three small edits. Expect to fix a syntax detail or two on first load.
- The Python reference and the Pine script were written to the same arithmetic but have not been compared bar for bar.
- The level study used the profile's **fallback path** — weekly sessions built from daily bars. The intrabar-built profile that TradingView draws is unmeasured.

### Reproduce

```
cd research
python3 fetch.py                                   # ~150 symbols, daily, from Yahoo into data/
python3 fetch.py 1h                                # the same symbols, hourly, into data1h/
python3 study.py > results.txt                     # every figure above (about an hour)
python3 direction_null.py > direction_null.txt     # the search that came back empty
python3 preview.py                                 # docs/preview_*.png
```
