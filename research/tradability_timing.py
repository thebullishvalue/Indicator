"""EXPLORATORY, not pre-registered: timing skill versus drift capture, per signal.

H4 found that the trail's state, centred on its trailing mean, does not predict
returns. Yet T-LS earns a positive Sharpe. This script asks where that comes
from. It runs the v9 scorer on each signal from the first bar on which all
signals are live:

    centred position × forward 20-bar log return / (σ √20)

It reports each signal's mean position next to its score. Continuous scores are
scaled to a unit mean |position|, so signals compare.

    python -I research/tradability_timing.py DATA_DIR classes.csv
"""
import csv
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tradability import load_csv, market_signals, nw_t  # noqa: E402

NAMES = ["T-LS", "AM", "TSMOM", "ST"]


def main(data, classes_csv):
    _ = {r["symbol"]: r["class"] for r in csv.DictReader(open(classes_csv))}
    sc = {s: [] for s in NAMES}
    meanpos = {s: [] for s in NAMES}
    for fn in sorted(os.listdir(data)):
        d = load_csv(os.path.join(data, fn))
        if len(d["close"]) < 600:
            continue
        sig, vol, tr = market_signals(d)
        c = d["close"]
        t0 = next((t for t in range(len(c)) if vol[t] and tr["dir"][t] != 0 and all(sig[s][t] is not None for s in NAMES)), None)
        if t0 is None:
            continue
        for s in NAMES:
            p = [sig[s][t] if sig[s][t] is not None else 0.0 for t in range(t0, len(c))]
            k = statistics.mean(abs(x) for x in p) or 1.0
            p = [x / k for x in p]
            meanpos[s].append(statistics.mean(p))
            x = []
            for i in range(250, len(p) - 20):
                t = t0 + i
                if vol[t] and vol[t] > 0:
                    x.append((p[i] - sum(p[i - 249:i + 1]) / 250) * math.log(c[t + 20] / c[t]) / (vol[t] * math.sqrt(20)))
            if len(x) > 60:
                sc[s].append((statistics.mean(x), nw_t(x, 20)))
    print("| Signal | Markets | Mean position (unit-scaled) | Timing score (centred, 20 bars) | Mean t | Share of markets t > 0 |")
    print("|---|---|---|---|---|---|")
    for s in NAMES:
        v = sc[s]
        print(f"| {s} | {len(v)} | {statistics.mean(meanpos[s]):+.2f} | {statistics.mean(a for a, _ in v):+.4f} | "
              f"{statistics.mean(b for _, b in v):+.2f} | {sum(b > 0 for _, b in v) / len(v):.0%} |")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
