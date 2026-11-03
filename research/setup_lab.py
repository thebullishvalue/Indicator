"""Setup lab: docs/setup-lab.md, run exactly as written, once.

    python3 research/setup_lab.py --dev DATA/csv --ha HA/csv --cache CACHE --out research/results/setup-lab

DEV and HB are the 119 markets of research/results/2026-11-02/universe.csv (DEV
dates <= 2019-12-31, HB 2020-01-01 .. 2026-10-31); HA the 411 markets of
research/results/lab/ha-universe.csv, full history. It refuses to run if the
results file already exists: the protocol allows one run.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "reference"))
from auction_trail import _atr_wilder  # noqa: E402
from push_gate import push_gate  # noqa: E402
from trail_lab import Base, cached, mom  # noqa: E402
from tradability import COST_BPS, strategy_returns, weights  # noqa: E402

SETS = {"DEV": ("0000-00-00", "2019-12-31"), "HB": ("2020-01-01", "2026-10-31"), "HA": ("0000-00-00", "9999-99-99")}
HS = (10, 20)


def universe(path):
    return [(r["symbol"], r["class"]) for r in csv.DictReader(open(path))]


def series(path, cache):
    """Everything one market needs, from the cached engine runs."""
    b = Base(path, cache)
    d = b.d
    if len(d["close"]) < 600:
        return None
    h, l, c = d["high"], d["low"], d["close"]
    v = [x if x is not None else 0.0 for x in d["volume"]]
    gate = cached(cache, path, "gate", lambda: push_gate(h, l, c, v))
    vol = b.vol
    return {"d": d, "vol": vol, "stale": stale_flags(vol), "S": mom(c, vol), "t126": b.trail(126), "t20": b.tr20, "gate": gate, "w": b.w,
            "atr": _atr_wilder(h, l, c, 20)}


MODE = "run1"          # run1 as first run; "a1" amendment 1 (stale bars dropped); "a1b" (z clipped to +-5)


def stale_flags(vol, window=1000, frac=0.25, need=250):
    """Amendment 1: sigma_t below a quarter of the median of its own last 1,000 values (>= 250 needed); no look-ahead."""
    import bisect
    win, out, hist = [], [], []
    for v in vol:
        if v is None:
            out.append(False)
            continue
        hist.append(v)
        bisect.insort(win, v)
        if len(hist) > window:
            old = hist.pop(0)
            del win[bisect.bisect_left(win, old)]
        med = win[len(win) // 2] if len(win) % 2 else (win[len(win) // 2 - 1] + win[len(win) // 2]) / 2
        out.append(len(win) >= need and v < frac * med)
    return out


def z(x, t, s, h):
    """The event's outcome: entered at open t+1, held h bars, in sigma units, in direction s."""
    o, vol = x["d"]["open"], x["vol"]
    if t + 1 + h >= len(o) or vol[t] is None or vol[t] <= 0:
        return None
    if MODE == "a1" and x["stale"][t]:
        return None
    v = s * math.log(o[t + 1 + h] / o[t + 1]) / (vol[t] * math.sqrt(h))
    return max(-5.0, min(5.0, v)) if MODE == "a1b" else v


def in_set(x, t, h, a, b):
    dates = x["d"]["date"]
    return t + 1 + h < len(dates) and a <= dates[t] and dates[t + 1 + h] <= b


