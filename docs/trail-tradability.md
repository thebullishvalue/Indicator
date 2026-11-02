# Can the acceptance trail be traded or invested? Council verdict and test plan

**Status:** sections 1–5 written and frozen on 2026-11-02, **before any market data was
read.** This document is a pre-registration. It fixes the candidates, the
data, the costs and the pass marks before a single result exists.
`research/tradability.py` runs it unchanged.
Section 6 and its amendment 6.1 (the data) were added before any result. Section 7 is the result.

---

## 1 · What the current engine is, stated plainly

The acceptance trail (spec v2) has four parts:

- A rolling 20-bar participation-weighted volume profile.
- A ratcheted value-area edge.
- Steps gated by conviction's push.
- Flips that require price beyond the trail, the POC following, and value having
  migrated that way.

Its output is a **binary trend state**: up, down, or not started.

Levine & Pedersen (2016, "Which trend is your friend?") show that every trend
filter built from past prices is a weighted sum of past returns. Trailing stops,
moving-average crossovers and time-series momentum differ mainly in how they
weight that past. **So the trail is a trend filter with an unusual weighting**
(participation-weighted location, ratcheted, acceptance-gated). It can add
something over a plain return kernel in only two places:

1. **Location.** The POC is a participation-weighted, outlier-resistant
   estimate of where the market agrees on price, not a single closing print.
2. **Acceptance.** The probe-versus-flip distinction claims to tell a break
   the market accepts from one it rejects.

Neither has been measured.

## 2 · Would we trade or invest it today? **No.** Why, in five points

1. **Untested on markets.** Every number so far is synthetic. Synthetic data
   holds whatever edge it was built with, so it says nothing about markets.
2. **Wrong horizon for single stocks.** A 20-bar daily trend state sits where
   individual stocks show **short-term reversal**, not continuation
   (Jegadeesh 1990; Lehmann 1990). Pragati's own audit agrees: the continuation
   ◆ measured negative, and buyers in control at a fair price lagged.
3. **Binary, unsized, undiversified.** The documented trend premium is earned
   by continuous, **volatility-scaled** positions spread over **many**
   uncorrelated markets, over **1–12 months** (Moskowitz, Ooi & Pedersen 2012;
   Hurst, Ooi & Pedersen 2017). A single market's trend signal typically has a
   Sharpe ratio of a few tenths and long flat spells. The trail is one market,
   one horizon, all-or-nothing.
4. **No cost model or risk rule.** A flip every 40–70 bars on synthetic data
   is a moderate turnover whose cost has never been charged.
5. **Its distinctive claim is unproven.** If acceptance does not separate
   breaks that follow through from breaks that fail, the trail is a
   slower Supertrend.

What it **is** good for today: structure. Where value was last accepted, and
where a stop belongs, is useful to a discretionary trader whatever the trail's
edge turns out to be.

## 3 · The envisioned engine: *Acceptance Momentum*

The council's design keeps what is distinctive about the auction engine and
puts it inside the architecture the trend literature supports.

| Part | Definition | Why |
|---|---|---|
| **Location** | The trail's own 20-bar POC, spec v2, unchanged | The engine's one new ingredient, a participation-weighted price |
| **Direction** | For *h* ∈ {21, 63, 126, 252} bars (about 1, 3, 6, 12 months): `s_h = ln(POC_t / POC_{t−h}) / (σ_t·√h)`, with σ_t the EWMA daily volatility (span 60). Score `S_t = mean_h clip(s_h, −2, 2) / 2` ∈ [−1, 1] | The horizons are the literature's, not searched. Volatility normalisation makes the four comparable. |
| **Acceptance** (variant AM-A only) | Halve \|S_t\| while the move in S's own direction is unaccepted: a probe onset in the last 5 bars whose break points the way S does. That is price beyond an opposing trail with neither the POC nor value having followed. | Tests the engine's distinctive claim as a *sizing* input, not as a filter that can only remove trades |
| **Sizing** (trading) | Target 10% annual volatility per market: `w_t = S_t · 0.10 / (σ_t·√252)`, capped at ±2 | The trend premium is a volatility-scaled premium |
| **Sizing** (investing) | Long-only, unlevered, **in or out**: `w_t = 1` while `S_t > 0`, else 0. AM-A holds 0.5 while its long move is unaccepted | A tactical allocation, the Faber (2007) use of a trend filter |
| **Portfolio** | Equal risk across markets: the mean of the markets' volatility-targeted returns | Diversification is where trend-following's Sharpe comes from |
| **Execution** | Weights decided at the close, traded at the **next open**. Rebalanced weekly, with a no-trade band of 10% of the target | No look-ahead; turnover held down |

