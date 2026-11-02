"""Diagnostics for the tradability test. Reporting only: no pass mark is computed here.

docs/trail-tradability.md section 4 promises results "per market, per class, per
era"; research/tradability.py prints only the portfolio. This script reuses that
harness's own functions unchanged and adds:

1. Per class: each candidate's equal-risk (trading) or equal-weight (investing)
   portfolio Sharpe within the class, pooled and per era.
2. Breadth: the share of markets where each trading candidate's net Sharpe > 0.
3. Cost drag: pooled portfolio Sharpe gross and net of costs.
4. Common start (a SENSITIVITY, not the test): every strategy in a market is
   scored only from the first bar on which all candidates are live (the push
   gate's ~450-bar warm-up and the trail's start), so BH gets no head start.

    python research/tradability_diag.py --data DIR --classes classes.csv --out diag.md
"""
from __future__ import annotations

import argparse
import csv
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tradability import (COST_BPS, ERAS, INVESTING, TRADING, era, load_csv,  # noqa: E402
                         market_signals, metrics, portfolio, strategy_returns, weights)

CLASS_ORDER = ["nse_stock", "index", "etf", "commodity", "fx", "crypto", "us_stock"]


def live_from(sig, vol, tr):
    """First bar on which every candidate's signal and the volatility exist and the trail has started."""
    for t in range(len(vol)):
        if vol[t] and tr["dir"][t] != 0 and all(sig[s][t] is not None for s in sig):
            return t
    return len(vol)


def sharpe(series, a="0000", b="9999"):
    m = metrics(era(series, a, b))
    return m["sharpe"] if m else float("nan")


def fmt(x):
    return "" if x != x else f"{x:+.2f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--classes", required=True)
    ap.add_argument("--out", default="tradability-diag.md")
    a = ap.parse_args()
    with open(a.classes, newline="") as f:
        classes = {r["symbol"]: r["class"] for r in csv.DictReader(f)}
    fams = (("trade", TRADING), ("invest", INVESTING))
    net = {fam: {s: {} for s in names} for fam, names in fams}      # market -> series
    gross = {fam: {s: {} for s in names} for fam, names in fams}
    common = {fam: {s: {} for s in names} for fam, names in fams}
    for fn in sorted(os.listdir(a.data)):
        if not fn.endswith(".csv"):
            continue
        sym = fn[:-4]
        d = load_csv(os.path.join(a.data, fn))
        if len(d["close"]) < 600:
            continue
        cost = COST_BPS.get(classes.get(sym, "index"), 10)
        sig, vol, tr = market_signals(d)
        t0 = live_from(sig, vol, tr)
        start = d["date"][min(t0 + 1, len(d["date"]) - 1)]
        for fam, names in fams:
            for s in names:
                w = weights(s, sig[s], vol, fam, ref=sig["AM"])
                r = strategy_returns(d, w, cost)
                net[fam][s][sym] = r
                gross[fam][s][sym] = strategy_returns(d, w, 0.0)
                common[fam][s][sym] = {k: v for k, v in r.items() if k >= start}
    syms = sorted(next(iter(net["trade"].values())))
    present = [c for c in CLASS_ORDER if any(classes.get(s) == c for s in syms)]
    L = ["# Tradability test · diagnostics (reporting only, no pass marks)", "",
         "Reuses `research/tradability.py` unchanged. Section 4 of the pre-registration lists per-class and per-era results as measures; these are they.", ""]
    for fam, names in fams:
        L += [f"## {'Trading' if fam == 'trade' else 'Investing'} family · Sharpe by class (net)", "",
              "| Class | Markets | Era | " + " | ".join(names) + " |", "|---|---|---|" + "---|" * len(names)]
        for c in present:
            mk = [s for s in syms if classes.get(s) == c]
            ports = {s: portfolio([net[fam][s][m] for m in mk]) for s in names}
            for name, x, y in [("pooled", "0000", "9999")] + ERAS:
                L.append(f"| {c} | {len(mk)} | {name} | " + " | ".join(fmt(sharpe(ports[s], x, y)) for s in names) + " |")
        L.append("")
    L += ["## Breadth · share of markets with net Sharpe > 0 (trading family, whole history)", "",
          "| Class | " + " | ".join(TRADING) + " |", "|---|" + "---|" * len(TRADING)]
    for c in present + ["all"]:
        mk = [s for s in syms if c == "all" or classes.get(s) == c]
        row = []
        for s in TRADING:
            v = [sharpe(net["trade"][s][m]) for m in mk]
            v = [x for x in v if x == x]
            row.append(f"{sum(x > 0 for x in v) / len(v):.0%}" if v else "")
        L.append(f"| {c} | " + " | ".join(row) + " |")
    L += ["", "## Cost drag · pooled portfolio Sharpe, gross → net", "", "| Family | " + " | ".join(sorted(set(TRADING) | set(INVESTING))) + " |",
          "|---|" + "---|" * len(set(TRADING) | set(INVESTING))]
    for fam, names in fams:
        cells = []
        for s in sorted(set(TRADING) | set(INVESTING)):
            if s in names:
                g = sharpe(portfolio(list(gross[fam][s].values())))
                n = sharpe(portfolio(list(net[fam][s].values())))
                cells.append(f"{g:+.2f} → {n:+.2f}")
            else:
                cells.append("")
        L.append(f"| {fam} | " + " | ".join(cells) + " |")
    L += ["", "## Common start · SENSITIVITY, not the pre-registered test", "",
          "Each market is scored from the first bar on which every candidate is live, so buy-and-hold gets no head start during the push gate's warm-up.", "",
          "| Family | Strategy | Era | CAGR | Sharpe | Max DD |", "|---|---|---|---|---|---|"]
    for fam, names in fams:
        for s in names:
            p = portfolio(list(common[fam][s].values()))
            for name, x, y in [("pooled", "0000", "9999")] + ERAS:
                m = metrics(era(p, x, y))
                if m:
                    L.append(f"| {fam} | {s} | {name} | {m['cagr']:+.1%} | {m['sharpe']:+.2f} | {m['mdd']:.1%} |")
    open(a.out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
