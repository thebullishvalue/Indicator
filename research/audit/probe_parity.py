"""Does the readout's PROBE agree with the engine's? (docs/audit-readout-v9.8.md, A1)

The reference trail (reference/auction_trail.py, spec v2) is run on every market
in a data folder at 20 and 126 bars. The readout's test is applied to each
closed bar, v9.7's and v9.8's, and counted against the engine's own probe flag.

    python -I research/audit/probe_parity.py DATA_DIR CACHE_DIR
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from trail_lab import Base  # noqa: E402


def v97(c, d, lvl, poc, mig):
    return poc is not None and ((c < lvl and poc >= lvl) if d > 0 else (c > lvl and poc <= lvl))


def v98(c, d, lvl, poc, mig):
    out = poc is not None and mig is not None and (c < lvl if d > 0 else c > lvl)
    acc = out and ((poc < lvl and mig <= -1) if d > 0 else (poc > lvl and mig >= 1))
    return out and not acc, acc


def main(data, cache):
    for n in (20, 126):
        eng = old = miss_old = new = miss_new = extra_new = acc_closed = 0
        for f in sorted(os.listdir(data)):
            b = Base(os.path.join(data, f), cache)
            if len(b.d["close"]) < 600:
                continue
            tr = b.tr20 if n == 20 else b.trail(126)
            for t, c in enumerate(b.d["close"]):
                d, lvl, poc, mig = tr["dir"][t], tr["lvl"][t], tr["poc"][t], tr["mig"][t]
                if not d or lvl is None:
                    continue
                e = tr["probe"][t]
                o = v97(c, d, lvl, poc, mig)
                p, a = v98(c, d, lvl, poc, mig)
                eng += e
                old += o
                miss_old += e and not o
                new += p
                miss_new += e and not p
                extra_new += p and not e
                acc_closed += a
        print(f"{n:>3} bars | engine probes {eng} | v9.7 readout {old}, missed {miss_old} ({miss_old / max(eng, 1):.1%}) | "
              f"v9.8 readout {new}, missed {miss_new}, extra {extra_new} | 'accepted' on a closed bar {acc_closed}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
