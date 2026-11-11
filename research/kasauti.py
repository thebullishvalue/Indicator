"""Reference implementation of kasauti.pine, bar for bar. Every number in the README is produced from this file."""
import numpy as np, pandas as pd
from statistics import NormalDist
WARM = 252
def ema(x, n): return pd.Series(x).ewm(span=n, adjust=False).mean().values           # ta.ema: alpha 2/(n+1), seeded with the first value
def run(d, H=10, cover=0.80, pstop=0.20, eta=0.02, cap=1.0, floor=0.5, tau=0.10, cost=0.0005, conformal=True, regimes=True, RN=500):
    """d: DataFrame open/high/low/close. floor=1 -> no trend throttle. Returns a DataFrame of every series the script draws."""
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close")); n = len(c)
    lc, lo = np.log(c), np.log(o); r = np.r_[np.nan, np.diff(lc)]
    on = lo - np.r_[np.nan, lc[:-1]]; co = lc - lo; hl = np.log(h) - np.log(l)
    gk = on ** 2 + 0.5 * hl ** 2 - (2 * np.log(2) - 1) * co ** 2
    v = np.where((hl > 0) & (gk > 0), gk, r ** 2)                                      # Garman-Klass with the gap; r^2 where the range is absent
    S, M, L, rL = ema(v, 5), ema(v, 22), ema(v, 252), ema(r ** 2, 252)
    k = np.clip(rL / L, 0.5, 2.0)
    sig = np.sqrt(k * (0.25 * S + 0.40 * M + 0.35 * L)); sig[:WARM] = np.nan; sig[~(sig > 0)] = np.nan   # per-bar risk forecast
    sH = sig * np.sqrt(H)
    def lag(x, j): return np.r_[np.full(j, np.nan), x[:-j]]
    T = sum((lc - lag(lc, j)) / (sig * np.sqrt(j)) for j in (63, 126, 252)) / 3        # trend, in sigma
    g = floor + (1 - floor) * (0.5 + 0.5 * np.tanh(T))
    lowH = pd.Series(l).rolling(H).min().values; highH = pd.Series(h).rolling(H).max().values
    u = (lc - lag(lc, H)) / lag(sH, H)                                                 # the surprise: realised H-bar move / forecast made H bars ago
    wS = (np.log(lowH) - lag(lc, H)) / lag(sH, H); wR = (np.log(highH) - lag(lc, H)) / lag(sH, H)
    z0 = NormalDist().inv_cdf(1 - (1 - cover) / 2); s0 = NormalDist().inv_cdf(1 - pstop / 2); a = (1 - cover) / 2
    # risk regime: ta.percentrank(sig, RN) cut in thirds - each regime keeps its own multipliers (Mondrian conformal)
    reg = np.ones(n, dtype=int)
    if regimes:
        W = np.lib.stride_tricks.sliding_window_view(sig, RN + 1)                      # rows end at t = RN .. n-1
        pr = (W[:, :-1] <= W[:, -1:]).sum(axis=1) / RN * 100.0; bad = np.isnan(W).any(axis=1)
        reg[RN:] = np.where(bad, 1, np.where(pr < 100 / 3, 0, np.where(pr < 200 / 3, 1, 2)))
    qU, qD, qS, qR = (np.full(n, np.nan) for _ in range(4)); cu, cd, cs, cr = ([z0] * 3, [z0] * 3, [s0] * 3, [s0] * 3)
    mU, mD, mS, mR = (np.zeros(n) for _ in range(4)); nF = np.zeros(n)
    st = np.full(n, -1); y = np.clip((lc - lag(lo, H - 1)) / lag(sH, H), -6, 6)                       # ledger outcome: open after the signal bar -> close H bars after it
    cnt = np.zeros(9); mean = np.zeros(9); neff = np.zeros(9); last = np.full(9, -10 ** 9); gn = 0; gm = 0.0; gq = 0.0
    post = np.full(n, np.nan); zpost = np.full(n, np.nan); edge = np.full(n, np.nan); ncell = np.zeros(n)
    for t in range(n):
        if t >= H and not np.isnan(u[t]) and not np.isnan(qU[t - H]):                  # the forecast made H bars ago has now been settled
            mU[t] = u[t] > qU[t - H]; mD[t] = u[t] < -qD[t - H]; mS[t] = wS[t] < -qS[t - H]; mR[t] = wR[t] > qR[t - H]; nF[t] = 1
            if conformal:
                j = reg[t - H]
                cu[j] *= np.exp(eta * (mU[t] - a)); cd[j] *= np.exp(eta * (mD[t] - a)); cs[j] *= np.exp(eta * (mS[t] - pstop)); cr[j] *= np.exp(eta * (mR[t] - pstop))
            s = st[t - H]
            if s >= 0 and not np.isnan(y[t]):
                cnt[s] += 1; mean[s] += (y[t] - mean[s]) / cnt[s]; gn += 1
                if t - H - last[s] >= H: neff[s] += 1; last[s] = t - H               # independent samples: signal bars at least H apart
                dlt = y[t] - gm; gm += dlt / gn; gq += dlt * (y[t] - gm)
        if not np.isnan(sig[t]): qU[t], qD[t], qS[t], qR[t] = cu[reg[t]], cd[reg[t]], cs[reg[t]], cr[reg[t]]
        if nF[t] and not np.isnan(T[t]):
            st[t] = 3 * (2 if T[t] > 0.5 else 0 if T[t] < -0.5 else 1) + (2 if mU[t] else 0 if mD[t] else 1)
            s = st[t]; ncell[t] = cnt[s]
            if neff[s] >= 5 and gn > 30 * H:
                se2 = (gq / (gn - 1)) / neff[s]; B = tau ** 2 / (tau ** 2 + se2); dd = mean[s] - gm
                edge[t] = dd; post[t] = B * dd; zpost[t] = dd * np.sqrt(B / se2)
    # exposure: risk parity to the instrument's own average risk, optionally throttled by trend
    star = np.nancumsum(sig) / np.maximum(np.cumsum(~np.isnan(sig)), 1)
    E = np.minimum(cap, star / sig) * g; E[np.isnan(T)] = np.nan
    ret = np.r_[np.nan, c[1:] / c[:-1] - 1]; E2 = lag(E, 2); E3 = lag(E, 3)
    pf = E2 * ret - cost * np.abs(E2 - np.nan_to_num(E3, nan=0.0)); ph = np.where(np.isnan(E2), np.nan, ret)   # decided at close t-2, filled at close t-1
    return pd.DataFrame(dict(reg=reg, sig=sig, T=T, u=u, qU=qU, qD=qD, qS=qS, qR=qR, mU=mU, mD=mD, mS=mS, mR=mR, nF=nF, st=st, y=y,
                             edge=edge, post=post, zpost=zpost, ncell=ncell, E=E, pf=pf, ph=ph, upper=c * np.exp(qU * sH), lower=c * np.exp(-qD * sH),
                             stopL=c * np.exp(-qS * sH), stopS=c * np.exp(qR * sH)), index=d.index)
