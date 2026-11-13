"""Column-flip signals, filtered by the trend tapes, risk, midline and VWAP.  python3 study_flip.py > flips.txt

Definitions (all on closed bars, as the pane draws them):
  FLIP      the surprise column changes sign: from below zero to at/above (bull), or the reverse (bear).
  OUTER     the stretch-ladder tape (outer, top) leans the flip's way: ladX on the flip's side.
  BOTH      OUTER and the trend tape (inner, top) on the flip's side: T on the flip's side.
  CALM / STRESSED   the risk tape's regime on the flip bar.
  +MID      close on the flip's side of the midline.   +VWAP   close on the flip's side of the session VWAP.
Outcome: the next 10 bars from the next open, in forecast sigma, signed by the flip's direction, minus the
instrument group's mean for that era - so a long flip in a rising market gets no credit for the drift."""
from lib import *
from pragyam import run
import warnings; warnings.filterwarnings("ignore")
pd.set_option("display.width", 250)
H = 10
def vwap(d, intraday):
    key = d.index.normalize() if intraday else d.index.to_period("W").start_time
    v = d.volume.astype(float).fillna(0); w = v.clip(lower=1e-10) if (v > 0).mean() >= 0.5 else pd.Series(1.0, d.index)
    return ((d.high + d.low + d.close) / 3 * w).groupby(key).cumsum() / w.groupby(key).cumsum()
BASE = [("flip", None), ("flip + outer", "O"), ("flip + both", "B"), ("flip + outer + calm", "Oc"), ("flip + outer + stressed", "Os"),
        ("flip + both + calm", "Bc"), ("flip + both + stressed", "Bs")]
ADD = [("", ""), (" + mid", "m"), (" + vwap", "v"), (" + mid + vwap", "mv")]
VARS = [(b + a, (k or "") + ak) for b, k in BASE for a, ak in ADD]
def cond(F, key, side):
    c = pd.Series(True, F.index)
    if "O" in key or "B" in key: c &= np.sign(F.ladX) == side
    if "B" in key: c &= np.sign(F["T"]) == side
    if "c" in key: c &= F.reg == 0
    if "s" in key: c &= F.reg == 2
    if "m" in key: c &= np.sign(F.close - F.mid) == side
    if "v" in key: c &= np.sign(F.close - F.vw) == side
    return c
