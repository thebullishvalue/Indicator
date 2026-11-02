# Pragati v9.9 · Audit of the volume profile and the information panel

**The question.** As `docs/audit-readout-v9.8.md` asked of the readout: does
every element draw or say what its code computes, with every edge case covered
and every tooltip true?

**Method.**
1. Every element was traced from its source series to what it draws or says.
2. Every claim was compared with the code.
3. Each suspicion was made a test, run on ports of the code and, where the data
   allowed, on the 119 daily markets of the trail lab.
4. A fix was adopted only where a defect was demonstrated.

The scripts are in `research/audit/`: `naked_poc.py` and `vp_props.py`. They
are not a compile.

**Out of scope.** The comments label the naked-POC ledger and VWAP/IB
"(measured)". Those are claims carried over from PVOI v2.1 and were not
re-verified here.

---

## 1 · Defect register

| ID | Element | Severity | Defect | Evidence | Fix (v9.9) | Re-test |
|---|---|---|---|---|---|---|
| **V2** | Naked POCs | **High**: a quarter of the drawn levels were false | The touch check ran **before** a new session's POC joined the ledger. The first bar of each session therefore could never trade through the POC it inherited, and the level stayed "naked" until a later bar touched it, or forever | `naked_poc.py`, with the profile and ledger ported, on 119 markets with the default weekly session on daily bars. **39.0%** of 136,276 weekly POCs are traded through on the next session's first bar. On the last bar, v9.8 drew 367 naked POCs and **98 (27%) had already been traded through** | The POC is added first, then the bar's touch check runs | Independent check: **0 of 320** drawn naked POCs had been traded through |
| **G1** | Profile, VWAP, IB | **High**: drawn from synthetic prices | v9.6 paused every pane family on non-standard charts, and v9.8 extended that to the readout. The profile was missed: on Heikin Ashi, Renko and the rest it built a POC and value area from bars that never traded | Code: `vpChartOn` had no chart-type test | `vpChartOn` needs `stdChart`, so the whole overlay and the panel's PROFILE rows stand down | By construction |
| **V3** | Profile build | **Medium** at non-default settings | A bar whose range covered more than 200 bins was spread over its **lowest** 200 only, so the top of the bar received nothing and the POC and value area were biased low. At the default 4 bins per ATR this needs a 50-ATR bar, but in **Fixed-ticks** mode with small ticks it is routine | Code: `nb = min(kh − kl + 1, 200)` and `for k = kl to kl + nb − 1` | The whole range is spread on every st-th bin, with st = ⌈nb / 200⌉: still at most 200 writes, and volume conserved | `vp_props.py`: at most 200 bins, volume conserved, the full range covered, identical whenever the bar fits — all pass |
| **V4** | Histogram rows | Low: a visual distortion | Above 110 bins, rows were groups of consecutive **array positions**, not of price. A session with a price gap (a weekend gap in a weekly session, or a limit move) made a row bridge the gap, drawing volume across prices that never traded and making that row taller than the rest | Code: `rr = i / step`, with the row's bounds taken from its first and last key | Rows are `step` bins of **price** from the lowest key, so a gap stays an empty row. Two arrays fewer | `vp_props.py`: at most 110 rows, volume conserved, no volume in a row with no traded bin, identical for gap-free sessions — all pass |
| **V5** | Initial Balance | Low: a misleading label | The IB span is counted in bars (default 12). On daily bars with weekly sessions, 12 bars cover the whole week, so IBH / IBL were just the session's high and low under another name | Code: `bar_index − vpSessStart < inpVpIbBars` | The IB is drawn on intraday charts only, and its tooltip says why | By construction |
| **V6** | Session anchor | Low | Above weekly, the anchor was "M": on a monthly chart every bar was its own one-bar session | Code | 12 months on monthly bars and above | By construction |
| **V7** | Session line | Low: a misleading label | With volume off (TPO), the session line is time-weighted but was tagged VWAP | Code: `wV = 1` when volume is off | The tag reads TWAP when volume is off | By construction |
| **P1** | Panel · declaration | **Medium**: says the wrong thing | With the ▲▼ switched off, the row read "none yet", as though they were on and had not fired | Code: no branch for `inpState` | Reads "off", in neutral | By construction |
| **P2** | Panel · Profile Mode | Low: breaks the colour grammar | Painted **green** when the profile delivered volume and intrabar data. Green is a direction in this script (buyers, rich), not "data OK" | Code: `C_BULL` | Neutral when delivered; gold when degraded | Visual |
| **P3** | Panel · Profile Mode | Low: claims more than it shows | The tooltip says "what the profile ACTUALLY did", but the right half reported only whether the **last bar** used intrabars. Intrabar history is plan-limited, so earlier bars of the session can be bar-spread | Code: `vpIntraOk` is the last bar's flag | Counts this session's bars and how many intrabars built. Shows the resolution, with its share when it is not every bar | By construction |

