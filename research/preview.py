"""Draws what kasauti.pine draws, from the reference implementation.  python3 preview.py"""
from lib import *
from kasauti import run
import warnings; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
D = load(); H = 10
BG, FG, CONE, UP, DN, NE, GOLD = "#0D1215", "#C9D1D6", "#5B8FD6", "#3FB980", "#E4776A", "#8A97A0", "#D9B44A"
def grad(x, a, b, c, ta, tb):                                              # colour c, transparency ta -> tb as x runs a -> b (Pine's from_gradient)
    f = min(max((x - a) / (b - a), 0), 1); return to_rgba(c, 1 - (ta + (tb - ta) * f) / 100)
for sym, title in (("_NSEI", "Nifty 50 · daily"), ("AAPL", "Apple · daily")):
    cls, d = D[sym]; R = run(d); n = 190; d2, R2 = d.iloc[-n:], R.iloc[-n:]; x = np.arange(n)
    fig, ax = plt.subplots(2, 1, figsize=(13.5, 9.2), sharex=True, gridspec_kw=dict(height_ratios=[2.5, 1.6], hspace=0.05), facecolor=BG)
    for a in ax:
        a.set_facecolor(BG); a.tick_params(colors=NE, labelsize=8); [s.set_color("#222a30") for s in a.spines.values()]; a.grid(color="#1a2227", lw=0.5)
    a = ax[0]
    for i in range(n):
        o, h, l, c = d2.open.iloc[i], d2.high.iloc[i], d2.low.iloc[i], d2.close.iloc[i]; col = UP if c >= o else DN
        a.plot([i, i], [l, h], color=col, lw=0.8); a.plot([i, i], [min(o, c), max(o, c)], color=col, lw=3)
    a.plot(x, R.upper.shift(H).iloc[-n:], color=CONE, lw=1, alpha=.2, label="landing band · the cone drawn 10 bars ago"); a.plot(x, R.lower.shift(H).iloc[-n:], color=CONE, lw=1, alpha=.2)
    a.plot(x, ((R.upper.shift(H) + R.lower.shift(H)) / 2).iloc[-n:], color=CONE, lw=2, label="midline")
    c, sg, qu, qd = d2.close.iloc[-1], R2.sig.iloc[-1], R2.qU.iloc[-1], R2.qD.iloc[-1]; j = np.arange(H + 1)
    a.fill_between(n - 1 + j, c * np.exp(-qd * sg * np.sqrt(j)), c * np.exp(qu * sg * np.sqrt(j)), color=CONE, alpha=.18, label="forward cone · 80%")
    a.plot([n - 1, n - 1 + H], [R2.stopL.iloc[-1]] * 2, color=DN, ls="--", lw=1, label="long stop · touched 20% of the time"); a.plot([n - 1, n - 1 + H], [R2.stopS.iloc[-1]] * 2, color=UP, ls="--", lw=1, label="short stop")
    a.legend(loc="upper left", fontsize=8, facecolor=BG, edgecolor="#222a30", labelcolor=FG); a.set_title(f"Kasauti · {title}   (rendered from research/kasauti.py, not from TradingView)", color=FG, fontsize=11, loc="left")
    a = ax[1]; tr = np.where(R2.u >= 0, UP, DN); out = ((R2.mU == 1) | (R2.mD == 1)).values; uu = R2.u.clip(-4, 4)
    a.bar(x[~out], uu[~out], color=tr[~out], alpha=.4); a.bar(x[out], uu[out], color=tr[out])
    a.plot(x, R.qU.shift(H).iloc[-n:], color=CONE, lw=1); a.plot(x, -R.qD.shift(H).iloc[-n:], color=CONE, lw=1)
    TY, MY, TH = 4.9, 5.6, 0.28
    for i in range(n):
        T, lx, up, dn, pr, rm = R2["T"].iloc[i], R2.ladX.iloc[i], R2.ladUp.iloc[i], R2.ladDn.iloc[i], R2.prk.iloc[i], np.log(R2.sig.iloc[i] / R.sig.shift(H).iloc[-n:].iloc[i])
        hue = UP if T >= 0 else DN; ct = grad(abs(T), 0, .5, hue, 90, 62) if abs(T) < .5 else grad(abs(T), .5, 1.5, hue, 40, 0)
        if np.isnan(lx): cl = to_rgba(NE, .18)
        else:
            hue = UP if lx >= 0 else DN; k = up if lx >= 0 else dn; cl = to_rgba(hue, 1) if k >= 3 else to_rgba(hue, .6) if k >= 1 else grad(abs(lx), 0, 1, hue, 92, 66)
        cr = to_rgba(NE, .18) if np.isnan(pr) else grad(pr, 0, 100 / 3, CONE, 15, 60) if pr < 100 / 3 else grad(pr, 200 / 3, 100, GOLD, 45, 0) if pr >= 200 / 3 else to_rgba(NE, .3)
        cm = grad(abs(rm), .1, .4, GOLD, 40, 0) if rm > .1 else grad(abs(rm), .1, .4, CONE, 45, 10) if rm < -.1 else to_rgba(NE, .14)
        for yy, cc in ((TY, ct), (MY, cl), (-TY, cr), (-MY, cm)): a.bar(i, 2 * TH, bottom=yy - TH, color=cc, width=1.0)
    for yy, t in ((MY, "STRETCH LADDER"), (TY, "TREND"), (-TY, "RISK"), (-MY, "RISK MOMENTUM")): a.text(n + 1, yy, t, color=NE, fontsize=7.5, va="center")
    a.set_ylim(-6.1, 6.1); a.set_ylabel("surprise (σ)", color=NE, fontsize=8); a.set_xlim(-2, n + 22); ax[0].set_xlim(-2, n + 22)
    k = np.arange(0, n, 21); a.set_xticks(k); a.set_xticklabels([d2.index[i].strftime("%b %Y") for i in k])
    fig.savefig(f"../docs/preview_{sym.strip('_').lower()}.png", dpi=110, bbox_inches="tight", facecolor=BG); plt.close(fig)
print("ok")
