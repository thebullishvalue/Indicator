"""Trail lab harness: docs/trail-lab.md, run exactly.

Machinery is research/tradability.py's, imported, not copied, wherever it can be:
- the data loader
- EWMA volatility
- the momentum score
- execution (strategy_returns)
- the portfolio
- the metrics and the deflated Sharpe

Subcommands:
    prior  --data D --classes C --cache K
        The eight earlier candidates on DEV; a reference, not budget.
    dev    --data D --classes C --cache K --round R --variants A,B
        Scores the named variants on DEV and logs every one. A logged name
        cannot be rerun; a changed variant needs a new name.
    final  --data D --classes C --ha-data D2 --ha-classes C2 --cache K
        Runs the frozen winner once on HA and HB. It refuses to run unless
        results/lab/frozen.json names the winner and matches this file's hash.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
import pickle
import statistics
import subprocess
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "reference"))
from auction_trail import auction_trail, participation  # noqa: E402
from push_gate import push_gate  # noqa: E402
from tradability import (BAND, CAP, COST_BPS, HORIZONS, REBAL, TARGET_VOL, deflated_sharpe, era,  # noqa: E402
                         load_csv, market_signals, metrics, nw_t, portfolio, strategy_returns, tick_of, weights)

DEV_END, HB_START = "2019-12-31", "2020-01-01"
DEV_ERAS = [("2006-13", "2006-01-01", "2013-12-31"), ("2014-19", "2014-01-01", "2019-12-31")]
LOG_DIR = os.path.join(HERE, "results", "lab")
LOG = os.path.join(LOG_DIR, "trials.jsonl")
NULLS = os.path.join(LOG_DIR, "nulls.json")
PRIOR = ["T-LS", "AM", "AM-A", "TSMOM", "ST", "T-LO", "SMA", "BH"]


# ── per-market base series (cached) ──────────────────────────────────────────
def _cache_path(cache, path, tag):
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    return os.path.join(cache, f"{os.path.basename(path)}.{h}.{tag}.pkl")


def cached(cache, path, tag, fn):
    p = _cache_path(cache, path, tag)
    if os.path.exists(p):
        return pickle.load(open(p, "rb"))
    x = fn()
    os.makedirs(cache, exist_ok=True)
    pickle.dump(x, open(p, "wb"))
    return x


class Base:
    """Lazily computed series for one market."""

    def __init__(self, path, cache):
        self.path, self.cache = path, cache
        self.d = load_csv(path)
        self._sig = None

    def _harness(self):
        if self._sig is None:
            self._sig = cached(self.cache, self.path, "harness", lambda: market_signals(self.d))
        return self._sig

    @property
    def sig(self):
        return self._harness()[0]

    @property
    def vol(self):
        return self._harness()[1]

    @property
    def tr20(self):
        return self._harness()[2]

    @property
    def w(self):
        d = self.d
        return participation(d["high"], d["low"], d["close"], [x if x is not None else 0.0 for x in d["volume"]])

    def trail(self, n):
        def build():
            d = self.d
            v = [x if x is not None else 0.0 for x in d["volume"]]
            gate = push_gate(d["high"], d["low"], d["close"], v)
            return auction_trail(d["high"], d["low"], d["close"], self.w, gate, n=n, mintick=tick_of(d["close"]))
        return cached(self.cache, self.path, f"trail{n}", build)


# ── signal building blocks ───────────────────────────────────────────────────
def log_returns(close):
    return [0.0] + [math.log(close[i] / close[i - 1]) for i in range(1, len(close))]


def mom(close, vol, horizons=HORIZONS, w=None):
    """Multi-horizon volatility-normalised momentum, the harness's score.

    With w=None: s_h = ln(C_t / C_{t-h}) / (sigma_t sqrt h).
    With weights: s_h = sum(w_i r_i) / (sigma_t sqrt(sum w_i^2)) over the last h
    returns, which reduces to the plain score when w = 1.
    S_t = mean_h clip(s_h, -2, 2) / 2."""
    r = log_returns(close)
    ww = [1.0] * len(r) if w is None else [x if x is not None else 1.0 for x in w]
    pa, pb = [0.0], [0.0]
    for a, b in zip(r, ww):
        pa.append(pa[-1] + a * b)
        pb.append(pb[-1] + b * b)
    H = max(horizons)
    out = []
    for t in range(len(close)):
        if t < H or vol[t] is None or vol[t] <= 0:
            out.append(None)
            continue
        s = []
        for h in horizons:
            num = pa[t + 1] - pa[t + 1 - h]
            den = vol[t] * math.sqrt(pb[t + 1] - pb[t + 1 - h])
            s.append(max(-2.0, min(2.0, num / den)) if den > 0 else 0.0)
        out.append(sum(s) / len(s) / 2.0)
    return out


def sign(x):
    return None if x is None else (1.0 if x > 0 else -1.0 if x < 0 else 0.0)


# ── variants: name -> (round, hypothesis, discrete, fn(Base) -> signal) ──────
VARIANTS = {}


def variant(name, rnd, discrete, hypothesis):
    def reg(fn):
        VARIANTS[name] = (rnd, hypothesis, discrete, fn)
        return fn
    return reg


@variant("TSMOM", 1, False, "Reference: multi-horizon (1/3/6/12 m) volatility-normalised momentum of the close, continuous. The engine to beat.")
def v_tsmom(b):
    return mom(b.d["close"], b.vol)


@variant("BOUND", 1, True, "A trail is binary. Does sign(S), the side of TSMOM's decision boundary, keep TSMOM's edge? Literature: continuous sizing beats sign (Baltas & Kosowski 2013).")
def v_bound(b):
    return [sign(x) for x in mom(b.d["close"], b.vol)]


@variant("TRAIL126", 1, True, "The acceptance trail failed at 20 bars, where timing skill is nil. Re-horizoned to a 126-bar (6-month) profile, where trend premia live, it may trend. Spec v2 otherwise.")
def v_trail126(b):
    return [float(x) for x in b.trail(126)["dir"]]


@variant("SKIP21", 1, False, "Single stocks reverse at 1 month (Jegadeesh 1990). Dropping the 21-bar horizon (63/126/252 only) should lift stocks without hurting other classes.")
def v_skip21(b):
    return mom(b.d["close"], b.vol, horizons=(63, 126, 252))


@variant("PMOM", 1, False, "Pragati's premise: moves made on high participation carry more information. Weight each return by the conviction engine's participation w.")
def v_pmom(b):
    return mom(b.d["close"], b.vol, w=b.w)


@variant("TRAIL252", 2, True, "The horizon lever continued: the acceptance trail on a 12-month (252-bar) profile.")
def v_trail252(b):
    return [float(x) for x in b.trail(252)["dir"]]


def trailx(b):
    dirs = [b.trail(n)["dir"] for n in (63, 126, 252)]
    return [sum(x) / 3.0 for x in zip(*dirs)]


@variant("TRAILX", 2, False, "Horizon diversification as TSMOM does it: the mean of the acceptance trail's state at 63, 126 and 252 bars.")
def v_trailx(b):
    return trailx(b)


@variant("TRAILX+TS", 2, False, "Two definitions of trend, where value is accepted (TRAILX) and where price has gone (TSMOM), each in [-1, 1]; if they err at different times their mean is steadier.")
def v_trailx_ts(b):
    s = mom(b.d["close"], b.vol)
    return [None if y is None else (x + y) / 2.0 for x, y in zip(trailx(b), s)]


@variant("TS+T20", 2, False, "Momentum crashes at turning points (Daniel & Moskowitz 2016; Garg et al. 2021): halve TSMOM while Pragati's 20-bar trail points against it.")
def v_ts_t20(b):
    s, d = mom(b.d["close"], b.vol), b.tr20["dir"]
    return [None if x is None else (x * 0.5 if d[t] != 0 and (d[t] > 0) != (x > 0) else x) for t, x in enumerate(s)]


@variant("T126+TS", 3, False, "The trail gives the side, momentum the size: (TRAIL126 + S)/2, so the sign is the 6-month trail's and TSMOM sets the size from ~0 to 1.")
def v_t126_ts(b):
    s, d = mom(b.d["close"], b.vol), b.trail(126)["dir"]
    return [None if y is None else (x + y) / 2.0 for x, y in zip(d, s)]


@variant("T63126+TS", 3, False, "Horizon diversification without the failed 12-month leg: (mean(TRAIL63, TRAIL126) + S)/2.")
def v_t63126_ts(b):
    s, d1, d2 = mom(b.d["close"], b.vol), b.trail(63)["dir"], b.trail(126)["dir"]
    return [None if y is None else ((x1 + x2) / 2.0 + y) / 2.0 for x1, x2, y in zip(d1, d2, s)]


@variant("T126xTS", 3, False, "Consensus only: TRAIL126's side sized max(0, S*side); flat when the two definitions of trend disagree.")
def v_t126xts(b):
    s, d = mom(b.d["close"], b.vol), b.trail(126)["dir"]
    return [None if y is None else x * max(0.0, x * y) for x, y in zip(d, s)]


# ── null test (Amendment 1): driftless walks, volume 1.3x on up days ─────────
def null_walks(folder, n=8, bars=6000):
    import random
    os.makedirs(folder, exist_ok=True)
    paths = []
    for k in range(n):
        p = os.path.join(folder, f"NULL{k}.csv")
        paths.append(p)
        if os.path.exists(p):
            continue
        rng = random.Random(1000 + k)
        c, rows = 100.0, []
        for i in range(bars):
            r = rng.gauss(0.0, 0.01)
            o, c = c, c * math.exp(r)
            hi = max(o, c) * (1 + abs(rng.gauss(0, 0.005)))
            lo = min(o, c) * (1 - abs(rng.gauss(0, 0.005)))
            v = 1e6 * (1.3 if r > 0 else 1.0) * math.exp(rng.gauss(0, 0.3))
            rows.append((f"{2000 + i // 250:04d}-{1 + (i % 250) // 21:02d}-{1 + i % 21:02d}", o, hi, lo, c, v))
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "open", "high", "low", "close", "volume"])
            w.writerows(rows)
    return paths


def _null_one(job):
    path, cache, names = job
    b = Base(path, cache)
    out = {}
    for n in names:
        x = [v for v in VARIANTS[n][3](b) if v is not None]
        out[n] = (sum(x), len(x))
    return out


def cmd_null(a):
    names = list(VARIANTS)
    paths = null_walks(os.path.join(a.cache, "null"))
    with Pool(4) as p:
        parts = p.map(_null_one, [(q, a.cache, names) for q in paths])
    res = {n: sum(x[n][0] for x in parts) / max(1, sum(x[n][1] for x in parts)) for n in names}
    old = json.load(open(NULLS)) if os.path.exists(NULLS) else {}
    old.update(res)
    json.dump(old, open(NULLS, "w"), indent=1)
    for n, v in res.items():
        print(f"{n:<12} null mean {v:+.3f} {'ok' if abs(v) <= 0.10 else 'FAILS'}")


# ── machinery ────────────────────────────────────────────────────────────────
def weights_trade(sig, vol, discrete):
    """tradability.weights' trading branch, with discreteness passed in rather than read from the name."""
    out, w = [], 0.0
    for t in range(len(sig)):
        s = sig[t]
        if s is None or vol[t] is None or vol[t] <= 0:
            out.append(0.0 if s is None else w)
            w = out[-1]
            continue
        target = max(-CAP, min(CAP, s * TARGET_VOL / (vol[t] * math.sqrt(252))))
        if discrete:
            if (t % REBAL == 0) or (math.copysign(1, target) != math.copysign(1, w)) or (target == 0) != (w == 0):
                w = target
        elif t % REBAL == 0 and abs(target - w) > BAND * max(abs(target), 1e-9):
            w = target
        out.append(w)
    return out


