"""Pragyam HPO - the reference implementation with its constants as arguments, plus loaders and splits.

run_p() is research/pragyam.py's run() verbatim, except that the risk forecast's EMA spans, blend weights
and k clip, and the trend's lookbacks, are arguments. With defaults it reproduces run() exactly
(check_equal() asserts it).
"""
import os, sys, glob
import numpy as np, pandas as pd
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, RESEARCH)
import pragyam as P                                      # noqa: E402

WARM, RN = 252, 500
ema, lag = P.ema, P.lag
SPLIT_DAILY = pd.Timestamp("2016-01-01")
DEF = dict(spans=(5, 22, 252), w=(0.25, 0.40, 0.35), kclip=(0.5, 2.0), tlb=(63, 126, 252))


def sigma(d, spans=DEF["spans"], w=DEF["w"], kclip=DEF["kclip"]):
    """The per-bar risk forecast, exactly as run() builds it, with its constants as arguments."""
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
    lc, lo = np.log(c), np.log(o); r = np.r_[np.nan, np.diff(lc)]
    gp = lo - np.r_[np.nan, lc[:-1]]; co = lc - lo; hl = np.log(h) - np.log(l)
    gk = gp ** 2 + 0.5 * hl ** 2 - (2 * np.log(2) - 1) * co ** 2
    v = np.where((hl > 0) & (gk > 0), gk, r ** 2)
    S, M, L, rL = ema(v, spans[0]), ema(v, spans[1]), ema(v, spans[2]), ema(r ** 2, 252)
    k = np.clip(rL / L, *kclip) if kclip is not None else np.ones_like(L)
    sig = np.sqrt(k * (w[0] * S + w[1] * M + w[2] * L)); sig[:WARM] = np.nan; sig[~(sig > 0)] = np.nan
    return sig, S, L


