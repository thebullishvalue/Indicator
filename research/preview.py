"""Draws what maryada.pine draws, from the reference implementation.  python3 preview.py"""
from lib import *
from maryada import run, touch_prob, profile, AP
import warnings; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
D = load(); H = 10
BG, SOFT, BULL, BEAR, NEUT, GOLD, VA, POC = "#0D1215", "#A8B3B9", "#3FB980", "#E4776A", "#8A97A0", "#CFC257", "#5B8FD6", "#FFB020"   # Pragati's palette, dark
def tr(c, t): return to_rgba(c, 1 - t / 100)                                # colour at Pine transparency t
def grad(x, a, b, c, ta, tb): f = min(max((x - a) / (b - a), 0), 1); return tr(c, ta + (tb - ta) * f)
for sym, title in (("_NSEI", "Nifty 50 · daily"), ("AAPL", "Apple · daily")):
    cls, d = D[sym]; R = run(d); n = 170; d2, R2 = d.iloc[-n:], R.iloc[-n:]; x = np.arange(n); P, naked, (bins, bw) = profile(d)
    fig, ax = plt.subplots(2, 1, figsize=(14.5, 9.4), sharex=True, gridspec_kw=dict(height_ratios=[2.6, 1.5], hspace=0.05), facecolor=BG)
    for a in ax:
        a.set_facecolor(BG); a.tick_params(colors=NEUT, labelsize=8); [s.set_color("#222a30") for s in a.spines.values()]; a.grid(color="#1a2227", lw=0.5)
    a = ax[0]
    for i in range(n):
        o, h, l, c = d2.open.iloc[i], d2.high.iloc[i], d2.low.iloc[i], d2.close.iloc[i]; col = BULL if c >= o else BEAR
        a.plot([i, i], [l, h], color=col, lw=0.8); a.plot([i, i], [min(o, c), max(o, c)], color=col, lw=3)
    a.plot(x, R.upper.shift(H).iloc[-n:], color=VA, lw=1, alpha=.45); a.plot(x, R.lower.shift(H).iloc[-n:], color=VA, lw=1, alpha=.45)
    c, sg, sH, qu, qd = d2.close.iloc[-1], R2.sig.iloc[-1], R2.sH.iloc[-1], R2.qU.iloc[-1], R2.qD.iloc[-1]; j = np.arange(H + 1); x0 = n - 1
    a.fill_between(x0 + j, c * np.exp(-qd * sg * np.sqrt(j)), c * np.exp(qu * sg * np.sqrt(j)), color=VA, alpha=.14, lw=0); a.plot(x0 + j, c * np.exp(qu * sg * np.sqrt(j)), color=VA, lw=1, alpha=.7); a.plot(x0 + j, c * np.exp(-qd * sg * np.sqrt(j)), color=VA, lw=1, alpha=.7)
    sl, ss = R2.stopL.iloc[-1], R2.stopS.iloc[-1]; a.plot([x0, x0 + H], [sl, sl], color=BEAR, ls="--", lw=1); a.plot([x0, x0 + H], [ss, ss], color=BULL, ls="--", lw=1)
    aU = [R2[f"aUp{k}"].iloc[-1] for k in range(len(AP))]; aD = [R2[f"aDn{k}"].iloc[-1] for k in range(len(AP))]
    def prob(L): return float(touch_prob(abs(np.log(L / c)) / sH, *(aU if L >= c else aD)))
    poc, vah, val, pp, pv, pl = P[-1]; left = x0 + H + 6; W = 30; ks = sorted(bins); vmax = max(bins.values())
    for k in ks:                                                          # the profile: amber POC row, blue value area, grey tails
        mid = (k + .5) * bw; col = POC if abs(mid - poc) < bw / 2 else VA if val <= mid <= vah else "#6E7C88"
        a.barh(k * bw, W * bins[k] / vmax, height=bw * .85, left=left, align="edge", color=tr(col, 25 if col == POC else 48 if col == VA else 72))
    ws = int(np.argmax(d.index.to_period("W").asi8[-n:] == d.index.to_period("W").asi8[-1]))
    a.plot([ws, left + W], [poc, poc], color=POC, lw=1.6); a.plot([ws, left + W], [vah, vah], color=VA, lw=1, alpha=.8); a.plot([ws, left + W], [val, val], color=VA, lw=1, alpha=.8); a.fill_between([ws, x0], val, vah, color=VA, alpha=.07, lw=0)
    for y, cc in ((pp, POC), (pv, VA), (pl, VA)): a.plot([x0 - 30, left + W], [y, y], color=cc, lw=1, ls=":", alpha=.6)
    for y in naked[-1]: a.plot([x0 - 60, x0], [y, y], color=POC, lw=1, ls=":", alpha=.7)
    tags = [(sl, "STOP long · 20%", BEAR), (ss, "STOP short · 20%", BULL), (c * np.exp(qu * sH), "CONE ▲", VA), (c * np.exp(-qd * sH), "CONE ▼", VA), (poc, f"POC · {prob(poc):.0%}", POC), (vah, f"VAH · {prob(vah):.0%}", VA),
            (val, f"VAL · {prob(val):.0%}", VA), (pp, f"pPOC · {prob(pp):.0%}", POC), (pv, f"pVAH · {prob(pv):.0%}", VA), (pl, f"pVAL · {prob(pl):.0%}", VA)]
    seated = []; gap = (d2.high.max() - d2.low.min()) * 0.022
    for y, t, cc in tags:                                                 # the tag column: first seated wins, as in the script
        if all(abs(y - s) >= gap for s in seated): seated.append(y); a.text(left + W + 3, y, f"{t}   {y:,.0f}", color=cc, fontsize=7.2, va="center")
    lo, hi = min(d2.low.min(), sl, val, pl) , max(d2.high.max(), ss, vah, pv); a.set_ylim(lo - (hi - lo) * .04, hi + (hi - lo) * .04)
    a.set_title(f"Maryada · {title}   (rendered from research/maryada.py, not from TradingView)", color=SOFT, fontsize=11, loc="left")
    a = ax[1]; u = R2.u.values; bU = R.qU.shift(H).iloc[-n:].values; bD = R.qD.shift(H).iloc[-n:].values; T = R2["T"].values
    for i in range(n):                                                    # columns in Pragati's three tiers
        if np.isnan(u[i]): continue
        hue = BULL if u[i] >= 0 else BEAR; b = bU[i] if u[i] >= 0 else bD[i]; au = abs(u[i]); pu = 0 if i == 0 or np.isnan(u[i - 1]) else u[i - 1]
        grow = u[i] > pu if u[i] >= 0 else u[i] < pu; out = R2.mU.iloc[i] or R2.mD.iloc[i]
        a.bar(i, np.clip(u[i], -4, 4), color=grad(au, b, 1.5 * b, hue, 18, 0) if out else grad(au, 0, b, hue, 60, 38) if grow else grad(au, 0, b, hue, 88, 62), width=.8)
        ok = not np.isnan(R2.ladX.iloc[i]); lx = R2.ladX.iloc[i]; k = (R2.ladUp.iloc[i] if lx >= 0 else R2.ladDn.iloc[i]) if ok else 0; lean = 0 if (not ok or k < 1) else (1 if lx >= 0 else -1)
        t = T[i]; ts = 2 if t > .5 else 0 if t < -.5 else 1; ta = abs(t); th = BULL if t >= 0 else BEAR
        ph = BULL if ts == 2 else BEAR if ts == 0 else BULL if lean == 1 else BEAR if lean == -1 else th
        wth = (ts == 2 and lean == 1) or (ts == 0 and lean == -1); ag = (ts == 2 and lean == -1) or (ts == 0 and lean == 1)
        cp = tr(NEUT, 80) if not ok else (tr(ph, 55) if lean else grad(ta, 0, .5, ph, 90, 72)) if ts == 1 else grad(ta, .5, 1.5, ph, 18, 0) if wth else tr(ph, 76) if ag else grad(ta, .5, 1.5, ph, 50, 35)
        pr = R2.prk.iloc[i]; rm = np.log(R2.sig.iloc[i] / R.sig.shift(H).iloc[-n:].iloc[i])
        ru = np.nan if np.isnan(pr) else min(max(pr / 100 + (.15 if rm > .1 else -.15 if rm < -.1 else 0), 0), 1)
        cr = tr(NEUT, 80) if np.isnan(ru) else grad(ru, 2 / 3, 1, GOLD, 35, 0) if ru >= 2 / 3 else grad(ru, 0, 2 / 3, GOLD, 88, 55)
        a.bar(i, .9, bottom=4.65, color=cp, width=1.0); a.bar(i, .9, bottom=-5.55, color=cr, width=1.0)
    a.plot(x, bU, color=SOFT, lw=1, alpha=.65); a.plot(x, -bD, color=SOFT, lw=1, alpha=.65); a.axhline(0, color=NEUT, lw=.5, alpha=.4)
    a.text(n + 2, 5.1, "PRICE", color=NEUT, fontsize=7.5, va="center"); a.text(n + 2, -5.1, "RISK", color=GOLD, fontsize=7.5, va="center")
    a.set_ylim(-6.0, 6.0); a.set_ylabel("surprise (σ)", color=NEUT, fontsize=8); a.set_xlim(-2, left + W + 26)
    k = np.arange(0, n, 21); a.set_xticks(k); a.set_xticklabels([d2.index[i].strftime("%b %Y") for i in k])
    fig.savefig(f"../docs/preview_{sym.strip('_').lower()}.png", dpi=110, bbox_inches="tight", facecolor=BG); plt.close(fig)
print("ok")
