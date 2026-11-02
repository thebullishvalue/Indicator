# Trail lab: an iterative council for a trail engine with an edge

**Status:** the protocol (§1–§4) was written and committed on 2026-11-02,
**before any variant in this document was run**. The rounds (§5) are a lab
notebook. Each round's proposals are written down before they run, and every
trial is logged, failures included.

**Why a protocol.** The tradability test (`docs/trail-tradability.md` §7) failed
every candidate on 119 markets. Searching that same data until something
passes would *manufacture* an edge, not find one. So the search is confined to
a development set. The verdict comes from a holdout that no variant has
touched, run once.

---

## 1 · What "a trail engine" means here

A trail engine outputs, on every bar:
1. A **position**: a signed size, decided at the close and traded at the next
   open.
2. A **trail**: the price at which that position would change sign, which is
   the engine's decision boundary drawn on the chart.

For the acceptance trail, the trail is its ratcheted level. For a
momentum-score engine, it is the close *C\** at which the score would be zero.

So "has an edge" is a claim about the position. The trail is how the position
is shown.

## 2 · Data split

| Set | Markets | Dates | Role | Status |
|---|---|---|---|---|
| **DEV** | The 119 markets of `research/results/2026-11-02` | ≤ 2019-12-31 (eras 2006–13 and 2014–19) | Every iteration is scored here, and only here | Seen: the eight earlier candidates' results are known |
| **HB** (time holdout) | The same 119 | 2020-01-01 → 2026-10-31 | Final test, run once | **Partly seen.** TSMOM's 2020–26 Sharpe (+1.13) is already known, so HB is not clean for TSMOM itself. It is clean for every new variant's *difference* from TSMOM |
| **HA** (market holdout) | Markets never used in any result | Full history | Final test, run once | **Unseen** |

**HA's markets**, built under `docs/trail-tradability.md` §6 and §6.1's price
rules:
- **NSE stocks:** every remaining eligible stock, ranks 61–451 by 2004–05
  median traded value (391 stocks). The top 60 are in DEV.
- **Crypto:** Binance USDT spot pairs, with the same exclusions as before,
  whose archive begins between 2019-01 and 2021-12. Ranked by quote volume over
  their first 12 months; the top 20 are taken.

Signals are always computed on a market's full history, since every signal at
bar *t* uses data up to *t* only. Each set simply scores the returns that fall
on its own dates.

## 3 · Rules of iteration

- **Machinery is fixed.** It is identical to `research/tradability.py`:
  - weights decided at close *t*, held from open *t+1* to open *t+2*;
  - 10% volatility target per market, capped at ±2;
  - weekly rebalancing, a 10% no-trade band for continuous sizes, and
    immediate sign changes;
  - the same per-class costs;
  - the equal-risk portfolio.
- **Budget:** at most **15 variants**, over at most **4 rounds**. Each variant
  needs a stated hypothesis from the literature or from evidence already in
  hand. A bare parameter sweep is not a variant.
- **DEV measures** for each trial:
  - net Sharpe, CAGR, max drawdown and Newey-West t;
  - Sharpe in each DEV era;
  - breadth (the share of markets with net Sharpe > 0);
  - annual turnover;
  - the **timing component**, defined below;
  - the deflated Sharpe probability, with trials = 8 (earlier) + the
    variants run so far.
- **The timing component** is the strategy rerun with each weight replaced by
  `w_t − mean(w_{t−249..t})`, gross of costs. That removes whatever the engine
  earns from simply leaning long in rising markets. T-LS's timing component
  was ≈ 0 (`timing-exploratory.md`). An engine with an edge must have a
  positive one.
- **Selection.** The winner has the highest DEV net Sharpe among variants that
  meet both conditions:
  1. positive in both DEV eras;
  2. a positive DEV timing component.

  Variants within 0.02 of each other go to the one with fewer moving parts.
- **Freeze.** The winner's code is committed and its hash written here
  *before* HA and HB are built into results. They then run **once**.

## 4 · Pass marks (fixed now)

**"The engine has an edge"** requires, on **each** of HA and HB:
1. a net portfolio Sharpe > 0 with Newey-West t ≥ 2.0; and
2. a timing component with Sharpe > 0 and t ≥ 2.0.

**"It improves on plain TSMOM"** requires, on each of HA and HB, that the daily
return difference (winner − TSMOM) has t ≥ 2.0. Otherwise its edge is called
what it is: TSMOM's.

**Context, not gates:**
- the tradability marks (`docs/trail-tradability.md` §4);
- per-class results;
- a 2× cost sensitivity.

If the winner fails, the holdout is spent. No variant is rescued on it.

---

## 5 · Lab notebook

(Rounds are appended below, each written before it runs.)

### Round 0 · reference (outside the budget)

The eight earlier candidates, rescored on DEV (`research/results/lab/trials.md`).
TSMOM's DEV eras (+0.62, +0.15) reproduce the tradability report exactly.

One **harness bug** was found and fixed before any variant ran. The timing
component centred each weight over a window that counted the warm-up's zeros.
That gave buy-and-hold, a constant position, a spurious timing Sharpe of +0.56.
The window now starts at the first live weight, and a constant position scores
exactly zero.

On DEV, no engine's timing component reaches t 2: TSMOM +0.18 (t 1.0),
Supertrend +0.34 (t 1.9), T-LS +0.19 (t 1.0). **Most of what every trend
engine earned on DEV was drift.** That is the bar Round 1 faces.

### Round 1 · proposals (written before running)

**Diagnosis**, from the evidence in hand:
1. The acceptance trail works at 20 bars, where no engine shows timing skill.
2. The POC adds nothing over the close.
3. Every engine's DEV return is mostly drift.

Round 1 tests the three levers that could create timing skill: **horizon**,
**sizing**, and **the information used**.

| Variant | Lever | Hypothesis | Seat that proposed it |
|---|---|---|---|
| TSMOM | — | Reference, the engine to beat (lab parity check; not budget) | — |
| BOUND | sizing | A trail is binary. Does sign(S), the side of TSMOM's decision boundary, keep its edge? The literature says continuous beats sign (Baltas & Kosowski 2013) | Pine engineer: the trail must be drawable |
| TRAIL126 | horizon | The acceptance trail re-horizoned to a 126-bar (6-month) profile, where trend premia live. Spec v2 otherwise | Inventor: give the trail its fair test |
| SKIP21 | horizon | Single stocks reverse at one month (Jegadeesh 1990). Drop the 21-bar horizon | Quant |
| PMOM | information | Weight each return by participation *w*. Moves on high participation carry more information (Pragati's premise; Gervais, Kaniel & Mingelgrin 2001) | Conviction-engine seat |

Statistician's note: with timing t ≈ 1 on DEV even for TSMOM, a variant that
"wins" by 0.05 in Sharpe is noise. Round 2 is designed from *patterns* across
classes and eras, not from the top line.