def centred(w, n=250):
    """w_t minus the mean of its last n values, counted from the first live (non-zero) weight;
    0 until n live bars exist, so a constant position (buy-and-hold) has no timing component."""
    t0 = next((i for i, x in enumerate(w) if x != 0), len(w))
    out, run = [0.0] * len(w), 0.0
    for t in range(t0, len(w)):
        run += w[t]
        if t - t0 >= n:
            run -= w[t - n]
        if t - t0 >= n - 1:
            out[t] = w[t] - run / n
    return out


def _one(job):
    path, cache, cls, names, prior = job
    b = Base(path, cache)
    if len(b.d["close"]) < 600:
        return None
    cost = COST_BPS.get(cls, 10)
    years = len(b.d["close"]) / 252
    res = {}
    for name in names:
        if prior:
            fam = "invest" if name in ("T-LO", "SMA", "BH") else "trade"
            w = weights(name, b.sig[name], b.vol, fam, ref=b.sig["AM"])
        else:
            _, _, discrete, fn = VARIANTS[name]
            w = weights_trade(fn(b), b.vol, discrete)
        res[name] = {"net": strategy_returns(b.d, w, cost), "timing": strategy_returns(b.d, centred(w), 0.0),
                     "turnover": sum(abs(w[i] - w[i - 1]) for i in range(1, len(w))) / years}
    return os.path.basename(path)[:-4], cls, res


