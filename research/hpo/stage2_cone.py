"""Stage 2 - the cone and stops. Interval score at the 80% target, coverage per risk regime, stop touches.

    python3 research/hpo/stage2_cone.py RD|FD|RH|FH|HD|HH <fresh_d> <fresh_h> <hold_d> <hold_h> <risk.json> [configs.json]

<risk.json>: the risk-forecast settings stage 1 settled on ({"spans", "w", "kclip"}). Writes
out/cone_<ds>.csv: per (config, split) the interval score, coverage per regime and overall, and stop
touch rates per side - all pooled over every settled forecast of every instrument.
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
H, COVER, PSTOP = 10, 0.80, 0.20
ALPHA = 1 - COVER
OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
GRID = ONLY or [dict(eta=e, regimes=r, trendf=t) for e, r, t in
                itertools.product((0.005, 0.01, 0.015, 0.02, 0.03, 0.05), (True, False), (True, False))]
KC = {"0.5-2": (0.5, 2.0), "0.25-4": (0.25, 4.0), "off": None}


def one(args):
    sym, d, cut, cfg = args
    o = C.run_p(d, H=H, cover=COVER, pstop=PSTOP, spans=tuple(RISK["spans"]), w=tuple(RISK["w"]),
                kclip=KC[RISK["kclip"]] if isinstance(RISK["kclip"], str) else RISK["kclip"], **cfg)
    ok = o.nF.to_numpy(bool)
    y = o.u.to_numpy(float)
    U = o.qU.shift(H).to_numpy(float); L = -o.qD.shift(H).to_numpy(float)
    reg = pd.Series(C.risk_regime(o.sig.to_numpy(float)), dtype=float).shift(H).to_numpy()   # the true regime
    trs = pd.Series(np.where(o["T"] > 0.5, 2, np.where(o["T"] < -0.5, 0, 1)), dtype=float).where(o["T"].notna()).shift(H).to_numpy()
    if cfg.get("regimes", True):
        assert np.array_equal(reg[np.isfinite(reg)], o.reg.shift(H).to_numpy(float)[np.isfinite(reg)])
    m = ok & np.isfinite(y) & np.isfinite(U) & np.isfinite(L)
    isc = (U - L) + (2 / ALPHA) * (L - y) * (y < L) + (2 / ALPHA) * (y - U) * (y > U)
    split = C.split_of(d.index, DS, cut)
    out = []
    for part in ("tune", "validate"):
        k = m & (split == part)
        if k.sum() < 100:
            continue
        row = dict(sym=sym, split=part, n=int(k.sum()), is_sum=float(isc[k].sum()),
                   up=float((y[k] > U[k]).sum()), dn=float((y[k] < L[k]).sum()),
                   stop_l=float(o.mS.to_numpy()[k].sum()), stop_s=float(o.mR.to_numpy()[k].sum()))
        for g in (0, 1, 2):
            kg = k & (reg == g)
            row[f"n_r{g}"] = int(kg.sum()); row[f"in_r{g}"] = float(((y[kg] <= U[kg]) & (y[kg] >= L[kg])).sum())
            kt = k & (trs == g)
            row[f"n_t{g}"] = int(kt.sum()); row[f"in_t{g}"] = float(((y[kt] <= U[kt]) & (y[kt] >= L[kt])).sum())
        out.append(row)
    return cfg, out


def main():
    D = C.load(DS, *PATHS)
    idx = pd.DatetimeIndex(sorted(set().union(*[set(d.index) for _, d in D.values()])))
    cut = idx[len(idx) // 2] if DS in ("RH", "FH", "HH") else None
    jobs = [(s, d, cut, cfg) for cfg in GRID for s, (_c, d) in D.items()]
    with Pool(4) as pool:
        res = pool.map(one, jobs, chunksize=8)
    agg = {}
    for cfg, rows in res:
        key = (cfg["eta"], cfg["regimes"], cfg["trendf"])
        for r in rows:
            a = agg.setdefault((key, r["split"]), {})
            for k, v in r.items():
                if k not in ("sym", "split"):
                    a[k] = a.get(k, 0) + v
    out = []
    for ((eta, rg, tf), part), a in agg.items():
        rec = dict(eta=eta, regimes=rg, trendf=tf, split=part, n=a["n"], interval_score=a["is_sum"] / a["n"],
                   coverage=1 - (a["up"] + a["dn"]) / a["n"], stop_long=a["stop_l"] / a["n"], stop_short=a["stop_s"] / a["n"])
        for g, nm in ((0, "calm"), (1, "normal"), (2, "stressed")):
            rec[f"cov_{nm}"] = a[f"in_r{g}"] / a[f"n_r{g}"] if a[f"n_r{g}"] else np.nan
        for g, nm in ((0, "down"), (1, "flat"), (2, "up")):
            rec[f"cov_{nm}"] = a[f"in_t{g}"] / a[f"n_t{g}"] if a[f"n_t{g}"] else np.nan
        rec["worst_cal_err"] = max(abs(rec[f"cov_{nm}"] - COVER) for nm in ("calm", "normal", "stressed"))
        rec["worst_trend_err"] = max(abs(rec[f"cov_{nm}"] - COVER) for nm in ("down", "flat", "up"))
        rec["worst_stop_err"] = max(abs(rec["stop_long"] - PSTOP), abs(rec["stop_short"] - PSTOP))
        out.append(rec)
    R = pd.DataFrame(out).sort_values(["split", "interval_score"])
    R.to_csv(os.path.join(OUT, f"cone_{DS}.csv"), index=False)
    print(DS, len(D), "instruments,", len(GRID), "configs")


if __name__ == "__main__":
    main()
