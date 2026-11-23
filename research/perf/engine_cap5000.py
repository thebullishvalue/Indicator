"""How far does calc_bars_count = 5000 move Anumaan's engine? research/anumaan.py run() on each daily instrument's
full history against its last 5,000 bars; compares the bars both runs share, at the end of the chart."""
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
import anumaan as P
from lib import load
from multiprocessing import Pool

COLS = ["sig", "qU", "qD", "E", "T"]

def one(a):
    sym, d = a
    if len(d) < 6000:
        return None
    f, c = P.run(d), P.run(d.iloc[-5000:])
    f = f.loc[c.index]
    out = dict(sym=sym, n=len(d))
    for w, tag in ((1, "last"), (250, "last250")):
        F, Cc = f.iloc[-w:], c.iloc[-w:]
        for col in COLS:
            x, y = F[col].to_numpy(float), Cc[col].to_numpy(float)
            out[f"{col}_{tag}"] = np.nanmax(np.abs(x - y) / np.abs(x)) if col != "T" and col != "E" else np.nanmax(np.abs(x - y))
        out[f"reg_{tag}"] = (F.reg.to_numpy() != Cc.reg.to_numpy()).mean()
        out[f"stops_{tag}"] = max(np.nanmax(np.abs(F.qS - Cc.qS) / F.qS) if "qS" in F else 0, 0)
    return out

if __name__ == "__main__":
    D = load("data", 1500)
    with Pool(4) as p:
        R = [r for r in p.map(one, [(s, d) for s, (_c, d) in D.items()]) if r]
    R = pd.DataFrame(R)
    print(len(R), "daily instruments with more than 6,000 bars; median history", int(R.n.median()), "bars")
    print("columns: sig/qU/qD = relative difference; E (exposure), T (trend, sigma) = absolute; reg = share of bars in a different risk regime")
    print(R.drop(columns=["sym", "n"]).describe(percentiles=[0.5, 0.9]).loc[["50%", "90%", "max"]].T.round(5).to_string())