def evaluate(data, classes, cache, names, prior=False, procs=4):
    jobs = [(os.path.join(data, f), cache, classes.get(f[:-4], "index"), names, prior)
            for f in sorted(os.listdir(data)) if f.endswith(".csv")]
    with Pool(procs) as p:
        out = [x for x in p.map(_one, jobs) if x]
    return out


def summarise(rows, name, a, b, eras):
    """Portfolio metrics for one strategy on the dates [a, b]."""
    net = portfolio([r[name]["net"] for _, _, r in rows])
    tim = portfolio([r[name]["timing"] for _, _, r in rows])
    m = metrics(era(net, a, b))
    mt = metrics(era(tim, a, b))
    per = [metrics(era(r[name]["net"], a, b)) for _, _, r in rows]
    per = [x["sharpe"] for x in per if x and x["sharpe"] == x["sharpe"]]
    return {
        "sharpe": m["sharpe"], "cagr": m["cagr"], "mdd": m["mdd"], "t": m["t"], "vol": m["vol"],
        "eras": {e: metrics(era(net, x, y))["sharpe"] for e, x, y in eras},
        "timing_sharpe": mt["sharpe"], "timing_t": mt["t"],
        "breadth": sum(x > 0 for x in per) / len(per) if per else float("nan"),
        "turnover": statistics.mean(r[name]["turnover"] for _, _, r in rows),
        "markets": len(rows),
        "daily_sr": (lambda x: (sum(x) / len(x)) / statistics.pstdev(x))(era(net, a, b)),
    }, era(net, a, b)


