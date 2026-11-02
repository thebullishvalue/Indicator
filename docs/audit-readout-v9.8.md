# Pragati v9.8 · Audit of the readout table: OI, CVG and AUCTION rows

**The question.** Does every cell in the readout say what its engine actually
computes, at the moment it says it, with every edge case covered and every
tooltip true?

**Method.** Four checks, each listed below with its evidence.
1. Every cell was traced from its source series to its text, colour and tooltip.
2. Each claim in a tooltip or comment was compared with the code line by line.
3. Each suspicion was made a test:
   - **probe parity:** the engine's own reference trail on 119 markets;
   - **grid properties:** a literal port of the grid's state engine on 200,000
     random bars;
   - **OI scenarios:** a literal port of the OI block on scripted feeds.
4. A fix was adopted only where a defect was demonstrated, and each fix was
   re-tested.

The scripts are in `research/audit/`. None of them is a substitute for compiling
in TradingView.

**Out of scope.** The engines themselves were not re-validated here: the
conviction tape, the value tape and Samanvaya. The v9 audit's numbers quoted in
tooltips come from the Sanket repository, which is not reachable from this
session, so they were **not** re-verified. They are marked *external* below.

---

## 1 · Defect register: what was wrong, and how it was proven

| ID | Row | Severity | Defect | Evidence | Fix (v9.8) | Re-test |
|---|---|---|---|---|---|---|
| **A1** | AUCTION | **High**: the readout contradicts the chart | The probe test checked only "POC not following". Since spec v2, a break is also a probe when the POC followed but value had **not migrated**. On those bars the readout said "in value", in neutral grey, while the engine recorded a probe and could mark it with a gold × | `probe_parity.py`, against the reference trail on 119 markets: the engine had 140,686 probe bars at 126 bars and the readout **missed 26,337 (18.7%)**; at 20 bars it missed 12,875 (13.9%). It never claimed one the engine did not | The test now mirrors the engine: beyond the trail is **accepted** only with the POC beyond **and** migration that way; anything less is a probe; with no POC or migration reading, no call is made. An accepted break on the live bar reads "accepted, flips at the close" | 140,686 / 140,686 and 92,909 / 92,909 agree, with **0 missed and 0 extra**. "Accepted" appears on **0** closed bars, as it must, since an accepted break has already flipped |
| **G1** | CVG, OI, AUCTION | **High**: readings from synthetic prices | v9.6 paused every pane family on non-standard charts (Heikin Ashi, Renko, Kagi and others). The readout was missed: the grid's readability flag was the two tapes alone, so CVG showed a family and units built from synthetic prices. OI took its side from a synthetic close. AUCTION stood down but blamed "no trail yet" | Code: `gRead = mtfCOk and mtfVOk`, with no `chart.is_standard`. `oiDpx` uses the chart's `close`. The AUCTION row's reason text had no non-standard branch | The grid's readability flag now includes `stdChart`, so the CVG row, its background tint and its alerts pause. The OI reading needs `stdChart`, and its state reads "Paused · non-standard chart". AUCTION says "non-standard chart" | By construction. A chart-type test needs TradingView |
| **O1** | OI | **Medium**: a false reading | Until 10 accepted changes exist, the σ baseline is empty and `oiZ` is forced to 0. For the first ten live bars **every** bar read "Balanced +0.0σ", through any build or unwind | `oi_scenarios.py`, a steady 1–2% daily build with price rising: v9.7 reads "Balanced +0.0σ" on bars 49–58, then "Long build-up +1.1σ" | The feed (`oiLive`) is separated from a reading (`oiHas`, which also needs the baseline). The feed state is "Warming · building its baseline". Structural bars are still screened during the warm-up by the share rule, which needs no σ | v9.8 reads "Warming" on bars 49–58, then the same build-up |
| **O2** | OI | **Medium**: text contradicts code | The tooltip defined BALANCED as "the change is inside 0.5σ of zero". The code also returned balanced whenever the close was **unchanged**, however far the book moved, and WHY then said "no net change" | `oi_scenarios.py`: a +15% book (+8.1σ) on an unchanged close reads "Balanced · no net change" | The state reads "Price flat · no side to read" when \|z\| > 0.5σ and the close did not move. The tooltip lists PRICE FLAT | v9.8 reads "Price flat +8.1σ" |
| **A2** | AUCTION | Low: an inconsistent column | PUSH showed "—" whenever the tapes were not ready, but the trail steps by the push gate regardless of the tapes. For as long as the tapes were warming, the row hid the push the trail was obeying | Code: the push text was gated on the grid's readability, which the trail does not use | PUSH is gated by the gate alone, on both rows | By construction |
| **C2** | CVG | Low: undisclosed | During the push gate's warm-up (≈ 450 bars at the defaults), rows track the tape with **no memory**: `na(gGate)` snaps `gRow` to the target. That is by design, but the row never said so, and the reading was not yet the grid Pragyam reads | Code, line `if na(gRow) or na(gGate)`. The property test's P3 holds only when a gate exists | WHY appends "· gate warming". The ▲ was already safe, since it needs `cvReady` | By construction |
| **O3** | OI | Low: breaks the colour grammar | "No OI", the correct answer on cash equity and spot, was painted **gold**, the script's word for caution | Code: `not oiHas ? C_GOLD` | Neutral when the symbol has no open interest at all. Stale, daily-only, no-symbol, warming and paused stay gold | Visual |
| **O4** | OI | Low | An untrusted series (ρ < 0.20) faded its text but kept a full background tint | Code | The background fades with the text | Visual |
| **O5** | OI | Low: robustness | The σ baseline's push ran on every realtime update. Pine rolls `var` state back between updates, so this is not known to double-count, but the trail's own pushes are guarded and this one was not | Code review | Committed at `barstate.isconfirmed`. History is identical, since every historical bar is confirmed | No historical change, by construction |
| **S1** | All | Low: inconsistent units | SPAN read "1 bar" but then "2d" on a daily chart. AUCTION counted the flip bar as 0, so a fresh flip showed a blank span, while OI and CVG count their first bar as 1 | Code: `f_span`, and `bar_index − TS.since` | One unit throughout ("1d", "2d"; "1 bar", "2 bars" intraday). AUCTION counts its first bar as 1 | By construction |
| **H1** | Header | Low: undocumented | The column CHART means different things on the CVG and AUCTION rows, against the section's own rule that "every column means the same thing on every row". The header cells had no tooltips | Code | Each header cell defines its column row by row. The section comment says CHART is "one more reading per row" | Visual |

