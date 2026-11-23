"""Pramana's engine, ported from pramana.pine section by section, bar for bar.

Every series the script draws, every number its table prints and every alert it raises is computed here,
in the order the script computes it. Pine's semantics are kept where they decide a value:

    ta.ema         seeded with the first non-na value; na inputs are skipped
    ta.percentrank share of the previous `length` values <= the current one; any na in the window gives na
    ta.sma         na inputs are skipped (the mean of the last `length` non-na values)
    ta.lowest/highest  na inputs are skipped
    comparisons    with na are false; math.min / math.max with na give na
    calc_bars_count = 5000: the script runs on the last 5,000 bars, so the caller passes at most that many

Section numbers follow the script's.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

WARM = 252
RN = 500
CALC_BARS = 5000
NAN = float("nan")


@dataclass
class Inputs:
    """Every input of pramana.pine, with the script's defaults. Names follow the script."""
    # 1 · Display
    pane: str = "Surprise"              # "Surprise" | "Proof"
    tapes: bool = True
    cone: bool = False
    land: bool = True
    mid: bool = True
    mid_marks: bool = False
    trail: bool = False
    table: bool = False
    table_pos: str = "Bottom left"
    marks: bool = True
    theme: str = "Auto"                 # "Auto" | "Light" | "Dark"
    # 2 · Forecast
    H: int = 10
    cover: float = 80.0
    stop: float = 20.0
    risk: float = 1.0
    # 3 · Exposure
    mode: str = "Risk × trend"          # "Risk × trend" | "Risk only"
    cap: float = 1.0
    # 4 · Advanced
    eta: float = 0.02
    reg: bool = True
    trend_f: bool = True
    floor: float = 0.5
    step: float = 0.10
    cost: float = 5.0
    tau: float = 0.10
    # 5 · Volume profile
    vp: bool = True
    vp_intrabar: bool = True
    vp_use_vol: bool = True
    vp_bin_mode: str = "ATR adaptive"   # "ATR adaptive" | "Fixed ticks"
    vp_bins_per_atr: float = 4.0
    vp_bin_ticks: int = 20
    vp_va_pct: float = 0.70
    vp_histogram: bool = True
    vp_style: str = "Monochrome"        # "Monochrome" | "Delta split"
    vp_width: int = 24
    vp_nodes: bool = True
    vp_va: bool = True
    vp_poc: bool = True
    vp_trail: bool = False
    vp_prev: bool = True
    vp_naked: bool = True
    vp_naked_max: int = 5
    vp_naked_age: int = 250
    vp_vwap: bool = True
    vp_ib: bool = True
    vp_ib_bars: int = 12

    def as_dict(self) -> dict:
        return asdict(self)


# ── Pine built-ins ─────────────────────────────────────────────────────────────
def pine_ema(x: np.ndarray, n: int) -> np.ndarray:
    a = 2.0 / (n + 1.0)
    out = np.full(len(x), NAN)
    s = NAN
    for i, v in enumerate(x):
        if not math.isnan(v):
            s = v if math.isnan(s) else a * v + (1.0 - a) * s
        out[i] = s
    return out


def pine_rma(x: np.ndarray, n: int) -> np.ndarray:
    """ta.rma: seeded with the SMA of the first n non-na values."""
    a = 1.0 / n
    out = np.full(len(x), NAN)
    s = NAN
    seed: list[float] = []
    for i, v in enumerate(x):
        if not math.isnan(v):
            if math.isnan(s):
                seed.append(v)
                if len(seed) == n:
                    s = sum(seed) / n
            else:
                s = a * v + (1.0 - a) * s
        out[i] = s
    return out


def pine_atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    pc = np.r_[NAN, c[:-1]]
    with np.errstate(invalid="ignore"):
        tr = np.where(np.isnan(pc), h - l, np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc))))
    return pine_rma(tr, n)


def pine_percentrank(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), NAN)
    if len(x) > n:
        W = np.lib.stride_tricks.sliding_window_view(x, n + 1)
        with np.errstate(invalid="ignore"):
            p = (W[:, :-1] <= W[:, -1:]).sum(axis=1) / n * 100.0
        bad = np.isnan(W).any(axis=1)
        out[n:] = np.where(bad, NAN, p)
    return out


def pine_lowest(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n, min_periods=1).min().to_numpy()


