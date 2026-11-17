"""Stage 1 - the risk forecast. QLIKE of the H-bar variance forecast against the next H bars' realised variance.

    python3 research/hpo/stage1_risk.py RD|FD|RH|FH|HD|HH <fresh_d> <fresh_h> <hold_d> <hold_h> [config.json]

Writes out/risk_<ds>.csv: one row per (config, split) with the instrument-averaged QLIKE. With a config
file, scores only the configs it lists (the final test).
"""
import os, sys, json, itertools
import numpy as np, pandas as pd
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hpo_core as C                                     # noqa: E402

DS = sys.argv[1]; PATHS = sys.argv[2:6]
ONLY = json.load(open(sys.argv[6])) if len(sys.argv) > 6 else None
H = 10
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
SS, MS, LS = (3, 5, 10), (15, 22, 44), (126, 252)
WGRID = [(a / 10, b / 10, round(1 - a / 10 - b / 10, 1)) for a in range(11) for b in range(11 - a)] + [(0.25, 0.40, 0.35)]
KCLIPS = {"0.5-2": (0.5, 2.0), "0.25-4": (0.25, 4.0), "off": None}


def configs():
    if ONLY:
        return [(tuple(c["spans"]), tuple(c["w"]), c["kclip"]) for c in ONLY]
    return [(sp, w, kc) for sp in itertools.product(SS, MS, LS) for w in WGRID for kc in KCLIPS]


def one(args):
    sym, d, cut = args
    o, h, l, c = (d[k].values.astype(float) for k in ("open", "high", "low", "close"))
    lc, lo = np.log(c), np.log(o); r = np.r_[np.nan, np.diff(lc)]
    gp = lo - np.r_[np.nan, lc[:-1]]; co = lc - lo; hl = np.log(h) - np.log(l)
    with np.errstate(all="ignore"):
        gk = gp ** 2 + 0.5 * hl ** 2 - (2 * np.log(2) - 1) * co ** 2
        v = np.where((hl > 0) & (gk > 0), gk, r ** 2)
        rL = C.ema(r ** 2, 252)
        E = {s: C.ema(v, s) for s in set(SS + MS + LS)}
        rv = pd.Series(r ** 2).rolling(H).sum().shift(-H).to_numpy()          # realised variance of the next H bars
    split = C.split_of(d.index, DS, cut)
    n = len(c); valid = np.isfinite(rv) & (rv > 0); valid[:C.WARM] = False
    out = {}
    for sp in {x[0] for x in configs()}:
        V = np.stack([E[sp[0]], E[sp[1]], E[sp[2]]])                      # 3 x n
        for kc in {x[2] for x in configs()}:
            clip = KCLIPS[kc] if isinstance(kc, str) else (tuple(kc) if kc else None)
            k = np.clip(rL / E[sp[2]], *clip) if clip else np.ones(n)
            ws = [x[1] for x in configs() if x[0] == sp and x[2] == kc]
            Wm = np.array(ws)                                              # m x 3
            with np.errstate(all="ignore"):
                hvar = (Wm @ V) * k * H                                    # m x n: the H-bar variance forecast
                x = np.clip(rv / hvar, 0.01, 100.0)                       # one glitched bar cannot decide it
                q = x - np.log(x) - 1.0
                lx2 = np.log(x) ** 2
            ok = valid & np.isfinite(q).all(axis=0)
            for part in ("tune", "validate"):
                m = ok & (split == part)
                if m.sum() < 200:
                    continue
                means, msle = q[:, m].mean(axis=1), lx2[:, m].mean(axis=1)
                for w, val, ml in zip(ws, means, msle):
                    out[(sp, w, kc, part)] = (float(val), float(ml))
    return sym, out


def main():
    D = C.load(DS, *PATHS)
    idx = pd.DatetimeIndex(sorted(set().union(*[set(d.index) for _, d in D.values()])))
    cut = idx[len(idx) // 2] if DS in ("RH", "FH", "HH") else None
    with Pool(4) as pool:
        res = pool.map(one, [(s, d, cut) for s, (_c, d) in D.items()], chunksize=4)
    rows = {}
    for _sym, out in res:
        for key, val in out.items():
            rows.setdefault(key, []).append(val)
    R = pd.DataFrame([dict(spans=k[0], w=k[1], kclip=k[2] if isinstance(k[2], str) else str(k[2]), split=k[3],
                           qlike=float(np.mean([a for a, _ in v])), qlike_median=float(np.median([a for a, _ in v])),
                           msle=float(np.mean([b for _, b in v])), n_inst=len(v))
                      for k, v in rows.items()])
    R.to_csv(os.path.join(OUT, f"risk_{DS}.csv"), index=False)
    print(DS, len(D), "instruments,", R[["spans", "w", "kclip"]].drop_duplicates().shape[0], "configs")


if __name__ == "__main__":
    main()
