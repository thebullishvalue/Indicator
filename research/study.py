"""Every number quoted in the README and in pragyam.pine's header.  Run:  python3 fetch.py && python3 study.py > results.txt"""
from lib import *
from pragyam import run
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
    for nm, kw in (("pragyam (regime + trend)", {}), ("regime only", dict(trendf=False)), ("one width", dict(regimes=False, trendf=False)), ("fixed normal", dict(conformal=False))):
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
    REG = run(d, trendf=False).reg                                                                   # the regime at forecast time, the same for every variant
    for nm, kw in (("fixed normal", dict(conformal=False)), ("one width", dict(regimes=False, trendf=False)), ("regime only", dict(trendf=False)), ("pragyam (regime + trend)", {}), ("pragyam, eta .01", dict(eta=.01)), ("pragyam, eta .05", dict(eta=.05))):
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

# ---------- 5-9. the tapes, other settings, other timeframes, the dial's shape
H = 10
def stats2(p):
    p = p.dropna()
    if len(p) < 500 or p.std() == 0: return None
    eq = (1 + p).cumprod(); dd = (eq / eq.cummax() - 1).min()
    return dict(sh=p.mean() / p.std(), dd=dd)
rows = []
for s, (cls, d) in D.items():
    R = run(d); lc = np.log(d.close)
    R["dsig"] = np.log(R.sig.shift(-H) / R.sig)                          # what risk did over the next H bars
    R["m_sl"] = R.slope; R["m_chg"] = np.log(R.sig / R.sig.shift(H))
    R["z1"] = ((lc.shift(-1) - lc) / R.sig).clip(-8, 8)                                # next bar's return per unit of forecast risk
    for c in ("mU", "mD", "mS", "mR", "nF"): R["f_" + c] = R[c].shift(-H)  # the fate of the forecast made on this bar
    R["yf"] = R.y.shift(-H)
    R["sym"] = s; R["cls"] = cls; R["date"] = R.index; rows.append(R[R.sig.notna()])
