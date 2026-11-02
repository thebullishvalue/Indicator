"""Apply docs/trail-tradability.md sections 6 and 6.1 to the downloaded files.

Inputs: INDIA (fetch_india.py's folder) and BINANCE (fetch_binance.py's folder).
Writes, into OUT:
- csv/SYMBOL.csv, one per market, in the harness's format
- classes.csv
- universe.csv: bars, first and last date, and the sha256 of each CSV
- build-log.txt: dropped bad prints and neutralised corporate-action gaps

Rules:
- NSE: listed by 2003, >= 300 bars in 2004-05, the top 60 by median traded value.
- Indices: all but INDIA_VIX. ETFs: all but LIQUIDBEES. Commodities, FX: all.
- Crypto: fetch_binance.py's top 15.
- Prices: total return (OHLC x adj_close / close).
- Rule (a): bad-print episodes are dropped.
- Rule (b): gaps beyond x0.5 or x2 are neutralised, outside crypto.

Needs pandas and pyarrow.

    python -I research/data/build_universe.py INDIA BINANCE OUT
"""
import csv
import glob
import hashlib
import os
import shutil
import sys

import pandas as pd

F = ("open", "high", "low", "close")


def spikes(df):
    """Rule (a): episodes of 1-5 bars where every bar has a price beyond 3x or 1/3 of both
    the last close before and the first close after the episode."""
    c = df["close"].tolist()
    px = df[list(F)].values.tolist()
    n, bad, i = len(c), [], 1

    def off(j, a, b):
        return any((x > 3 * a and x > 3 * b) or (x < a / 3 and x < b / 3) for x in px[j])

    while i < n - 1:
        hit = 0
        for L in range(1, 6):
            if i + L >= n:
                break
            a, b = c[i - 1], c[i + L]
            if a > 0 and b > 0 and all(off(j, a, b) for j in range(i, i + L)):
                hit = L
                break
        if hit:
            bad += list(range(i, i + hit))
            i += hit
        else:
            i += 1
    return bad


def corp(df):
    """Rule (b): an overnight gap beyond x0.5 / x2 rescales every earlier price by the gap."""
    df, ev = df.copy(), []
    o, c = df["open"].values, df["close"].values
    for t in range(len(df) - 1, 0, -1):
        if c[t - 1] > 0 and o[t] > 0:
            g = o[t] / c[t - 1]
            if g < 0.5 or g > 2.0:
                for k in F:
                    df.loc[: t - 1, k] = df.loc[: t - 1, k] * g
                o, c = df["open"].values, df["close"].values
                ev.append((str(df["date"].iloc[t])[:10], round(float(g), 3)))
    return df, ev


def yahoo(path):
    d = pd.read_parquet(path)
    f = (d["adj_close"] / d["close"]).where((d["adj_close"] > 0) & (d["close"] > 0)).fillna(1.0)
    for k in F:
        d[k] = d[k] * f
    return d[["date", *F, "volume"]]


def main(india, binance, out):
    csvdir = os.path.join(out, "csv")
    shutil.rmtree(csvdir, ignore_errors=True)
    os.makedirs(csvdir)
    log, classes, dropped, corpev = [], [], {}, {}

    def write(sym, df, cls):
        df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
        df = df[(df[list(F)] > 0).all(axis=1)].reset_index(drop=True)
        bad = spikes(df)
        if bad:
            dropped[sym] = [str(df["date"].iloc[i])[:10] for i in bad]
            df = df.drop(index=bad).reset_index(drop=True)
        if cls != "crypto":
            df, ev = corp(df)
            if ev:
                corpev[sym] = ev
        path = os.path.join(csvdir, sym + ".csv")
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", *F, "volume"])
            for r in df.itertuples(index=False):
                v = "" if (pd.isna(r.volume) or r.volume <= 0) else repr(float(r.volume))
                w.writerow([str(r.date)[:10], repr(r.open), repr(r.high), repr(r.low), repr(r.close), v])
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        classes.append((sym, cls))
        log.append((sym, cls, len(df), str(df["date"].iloc[0])[:10], str(df["date"].iloc[-1])[:10], sha))

    rank = []
    for p in glob.glob(os.path.join(india, "stocks", "*.parquet")):
        d = pd.read_parquet(p, columns=["date", "close", "volume"])
        when = pd.to_datetime(d["date"])
        win = d[(when >= "2004-01-01") & (when <= "2005-12-31")]
        if len(win) >= 300:
            rank.append((float((win["close"] * win["volume"]).median()), os.path.basename(p)[:-8]))
    rank.sort(reverse=True)
    for _, s in rank[:60]:
        write(s, yahoo(os.path.join(india, "stocks", s + ".parquet")), "nse_stock")
    for sub, cls, skip in (("indices", "index", {"INDIA_VIX"}), ("etfs", "etf", {"LIQUIDBEES"}),
                           ("commodities", "commodity", set()), ("forex", "fx", set())):
        for p in sorted(glob.glob(os.path.join(india, sub, "*.parquet"))):
            s = os.path.basename(p)[:-8]
            if s not in skip:
                write(s, yahoo(p), cls)
    for p in sorted(glob.glob(os.path.join(binance, "csv", "*.csv"))):
        write(os.path.basename(p)[:-4], pd.read_csv(p), "crypto")

    with open(os.path.join(out, "classes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "class"])
        w.writerows(classes)
    with open(os.path.join(out, "universe.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "class", "bars", "first", "last", "sha256"])
        w.writerows(log)
    counts = pd.Series([c for _, c in classes]).value_counts().to_dict()
    lines = [f"NSE eligible: {len(rank)}; taken: {' '.join(s for _, s in rank[:60])}",
             f"markets: {len(classes)} {counts}",
             f"rule (a) bad prints dropped: {sum(map(len, dropped.values()))} bars in {len(dropped)} markets"]
    lines += [f"  {k}: {' '.join(v)}" for k, v in dropped.items()]
    lines += [f"rule (b) corporate-action gaps neutralised: {sum(map(len, corpev.values()))} in {len(corpev)} markets"]
    lines += [f"  {k}: " + " ".join(f"{d}(x{g})" for d, g in v) for k, v in corpev.items()]
    open(os.path.join(out, "build-log.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:3]), file=sys.stderr)


if __name__ == "__main__":
    main(*sys.argv[1:4])
