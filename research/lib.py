import os, glob, numpy as np, pandas as pd
CLASSES = ["us", "nse", "index", "cmdty", "fx", "bond", "crypto"]
ERAS = [("2003", "2012"), ("2013", "2019"), ("2020", "2026")]
def load():
    out = {}
    for c in CLASSES:
        for fn in sorted(glob.glob(f"data/{c}/*.csv")):
            d = pd.read_csv(fn, index_col=0, parse_dates=True)
            d = d[(d.close > 0) & (d.high >= d.low)].copy()
            k = (d.adj / d.close).where(d.adj > 0, 1.0)
            for col in ["open", "high", "low", "close"]: d[col] = d[col] * k
            d["open"] = d.open.where((d.open > 0) & (np.log(d.open / d.close).abs() < 0.3), d.close)   # missing or misprinted opens
            d = d[d.close.pct_change().abs().fillna(0) < 0.6]      # bad prints
            if len(d) > 1500: out[os.path.basename(fn)[:-4]] = (c, d)
    return out
def feats(d, sig_n=63):
    lc = np.log(d.close); r = lc.diff()
    sd = r.rolling(sig_n).std()                                    # known at the close of t
    f = pd.DataFrame(index=d.index)
    f["sd"] = sd
    for h in (3, 5, 10): f[f"S{h}"] = (lc - lc.shift(h)) / (sd * np.sqrt(h))
    f["T"] = sum((lc - lc.shift(h)) / (sd * np.sqrt(h)) for h in (63, 126, 252)) / 3
    f["T200"] = (lc - lc.rolling(200).mean()) / (sd * np.sqrt(100))
    f["V"] = r.rolling(10).std() / r.rolling(100).std()
    f["RV"] = d.volume / d.volume.rolling(50).median().replace(0, np.nan)
    f["CL"] = ((d.close - d.low) / (d.high - d.low).replace(0, np.nan)).fillna(0.5)
    lo = np.log(d.open)
    for h in (5, 10, 20):
        f[f"fc{h}"] = (lc.shift(-h) - lc) / (sd * np.sqrt(h))                 # close t -> close t+h
        f[f"fo{h}"] = (lc.shift(-h) - lo.shift(-1)) / (sd * np.sqrt(h))       # open t+1 -> close t+h
        for p in ("fc", "fo"):                                                # causal baseline: own trailing mean, realised by t
            f[f"x{p[1]}{h}"] = f[f"{p}{h}"] - f[f"{p}{h}"].shift(h + 1).rolling(1000, min_periods=250).mean()
    return f
def panel(sig_n=63):
    rows = []
    for s, (c, d) in load().items():
        f = feats(d, sig_n); f["sym"] = s; f["cls"] = c; rows.append(f)
    P = pd.concat(rows); P["date"] = P.index
    return P.dropna(subset=["T", "S5", "xo10"])
def tstat_by_date(P, col):
    """mean and t-stat with dates as the independent unit (cross-section collapsed), Newey-West over h"""
    g = P.groupby("date")[col]; m = g.mean(); n = g.size()
    x = (m * n).values; w = n.values                                # weighted by obs
    mu = x.sum() / w.sum(); e = x - mu * w
    T = len(e); h = int(col[-2:]) if col[-2:].isdigit() else int(col[-1]); v = (e * e).sum()
    for L in range(1, h + 1): v += 2 * (1 - L / (h + 1)) * (e[L:] * e[:-L]).sum()
    return mu, mu / (np.sqrt(v) / w.sum()), len(P)
