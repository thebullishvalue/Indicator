"""Crypto universe for the tradability test, from Binance's public archive (data.binance.vision).

Applies docs/trail-tradability.md section 6:
- Eligible: USDT spot pairs whose archive begins in or before 2018-12.
- Excluded: stablecoin bases and leveraged tokens.
- Ranked by total quote volume over calendar 2018.
- The top 15 are taken, delisted pairs included.

Writes OUT/csv/SYMBOL.csv (date,open,high,low,close,volume; UTC days) and
OUT/rank2018.json.

    python -I research/data/fetch_binance.py OUT
"""
import concurrent.futures as cf
import csv
import datetime as dt
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import zipfile

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DL = "https://data.binance.vision/"
STABLE = {"USDC", "TUSD", "PAX", "USDP", "BUSD", "USDS", "USDSB", "DAI", "FDUSD"}


def get(url):
    for a in range(6):
        try:
            return urllib.request.urlopen(url, timeout=60).read()
        except Exception:
            if a == 5:
                raise
            time.sleep(2 ** a)


def listing(prefix, delimiter=""):
    """S3 listing: keys, or with a delimiter the sub-prefixes."""
    out, marker = [], ""
    while True:
        q = {"prefix": prefix, "marker": marker}
        if delimiter:
            q["delimiter"] = delimiter
        x = get(f"{S3}?{urllib.parse.urlencode(q)}").decode()
        items = re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:] + re.findall(r"<Key>([^<]+)</Key>", x)
        out += items
        if "<IsTruncated>true</IsTruncated>" not in x or not items:
            return out
        marker = items[-1]


def klines(key):
    z = zipfile.ZipFile(io.BytesIO(get(DL + key)))
    return [r for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]))) if r and r[0].isdigit()]


def main(out):
    os.makedirs(os.path.join(out, "csv"), exist_ok=True)
    syms = [p.rstrip("/").split("/")[-1] for p in listing("data/spot/monthly/klines/", "/")]
    syms = [s for s in syms if s.endswith("USDT") and s[:-4] not in STABLE and not re.search(r"(UP|DOWN|BULL|BEAR)$", s[:-4])]

    def months(s):
        return s, sorted(k for k in listing(f"data/spot/monthly/klines/{s}/1d/") if k.endswith(".zip"))

    with cf.ThreadPoolExecutor(6) as ex:
        mm = dict(ex.map(months, syms))
    elig = {s: k for s, k in mm.items() if k and re.search(r"-(\d{4})-\d{2}\.zip$", k[0]).group(1) <= "2018"}

    def qv2018(s):
        return s, sum(float(r[7]) for k in elig[s] if "-2018-" in k for r in klines(k))

    with cf.ThreadPoolExecutor(6) as ex:
        rank = sorted(ex.map(qv2018, elig), key=lambda x: -x[1])
    json.dump(rank, open(os.path.join(out, "rank2018.json"), "w"))
    top = [s for s, _ in rank[:15]]
    print(f"eligible {len(elig)}; top 15: {' '.join(top)}", file=sys.stderr)

    def full(s):
        rows = set()
        for k in elig[s]:
            for r in klines(k):
                t = int(r[0])
                t = t // 1000 if t > 1e14 else t  # the archive moved to microseconds in 2025
                day = dt.datetime.fromtimestamp(t / 1000, tz=dt.timezone.utc).strftime("%Y-%m-%d")
                rows.add((day, r[1], r[2], r[3], r[4], r[5]))
        rows = sorted(rows)
        with open(os.path.join(out, "csv", s + ".csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date", "open", "high", "low", "close", "volume"])
            w.writerows(rows)
        return s, len(rows), rows[0][0], rows[-1][0]

    with cf.ThreadPoolExecutor(6) as ex:
        for x in ex.map(full, top):
            print(*x, file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
