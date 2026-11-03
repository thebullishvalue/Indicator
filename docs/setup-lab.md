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

## 5a · Amendment 1 (2026-11-03, after run 1, before run 2)

**What run 1 showed.** On HA, F1, S1 and S2 came out numerically invalid:
mean excesses of the order of 10^8 σ. The cause is a defect in the measuring
stick, not a market effect:
- 38 markets, mostly suspended or illiquid NSE stocks, carry stretches of
  unchanged prices;
- there the EWMA volatility σ_t falls to zero (to 1e-17), and z = r ÷ (σ√h)
  divides by it;
- the D-side baselines include those bars, while the AM-agree baselines
  mostly do not, because S is undefined there. That is why S3, S4, S5 and I1
  were finite.

All of run 1's output was seen before this amendment was written. Run 1 is
kept unchanged in `research/results/setup-lab/results.json`.

**The fix.** It is chosen on principle, applies to every set and hypothesis,
and changes no definition, horizon, baseline or pass mark:
- **Primary (run 2):** a bar is **stale** when σ_t is below a quarter of the
  median of its own last 1,000 values. That uses no look-ahead and needs at
  least 250 values. Stale bars are dropped as events and as baseline bars.
  A genuinely quiet market, such as USDINR at its calmest, stays well above a
  quarter of its own median; a frozen price does not.
- **Sensitivity (run 2b):** no bar is dropped, and z is clipped to ±5.

Run 2 decides the verdicts. Run 2b is reported beside it. Where the two
disagree, the verdict is the weaker of the two. I1 does not use z and is
unchanged.

**Seen, so stated.** The protocol pre-registered the S hypotheses at N = 126
only. The harness also computed them at N = 20. Those rows are reported in an
appendix as **exploratory**, not as tests.

## 6 · Results

Run 2 (`results-a1.json`) decides the verdicts. Run 2b (`results-a1b.json`,
z clipped to ±5) is given in brackets wherever its t differs by more than 0.3.
Run 1 is in `results.json`: identical where it was finite.

**How to read the tables.**
- **Excess** is in σ units. It is the outcome beyond the hypothesis's
  baseline, averaged within each market and then across markets.
- **t** treats markets as the units.
- **m** is the number of markets with at least 3 events; **events** is the
  pooled count.
- The trail is N = 126, the default, unless marked otherwise.

### 6.1 · The trail's probes (F1)

| | DEV | HB | HA |
|---|---|---|---|
| Probe onsets | 6,012 | 3,019 | 31,961 |
| Flipped within 10 bars | 2.3% | 1.9% | 1.9% |
| Flipped within 20 bars | 4.5% | 3.8% | 4.2% |
| Back on the trail's side within 5 bars | 56.9% | 57.5% | 56.9% |
| Median probe length (bars) | 4 | 4 | 4 |
| **F1** excess on the trail's side, 10 bars | −0.076 (t −3.0) | −0.048 (t −1.9) | −0.070 (t −8.5) |
| **F1** excess on the trail's side, 20 bars | −0.092 (t −2.2) | −0.038 (t −1.4) | −0.080 (t −8.7) |

**F1 · not supported, and the opposite.** A probe is not a fakeout the trend
shrugs off:
- after a probe onset, the trail's side does **worse** than its typical bar,
  in all three sets and at both horizons;
- yet the 126-bar trail almost never flips: under 5% within 20 bars.

So the probe is a **caution on the trend**, which is what its gold mark says.
It is not a break to fade, and not a break to chase.

The 20-bar trail (secondary):

| | DEV | HB | HA |
|---|---|---|---|
| Flipped within 10 / 20 bars | 26.9% / 59.4% | 27.6% / 58.6% | 26.1% / 58.6% |
| Back on the trail's side within 5 bars | 55.9% | 56.0% | 55.4% |
| F1 excess, 10 bars | −0.056 (t −3.4) | −0.039 (t −2.3) | −0.048 (t −8.2) |
| F1 excess, 20 bars | −0.041 (t −2.0) | −0.095 (t −4.7) | −0.059 (t −8.9) |

