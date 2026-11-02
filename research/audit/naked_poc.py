"""Naked POC ledger: v9.8 order (touch check before the new POC is added) against v9.9
(added first), on daily bars with the script's weekly session (docs/audit-vp-panel-v9.9.md, V2).

The session profile is ported from f_vpBuild's fallback path: each bar's volume spread
evenly over the bins its range covers, the bin frozen at session start at ATR(20)/4,
the POC the first bin to reach the running maximum.

    python -I research/audit/naked_poc.py DATA_DIR
"""
import csv
import datetime as dt
import math
import os
import sys


def atr_wilder(h, l, c, n=20):
    out, a = [], None
    for i in range(len(c)):
        tr = h[i] - l[i] if i == 0 else max(h[i], c[i - 1]) - min(l[i], c[i - 1])
        a = tr if a is None and i == n - 1 else a
        if i < n - 1:
            out.append(None)
            continue
        if i >= n:
            a = (a * (n - 1) + tr) / n
        out.append(a)
    return out


def run(rows, fixed, max_kept=5, max_age=250):
    d = [r[0] for r in rows]
    h = [r[2] for r in rows]
    l = [r[3] for r in rows]
    c = [r[4] for r in rows]
    v = [r[5] or 0.0 for r in rows]
    atr = atr_wilder(h, l, c)
    wk = [dt.date.fromisoformat(x).isocalendar()[:2] for x in d]
    bins, pk, pv, poc, prev = {}, None, 0.0, None, None
    bw = None
    naked = []          # [price, added_at]
    events = []         # (added_at, touched_on_first_bar, removed_at or None)
    first_touch = 0
    for t in range(len(c)):
        new = t == 0 or wk[t] != wk[t - 1]
        if new:
            prev = poc
            bins, pk, pv = {}, None, 0.0
            bw = max((atr[t] or (h[t] - l[t]) or 1e-9) / 4.0, 1e-9)
        # this bar's volume into the session profile
        kl, kh = math.floor(l[t] / bw), math.floor(h[t] / bw)
        nb = max(1, min(kh - kl + 1, 200))
        for k in range(kl, kl + nb):
            bins[k] = bins.get(k, 0.0) + (v[t] or 1.0) / nb
            if bins[k] > pv:
                pv, pk = bins[k], k
        poc = (pk + 0.5) * bw if pk is not None else None

        def add():
            if new and prev is not None and not any(abs(y - prev) <= (atr[t] or 0) * 0.1 for y, _ in naked):
                naked.append([prev, t])
                del naked[:-max_kept]

        def touch():
            nonlocal first_touch
            for item in list(naked):
                if h[t] >= item[0] >= l[t]:
                    naked.remove(item)
                    if item[1] == t:
                        first_touch += 1
        if fixed:
            add()
            touch()
        else:
            touch()
            add()
        naked[:] = [x for x in naked if t - x[1] <= max_age]
    return first_touch, naked


def main(data):
    tot_new = tot_first = 0
    false_now = shown_now = 0
    viol = {False: 0, True: 0}
    drawn = {False: 0, True: 0}
    for f in sorted(os.listdir(data)):
        rows = []
        for r in csv.DictReader(open(os.path.join(data, f))):
            rows.append((r["date"], float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]),
                         float(r["volume"]) if r["volume"] else None))
        if len(rows) < 600:
            continue
        ft, naked_fixed = run(rows, True)
        _, naked_old = run(rows, False)
        tot_first += ft
        # weekly sessions in the history = POCs offered to the ledger
        tot_new += len({dt.date.fromisoformat(r[0]).isocalendar()[:2] for r in rows}) - 1
        # independent check: a drawn naked POC must not have been traded through
        # on any bar since its session ended (the bar it was added included)
        for ver, nk in ((False, naked_old), (True, naked_fixed)):
            for y, t0 in nk:
                drawn[ver] += 1
                viol[ver] += any(rows[t][2] >= y >= rows[t][3] for t in range(t0, len(rows)))
        old = {round(y, 9) for y, _ in naked_old}
        new = {round(y, 9) for y, _ in naked_fixed}
        false_now += len(old - new)
        shown_now += len(old)
    print(f"weekly POCs offered: {tot_new}")
    print(f"touched on the very first bar of the next session: {tot_first} ({tot_first / tot_new:.1%}) - "
          f"v9.8 cannot see these touches")
    print(f"on the last bar: v9.8 draws {shown_now} naked POCs, of which {false_now} ({false_now / max(shown_now, 1):.1%}) "
          f"were already traded through")
    for ver, name in ((False, "v9.8"), (True, "v9.9")):
        print(f"independent check, {name}: {viol[ver]} of {drawn[ver]} drawn naked POCs had been traded through")


if __name__ == "__main__":
    main(sys.argv[1])