def pine_highest(x: np.ndarray, n: int) -> np.ndarray:
    return pd.Series(x).rolling(n, min_periods=1).max().to_numpy()


def lag(x: np.ndarray, j: int) -> np.ndarray:
    if j <= 0:
        return x.copy()
    return np.r_[np.full(min(j, len(x)), NAN), x[:-j]] if j < len(x) else np.full(len(x), NAN)


def f_inv_norm(p: float) -> float:
    """Acklam's inverse normal, exactly the script's f_invNorm."""
    def tail(q):
        return ((((((-7.784894002430293e-03 * q - 3.223964580411365e-01) * q - 2.400758277161838) * q - 2.549732539343734) * q
                  + 4.374664141464968) * q + 2.938163982698783) /
                ((((7.784695709041462e-03 * q + 3.224671290700398e-01) * q + 2.445134137142996) * q + 3.754408661907416) * q + 1.0))
    if p < 0.02425:
        return tail(math.sqrt(-2.0 * math.log(p)))
    if p > 1.0 - 0.02425:
        return -tail(math.sqrt(-2.0 * math.log(1.0 - p)))
    q = p - 0.5
    r = q * q
    return ((((((-3.969683028665376e+01 * r + 2.209460984245205e+02) * r - 2.759285104469687e+02) * r + 1.383577518672690e+02) * r
              - 3.066479806614716e+01) * r + 2.506628277459239) * q /
            (((((-5.447609879822406e+01 * r + 1.615858368580409e+02) * r - 1.556989798598866e+02) * r + 6.680131188771972e+01) * r
              - 1.328068155288572e+01) * r + 1.0))


def f_tanh(x: float) -> float:
    xc = max(-10.0, min(10.0, x))
    e = math.exp(2.0 * xc)
    return (e - 1.0) / (e + 1.0)


def _nan(x) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


