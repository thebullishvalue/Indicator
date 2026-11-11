"""The search that came back empty: no price or volume state led the next bars in all three eras.  python3 direction_null.py > direction_null.txt"""
from lib import *
import warnings; warnings.filterwarnings("ignore")
D = load()
def prep(d, sig_n=63):
    lc = np.log(d.close); lo = np.log(d.open); r = lc.diff()
    sd = r.rolling(sig_n).std()
    f = pd.DataFrame(index=d.index)
    f["sd"] = sd; f["r"] = r
    f["S5"] = (lc - lc.shift(5)) / (sd * np.sqrt(5)); f["S3"] = (lc - lc.shift(3)) / (sd * np.sqrt(3)); f["S10"] = (lc - lc.shift(10)) / (sd * np.sqrt(10))
    f["T"] = sum((lc - lc.shift(h)) / (sd * np.sqrt(h)) for h in (63, 126, 252)) / 3
    f["T252"] = (lc - lc.shift(252)) / (sd * np.sqrt(252))
    f["M200"] = lc - lc.rolling(200).mean()
    f["V"] = r.rolling(10).std() / r.rolling(100).std()
    f["HI"] = lc - lc.rolling(252).max()                         # distance below 52w high (<=0), log
    f["HIz"] = f["HI"] / (sd * np.sqrt(63))
    # next-bar return per unit of risk known at t: open t+1 -> open t+2 (decide at close t, trade next open)
    f["zo"] = (lo.shift(-2) - lo.shift(-1)) / sd
    f["zc"] = (lc.shift(-1) - lc) / sd                           # close t -> close t+1
    return f
F = {s: (c, prep(d)) for s, (c, d) in D.items()}
def score(rule, ret="zo", cost=0.0, years=None):
    """per-instrument annualised Sharpe of pos*z, mean by class; cost in sd-units per unit turnover"""
    rows = []
    for s, (c, f) in F.items():
        pos = rule(f).reindex(f.index)
        pnl = (pos * f[ret] - cost * pos.diff().abs().fillna(0)).dropna()
        if years: pnl = pnl[years[0]:years[1]]
        if len(pnl) < 500 or pnl.std() == 0: continue
        rows.append((c, s, pnl.mean() / pnl.std() * np.sqrt(252), pnl.mean() * 252, (pos.loc[pnl.index] != 0).mean()))
    R = pd.DataFrame(rows, columns=["cls", "sym", "sh", "mu", "inmkt"])
    return R
rules = {
 "hold":            lambda f: pd.Series(1.0, f.index).where(f["T"].notna()),
 "T>0 long/flat":   lambda f: (f["T"] > 0).astype(float).where(f["T"].notna()),
 "T long/short":    lambda f: np.sign(f["T"]),
 "M200 long/flat":  lambda f: (f["M200"] > 0).astype(float).where(f["T"].notna()),
 "S5<-1 long":      lambda f: (f["S5"] < -1).astype(float).where(f["T"].notna()),
 "S5<-1 & T>0":     lambda f: ((f["S5"] < -1) & (f["T"] > 0)).astype(float).where(f["T"].notna()),
 "S5<-1 & T<0":     lambda f: ((f["S5"] < -1) & (f["T"] < 0)).astype(float).where(f["T"].notna()),
 "S5>1 & T<0":      lambda f: ((f["S5"] > 1) & (f["T"] < 0)).astype(float).where(f["T"].notna()),
 "S5>1 & T>0":      lambda f: ((f["S5"] > 1) & (f["T"] > 0)).astype(float).where(f["T"].notna()),
 "-S5 linear":      lambda f: (-f["S5"]).clip(-2, 2) / 2,
 "nearHI(>-1)":     lambda f: (f["HIz"] > -1).astype(float).where(f["T"].notna()),
 "V<1 hold":        lambda f: (f["V"] < 1).astype(float).where(f["T"].notna()),
}
pd.set_option("display.width", 250)
for ret in ("zc", "zo"):
    tab = {}
    for k, rule in rules.items():
        R = score(rule, ret); g = R.groupby("cls")["sh"].mean().reindex(CLASSES); g["ALL"] = R.sh.mean(); g["inmkt"] = R.inmkt.mean(); tab[k] = g
    print(f"\nA. SIMPLE RULES AS POSITIONS. mean per-instrument Sharpe in sigma units; zc = close to close, zo = next open to the open after. return={ret}"); print(pd.DataFrame(tab).T.round(2).to_string())
print("\nby era (zo, ex-crypto) ")
tab = {}
for k, rule in rules.items():
    tab[k] = pd.Series({f"{a}-{b}": (lambda R: R[R.cls != "crypto"].sh.mean())(score(rule, "zo", years=(a, b))) for a, b in ERAS})
print(pd.DataFrame(tab).T.round(2).to_string())