At 20 bars, most probes become flips (59% within 20 bars). That is about the
rate seen on driftless random walks (58%), so a short trail's probes say little
beyond its own mechanics. F1 is the same sign as at 126 bars.

### 6.2 · What gets accepted (F2), flip within 20 bars

| Feature at the onset | N | DEV | HB | HA | Verdict |
|---|---|---|---|---|---|
| a · push against the trail | 126 | 3.6% vs 5.3% (t −2.7) | 3.3% vs 4.2% (t −1.6) | 3.4% vs 4.8% (t −5.3) | not supported (opposite) |
| b · migration already toward the break | 126 | 27.6% vs 4.2% (t +3.6, m 10) | 15.7% vs 3.6% (t +1.2, m 6) | 15.2% vs 4.0% (t +4.4, m 87) | **consistent** |
| c · close ≥ 0.5 ATR beyond the trail | 126 | 5.2% vs 4.2% (t +1.9) | 4.1% vs 3.6% (t +0.2) | 4.3% vs 4.1% (t −0.4) | not supported |
| d · participation w ≥ 1.5 | 126 | 4.6% vs 4.5% (t −0.1) | 3.3% vs 3.9% (t −2.4) | 3.2% vs 4.5% (t −5.4) | not supported (opposite) |
| a · push against the trail | 20 | 60.6% vs 57.0% (t +3.4) | 59.6% vs 56.9% (t +1.2) | 60.4% vs 55.4% (t +8.6) | consistent |
| b · migration toward the break | 20 | 61.2% vs 59.2% (t +1.9) | 68.3% vs 57.3% (t +5.0) | 61.9% vs 58.2% (t +5.1) | consistent |
| c · close ≥ 0.5 ATR beyond | 20 | 70.5% vs 54.6% (t +14.1) | 67.6% vs 54.4% (t +8.4) | 70.6% vs 53.8% (t +37.5) | **confirmed** |
| d · participation w ≥ 1.5 | 20 | 65.5% vs 57.6% (t +4.8) | 62.4% vs 57.4% (t +2.5) | 61.8% vs 57.3% (t +9.7) | **confirmed** |

**By count of conditions met (pooled flip rate within 20 bars):**

| Conditions met | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| N 20 · DEV | 52.0% | 56.5% | 63.8% | 73.2% | 76.8% (99) |
| N 20 · HB | 49.1% | 56.8% | 63.4% | 69.2% | 65.9% (44) |
| N 20 · HA | 51.1% | 56.2% | 62.1% | 71.3% | 71.9% (558) |
| N 126 · HA | 4.5% | 4.4% | 3.7% | 3.1% | 11.9% (42) |

On the 20-bar trail, a deep break on heavy participation, with the push and
migration behind it, is accepted about 70% of the time, against about 50% with
none of them. On the 126-bar trail only migration matters. Breaks that are
hard and heavy flip it *less*: a six-month floor is not broken by one day's
force.

### 6.3 · Entries (N = 126)

| ID | Entry | 10 bars: DEV | HB | HA | 20 bars: DEV | HB | HA | Verdict |
|---|---|---|---|---|---|---|---|---|
| S1 | rejection of a probe | −0.029 (−1.4) | +0.019 (+0.7) | −0.041 (−5.3) | −0.056 (−1.6) | +0.051 (+1.6) | −0.044 (−4.7) | not supported |
| S2 | acceptance (the flip) | +0.024 (+0.6) | +0.088 (+1.6) | +0.075 (+4.4) | +0.045 (+1.2) | +0.105 (+1.7) | +0.106 (+6.7) | **consistent** |
| S3 | pullback into value, AM agreeing | −0.003 (−0.2) | +0.008 (+0.4) | −0.001 (−0.1) | −0.014 (−0.9) | −0.048 (−2.2) | −0.007 (−1.0) | not supported |
| S4 | breakout from value, AM agreeing | +0.062 (+4.1) | +0.050 (+2.5) | +0.064 (+10.4) | +0.043 (+2.3) | +0.042 (+2.1) [1.8] | +0.054 (+8.1) | no prediction; positive, t ≥ 2 everywhere at 10 bars |
| S3 − S4 | pullback minus breakout | −0.067 (−4.3) | −0.042 (−2.5) | −0.064 (−10.9) | −0.069 (−5.6) | −0.090 (−5.2) | −0.061 (−11.5) | the breakout is better, everywhere |