**Cost.** The compiled-token estimate rises from ≈ 98,970 to ≈ 99,450,
against the 100,256 ceiling. No plot, request or drawing count changed.

## 2 · Checked and sound

### CVG: the state engine (`research/audit/grid_props.py`, 195,925 readable bars)

| Property the tooltips state | Result |
|---|---|
| P1 · units stay inside the map's range [0.25, 4] | pass |
| P2 · the shaded position stays inside the map | pass |
| P3 · a row moves only on a push its way | pass |
| P4 · a row that moves lands on its tape | pass |
| P5 · an unheld, confirmed row sits at or past the knee's ink (≥ 0.65) | pass |
| P6 · the FAINT row stays inside ±0.33 | pass |
| P7 · a held name sits between its held row and half-way to the neighbour, by the push's strength | pass |
| P8 · the map's corners are the nine cells | pass |

| Cell | Claim | Verdict |
|---|---|---|
| STATE | The action and units: the family's units read bilinearly at the shaded position | Sound. The unit table matches the tooltip cell for cell (UP 3 · 1.5 · 0.75; FAINT 1.5 · 1 · 0.75; DOWN 4 · 1.5 · 0.25). Colour follows the side the action works: Buy and Accumulate +1, Trim and Exit −1, Hold and Wait 0 |
| WHY | Each momentum's phase on its own edge, its side held until it crosses its own knee; HELD in gold | Sound. The phase and wording table matches the code. New: gate warming, non-standard chart |
| PUSH | ↑↑ an impulse, ↑ a push, TURNING, QUIET in gold | Sound: tier 0 → ↑↑, tiers 1–2 → ↑, tier 3 → turning, the quiet regime → quiet |
| CHART | This chart's conviction and value on the tapes' own cuts, compared by units with the state | Sound. It compares unshaded cell units, as stated |
| SPAN | Bars in the family, never counted twice live | Sound. A scalar `var` is rolled back on each realtime update |
| ▲ / ▼ | Entered means entered | Sound: `gRead[1]` and not-already-in. The ▲ needs `cvReady` and a standard chart (`triOk`) |

### OI

| Cell | Claim | Verdict |
|---|---|---|
| Companion symbol | Built from prefix and ticker, never `tickerid`; malformed → a null symbol | Sound |
| Look-ahead | — | None: same-timeframe `request.security`, `lookahead_off` |
| Staleness | Fewer than 20% of the last 50 bars carrying a change → stale | Sound: matches the tooltip, and a gap is not a change |
| BUILD σ | Log change over the RMS of the last 50 accepted changes, measured before this bar joins; zero-centred | Sound, apart from the empty baseline (O1, fixed) |
| Structural | > 50% of the book, or > 3σ and > 20% | Sound: matches the tooltip. Structural bars stay out of the baseline and out of ρ |
| Character | The word always agrees with the sign of ΔOI | Sound. Flat price is fixed (O2) |
| Trust | ρ(\|ΔOI\|, activity) ≥ 0.20, or the row dims | Sound. The signed-correlation argument in the tooltip is right |
| Crowded | GOLD from the 80th percentile | Sound: the code says ≥ 80 |

### AUCTION

| Cell | Claim | Verdict |
|---|---|---|
| STATE | Migrating, Shifting or Balance against the window N bars earlier | Sound: matches spec v2 §4.1 exactly |
| WHY | The side, probe or accepted, and the close against value | Fixed (A1, G1) |
| CHART | Accepted momentum's position, or the trail's level | Sound. The position is the trail's committed side times live S: provisional on the forming bar, final at the close. The tooltip now says so |
| SPAN | Since the trail started or flipped | Fixed (S1). The tooltip now says the Accepted momentum position can be younger than the side |

## 3 · Open: known, unfixed, stated

| ID | Issue | Why it is not fixed here |
|---|---|---|
| X1 | **Expiry contamination, unmeasured.** On a continuous front-month future, the book falls into each expiry as positions roll. A daily fall below the structural cut (under 20% of the book, or under 3σ) reads as covering or unwinding, and the 250-bar book percentile partly tracks the expiry calendar | No OI data is reachable from this session to measure it. An expiry-window guard (`syminfo.expiration_date` on the current contract) cannot be compile-tested here. The tooltip now states the caution |
| X2 | "Daily only" is detected on the first companion symbol only. If only the second or third form carries daily OI, the state reads "No OI" | Fixing it costs two requests of the three left (37 of 40 used), for a label |
| X3 | Tooltip figures from the v9 audit are **external** and were not re-verified: Buy · capitulation +0.06 to +0.08σ; short covering lagged on 187 NSE F&O stocks; the graded units positive in all three eras | The Sanket repository is not reachable here |
| X4 | **Not compiled.** Every check here runs on a Python port or the parser. The new Pine is boolean and string logic of the kinds the script already uses | Needs TradingView |