The capitulation lean stays where the v9 audit measured it, as a separate
counter-trend sleeve. Combining the two is a later question, after each stands
on its own.

## 4 · The test

### Candidates (fixed; nothing is added after results)

| ID | Strategy | Family |
|---|---|---|
| T-LS | The trail's state *D* as a position, long +1 / short −1, volatility-targeted | trading (the spec's H4) |
| T-LO | Long while *D* = +1, flat otherwise, unlevered | investing |
| AM | Acceptance Momentum, as §3 | trading and investing |
| AM-A | AM with the acceptance modifier | trading and investing |
| TSMOM | The same as AM with the **close** in place of the POC: isolates what the POC adds | baseline |
| ST | Supertrend(10, 3) state, volatility-targeted | baseline |
| SMA | Long while close > its 200-day average, flat otherwise | investing baseline |
| BH | Buy and hold | investing baseline |

### Data

- Daily OHLCV, as long as each market has, with eras 2006–13, 2014–19 and
  2020–26.
- The universe is the v9 audit's six classes: NSE stocks, US stocks, world
  indices, commodities, FX and crypto.
- Each market is assigned to its class before results are read.

### Costs (one way, on every change in weight)

| Class | Cost |
|---|---|
| Index futures and ETFs | 5 bps |
| FX | 3 bps |
| Commodities | 8 bps |
| US stocks | 10 bps |
| NSE stocks | 15 bps |
| Crypto | 20 bps |

### Measures

- CAGR, annual volatility, Sharpe ratio (net, zero risk-free), maximum
  drawdown, annual turnover, and time invested. Reported per market, per class,
  per era, and for the equal-risk portfolio.
- The mean daily return's t-statistic with Newey-West errors (10 lags).
- The **deflated Sharpe ratio** (Bailey & López de Prado 2014), with the
  number of trials set to the candidates' count.
- The spec's H4 scorer, the v9 audit's: each position centred on its trailing
  250-bar mean, forward 10- and 20-bar returns scaled by trailing volatility,
  Newey-West errors.
- **H5, acceptance discrimination.** This is the engine's distinctive claim,
  added here before results. Each flip and each probe onset is scored by its
  **excess persistence**: whether price is still beyond the trail 10 bars later,
  minus the chance a driftless walk from that distance, at that volatility,
  would be. A flip starts further from the trail than a probe, so raw
  persistence would favour flips even in a random walk; the excess reads ≈ 0
  there. Acceptance is real only if flips' excess exceeds probes'.

### Pass marks: what would make us trade or invest

| Use | Passes only if |
|---|---|
| **Trade** AM or AM-A | Portfolio net Sharpe ≥ 0.5; **≥ TSMOM's Sharpe** (otherwise the POC adds nothing and plain TSMOM is the honest engine); positive in all three eras; deflated Sharpe probability ≥ 0.95; t > 3 |
| **Trade** T-LS | The same marks against ST and TSMOM |
| **Invest** with T-LO, AM or AM-A | Maximum drawdown at least 30% shallower than BH's, with CAGR no more than 1 point a year below BH's, in at least two of the three eras and pooled |
| **Acceptance is real** (H5) | Flips persist more than probes in all three eras, t > 3. Only then may AM-A's modifier be kept |

A candidate that fails is not tuned and retried. A changed definition is a new
hypothesis under a new version of this document, and gets a live out-of-sample
year before any capital.

### Then, if a candidate passes

1. Six months of paper trading on live data, at the same costs.
2. Small capital, one-tenth of the intended size, for six months.
3. Kill rule, fixed now: a drawdown beyond 1.5× the backtest's worst, or a
   rolling 12-month Sharpe below 0 for two consecutive quarters, stops it.

### Corrections made before any data (from the harness's synthetic smoke test)

1. **Investing sizing** was `clip(S, 0, 1)`. |S| is usually 0.3–0.5, so that
   left the portfolio mostly in cash and failed the CAGR mark by construction.
   It is now in-or-out.
2. **H5** compared raw persistence, which a random walk alone tilts toward
   flips (+20 points on synthetic walks). It now compares each event with its
   own random-walk expectation.

## 5 · What is needed to run it

`research/tradability.py` runs everything above on a folder of daily OHLCV CSV
files (one per market: `date,open,high,low,close,volume`):

```
python research/tradability.py --data path/to/csvs --classes classes.csv --out report.md
```

The Sanket audit already holds 20 years of daily data for 380 markets, so the
fastest path is to run it there. This environment cannot fetch market data:
its data hosts are blocked, and attaching Sanket needs the owner's go-ahead.

## 6 · Data addendum (2026-11-02, before any strategy result was computed)

