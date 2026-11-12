"""Draws what pragyam.pine draws, from the reference implementation (the volume profile and table are not drawn).  python3 preview.py"""
from lib import *
from pragyam import run
import warnings; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
D = load(); H = 10
BG, TEXT, CONE, UP, DN, UPD, DND, NE, GOLD = "#0D1215", "#C9D1D6", "#5B8FD6", "#4FCB9B", "#E5533C", "#1A9498", "#B85068", "#8A97A0", "#F0C54E"   # the script's dark palette
SOLID, FIRM, QUIET, FAINT, WARM = 0, 40, 65, 80, 90                                                                                      # its transparency ladder
CLIP, TY, TH, OY, OH = 3.5, 4.3, 0.40, 5.15, 0.22
def tr(c, t): return to_rgba(c, 1 - t / 100)
def grad(x, a, b, c, ta, tb): f = min(max((x - a) / (b - a), 0), 1); return tr(c, ta + (tb - ta) * f)
for sym, title in (("_NSEI", "Nifty 50 · daily"), ("AAPL", "Apple · daily")):
    cls, d = D[sym]; R = run(d); n = 170; d2, R2 = d.iloc[-n:], R.iloc[-n:]; x = np.arange(n)
    fig, ax = plt.subplots(2, 1, figsize=(13.5, 9.2), sharex=True, gridspec_kw=dict(height_ratios=[2.5, 1.6], hspace=0.05), facecolor=BG)
    for a in ax:
        a.set_facecolor(BG); a.tick_params(colors=NE, labelsize=8); [s.set_color("#222a30") for s in a.spines.values()]; a.grid(color="#1a2227", lw=0.5)
    a = ax[0]
    for i in range(n):
        o, h, l, c = d2.open.iloc[i], d2.high.iloc[i], d2.low.iloc[i], d2.close.iloc[i]; col = UP if c >= o else DN
        a.plot([i, i], [l, h], color=col, lw=0.8); a.plot([i, i], [min(o, c), max(o, c)], color=col, lw=3)
    up_, lo_ = R.upper.shift(H).iloc[-n:], R.lower.shift(H).iloc[-n:]
    a.plot(x, up_, color=tr(CONE, 70), lw=1, label="landing band"); a.plot(x, lo_, color=tr(CONE, 70), lw=1); a.plot(x, (up_ + lo_) / 2, color=tr(CONE, 45), lw=1, label="midline")
    c, sg, qu, qd = d2.close.iloc[-1], R2.sig.iloc[-1], R2.qU.iloc[-1], R2.qD.iloc[-1]; j = np.arange(H + 1); x0 = n - 1
    a.fill_between(x0 + j, c * np.exp(-qd * sg * np.sqrt(j)), c * np.exp(qu * sg * np.sqrt(j)), color=tr(CONE, 86), lw=0)
    a.plot(np.r_[x0 + j, (x0 + j)[::-1], x0], np.r_[c * np.exp(qu * sg * np.sqrt(j)), (c * np.exp(-qd * sg * np.sqrt(j)))[::-1], c], color=CONE, lw=2, label="forward cone · 80%")
    sl, ss = R2.stopL.iloc[-1], R2.stopS.iloc[-1]; top, bot = max(ss, R2.upper.iloc[-1]), min(sl, R2.lower.iloc[-1])
    a.plot([x0, x0 + H], [sl, sl], color=DN, ls="--", lw=2); a.plot([x0, x0 + H], [ss, ss], color=UP, ls="--", lw=2)
    a.annotate(f"SHORT STOP {ss:,.0f}", (x0 + H, top), xytext=(0, 5), textcoords="offset points", color=UP, fontsize=8.5, ha="right", va="bottom")
    a.annotate(f"LONG STOP {sl:,.0f}", (x0 + H, bot), xytext=(0, -5), textcoords="offset points", color=DN, fontsize=8.5, ha="right", va="top")
    a.legend(loc="upper left", fontsize=8, facecolor=BG, edgecolor="#222a30", labelcolor=TEXT)
    a.set_title(f"Pragyam · {title}   (rendered from research/pragyam.py, not from TradingView; profile and table not shown)", color=TEXT, fontsize=10.5, loc="left")
    lo, hi = min(d2.low.min(), bot), max(d2.high.max(), top); a.set_ylim(lo - (hi - lo) * .05, hi + (hi - lo) * .07)
    a = ax[1]; u = R2.u.values; T = R2["T"].values; bU = R.qU.shift(H).iloc[-n:].values; bD = R.qD.shift(H).iloc[-n:].values; sgH = R.sig.shift(H).iloc[-n:].values
    for i in range(n):
        if not np.isnan(u[i]):                                             # columns: opacity is the event, hue is whether the trend backs it
            ts = 2 if T[i] > .5 else 0 if T[i] < -.5 else 1; wth = (u[i] >= 0 and ts == 2) or (u[i] < 0 and ts == 0); out = R2.mU.iloc[i] or R2.mD.iloc[i]; hue = (UP if u[i] >= 0 else DN) if wth else NE
            a.bar(i, np.clip(u[i], -CLIP, CLIP), color=tr(hue if wth else TEXT, SOLID) if out else tr(hue, QUIET if wth else FAINT), width=.8)
        t = T[i]; ta = abs(t); th = UPD if t >= 0 else DND
        ct = tr(NE, WARM) if np.isnan(t) else grad(ta, 0, .5, th, WARM, QUIET) if ta < .5 else grad(ta, .5, 1.5, th, FIRM, SOLID)
        lx = R2.ladX.iloc[i]; ok = not np.isnan(lx); k = (R2.ladUp.iloc[i] if lx >= 0 else R2.ladDn.iloc[i]) if ok else 0; lh = UP if (ok and lx >= 0) else DN
        cl = tr(NE, WARM) if not ok else tr(lh, FIRM) if k >= 3 else tr(lh, QUIET) if k >= 1 else grad(abs(lx), 0, 1, lh, WARM, FAINT)
        pr = R2.prk.iloc[i]; rm = np.log(R2.sig.iloc[i] / sgH[i])
        cr = tr(NE, WARM) if np.isnan(pr) else grad(pr, 200 / 3, 100, GOLD, FIRM, SOLID) if pr >= 200 / 3 else grad(pr, 100 / 3, 200 / 3, GOLD, QUIET, 55) if pr >= 100 / 3 else grad(pr, 0, 100 / 3, GOLD, WARM, FAINT)
        cm = tr(NE, WARM) if np.isnan(rm) else grad(abs(rm), .1, .4, GOLD, QUIET, FIRM) if rm > .1 else grad(abs(rm), .1, .4, NE, QUIET, 50) if rm < -.1 else tr(NE, FAINT)
        for yy, hh, cc in ((TY, TH, ct), (OY, OH, cl), (-TY, TH, cr), (-OY, OH, cm)): a.bar(i, 2 * hh, bottom=yy - hh, color=cc, width=1.0)
    a.plot(x, np.minimum(bU, CLIP), color=tr(CONE, 30), lw=1); a.plot(x, np.maximum(-bD, -CLIP), color=tr(CONE, 30), lw=1); a.axhline(0, color=tr(NE, 55), lw=.6, ls=":")
    for yy, t in ((OY, "LADDER"), (TY, "TREND"), (-TY, "RISK"), (-OY, "MOMENTUM")): a.text(n + 1, yy, t, color=NE, fontsize=7.5, va="center")
    a.set_ylim(-5.7, 5.7); a.set_ylabel("surprise (σ)", color=NE, fontsize=8); a.set_xlim(-2, n + 20); ax[0].set_xlim(-2, n + 20)
    k = np.arange(0, n, 21); a.set_xticks(k); a.set_xticklabels([d2.index[i].strftime("%b %Y") for i in k])
    fig.savefig(f"../docs/preview_{sym.strip('_').lower()}.png", dpi=110, bbox_inches="tight", facecolor=BG); plt.close(fig)
print("ok")