def run_p(d, H=10, cover=0.80, pstop=0.20, eta=0.02, cap=1.0, floor=0.5, power=1.0, tau=0.10, cost=0.0005,
          conformal=True, regimes=True, trendf=True, ladf=False, band=0.10,
          spans=DEF["spans"], w=DEF["w"], kclip=DEF["kclip"], tlb=DEF["tlb"]):
    """research/pragyam.py run(), constants as arguments. Returns the same DataFrame."""
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close")); n = len(c)
    lc = np.log(c)
    sig, S, L = sigma(d, spans, w, kclip)
    slope = 0.5 * np.log(S / L); slope[np.isnan(sig)] = np.nan
    reg = np.ones(n, dtype=int); prk = np.full(n, np.nan)
    if n > RN:
        W = np.lib.stride_tricks.sliding_window_view(sig, RN + 1)
        p = (W[:, :-1] <= W[:, -1:]).sum(axis=1) / RN * 100.0; bad = np.isnan(W).any(axis=1)
        prk[RN:] = np.where(bad, np.nan, p)
        if regimes: reg[RN:] = np.where(bad, 1, np.where(p < 100 / 3, 0, np.where(p < 200 / 3, 1, 2)))
    T = sum((lc - lag(lc, j)) / (sig * np.sqrt(j)) for j in tlb) / len(tlb)
    g = floor + (1 - floor) * (0.5 + 0.5 * np.tanh(T))
    RG = [max(2, H // 2), H, 2 * H, 4 * H]; NR = len(RG)
    U = [(lc - lag(lc, j)) / (lag(sig, j) * np.sqrt(j)) for j in RG]
    sH = sig * np.sqrt(H)
    wS = (np.log(pd.Series(l).rolling(H).min().values) - lag(lc, H)) / lag(sH, H); wR = (np.log(pd.Series(h).rolling(H).max().values) - lag(lc, H)) / lag(sH, H)
    a = (1 - cover) / 2; z0 = NormalDist().inv_cdf(1 - a); s0 = NormalDist().inv_cdf(1 - pstop / 2)
    lz, ls = np.log(z0), np.log(s0)
    bU = [[lz] * 3 for _ in RG]; bD = [[lz] * 3 for _ in RG]; bS = [ls] * 3; bR = [ls] * 3
    tU = [[0.0] * 3 for _ in RG]; tD = [[0.0] * 3 for _ in RG]; tS = [0.0] * 3; tR = [0.0] * 3
    dU = [[0.0] * 3 for _ in RG]; dD = [[0.0] * 3 for _ in RG]; dS = [0.0] * 3; dR = [0.0] * 3
    trs = np.where(T > 0.5, 2, np.where(T < -0.5, 0, 1)) if trendf else np.ones(n, dtype=int); lads = np.ones(n, dtype=int)
    QU = np.full((NR, n), np.nan); QD = np.full((NR, n), np.nan); qS = np.full(n, np.nan); qR = np.full(n, np.nan)
    MU = np.zeros((NR, n)); MD = np.zeros((NR, n)); OK = np.zeros((NR, n)); X = np.full((NR, n), np.nan)
    mS = np.zeros(n); mR = np.zeros(n)
    for t in range(n):
        for i, j in enumerate(RG):
            if t >= j and not np.isnan(U[i][t]) and not np.isnan(QU[i][t - j]):
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
        if ladf and OK[:, t].sum() == NR: lads[t] = 0 if MD[:, t].sum() >= 3 else 2 if MU[:, t].sum() >= 3 else 1
        if not np.isnan(sig[t]):
            jr, jt, jl = reg[t], trs[t], lads[t]
            for i in range(NR): QU[i][t], QD[i][t] = np.exp(bU[i][jr] + tU[i][jt] + dU[i][jl]), np.exp(bD[i][jr] + tD[i][jt] + dD[i][jl])
            qS[t], qR[t] = np.exp(bS[jr] + tS[jt] + dS[jl]), np.exp(bR[jr] + tR[jt] + dR[jl])
    star = np.nancumsum(sig) / np.maximum(np.cumsum(~np.isnan(sig)), 1)
    dialR = np.minimum(cap, (star / sig) ** power); E = dialR * g; E[np.isnan(T)] = np.nan
    if band > 0:
        held = np.nan
        for t in range(n):
            if not np.isnan(E[t]) and (np.isnan(held) or abs(E[t] - held) >= band): held = E[t]
            E[t] = held if not np.isnan(E[t]) else np.nan
    ret = np.r_[np.nan, c[1:] / c[:-1] - 1]; E2 = lag(E, 2); E3 = lag(E, 3)
    pf = E2 * ret - cost * np.abs(E2 - np.nan_to_num(E3, nan=0.0)); ph = np.where(np.isnan(E2), np.nan, ret)
    return pd.DataFrame(dict(sig=sig, T=T, reg=reg, u=U[1], qU=QU[1], qD=QD[1], mU=MU[1], mD=MD[1], mS=mS, mR=mR,
                             nF=OK[1], E=E, pf=pf, ph=ph), index=d.index)


def risk_regime(sig):
    """The risk regime (0 calm, 1 normal, 2 stressed) exactly as run() labels it with regimes on - computed here so
    every config, including those that do not adapt to it, is judged by the same yardstick."""
    n = len(sig); reg = np.ones(n, dtype=int)
    if n > RN:
        W = np.lib.stride_tricks.sliding_window_view(sig, RN + 1)
        p = (W[:, :-1] <= W[:, -1:]).sum(axis=1) / RN * 100.0; bad = np.isnan(W).any(axis=1)
        reg[RN:] = np.where(bad, 1, np.where(p < 100 / 3, 0, np.where(p < 200 / 3, 1, 2)))
    return reg


def check_equal(d):
    a, b = P.run(d), run_p(d)
    for col in ("sig", "T", "reg", "u", "qU", "qD", "mS", "mR", "E", "pf"):
        x, y = a[col].to_numpy(float), b[col].to_numpy(float)
        assert np.allclose(x, y, equal_nan=True, rtol=0, atol=1e-12), col
    return True


def _clean(d):
    d = d[(d.close > 0) & (d.high >= d.low)].copy()
    d["open"] = d.open.where((d.open > 0) & (np.log(d.open / d.close).abs() < 0.3), d.close)
    return d[d.close.pct_change().abs().fillna(0) < 0.6]


def load(ds, fresh_d=None, fresh_h=None, hold_d=None, hold_h=None):
    """{symbol: (class, frame)} for RD / RH (research), FD / FH (fresh), HD / HH (the sealed universe)."""
    if ds in ("RD", "RH"):
        cwd = os.getcwd(); os.chdir(RESEARCH)
        from lib import load as lload
        D = lload("data1h" if ds == "RH" else "data", 2500 if ds == "RH" else 1500)
        os.chdir(cwd)
        return D
    src = {"FD": fresh_d, "FH": fresh_h, "HD": hold_d, "HH": hold_h}[ds]
    out = {}
    for fn in sorted(glob.glob(os.path.join(src, "*.csv"))):
        m, t = os.path.basename(fn)[:-4].split("__", 1)
        d = _clean(pd.read_csv(fn, index_col=0, parse_dates=True))
        if len(d) >= 1500:
            out[t] = (m, d)
    return out


def split_of(index, ds, hourly_cut=None):
    """'tune' / 'validate' per bar: before / after 2016 on daily data; the first / second half of dates hourly."""
    idx = pd.DatetimeIndex(index)
    cut = SPLIT_DAILY if ds in ("RD", "FD", "HD") else hourly_cut
    return np.where(idx < cut, "tune", "validate")
