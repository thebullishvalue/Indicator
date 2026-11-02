# Pragati v9.6 · Engine audit

**Question.** Does any engine or implementation need more depth or support so
that the v9.4 Acceptance Trail, Pragati's trend layer, is robust?

**Method.**
- Every engine was read for what it hands the trail and for defects of its own.
- Each suspicion was turned into synthetic data built to provoke it:
  regime-switching walks, two-cluster ranges, low-volatility grinds, and
  expiry-like volume spikes of 12–30× normal.
- A fix was adopted only on principle, and only after the defect replicated on
  fresh seeds.
- **No market data was read and no hypothesis was run**, so the spec's
  pre-registration (H1–H4) is intact.

The scripts are a Python port of each mechanism plus the trail's reference
(`reference/auction_trail.py`). They are not a substitute for compiling in
TradingView.

---

## 1 · What the trail leans on

```
chart OHLCV ─┬─► participation weight w  (conviction engine) ─► rolling profile ─► POC · value area
             └─► ATR(20) ─► bin width ──────────────────────────┘                    │
conviction's histogram ─► the grid's push gate gGate ─► trail starts / steps ◄─ migration ◄┘
conviction tape · value tape ─► the trail's colour (intensity · gold)
```

The display volume profile is **not** an input, by design. It is session-
anchored, its compute follows display switches, and its intrabars reach only a
few years back. The audit re-examined that choice and kept it (§3).

## 2 · The trail itself: four defects found and fixed (spec v2)

Every result below is from 24 fresh seeds × 3,000 bars. The first eight seeds
found each defect; the 24 replicated it.

| | Defect | Evidence | Fix |
|---|---|---|---|
| W1 | Raw volume weighted the profile, so one spike owned the POC for *N* bars | Flips were **2.02×** likelier on the bar a spike *left* the window, where nothing happened; the POC jumped 1.87× more there | Weights = the conviction engine's capped participation *w*, the cap Pragati already measured for exactly this. The artifact falls to 1.48× (1.65× with W2's fix) |
| W2 | Bins anchored at the window's low and re-derived from ATR every bar | **29.4%** of the value area's bin-sized moves were phantom against a fine reference grid | Absolute grid, width a power of two of the tick near ATR/4: phantom moves 25.7%, flips −15%, range whipsaw −19% |
| W4 | In a balanced range the POC hops between two clusters and counted as acceptance | Range whipsaw of 41.0 flips per 1,000 range bars after W1 and W2 | A flip also needs migration that way. Whipsaw falls to **18.8**, all flips 27.2 → 14.9, trend agreement 83.2% → 84.2% |
| — | A gold × on every probe bar | Probe bars were 22–27% of the chart | Mark onsets only: about 55 per 1,000 bars, median episode 4 bars |

**Cost, stated.** Acceptance-by-migration adds about **6 bars of median lag on
genuine reversals** (18 → 24; p90 47 → 51). Supertrend(10, 3) on the same data:
median 13 bars, but more flips.

**Invariants checked on every bar:** price is on the trail's side except on probe
and flip bars; every flip has migration in its direction; every onset is a
probe whose previous bar was not.

## 3 · Engine by engine

| Engine | Role for the trail | Checked | Verdict |
|---|---|---|---|
| **Conviction core** (`f_convCore`) | Now supplies the profile's weight *w* | Participation cap, hollow-bar carry, zero-range bars, the shared core used three ways | **Sound.** It is the source of the W1 fix. Under *Participation · Off* the profile becomes time-at-price, consistently. |
| **Push gate** (`gGate`: histogram tiers, quiet regime) | Opens the trail's start and steps | Ported and run per regime. Suspected of shutting in smooth low-volatility trends | **Sound; suspicion rejected.** Quiet on 10.6% of grind bars against 43% of range bars; the trail sits on its side 92.6% of the time in a grind. Its **≈ 450-bar warm-up** (1.8 years daily, 8.7 weekly) is now named in the readout. |
| **ATR(20)** (`vpATR`) | Bin width | Floor at the tick; behaviour with W2 | Sound. W2 changed how it is used, not what it is. |
| **Display volume profile** | None by design | Re-examined as a possible source of depth: intrabar fidelity | **Kept independent.** Intrabars would make the trail's quality change with history depth and break 20-year parity. Its own volume test was lifetime-based (W3) and now reads the last 500 bars. |
| **Conviction ladder** (up and down) | The trail's intensity | Reconstruction pattern, depth disclosure | Sound. Ladder *confirmation* of the trail is deferred (§4). |
| **Samanvaya value engine** and value ladder | The trail's gold ("paid for") | Driver timing, self-screen, hedge skill, ensemble, breadth | Sound for this role. **One inherited gap:** its breadth leg's flow-member test is the same lifetime-based volume test as W3. It is left unchanged here to keep parity with `samanvaya.pine`; fix both in lockstep. |
| **Grid and ▲▼** | Shares the push gate; H2 splits capitulation by the trail | v9.3 gate, first-readable rule | Sound. |
| **Divergence R/H, continuation ◆** | None | — | Unchanged; measured null or negative, off by default. |
| **Open interest** | None | — | Display only; unchanged. |
| **Whole indicator** | — | Chart types | **G1 fixed:** on non-standard charts (Heikin Ashi, Renko, Kagi, Point & Figure, range bars) every family pauses with the reason shown, and the auction engine stands down. |

## 4 · Depth deliberately not added yet

Each item below is a real candidate. Each changes what the trail claims, so
each waits for H1–H4 rather than being added on design grounds:

1. **Ladder confirmation:** the trail on the next higher frame, through one
   request (37 → 38 of 40), so a flip can be "accepted on two horizons".
2. **Ladder-gated steps:** step on the conviction *tape* rather than the
   chart's own histogram.
3. **A softer window edge:** weight bars by recency so a spike's exit fades
   instead of stepping. W1's fix already removed most of the artifact; the
   residual is 1.65×.
4. **Volatility-aware bins:** an ATR percentile in place of ATR/4.

The next real evidence is the spec's H1–H4 in the audit port, with
`reference/auction_trail.py` for parity.