def market(job):
    path, cache, sets, mode = job
    global MODE
    MODE = mode
    x = series(path, cache)
    if x is None:
        return None
    c, S, gate, w, atr = x["d"]["close"], x["S"], x["gate"], x["w"], x["atr"]
    n = len(c)
    out = {}
    for sname in sets:
        a, b = SETS[sname]
        res = {}
        for N, tr in (("126", x["t126"]), ("20", x["t20"])):
            D, T, M, val, vah = tr["dir"], tr["lvl"], tr["mig"], tr["val"], tr["vah"]
            probe, onset, flip = tr["probe"], tr["onset"], tr["flip"]
            r = {}
            for h in HS:
                # baselines: every bar on a side, and every bar where AM agrees, by direction
                base, agree = {1: [], -1: []}, {1: [], -1: []}
                for t in range(n):
                    if D[t] in (1, -1) and in_set(x, t, h, a, b):
                        zz = z(x, t, D[t], h)
                        if zz is None:
                            continue
                        base[D[t]].append(zz)
                        if S[t] is not None and D[t] * S[t] > 0:
                            agree[D[t]].append(zz)
                B = {k: (statistics.fmean(v) if v else None) for k, v in base.items()}
                A = {k: (statistics.fmean(v) if v else None) for k, v in agree.items()}
                ev = {"F1": [], "S1": [], "S2": [], "S3": [], "S4": []}
                for t in range(1, n):
                    if not in_set(x, t, h, a, b) or D[t] not in (1, -1):
                        continue
                    d_ = D[t]
                    ag = S[t] is not None and d_ * S[t] > 0
                    if onset[t]:
                        ev["F1"].append((t, d_, "B"))
                    if probe[t - 1] and not probe[t] and not flip[t] and D[t - 1] == d_:
                        ev["S1"].append((t, d_, "B"))
                    if flip[t]:
                        ev["S2"].append((t, d_, "B"))
                    if ag and None not in (val[t], vah[t], val[t - 1], vah[t - 1]):
                        inside = val[t] <= c[t] <= vah[t]
                        beyond_prev = c[t - 1] > vah[t - 1] if d_ > 0 else c[t - 1] < val[t - 1]
                        beyond = c[t] > vah[t] if d_ > 0 else c[t] < val[t]
                        inside_prev = val[t - 1] <= c[t - 1] <= vah[t - 1]
                        if inside and beyond_prev:
                            ev["S3"].append((t, d_, "A"))
                        if beyond and inside_prev:
                            ev["S4"].append((t, d_, "A"))
                for k, lst in ev.items():
                    ex, raw = [], []
                    for t, s, bk in lst:
                        zz = z(x, t, s, h)
                        ref = (B if bk == "B" else A)[s]
                        if zz is None or ref is None:
                            continue
                        ex.append(zz - ref)
                        raw.append(zz)
                    r[f"{k}@{h}"] = {"n": len(ex), "excess": statistics.fmean(ex) if len(ex) >= 3 else None,
                                     "raw": statistics.fmean(raw) if raw else None, "hit": sum(1 for q in raw if q > 0) / len(raw) if raw else None}
            # S5: migrating with the trail against balance, AM-agree bars, h = 20
            g2, g0 = [], []
            for t in range(n):
                if D[t] in (1, -1) and M[t] is not None and S[t] is not None and D[t] * S[t] > 0 and in_set(x, t, 20, a, b):
                    zz = z(x, t, D[t], 20)
                    if zz is None:
                        continue
                    if M[t] * D[t] == 2:
                        g2.append(zz)
                    elif M[t] == 0:
                        g0.append(zz)
            r["S5"] = {"n2": len(g2), "n0": len(g0), "diff": statistics.fmean(g2) - statistics.fmean(g0) if len(g2) >= 3 and len(g0) >= 3 else None}
            # F1 descriptive and F2 features, on onsets
            ons = []
            for t in range(1, n):
                if not onset[t] or D[t] not in (1, -1) or not in_set(x, t, 20, a, b):
                    continue
                d_ = D[t]
                f10 = any(flip[k] for k in range(t + 1, t + 11))
                f20 = any(flip[k] for k in range(t + 1, t + 21))
                back5 = False
                for k in range(t + 1, t + 6):
                    if flip[k]:
                        break
                    if not probe[k] and D[k] == d_:
                        back5 = True
                        break
                ln = 1
                while t + ln < n and probe[t + ln] and D[t + ln] == d_:
                    ln += 1
                feats = (gate[t] is not None and gate[t] == -d_,
                         M[t] is not None and -d_ * M[t] >= 1,
                         atr[t] is not None and T[t] is not None and abs(c[t] - T[t]) >= 0.5 * atr[t],
                         w[t] is not None and w[t] >= 1.5)
                ons.append((f10, f20, back5, ln, feats))
            r["onsets"] = ons
            res[N] = r
        # I1: the investor's filter on the 126-bar trail, non-crypto only
        res["I1"] = None
        out[sname] = res
    return os.path.basename(path)[:-4], out


