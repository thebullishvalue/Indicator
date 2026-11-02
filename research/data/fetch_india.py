"""NSE stocks, Indian indices and ETFs, commodity futures and INR pairs for the tradability test.

Source: Hugging Face dataset vishnun0027/indian-market-historical-ohlcv (MIT;
Yahoo Finance via yfinance), pinned to revision 825144cb, as fixed in
docs/trail-tradability.md section 6.

Downloads to OUT:
- metadata/asset_universe.parquet
- every equity listed on or before 2003-12-31; the top-60 rule is applied
  later, by build_universe.py
- every index, ETF, commodity and FX file

Needs pandas and pyarrow.

    python -I research/data/fetch_india.py OUT
"""
import concurrent.futures as cf
import os
import sys
import time
import urllib.request

import pandas as pd

REV = "825144cb2f19c3930e6c56542794f2bbf0e2c6cf"
ROOT = f"https://huggingface.co/datasets/vishnun0027/indian-market-historical-ohlcv/resolve/{REV}/"
OTHER = {
    "indices": "INDIA_VIX NIFTY_50 NIFTY_AUTO NIFTY_BANK NIFTY_COMMODITIES NIFTY_ENERGY NIFTY_FMCG NIFTY_INFRA NIFTY_IT "
               "NIFTY_MEDIA NIFTY_METAL NIFTY_MNC NIFTY_PHARMA NIFTY_PSE NIFTY_PSU_BANK NIFTY_REALTY SENSEX",
    "etfs": "BANKBEES CPSEETF GOLDBEES HNGSNGBEES ITETF JUNIORBEES LIQUIDBEES MIDCAPETF MOM100 MOM50 MON100 NIFTYBEES "
            "PHARMABEES PSUBNKBEES SETFNIF50 SETFNIFBK SILVERBEES",
    "commodities": "ALUMINIUM COPPER CRUDE_OIL GOLD NATURAL_GAS PALLADIUM PLATINUM SILVER",
    "forex": "AUDINR CADINR CHFINR EURINR GBPINR JPYINR SGDINR USDINR",
}


def get(out, path):
    dst = os.path.join(out, path)
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return path
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for a in range(6):
        try:
            data = urllib.request.urlopen(ROOT + path, timeout=90).read()
            with open(dst, "wb") as f:
                f.write(data)
            return path
        except Exception as e:
            if a == 5:
                print("FAIL", path, e, file=sys.stderr)
                return None
            time.sleep(2 ** a)


def main(out):
    get(out, "metadata/asset_universe.parquet")
    u = pd.read_parquet(os.path.join(out, "metadata/asset_universe.parquet"))
    eq = u[(u.asset_type == "EQUITY") & (pd.to_datetime(u.listing_date, errors="coerce") <= "2003-12-31")]
    paths = [f"stocks/{s}.parquet" for s in eq.symbol]
    paths += [f"{d}/{n}.parquet" for d, names in OTHER.items() for n in names.split()]
    with cf.ThreadPoolExecutor(6) as ex:
        ok = [p for p in ex.map(lambda p: get(out, p), paths) if p]
    print(f"equities listed by 2003: {len(eq)}; fetched {len(ok)} of {len(paths)}", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