def block(D, title, ann, intraday):
    evs = []; rules = []
    for s, (cls, d) in D.items():
        R = run(d); c = d.close; lc, lo = np.log(c), np.log(d.open)
        F = pd.DataFrame(dict(u=R.u, ladX=R.ladX, T=R["T"], reg=R.reg.where(R.prk.notna()), close=c, mid=(R.upper.shift(H) + R.lower.shift(H)) / 2, vw=vwap(d, intraday)), index=d.index)
        up = (F.u >= 0) & (F.u.shift(1) < 0); dn = (F.u < 0) & (F.u.shift(1) >= 0)
        ok = F.notna().all(axis=1) & F.u.shift(1).notna()
        sH = R.sig * np.sqrt(H)
        f = ((lc.shift(-H) - lo.shift(-1)) / sH).clip(-6, 6)
        ro = d.open.shift(-2) / d.open.shift(-1) - 1; cost = 0.001 if cls == "crypto" else 0.0005
        hold = ro.where(ok).dropna()
        for name, key in VARS:
            bu = up & ok & cond(F, key, 1); bd = dn & ok & cond(F, key, -1)
            for side, m in ((1, bu), (-1, bd)):
                if m.any(): evs.append(pd.DataFrame(dict(v=name, side=side, f=f[m], date=d.index[m], cls=cls, sym=s)))
            # rule: on a signal, hold its side for H bars; an opposite signal switches. Long-only and long/short.
            sig = pd.Series(np.where(bu, 1.0, np.where(bd, -1.0, np.nan)), d.index)
            last = sig.ffill(limit=H - 1)                                   # the side held for H bars after the signal
            for mode in ("long", "long/short"):
                p = last.clip(lower=0) if mode == "long" else last
                p = p.fillna(0.0).where(ok | p.notna())
                pnl = (p * ro - cost * p.diff().abs().fillna(0)).where(ok).dropna()
                if len(pnl) > 250 and pnl.std() > 0:
                    eq = (1 + pnl).cumprod(); eh = (1 + hold).cumprod()
                    rules.append(dict(v=name, mode=mode, sym=s, cls=cls, sh=pnl.mean() / pnl.std() * np.sqrt(ann), h_sh=hold.mean() / hold.std() * np.sqrt(ann),
                                      dd=(eq / eq.cummax() - 1).min(), h_dd=(eh / eh.cummax() - 1).min(), inmkt=(p != 0).mean(), n=int((bu | bd).sum()),
                                      **({f"sh_{a[2:]}": (lambda q: q.mean() / q.std() * np.sqrt(ann) if len(q) > 250 and q.std() > 0 else np.nan)(pnl[a:b]) for a, b in ERAS} if ann == 252 else {})))
    E = pd.concat(evs, ignore_index=True)
    E["era"] = pd.cut(E.date.dt.year, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"])
    E["grp"] = np.where(E.cls.isin(["us", "nse", "index"]), "equity", np.where(E.cls == "crypto", "crypto", "macro"))
    # baseline: the mean 10-bar forward return of ALL bars in that group and era (from the 'flip' universe is biased; use every bar)
    return E, pd.DataFrame(rules)
def report(E, X, title, base, ann):
    E = E.merge(base, on=["grp", "era"], how="left") if "era" in base.columns else E.merge(base, on="grp", how="left")
    E["x"] = E.side * (E.f - E.mu)                                        # follow-through beyond drift, sigma
    E = E[E.x.notna()]                                                    # events too recent to have 10 bars after them
    def tt(q):
        g = q.groupby("date").x; m, n = g.mean(), g.size(); x = (m * n).values; mu = x.sum() / n.sum(); e = x - mu * n.values; v = (e * e).sum()
        for L in range(1, H + 1): v += 2 * (1 - L / (H + 1)) * (e[L:] * e[:-L]).sum()
        return mu / (np.sqrt(v) / n.sum())
    order = [v for v, _ in VARS]
    Q = E[E.grp != "crypto"]
    print(f"\n{title}\nA. FOLLOW-THROUGH. Next 10 bars in the flip's direction, beyond drift, sigma x100 (ex crypto). t clustered by date, Newey-West over 10 bars.")
    g = Q.groupby("v", sort=False)
    t = pd.DataFrame(dict(events=g.size(), per_inst_yr=g.size() / (Q.sym.nunique() * max(1, (Q.date.max() - Q.date.min()).days / 365.25)), all=g.x.mean() * 100,
                          t=g.apply(tt), long=Q[Q.side == 1].groupby("v").x.mean() * 100, short=Q[Q.side == -1].groupby("v").x.mean() * 100))
    if "era" in Q.columns and Q.era.nunique() > 1:
        t = t.join(Q.groupby(["v", "era"], observed=True).x.mean().unstack().mul(100))
    print(t.reindex(order).round(2).to_string())
    print("\n   crypto:"); C = E[E.grp == "crypto"]; gc = C.groupby("v", sort=False)
    print(pd.DataFrame(dict(events=gc.size(), all=gc.x.mean() * 100, t=gc.apply(tt))).reindex(order).round(2).to_string())
    for mode in ("long", "long/short"):
        Y = X[X["mode"] == mode]; g = Y.groupby("v", sort=False)
        cols = dict(inmkt=g.inmkt.mean(), sharpe=g.sh.mean(), hold=g.h_sh.mean(), dd=g.dd.mean(), hold_dd=g.h_dd.mean(), sh_win=g.apply(lambda q: (q.sh > q.h_sh).mean()))
        for c in [c for c in Y.columns if c.startswith("sh_")]: cols[c] = g[c].mean()
        print(f"\nB. AS A RULE, {mode}: on a signal hold its side for 10 bars, filled at the next open, net of costs; mean across instruments")
        print(pd.DataFrame(cols).reindex(order).round(3).to_string())
D = load()
E, X = block(D, "", 252, False)
# drift baseline per group and era, from every bar
rows = []
for s, (cls, d) in D.items():
    R = run(d); lc, lo = np.log(d.close), np.log(d.open); f = ((lc.shift(-H) - lo.shift(-1)) / (R.sig * np.sqrt(H))).clip(-6, 6).dropna()
    rows.append(pd.DataFrame(dict(f=f.values, yr=f.index.year, cls=cls)))
B = pd.concat(rows); B["era"] = pd.cut(B.yr, [1999, 2012, 2019, 2030], labels=["03-12", "13-19", "20-26"]); B["grp"] = np.where(B.cls.isin(["us", "nse", "index"]), "equity", np.where(B.cls == "crypto", "crypto", "macro"))
base = B.groupby(["grp", "era"], observed=True).f.mean().rename("mu").reset_index()
report(E, X, "═══ DAILY BARS, 2001-2026 · weekly VWAP ═══", base, 252)
D1 = load("data1h", 2500)
E1, X1 = block(D1, "", 252 * 7, True)
rows = []
for s, (cls, d) in D1.items():
    R = run(d); lc, lo = np.log(d.close), np.log(d.open); f = ((lc.shift(-H) - lo.shift(-1)) / (R.sig * np.sqrt(H))).clip(-6, 6).dropna()
    rows.append(pd.DataFrame(dict(f=f.values, cls=cls)))
B1 = pd.concat(rows); B1["grp"] = np.where(B1.cls.isin(["us", "nse", "index"]), "equity", np.where(B1.cls == "crypto", "crypto", "macro"))
base1 = B1.groupby("grp").f.mean().rename("mu").reset_index()
E1 = E1.drop(columns="era")
report(E1, X1, "═══ HOURLY BARS, about two years · daily VWAP ═══", base1, 252 * 7)
