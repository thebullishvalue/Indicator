# Setup lab: fakeouts, entries and an investor's filter, pre-registered

**Status:** this protocol (§1 to §5) was written and committed on 2026-11-03,
**before any test below was run on any market**. Results are appended in §6,
written once and never edited. Every number, including the failures, goes
into the field manual. A test whose result disappoints is reported as it came
out. Changing a definition, a horizon or a pass mark after a result is seen
makes a **new** hypothesis, which needs a new version of this document.

**Why.** Manual 2.0 must teach setups: how to treat a probe, where to enter,
what makes a break real, and how an investor can use the trail. Teaching
setups that were never tested would put opinion where evidence should be. Some
setups can be tested with the code in this repository, which reproduces the
indicator's auction engine bar for bar (spec v2, parity-tested against the
Pine with 0 missed probes). Those are tested here, once each.

The conviction and value **tapes**, the **grid** and the **▲▼** cannot be
tested here. Their engines need TradingView's intrabar data and Samanvaya's
macro drivers. The manual tags those setups External (the v9 audit) or
Unmeasured.

---

## 1 · Data

| Set | Markets | Dates | Note |
|---|---|---|---|
| **DEV** | The 119 markets of `research/results/2026-11-02/universe.csv` with ≥ 600 bars | ≤ 2019-12-31 | The tradability and trail lab's development set |
| **HB** | The same 119 | 2020-01-01 → 2026-10-31 | Time holdout |
| **HA** | The 411 markets of `research/results/lab/ha-universe.csv` (391 NSE stocks, 20 crypto) | full history | Market holdout. Used once before, for Accepted momentum only. Unseen for every question here |

These are daily bars. Every series is computed on a market's full history, so
the series at bar *t* uses data up to *t* only. Each set scores only the events
that fall on its own dates. All three sets are run **once**. There is no
development loop, because nothing here is tuned.

## 2 · Definitions

- **Engine.** `reference/auction_trail.py` (spec v2), with participation *w*
  from the same file and the push gate from `research/push_gate.py`.
  - **N = 126** is primary. That is the trail Pragati draws by default, with
    Accepted momentum on, and it is the trail behind the default probe marks
    and AUCTION row.
  - **N = 20**, the Lookback trail drawn when Accepted momentum is off, is
    secondary. F1 and F2 are also run there.
  - Per bar: *D* (side), *T* (level), VAL, POC, VAH, *M* (migration), probe,
    onset and flip.
- **σ** is the EWMA (span 60) volatility of daily log returns
  (`tradability.ewma_vol`).
- **S** is the momentum score `trail_lab.mom(close, σ)`.
- **AM position** = *D*·max(0, *D*·*S*). **AM agrees** when *D*·*S* > 0.
- **ATR20** is Wilder's ATR(20).
- **Timing.** An event is known at the close of bar *t* and entered at the open
  of *t*+1. Its outcome over *h* bars, in its direction *s* ∈ {+1, −1}, is
  z_h = *s* · ln(O_{t+1+h} / O_{t+1}) / (σ_t √h): the move in σ units, net
  of nothing.
- **Excess.** For each market, excess = mean z_h over the events minus mean
  z_h over the hypothesis's **baseline** bars, in the same market and set.
  This measures timing *beyond* simply being on that side. A market needs ≥ 3
  events in a set to count.
- **Statistic.** The mean excess across markets, with t = mean ÷ (sd ÷ √n),
  markets as the units. Events overlap in time within a market; the
  per-market mean absorbs that. Markets are correlated with one another,
  which flatters t, so a pass needs agreement across all three sets.

## 3 · Hypotheses

Each has a predicted sign, fixed now.

