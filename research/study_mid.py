"""The midline of the landing band as a trend divider - and whether calm risk and flips sharpen it.  python3 study_mid.py > midline.txt"""
from lib import *
from pragyam import run
import warnings, sys; warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
H = 10
def build(d, cls, cost):
    R = run(d); c, o = d.close, d.open
    mid = (R.upper.shift(H) + R.lower.shift(H)) / 2                       # the average of the landing band
    ab = pd.Series(np.where(mid.isna(), np.nan, np.where(c > mid, 1.0, -1.0)), index=d.index)
    cross = ab.where(ab != ab.shift(1)).where(ab.shift(1).notna())        # +1 crossed above, -1 crossed below, on the bar it closed across
    T = R["T"]; reg = R.reg.where(R.prk.notna()); u = R.u
    tsign = np.sign(T); tflip = (tsign != tsign.shift(1)) & tsign.shift(1).notna()
    tflipK = tflip.rolling(H).max().fillna(0).astype(bool)                # trend changed side within the last H bars
    def hold_from(cond):                                                  # take the cross's side if cond holds on the cross bar, else stand aside; hold to the next cross
        return cross.where(cond, 0.0).where(cross.notna()).ffill()
    calm, stress = reg == 0, reg == 2
    P = {
     "hold":                              pd.Series(1.0, d.index).where(ab.notna()),
     "midline long/flat":                 ab.clip(lower=0),
     "midline long/short":                ab,
     "close vs close[10] long/flat":      pd.Series(np.where(c > c.shift(H), 1.0, 0.0), d.index).where(ab.notna()),
     "trend tape long/flat (T>0)":        (T > 0).astype(float).where(ab.notna()),
     "midline AND trend agree, l/f":      ((ab > 0) & (T > 0)).astype(float).where(ab.notna()),
     "midline AND trend agree, l/s":      pd.Series(np.where((ab > 0) & (T > 0), 1.0, np.where((ab < 0) & (T < 0), -1.0, 0.0)), d.index).where(ab.notna()),
     "cross in CALM risk, l/f":           hold_from(calm).clip(lower=0),
     "cross in CALM risk, l/s":           hold_from(calm),
     "cross in NORMAL risk, l/s":         hold_from(reg == 1),
     "cross in STRESSED risk, l/s":       hold_from(stress),
     "cross with trend FLIP, l/s":        hold_from(tflipK & (tsign == cross)),
     "cross in CALM + trend agrees, l/s": hold_from(calm & (tsign == cross)),
     "cross in CALM + trend FLIP, l/s":   hold_from(calm & tflipK & (tsign == cross)),
    }
    ro = (o.shift(-2) / o.shift(-1) - 1)                                  # decided at the close of t, filled at the next open, held to the open after
    out = {}
    for k, p in P.items():
        pnl = (p * ro - cost * p.diff().abs().fillna(0)).shift(2)        # dated when it is earned
        out[k] = (p, pnl)
    return R, mid, ab, cross, reg, T, out
def stats(p, ann=252):
    p = p.dropna()
    if len(p) < 500 or p.std() == 0: return None
    eq = (1 + p).cumprod(); return dict(sh=p.mean() / p.std() * np.sqrt(ann), dd=(eq / eq.cummax() - 1).min(), cagr=eq.iloc[-1] ** (ann / len(p)) - 1)
