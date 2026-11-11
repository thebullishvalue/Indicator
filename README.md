# Indicator

Two TradingView (Pine v6) scripts.

| File | What it is |
|---|---|
| `kasauti.pine` | **Kasauti** — calibrated risk, exposure and self-audit. Built from scratch on the research in `research/`. |
| `pragati.pine` | **Pragati** — the multi-timeframe conviction oscillator. Unchanged; it was the direction of thought and the benchmark. |

## Kasauti · कसौटी

*Kasauti* is the touchstone: the stone a goldsmith rubs metal on to see what it is.
The script answers three questions for the chart it is on, and then tests its own answers:

1. **How far can it go?** A cone for the close 10 bars ahead that holds 80% of the time.
2. **Where am I wrong?** A stop level that is touched within 10 bars 20% of the time, and the position size that goes with it.
3. **How much should I hold?** An exposure dial between 0 and 1.

![Kasauti on Nifty 50](docs/preview_nsei.png)

*Rendered from the reference implementation (`research/kasauti.py`), not from TradingView.*

### Why it is not an oscillator

The first thing measured was whether anything on a single chart forecasts direction.
On 151 instruments (US and NSE stocks, indices, commodities, FX, bonds, crypto), daily bars, 2001–2026, in three eras:

- No state tried — trend, stretch, dips in uptrends, relative volume, overnight against session drift, close location, efficiency — led the next 10 bars in a way that held in all three eras (`research/direction_null.txt`).
- Deep dips paid in 2003–2019 and stopped after 2020.
- No simple long/flat rule beat a risk-scaled buy and hold on Sharpe.

Risk is different. The next 10 bars' variance is forecast out of sample with a log R² of 0.71.
So Kasauti forecasts risk, states it as probabilities, and turns it into size, stop and exposure.

### What it measured

All figures are from `research/results.txt`, net of 5 bp costs (10 bp crypto), acting one bar late.

| Claim | Kasauti | Comparison |
|---|---|---|
| Cone holds 80% of the time | 80.0% realised; within 3 points in 94% of instrument-eras | fixed normal band: 61% of instrument-eras |
| Cone holds in calm / normal / stressed markets | 80% / 80% / 81% | fixed normal band: 80% / 83% / 85% |
| Long stop touched 20% of the time | 19.9% realised; within 3 points in 99% of instrument-eras | a 2 × ATR(14) stop: 17% to 44% depending on the instrument |
| Risk forecast error (QLIKE, 2013–2026) | 0.354 | 20-bar standard deviation: 0.509 |
| Exposure dial, risk only | Sharpe 0.56, worst drawdown −55% | buy and hold: 0.53, −62% |
| Exposure dial, risk × trend (default) | Sharpe 0.54, worst drawdown −45%; shallower on 99% of instruments in every era | buy and hold: 0.53, −62% |

### What it does not do

- **It does not call direction.** After 2013 neither dial beats buy and hold on Sharpe. The dial is risk control: about the same return per unit of risk, with a drawdown roughly a quarter shallower.
- **The ledger will usually say "unproven".** Each of nine states (trend × surprise) is scored on the chart's own history and shrunk toward "no edge". Pooled, no state passes |t| = 1.1 outside crypto; on random walks it calls a state proven on 0.5% of bars. A proven state lit on only 6 of 151 instruments, too few to claim anything from.
- **Calibration is a long-run frequency.** Inside one shock the cone can miss several bars running.
- **The stocks are today's large caps.** That flatters buy and hold and the dial alike. Indices, commodities, FX and bonds carry no such bias.

### How to read it

| Where | What | Read it as |
|---|---|---|
| Price chart | Forward cone | where the close should be H bars from now |
| Price chart | Dashed lines across the cone | long and short stops at the stated touch probability |
| Price chart | Landing band | the cone drawn H bars ago; a close outside it is a surprise |
| Pane · Surprise | Columns against two bands | the realised move ÷ the forecast made H bars ago; coloured by trend |
| Pane · Exposure | Step line | how much of a full position to hold |
| Pane · Proof | Two lines | following the dial against buy and hold on this chart |
| Table | Nine rows | risk, cone, stops and size, exposure, the state's record, calibration, proof |

### Status

- The Pine script has **not been compiled in TradingView**. No Pine compiler is available here, and it was checked by hand against the reference implementation only. Expect to fix a syntax detail or two on first load.
- Everything was measured on **daily bars**. The script runs on any timeframe, but intraday is unmeasured.

### Reproduce

```
cd research
python3 fetch.py                                   # ~150 symbols from Yahoo into data/
python3 study.py > results.txt                     # every figure above
python3 direction_null.py > direction_null.txt     # the search that came back empty
python3 preview.py                                 # docs/preview_*.png
```

`research/kasauti.py` is the bar-for-bar reference for `kasauti.pine`.
