"""Draws what pragyam.pine draws, from the reference implementation: price chart with the volume profile, pane with the tapes.
The profile here is built from daily bars (weekly sessions, each bar's range spread evenly) - TradingView builds it from intrabars.
The table is not drawn.  python3 preview.py"""
from lib import *
from pragyam import run
import warnings; warnings.filterwarnings("ignore")
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
D = load(); H = 10
# the script's dark palette
BG, TEXT, NEUT, CONE = "#0D1215", "#C9D1D6", "#8A97A0", "#B4BEC6"
UP, DN, UPD, DND, GOLD = "#3FB980", "#E4776A", "#2A8660", "#B4554B", "#D9B44A"
POC, VA, VWAP, NODE = "#FFB020", "#5B8FD6", "#F06BA8", "#6E7C88"
SOLID, FIRM, QUIET, FAINT, WARM = 0, 40, 65, 80, 90
CLIP, TY, TH, OY, OH = 3.5, 4.3, 0.40, 5.15, 0.22
VP_W, VP_LEFT, VP_GUT = 24, 4, 1
def tr(c, t): return to_rgba(c, 1 - t / 100)
def grad(x, a, b, c, ta, tb): f = min(max((x - a) / (b - a), 0), 1); return tr(c, ta + (tb - ta) * f)
def profile(d):
    """The session in progress: weekly on daily bars. Bin = ATR(20)/4 frozen at the session's first bar; each bar's volume spread over its range."""
    h, l, c, v = d.high.values, d.low.values, d.close.values, d.volume.values.astype(float)
    trr = np.maximum(h - l, np.maximum(np.abs(h - np.r_[c[0], c[:-1]]), np.abs(l - np.r_[c[0], c[:-1]])))
    atr = pd.Series(trr).ewm(alpha=1 / 20, adjust=False).mean().values
    wk = d.index.to_period("W").asi8; s0 = int(np.flatnonzero(wk == wk[-1])[0]); s1 = int(np.flatnonzero(wk == wk[s0 - 1])[0])
    def build(a, b):
        bw = atr[a] / 4; bins = {}; use = (np.nan_to_num(v) > 0).mean() >= .5
        for t in range(a, b):
            kl, kh = int(np.floor(l[t] / bw)), int(np.floor(h[t] / bw)); nb = max(1, kh - kl + 1); per = (v[t] if use else 1.0) / nb
            for k in range(kl, kl + nb): bins[k] = bins.get(k, 0.0) + per
        ks = sorted(bins); vs = [bins[k] for k in ks]; pi = int(np.argmax(vs)); lo = hi = pi; acc = vs[pi]; tot = sum(vs)
        while acc < .7 * tot and (lo > 0 or hi < len(ks) - 1):
            vd = vs[lo - 1] if lo > 0 else -1; vu = vs[hi + 1] if hi < len(ks) - 1 else -1
            if vu >= vd: hi += 1; acc += vu
            else: lo -= 1; acc += vd
        return dict(bins=bins, bw=bw, poc=(ks[pi] + .5) * bw, vah=(ks[hi] + 1) * bw, val=ks[lo] * bw)
    cur, prev = build(s0, len(c)), build(s1, s0)
    w = np.where(np.nan_to_num(v[s0:]) > 0, v[s0:], 1.0); hlc = (h[s0:] + l[s0:] + c[s0:]) / 3
    cur["vwap"] = np.cumsum(hlc * w) / np.cumsum(w); cur["start"] = s0
    return cur, prev
