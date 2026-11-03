"""Case studies for the field manual: docs/setup-lab.md section 5, exactly.

    python3 research/case_extract.py --data DATA/csv --cache CACHE --out docs/manual/src/cases

Six markets fixed in advance, one per class. For each, the display window is the
last 300 bars to the data's end (fixed before anything was plotted), and the
case events are the MOST RECENT of each type before 2026-09-30 whose 20-bar
outcome is complete, whatever the outcome:
  probe rejected   a probe onset with no flip within 20 bars
  probe accepted   a probe onset followed by a flip within 20 bars
  AM long cycle    the latest completed campaign of the TRADED weight > 0 (the tested engine:
                   weekly rebalance, 10% band, so a campaign is what an account would have held)
  AM short / flat  the latest completed campaign < 0, and the latest flat stretch
  pullback (S3)    the latest S3 event
Outcomes are reported as in the setup lab: z over 10 and 20 bars from the next
open, in the event's direction, in sigma units; AM cycles as the vol-targeted
return of the tested sizing (size x 10% / annualised vol, cap 2), net of the test's costs.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "reference"))
from trail_lab import Base, mom, weights_trade  # noqa: E402
from tradability import COST_BPS  # noqa: E402

MARKETS = [("NIFTY_50", "index"), ("RELIANCE", "nse_stock"), ("GOLD", "commodity"), ("USDINR", "fx"), ("BTCUSDT", "crypto"), ("BANKBEES", "etf")]
CUTOFF, WINDOW = "2026-09-30", 300


def zout(o, vol, t, s, h):
    if t + 1 + h >= len(o) or not vol[t]:
        return None
    return s * math.log(o[t + 1 + h] / o[t + 1]) / (vol[t] * math.sqrt(h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for sym, cls in MARKETS:
        b = Base(os.path.join(a.data, sym + ".csv"), a.cache)
        d, vol = b.d, b.vol
        tr = b.trail(126)
        S = mom(d["close"], vol)
        n = len(d["close"])
        D, val, vah = tr["dir"], tr["val"], tr["vah"]
        am = [None if (S[t] is None or D[t] == 0) else D[t] * max(0.0, D[t] * S[t]) for t in range(n)]
        o, c, dates = d["open"], d["close"], d["date"]
        last_ok = max(t for t in range(n) if dates[t] <= CUTOFF and t + 21 < n)

        def flip_within(t, h=20):
            return next((k for k in range(t + 1, t + h + 1) if tr["flip"][k]), None)
        ev = {}
        for t in range(last_ok, 0, -1):
            if tr["onset"][t] and "probe_rejected" not in ev and flip_within(t) is None:
                ev["probe_rejected"] = t
            if tr["onset"][t] and "probe_accepted" not in ev and flip_within(t) is not None:
                ev["probe_accepted"] = t
            if "pullback" not in ev and am[t] and am[t - 1] is not None and None not in (val[t], vah[t], val[t - 1], vah[t - 1]):
                dd = D[t]
                if val[t] <= c[t] <= vah[t] and (c[t - 1] > vah[t - 1] if dd > 0 else c[t - 1] < val[t - 1]):
                    ev["pullback"] = t
            if len(ev) == 3:
                break
        # AM campaigns: maximal runs of the TRADED weight's sign, completed before the cutoff
        wt = weights_trade(am, vol, False)
        cost = COST_BPS.get(cls, 10) / 1e4
        sg = [0 if abs(x) < 1e-12 else (1 if x > 0 else -1) for x in wt]
        runs, t = [], 0
        while t < n:
            k = t
            while k + 1 < n and sg[k + 1] == sg[t]:
                k += 1
            runs.append((t, k, sg[t]))
            t = k + 1
        done = [r for r in runs if dates[r[1]] <= CUTOFF and r[1] + 2 < n and vol[r[0]]]

        def cycle(r):
            t0, t1, s = r
            eq, peak, mdd = 1.0, 1.0, 0.0
            for t in range(t0, t1 + 1):
                prev = wt[t - 1] if t > 0 else 0.0
                rr = wt[t] * (o[t + 2] / o[t + 1] - 1.0) - cost * abs(wt[t] - prev)
                eq *= 1 + rr
                peak = max(peak, eq)
                mdd = min(mdd, eq / peak - 1)
            eq *= 1 - cost * abs(wt[t1 + 1] - wt[t1]) if s != 0 else 1
            return {"start": dates[t0], "end": dates[t1], "bars": t1 - t0 + 1, "side": s, "ret": eq - 1.0, "mdd": mdd,
                    "px_in": o[t0 + 1], "px_out": o[min(t1 + 2, n - 1)], "w_max": max(abs(wt[t]) for t in range(t0, t1 + 1)),
                    "move": (o[min(t1 + 2, n - 1)] / o[t0 + 1] - 1.0)}
        longs = [r for r in done if r[2] == 1]
        shorts = [r for r in done if r[2] == -1]
        flats = [r for r in done if r[2] == 0]
        events = []
        for kind, t in ev.items():
            s = D[t] if kind != "probe_accepted" else D[t]
            fk = flip_within(t) if kind.startswith("probe") else None
            events.append({"kind": kind, "date": dates[t], "i": t, "side": D[t], "close": c[t], "trail": tr["lvl"][t], "val": val[t], "vah": vah[t],
                           "poc": tr["poc"][t], "mig": tr["mig"][t], "S": S[t], "am": am[t],
                           "z10": zout(o, vol, t, s, 10), "z20": zout(o, vol, t, s, 20), "flip_date": dates[fk] if fk else None})
        cyc = {"long": cycle(longs[-1]) if longs else None, "short": cycle(shorts[-1]) if shorts else None, "flat": cycle(flats[-1]) if flats else None}
        allc = [cycle(r) for r in done if r[2] != 0]
        hist = {"cycles": len(allc), "wins": sum(1 for x in allc if x["ret"] > 0), "mean_ret": sum(x["ret"] for x in allc) / max(1, len(allc)),
                "median_bars": sorted(x["bars"] for x in allc)[len(allc) // 2] if allc else None,
                "flips": sum(1 for x in tr["flip"] if x), "onsets": sum(1 for x in tr["onset"] if x), "years": n / 252}
        w0 = n - WINDOW
        rnd = lambda x, p=6: None if x is None else round(x, p)
        win = {k: [rnd(x) if isinstance(x, float) else x for x in v[w0:]] for k, v in
               {"date": dates, "open": o, "high": d["high"], "low": d["low"], "close": c, "val": val, "poc": tr["poc"], "vah": vah, "dir": D,
                "lvl": tr["lvl"], "probe": tr["probe"], "onset": tr["onset"], "flip": tr["flip"], "mig": tr["mig"], "S": S, "am": am, "w": wt, "vol": vol}.items()}
        last = n - 1
        now = {"date": dates[last], "close": c[last], "dir": D[last], "lvl": tr["lvl"][last], "val": val[last], "poc": tr["poc"][last], "vah": vah[last],
               "mig": tr["mig"][last], "S": S[last], "am": am[last], "vol_ann": vol[last] * math.sqrt(252) if vol[last] else None,
               "target": None if (am[last] is None or not vol[last]) else max(-2.0, min(2.0, am[last] * 0.10 / (vol[last] * math.sqrt(252)))), "weight": wt[last]}
        json.dump({"symbol": sym, "class": cls, "window": win, "events": events, "cycles": cyc, "history": hist, "now": now},
                  open(os.path.join(a.out, sym + ".json"), "w"), separators=(",", ":"))
        print(sym, now["date"], "events", {e["kind"]: (e["date"], rnd(e["z10"], 2), rnd(e["z20"], 2)) for e in events},
              "| long", cyc["long"] and (cyc["long"]["start"], cyc["long"]["end"], round(cyc["long"]["ret"], 3)),
              "| short", cyc["short"] and (cyc["short"]["start"], cyc["short"]["end"], round(cyc["short"]["ret"], 3)),
              "| now", now["dir"], rnd(now["am"], 2), rnd(now["weight"], 2))


if __name__ == "__main__":
    main()
