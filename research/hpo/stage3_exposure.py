"""Stage 3 - the exposure rule. Net Sharpe of the exposure line minus buy and hold's, per instrument.

    python3 research/hpo/stage3_exposure.py RD|FD|HD <fresh_d> <fresh_h> <hold_d> <hold_h> <risk.json> [configs.json]

Daily only (the exposure rule is a daily / weekly rule). Exposure exactly as run() builds it
(check() asserts it against hpo_core.run_p). Every config is scored on the same bars: those where the
longest trend lookback has a reading. Writes out/exposure_<ds>.csv.
"""
import os, sys, json, itertools
import numpy as np, pandas as pd
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hpo_core as C                                     # noqa: E402

DS = sys.argv[1]; PATHS = sys.argv[2:6]
RISK = json.load(open(sys.argv[6]))
ONLY = json.load(open(sys.argv[7])) if len(sys.argv) > 7 else None
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
KC = {"0.5-2": (0.5, 2.0), "0.25-4": (0.25, 4.0), "off": None}
TLBS = {"63-126-252": (63, 126, 252), "21-63-126": (21, 63, 126), "126-252-504": (126, 252, 504)}
GRID = ONLY or [dict(floor=f, power=p, band=b, tlb=t) for f, p, b, t in itertools.product(
    (0.0, 0.25, 0.5, 0.75, 1.0), (0.5, 0.75, 1.0, 1.25, 1.5), (0.0, 0.05, 0.10, 0.15, 0.20), TLBS)]
CAP = 1.0


def exposure(c, sig, T, floor, power, band, cost):
    g = floor + (1 - floor) * (0.5 + 0.5 * np.tanh(T))
    star = np.nancumsum(sig) / np.maximum(np.cumsum(~np.isnan(sig)), 1)
    with np.errstate(all="ignore"):
        E = np.minimum(CAP, (star / sig) ** power) * g
    E[np.isnan(T)] = np.nan
    if band > 0:
        held = np.nan
        for t in range(len(E)):
            if not np.isnan(E[t]) and (np.isnan(held) or abs(E[t] - held) >= band): held = E[t]
            E[t] = held if not np.isnan(E[t]) else np.nan
    ret = np.r_[np.nan, c[1:] / c[:-1] - 1]; E2 = C.lag(E, 2); E3 = C.lag(E, 3)
    pf = E2 * ret - cost * np.abs(E2 - np.nan_to_num(E3, nan=0.0)); ph = np.where(np.isnan(E2), np.nan, ret)
    return pf, ph


def trend(lc, sig, tlb):
    with np.errstate(all="ignore"):
        return sum((lc - C.lag(lc, j)) / (sig * np.sqrt(j)) for j in tlb) / len(tlb)


def check(d):
    o = C.run_p(d)
    c = d.close.values.astype(float); sig, _, _ = C.sigma(d)
    pf, _ = exposure(c, sig, trend(np.log(c), sig, (63, 126, 252)), 0.5, 1.0, 0.10, 0.0005)
    assert np.allclose(pf, o.pf.to_numpy(float), equal_nan=True, atol=1e-12)
    return True


def stats(x):
    x = x[np.isfinite(x)]
    if len(x) < 250 or x.std() == 0:
        return np.nan, np.nan
    eq = np.cumprod(1 + x)
    return x.mean() / x.std() * np.sqrt(252), (eq / np.maximum.accumulate(eq) - 1).min()


def one(args):
    sym, cls, d = args
    c = d.close.values.astype(float); lc = np.log(c)
    sig, _, _ = C.sigma(d, tuple(RISK["spans"]), tuple(RISK["w"]),
                        KC[RISK["kclip"]] if isinstance(RISK["kclip"], str) else RISK["kclip"])
    Ts = {k: trend(lc, sig, v) for k, v in TLBS.items()}
    common = np.isfinite(C.lag(Ts["126-252-504"], 2))                    # bars every config can be scored on
    split = C.split_of(d.index, DS)
    cost = 0.001 if cls == "crypto" else 0.0005
    out = []
    for cfg in GRID:
        pf, ph = exposure(c, sig, Ts[cfg["tlb"]], cfg["floor"], cfg["power"], cfg["band"], cost)
        for part in ("tune", "validate"):
            k = common & (split == part)
            se, de = stats(pf[k]); sh, dh = stats(ph[k])
            if np.isfinite(se) and np.isfinite(sh):
                out.append(dict(cfg, sym=sym, split=part, sharpe=se, sharpe_hold=sh, uplift=se - sh,
                                dd=de, dd_hold=dh, dd_ratio=de / dh if dh < 0 else np.nan))
    return out


def main():
    D = C.load(DS, *PATHS)
    if DS == "RD":
        assert check(D["AAPL"][1]) and check(D["_GSPC"][1])
    with Pool(4) as pool:
        res = pool.map(one, [(s, c, d) for s, (c, d) in D.items()], chunksize=4)
    A = pd.DataFrame([r for rows in res for r in rows])
    A.to_csv(os.path.join(OUT, f"exposure_{DS}_per_instrument.csv.gz"), index=False)
    R = A.groupby(["floor", "power", "band", "tlb", "split"]).agg(
        uplift_median=("uplift", "median"), uplift_mean=("uplift", "mean"), beats_hold=("uplift", lambda x: (x > 0).mean()),
        dd_ratio_median=("dd_ratio", "median"), sharpe_median=("sharpe", "median"), n_inst=("uplift", "size")).reset_index()
    R.to_csv(os.path.join(OUT, f"exposure_{DS}.csv"), index=False)
    print(DS, len(D), "instruments,", len(GRID), "configs")


if __name__ == "__main__":
    main()