for sym, title in (("_NSEI", "Nifty 50 · daily"), ("AAPL", "Apple · daily")):
    cls, d = D[sym]; R = run(d); n = 130; off = len(d) - n; d2, R2 = d.iloc[-n:], R.iloc[-n:]; x = np.arange(n); x0 = n - 1
    P, Pp = profile(d)
    fig, ax = plt.subplots(2, 1, figsize=(13.5, 9.4), sharex=True, gridspec_kw=dict(height_ratios=[2.6, 1.5], hspace=0.05), facecolor=BG)
    for a in ax:
        a.set_facecolor(BG); a.tick_params(colors=NEUT, labelsize=8); [s.set_color("#222a30") for s in a.spines.values()]; a.grid(color="#1a2227", lw=0.5)
    a = ax[0]
    # beneath everything: the cone family, quiet neutral
    up_, lo_ = R.upper.shift(H).iloc[-n:], R.lower.shift(H).iloc[-n:]
    a.plot(x, up_, color=tr(CONE, 80), lw=1); a.plot(x, lo_, color=tr(CONE, 80), lw=1); a.plot(x, (up_ + lo_) / 2, color=tr(CONE, 50), lw=1, label="midline")
    c, sg, qu, qd = d2.close.iloc[-1], R2.sig.iloc[-1], R2.qU.iloc[-1], R2.qD.iloc[-1]; j = np.arange(H + 1)
    a.plot(x0 + j, c * np.exp(qu * sg * np.sqrt(j)), color=tr(CONE, 55), lw=1); a.plot(x0 + j, c * np.exp(-qd * sg * np.sqrt(j)), color=tr(CONE, 55), lw=1)
    sl, ss = R2.stopL.iloc[-1], R2.stopS.iloc[-1]; top, bot = max(ss, R2.upper.iloc[-1]), min(sl, R2.lower.iloc[-1])
    a.plot([x0, x0 + H], [sl, sl], color=tr(DN, 50), ls="--", lw=1); a.plot([x0, x0 + H], [ss, ss], color=tr(UP, 50), ls="--", lw=1)
    a.annotate(f"short stop {ss:,.0f}", (x0 + H, top), xytext=(0, 3), textcoords="offset points", color=tr(CONE, 25), fontsize=7, ha="right", va="bottom")
    a.annotate(f"long stop {sl:,.0f}", (x0 + H, bot), xytext=(0, -3), textcoords="offset points", color=tr(CONE, 25), fontsize=7, ha="right", va="top")
    # candles
    for i in range(n):
        o, h, l, cc = d2.open.iloc[i], d2.high.iloc[i], d2.low.iloc[i], d2.close.iloc[i]; col = UP if cc >= o else DN
        a.plot([i, i], [l, h], color=col, lw=0.8); a.plot([i, i], [min(o, cc), max(o, cc)], color=col, lw=3)
    # the volume profile: beside the last bar, at full weight
    left = x0 + VP_LEFT; right = left + VP_W; tagx = right + VP_GUT; bins, bw = P["bins"], P["bw"]; vmax = max(bins.values())
    for k, vv in bins.items():
        mid = (k + .5) * bw; isP = abs(mid - P["poc"]) < bw / 2; inV = P["val"] <= mid <= P["vah"]
        a.barh(k * bw, VP_W * vv / vmax, height=bw * .85, left=left, align="edge", color=tr(POC, 25) if isP else tr(VA, 48) if inV else tr(NODE, 72), lw=0)
    xs = max(P["start"] - off, 0)
    a.fill_between([xs, x0], P["val"], P["vah"], color=tr(VA, 93), lw=0)
    a.plot([xs, tagx], [P["poc"]] * 2, color=POC, lw=2); a.plot([xs, tagx], [P["vah"]] * 2, color=tr(VA, 20), lw=1); a.plot([xs, tagx], [P["val"]] * 2, color=tr(VA, 20), lw=1)
    for yy, cc in ((Pp["poc"], POC), (Pp["vah"], VA), (Pp["val"], VA)): a.plot([xs, tagx], [yy] * 2, color=tr(cc, 55), lw=1, ls=":")
    vw = P["vwap"]; a.plot(np.arange(P["start"] - off, n), vw, color=VWAP, lw=1, label="VWAP"); a.plot([x0, tagx], [vw[-1]] * 2, color=tr(VWAP, 45), lw=1)
    seated = []; gap = (d2.high.max() - d2.low.min()) * 0.02
    for yy, t, cc in ((P["poc"], "POC", POC), (P["vah"], "VAH", VA), (P["val"], "VAL", VA), (vw[-1], "VWAP", VWAP), (Pp["poc"], "pPOC", POC), (Pp["vah"], "pVAH", VA), (Pp["val"], "pVAL", VA)):
        if all(abs(yy - s) >= gap for s in seated): seated.append(yy); a.text(tagx + 1, yy, f"{t} {yy:,.0f}", color=cc, fontsize=7.5, va="center", bbox=dict(facecolor=tr(cc, 88), edgecolor="none", pad=1.2))
    a.legend(loc="upper left", fontsize=8, facecolor=BG, edgecolor="#222a30", labelcolor=TEXT)
    a.set_title(f"Pragyam · {title}   (rendered from research/pragyam.py, not from TradingView)", color=TEXT, fontsize=10.5, loc="left")
    lo, hi = min(d2.low.min(), bot), max(d2.high.max(), top); a.set_ylim(lo - (hi - lo) * .04, hi + (hi - lo) * .05)
    # ---------------- the pane ----------------
    a = ax[1]; u = R2.u.values; T = R2["T"].values; bU = R.qU.shift(H).iloc[-n:].values; bD = R.qD.shift(H).iloc[-n:].values; sgH = R.sig.shift(H).iloc[-n:].values
    for i in range(n):
        if not np.isnan(u[i]):
            ts = 2 if T[i] > .5 else 0 if T[i] < -.5 else 1; wth = (u[i] >= 0 and ts == 2) or (u[i] < 0 and ts == 0); out = R2.mU.iloc[i] or R2.mD.iloc[i]; hue = (UP if u[i] >= 0 else DN) if wth else NEUT
            a.bar(i, np.clip(u[i], -CLIP, CLIP), color=tr(hue if wth else TEXT, SOLID) if out else tr(hue, QUIET if wth else FAINT), width=.8)
        t = T[i]; ta = abs(t); th = UPD if t >= 0 else DND
        ct = tr(NEUT, WARM) if np.isnan(t) else grad(ta, 0, .5, th, WARM, QUIET) if ta < .5 else grad(ta, .5, 1.5, th, 30, SOLID)
        lx = R2.ladX.iloc[i]; ok = not np.isnan(lx); k = (R2.ladUp.iloc[i] if lx >= 0 else R2.ladDn.iloc[i]) if ok else 0; lh = UP if (ok and lx >= 0) else DN
        cl = tr(NEUT, WARM) if not ok else tr(lh, SOLID) if k >= 3 else tr(lh, 72) if k >= 1 else grad(abs(lx), 0, 1, lh, WARM, 82)
        pr = R2.prk.iloc[i]; rm = np.log(R2.sig.iloc[i] / sgH[i])
        cr = tr(NEUT, WARM) if np.isnan(pr) else grad(pr, 200 / 3, 100, GOLD, FIRM, SOLID) if pr >= 200 / 3 else grad(pr, 100 / 3, 200 / 3, GOLD, QUIET, 55) if pr >= 100 / 3 else grad(pr, 0, 100 / 3, GOLD, 95, 86)
        cm = tr(NEUT, WARM) if np.isnan(rm) else grad(abs(rm), .1, .4, GOLD, QUIET, FIRM) if rm > .1 else grad(abs(rm), .1, .4, NEUT, QUIET, 50) if rm < -.1 else tr(NEUT, FAINT)
        for yy, hh, cc in ((TY, TH, ct), (OY, OH, cl), (-TY, TH, cr), (-OY, OH, cm)): a.bar(i, 2 * hh, bottom=yy - hh, color=cc, width=1.0)
    a.plot(x, np.minimum(bU, CLIP), color=tr(CONE, 40), lw=1); a.plot(x, np.maximum(-bD, -CLIP), color=tr(CONE, 40), lw=1); a.axhline(0, color=tr(NEUT, 55), lw=.6, ls=":")
    for yy, t in ((OY, "LADDER"), (TY, "TREND"), (-TY, "RISK"), (-OY, "MOMENTUM")): a.text(n + 1, yy, t, color=NEUT, fontsize=7.5, va="center")
    a.set_ylim(-5.7, 5.7); a.set_ylabel("surprise (σ)", color=NEUT, fontsize=8)
    for a in ax: a.set_xlim(-2, tagx + 14)
    kk = np.arange(0, n, 21); ax[1].set_xticks(kk); ax[1].set_xticklabels([d2.index[i].strftime("%b %Y") for i in kk])
    fig.savefig(f"../docs/preview_{sym.strip('_').lower()}.png", dpi=110, bbox_inches="tight", facecolor=BG); plt.close(fig)
print("ok")
