# v2.7 volume profile: checks

| Check | Result |
|---|---|
| `vp_v6_division.py`: the row search as written before v2.7, `int mid = (lo + hi) / 2`, under Pine v6 division (fractional) with array indices truncated | Keys out of order or duplicated in 1,983 of 2,000 simulated sessions; a key that is present not found in 1,994. That is the stale POC / VAH / VAL: when the POC's row cannot be found, the walk keeps the last levels it had |
| `vp_equivalence.py`: the v2.6 accumulation and per-bar value-area walk (with a correct search) against v2.7's (one search per span, a neighbour hint, the walk only where it is read); random sessions, intrabars, gaps and volumes; every bar in turn as the last bar, trails off and on | Identical on all 33,724 last-bar states |
| Same port, timed on the last 5,000 real bars of five symbols | 28% less work with 12 intrabars a bar, 47% less on plain daily bars, before the window below |
| `vp_recent_gate.py`: building the profile only over its window (two naked-POC ages and three sessions) against building it from the first bar, comparing the naked-POC list at many end points (run from `research/`) | Hourly: identical at all 27,948 end points. Daily: 14 of 23,304 differ, all on two Indian stocks, where one naked POC's line starts a week apart because a chain of duplicate checks reached past the window. In v2.7 the window is the definition: a naked POC is judged against the naked POCs of its window |

## Against main (v2.6): what is identical and what is not

Every engine line - risk forecast, trend, cone, stops, ledger, exposure, proof, pane, tapes, table, alerts - is
v2.6's, apart from two that cannot change a value: the cone's starting widths are worked out once on the first
bar (they depend on inputs only), and the words for labels and the table are built on the last bar only (the
only bar that draws them). `pramana.pine` is `pragyam.pine` renamed; nothing else differs.

| Change | Effect on output |
|---|---|
| Profile search fixed | Intended: v2.6's profile was wrong (stale POC / VAH / VAL) |
| Profile speed-ups | None (`vp_equivalence.py`) |
| Profile built over its window | Where an old naked POC's line starts, rarely (`vp_recent_gate.py`) |
| Intrabars about sixteen per bar; rows at least one bar wide | Intended display changes |
| Forward cone off by default | Default only |
| `calc_bars_count = 5000` | None on charts of 5,000 bars or fewer. On longer charts the learned parts differ (`engine_cap5000.py`, run from `research/`; 122 daily instruments with more than 6,000 bars, full history against the last 5,000, compared at the last bar): risk forecast, trend and risk regime identical; cone and stop widths median 1.5% apart (90th percentile 3.5-4%, worst 15%); exposure median 0.02 apart (90th percentile 0.07, worst 0.18). Kept: it is what lets daily charts with decades of history run inside the time limit, and it is how every intraday chart already runs under the plan's bar limit |

The version before all of this - v2.6, calculating on the full history - is kept on the branch `pragyam-full-history`.