| ID | Question | Event at close *t* | *s* | Baseline | h | Prediction |
|---|---|---|---|---|---|---|
| **F1** | Is a probe a fakeout? | probe onset | *D* (the trail's side) | bars with *D_t* = *s* | 10, 20 | excess > 0: on average the break fails |
| **F2a–d** | What gets accepted? | probe onset, split by a feature at the onset bar | — | — | 20 | the first group flips more often (below) |
| **S1** | Enter on the rejection | the bar a probe episode ends with no flip: probe_{t−1}, not probe_t, not flip_t, *D_t* = *D_{t−1}* ≠ 0 | *D* | bars with *D_t* = *s* | 10, 20 | excess > 0 |
| **S2** | Enter on the acceptance | flip_t | the new *D* | bars with *D_t* = *s* | 10, 20 | excess > 0 |
| **S3** | Buy the pullback into value | AM agrees; VAL_t ≤ C_t ≤ VAH_t; C_{t−1} beyond value on *D*'s side (> VAH up, < VAL down) | *D* | AM-agree bars | 10, 20 | excess > 0 |
| **S4** | Buy the breakout from value | AM agrees; C_t beyond value on *D*'s side; C_{t−1} inside value | *D* | AM-agree bars | 10, 20 | none: reported two-sided, with S3 − S4 |
| **S5** | Does migration matter in a trend? | AM-agree bars with *M*·*D* = 2, against AM-agree bars with *M* = 0 | *D* | (the balance bars) | 20 | migrating > balance |
| **I1** | An investor's trend filter | — | — | — | — | below |

**F2 groups**, at the onset bar, with the flip rate measured as a flip within
20 bars:

| ID | First group | Second group |
|---|---|---|
| F2a | the push gate against the trail (gate = −*D*) | otherwise |
| F2b | migration already toward the break (−*D*·*M* ≥ 1) | otherwise |
| F2c | the close ≥ 0.5 ATR20 beyond *T* | less |
| F2d | participation *w* ≥ 1.5 | less |

Per market: the flip-rate difference, first group minus second, in markets
with ≥ 3 onsets in each group. The statistic is as in §2. The flip rate is
also reported by **how many** of the four conditions hold (0 to 4), pooled.
That is the manual's fakeout checklist.

**F1 descriptive**, reported for both N:
- the share of onsets followed by a flip within 10 and 20 bars;
- the share back on the trail's side (a close on *D*'s side of *T*) within 5
  bars;
- the median probe episode length.

**I1 · the investor's trend filter.**
- **Rule:** long-only and unlevered, holding 1 while the AM position > 0 and 0
  otherwise. Decided at the close and traded at the next open.
- **Rebalance:** checked weekly (t % 5 = 0) and immediately when the state
  changes, exactly as `tradability.weights(family="invest")`. Per-class costs
  are as in `tradability.COST_BPS`.
- **Benchmark:** buy-and-hold on the same markets.
- **Portfolio:** equal weight across live markets, rebalanced daily.
- **Markets:** non-crypto only. DEV and HB use all non-crypto classes; HA uses
  its 391 NSE stocks.
- **Reported:** CAGR, volatility, Sharpe, maximum drawdown and time invested,
  for both the filter and buy-and-hold.
- **Prediction:** the filter's maximum drawdown is smaller than buy-and-hold's
  in all three sets, and its Sharpe is no more than 0.10 below buy-and-hold's.
  Its CAGR is reported whatever it is.

## 4 · Verdicts

- **Confirmed:** the predicted sign, with t ≥ 2.0, in **all three** sets.
- **Consistent:** the predicted sign in all three sets, with t < 2.0 in at
  least one.
- **Not supported:** anything else, including the opposite sign anywhere.
- **I1:** confirmed only if both of its conditions hold in all three sets.

The manual tags a confirmed setup Measured. Every other setup carries its
numbers and the plain word for its verdict. Sixteen tests are run (F1 and S1
to S4 at two horizons, S5, F2a–d, I1), so about one false "t ≥ 2" is expected
in any single set by chance. Requiring all three sets is the guard.

## 5 · Case studies: the selection rule, fixed now

The manual's real-data case studies come from six markets fixed now, one per
class:

| Class | Market |
|---|---|
| Index | NIFTY_50 |
| NSE stock | RELIANCE |
| Commodity | GOLD |
| FX | USDINR |
| Crypto | BTCUSDT |
| ETF | BANKBEES |

For each case type, the case is the **most recent** qualifying event before
2026-09-30, whose 20-bar outcome is complete, **whatever its outcome**. The
case types are:
- a probe that was rejected;
- a probe that was accepted (flipped within 20 bars);
- the latest completed Accepted momentum long and short (or flat) cycle;
- a pullback into value (S3).

A case chosen this way can lose. That is the point: cases show how the
readings unfold, not that they win.

## 6 · Results

(Appended once, after the run.)
