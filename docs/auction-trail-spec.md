# Pragati v9.4 · Auction engine and Acceptance Trail — frozen specification

**Status: FROZEN on 2026-11-02, before any market result was seen** (one
design revision on synthetic data is logged in §4.3).
The Pine implementation (`pragati.pine`, section *AUCTION ENGINE · ACCEPTANCE
TRAIL*) and the Python reference in the audit port are both built from this
text and must agree bar for bar on §2–§4. Changing any definition or constant
below creates a **new hypothesis**: write a new version of this document, with a
new date, and say so in the script header.

---

## 1 · Purpose and scope

The volume profile is the only part of Pragati that measures *where volume was
accepted*, which is different from *which way bars closed*. This engine turns
it into:

1. a **migration state**: is value moving, and which way;
2. an **Acceptance Trail**: a stepped line on the price chart showing where
   value was last accepted, coloured by the pane's verdicts.

It is **display-only** in v9.4. Nothing here feeds a signal, a tape, the grid
or the pane. §6 lists the tests that decide what it may claim later.

**It does not read the display volume profile.** That profile's compute follows
display switches, its session changes with timeframe (D / W / M), and its
intrabars reach back only a few years. This engine builds its own profile from
the chart's OHLCV, so it is the same on every setting, stationary across 20
years, and can be rebuilt in Python.

## 2 · Inputs per bar *t*

| Symbol | Definition |
|---|---|
| OHLCV | the chart's own bars |
| *N* | the conviction **Lookback** input (default 20); no separate input |
| ATR20 | `ta.atr(20)` (Wilder RMA of true range), floored at `syminfo.mintick`; `mintick` where undefined |
| *usesVolume* | the share of bars so far (expanding, from bar 0) carrying `volume > 0` is ≥ 0.5 |
| *push* | the Conviction-Value Grid's push gate `gGate` ∈ {+1, 0, −1}, built from conviction's own histogram (not the trace's); undefined counts as 0 |

## 3 · Rolling composite profile (window = bars *t−N+1 … t*)

Defined from bar index *N−1* onwards.

1. `lo` = lowest low, `hi` = highest high over the window.
2. Bin width `b = max(ATR20_t / 4, mintick)`. Bin count `nb = floor((hi − lo) / b) + 1`.
   If `nb > 300`: `b = (hi − lo) / 299`, `nb = 300`.
3. Each bar's weight `w` = `max(volume, 0)` (na → 0) if *usesVolume*, else `1`
   (time at price). Bars with `w = 0` contribute nothing.
4. Bin of a price `x`: `clamp(floor((x − lo) / b), 0, nb − 1)`. Each bar's
   weight is spread **evenly** over the bins from its low's bin to its high's
   bin inclusive (swapped if inverted).
5. If the total weight is 0, the profile is undefined for that bar.
6. **POC bin**: the bin with the largest weight. Ties (relative tolerance 1e−9)
   go to the bin whose index is nearest `(nb − 1) / 2`; if still tied, the lower
   index.
7. **Value area**: start with the POC bin. While the accumulated weight is below
   70% of the total and a neighbour exists, add the next bin above or below,
   whichever holds more weight. A missing side counts as −1; the upper bin wins
   ties.
8. `POC_t = lo + (kPOC + 0.5)·b`, `VAL_t = lo + kLow·b`, `VAH_t = lo + (kHigh + 1)·b`.

## 4 · Migration state and Acceptance Trail

### 4.1 Migration state *M_t*

This compares the current window with the window that ended *N* bars earlier,
using `VAL_{t−N}`, `VAH_{t−N}` exactly as they were computed on bar *t−N*.

| *M_t* | Name | Condition (first match) |
|---|---|---|
| +2 | Migrating ↑ | `VAL_t > VAH_{t−N}` (value areas no longer overlap, above) |
| −2 | Migrating ↓ | `VAH_t < VAL_{t−N}` |
| +1 | Shifting ↑ | `POC_t > VAH_{t−N}` |
| −1 | Shifting ↓ | `POC_t < VAL_{t−N}` |
| 0 | Balance | otherwise |

*M_t* is undefined if any input to it is undefined.

### 4.2 Acceptance Trail

State: direction *D* ∈ {+1, −1, 0} (0 = not started) and level *T*. Updated
**on closed bars only**. Each bar first clears its *probe* and *flip* flags.
Nothing happens on a bar where *M_t* or `POC_t` is undefined.

- **Start** (*D* = 0): if `M_t ≥ +1` and `push > 0` and `close ≥ VAL_t`, then
  *D* = +1 and *T* = `VAL_t`. If `M_t ≤ −1` and `push < 0` and `close ≤ VAH_t`,
  then *D* = −1 and *T* = `VAH_t`.
- **Up** (*D* = +1), checked in this order:
  1. **Flip**: `close < T` and `POC_t < T` → *D* = −1, *T* unchanged (the broken
     floor becomes the ceiling). *flip* = true.
  2. **Probe**: `close < T` (and `POC_t ≥ T`) → *probe* = true; nothing else changes.
  3. **Step**: `M_t ≥ +1` and `push > 0` and `VAL_t > T` and `close ≥ VAL_t`
     → *T* = `VAL_t`. A floor is never lifted above price.
- **Down** (*D* = −1): the mirror image (flip on `close > T` and `POC_t > T`;
  probe on `close > T` alone; step on `M_t ≤ −1`, `push < 0`, `VAH_t < T`,
  `close ≤ VAH_t` → *T* = `VAH_t`).

So the trail is the **ratcheted far edge of value**: the value-area low while
up, the value-area high while down, which is the floor or ceiling of where the
market has accepted price. It steps only when value shifts or migrates its way
**and** conviction confirms a push that way, which is the same gate by which the
grid moves a row. It flips only on **acceptance**: price beyond it *and* the
market's value (the POC) following. Price beyond it without that is a probe,
which in Market Profile terms is price outside value that has not been accepted.

### 4.3 Design-validation log (before any market data)

The first draft stepped the trail to the **current POC**. Run through the
Python reference on synthetic regime-switching random walks (6 × 2,000 bars,
with a stand-in push), it flipped once every 16 bars, against once every 43
for Supertrend(10, 3). The trail sat on top of value, so the POC only had to
drift one bin for a close beyond it to count as "accepted". Three alternatives
were checked on the same synthetic data:

| Trail level | Bars per flip | Probes |
|---|---|---|
| current POC (draft) | 16 | 2,019 |
| previous window's POC | 60 | 1,682 |
| **current value-area edge (adopted)** | **45** | 2,299 |
| current POC, acceptance = whole value area beyond | 52 | 4,670 |

The value-area edge was adopted **on principle**: it gives acceptance its
Market Profile meaning (price outside value is a probe; value following is
acceptance), and it is what the council described as "the floor of accepted
value". Its cadence close to Supertrend's was a sanity check, not the
criterion. A second check on the same data found a step could lift the floor
above the close on 0.2% of bars; steps now also require the close on the
trail's side of the new level (`close ≥ VAL_t` up, `≤ VAH_t` down), and so
does the start. No market
data was used, so both revisions precede the freeze. From here on, §7 applies.

## 5 · Display (Pine only; not part of any hypothesis)

- **Trail line**: the level *T*, hue by *D*. Intensity follows the conviction tape *C* in the
  trail's direction (`D·C ≥ outer zone` solid, `≥ inner zone` strong, `> 0`
  moderate, `≤ 0` faint; moderate while the tape is warming). It turns **gold**
  when the value tape is stretched past θ in the trail's direction
  (`D·V ≥ θ`): the move is already paid for, so it is late.