def by_class(rows, name, a, b):
    out = {}
    for c in sorted({c for _, c, _ in rows}):
        sub = [r for r in rows if r[1] == c]
        m = metrics(era(portfolio([r[name]["net"] for _, _, r in sub]), a, b))
        if m:
            out[c] = round(m["sharpe"], 3)
    return out


def read_log():
    if not os.path.exists(LOG):
        return []
    return [json.loads(x) for x in open(LOG) if x.strip()]


def write_md(log):
    L = ["# Trail lab · every trial, in order (DEV: 119 markets, dates ≤ 2019-12-31)", "",
         "Generated by `research/trail_lab.py`. Round 0 is the eight earlier candidates, a reference outside the budget.", "",
         "| Round | Variant | Sharpe | t | 2006-13 | 2014-19 | Timing SR (t) | Breadth | Turnover/yr | Max DD | Deflated p | Null mean | Eligible |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    nulls = json.load(open(NULLS)) if os.path.exists(NULLS) else {}
    for x in log:
        m = x["dev"]
        e = m["eras"]
        nm = nulls.get(x["name"])
        ok = all(v > 0 for v in e.values()) and m["timing_sharpe"] > 0 and nm is not None and abs(nm) <= 0.10
        L.append(f"| {x['round']} | {x['name']} | {m['sharpe']:+.2f} | {m['t']:+.2f} | {e['2006-13']:+.2f} | {e['2014-19']:+.2f} | "
                 f"{m['timing_sharpe']:+.2f} ({m['timing_t']:+.1f}) | {m['breadth']:.0%} | {m['turnover']:.1f} | {m['mdd']:.1%} | "
                 f"{'' if x['round'] == 0 else format(x['deflated_p'], '.3f')} | {'' if nm is None else format(nm, '+.3f')} | {'' if x['round'] == 0 else ('yes' if ok else 'no')} |")
    L += ["", "## Per class (DEV Sharpe)", "", "| Variant | " + " | ".join(sorted(log[0]["classes"])) + " |",
          "|---|" + "---|" * len(log[0]["classes"])]
    for x in log:
        L.append(f"| {x['name']} | " + " | ".join(f"{x['classes'].get(c, float('nan')):+.2f}" for c in sorted(log[0]["classes"])) + " |")
    L += ["", "## Hypotheses", ""] + [f"- **{x['name']}** (round {x['round']}): {x['hypothesis']}" for x in log if x["round"] > 0]
    open(os.path.join(LOG_DIR, "trials.md"), "w").write("\n".join(L) + "\n")


def git_head():
    try:
        return subprocess.check_output(["git", "-C", HERE, "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "?"


def cmd_dev(a, classes, prior=False):
    log = read_log()
    done = {x["name"] for x in log}
    names = PRIOR if prior else a.variants.split(",")
    if prior and any(x["round"] == 0 for x in log):
        sys.exit("prior already logged")
    for n in names:
        if not prior and n not in VARIANTS:
            sys.exit(f"unknown variant {n}")
        if not prior and n in done:
            sys.exit(f"{n} is already logged; a changed variant needs a new name")
    budget = sum(1 for x in log if x["round"] > 0 and x["name"] != "TSMOM")
    if not prior and budget + len([n for n in names if n != "TSMOM"]) > 15:
        sys.exit("budget of 15 variants exceeded")
    rows = evaluate(a.data, classes, a.cache, names, prior=prior)
    for n in names:
        s, series = summarise(rows, n, "0000", DEV_END, DEV_ERAS)
        # the lab's TSMOM duplicates prior:TSMOM, so it is not counted twice
        trial_sr = [x["dev"]["daily_sr"] for x in log if x["name"] != "TSMOM"] + [s["daily_sr"]]
        rec = {"round": 0 if prior else int(a.round), "name": ("prior:" + n) if prior else n,
               "hypothesis": "earlier candidate" if prior else VARIANTS[n][1],
               "discrete": None if prior else VARIANTS[n][2], "dev": s,
               "deflated_p": deflated_sharpe(series, trial_sr) if len(trial_sr) >= 2 else float("nan"),
               "classes": by_class(rows, n, "0000", DEV_END),
               "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "commit": git_head()}
        log.append(rec)
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"{rec['name']:<14} SR {s['sharpe']:+.2f} t {s['t']:+.2f} eras {s['eras']} timing {s['timing_sharpe']:+.2f} "
              f"({s['timing_t']:+.1f}) breadth {s['breadth']:.0%} TO {s['turnover']:.1f}")
    write_md(log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prior", "dev", "null", "final"])
    ap.add_argument("--data", required=True)
    ap.add_argument("--classes", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--round")
    ap.add_argument("--variants")
    ap.add_argument("--ha-data")
    ap.add_argument("--ha-classes")
    a = ap.parse_args()
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(a.classes, newline="") as f:
        classes = {r["symbol"]: r["class"] for r in csv.DictReader(f)}
    if a.cmd == "prior":
        cmd_dev(a, classes, prior=True)
    elif a.cmd == "dev":
        cmd_dev(a, classes)
    elif a.cmd == "null":
        cmd_null(a)
    else:
        sys.exit("final: see cmd_final, added at freeze")


if __name__ == "__main__":
    main()
