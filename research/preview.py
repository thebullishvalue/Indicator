"""Draws what kasauti.pine draws, from the reference implementation.  python3 preview.py"""
from lib import *
from kasauti import run
import warnings; warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = load(); H = 10
for sym, title in (("_NSEI", "Nifty 50 · daily"), ("AAPL", "Apple · daily")):
    cls, d = D[sym]; R = run(d); n = 170; d2, R2 = d.iloc[-n:], R.iloc[-n:]; x = np.arange(n)
    BG, FG, CONE, UP, DN, NE = "#0D1215", "#C9D1D6", "#5B8FD6", "#3FB980", "#E4776A", "#8A97A0"
    fig, ax = plt.subplots(3, 1, figsize=(13, 9), sharex=True, gridspec_kw=dict(height_ratios=[3, 1.1, 1.1], hspace=0.06), facecolor=BG)
    for a in ax:
        a.set_facecolor(BG); a.tick_params(colors=NE, labelsize=8); [s.set_color("#222a30") for s in a.spines.values()]; a.grid(color="#1a2227", lw=0.5)
    a = ax[0]
    for i in range(n):
        o, h, l, c = d2.open.iloc[i], d2.high.iloc[i], d2.low.iloc[i], d2.close.iloc[i]; col = UP if c >= o else DN
        a.plot([i, i], [l, h], color=col, lw=0.8); a.plot([i, i], [min(o, c), max(o, c)], color=col, lw=3)
    a.plot(x, R.upper.shift(H).iloc[-n:], color=CONE, lw=1, alpha=.6, label="landing band (the cone drawn 10 bars ago)"); a.plot(x, R.lower.shift(H).iloc[-n:], color=CONE, lw=1, alpha=.6)
    a.step(x, R2.stopL, color=DN, lw=.8, alpha=.5, where="post", label="long stop (touched 20% of the time)"); a.step(x, R2.stopS, color=UP, lw=.8, alpha=.5, where="post", label="short stop")
    c, sg, qu, qd = d2.close.iloc[-1], R2.sig.iloc[-1], R2.qU.iloc[-1], R2.qD.iloc[-1]; j = np.arange(H + 1)
    a.fill_between(n - 1 + j, c * np.exp(-qd * sg * np.sqrt(j)), c * np.exp(qu * sg * np.sqrt(j)), color=CONE, alpha=.18, label="forward cone (80%)")
    a.plot([n - 1, n - 1 + H], [R2.stopL.iloc[-1]] * 2, color=DN, ls="--", lw=1); a.plot([n - 1, n - 1 + H], [R2.stopS.iloc[-1]] * 2, color=UP, ls="--", lw=1)
    a.legend(loc="upper left", fontsize=8, facecolor=BG, edgecolor="#222a30", labelcolor=FG); a.set_title(f"Kasauti · {title}   (rendered from research/kasauti.py)", color=FG, fontsize=11, loc="left")
    a = ax[1]; tr = np.where(R2["T"] > .5, UP, np.where(R2["T"] < -.5, DN, NE)); out = ((R2.mU == 1) | (R2.mD == 1)).values
    a.bar(x[~out], R2.u[~out], color=tr[~out], alpha=.45); a.bar(x[out], R2.u[out], color=tr[out]); a.plot(x, R.qU.shift(H).iloc[-n:], color=CONE, lw=1); a.plot(x, -R.qD.shift(H).iloc[-n:], color=CONE, lw=1)
    a.set_ylabel("surprise (σ)", color=NE, fontsize=8)
    a = ax[2]; a.step(x, R2.E, color=CONE, lw=1.6, where="post"); a.axhline(1, color=NE, lw=.6); a.set_ylim(0, 1.1); a.set_ylabel("exposure dial", color=NE, fontsize=8)
    k = np.arange(0, n, 20); a.set_xticks(k); a.set_xticklabels([d2.index[i].strftime("%b %Y") for i in k])
    fig.savefig(f"../docs/preview_{sym.strip('_').lower()}.png", dpi=110, bbox_inches="tight", facecolor=BG); plt.close(fig)
print("ok")