Sanket could not be attached from this session. Yahoo and Dukascopy answered
429, stooq served a browser check, and Nasdaq Data Link did not answer. The
first-party price sets on Hugging Face are gated. This addendum fixes the data
that *could* be reached, and the rules for using it, before the harness runs.
The candidates, costs, measures and pass marks above are unchanged.

### Sources

| Source | What it holds | Used for |
|---|---|---|
| Hugging Face `vishnun0027/indian-market-historical-ohlcv`, revision `825144cb` (MIT; Yahoo Finance via yfinance) | Daily OHLCV for 2,663 NSE stocks, 17 Indian indices, 17 Indian ETFs, 8 commodity futures, 8 INR currency pairs | NSE stocks, indices, ETFs, commodities, FX |
| Binance's public archive, `data.binance.vision`, spot daily klines | Exchange-native daily OHLCV, from 2017-08 | Crypto |

### Universe rules

None of these rules reads a strategy output.

- **NSE stocks** (`nse_stock`, 15 bps):
  - Eligible: equities whose listing date is on or before 2003-12-31 and that
    have at least 300 bars between 2004-01-01 and 2005-12-31.
  - Ranked by median daily traded value (close × volume) over those two years,
    which end before the first era begins.
  - The **top 60** are taken.
- **Indices** (`index`, 5 bps): all 17 index files except INDIA_VIX, which is a
  volatility index, not an investable price.
- **ETFs** (`etf`, 5 bps): all 17 ETF files except LIQUIDBEES, a cash fund with
  a near-constant price.
- **Commodities** (`commodity`, 8 bps): all 8 files.
- **FX** (`fx`, 3 bps): all 8 files.
- **Crypto** (`crypto`, 20 bps):
  - Eligible: USDT spot pairs whose archive begins in or before 2018-12.
  - Excluded: stablecoin bases (USDC, TUSD, PAX, USDP, BUSD, USDS, USDSB, DAI,
    FDUSD) and leveraged tokens (names ending UP, DOWN, BULL or BEAR).
  - Ranked by total quote volume over calendar 2018.
  - The **top 15** are taken, delisted pairs included.
- **US stocks and world indices:** no source could be reached, so these classes
  are **absent**. The verdict covers the five classes above.

### Price treatment

- **Total return.** Open, high, low and close are each multiplied by that bar's
  `adj_close / close` where both exist. Yahoo's OHLC are split-adjusted but
  not dividend-adjusted, so without this, dividends would be missing from every
  long position and from BH.
- **Isolated bad prints.** A bar is dropped when its close is more than 3×, or
  less than ⅓, of *both* neighbouring closes. That is a one-bar spike that
  reverts. The count of dropped bars is reported.
- **Missing volume.** It is passed as missing. The participation weight then
  falls back to relative true range, as Pragati's *Auto* mode does on a chart
  without volume. This applies to all FX and parts of the index history.
- **Crypto.** UTC daily bars; the archive's quote-asset volume is not used.
- The harness's own rules stand: nonpositive bars are dropped, and a market
  needs at least 600 bars.

### Known biases, stated before the result

1. **Survivorship.** The NSE file set is today's listings, so stocks delisted
   since 2004 are missing. This flatters buy-and-hold and long-only rules most.
2. **Concentration.** This is mostly one country. Fifteen Indian sector indices
   and index ETFs are highly correlated, so the equal-risk portfolio is less
   diversified than its market count suggests. That works against the trend
   portfolio's Sharpe, not for it.
3. **Commodity rolls.** Yahoo's continuous futures are not roll-adjusted, so
   each roll shows as a price jump.
4. **Missing classes.** US stocks and world indices are absent. The literature's
   trend premium is strongest in exactly the diversified futures universe that
   this sample lacks.

### 6.1 · Amendment (same day, after a data-quality scan, still before any result)

A scan of the assembled files found defects the close-only rule misses. The
harness trades **opens**, and its ranges use all four prices:

- **Bad opens.** On 2011-07-20, every INR pair opens at a tenth of the
  previous close but closes normally.
- **Two-bar ÷10 episodes.** Five ETFs on 2019-12-19/20; MON100 on 2021-06-17/18.
- **Unadjusted demergers**, each a single persistent gap:
  - BAJAJHLDNG on 2008-03-14 (−65%)
  - MASTEK on 2015-06-12 (−66%)
  - ABREL on 2019-10-11 (−56%)
  - VEDL on 2026-04-30 (−63%)

Left in, a ±2 volatility-targeted position takes a false loss of up to 130% in
a day.

The bad-print rule is therefore replaced, and one rule is added:

- **(a) Bad prints.** An episode of 1 to 5 consecutive bars is dropped when
  every bar in it has an open, high, low or close more than 3×, or less than
  ⅓, of both the last close before the episode and the first close after it.