Events: S1 5,135 / 2,605 / 27,039; S2 949 / 477 / 5,189; S3 9,289 / 4,552 /
49,427; S4 9,025 / 4,463 / 48,248. The hit rates (z > 0) are 50% to 54%
throughout. These are small leans on average, not setups that win most of the
time.

**S4 was not predicted**, so by §4 it cannot be called confirmed. It came out
positive with t ≥ 2 in all three sets at 10 bars, in both runs. The manual
reports it as a measured observation that a fresh holdout must confirm. The
practical reading matches momentum: with the trend, a close **out of value**
in its direction beats a pullback **into** value.

### 6.4 · Context (S5, N = 126, 20 bars)

| | DEV | HB | HA | Verdict |
|---|---|---|---|---|
| AM agreeing: migrating with the trail, minus balance | +0.053 (t +1.9) | +0.081 (t +2.3) | +0.036 (t +3.8) | **consistent** |

### 6.5 · The investor's filter (I1)

| Set | Markets | Time invested | Filter: CAGR · vol · Sharpe · max DD | Buy-and-hold: CAGR · vol · Sharpe · max DD |
|---|---|---|---|---|
| DEV (1992–2019) | 106 | 46% | 11.5% · 14.7% · 0.82 · −31% | 20.0% · 28.0% · 0.79 · −58% |
| HB (2020–26) | 106 | 53% | 7.4% · 9.4% · 0.81 · −29% | 18.2% · 17.5% · 1.04 · −36% |
| HA (1997–2026) | 391 | 43% | 16.5% · 11.7% · 1.36 · −28% | 37.8% · 25.5% · 1.39 · −64% |

**I1 · not confirmed.** The drawdown condition held in all three sets. The
Sharpe condition failed in HB, where buy-and-hold's Sharpe was 0.23 higher.

The filter roughly halves the deepest drawdown, at about half the return,
while invested a little under half the time. These are equal-weight
portfolios, rebalanced daily. HA is today's NSE listings, so it carries
survivorship. Its buy-and-hold CAGR is flattered by both, and only the
filter-against-buy-and-hold comparison on the same markets is meaningful.

### 6.6 · Exploratory, not pre-registered (S at N = 20)

| | 10 bars: DEV | HB | HA |
|---|---|---|---|
| S2 acceptance | +0.070 (+3.7) | +0.145 (+5.2) | +0.045 (+5.3) |
| S4 breakout | +0.000 (0.0) | +0.042 (+4.0) | +0.051 (+13.0) |
| S5 migration | −0.030 (−1.1) | +0.076 (+3.8) | −0.069 (−7.0) |

These are reported because they were computed, not because they were tested.

### 6.7 · Verdicts in one line each

- **F1:** the opposite of the prediction. A probe weakens the trend's next
  weeks.
- **F2b:** consistent at 126.
- **F2c and F2d:** confirmed at 20 bars.
- **S2 and S5:** consistent.
- **S1 and S3:** not supported.
- **S4:** positive everywhere, but unpredicted.
- **I1:** not confirmed, though its drawdown half held.

Nothing here makes a trading system on its own. What it changes is how the
probe, the break and the pullback are taught.