- **Value ribbon**: the rolling value area (`VAL_t`…`VAH_t`) as a band in the
  profile's identity blue, with the rolling POC dotted, over the last 1,500
  closed bars.
- **Probe marks**: a gold × at the close of each probe bar (the latest 40).
- **AUCTION row** in the readout: STATE = *M_t*'s name; WHY = trail direction and
  where the close sits against the value area (or the live probe); PUSH = the
  grid's push; CHART = the trail level; SPAN = bars since the trail started or
  last flipped.
- **Alert** (opt-in): trail flips, through the one *Any alert() function call* alert.

## 6 · Pre-registered hypotheses

**Scorer**: the v9 audit scorer, unchanged.
- Each position is centred on its own trailing 250-bar mean, and returns are
  scaled by trailing volatility, with no look-ahead.
- Forward horizons of 10 and 20 bars.
- Three eras (2006–13, 2014–19, 2020–26), on daily and weekly bars.
- Six classes: NSE stocks, US stocks, world indices, commodities, FX and crypto;
  stocks are also scored by cross-sectional rank IC.

**Significance**: t > 3 (Harvey, Liu & Zhu 2016), with overlapping windows
accounted for. The three eras were already used for v9, so a pass also needs a
live out-of-sample period of at least one year before anything becomes a
default.

| ID | Hypothesis | Pass | Kill |
|---|---|---|---|
| **H1** | *M_t* carries information beyond the tapes: \|ρ(*M_t*, C)\| and \|ρ(*M_t*, V)\|, pooled daily | both < 0.6 | either > 0.7 → the engine restates the tapes; remove the AUCTION row's verdict wording |
| **H2** (primary) | Inside the capitulation cell (grid DOWN · cheap), forward returns when the decline is **unaccepted** (`M_t ≥ 0`) exceed those when it is **accepted** (`M_t ≤ −1`) | positive in all three eras, daily **and** weekly, in ≥ 4 of 5 non-crypto classes, t > 3 pooled; the smaller side holds ≥ 20% of the cell's bars in every era | any era negative, or the smaller side < 20% → no gate, ever, on this definition |
| H2-secondary | The same split on the trail: unaccepted = `D ≠ −1`, accepted = `D = −1` | reported only | — |
| **H2b** | Mechanism: on crypto, unaccepted capitulations are positive | sign reported; if positive, a regime gate may replace the crypto symbol-type rule | — |
| **H3** | The trail state *D* carries information beyond the conviction tape: \|ρ(*D*, C)\| | < 0.6 | > 0.7 → keep the trail's levels, drop its verdict colouring |
| **H4** | *D* held as a position (long +1, short −1) | expected positive on futures, FX, crypto and weekly bars; expected ≈ 0 or negative on daily stocks | decides only the wording; the trail never becomes a signal on this test alone |

## 7 · Rules

- **No tuning after results.** *N*, the bins (ATR/4, cap 300), 70%, the tie
  rules, the push rule and the acceptance rule are fixed. Any change is a new
  hypothesis under a new version of this document.
- **Ship order**: display (v9.4) → tests → a gate only on an H2 pass, as an
  option whose default follows the result, never a silent change to the ▲.
- **Parity**: Pine and Python must agree on *M_t*, *D* and *T* on every bar of a
  shared test file before any result is read.
