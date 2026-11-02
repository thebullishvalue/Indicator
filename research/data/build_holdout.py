"""HA, the trail lab's market holdout (docs/trail-lab.md §2), under the price rules of
docs/trail-tradability.md §6 and §6.1. No market here was used in any earlier result.

- NSE: every remaining eligible stock, ranks 61-451 by 2004-05 median traded
  value (the top 60 are DEV). Reads fetch_india.py's folder.
- Crypto: Binance USDT spot pairs (same exclusions) whose archive begins
  2019-01 .. 2021-12, ranked by quote volume over their first 12 months; the
  top 20 are fetched here. Amendment 2: UST is excluded as a stablecoin, and a crypto
  series is cut at its first gap of more than 7 days (a relisted symbol).

    python -I research/data/build_holdout.py INDIA OUT
"""
import concurrent.futures as cf
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_universe import F, corp, spikes, yahoo  # noqa: E402
from fetch_binance import STABLE, klines, listing  # noqa: E402


def crypto(out):
    syms = [p.rstrip("/").split("/")[-1] for p in listing("data/spot/monthly/klines/", "/")]
    # Amendment 2: UST (TerraUSD) is a stablecoin base too
    syms = [s for s in syms if s.endswith("USDT") and s[:-4] not in STABLE | {"UST"} and not re.search(r"(UP|DOWN|BULL|BEAR)$", s[:-4])]

    def months(s):
        return s, sorted(k for k in listing(f"data/spot/monthly/klines/{s}/1d/") if k.endswith(".zip"))

    with cf.ThreadPoolExecutor(6) as ex:
        mm = dict(ex.map(months, syms))
    first = {s: re.search(r"-(\d{4}-\d{2})\.zip$", k[0]).group(1) for s, k in mm.items() if k}
    elig = {s: mm[s] for s, f in first.items() if "2019-01" <= f <= "2021-12"}

    def qv(s):
        return s, sum(float(r[7]) for k in elig[s][:12] for r in klines(k))

    with cf.ThreadPoolExecutor(6) as ex:
        rank = sorted(ex.map(qv, elig), key=lambda x: -x[1])
    json.dump(rank, open(os.path.join(out, "crypto-rank.json"), "w"))
    top = [s for s, _ in rank[:20]]
    print(f"crypto eligible {len(elig)}; top 20: {' '.join(top)}", file=sys.stderr)
    data = {}

    def full(s):
        rows = set()
        for k in elig[s]:
            for r in klines(k):
                t = int(r[0])
                t = t // 1000 if t > 1e14 else t
                rows.add((dt.datetime.fromtimestamp(t / 1000, tz=dt.timezone.utc).strftime("%Y-%m-%d"),
                          float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])))
        return s, pd.DataFrame(sorted(rows), columns=["date", *F, "volume"])

    with cf.ThreadPoolExecutor(6) as ex:
        for s, df in ex.map(full, top):
            data[s] = df
    return data


def main(india, out):
    csvdir = os.path.join(out, "csv")
    os.makedirs(csvdir, exist_ok=True)
    log, classes, dropped, corpev, cuts = [], [], {}, {}, {}

    def write(sym, df, cls):
        df = df.sort_values("date").drop_duplicates("date").reset_index(drop=True)
        if cls == "crypto":  # Amendment 2: a relisted symbol is a different asset; keep the series before its first gap > 7 days
            gap = pd.to_datetime(df["date"]).diff().dt.days
            cut = gap.index[gap > 7]
            if len(cut):
                cuts[sym] = str(df["date"].iloc[cut[0]])[:10]
                df = df.iloc[:cut[0]].reset_index(drop=True)
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
        classes.append((sym, cls))
        log.append((sym, cls, len(df), str(df["date"].iloc[0])[:10], str(df["date"].iloc[-1])[:10],
                    hashlib.sha256(open(path, "rb").read()).hexdigest()))

    rank = []
    for p in glob.glob(os.path.join(india, "stocks", "*.parquet")):
        d = pd.read_parquet(p, columns=["date", "close", "volume"])
        when = pd.to_datetime(d["date"])
        win = d[(when >= "2004-01-01") & (when <= "2005-12-31")]
        if len(win) >= 300:
            rank.append((float((win["close"] * win["volume"]).median()), os.path.basename(p)[:-8]))
    rank.sort(reverse=True)
    for _, s in rank[60:]:
        write(s, yahoo(os.path.join(india, "stocks", s + ".parquet")), "nse_stock")
    for s, df in crypto(out).items():
        write(s, df, "crypto")

    with open(os.path.join(out, "classes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "class"])
        w.writerows(classes)
    with open(os.path.join(out, "universe.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "class", "bars", "first", "last", "sha256"])
        w.writerows(log)
    lines = [f"NSE holdout: ranks 61-{len(rank)} ({len(rank) - 60} stocks)",
             f"markets: {len(classes)} " + str(pd.Series([c for _, c in classes]).value_counts().to_dict()),
             f"rule (a) bad prints dropped: {sum(map(len, dropped.values()))} bars in {len(dropped)} markets"]
    lines += [f"  {k}: {' '.join(v)}" for k, v in dropped.items()]
    lines += [f"Amendment 2 · crypto cut at a gap > 7 days: {cuts}"]
    lines += [f"rule (b) corporate-action gaps neutralised: {sum(map(len, corpev.values()))} in {len(corpev)} markets"]
    lines += [f"  {k}: " + " ".join(f"{d}(x{g})" for d, g in v) for k, v in corpev.items()]
    open(os.path.join(out, "build-log.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines[:3]), file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