def block(D, title, ann):
    rows = []; ev = []; runs = []
    for s, (cls, d) in D.items():
        R, mid, ab, cross, reg, T, out = build(d, cls, 0.001 if cls == "crypto" else 0.0005)
        for k, (p, pnl) in out.items():
            for a, b in [("2001", "2026")] + (ERAS if ann == 252 else []):
                st = stats(pnl[a:b], ann)
                if st: rows.append(dict(sym=s, cls=cls, v=k, era="all" if a == "2001" else a[2:] + "-" + b[2:], inmkt=(p[a:b] != 0).mean(), turn=p[a:b].diff().abs().mean() * ann, **st))
        lc, lo = np.log(d.close), np.log(d.open); sH = R.sig * np.sqrt(H)
        f10 = ((lc.shift(-H) - lo.shift(-1)) / sH).clip(-6, 6)             # next 10 bars from the next open, in forecast sigma
        m = cross.notna() & f10.notna() & reg.notna()
        ev.append(pd.DataFrame(dict(side=cross[m], f=f10[m] * cross[m], reg=reg[m], tr=np.sign(T[m]) * cross[m], date=d.index[m], cls=cls, sym=s, base=f10.mean())))
        # every run from one cross to the next: what it earned in the cross's direction, in sigma at entry, and how long it lasted
        idx = np.flatnonzero(cross.notna().values); o = d.open.values; sg = R.sig.values; cv = cross.values; rg = reg.values
        for a, b in zip(idx[:-1], idx[1:]):
            if a + 1 < len(o) and b + 1 < len(o) and not np.isnan(sg[a]) and not np.isnan(rg[a]):
                runs.append((cls, s, d.index[a].year, cv[a], rg[a], b - a, float(np.clip(cv[a] * np.log(o[b + 1] / o[a + 1]) / sg[a], -30, 30)), cv[a] * np.log(o[b + 1] / o[a + 1])))
    X = pd.DataFrame(rows); order = list(dict.fromkeys(X.v)); A = X[X.era == "all"]; hd = A[A.v == "hold"].set_index("sym")
    g = A.groupby("v", sort=False)
    t = g[["inmkt", "turn", "sh", "cagr", "dd"]].mean()
    t["sh>hold"] = g.apply(lambda q: (q.set_index("sym").sh > hd.sh.reindex(q.sym.values).values).mean()); t["dd<hold"] = g.apply(lambda q: (q.set_index("sym").dd > hd.dd.reindex(q.sym.values).values).mean())
    print(f"\n{title}\nA. AS A RULE. mean across {A.sym.nunique()} instruments, filled at the next open, net of costs")
    print(t.reindex(order).round(3).to_string())
    if ann == 252:
        print("\nSharpe by era"); print(X[X.era != "all"].pivot_table(index="v", columns="era", values="sh").reindex(order).round(2).to_string())
        print("\nSharpe by class"); print(A.pivot_table(index="v", columns="cls", values="sh").reindex(order)[[c for c in CLASSES]].round(2).to_string())
    E = pd.concat(ev); E["era"] = pd.cut(E.date.dt.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"]); E["regime"] = E.reg.map({0: "calm", 1: "normal", 2: "stressed"})
    E["grp"] = np.where(E.cls == "crypto", "crypto", "rest")
    def tt(q):
        gg = q.groupby("date")["f"]; m, n = gg.mean(), gg.size(); x = (m * n).values; mu = x.sum() / n.sum(); e = x - mu * n.values
        return mu / (np.sqrt((e * e).sum()) / n.sum())
    print("\nB. AFTER A CROSS. The next 10 bars in the cross's direction, in sigma x100 (positive = it followed through). ex crypto")
    Q = E[E.grp == "rest"]
    print(pd.DataFrame(dict(n=Q.groupby("side").size(), follow=Q.groupby("side").f.mean() * 100, t=Q.groupby("side").apply(tt))).rename(index={1.0: "crossed above", -1.0: "crossed below"}).round(2).to_string())
    if ann == 252: print("by era"); print((Q.groupby(["side", "era"], observed=True).f.mean().unstack() * 100).rename(index={1.0: "crossed above", -1.0: "crossed below"}).round(1).to_string())
    print("by the risk regime at the cross"); print(pd.DataFrame(dict(n=Q.groupby(["side", "regime"]).size(), follow=Q.groupby(["side", "regime"]).f.mean() * 100, t=Q.groupby(["side", "regime"]).apply(tt))).rename(index={1.0: "crossed above", -1.0: "crossed below"}).round(2).to_string())
    if ann == 252: print("by regime and era (both sides pooled)"); print((Q.groupby(["regime", "era"], observed=True).f.mean().unstack() * 100).round(1).to_string())
    print("by whether the trend tape already pointed the cross's way"); print(pd.DataFrame(dict(n=Q.groupby("tr").size(), follow=Q.groupby("tr").f.mean() * 100, t=Q.groupby("tr").apply(tt))).rename(index={1.0: "trend agreed", -1.0: "trend opposed", 0.0: "trend zero"}).round(2).to_string())
    Rn = pd.DataFrame(runs, columns=["cls", "sym", "yr", "side", "reg", "bars", "gain_sig", "gain"]); Rn = Rn[Rn.cls != "crypto"]; Rn["regime"] = Rn.reg.map({0: "calm", 1: "normal", 2: "stressed"})
    print("\nC. EVERY RUN, cross to the next cross (ex crypto). gain = move in the cross's direction, next open to next open")
    g = Rn.groupby("regime")
    print(pd.DataFrame(dict(runs=g.size(), bars_mean=g.bars.mean(), bars_median=g.bars.median(), won=g.apply(lambda q: (q.gain > 0).mean()), gain_pct_mean=g.gain.mean() * 100, gain_pct_median=g.gain.median() * 100,
                            gain_sigma_mean=g.gain_sig.mean(), big_runs=g.apply(lambda q: (q.bars >= 20).mean()), gain_of_big_pct=g.apply(lambda q: q[q.bars >= 20].gain.mean() * 100))).round(3).to_string())
    print("all runs:", dict(runs=len(Rn), won=round((Rn.gain > 0).mean(), 3), mean_pct=round(Rn.gain.mean() * 100, 3), median_bars=Rn.bars.median()))
    return X
D = load()
c = D["AAPL"][1]; R = run(c); mid = (R.upper.shift(H) + R.lower.shift(H)) / 2
agree = []
for s, (cls, d) in D.items():
    R = run(d); mid = (R.upper.shift(H) + R.lower.shift(H)) / 2; m = mid.notna()
    agree.append(((d.close > mid)[m] == (d.close > d.close.shift(H))[m]).mean())
print("WHAT THE MIDLINE IS. The average of the landing band is the close 10 bars ago, nudged by the cone's skew.")
print(f"Share of bars on which 'close above the midline' and 'close above the close 10 bars ago' say the same thing: {np.mean(agree):.3f} (min {np.min(agree):.3f})")
block(D, "═══ DAILY BARS, 2001-2026 ═══", 252)
block(load("data1h", 2500), "═══ HOURLY BARS, about two years ═══", 252 * 7)

# ---------- D, E: the state itself, and slower midlines (daily) ----------------------------------------------------------
rows = []; sweep = []
for s, (cls, d) in D.items():
    R = run(d); c = d.close; lc = np.log(c); mid = (R.upper.shift(H) + R.lower.shift(H)) / 2
    z1 = ((lc.shift(-1) - lc) / R.sig).clip(-8, 8); f10 = ((lc.shift(-H) - np.log(d.open).shift(-1)) / (R.sig * np.sqrt(H))).clip(-6, 6)
    ab = np.where(c > mid, "above", "below"); m = mid.notna() & z1.notna() & R.prk.notna()
    side = pd.Series(np.where(c > mid, 1.0, -1.0), index=d.index); cross = side.where(side != side.shift(1)).where(mid.shift(1).notna() & mid.notna())
    rows.append(pd.DataFrame(dict(state=ab[m], z1=z1[m], f10=f10[m], cross=cross[m], reg=R.reg[m].map({0: "calm", 1: "normal", 2: "stressed"}), tr=np.where(R["T"][m] > 0, "trend up", "trend down"), yr=d.index[m].year, cls=cls)))
    ro = c.shift(-2) / c.shift(-1) - 1; cost = 0.001 if cls == "crypto" else 0.0005
    for N in (5, 10, 20, 40, 63, 126, 252):
        p = pd.Series(np.where(c > c.shift(N), 1.0, 0.0), d.index).where(R.sig.notna()); pnl = (p * ro - cost * p.diff().abs().fillna(0)).dropna()
        hd = ro.where(R.sig.notna()).dropna()
        if len(pnl) > 500:
            eq = (1 + pnl).cumprod(); eh = (1 + hd).cumprod()
            sweep.append(dict(N=N, sh=pnl.mean() / pnl.std() * np.sqrt(252), h_sh=hd.mean() / hd.std() * np.sqrt(252), dd=(eq / eq.cummax() - 1).min(), h_dd=(eh / eh.cummax() - 1).min(), turn=p.diff().abs().mean() * 252, cls=cls))
Q = pd.concat(rows); Q = Q[Q.cls != "crypto"]; Q["era"] = pd.cut(Q.yr, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
print("\n═══ DAILY, ex crypto ═══\nD. THE STATE ITSELF. Next bar's return per unit of risk (sigma x100) while price is above / below the midline")
print(Q.groupby("state").z1.agg(["mean", "size"]).assign(mean=lambda x: x["mean"] * 100).round(2).to_string())
print("by era"); print((Q.groupby(["state", "era"], observed=True).z1.mean().unstack() * 100).round(2).to_string())
print("by risk regime"); print((Q.groupby(["state", "reg"]).z1.mean().unstack() * 100).round(2).to_string())
print("by the trend tape"); print((Q.groupby(["state", "tr"]).z1.mean().unstack() * 100).round(2).to_string())
X = Q[Q.cross.notna()].copy(); X["side"] = X.cross.map({1.0: "crossed above", -1.0: "crossed below"})
print("\nRAW next-10-bar return (sigma x100) after a cross, by side and trend tape - compare with all bars:", round(Q.f10.mean() * 100, 2))
print((X.groupby(["side", "tr"]).f10.mean().unstack() * 100).round(2).to_string()); print("counts"); print(X.groupby(["side", "tr"]).size().unstack().to_string())
print("the same in CALM risk only"); print((X[X.reg == "calm"].groupby(["side", "tr"]).f10.mean().unstack() * 100).round(2).to_string())
print("by era, calm risk, crossed above with trend up  /  crossed below with trend down")
print((X[(X.reg == "calm")].groupby(["side", "tr", "era"], observed=True).f10.mean().unstack() * 100).round(2).to_string())
S = pd.DataFrame(sweep); g = S.groupby("N")
print("\nE. A SLOWER MIDLINE. Long while the close is above the close N bars ago, flat otherwise; mean across instruments, net of costs")
print(pd.DataFrame(dict(sharpe=g.sh.mean(), hold=g.h_sh.mean(), dd=g.dd.mean(), hold_dd=g.h_dd.mean(), turnover=g.turn.mean(), sh_win=g.apply(lambda q: (q.sh > q.h_sh).mean()), dd_win=g.apply(lambda q: (q.dd > q.h_dd).mean()))).round(3).to_string())
