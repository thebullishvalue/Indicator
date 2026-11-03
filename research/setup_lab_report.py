"""Formats research/results/setup-lab/results-*.json as the tables in docs/setup-lab.md section 6."""
import json, sys
R = json.load(open(sys.argv[1]))
f = lambda v, p=3: "—" if v is None else (f"{v:+.{p}f}" if isinstance(v, float) else str(v))
for N in ("126", "20"):
    print(f"\n=== N = {N}")
    for k in ("F1@10", "F1@20", "S1@10", "S1@20", "S2@10", "S2@20", "S3@10", "S3@20", "S4@10", "S4@20", "S3-S4@10", "S3-S4@20", "S5"):
        print(f"{k:9}", " | ".join(f"{s}: {f(R[s][N][k]['mean'])} (t {f(R[s][N][k]['t'], 1)}, m {R[s][N][k]['n']}" + (f", ev {R[s][N][k].get('events')}, hit {R[s][N][k]['hit']:.2f})" if 'events' in R[s][N][k] else ")") for s in ("DEV", "HB", "HA")))
    for s in ("DEV", "HB", "HA"):
        print(s, "F1desc", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in R[s][N]["F1desc"].items()})
    for k in ("F2a", "F2b", "F2c", "F2d"):
        print(k, " | ".join(f"{s}: {f(R[s][N]['F2'][k]['mean'])} (t {f(R[s][N]['F2'][k]['t'], 1)}, m {R[s][N]['F2'][k]['n']}) {R[s][N]['F2'][k]['rate1']:.3f} vs {R[s][N]['F2'][k]['rate0']:.3f}" for s in ("DEV", "HB", "HA")))
    for s in ("DEV", "HB", "HA"):
        print(s, "count", {k: (v['n'], None if v['flip20'] is None else round(v['flip20'], 3)) for k, v in R[s][N]["F2"]["by_count"].items()})
