"""Download daily OHLCV from Yahoo's public chart endpoint into data/<class>/<symbol>.csv"""
import os, sys, time, json, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
U = {
 "us": "AAPL MSFT AMZN GOOGL NVDA JPM JNJ XOM PG KO PEP WMT HD DIS INTC CSCO ORCL IBM GE BA CAT MMM MCD NKE UNH PFE MRK ABT T VZ CVX COP BAC WFC C GS AXP MO LLY AMGN GILD TXN QCOM ADBE COST SBUX LOW UPS FDX HON".split(),
 "nse": [s + ".NS" for s in "RELIANCE TCS INFY HDFCBANK ICICIBANK SBIN ITC HINDUNILVR LT AXISBANK KOTAKBANK BHARTIARTL MARUTI SUNPHARMA TATAMOTORS TATASTEEL WIPRO HCLTECH ONGC NTPC POWERGRID BAJFINANCE ASIANPAINT TITAN ULTRACEMCO NESTLEIND M&M DRREDDY CIPLA GRASIM HINDALCO JSWSTEEL BPCL HEROMOTOCO EICHERMOT BRITANNIA TECHM INDUSINDBK ADANIENT BAJAJ-AUTO".split()],
 "index": "^GSPC ^NDX ^DJI ^RUT ^NSEI ^NSEBANK ^FTSE ^GDAXI ^FCHI ^N225 ^HSI ^STOXX50E ^BVSP ^AXJO ^KS11 ^TWII ^GSPTSE ^MXX".split(),
 "cmdty": "GC=F SI=F CL=F BZ=F NG=F HG=F PL=F PA=F ZC=F ZS=F ZW=F KC=F SB=F CT=F CC=F LE=F".split(),
 "fx": [s + "=X" for s in "EURUSD GBPUSD USDJPY AUDUSD USDCAD USDCHF NZDUSD USDINR EURJPY GBPJPY EURGBP USDMXN USDZAR".split()],
 "crypto": [s + "-USD" for s in "BTC ETH LTC XRP BNB ADA DOGE SOL LINK".split()],
 "bond": "TLT IEF SHY LQD HYG TIP".split(),
}
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
HOURLY = len(sys.argv) > 1 and sys.argv[1] == "1h"          # python3 fetch.py 1h -> the ~730 days of hourly bars Yahoo carries, into data1h/
def get(args):
    cls, sym = args
    fn = f"{'data1h' if HOURLY else 'data'}/{cls}/{sym.replace('^','_').replace('=','_')}.csv"
    if os.path.exists(fn): return sym, "cached"
    for k in range(4):
        try:
            r = S.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(sym)}",
                      params=dict(range="730d", interval="1h") if HOURLY else dict(period1=946684800, period2=int(time.time()), interval="1d", events="div,splits"), timeout=40)
            if r.status_code != 200: time.sleep(2 * (k + 1)); continue
            res = r.json()["chart"]["result"][0]; q = res["indicators"]["quote"][0]
            df = pd.DataFrame(dict(open=q["open"], high=q["high"], low=q["low"], close=q["close"], volume=q["volume"],
                 adj=q["close"] if HOURLY else res["indicators"]["adjclose"][0]["adjclose"]), index=pd.to_datetime(res["timestamp"], unit="s") if HOURLY else pd.to_datetime(res["timestamp"], unit="s").normalize())
            df = df.dropna(subset=["close"]); df = df[~df.index.duplicated()]
            os.makedirs(os.path.dirname(fn), exist_ok=True); df.to_csv(fn); return sym, len(df)
        except Exception as e: err = repr(e)[:80]; time.sleep(2 * (k + 1))
    return sym, "FAIL"
with ThreadPoolExecutor(6) as ex:
    out = list(ex.map(get, [(c, s) for c, v in U.items() for s in v]))
print([o for o in out if o[1] == "FAIL"], len(out))
