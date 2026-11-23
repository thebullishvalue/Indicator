# v2.7 volume profile: checks

| Check | Result |
|---|---|
| `vp_v6_division.py`: the row search as written before v2.7, `int mid = (lo + hi) / 2`, under Pine v6 division (fractional) with array indices truncated | Keys out of order or duplicated in 1,983 of 2,000 simulated sessions; a key that is present not found in 1,994. That is the stale POC / VAH / VAL: when the POC's row cannot be found, the walk keeps the last levels it had |
| `vp_equivalence.py`: the v2.6 accumulation and per-bar value-area walk (with a correct search) against v2.7's (one search per span, a neighbour hint, the walk only where it is read); random sessions, intrabars, gaps and volumes; every bar in turn as the last bar, trails off and on | Identical on all 33,724 last-bar states |
| Same port, timed on the last 5,000 real bars of five symbols | 28% less work with 12 intrabars a bar, 47% less on plain daily bars, before the window below |
| `vp_recent_gate.py`: building the profile only over its window (two naked-POC ages and three sessions) against building it from the first bar, comparing the naked-POC list at many end points (run from `research/`) | Hourly: identical at all 27,948 end points. Daily: 14 of 23,304 differ, all on two Indian stocks, where one naked POC's line starts a week apart because a chain of duplicate checks reached past the window. In v2.7 the window is the definition: a naked POC is judged against the naked POCs of its window |
