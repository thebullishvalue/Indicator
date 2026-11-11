"""Every number quoted in the README and in kasauti.pine's header.  Run:  python3 fetch.py && python3 study.py > results.txt"""
from lib import *
from kasauti import run
import warnings; warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
D = load()
def era_of(idx): return pd.cut(idx.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
print(f"UNIVERSE: {len(D)} instruments, daily bars, Yahoo.  " + ", ".join(f"{c} {sum(1 for v in D.values() if v[0] == c)}" for c in CLASSES))
# ---------- 0. the risk forecast
H = 10
def vfeat(d):
    lc, lo, lh, ll = np.log(d.close), np.log(d.open), np.log(d.high), np.log(d.low)
    r = lc.diff(); on = lo - lc.shift(1); co = lc - lo; hl = lh - ll
    gk = on ** 2 + 0.5 * hl ** 2 - (2 * np.log(2) - 1) * co ** 2          # Garman-Klass with the overnight gap
    gk = gk.where((hl > 0) & (gk > 0), r ** 2)                             # flat/absent ranges fall back to r^2
    f = pd.DataFrame(index=d.index); f["r"] = r
    f["cc20"] = r.rolling(20).var(); f["cc63"] = r.rolling(63).var()
    for n in (20, 40, 100): f[f"ew{n}"] = (r ** 2).ewm(span=n, min_periods=n).mean()
    f["gS"] = gk.ewm(span=5, min_periods=5).mean(); f["gM"] = gk.ewm(span=22, min_periods=22).mean(); f["gL"] = gk.ewm(span=252, min_periods=126).mean()
    f["rS"] = (r ** 2).ewm(span=5, min_periods=5).mean(); f["rM"] = (r ** 2).ewm(span=22, min_periods=22).mean(); f["rL"] = (r ** 2).ewm(span=252, min_periods=126).mean()
    f["rv"] = (r ** 2).rolling(H).sum().shift(-H) / H                       # realised next-H variance per bar
    f["k"] = f["rL"] / f["gL"]                                              # range estimator's bias vs close-close, learned causally
    return f
rows = []
for s, (cls, d) in D.items():
    f = vfeat(d); f["sym"] = s; f["cls"] = cls; f["date"] = f.index; rows.append(f)
P = pd.concat(rows).dropna(); P = P[P.rv > 0]
tr = P[P.date < "2013"]; te = P[P.date >= "2013"]
def fit(cols, Lc, Q):
    X = np.column_stack([Q[c] / Q[Lc] for c in cols] + [np.ones(len(Q))]); y = (Q["rv"] / Q[Lc]).clip(upper=20)
    return np.linalg.lstsq(X, y, rcond=None)[0]
bg = fit(["gS", "gM"], "gL", tr); br = fit(["rS", "rM"], "rL", tr)
print("\n0. THE RISK FORECAST\nHAR weights fitted 2001-2012 (short, medium, long):  range-based", bg.round(3), " close-close", br.round(3))
print("mean k (close-close var / range var):", P.k.median().round(3))
def qlike(f, Q): x = Q["rv"] / f; return (x - np.log(x) - 1).mean()
def r2(f, Q): return np.corrcoef(np.log(f), np.log(Q["rv"]))[0, 1] ** 2
C = {
 "cc20": lambda Q: Q.cc20, "cc63": lambda Q: Q.cc63, "ewma20": lambda Q: Q.ew20, "ewma40": lambda Q: Q.ew40, "ewma100": lambda Q: Q.ew100,
 "HAR close-close (fit)": lambda Q: br[0] * Q.rS + br[1] * Q.rM + br[2] * Q.rL,
 "HAR range (fit) x k":   lambda Q: (bg[0] * Q.gS + bg[1] * Q.gM + bg[2] * Q.gL) * Q.k,
 "HAR range .25/.40/.35 x k": lambda Q: (0.25 * Q.gS + 0.40 * Q.gM + 0.35 * Q.gL) * Q.k,
 "HAR range .3/.4/.3 x k": lambda Q: (0.3 * Q.gS + 0.4 * Q.gM + 0.3 * Q.gL) * Q.k,
}
print("\nOUT OF SAMPLE 2013-2026, forecasting the next 10 bars' realised variance")
out = {k: dict(QLIKE=qlike(f(te), te), R2log=r2(f(te), te), bias=(te.rv / f(te)).mean()) for k, f in C.items()}
print(pd.DataFrame(out).T.round(3).to_string())
print("\nQLIKE by class (OOS)"); print(pd.DataFrame({k: te.groupby("cls").apply(lambda Q: qlike(f(Q), Q)) for k, f in C.items()}).T[CLASSES].round(3).to_string())

# ---------- 1. calibration: conformal vs fixed Gaussian --------------------------------------------------------------
rows = []
for s, (cls, d) in D.items():
    for nm, kw in (("kasauti (per regime)", {}), ("one multiplier", dict(regimes=False)), ("fixed gaussian", dict(conformal=False))):
        R = run(d, **kw); R = R[R.nF == 1]; R["era"] = era_of(R.index)
        for e, Q in R.groupby("era", observed=True):
            if len(Q) > 300: rows.append(dict(sym=s, cls=cls, kind=nm, era=e, cover=1 - Q.mU.mean() - Q.mD.mean(), up=Q.mU.mean(), dn=Q.mD.mean(), stopL=Q.mS.mean(), stopS=Q.mR.mean()))
C = pd.DataFrame(rows)
print("\n1. CALIBRATION  target: cone 80% (10% each tail), stop touched 20%   [mean across instruments]")
print(C.groupby("kind")[["cover", "up", "dn", "stopL", "stopS"]].mean().round(3).to_string())
print("\nworst-case: share of instrument-eras whose realised cone coverage is within 3 points of 80%, and stop within 3 of 20%")
print(C.assign(ok=(C.cover - .8).abs() < .03, okS=(C.stopL - .2).abs() < .03).groupby("kind")[["ok", "okS"]].mean().round(3).to_string())
print("\ncone coverage by class and era"); print(C.pivot_table(index=["kind", "cls"], columns="era", values="cover").round(3).to_string())
print("\nlong-stop touch rate by class and era"); print(C.pivot_table(index=["kind", "cls"], columns="era", values="stopL").round(3).to_string())
print("\nspread across instruments (std of realised coverage):"); print(C.groupby("kind")[["cover", "stopL"]].std().round(3).to_string())

rows = []; rows2 = []
for s, (cls, d) in D.items():
    REG = run(d).reg                                                                   # the regime at forecast time, the same for every variant
    for nm, kw in (("fixed gaussian", dict(conformal=False)), ("one multiplier", dict(regimes=False)), ("kasauti (per regime)", {}), ("per regime eta .01", dict(eta=.01)), ("per regime eta .05", dict(eta=.05))):
        R = run(d, **kw); Q = R[R.nF == 1].copy(); Q["rg"] = REG.shift(10).reindex(Q.index); Q["era"] = pd.cut(Q.index.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
        for rg, q in Q.groupby("rg"): rows.append(dict(sym=s, kind=nm, reg=["calm", "normal", "stressed"][int(rg)], cover=1 - q.mU.mean() - q.mD.mean(), stopL=q.mS.mean(), stopS=q.mR.mean()))
        for e, q in Q.groupby("era", observed=True):
            if len(q) > 300: rows2.append(dict(sym=s, kind=nm, cover=1 - q.mU.mean() - q.mD.mean(), stopL=q.mS.mean(), w=np.log(R.upper / R.lower).reindex(q.index).mean()))
A = pd.DataFrame(rows); B = pd.DataFrame(rows2)
print("\n1b. coverage by risk regime at forecast time"); print(A.pivot_table(index="kind", columns="reg", values=["cover", "stopL"]).round(3).to_string())
print("\ninstrument-eras within 3 points of target, and mean cone width (log)"); print(B.assign(ok=(B.cover - .8).abs() < .03, okS=(B.stopL - .2).abs() < .03).groupby("kind")[["ok", "okS", "cover", "stopL", "w"]].mean().round(3).to_string())

rows = []; atr_rows = []
for s, (cls, d) in D.items():
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1); atr = tr.ewm(alpha=1 / 14, adjust=False).mean()
    lowH = d.low.rolling(10).min()
    for m in (1.5, 2.0, 3.0): atr_rows.append(dict(sym=s, cls=cls, m=m, touch=(lowH < (d.close - m * atr).shift(10)).iloc[300:].mean()))
A = pd.DataFrame(atr_rows)
print("\nthe usual alternative - a k x ATR(14) stop: share of the time it is touched within 10 bars")
print(A.groupby("m")["touch"].agg(["mean", "std", "min", "max"]).round(3).to_string()); print(A[A.m == 2].groupby("cls")["touch"].mean().round(3).to_string())

def stats(p):
    p = p.dropna()
    if len(p) < 500 or p.std() == 0: return None
    eq = (1 + p).cumprod(); dd = (eq / eq.cummax() - 1).min(); cg = eq.iloc[-1] ** (252 / len(p)) - 1
    return dict(sh=p.mean() / p.std() * np.sqrt(252), cagr=cg, vol=p.std() * np.sqrt(252), dd=dd, calmar=cg / -dd)
# ---------- 2. exposure ----------------------------------------------------------------------------------------------
rows = []
V = {"risk dial, cap 1.0": dict(cap=1.0, floor=1.0), "risk dial, cap 1.5": dict(cap=1.5, floor=1.0), "risk dial, cap 2.0": dict(cap=2.0, floor=1.0),
     "risk x trend, floor .5": dict(cap=1.0, floor=0.5), "risk x trend, floor .25": dict(cap=1.0, floor=0.25), "risk x trend, floor 0": dict(cap=1.0, floor=0.0)}
for s, (cls, d) in D.items():
    for nm, kw in V.items():
        R = run(d, cost=0.001 if cls == "crypto" else 0.0005, **kw)
        for a, b in [("2003", "2026")] + ERAS:
            f, hd = stats(R.pf[a:b]), stats(R.ph[a:b])
            if f and hd: rows.append(dict(sym=s, cls=cls, v=nm, era=a[2:] + "-" + b[2:], expo=R.E[a:b].mean(), **{k: f[k] for k in f}, **{"h_" + k: hd[k] for k in hd}))
X = pd.DataFrame(rows); X.to_pickle("X.pkl"); A = X[X.era == "03-26"]; order = list(V)
print("\n2. EXPOSURE DIAL vs BUY AND HOLD   full sample, mean across 151 instruments, net of costs, one-bar delay")
g = A.groupby("v"); t = g[["expo", "sh", "h_sh", "cagr", "h_cagr", "vol", "h_vol", "dd", "h_dd", "calmar", "h_calmar"]].mean()
t["sh>hold"] = g.apply(lambda q: (q.sh > q.h_sh).mean()); t["dd<hold"] = g.apply(lambda q: (q.dd > q.h_dd).mean()); t["calmar>hold"] = g.apply(lambda q: (q.calmar > q.h_calmar).mean())
print(t.reindex(order).round(3).to_string())
E = X[X.era != "03-26"]; g = E.groupby(["v", "era"])
print("\nby era: Sharpe followed / hold, maxDD followed / hold, share of instruments with shallower DD and with higher Sharpe")
print(pd.DataFrame(dict(sh=g.sh.mean(), h_sh=g.h_sh.mean(), dd=g.dd.mean(), h_dd=g.h_dd.mean(), dd_win=g.apply(lambda q: (q.dd > q.h_dd).mean()), sh_win=g.apply(lambda q: (q.sh > q.h_sh).mean()))).round(3).loc[order].to_string())
g = A.groupby(["v", "cls"])
print("\nby class (full sample)"); print(pd.DataFrame(dict(sh=g.sh.mean(), h_sh=g.h_sh.mean(), dd=g.dd.mean(), h_dd=g.h_dd.mean(), sh_win=g.apply(lambda q: (q.sh > q.h_sh).mean()))).round(2).loc[["risk dial, cap 1.0", "risk x trend, floor .5"]].to_string())

# ---------- 3, 4. the states and the ledger
rows = []; NAMES = [f"{t} · {c}" for t in ("down", "flat", "up") for c in ("broke down", "inside", "broke up")]
for s, (cls, d) in D.items():
    R = run(d); R["yf"] = R.y.shift(-10); R["sym"] = s; R["cls"] = cls; R["date"] = R.index; rows.append(R[R.st >= 0])
P = pd.concat(rows).dropna(subset=["yf"]); P["era"] = pd.cut(P.date.dt.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
P["grp"] = np.where(P.cls.isin(["us", "nse", "index"]), "equity", np.where(P.cls == "crypto", "crypto", "macro"))
def tdate(q):
    g = q.groupby("date")["d"]; m, n = g.mean(), g.size(); x = (m * n).values; mu = x.sum() / n.sum(); e = x - mu * n.values; v = (e * e).sum()
    for L in range(1, 11): v += 2 * (1 - L / 11) * (e[L:] * e[:-L]).sum()
    return mu / (np.sqrt(v) / n.sum())
P["d"] = P.yf - P.groupby(["grp", "era"], observed=True)["yf"].transform("mean")            # vs the group's own mean that era: a constant, not a trailing mean
print("\n3. THE NINE STATES, pooled: next-10-bar return in sigma, minus the group mean of that era (x100)   [share of bars, t clustered by date]")
T = P[P.grp != "crypto"].groupby("st").apply(lambda q: pd.Series(dict(share=len(q) / len(P[P.grp != "crypto"]), all=q.d.mean() * 100, t=tdate(q), **{e: q[q.era == e].d.mean() * 100 for e in ("03-12", "13-19", "20-26")})))
T.index = [NAMES[i] for i in T.index]; print(T.round(2).to_string())
print("\ncrypto"); T = P[P.grp == "crypto"].groupby("st").apply(lambda q: pd.Series(dict(all=q.d.mean() * 100, t=tdate(q), n=len(q)))); T.index = [NAMES[i] for i in T.index]; print(T.round(2).to_string())
# the ledger's own verdict, out of sample: once a state reads PROVEN on a chart (|z| >= 2 after shrinkage), what did the NEXT entries into it do?
P["proven"] = np.where(P.zpost >= 2, 1, np.where(P.zpost <= -2, -1, 0)); P["entry"] = P.groupby("sym")["st"].diff().fillna(1) != 0
E = P[P.entry]
print("\n4. THE LEDGER, OUT OF SAMPLE. Entries into a state the chart's own history had already 'proven' - what the next 10 bars did (sigma x100: raw, and against the group's mean)")
print(E.groupby("proven").apply(lambda q: pd.Series(dict(n=len(q), instruments=q.sym.nunique(), raw=q.yf.mean() * 100, vs_group=q.d.mean() * 100, hit=(q.yf > 0).mean()))).round(2).to_string())
print("by era"); print(E.groupby(["proven", "era"], observed=True)["yf"].agg(["mean", "size"]).assign(mean=lambda x: x["mean"] * 100).round(2).to_string())
print("\nshare of bars on which the current state reads proven:", (P.proven != 0).mean().round(4), " +:", (P.proven == 1).mean().round(4), " -:", (P.proven == -1).mean().round(4))
print("random-walk control (should be ~4.6% by chance at |z|>=2 without shrinkage, far less with):")
rng = np.random.default_rng(1); k = 0; nb = 0
for i in range(40):
    n = 6000; r = rng.standard_t(4, n) * 0.01 * np.exp(0.5 * np.sin(np.arange(n) / 200) + np.cumsum(rng.standard_normal(n)) * 0.02)
    c = np.exp(np.cumsum(r)); o = np.r_[c[0], c[:-1]]; d = pd.DataFrame(dict(open=o, high=np.maximum(o, c) * 1.002, low=np.minimum(o, c) * 0.998, close=c))
    R = run(d); k += (R.zpost.abs() >= 2).sum(); nb += (R.st >= 0).sum()
print(" proven share on random walks:", round(k / nb, 4))