P = pd.concat(rows); P["era"] = pd.cut(P.date.dt.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
P["grp"] = np.where(P.cls.isin(["us", "nse", "index"]), "equity", np.where(P.cls == "crypto", "crypto", "macro"))
P["regime"] = pd.Categorical.from_codes(np.where(P.prk.isna(), 1, np.where(P.prk < 100 / 3, 0, np.where(P.prk < 200 / 3, 1, 2))), ["calm", "normal", "stressed"])
P = P[P.prk.notna()]
print("\n5. THE TAPES\n5a. RISK TAPE. What forecast risk did over the next 10 bars (median log change x100), by regime")
print(P.groupby("regime", observed=True)["dsig"].median().mul(100).round(1).to_string())
print("\nrisk momentum candidates - median next-10-bar log change in risk x100, by regime (rows) and momentum tercile within regime (cols)")
for m, nm in (("m_sl", "short over long (0.5 ln vS/vL)"), ("m_chg", "change over the last 10 bars (ln sig/sig[10])")):
    P["mb"] = P.groupby("regime", observed=True)[m].transform(lambda x: pd.qcut(x, 3, labels=["low", "mid", "high"]))
    print(nm); print(P.groupby(["regime", "mb"], observed=True)["dsig"].median().unstack().mul(100).round(1).to_string())
    print("   share of bars on which risk was HIGHER 10 bars later:"); print(P.groupby(["regime", "mb"], observed=True)["dsig"].apply(lambda x: (x > 0).mean()).unstack().round(2).to_string())
print("\nfixed cut on the 10-bar change: falling < -0.10 | steady | rising > +0.10   share of bars, median next change x100, share higher")
P["rm"] = pd.cut(P.m_chg, [-9, -0.10, 0.10, 9], labels=["falling", "steady", "rising"])
print(P.groupby("rm", observed=True)["dsig"].agg(share=lambda x: len(x) / len(P), med=lambda x: x.median() * 100, higher=lambda x: (x > 0).mean()).round(2).to_string())
print("by era (median next change x100)"); print(P.groupby(["era", "rm"], observed=True)["dsig"].median().unstack().mul(100).round(1).to_string())
print("\n5b. RETURN PER UNIT OF RISK (next bar, sigma x100) by risk regime - does the reward for risk fall when risk is high?")
print(P.groupby(["grp", "regime"], observed=True)["z1"].mean().unstack().mul(100).round(2).to_string())
print("by era, ex crypto"); print(P[P.grp != "crypto"].groupby(["era", "regime"], observed=True)["z1"].mean().unstack().mul(100).round(2).to_string())
print("by risk momentum, ex crypto"); print(P[P.grp != "crypto"].groupby(["era", "rm"], observed=True)["z1"].mean().unstack().mul(100).round(2).to_string())
print("\n5c. STRETCH LADDER. Rungs 5, 10, 20, 40 bars, each with its own learned 80% cone. Share of bars by number of rungs outside:")
L = P[P.ladX.notna()].copy(); L["up"] = L.ladUp.astype(int); L["dn"] = L.ladDn.astype(int)
print(pd.DataFrame(dict(above=L.up.value_counts(normalize=True).sort_index(), below=L.dn.value_counts(normalize=True).sort_index())).round(3).T.to_string())
L["state"] = np.where(L.up >= 3, "3-4 above", np.where(L.dn >= 3, "3-4 below", np.where(L.up >= 1, "1-2 above", np.where(L.dn >= 1, "1-2 below", "inside"))))
Q = L[L.f_nF == 1]
print("the cone drawn on such a bar - did it still hold? (target 80 / 10 / 10; long stop 20)")
print(Q.groupby("state").apply(lambda q: pd.Series(dict(share=len(q) / len(Q), held=1 - q.f_mU.mean() - q.f_mD.mean(), above=q.f_mU.mean(), below=q.f_mD.mean(), long_stop=q.f_mS.mean(), short_stop=q.f_mR.mean()))).round(3).to_string())
Q = L[L.yf.notna() & (L.grp != "crypto")].copy(); Q["d"] = Q.yf - Q.groupby(["grp", "era"], observed=True)["yf"].transform("mean")
print("next 10 bars' return in sigma x100, against the group mean of the era (ex crypto)"); print(Q.groupby(["state", "era"], observed=True)["d"].mean().unstack().mul(100).round(1).to_string())
print("\n5d. TREND TAPE. The cone drawn in each trend state - did it hold? (target 80 / 10 / 10)")
Q = P[P.f_nF == 1].copy(); Q["trend"] = pd.cut(Q["T"], [-99, -0.5, 0.5, 99], labels=["down", "flat", "up"])
print(Q.groupby("trend", observed=True).apply(lambda q: pd.Series(dict(share=len(q) / len(Q), held=1 - q.f_mU.mean() - q.f_mD.mean(), above=q.f_mU.mean(), below=q.f_mD.mean(), long_stop=q.f_mS.mean(), short_stop=q.f_mR.mean()))).round(3).to_string())
# ---------- 6. other settings -----------------------------------------------------------------------------------------
print("\n6. OTHER SETTINGS. Realised against target, mean across instruments, and share of instruments within 3 points")
rows = []
for nm, kw in (("H 5", dict(H=5)), ("H 20", dict(H=20)), ("H 40", dict(H=40)), ("cone 50%", dict(cover=.5)), ("cone 90%", dict(cover=.9)), ("stop 10%", dict(pstop=.1)), ("stop 30%", dict(pstop=.3))):
    for s, (cls, d) in D.items():
        R = run(d, **kw); Q = R[R.nF == 1]
        rows.append(dict(setting=nm, cover=1 - Q.mU.mean() - Q.mD.mean(), stop=Q.mS.mean(), tc=kw.get("cover", .8), ts=kw.get("pstop", .2)))
A = pd.DataFrame(rows); print(A.groupby("setting", sort=False).apply(lambda q: pd.Series(dict(cone_target=q.tc.iloc[0], cone=q.cover.mean(), cone_ok=((q.cover - q.tc).abs() < .03).mean(), stop_target=q.ts.iloc[0], stop=q.stop.mean(), stop_ok=((q.stop - q.ts).abs() < .03).mean()))).round(3).to_string())
# ---------- 7, 8. other timeframes ------------------------------------------------------------------------------------
def tf_block(DD, title, ann):
    rows = []
    for s, (cls, d) in DD.items():
        R = run(d, cost=0.001 if cls == "crypto" else 0.0005); G = run(d, conformal=False); Q = R[R.nF == 1]; QG = G[G.nF == 1]
        if len(Q) < 300: continue
        f, hd = stats2(R.pf), stats2(R.ph); fr = stats2(run(d, cost=0.001 if cls == "crypto" else 0.0005, floor=1.0).pf)
        rows.append(dict(cls=cls, n=len(Q), cover=1 - Q.mU.mean() - Q.mD.mean(), stop=Q.mS.mean(), g_cover=1 - QG.mU.mean() - QG.mD.mean(), g_stop=QG.mS.mean(),
                         sh=f["sh"] * np.sqrt(ann) if f else np.nan, r_sh=fr["sh"] * np.sqrt(ann) if fr else np.nan, r_dd=fr["dd"] if fr else np.nan, h_sh=hd["sh"] * np.sqrt(ann) if hd else np.nan, dd=f["dd"] if f else np.nan, h_dd=hd["dd"] if hd else np.nan))
    A = pd.DataFrame(rows); print(f"\n{title}: {len(A)} instruments, {int(A.n.median())} settled forecasts each (median)")
    print(pd.Series(dict(cone=A.cover.mean(), cone_within3=((A.cover - .8).abs() < .03).mean(), stop=A['stop'].mean(), stop_within3=((A['stop'] - .2).abs() < .03).mean(),
                         normal_cone=A.g_cover.mean(), normal_cone_within3=((A.g_cover - .8).abs() < .03).mean(), normal_stop=A.g_stop.mean(), normal_stop_within3=((A.g_stop - .2).abs() < .03).mean())).round(3).to_string())
    print("dial against hold:", pd.Series(dict(sharpe=A.sh.mean(), risk_only_sharpe=A.r_sh.mean(), hold_sharpe=A.h_sh.mean(), dd=A.dd.mean(), risk_only_dd=A.r_dd.mean(), hold_dd=A.h_dd.mean(), dd_shallower=(A.dd > A.h_dd).mean(), sharpe_higher=(A.sh > A.h_sh).mean(), risk_only_sharpe_higher=(A.r_sh > A.h_sh).mean())).round(3).to_dict())
    print(A.groupby("cls")[["cover", "stop", "g_cover", "g_stop"]].mean().round(3).reindex([c for c in CLASSES if c in set(A.cls)]).to_string())
WK = {s: (c, d.resample("W-FRI").agg(dict(open="first", high="max", low="min", close="last", volume="sum", adj="last")).dropna()) for s, (c, d) in D.items()}
tf_block({s: v for s, v in WK.items() if len(v[1]) > 600}, "7. WEEKLY BARS (resampled)", 52)
tf_block(load("data1h", 2500), "8. HOURLY BARS (about two years)", 252 * 7)
# ---------- 9. the dial's shape ---------------------------------------------------------------------------------------
print("\n9. THE DIAL'S SHAPE. exposure = min(cap, (average risk / risk now)^power) x trend throttle")
rows = []
for nm, kw in (("power 1, no throttle", dict(floor=1.0)), ("power 2, no throttle", dict(floor=1.0, power=2.0)), ("power 1, floor .5", {}), ("power 1.5, floor .5", dict(power=1.5)), ("power 2, floor .5", dict(power=2.0))):
    for s, (cls, d) in D.items():
        R = run(d, cost=0.001 if cls == "crypto" else 0.0005, **kw)
        for a, b in [("2003", "2026")] + ERAS:
            f, hd = stats2(R.pf[a:b]), stats2(R.ph[a:b])
            if f and hd: rows.append(dict(v=nm, era=a[2:] + "-" + b[2:], expo=R.E[a:b].mean(), sh=f["sh"] * np.sqrt(252), h_sh=hd["sh"] * np.sqrt(252), dd=f["dd"], h_dd=hd["dd"]))
X = pd.DataFrame(rows); g = X.groupby(["v", "era"], sort=False)
print(pd.DataFrame(dict(expo=g.expo.mean(), sh=g.sh.mean(), h_sh=g.h_sh.mean(), dd=g.dd.mean(), h_dd=g.h_dd.mean(), sh_win=g.apply(lambda q: (q.sh > q.h_sh).mean()), dd_win=g.apply(lambda q: (q.dd > q.h_dd).mean()))).round(3).to_string())

# ---------- 10, 11. what the cone listens to; the dial's step
V = {"regime only": dict(trendf=False), "regime + trend": {}, "regime + trend + ladder": dict(ladf=True)}
BASE = {s: run(d, trendf=False) for s, (c, d) in D.items()}                 # common conditioning states for every variant
rows = []; era_rows = []
for nm, kw in V.items():
    for s, (cls, d) in D.items():
        R = run(d, **kw); B = BASE[s]
        Q = pd.DataFrame(dict(mU=R.mU.shift(-H), mD=R.mD.shift(-H), mS=R.mS.shift(-H), mR=R.mR.shift(-H), ok=R.nF.shift(-H), w=np.log(R.upper / R.lower), ws=np.log(R.stopS / R.stopL),
                              regime=B.reg, T=B["T"], up=B.ladUp, dn=B.ladDn, chg=np.log(B.sig / B.sig.shift(H)), prk=B.prk), index=R.index)
        Q = Q[(Q.ok == 1) & Q.prk.notna()]; Q["v"] = nm; Q["sym"] = s; rows.append(Q)
        Q2 = R[R.nF == 1].copy(); Q2["era"] = pd.cut(Q2.index.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
        for e, q in Q2.groupby("era", observed=True):
            if len(q) > 300: era_rows.append(dict(v=nm, cover=1 - q.mU.mean() - q.mD.mean(), stop=q.mS.mean(), stopS=q.mR.mean()))
P = pd.concat(rows)
P["trend"] = pd.cut(P["T"], [-99, -0.5, 0.5, 99], labels=["down", "flat", "up"]); P["reg"] = P.regime.map({0: "calm", 1: "normal", 2: "stressed"})
P["lad"] = np.where(P.up >= 3, "3-4 above", np.where(P.dn >= 3, "3-4 below", "other")); P["rm"] = pd.cut(P.chg, [-9, -0.10, 0.10, 9], labels=["falling", "steady", "rising"])
def tab(key):
    g = P.groupby(["v", key], observed=True, sort=False)
    return pd.DataFrame(dict(held=1 - g.mU.mean() - g.mD.mean(), above=g.mU.mean(), below=g.mD.mean(), long_stop=g.mS.mean(), short_stop=g.mR.mean())).round(3)
E = pd.DataFrame(era_rows)
print("10. WHAT THE CONE LISTENS TO. target: held 80, above 10, below 10, stops 20")
print("overall: instrument-eras within 3 points, and mean widths (log)")
print(pd.concat([E.assign(ok=(E.cover - .8).abs() < .03, okL=(E['stop'] - .2).abs() < .03, okS=(E.stopS - .2).abs() < .03).groupby("v", sort=False)[["ok", "okL", "okS"]].mean(), P.groupby("v", sort=False)[["w", "ws"]].mean()], axis=1).round(3).to_string())
for k, t in (("trend", "by TREND state when the cone was drawn"), ("reg", "by RISK regime"), ("lad", "by STRETCH ladder state"), ("rm", "by RISK MOMENTUM")):
    print("\n" + t); print(tab(k).to_string())
# ---------- the dial's step ----------
def stats3(p, ann):
    p = p.dropna()
    if len(p) < 500 or p.std() == 0: return None
    eq = (1 + p).cumprod(); return dict(sh=p.mean() / p.std() * np.sqrt(ann), dd=(eq / eq.cummax() - 1).min())
print("\n11. THE DIAL'S STEP. Act only when the dial has moved by this much. Turnover is the sum of position changes per year.")
H1 = load("data1h", 2500); WK = {s: (c, d.resample("W-FRI").agg(dict(open="first", high="max", low="min", close="last", volume="sum", adj="last")).dropna()) for s, (c, d) in D.items()}; WK = {s: v for s, v in WK.items() if len(v[1]) > 600}
for title, DD, ann in (("daily", D, 252), ("weekly", WK, 52), ("hourly", H1, 252 * 7)):
    rows = []
    for b in (0.0, 0.05, 0.10, 0.20):
        for s, (cls, d) in DD.items():
            R = run(d, cost=0.001 if cls == "crypto" else 0.0005, band=b); f, hd = stats3(R.pf, ann), stats3(R.ph, ann)
            if f and hd: rows.append(dict(step=b, sh=f["sh"], h_sh=hd["sh"], dd=f["dd"], h_dd=hd["dd"], turn=R.E.diff().abs().mean() * ann))
    A = pd.DataFrame(rows); g = A.groupby("step")
    print(title); print(pd.DataFrame(dict(sharpe=g.sh.mean(), hold=g.h_sh.mean(), dd=g.dd.mean(), hold_dd=g.h_dd.mean(), turnover=g.turn.mean(), sh_win=g.apply(lambda q: (q.sh > q.h_sh).mean()), dd_win=g.apply(lambda q: (q.dd > q.h_dd).mean()))).round(3).to_string())