def investor(job):
    """I1 for one market: daily net returns of the filter and of buy-and-hold, from the first live bar."""
    path, cache, cls = job
    x = series(path, cache)
    if x is None or cls == "crypto":
        return None
    D, S = x["t126"]["dir"], x["S"]
    pos = [None if (S[t] is None or D[t] == 0) else D[t] * max(0.0, D[t] * S[t]) for t in range(len(S))]
    t0 = next((t for t, p in enumerate(pos) if p is not None), None)
    if t0 is None:
        return None
    sig = [None if t < t0 else (1.0 if (pos[t] or 0) > 0 else 0.0) for t in range(len(pos))]
    wf = weights("AM", sig, x["vol"], "invest")
    wb = [0.0 if t < t0 else 1.0 for t in range(len(pos))]
    cost = COST_BPS.get(cls, 10)
    start = x["d"]["date"][t0 + 1] if t0 + 1 < len(x["d"]["date"]) else "9999"
    rf = {k: v for k, v in strategy_returns(x["d"], wf, cost).items() if k >= start}
    rb = {k: v for k, v in strategy_returns(x["d"], wb, cost).items() if k >= start}
    inv = {x["d"]["date"][t + 1]: wf[t] for t in range(t0, len(wf) - 2)}
    return os.path.basename(path)[:-4], cls, rf, rb, inv


def tstat(vals):
    v = [q for q in vals if q is not None]
    if len(v) < 3:
        return {"n": len(v), "mean": None, "t": None}
    m, sd = statistics.fmean(v), statistics.stdev(v)
    return {"n": len(v), "mean": m, "t": m / (sd / math.sqrt(len(v))) if sd > 0 else None}


