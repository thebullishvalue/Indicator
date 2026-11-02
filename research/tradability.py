"""The pre-registered tradability test for Pragati's acceptance trail.

Implements docs/trail-tradability.md exactly: its candidates, costs, measures
and pass marks. Nothing here is tuned; a change is a new version of that
document.

    python research/tradability.py --data DIR --classes classes.csv --out report.md
    python research/tradability.py --synthetic 12 --out smoke.md   # mechanics only

DIR holds one CSV per market, named SYMBOL.csv, with a header
date,open,high,low,close,volume (date as YYYY-MM-DD; volume may be empty).
classes.csv maps symbol,class with class in: index etf fx commodity us_stock
nse_stock crypto.

Execution: weights are decided at the close of bar t and held from the open of
t+1 to the open of t+2, so no bar's own close or later is ever traded on.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import random
import statistics
import sys
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "reference"))
sys.path.insert(0, HERE)
from auction_trail import _atr_wilder, auction_trail, participation  # noqa: E402
from push_gate import push_gate  # noqa: E402

ERAS = [("2006-13", "2006-01-01", "2013-12-31"), ("2014-19", "2014-01-01", "2019-12-31"), ("2020-26", "2020-01-01", "2026-12-31")]
COST_BPS = {"index": 5, "etf": 5, "fx": 3, "commodity": 8, "us_stock": 10, "nse_stock": 15, "crypto": 20}
HORIZONS = (21, 63, 126, 252)
TARGET_VOL, CAP, BAND, REBAL = 0.10, 2.0, 0.10, 5
TRADING = ["T-LS", "AM", "AM-A", "TSMOM", "ST"]
INVESTING = ["T-LO", "AM", "AM-A", "TSMOM", "SMA", "BH"]
N_TRIALS = len(set(TRADING) | set(INVESTING))


# ── data ─────────────────────────────────────────────────────────────────────
def load_csv(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            try:
                o, h, l, c = (float(r[k]) for k in ("open", "high", "low", "close"))
            except (KeyError, ValueError):
                continue
            if min(o, h, l, c) <= 0:
                continue
            v = r.get("volume")
            rows.append((r["date"][:10], o, max(h, o, c), min(l, o, c), c, float(v) if v not in (None, "") else None))
    rows.sort()
    return {k: [x[i] for x in rows] for i, k in enumerate(("date", "open", "high", "low", "close", "volume"))}


def synthetic(n_markets, bars=5200, seed=0):
    """Mechanics only: regime-switching walks. Any 'edge' here is the one built in."""
    out = {}
    for mkt in range(n_markets):
        rnd = random.Random(seed + mkt)
        px, rows, day = 100.0, [], 0
        for t in range(bars):
            if t % 140 == 0:
                drift = rnd.choice([0.0008, -0.0008, 0.0, 0.0])
            o = px * math.exp(0.002 * rnd.gauss(0, 1))
            c = o * math.exp(drift + 0.011 * rnd.gauss(0, 1))
            h = max(o, c) * math.exp(abs(0.005 * rnd.gauss(0, 1)))
            l = min(o, c) * math.exp(-abs(0.005 * rnd.gauss(0, 1)))
            y, d = 2005 + day // 252, day % 252
            rows.append((f"{y:04d}-{1 + d // 21:02d}-{1 + d % 21:02d}", o, h, l, c, 1e6 * math.exp(0.35 * rnd.gauss(0, 1))))
            px, day = c, day + 1
        out[f"SYN{mkt:02d}"] = {k: [x[i] for x in rows] for i, k in enumerate(("date", "open", "high", "low", "close", "volume"))}
    return out


# ── signals ──────────────────────────────────────────────────────────────────
def ewma_vol(close, span=60):
    a, var, out = 2.0 / (span + 1), None, [None]
    for i in range(1, len(close)):
        r = math.log(close[i] / close[i - 1])
        var = r * r if var is None else (1 - a) * var + a * r * r
        out.append(math.sqrt(var) if i >= span else None)
    return out


def momentum_score(level, vol):
    """S_t = mean over the four horizons of clip(ln(L_t / L_{t-h}) / (sigma_t * sqrt h), -2, 2), over 2."""
    out = []
    for t in range(len(level)):
        if vol[t] is None or vol[t] <= 0 or level[t] is None or t < max(HORIZONS):
            out.append(None)
            continue
        parts = [level[t - h] for h in HORIZONS]
        if None in parts:
            out.append(None)
            continue
        s = [max(-2.0, min(2.0, math.log(level[t] / p) / (vol[t] * math.sqrt(h)))) for p, h in zip(parts, HORIZONS)]
        out.append(sum(s) / len(s) / 2.0)
    return out


def supertrend(high, low, close, n=10, k=3.0):
    atr = _atr_wilder(high, low, close, n)
    d, up, dn, out = 1, None, None, []
    for t in range(len(close)):
        if atr[t] is None:
            out.append(0)
            continue
        hl2 = (high[t] + low[t]) / 2
        bu, bd = hl2 - k * atr[t], hl2 + k * atr[t]
        up = bu if up is None or close[t - 1] < up else max(bu, up)
        dn = bd if dn is None or close[t - 1] > dn else min(bd, dn)
        d = 1 if close[t] > dn else -1 if close[t] < up else d
        out.append(d)
    return out


def tick_of(close):
    med = statistics.median(close)
    return 10 ** math.floor(math.log10(med)) / 1000.0


def market_signals(d):
    h, l, c, v = d["high"], d["low"], d["close"], [x if x is not None else 0.0 for x in d["volume"]]
    w = participation(h, l, c, v)
    gate = push_gate(h, l, c, v)
    tr = auction_trail(h, l, c, w, gate, n=20, mintick=tick_of(c))
    vol = ewma_vol(c)
    am = momentum_score(tr["poc"], vol)
    ts = momentum_score(c, vol)
    # AM-A: halve |S| while the move in S's own direction is unaccepted - a probe
    # onset in the last 5 bars whose break points the way S does (break side = -D)
    ama, last_onset = [], []
    for t in range(len(c)):
        if tr["onset"][t]:
            last_onset.append((t, -tr["dir"][t]))
        last_onset = [x for x in last_onset if t - x[0] < 5]
        s = am[t]
        if s is not None and any(side == (1 if s > 0 else -1) for _, side in last_onset):
            s = s / 2.0
        ama.append(s)
    sma = [None] * len(c)
    run = 0.0
    for t in range(len(c)):
        run += c[t]
        if t >= 200:
            run -= c[t - 200]
        if t >= 199:
            sma[t] = 1.0 if c[t] > run / 200 else 0.0
    sig = {"T-LS": [float(x) for x in tr["dir"]], "T-LO": [1.0 if x == 1 else 0.0 for x in tr["dir"]], "AM": am, "AM-A": ama,
           "TSMOM": ts, "ST": [float(x) for x in supertrend(h, l, c)], "SMA": sma, "BH": [1.0] * len(c)}
    return sig, vol, tr


# ── backtest ─────────────────────────────────────────────────────────────────
def weights(name, sig, vol, family, ref=None):
    """Trading: volatility-targeted. Investing: long-only, unlevered, IN (1) while
    the signal is positive, OUT (0) otherwise - Faber's use of a trend filter;
    AM-A holds half while its long move is unaccepted (its score was halved)."""
    discrete = name in ("T-LS", "T-LO", "ST", "SMA", "BH") or family == "invest"
    out, w = [], 0.0
    for t in range(len(sig)):
        s = sig[t]
        if s is None or vol[t] is None or vol[t] <= 0:
            out.append(0.0 if s is None else w)
            w = out[-1]
            continue
        if family == "trade":
            target = max(-CAP, min(CAP, s * TARGET_VOL / (vol[t] * math.sqrt(252))))
        else:
            target = 1.0 if s > 0 else 0.0
            if name == "AM-A" and ref is not None and ref[t] is not None and abs(s) < abs(ref[t]):
                target *= 0.5
        if discrete:
            if (t % REBAL == 0) or (math.copysign(1, target) != math.copysign(1, w)) or (target == 0) != (w == 0):
                w = target
        elif t % REBAL == 0 and abs(target - w) > BAND * max(abs(target), 1e-9):
            w = target
        out.append(w)
    return out


def strategy_returns(d, w, cost_bps):
    """Weight decided at close t, held open(t+1) -> open(t+2). Returns {date of t+1: net return}."""
    o, dates, out, prev = d["open"], d["date"], {}, 0.0
    for t in range(len(o) - 2):
        r = w[t] * (o[t + 2] / o[t + 1] - 1.0) - cost_bps / 1e4 * abs(w[t] - prev)
        out[dates[t + 1]] = r
        prev = w[t]
    return out


# ── measures ─────────────────────────────────────────────────────────────────
def nw_t(x, lags=10):
    n = len(x)
    if n < 30:
        return float("nan")
    m = sum(x) / n
    e = [v - m for v in x]
    g0 = sum(v * v for v in e) / n
    s = g0 + 2 * sum((1 - L / (lags + 1)) * sum(e[i] * e[i - L] for i in range(L, n)) / n for L in range(1, lags + 1))
    return m / math.sqrt(s / n) if s > 0 else float("nan")


def metrics(rets, turnover=None):
    x = list(rets)
    n = len(x)
    if n < 60:
        return None
    eq, peak, mdd, logsum = 1.0, 1.0, 0.0, 0.0
    for r in x:
        eq *= 1 + r
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
        logsum += math.log(max(1 + r, 1e-9))
    sd = statistics.pstdev(x)
    return {"cagr": math.exp(logsum * 252 / n) - 1, "vol": sd * math.sqrt(252), "sharpe": (sum(x) / n) / sd * math.sqrt(252) if sd > 0 else float("nan"),
            "mdd": mdd, "t": nw_t(x), "n": n, "turnover": turnover}


def deflated_sharpe(rets, trial_sharpes_daily):
    """Bailey & Lopez de Prado (2014): P(true SR > the best of N noise trials)."""
    x = list(rets)
    n = len(x)
    m, sd = sum(x) / n, statistics.pstdev(x)
    if sd <= 0 or len(trial_sharpes_daily) < 2:
        return float("nan")
    sr = m / sd
    sk = sum((v - m) ** 3 for v in x) / n / sd ** 3
    ku = sum((v - m) ** 4 for v in x) / n / sd ** 4
    N, g = len(trial_sharpes_daily), 0.5772156649
    z = NormalDist()
    sr0 = math.sqrt(statistics.pvariance(trial_sharpes_daily)) * ((1 - g) * z.inv_cdf(1 - 1 / N) + g * z.inv_cdf(1 - 1 / (N * math.e)))
    den = math.sqrt(max(1 - sk * sr + (ku - 1) / 4 * sr * sr, 1e-12))
    return z.cdf((sr - sr0) * math.sqrt(n - 1) / den)


def portfolio(series_by_market):
    days = sorted({d for s in series_by_market for d in s})
    out = {}
    for d in days:
        v = [s[d] for s in series_by_market if d in s]
        if v:
            out[d] = sum(v) / len(v)
    return out


def era(series, a, b):
    return [r for d, r in sorted(series.items()) if a <= d <= b]


def h4_scorer(d, pos, vol, horizon):
    """The v9 scorer: position centred on its trailing 250-bar mean x forward return over sigma*sqrt(h)."""
    c, out = d["close"], []
    for t in range(250, len(c) - horizon):
        if vol[t] is None or vol[t] <= 0:
            continue
        centred = pos[t] - sum(pos[t - 249:t + 1]) / 250
        out.append(centred * math.log(c[t + horizon] / c[t]) / (vol[t] * math.sqrt(horizon)))
    return out


def h5_counts(d, tr, vol, horizon=10):
    """EXCESS persistence: after a flip (price on the new side) or a probe onset
    (price beyond the trail on the break side), is price still beyond the trail
    10 bars on - minus the chance a driftless walk from that distance, at that
    volatility, would be: Phi(side * ln(C/T) / (sigma * sqrt h)). A flip starts
    further from the trail than a probe, so raw persistence favours flips even
    in a random walk; the excess does not. Returns sums and counts."""
    c, z = d["close"], NormalDist()
    f, p = [], []
    for t in range(len(c) - horizon):
        T, s = tr["lvl"][t], vol[t]
        if T is None or T <= 0 or s is None or s <= 0:
            continue
        for flag, side, bucket in ((tr["flip"][t], tr["dir"][t], f), (tr["onset"][t], -tr["dir"][t], p)):
            if flag and side:
                hit = 1.0 if side * (c[t + horizon] - T) > 0 else 0.0
                bucket.append(hit - z.cdf(side * math.log(c[t] / T) / (s * math.sqrt(horizon))))
    return f, p


# ── run ──────────────────────────────────────────────────────────────────────
def run(markets, classes, out_path, synthetic_flag):
    res = {fam: {s: [] for s in names} for fam, names in (("trade", TRADING), ("invest", INVESTING))}
    turn = {fam: {s: [] for s in names} for fam, names in (("trade", TRADING), ("invest", INVESTING))}
    h4 = {10: [], 20: []}
    h5 = {e[0]: ([], []) for e in ERAS}
    h5["all"] = ([], [])
    for sym, d in sorted(markets.items()):
        if len(d["close"]) < 600:
            continue
        cls = classes.get(sym, "index")
        sig, vol, tr = market_signals(d)
        years = len(d["close"]) / 252
        for fam, names in (("trade", TRADING), ("invest", INVESTING)):
            for s in names:
                w = weights(s, sig[s], vol, fam, ref=sig["AM"])
                res[fam][s].append(strategy_returns(d, w, COST_BPS.get(cls, 10)))
                turn[fam][s].append(sum(abs(w[i] - w[i - 1]) for i in range(1, len(w))) / years)
        for hz in (10, 20):
            x = h4_scorer(d, sig["T-LS"], vol, hz)
            if len(x) > 60:
                h4[hz].append((sum(x) / len(x), nw_t(x, hz)))
        for name, a, b in ERAS + [("all", "0000", "9999")]:
            keep = [i for i, dt in enumerate(d["date"]) if a <= dt <= b]
            sub = {k: [tr[k][i] for i in keep] for k in ("flip", "onset", "dir", "lvl")}
            f, p = h5_counts({"close": [d["close"][i] for i in keep]}, sub, [vol[i] for i in keep])
            h5[name][0].extend(f)
            h5[name][1].extend(p)
    lines = []
    if synthetic_flag:
        lines += ["# SMOKE TEST ON SYNTHETIC DATA - mechanics only, NOT evidence", "",
                  "Synthetic walks contain whatever edge they were built with. Nothing below says anything about markets.", ""]
    else:
        lines += ["# Pragati acceptance trail - tradability test", "", "Pre-registered in docs/trail-tradability.md; run unchanged.", ""]
    verdict = {}
    for fam, names in (("trade", TRADING), ("invest", INVESTING)):
        port = {s: portfolio(res[fam][s]) for s in names}
        daily_sr = []
        for s in names:
            x = list(port[s].values())
            sd = statistics.pstdev(x) if len(x) > 1 else 0
            daily_sr.append(sum(x) / len(x) / sd if sd > 0 else 0.0)
        lines += [f"## {'Trading' if fam == 'trade' else 'Investing'} family · equal-{'risk' if fam == 'trade' else 'weight'} portfolio, net of costs", "",
                  "| Strategy | Era | CAGR | Vol | Sharpe | Max DD | t (NW) | Turnover/yr | Deflated SR p |", "|---|---|---|---|---|---|---|---|---|"]
        for s in names:
            to = statistics.mean(turn[fam][s]) if turn[fam][s] else float("nan")
            for name, a, b in [("pooled", "0000", "9999")] + ERAS:
                m = metrics(era(port[s], a, b), to)
                if not m:
                    continue
                dsr = deflated_sharpe(era(port[s], a, b), daily_sr) if name == "pooled" else float("nan")
                verdict[(fam, s, name)] = (m, dsr)
                lines.append(f"| {s} | {name} | {m['cagr']:+.1%} | {m['vol']:.1%} | {m['sharpe']:+.2f} | {m['mdd']:.1%} | {m['t']:+.2f} | {to:.1f} | {'' if math.isnan(dsr) else f'{dsr:.3f}'} |")
        lines.append("")
    # pass marks
    def get(f, s, e):
        return verdict.get((f, s, e), (None, float("nan")))
    lines += ["## Pass marks (docs/trail-tradability.md §4)", ""]
    ts = get("trade", "TSMOM", "pooled")[0]
    for s in ("AM", "AM-A", "T-LS"):
        m, dsr = get("trade", s, "pooled")
        if not m:
            continue
        ref = [get("trade", b, "pooled")[0] for b in (("TSMOM",) if s != "T-LS" else ("TSMOM", "ST"))]
        eras_pos = all((get("trade", s, e)[0] or {"sharpe": -1})["sharpe"] > 0 for e, _, _ in ERAS)
        ok = (m["sharpe"] >= 0.5 and all(r and m["sharpe"] >= r["sharpe"] for r in ref) and eras_pos and dsr >= 0.95 and m["t"] > 3)
        refs = ", ".join("%+.2f" % r["sharpe"] for r in ref if r)
        lines.append(f"- **Trade {s}: {'PASS' if ok else 'FAIL'}**: Sharpe {m['sharpe']:+.2f} (needs ≥ 0.50 and ≥ {refs}), every era positive: {eras_pos}, deflated p {dsr:.3f} (≥ 0.95), t {m['t']:+.2f} (> 3)")
    bh = get("invest", "BH", "pooled")[0]
    for s in ("T-LO", "AM", "AM-A"):
        m = get("invest", s, "pooled")[0]
        if not (m and bh):
            continue
        def good(e):
            a, b = get("invest", s, e)[0], get("invest", "BH", e)[0]
            return bool(a and b and abs(a["mdd"]) <= 0.7 * abs(b["mdd"]) and a["cagr"] >= b["cagr"] - 0.01)
        n_eras = sum(good(e) for e, _, _ in ERAS)
        ok = good("pooled") and n_eras >= 2
        lines.append(f"- **Invest {s}: {'PASS' if ok else 'FAIL'}**: max DD {m['mdd']:.1%} vs BH {bh['mdd']:.1%} (needs ≥ 30% shallower), CAGR {m['cagr']:+.1%} vs BH {bh['cagr']:+.1%} (≥ BH − 1 pt), eras passing {n_eras}/3 (≥ 2)")
    lines += ["", "## H4 · the trail's state as a position (the v9 scorer)", "", "| Horizon | Markets | Mean score | Mean t |", "|---|---|---|---|"]
    for hz in (10, 20):
        if h4[hz]:
            lines.append(f"| {hz} bars | {len(h4[hz])} | {statistics.mean(x[0] for x in h4[hz]):+.4f} | {statistics.mean(x[1] for x in h4[hz]):+.2f} |")
    lines += ["", "## H5 · does acceptance separate breaks that hold from breaks that fail?", "",
              "Excess persistence 10 bars on, against each event's own random-walk expectation (≈ 0 on a driftless walk).", "",
              "| Era | Flips | Flip excess | Probe onsets | Probe excess | Difference | t |", "|---|---|---|---|---|---|---|"]
    for name in [e[0] for e in ERAS] + ["all"]:
        f, p = h5[name]
        if len(f) > 1 and len(p) > 1:
            mf, mp = statistics.mean(f), statistics.mean(p)
            se = math.sqrt(statistics.pvariance(f) / len(f) + statistics.pvariance(p) / len(p))
            lines.append(f"| {name} | {len(f)} | {mf:+.1%} | {len(p)} | {mp:+.1%} | {mf - mp:+.1%} | {(mf - mp) / se if se > 0 else float('nan'):+.2f} |")
    lines += ["", f"Markets: {sum(1 for d in markets.values() if len(d['close']) >= 600)} · candidates: {N_TRIALS} (the deflated Sharpe's trial count) · costs: {COST_BPS} bps one way."]
    open(out_path, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data")
    ap.add_argument("--classes")
    ap.add_argument("--synthetic", type=int, default=0)
    ap.add_argument("--out", default="tradability-report.md")
    a = ap.parse_args()
    if a.synthetic:
        markets, classes = synthetic(a.synthetic), {}
    else:
        markets = {os.path.splitext(f)[0]: load_csv(os.path.join(a.data, f)) for f in os.listdir(a.data) if f.endswith(".csv")}
        classes = {}
        if a.classes:
            with open(a.classes, newline="") as f:
                classes = {r["symbol"]: r["class"] for r in csv.DictReader(f)}
    run(markets, classes, a.out, bool(a.synthetic))


if __name__ == "__main__":
    main()
