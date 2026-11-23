# v2.6.1 speed-up: checks

`pragyam.pine` v2.6.1 cuts the volume profile's work without changing what it draws.

| Check | Result |
|---|---|
| `vp_equivalence.py`: old and new profile code ported line for line (per-row search and a value-area walk on every bar, against one search per span with a neighbour hint and the walk only where it is read); random sessions, intrabars, gaps and volumes; every bar taken in turn as the last bar, with trails off and on | Identical on all 33,724 last-bar states: rows, volumes, POC, value area, prior-session levels |
| Same port, timed on the last 5,000 real bars of five symbols | 28% less profile work with 12 intrabars a bar, 47% less on plain daily bars. A floor: Python's search is compiled, Pine's is not |
| `vp_recent_gate.py`: the opt-in *Recent sessions only*, replaying the naked-POC list from the first bar and from the gate at many end points (run from `research/`) | Hourly: identical at all 27,948 end points. Daily: different at 14 of 23,304 (0.06%), all on two Indian stocks, where a naked POC's line started one week apart. Not exact, so off by default |
