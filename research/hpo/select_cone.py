"""Stage 2 selection. Pools research and fresh per timeframe (interval score weighted by forecasts), takes the
worst calibration error over both sets, and picks the candidate by tuning score averaged over daily and hourly
among configs calibrated on the tuning split. Checks it on validation and writes out/cone.json.

Calibrated: coverage within 3 points of 80% in every true risk regime, and stop touches within 3 points of 20%
on each side - on both research and fresh, on both timeframes.

    python3 research/hpo/select_cone.py
"""
import os, json
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
K = ["eta", "regimes", "trendf"]
DEFAULT = (0.02, True, True)
BAR, TOL = 0.01, 0.03


def pooled(a, b):
    X = pd.concat([pd.read_csv(os.path.join(OUT, f"cone_{d}.csv")) for d in (a, b)])
    X["is_n"] = X.interval_score * X.n
    G = X.groupby(K + ["split"]).agg(is_n=("is_n", "sum"), n=("n", "sum"), cal=("worst_cal_err", "max"),
                                     stop=("worst_stop_err", "max"), trend=("worst_trend_err", "max"))
    G["isc"] = G.is_n / G.n
    P = G[["isc", "cal", "stop", "trend"]].unstack("split")
    P.columns = [f"{m}_{s}" for m, s in P.columns]
    P["rel_tune"] = P.isc_tune / P.loc[DEFAULT, "isc_tune"]
    P["rel_validate"] = P.isc_validate / P.loc[DEFAULT, "isc_validate"]
    return P


def main():
    S = pooled("RD", "FD").join(pooled("RH", "FH"), lsuffix="_d", rsuffix="_h")
    S["tune"] = (S.rel_tune_d + S.rel_tune_h) / 2
    S["calibrated_tune"] = (S[["cal_tune_d", "cal_tune_h", "stop_tune_d", "stop_tune_h"]] <= TOL).all(axis=1)
    S["calibrated_validate"] = (S[["cal_validate_d", "cal_validate_h", "stop_validate_d", "stop_validate_h"]] <= TOL).all(axis=1)
    S = S.sort_values("tune")
    cols = ["tune", "rel_validate_d", "rel_validate_h", "cal_tune_d", "cal_tune_h", "cal_validate_d", "cal_validate_h",
            "stop_validate_d", "stop_validate_h", "trend_validate_d", "trend_validate_h", "calibrated_tune"]
    print("interval score relative to the default (1.000); worst calibration errors in points of coverage\n")
    print(S[cols].round(4).to_string())
    elig = S[S.calibrated_tune]
    best = elig.index[0]
    v = S.loc[best]
    keep = v.rel_validate_d <= 1 - BAR and v.rel_validate_h <= 1 - BAR and v.calibrated_validate
    print("\ncandidate:", dict(zip(K, best)))
    print(f"validate daily {1 - v.rel_validate_d:+.2%}, hourly {1 - v.rel_validate_h:+.2%} better than the default"
          f" (needs {BAR:.0%} on both); calibrated on validation: {bool(v.calibrated_validate)}")
    print("verdict:", "kept for the final test" if keep else "default stays")
    chosen = best if keep else DEFAULT
    json.dump(dict(zip(K, [float(chosen[0]), bool(chosen[1]), bool(chosen[2])]), candidate=[float(best[0]), bool(best[1]), bool(best[2])],
                   kept=bool(keep)), open(os.path.join(OUT, "cone.json"), "w"), indent=1)
    S.round(5).to_csv(os.path.join(OUT, "cone_relative.csv"))


if __name__ == "__main__":
    main()
