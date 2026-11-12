"""Two more observations, tested alone and together with the midline.  python3 study_obs.py > observations.txt
  1. When the long stop is further from the close than the short stop, the trend is bearish - and the reverse.
  2. Does the session VWAP, mixed with that and with the midline, change anything?"""
from lib import *
from kasauti import run
import warnings; warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
H = 10
def vwap(d, intraday):
    key = d.index.normalize() if intraday else d.index.to_period("W").start_time       # the profile's sessions: a day intraday, a week on daily bars
    v = d.volume.astype(float).fillna(0); use = (v > 0).mean() >= 0.5; w = v.clip(lower=1e-10) if use else pd.Series(1.0, d.index)
    pv = ((d.high + d.low + d.close) / 3 * w).groupby(key).cumsum(); vv = w.groupby(key).cumsum()
    return pv / vv
def block(D, title, ann, intraday):
    rows = []; pn = []
    for s, (cls, d) in D.items():
        R = run(d); c = d.close; lc = np.log(c)
        mid = (R.upper.shift(H) + R.lower.shift(H)) / 2; vw = vwap(d, intraday)
        dL = c - R.stopL; dS = R.stopS - c; asym = np.log(dL / dS)                      # > 0: the long stop is the further one
        z1 = ((lc.shift(-1) - lc) / R.sig).clip(-8, 8); f10 = ((lc.shift(-H) - np.log(d.open).shift(-1)) / (R.sig * np.sqrt(H))).clip(-6, 6)
        m = mid.notna() & asym.notna() & z1.notna() & R.prk.notna() & vw.notna()
        F = pd.DataFrame(dict(asym=asym, far=np.where(asym > 0, "long stop further", "short stop further"), mid=np.where(c > mid, "above mid", "below mid"), vw=np.where(c > vw, "above vwap", "below vwap"),
                              T=R["T"], tr=np.where(R["T"] > 0.5, "up", np.where(R["T"] < -0.5, "down", "flat")), reg=R.reg.map({0: "calm", 1: "normal", 2: "stressed"}), z1=z1, f10=f10, yr=d.index.year, cls=cls, sym=s), index=d.index)[m]
        rows.append(F)
        ro = c.shift(-2) / c.shift(-1) - 1; cost = 0.001 if cls == "crypto" else 0.0005; ok = m
        bullA = asym < 0; aM = c > mid; aV = c > vw                                    # the observation: short stop further = bullish
        P = {"hold": pd.Series(1.0, d.index), "stop asymmetry (short stop further = long)": bullA.astype(float), "stop asymmetry, REVERSED": (~bullA).astype(float),
             "above vwap": aV.astype(float), "below vwap (the reverse)": (~aV).astype(float), "above vwap, NO COSTS": aV.astype(float), "below vwap, NO COSTS": (~aV).astype(float), "above midline": aM.astype(float), "above vwap AND midline": (aV & aM).astype(float),
             "all three bullish": (aV & aM & bullA).astype(float), "all three, long/short": pd.Series(np.where(aV & aM & bullA, 1.0, np.where(~aV & ~aM & ~bullA, -1.0, 0.0)), d.index),
             "vwap AND midline, long/short": pd.Series(np.where(aV & aM, 1.0, np.where(~aV & ~aM, -1.0, 0.0)), d.index),
             "all three bullish, entered in CALM risk": None}
        for k, p in P.items():
            if p is None:
                st = (aV & aM & bullA); ent = st & ~st.shift(1, fill_value=False); pos = pd.Series(np.nan, d.index); pos[ent & (R.reg == 0)] = 1.0; pos[ent & (R.reg != 0)] = 0.0; pos[~st] = 0.0; p = pos.ffill().fillna(0.0)
            p = p.where(ok); pnl = (p * ro - (0.0 if "NO COSTS" in k else cost) * p.diff().abs().fillna(0)).dropna()
            if len(pnl) > 500 and pnl.std() > 0:
                eq = (1 + pnl).cumprod(); pn.append(dict(v=k, sym=s, cls=cls, sh=pnl.mean() / pnl.std() * np.sqrt(ann), dd=(eq / eq.cummax() - 1).min(), inmkt=(p != 0).mean(), turn=p.diff().abs().mean() * ann,
                                                          **({f"sh_{a[2:]}": (lambda q: q.mean() / q.std() * np.sqrt(ann) if len(q) > 250 and q.std() > 0 else np.nan)(pnl[a:b]) for a, b in ERAS} if ann == 252 else {})))
    Q = pd.concat(rows, ignore_index=True); Q = Q[Q.cls != "crypto"].reset_index(drop=True); Q["era"] = pd.cut(Q.yr, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
    print(f"\n{title}  (ex crypto unless stated; returns are per unit of forecast risk, sigma x100; all bars: next bar {Q.z1.mean() * 100:.2f}, next 10 bars {Q.f10.mean() * 100:.2f})")
    print("\n1. STOP ASYMMETRY. Which stop is further from the close, by the trend tape's state (share of bars in each trend state)")
    print(pd.crosstab(Q.tr, Q.far, normalize="index").round(3).to_string())
    print("mean trend (sigma) by which stop is further:", Q.groupby("far")["T"].mean().round(2).to_dict(), " correlation of asymmetry with trend:", round(Q.asym.corr(Q["T"]), 3))
    print("what followed: next bar / next 10 bars"); print((Q.groupby("far")[["z1", "f10"]].mean() * 100).round(2).assign(bars=Q.groupby("far").size()).to_string())
    if ann == 252: print("next 10 bars, by era"); print((Q.groupby(["far", "era"], observed=True).f10.mean().unstack() * 100).round(2).to_string())
    print("next 10 bars, within each trend state (does the asymmetry add anything to the trend tape?)"); print((Q.groupby(["tr", "far"]).f10.mean().unstack() * 100).round(2).to_string())
    print("\n2. VWAP, AND THE THREE TOGETHER. Next bar's return")
    print((Q.groupby("vw").z1.mean() * 100).round(2).to_dict())
    print("vwap x midline"); print((Q.groupby(["vw", "mid"]).z1.mean().unstack() * 100).round(2).to_string()); print((Q.groupby(["vw", "mid"]).size().unstack() / len(Q)).round(3).to_string())
    print("vwap x midline x stop asymmetry: next bar"); print((Q.groupby(["vw", "mid", "far"]).z1.mean().unstack() * 100).round(2).to_string())
    print("vwap x midline x stop asymmetry: next 10 bars"); print((Q.groupby(["vw", "mid", "far"]).f10.mean().unstack() * 100).round(2).to_string())
    if ann == 252:
        Q["all3"] = np.where((Q.vw == "above vwap") & (Q.mid == "above mid") & (Q.far == "short stop further"), "all bullish", np.where((Q.vw == "below vwap") & (Q.mid == "below mid") & (Q.far == "long stop further"), "all bearish", "mixed"))
        print("all three agreeing, next 10 bars by era"); print((Q.groupby(["all3", "era"], observed=True).f10.mean().unstack() * 100).round(2).assign(share=Q.groupby("all3").size() / len(Q)).to_string())
        print("all three agreeing, next 10 bars by risk regime"); print((Q.groupby(["all3", "reg"]).f10.mean().unstack() * 100).round(2).to_string())
    X = pd.DataFrame(pn); order = list(dict.fromkeys(X.v)); hd = X[X.v == "hold"].set_index("sym"); g = X.groupby("v", sort=False)
    t = g[["inmkt", "turn", "sh", "dd"] + ([c for c in X.columns if c.startswith("sh_")])].mean()
    t["sh>hold"] = g.apply(lambda q: (q.set_index("sym").sh > hd.sh.reindex(q.sym.values).values).mean()); t["dd<hold"] = g.apply(lambda q: (q.set_index("sym").dd > hd.dd.reindex(q.sym.values).values).mean())
    print(f"\n3. AS RULES. long while the condition holds, one bar late, net of costs; mean across {X.sym.nunique()} instruments (crypto included)"); print(t.reindex(order).round(3).to_string())
block(load(), "═══ DAILY BARS, 2001-2026 · weekly VWAP ═══", 252, False)
block(load("data1h", 2500), "═══ HOURLY BARS, about two years · daily VWAP ═══", 252 * 7, True)
