"""Reference implementation of maryada.pine. Every number in the README is produced from this file.

The nine-state ledger (st, edge, post, zpost) is computed here for the study only: it found no direction and is not in the script."""
import numpy as np, pandas as pd
from statistics import NormalDist
WARM, RN = 252, 500
AP = (0.75, 0.50, 0.25, 0.10)                                                                # the touch curve's anchors: nearest first
ND = NormalDist()
def ema(x, n): return pd.Series(x).ewm(span=n, adjust=False).mean().values           # ta.ema: alpha 2/(n+1), seeded with the first value
def lag(x, j): return np.r_[np.full(j, np.nan), x[:-j]]
def run(d, H=10, cover=0.80, pstop=0.20, eta=0.02, cap=1.0, floor=0.5, power=1.0, tau=0.10, cost=0.0005, conformal=True, regimes=True, trendf=True, ladf=False, band=0.10):
    """d: DataFrame open/high/low/close. floor=1 -> no trend throttle. Returns every series the script draws."""
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close")); n = len(c)
    lc, lo = np.log(c), np.log(o); r = np.r_[np.nan, np.diff(lc)]
    gp = lo - np.r_[np.nan, lc[:-1]]; co = lc - lo; hl = np.log(h) - np.log(l)
    gk = gp ** 2 + 0.5 * hl ** 2 - (2 * np.log(2) - 1) * co ** 2
    v = np.where((hl > 0) & (gk > 0), gk, r ** 2)                                      # Garman-Klass with the gap; r^2 where the range is absent
    S, M, L, rL = ema(v, 5), ema(v, 22), ema(v, 252), ema(r ** 2, 252)
    k = np.clip(rL / L, 0.5, 2.0)
    sig = np.sqrt(k * (0.25 * S + 0.40 * M + 0.35 * L)); sig[:WARM] = np.nan; sig[~(sig > 0)] = np.nan   # per-bar risk forecast
    slope = 0.5 * np.log(S / L); slope[np.isnan(sig)] = np.nan                         # risk momentum: short-horizon risk over long, log
    # risk regime: ta.percentrank(sig, RN) cut in thirds - each regime keeps its own widths (Mondrian conformal)
    reg = np.ones(n, dtype=int); prk = np.full(n, np.nan)
    if n > RN:
        W = np.lib.stride_tricks.sliding_window_view(sig, RN + 1)
        p = (W[:, :-1] <= W[:, -1:]).sum(axis=1) / RN * 100.0; bad = np.isnan(W).any(axis=1)
        prk[RN:] = np.where(bad, np.nan, p)
        if regimes: reg[RN:] = np.where(bad, 1, np.where(p < 100 / 3, 0, np.where(p < 200 / 3, 1, 2)))
    T = sum((lc - lag(lc, j)) / (sig * np.sqrt(j)) for j in (63, 126, 252)) / 3        # trend, in sigma
    g = floor + (1 - floor) * (0.5 + 0.5 * np.tanh(T))
    # the horizon ladder: every rung settles its own forecast and learns its own widths
    RG = [max(2, H // 2), H, 2 * H, 4 * H]; NR = len(RG)
    U = [(lc - lag(lc, j)) / (lag(sig, j) * np.sqrt(j)) for j in RG]
    sH = sig * np.sqrt(H)
    wS = (np.log(pd.Series(l).rolling(H).min().values) - lag(lc, H)) / lag(sH, H); wR = (np.log(pd.Series(h).rolling(H).max().values) - lag(lc, H)) / lag(sH, H)
    a = (1 - cover) / 2; z0 = NormalDist().inv_cdf(1 - a); s0 = NormalDist().inv_cdf(1 - pstop / 2)
    # learned widths, in logs: one term per risk regime plus one per trend state (and optionally per ladder state), for each side
    lz, ls = np.log(z0), np.log(s0)
    bU = [[lz] * 3 for _ in RG]; bD = [[lz] * 3 for _ in RG]; bS = [ls] * 3; bR = [ls] * 3            # by risk regime
    tU = [[0.0] * 3 for _ in RG]; tD = [[0.0] * 3 for _ in RG]; tS = [0.0] * 3; tR = [0.0] * 3        # by trend state
    dU = [[0.0] * 3 for _ in RG]; dD = [[0.0] * 3 for _ in RG]; dS = [0.0] * 3; dR = [0.0] * 3        # by ladder state
    # the touch curve: for each anchor probability, how far (in sigma) price must be for a touch within H bars to be that likely
    za = [np.log(ND.inv_cdf(1 - p / 2)) for p in AP]
    bA = [[[z] * 3 for z in za] for _ in (0, 1)]; tA = [[[0.0] * 3 for _ in AP] for _ in (0, 1)]       # [side: 0 below, 1 above][anchor][state]
    QA = np.full((2, len(AP), n), np.nan)
    trs = np.where(T > 0.5, 2, np.where(T < -0.5, 0, 1)) if trendf else np.ones(n, dtype=int); lads = np.ones(n, dtype=int)
    QU = np.full((NR, n), np.nan); QD = np.full((NR, n), np.nan); qS = np.full(n, np.nan); qR = np.full(n, np.nan)
    MU = np.zeros((NR, n)); MD = np.zeros((NR, n)); OK = np.zeros((NR, n)); X = np.full((NR, n), np.nan)
    mS = np.zeros(n); mR = np.zeros(n)
    st = np.full(n, -1); y = np.clip((lc - lag(lo, H - 1)) / lag(sH, H), -6, 6)        # ledger outcome: open after the signal bar -> close H bars after it
    cnt = np.zeros(9); mean = np.zeros(9); neff = np.zeros(9); last = np.full(9, -10 ** 9); gn = 0; gm = 0.0; gq = 0.0
    post = np.full(n, np.nan); zpost = np.full(n, np.nan); edge = np.full(n, np.nan)
    for t in range(n):
        for i, j in enumerate(RG):
            if t >= j and not np.isnan(U[i][t]) and not np.isnan(QU[i][t - j]):        # the forecast made j bars ago has now been settled
                qu, qd = QU[i][t - j], QD[i][t - j]; uu = U[i][t]
                MU[i][t] = uu > qu; MD[i][t] = uu < -qd; OK[i][t] = 1; X[i][t] = uu / qu if uu >= 0 else uu / qd
                if conformal:
                    jr, jt, jl = reg[t - j], trs[t - j], lads[t - j]; eu, ed = eta * (MU[i][t] - a), eta * (MD[i][t] - a)
                    bU[i][jr] += eu; bD[i][jr] += ed
                    if trendf: tU[i][jt] += eu; tD[i][jt] += ed
                    if ladf: dU[i][jl] += eu; dD[i][jl] += ed
        if OK[1][t]:
            mS[t] = wS[t] < -qS[t - H]; mR[t] = wR[t] > qR[t - H]
            if conformal:
                jr, jt, jl = reg[t - H], trs[t - H], lads[t - H]; es, er = eta * (mS[t] - pstop), eta * (mR[t] - pstop)
                bS[jr] += es; bR[jr] += er
                if trendf: tS[jt] += es; tR[jt] += er
                if ladf: dS[jl] += es; dR[jl] += er
            for k, p in enumerate(AP):                                                     # settle each anchor on the same path
                if conformal:
                    e0 = eta * ((wS[t] < -QA[0][k][t - H]) - p); e1 = eta * ((wR[t] > QA[1][k][t - H]) - p)
                    bA[0][k][jr] += e0; bA[1][k][jr] += e1
                    if trendf: tA[0][k][jt] += e0; tA[1][k][jt] += e1
            s = st[t - H]
            if s >= 0 and not np.isnan(y[t]):
                cnt[s] += 1; mean[s] += (y[t] - mean[s]) / cnt[s]; gn += 1
                if t - H - last[s] >= H: neff[s] += 1; last[s] = t - H                 # independent samples: signal bars at least H apart
                dlt = y[t] - gm; gm += dlt / gn; gq += dlt * (y[t] - gm)
        if ladf and OK[:, t].sum() == NR: lads[t] = 0 if MD[:, t].sum() >= 3 else 2 if MU[:, t].sum() >= 3 else 1
        if not np.isnan(sig[t]):
            jr, jt, jl = reg[t], trs[t], lads[t]
            for i in range(NR): QU[i][t], QD[i][t] = np.exp(bU[i][jr] + tU[i][jt] + dU[i][jl]), np.exp(bD[i][jr] + tD[i][jt] + dD[i][jl])
            qS[t], qR[t] = np.exp(bS[jr] + tS[jt] + dS[jl]), np.exp(bR[jr] + tR[jt] + dR[jl])
            for k in range(len(AP)): QA[0][k][t] = np.exp(bA[0][k][jr] + tA[0][k][jt]); QA[1][k][t] = np.exp(bA[1][k][jr] + tA[1][k][jt])
        if OK[1][t] and not np.isnan(T[t]):
            st[t] = 3 * (2 if T[t] > 0.5 else 0 if T[t] < -0.5 else 1) + (2 if MU[1][t] else 0 if MD[1][t] else 1)
            s = st[t]
            if neff[s] >= 5 and gn > 30 * H:
                se2 = (gq / (gn - 1)) / neff[s]; B = tau ** 2 / (tau ** 2 + se2); dd = mean[s] - gm
                edge[t] = dd; post[t] = B * dd; zpost[t] = dd * np.sqrt(B / se2)
    # exposure: the instrument's own average risk over its risk now, optionally throttled by trend
    star = np.nancumsum(sig) / np.maximum(np.cumsum(~np.isnan(sig)), 1)
    dialR = np.minimum(cap, (star / sig) ** power); E = dialR * g; E[np.isnan(T)] = np.nan
    if band > 0:                                                                       # act only when the dial has moved by a full step
        held = np.nan
        for t in range(n):
            if not np.isnan(E[t]) and (np.isnan(held) or abs(E[t] - held) >= band): held = E[t]
            E[t] = held if not np.isnan(E[t]) else np.nan
    ret = np.r_[np.nan, c[1:] / c[:-1] - 1]; E2 = lag(E, 2); E3 = lag(E, 3)
    pf = E2 * ret - cost * np.abs(E2 - np.nan_to_num(E3, nan=0.0)); ph = np.where(np.isnan(E2), np.nan, ret)   # decided at close t-2, filled at close t-1
    allok = OK.sum(axis=0) == NR
    out = dict(trs=trs, reg=reg, prk=prk, slope=slope, sig=sig, T=T, u=U[1], qU=QU[1], qD=QD[1], qS=qS, qR=qR, mU=MU[1], mD=MD[1], mS=mS, mR=mR, nF=OK[1], st=st, y=y,
               edge=edge, post=post, zpost=zpost, dialR=dialR, dialT=g, E=E, pf=pf, ph=ph, upper=c * np.exp(QU[1] * sH), lower=c * np.exp(-QD[1] * sH),
               stopL=c * np.exp(-qS * sH), stopS=c * np.exp(qR * sH),
               ladX=np.where(allok, X.mean(axis=0), np.nan), ladUp=np.where(allok, MU.sum(axis=0), np.nan), ladDn=np.where(allok, MD.sum(axis=0), np.nan),
               ladMom=np.where(allok, X[0] - X[NR - 1], np.nan))
    for k in range(len(AP)): out[f"aDn{k}"] = QA[0][k]; out[f"aUp{k}"] = QA[1][k]
    out["sH"] = sH
    for i in range(NR): out[f"u{i}"] = U[i]; out[f"ok{i}"] = OK[i]; out[f"mU{i}"] = MU[i]; out[f"mD{i}"] = MD[i]; out[f"qU{i}"] = QU[i]; out[f"qD{i}"] = QD[i]
    return pd.DataFrame(out, index=d.index)

def _order(a):
    a = [np.asarray(x, float) for x in a]
    for k in range(1, len(a)): a[k] = np.maximum(a[k], a[k - 1] * 1.0001)             # keep the anchors ordered
    return a
ZA = [ND.inv_cdf(1 - p / 2) for p in AP]
def touch_prob(x, *a):
    """Probability that a level x sigma away (x >= 0) is touched within H bars, from the learned anchors (distances at 75, 50, 25, 10%).
    Piecewise linear in z = Phi^-1(1 - p/2) through the origin and the anchors, the last slope carried outward. Vectorised."""
    from scipy.special import ndtr
    a = _order(a); x = np.asarray(x, float); z = ZA[0] * x / a[0]
    for k in range(1, len(a)):
        z = np.where(x > a[k - 1], ZA[k - 1] + (ZA[k] - ZA[k - 1]) * (x - a[k - 1]) / (a[k] - a[k - 1]), z)
    return 2 * (1 - ndtr(z))
def inv_touch(p, *a):
    """Distance (sigma) at which the touch curve reads probability p."""
    a = _order(a); z = ND.inv_cdf(1 - p / 2); x = a[0] * z / ZA[0]
    for k in range(1, len(a)):
        if z > ZA[k - 1]: x = a[k - 1] + (a[k] - a[k - 1]) * (z - ZA[k - 1]) / (ZA[k] - ZA[k - 1])
    return x

def profile(d):
    """Pragati's volume profile on its fallback path (bar range spread uniformly), weekly sessions on daily bars.
    Returns per bar: developing POC/VAH/VAL, prior-session POC/VAH/VAL, and the naked-POC ledger as it stood at the close."""
    h, l, c, v = d.high.values, d.low.values, d.close.values, d.volume.values.astype(float); n = len(c)
    tr = np.maximum(h - l, np.maximum(np.abs(h - np.r_[np.nan, c[:-1]]), np.abs(l - np.r_[np.nan, c[:-1]]))); tr[0] = h[0] - l[0]
    atr = pd.Series(tr).ewm(alpha=1 / 20, adjust=False).mean().values
    usable = np.cumsum(np.nan_to_num(v) > 0) / np.arange(1, n + 1) >= 0.5
    wk = d.index.to_period("W").asi8; new = np.r_[True, wk[1:] != wk[:-1]]
    out = np.full((n, 6), np.nan); naked = [None] * n; led = []; ledx = []
    bins = {}; binw = np.nan; poc = vah = val = np.nan; pp = pv = pl = np.nan; pk = None; pvol = 0.0; tot = 0.0
    for t in range(n):
        led2 = [(y, x) for y, x in zip(led, ledx) if not (h[t] >= y >= l[t])]; led = [y for y, x in led2]; ledx = [x for y, x in led2]
        if new[t]:
            pp, pv, pl = poc, vah, val
            if not np.isnan(pp) and not any(abs(y - pp) <= atr[t] * 0.1 for y in led):
                led.append(pp); ledx.append(t); led, ledx = led[-5:], ledx[-5:]
            bins = {}; tot = 0.0; pk = None; pvol = 0.0; binw = max(atr[t] / 4.0, 1e-12)
        while ledx and t - ledx[0] > 250: led.pop(0); ledx.pop(0)
        bv = 1.0 if not usable[t] else max(np.nan_to_num(v[t]), 0.0)
        kl = int(np.floor(l[t] / binw)); kh = int(np.floor(h[t] / binw)); nb = max(1, min(kh - kl + 1, 200)); per = bv / nb
        for k in range(kl, kl + nb):
            x = bins.get(k, 0.0) + per; bins[k] = x; tot += per
            if x > pvol: pvol = x; pk = k
        if pk is not None:
            ks = sorted(bins); vs = [bins[k] for k in ks]; pi = ks.index(pk); lo = hi = pi; acc = vs[pi]; tgt = tot * 0.70
            while acc < tgt and (lo > 0 or hi < len(ks) - 1):
                vd = vs[lo - 1] if lo > 0 else -1.0; vu = vs[hi + 1] if hi < len(ks) - 1 else -1.0
                if vu >= vd: hi += 1; acc += vu
                else: lo -= 1; acc += vd
            poc, vah, val = (pk + 0.5) * binw, (ks[hi] + 1.0) * binw, ks[lo] * binw
        out[t] = (poc, vah, val, pp, pv, pl); naked[t] = list(led)
    return out, naked, (dict(bins), binw)