P = pd.concat([f.assign(sym=s, cls=c, date=f.index) for s, (c, f) in F.items()]).dropna(subset=["T", "S5", "zo", "V"])
P["era"] = pd.cut(P.date.dt.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
P["grp"] = np.where(P.cls.isin(["us", "nse", "index"]), "equity", np.where(P.cls == "crypto", "crypto", "macro"))
def dens(Q, col="zo"):
    g = Q.groupby("date")[col]; m, n = g.mean(), g.size(); x = (m * n).values
    mu = x.sum() / n.sum(); e = x - mu * n.values
    return pd.Series(dict(mu=100 * mu, t=mu / (np.sqrt((e * e).sum() + 2 * (e[1:] * e[:-1]).sum()) / n.sum()), n=len(Q)))
pd.set_option("display.width", 250)
P["tb"] = pd.cut(P["T"], [-99, -1, 0, 1, 99], labels=["T<<", "T<", "T>", "T>>"])
P["sb"] = pd.cut(P["S5"], [-99, -2, -1, 0, 1, 2, 99], labels=["S<-2", "-2..-1", "-1..0", "0..1", "1..2", "S>2"])
P["vb"] = pd.cut(P["V"], [0, 0.8, 1.25, 99], labels=["calm", "norm", "stress"])
print("\nB. NEXT-BAR RETURN BY TREND x 5-BAR STRETCH\nunconditional density (mean next-day z x100) by grp:"); print(P.groupby("grp").apply(dens).round(2))
for g in ("equity", "macro", "crypto"):
    Q = P[P.grp == g]
    print(f"\n=== {g}: mean next-day z x100 (open->open), T rows x S5 cols"); print(Q.groupby(["tb", "sb"], observed=True)["zo"].mean().unstack().mul(100).round(1).to_string())
    print("t (date-clustered)"); print(Q.groupby(["tb", "sb"], observed=True).apply(lambda q: dens(q)["t"]).unstack().round(1).to_string())
    if g != "crypto":
        for e in ("03-12", "13-19", "20-26"):
            print(f"era {e}"); print(Q[Q.era == e].groupby(["tb", "sb"], observed=True)["zo"].mean().unstack().mul(100).round(1).to_string())
print("\n=== equity, stress split: S5 cols by V rows (T>0 only / T<0 only)")
for nm, Q in (("T>0", P[(P.grp == "equity") & (P["T"] > 0)]), ("T<0", P[(P.grp == "equity") & (P["T"] < 0)])):
    print(nm); print(Q.groupby(["vb", "sb"], observed=True)["zo"].mean().unstack().mul(100).round(1).to_string())

rows = []
for s, (cls, d) in D.items():
    lc, lo = np.log(d.close), np.log(d.open); r = lc.diff(); sd = r.rolling(63).std()
    on = lo - lc.shift(1); idr = lc - lo
    f = pd.DataFrame(index=d.index)
    for k in (21, 63):
        f[f"ON{k}"] = on.rolling(k).sum() / (sd * np.sqrt(k)); f[f"ID{k}"] = idr.rolling(k).sum() / (sd * np.sqrt(k))
    f["T"] = sum((lc - lc.shift(h)) / (sd * np.sqrt(h)) for h in (63, 126, 252)) / 3
    f["S5"] = (lc - lc.shift(5)) / (sd * np.sqrt(5))
    med = d.volume.rolling(50).median().replace(0, np.nan)
    f["RV1"] = np.log(d.volume.replace(0, np.nan) / med); f["RV5"] = np.log(d.volume.rolling(5).mean() / med)
    f["V"] = r.rolling(10).std() / r.rolling(100).std()
    f["CL5"] = (((d.close - d.low) / (d.high - d.low).replace(0, np.nan)).fillna(.5)).rolling(5).mean()
    f["ER"] = (lc - lc.shift(20)).abs() / r.abs().rolling(20).sum()            # efficiency ratio
    f["zo"] = (lo.shift(-2) - lo.shift(-1)) / sd
    f["f10"] = (lc.shift(-10) - lo.shift(-1)) / (sd * np.sqrt(10)); f["f20"] = (lc.shift(-20) - lo.shift(-1)) / (sd * np.sqrt(20))
    f["sym"] = s; f["cls"] = cls; f["date"] = f.index; rows.append(f)
print('\nC. OTHER FEATURES: overnight vs session drift, relative volume, close location, efficiency, risk ratio')
P = pd.concat(rows).dropna(subset=["T", "f20"])
P["era"] = pd.cut(P.date.dt.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
P["grp"] = np.where(P.cls.isin(["us", "nse"]), "stocks", np.where(P.cls == "index", "index", np.where(P.cls == "crypto", "crypto", "macro")))
pd.set_option("display.width", 250)
def q5(P, feat, tgt="f10"):
    Q = P.dropna(subset=[feat]).copy(); Q["q"] = pd.cut(Q[feat], [-np.inf] + list(np.nanquantile(Q[feat], [.1, .3, .7, .9])) + [np.inf], labels=["lo10", "lo", "mid", "hi", "hi10"])
    return Q.groupby(["grp", "q"], observed=True)[tgt].mean().unstack().mul(100).round(1)
def q5e(P, feat, tgt="f10"):
    Q = P[P.grp == "stocks"].dropna(subset=[feat]).copy(); Q["q"] = pd.cut(Q[feat], [-np.inf] + list(np.nanquantile(Q[feat], [.1, .3, .7, .9])) + [np.inf], labels=["lo10", "lo", "mid", "hi", "hi10"])
    return Q.groupby(["era", "q"], observed=True)[tgt].mean().unstack().mul(100).round(1)
for feat in ("ON63", "ID63", "ON21", "ID21", "RV1", "RV5", "CL5", "ER", "V"):
    print(f"\n--- {feat}: fwd 10-bar z x100 by pooled quantile bucket"); print(q5(P, feat).to_string()); print("stocks by era:"); print(q5e(P, feat).to_string())
# dips by volume: capitulation on heavy volume?
Q = P[(P.S5 < -1.5)].copy(); Q["vol"] = np.where(Q.RV5 > 0.3, "heavy", np.where(Q.RV5 < -0.1, "light", "normal")); Q["tr"] = np.where(Q["T"] > 0, "up", "down")
print("\nDIPS (S5<-1.5): fwd10 z x100 by volume and trend"); print(Q.groupby(["grp", "tr", "vol"])["f10"].agg(["mean", "size"]).assign(mean=lambda x: x["mean"] * 100).round(1).unstack().to_string())
print("by era, stocks+index"); print(Q[Q.grp.isin(["stocks", "index"])].groupby(["era", "tr", "vol"], observed=True)["f10"].mean().mul(100).round(1).unstack().to_string())