# ── the engine ─────────────────────────────────────────────────────────────────
def run(d: pd.DataFrame, inp: Inputs | None = None) -> dict:
    """d: open/high/low/close/volume indexed by bar time (at most CALC_BARS rows - the script's calc_bars_count).

    Returns a dict: per-bar arrays under their script names, plus `last` (the table's values on the last bar),
    `ledger` (the nine states), `alerts` (every alert condition that fired, by bar) and `proof` (the record).
    """
    inp = inp or Inputs()
    d = d.iloc[-CALC_BARS:]
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    t_ms = (d.index.view("int64") // 10 ** 6).astype(np.int64) if isinstance(d.index, pd.DatetimeIndex) else np.arange(len(d))
    n = len(c)
    H = int(inp.H)
    bi = np.arange(n)

    # ── 1 · THE RISK FORECAST ──────────────────────────────────────────────────
    with np.errstate(divide="ignore", invalid="ignore"):
        lc = np.log(c)
        lnO = np.log(o)
        r1 = lc - lag(lc, 1)
        gp = lnO - lag(lc, 1)
        co = lc - lnO
        hl = np.log(h) - np.log(l)
        gk = gp * gp + 0.5 * hl * hl - (2.0 * math.log(2.0) - 1.0) * co * co
        vBar = np.where((hl > 0.0) & (gk > 0.0), gk, r1 * r1)          # na comparisons are false: bar 0 falls back to r1², which is na
    varS, varM, varL = pine_ema(vBar, 5), pine_ema(vBar, 22), pine_ema(vBar, 252)
    rL = pine_ema(r1 * r1, 252)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = rL / varL
        kk = np.where(varL > 0.0, np.where(np.isnan(ratio), NAN, np.clip(ratio, 0.5, 2.0)), 1.0)
        s0 = np.where(bi >= WARM, np.sqrt(kk * (0.25 * varS + 0.40 * varM + 0.35 * varL)), NAN)
    sig = np.where(s0 > 0.0, s0, NAN)
    sH = sig * math.sqrt(H)

    prk = pine_percentrank(sig, RN)
    regOk = (bi >= WARM + RN) & ~np.isnan(prk)
    regRaw = np.where(regOk, np.where(prk < 100.0 / 3.0, 0, np.where(prk < 200.0 / 3.0, 1, 2)), 1).astype(int)
    reg = regRaw if inp.reg else np.ones(n, dtype=int)

    with np.errstate(divide="ignore", invalid="ignore"):
        rMom = np.log(sig / lag(sig, H))
    rmS = np.where(rMom > 0.10, 2, np.where(rMom < -0.10, 0, 1))

    with np.errstate(divide="ignore", invalid="ignore"):
        T = ((lc - lag(lc, 63)) / (sig * math.sqrt(63.0)) + (lc - lag(lc, 126)) / (sig * math.sqrt(126.0))
             + (lc - lag(lc, 252)) / (sig * math.sqrt(252.0))) / 3.0
    trRaw = np.where(T > 0.5, 2, np.where(T < -0.5, 0, 1)).astype(int)
    trs = trRaw if inp.trend_f else np.ones(n, dtype=int)

    # ── 2 · THE CONE, THE STOPS AND THE LADDER ─────────────────────────────────
    aTail = (1.0 - inp.cover / 100.0) / 2.0
    pTch = inp.stop / 100.0
    zInit = math.log(f_inv_norm(1.0 - aTail))
    sInit = math.log(f_inv_norm(1.0 - pTch / 2.0))
    eta = inp.eta

    def w_new(b0):
        return [b0, b0, b0, 0.0, 0.0, 0.0]

    def f_q(a, rg, tr):
        return math.exp(a[rg] + a[3 + tr])

    def f_step(a, rg, tr, e):
        a[rg] += e
        a[3 + tr] += e if inp.trend_f else 0.0

    h0 = max(2, H // 2)
    RG = [h0, H, 2 * H, 4 * H]
    NR = len(RG)
    wU = [w_new(zInit) for _ in RG]
    wD = [w_new(zInit) for _ in RG]
    wS, wR = w_new(sInit), w_new(sInit)
    with np.errstate(divide="ignore", invalid="ignore"):
        U = [(lc - lag(lc, j)) / (lag(sig, j) * math.sqrt(j)) for j in RG]
    QU = np.full((NR, n), NAN)
    QD = np.full((NR, n), NAN)
    BU = np.full((NR, n), NAN)                    # the band each rung is judged against (quP)
    BD = np.full((NR, n), NAN)
    OK = np.zeros((NR, n), dtype=bool)
    MU = np.zeros((NR, n), dtype=bool)
    MD = np.zeros((NR, n), dtype=bool)
    X = np.full((NR, n), NAN)

    with np.errstate(divide="ignore", invalid="ignore"):
        pS = (np.log(pine_lowest(l, H)) - lag(lc, H)) / lag(sH, H)
        pR = (np.log(pine_highest(h, H)) - lag(lc, H)) / lag(sH, H)
        yRaw = (lc - lag(lnO, H - 1)) / lag(sH, H)
    yOut = np.where(np.isnan(yRaw), NAN, np.clip(yRaw, -6.0, 6.0))

    qS = np.full(n, NAN)
    qR = np.full(n, NAN)
    mS = np.zeros(n, dtype=bool)
    mR = np.zeros(n, dtype=bool)
    st = np.full(n, -1, dtype=int)
    nF = nMU = nMD = nMS = nMR = 0
    nF_s = np.zeros(n, dtype=int)
    lCnt, lMean, lEff, lLast = [0.0] * 9, [0.0] * 9, [0.0] * 9, [-1_000_000_000] * 9
    gN, gM, gQ = 0, 0.0, 0.0
    lEdge = np.full(n, NAN)
    lPost = np.full(n, NAN)
    lZ = np.full(n, NAN)
    lNe = np.full(n, NAN)
    lMu = np.full(n, NAN)
    gM_s = np.full(n, NAN)

    for t in range(n):
        for i, j in enumerate(RG):
            uu = U[i][t]
            quP = QU[i][t - j] if t >= j else NAN
            qdP = QD[i][t - j] if t >= j else NAN
            BU[i][t], BD[i][t] = quP, qdP
            ok = not math.isnan(uu) and not math.isnan(quP)
            up = ok and uu > quP
            dn = ok and uu < -qdP
            if ok:
                rgP, trP = reg[t - j], trs[t - j]
                f_step(wU[i], rgP, trP, eta * ((1.0 if up else 0.0) - aTail))
                f_step(wD[i], rgP, trP, eta * ((1.0 if dn else 0.0) - aTail))
                OK[i][t], MU[i][t], MD[i][t] = True, up, dn
                X[i][t] = uu / quP if uu >= 0.0 else uu / qdP
            if not math.isnan(sig[t]):
                QU[i][t] = f_q(wU[i], reg[t], trs[t])
                QD[i][t] = f_q(wD[i], reg[t], trs[t])

        settled = OK[1][t]
        if settled:
            qSP = qS[t - H]
            qRP = qR[t - H]
            mS[t] = pS[t] < -qSP                              # na comparisons are false
            mR[t] = pR[t] > qRP
            f_step(wS, reg[t - H], trs[t - H], eta * ((1.0 if mS[t] else 0.0) - pTch))
            f_step(wR, reg[t - H], trs[t - H], eta * ((1.0 if mR[t] else 0.0) - pTch))
            nF += 1
            nMU += int(MU[1][t])
            nMD += int(MD[1][t])
            nMS += int(mS[t])
            nMR += int(mR[t])
            sp = st[t - H] if t >= H else -1
            if sp >= 0 and not math.isnan(yOut[t]):
                c1 = lCnt[sp] + 1.0
                lCnt[sp] = c1
                lMean[sp] = lMean[sp] + (yOut[t] - lMean[sp]) / c1
                gN += 1
                if t - H - lLast[sp] >= H:
                    lEff[sp] += 1.0
                    lLast[sp] = t - H
                dlt = yOut[t] - gM
                gM += dlt / gN
                gQ += dlt * (yOut[t] - gM)
        nF_s[t] = nF
        gM_s[t] = gM
        if not math.isnan(sig[t]):
            qS[t] = f_q(wS, reg[t], trs[t])
            qR[t] = f_q(wR, reg[t], trs[t])
        cnS = 2 if MU[1][t] else 0 if MD[1][t] else 1
        if settled and not math.isnan(T[t]):
            st[t] = 3 * trRaw[t] + cnS
        s_ = st[t]
        if s_ >= 0:
            lNe[t] = lEff[s_]
            lMu[t] = lMean[s_]
            if lEff[s_] >= 5.0 and gN > 30 * H:
                se2 = gQ / (gN - 1) / lEff[s_]
                shr = inp.tau * inp.tau / (inp.tau * inp.tau + se2)
                lEdge[t] = lMean[s_] - gM
                lPost[t] = shr * lEdge[t]
                lZ[t] = lEdge[t] * math.sqrt(shr / se2)

    u, bU, bD, mU, mD, settled_s = U[1], BU[1], BD[1], MU[1], MD[1], OK[1]
    ladOk = OK[0] & OK[1] & OK[2] & OK[3]
    ladUp = MU.sum(axis=0)
    ladDn = MD.sum(axis=0)
    ladX = np.where(ladOk, X.mean(axis=0), NAN)
    ladN = np.where(ladX >= 0.0, ladUp, ladDn)

    proven = np.where(lZ >= 2.0, 1, np.where(lZ <= -2.0, -1, 0))
    stEnter = (st >= 0) & (st != lag(st.astype(float), 1))
    provenUp = stEnter & (proven == 1)
    provenDn = stEnter & (proven == -1)

    miss = np.where(settled_s, (mU | mD).astype(float), NAN)
    covRecent = 1.0 - _sma_skip_na(miss, 250)

    # ── 4 · LEVELS ─────────────────────────────────────────────────────────────
    with np.errstate(invalid="ignore", over="ignore"):
        upper = c * np.exp(QU[1] * sH)
        lower = c * np.exp(-QD[1] * sH)
        stopL = c * np.exp(-qS * sH)
        stopS = c * np.exp(qR * sH)
    coneOk = ~np.isnan(sig) & ~np.isnan(QU[1]) & ~np.isnan(qS)

    # ── 5 · THE EXPOSURE DIAL ──────────────────────────────────────────────────
    sumSig, nSig = 0.0, 0
    sigStar = np.full(n, NAN)
    dialR = np.full(n, NAN)
    dialT = np.full(n, NAN)
    dial = np.full(n, NAN)
    E = np.full(n, NAN)
    held = NAN
    for t in range(n):
        if not math.isnan(sig[t]):
            sumSig += sig[t]
            nSig += 1
        sigStar[t] = sumSig / nSig if nSig > 0 else NAN
        dialR[t] = NAN if math.isnan(sig[t]) else min(inp.cap, sigStar[t] / sig[t])
        dialT[t] = 1.0 if inp.mode == "Risk only" else (NAN if math.isnan(T[t]) else inp.floor + (1.0 - inp.floor) * (0.5 + 0.5 * f_tanh(T[t])))
        dial[t] = NAN if math.isnan(T[t]) else dialR[t] * dialT[t]
        if not math.isnan(dial[t]) and (math.isnan(held) or abs(dial[t] - held) >= inp.step):
            held = dial[t]
        E[t] = NAN if math.isnan(dial[t]) else held

    # ── 6 · THE PROOF ──────────────────────────────────────────────────────────
    ret = c / lag(c, 1) - 1.0
    e2, e3 = lag(E, 2), lag(E, 3)
    cost = inp.cost / 10000.0
    pF = np.where(np.isnan(e2), NAN, e2 * ret - cost * np.abs(e2 - np.nan_to_num(e3, nan=0.0)))
    pH = np.where(np.isnan(e2), NAN, ret)
    eqF = np.ones(n)
    eqH = np.ones(n)
    nP, tP = 0, None
    sF = sF2 = sHd = sHd2 = 0.0
    ef = eh = pkF = pkH = 1.0
    ddF = ddH = 0.0
    for t in range(n):
        if not math.isnan(pF[t]) and not math.isnan(pH[t]):
            if tP is None:
                tP = int(t_ms[t])
            nP += 1
            sF += pF[t]; sF2 += pF[t] ** 2; sHd += pH[t]; sHd2 += pH[t] ** 2
            ef *= 1.0 + pF[t]; eh *= 1.0 + pH[t]
            pkF = max(pkF, ef); pkH = max(pkH, eh)
            ddF = min(ddF, ef / pkF - 1.0); ddH = min(ddH, eh / pkH - 1.0)
        eqF[t], eqH[t] = ef, eh
    yrs = NAN if tP is None else (int(t_ms[-1]) - tP) / 31557600000.0
    bpy = nP / yrs if yrs and yrs > 0 else NAN

    def _sd(s, s2):
        return math.sqrt(max(s2 / nP - (s / nP) ** 2, 0.0)) if nP > 1 else NAN

    sdF, sdHd = _sd(sF, sF2), _sd(sHd, sHd2)
    shF = sF / nP / sdF * math.sqrt(bpy) if sdF and sdF > 0 and not math.isnan(bpy) else NAN
    shH = sHd / nP / sdHd * math.sqrt(bpy) if sdHd and sdHd > 0 and not math.isnan(bpy) else NAN
    cagF = ef ** (1.0 / yrs) - 1.0 if yrs and yrs > 0 and ef > 0 else NAN
    cagH = eh ** (1.0 / yrs) - 1.0 if yrs and yrs > 0 and eh > 0 else NAN

    # ── 6b · THE MIDLINE AND ITS RECORD ────────────────────────────────────────
    midL = (lag(upper, H) + lag(lower, H)) / 2.0
    midSide = np.where(np.isnan(midL), 0, np.where(c > midL, 1, -1))
    ms1 = np.r_[0, midSide[:-1]]
    midUp = (midSide == 1) & (ms1 == -1)
    midDn = (midSide == -1) & (ms1 == 1)
    mRuns = mWon = mLong = 0
    mGain = 0.0
    mPx = NAN
    mBar = None
    mDir = 0
    for t in range(n):
        if midUp[t] or midDn[t]:
            if mDir != 0 and not math.isnan(mPx):
                gRun = mDir * math.log(c[t] / mPx)
                mRuns += 1
                mWon += 1 if gRun > 0.0 else 0
                mLong += 1 if t - mBar >= 20 else 0
                mGain += gRun
            mPx, mBar, mDir = c[t], t, (1 if midUp[t] else -1)
    m2 = np.where(lag(midSide.astype(float), 2) == 1, 1.0, 0.0)
    m3 = np.where(lag(midSide.astype(float), 3) == 1, 1.0, 0.0)
    pM = np.where(np.isnan(e2), NAN, m2 * ret - cost * np.abs(m2 - m3))
    ok_m = ~np.isnan(pM) & ~np.isnan(pH)
    sM, sM2 = float(np.nansum(np.where(ok_m, pM, 0.0))), float(np.nansum(np.where(ok_m, pM * pM, 0.0)))
    sdM = _sd(sM, sM2)
    shM = sM / nP / sdM * math.sqrt(bpy) if sdM and sdM > 0 and not math.isnan(bpy) else NAN

    # ── ALERTS ─────────────────────────────────────────────────────────────────
    E_prev = lag(E, 1)
    alerts = {
        "Landing band · close above": mU,
        "Landing band · close below": mD,
        "Stretch ladder · 3+ rungs above": ladOk & (ladUp >= 3) & ~(lag(ladUp.astype(float), 1) >= 3),
        "Stretch ladder · 3+ rungs below": ladOk & (ladDn >= 3) & ~(lag(ladDn.astype(float), 1) >= 3),
        "Risk · stressed": (regRaw == 2) & (lag(regRaw.astype(float), 1) != 2),
        "Risk · rising": (rmS == 2) & (lag(rmS.astype(float), 1) != 2),
        "Midline · close above": midUp,
        "Midline · close below": midDn,
        "Exposure · changed": (E != E_prev) & ~np.isnan(E_prev) & ~np.isnan(E),
        "Ledger · proven state, positive": provenUp,
        "Ledger · proven state, negative": provenDn,
    }

    series = dict(
        lc=lc, sig=sig, sH=sH, prk=prk, regOk=regOk, regRaw=regRaw, reg=reg, rMom=rMom, rmS=rmS, T=T, trRaw=trRaw, trs=trs,
        u=u, bU=bU, bD=bD, mU=mU, mD=mD, settled=settled_s, qU=QU[1], qD=QD[1], qS=qS, qR=qR, mS=mS, mR=mR,
        ladOk=ladOk, ladUp=ladUp, ladDn=ladDn, ladX=ladX, ladN=ladN, st=st, lNe=lNe, lMu=lMu, lEdge=lEdge, lPost=lPost, lZ=lZ,
        proven=proven, provenUp=provenUp, provenDn=provenDn, covRecent=covRecent, upper=upper, lower=lower, stopL=stopL,
        stopS=stopS, coneOk=coneOk, sigStar=sigStar, dialR=dialR, dialT=dialT, dial=dial, E=E, pF=pF, pH=pH, eqF=eqF, eqH=eqH,
        midL=midL, midSide=midSide, midUp=midUp, midDn=midDn, pM=pM, nF=nF_s, gM=gM_s,
    )
    for i in range(NR):
        series[f"u{i}"], series[f"ok{i}"], series[f"mU{i}"], series[f"mD{i}"] = U[i], OK[i], MU[i], MD[i]
        series[f"qU{i}"], series[f"qD{i}"], series[f"x{i}"] = QU[i], QD[i], X[i]

    ledger = [dict(state=s, trend=("down", "flat", "up")[s // 3], close=("below the band", "inside the band", "above the band")[s % 3],
                   n=int(lCnt[s]), n_eff=int(lEff[s]), mean=lMean[s] if lCnt[s] else NAN) for s in range(9)]
    last = dict(
        nF=nF, nMU=nMU, nMD=nMD, nMS=nMS, nMR=nMR, cov=(1.0 - (nMU + nMD) / nF) if nF > 0 else NAN,
        gN=gN, gM=gM, gQ=gQ, nP=nP, yrs=yrs, bpy=bpy, shF=shF, shH=shH, ddF=ddF, ddH=ddH, cagF=cagF, cagH=cagH, eqF=ef, eqH=eh,
        mRuns=mRuns, mWon=mWon, mLong=mLong, mGain=mGain, shM=shM, h0=h0, h2=2 * H, h3=4 * H,
    )
    return dict(series=series, last=last, ledger=ledger, alerts=alerts, inputs=inp, n=n, index=d.index)


def _sma_skip_na(x: np.ndarray, n: int) -> np.ndarray:
    """ta.sma with na inputs skipped: the mean of the last n non-na values seen so far (na until n have been seen)."""
    out = np.full(len(x), NAN)
    buf: list[float] = []
    s = 0.0
    for i, v in enumerate(x):
        if not math.isnan(v):
            buf.append(v)
            s += v
            if len(buf) > n:
                s -= buf.pop(0)
        if len(buf) == n:
            out[i] = s / n
    return out