- **(b) Unadjusted corporate actions** (all classes but crypto). After (a), an
  overnight gap with `open_t / close_{t−1}` below 0.5 or above 2.0 is treated
  as an unadjusted split, bonus or demerger. Every earlier open, high, low and
  close is scaled by that ratio, so a holder's return across the gap is zero.

Genuine crashes are intraday, and (b) leaves them alone. GTL's −90% on
2011-06-20 is kept.

**Known residual:** smaller unadjusted demergers stay in the data. Tata Motors'
on 2025-10-14 is one.

## 7 · Result (2026-11-02, the harness run unchanged on the §6 data)

**Files** (in `research/results/2026-11-02/`):
- `report.md`: the harness's own output.
- `diagnostics.md`: the per-class and per-era measures §4 promised.
- `timing-exploratory.md`: **not** pre-registered.
- `universe.csv`: holds each file's sha256.
- `build-log.txt`: every dropped bar and neutralised gap.

119 of the 123 markets reached the harness; four have fewer than 600 bars.

### Verdict: no candidate passes. Trade or invest with neither the trail nor Acceptance Momentum.

| Candidate | Use | Result | Mark |
|---|---|---|---|
| T-LS | Trade | Sharpe +0.48, t +2.90. 2014–19 −0.05 | **Fail**: below 0.50, TSMOM (+0.58) and ST (+0.51) |
| AM | Trade | +0.52, t +3.04. 2014–19 −0.02 | **Fail**: below TSMOM; one era negative |
| AM-A | Trade | +0.51, t +3.01. 2014–19 −0.02 | **Fail**: as AM |
| T-LO | Invest | Max DD −35.0% vs BH −73.5%; CAGR +13.5% vs +24.4% | **Fail**: CAGR 11 pts short; 0 of 3 eras |
| AM | Invest | −44.7%; +15.9% | **Fail**: 0 of 3 eras |
| AM-A | Invest | −44.4%; +15.5% | **Fail**: 0 of 3 eras |
| H4 | Trail state predicts | 10 bars +0.006 (t +0.16); 20 bars +0.002 (t +0.04) | **Null** |
| H5 | Acceptance | Flips beat probes by +2.1 pts pooled (t +3.69). By era: −0.2 (t −0.19), +2.4 (t +2.12), +3.7 (t +3.61) | **Fail**: needs every era, t > 3. AM-A's modifier is not kept |

### What the numbers say

1. **The POC adds nothing over the close.** AM's Sharpe is 0.52 against TSMOM's
   0.58, and it trails TSMOM in five of six classes. The exception is the eight
   commodities: 0.52 against 0.46.
2. **The trail has no timing skill; what it earns is drift.**
   - H4 is null.
   - The exploratory centred score is t +0.09, positive in 49% of markets: a
     coin toss.
   - The trail's average position is long (+0.20 on a unit scale), so T-LS
     earns what a long tilt earns in rising markets.
   - TSMOM, by contrast, is positive in 70% of markets.
3. **As an investing filter it does halve drawdowns, at a price.**
   - Pooled, it costs about 11 points of CAGR a year.
   - In the common-start sensitivity, BH gets no head start during the push
     gate's warm-up. There it costs 6 points, and the drawdown cut shrinks
     to 26%.
   - Every trend filter tested buys protection at about the same price. SMA200
     reached −45% drawdown with +15.7% CAGR. The trail is no cheaper than they
     are.
4. **Acceptance is real but unstable.**
   - Ten bars on, flips are still beyond the trail 3.4 points more often than a
     random walk would leave them; probe onsets 1.2 points more.
   - The gap appears only after 2014.
5. **The one engine that clears the trading marks is the baseline, plain
   TSMOM.**
   - Sharpe +0.58; eras +0.62 / +0.15 / +1.13; deflated p 1.000; t +3.58.
   - Positive in 86% of markets.
   - It is the literature's engine, entered here as a baseline. Its showing is
     a replication on Indian and crypto data, not a Pragati discovery.
   - It was weak in 2014–19 and negative in FX.
6. **§2's single-stock worry did not appear.** Trend on NSE stocks was positive:
   TSMOM +0.51, T-LS +0.43. Survivorship (§6, bias 1) may flatter this.

### What follows, under §4's rules

- No candidate is tuned and retried.
- The trail stays what §2 said it is good for: **structure for a discretionary
  reader**. It shows where value was last accepted and where a stop belongs.
- If a systematic trend book is wanted, this evidence points to TSMOM on the
  close, diversified across many markets. That is a **new hypothesis**. It
  needs its own pre-registration and a live out-of-sample year, then paper
  trading, one-tenth size, and the kill rule.
- Before any of that, this test should be repeated on Sanket's 380 markets.
  Sanket holds the US stocks, world indices and futures that this sample lacks.