def pmetrics(ser, a, b):
    days = sorted(d for d in ser if a <= d <= b)
    x = [ser[d] for d in days]
    if len(x) < 250:
        return None
    eq, peak, mdd, ls = 1.0, 1.0, 0.0, 0.0
    for r in x:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
        ls += math.log(max(1 + r, 1e-9))
    sd = statistics.pstdev(x)
    return {"cagr": math.exp(ls * 252 / len(x)) - 1, "vol": sd * math.sqrt(252), "sharpe": statistics.fmean(x) / sd * math.sqrt(252) if sd else None,
            "mdd": mdd, "days": len(x), "from": days[0], "to": days[-1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", required=True)
    ap.add_argument("--ha", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", default="run1", choices=["run1", "a1", "a1b"])
    a = ap.parse_args()
    global MODE
    MODE = a.mode
    res_path = os.path.join(a.out, "results.json" if MODE == "run1" else f"results-{MODE}.json")
    if os.path.exists(res_path):
        sys.exit("results.json exists: the protocol allows one run")
    os.makedirs(a.out, exist_ok=True)
    dev = universe(os.path.join(HERE, "results", "2026-11-02", "universe.csv"))
    ha = universe(os.path.join(HERE, "results", "lab", "ha-universe.csv"))
    jobs = [(os.path.join(a.dev, s + ".csv"), a.cache, ("DEV", "HB"), MODE) for s, _ in dev] + [(os.path.join(a.ha, s + ".csv"), a.cache, ("HA",), MODE) for s, _ in ha]
    with Pool(4) as p:
        per = [r for r in p.map(market, jobs, chunksize=4) if r is not None]
        inv = p.map(investor, [(os.path.join(a.dev, s + ".csv"), a.cache, c) for s, c in dev] + [(os.path.join(a.ha, s + ".csv"), a.cache, c) for s, c in ha], chunksize=4)
    devset = {s for s, _ in dev}
    summary = {}
    for sname in ("DEV", "HB", "HA"):
        rows = [o[sname] for name, o in per if sname in o]
        S_ = {"markets": len(rows)}
        for N in ("126", "20"):
            R = [r[N] for r in rows]
            blk = {}
            for k in ("F1", "S1", "S2", "S3", "S4"):
                for h in HS:
                    key = f"{k}@{h}"
                    st = tstat([r[key]["excess"] for r in R])
                    st["events"] = sum(r[key]["n"] for r in R)
                    raws = [r[key]["raw"] for r in R if r[key]["raw"] is not None and r[key]["n"] >= 3]
                    st["raw_mean"] = statistics.fmean(raws) if raws else None
                    hits = [(r[key]["hit"], r[key]["n"]) for r in R if r[key]["hit"] is not None]
                    st["hit"] = sum(hh * nn for hh, nn in hits) / max(1, sum(nn for _, nn in hits))
                    blk[key] = st
            # S3 - S4, per market, both horizons
            for h in HS:
                blk[f"S3-S4@{h}"] = tstat([(r[f"S3@{h}"]["excess"] - r[f"S4@{h}"]["excess"]) if (r[f"S3@{h}"]["excess"] is not None and r[f"S4@{h}"]["excess"] is not None) else None for r in R])
            blk["S5"] = tstat([r["S5"]["diff"] for r in R])
            ons = [o for r in R for o in r["onsets"]]
            blk["F1desc"] = {"onsets": len(ons), "flip10": sum(o[0] for o in ons) / max(1, len(ons)), "flip20": sum(o[1] for o in ons) / max(1, len(ons)),
                             "back5": sum(o[2] for o in ons) / max(1, len(ons)), "median_len": statistics.median([o[3] for o in ons]) if ons else None}
            f2 = {}
            for j, lab in enumerate("abcd"):
                diffs = []
                for r in R:
                    g1 = [o[1] for o in r["onsets"] if o[4][j]]
                    g0 = [o[1] for o in r["onsets"] if not o[4][j]]
                    diffs.append(sum(g1) / len(g1) - sum(g0) / len(g0) if len(g1) >= 3 and len(g0) >= 3 else None)
                st = tstat(diffs)
                g1 = [o[1] for o in ons if o[4][j]]
                g0 = [o[1] for o in ons if not o[4][j]]
                st.update({"rate1": sum(g1) / max(1, len(g1)), "rate0": sum(g0) / max(1, len(g0)), "n1": len(g1), "n0": len(g0)})
                f2[f"F2{lab}"] = st
            f2["by_count"] = {str(kk): {"n": len(g), "flip20": sum(g) / len(g) if g else None}
                              for kk in range(5) for g in [[o[1] for o in ons if sum(o[4]) == kk]]}
            blk["F2"] = f2
            S_[N] = blk
        summary[sname] = S_
    # I1 portfolios
    inv = [q for q in inv if q is not None]
    i1 = {}
    for sname in ("DEV", "HB", "HA"):
        a_, b_ = SETS[sname]
        pick = [q for q in inv if (q[0] in devset) == (sname != "HA")]
        if sname == "HA":
            pick = [q for q in pick if q[1] == "nse_stock"]
        pf, pb = {}, {}
        days = sorted({d for q in pick for d in q[2]})
        for dd in days:
            vf = [q[2][dd] for q in pick if dd in q[2]]
            vb = [q[3][dd] for q in pick if dd in q[3]]
            if vf:
                pf[dd] = sum(vf) / len(vf)
            if vb:
                pb[dd] = sum(vb) / len(vb)
        invested = [w for q in pick for dd, w in q[4].items() if a_ <= dd <= b_]
        i1[sname] = {"markets": len(pick), "filter": pmetrics(pf, a_, b_), "buyhold": pmetrics(pb, a_, b_),
                     "time_invested": statistics.fmean(invested) if invested else None}
    summary["I1"] = i1
    json.dump(summary, open(res_path, "w"), indent=1)
    print(json.dumps(summary, indent=1)[:200])


if __name__ == "__main__":
    main()