**Cost.** At the fitted ratio (`docs/audit-readout-v9.8.md`), v9.9 is estimated at
≈ 94,260 compiled tokens, against the 100,256 ceiling. No plot, request or
drawing count changed; the boxes are at most what v9.8 drew.

## 2 · Checked and sound

### Volume profile

| Element | Claim | Verdict |
|---|---|---|
| Bins | Width frozen at session start: ATR(20)/bins-per-ATR, or fixed ticks; floored at the tick | Sound. ATR is evaluated every bar, outside the session branch |
| POC | "O(1)": the first bin to reach the running maximum | Sound and exact: bins only grow within a session, so a running maximum is the maximum. Ties go to the first bin to reach the level |
| Value area | 70% walked out from the POC, the larger neighbour first | Sound. The walk is guarded; VAH and VAL are the outer bins' edges |
| Volume test | Volume is used when at least half of the last 500 bars print it (lifetime until 500 exist); otherwise TPO automatically | Sound. The panel reports what happened (TPO · auto), not what was asked |
| Intrabar build | `request.security_lower_tf`; TPO splits each chart bar across its intrabars; seconds charts stand down | Sound. History depth is plan-dependent and now reported (P3) |
| Inferred delta | Close-location share per bar; the tick rule per intrabar | Sound as labelled: an inference, display-only, drawn only in the split style |
| Width | Normalised by the widest drawn row, not the POC bin | Sound: aggregated rows cannot overshoot |
| HVN / LVN | A local peak ≥ mean + 1.2σ of the non-empty rows; a local trough ≤ the 10th percentile | Sound as a heuristic. The thresholds are unmeasured |
| Drawing limits | ≤ 470 profile boxes plus one value-area box, inside `max_boxes_count = 500`; every x ≥ `bar_index − 5000` | Sound |
| Developing trails | Blank on the session's first bar, so the previous session never connects to this one | Sound |
| Realtime | The profile's `var` arrays are updated on every realtime update | Relies on Pine rolling back `var` state, collections included, between realtime updates, which is how the script treats all its `var` arrays. Not testable here |

### Information panel

| Row | Claim | Verdict |
|---|---|---|
| Header | The zone or stretch words follow the trace's own rails; WARMING UP before `ready` | Sound |
| declaration | The last ▲ or ▼ and its age; paused with the reason | Sound; the off case is fixed (P1) |
| value · chart | Samanvaya's value against θ; gold while the basket settles | Sound |
| MTF tapes | The ladder readings, ↺ on fallback, — when off or warming | Sound. A reading of exactly 0 prints "cheap 0", which is cosmetic |
| impulse | The histogram against k·σ, in native units; the ▲▼ do not read it | Sound. It also agrees with the corrected k tooltip (v9.8 K1) |
| participation | The last **closed** bar's weight and the branch that set it | Sound: the forming bar is excluded, as stated |
| effort → result | Σ\|c\|·w / Σw, its percentile, ABSORBED in the bottom fifth | Sound |
| driver timing, rungs, rebuild error, layer overlap | As stated | Sound |
| Location | Above, below or in value, or at the POC (within one bin); gold off value | Sound |
| Table | Built once and written into; the row count follows the inputs | Sound. With G1 the PROFILE rows drop out on non-standard charts, and the row count follows `vpChartOn` |

## 3 · Open: known, unfixed, stated

| ID | Issue | Why it is not fixed here |
|---|---|---|
| Y1 | The Initial Balance is a span of **bars**, so its length in time changes with the chart's timeframe. Twelve 5-minute bars are an hour; twelve 1-hour bars cover a whole equity session | A time-based IB means a new input meaning; left for a design decision |
| Y2 | The naked-POC and VWAP/IB "(measured)" labels are PVOI's | Not re-verified; PVOI's evidence is not in this repository |
| Y3 | **Not compiled.** Every check here runs on a port or the parser | Needs TradingView |
