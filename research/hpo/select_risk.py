"""Stage 1 selection. Pools research and fresh per timeframe (weighted by instruments), scores each config
relative to the default, picks the candidate by its tuning score averaged over daily and hourly, and checks it
on validation. Prints the verdict and writes out/risk.json (the settings stage 2 reads).

    python3 research/hpo/select_risk.py
"""
import os, json
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
KEY = ["spans", "w", "kclip"]
DEFAULT = ("(5, 22, 252)", "(0.25, 0.4, 0.35)", "0.5-2")
BAR = 0.01


def pooled(a, b):
    X = pd.concat([pd.read_csv(os.path.join(OUT, f"risk_{d}.csv")) for d in (a, b)])
    for c in ("qlike", "msle", "qlike_median"):
        X[c] = X[c] * X.n_inst
    G = X.groupby(KEY + ["split"])[["qlike", "msle", "qlike_median", "n_inst"]].sum()
    for c in ("qlike", "msle", "qlike_median"):
        G[c] = G[c] / G.n_inst
    P = G.drop(columns="n_inst").unstack("split")
    P.columns = [f"{m}_{s}" for m, s in P.columns]
    return P / P.loc[DEFAULT]                                   # 1.0 = the default; below 1 is better


def main():
    D, H = pooled("RD", "FD"), pooled("RH", "FH")
    S = D.join(H, lsuffix="_d", rsuffix="_h")
    S["tune"] = (S.qlike_tune_d + S.qlike_tune_h) / 2
    S = S.sort_values("tune")
    cols = ["tune", "qlike_tune_d", "qlike_validate_d", "qlike_tune_h", "qlike_validate_h",
            "msle_validate_d", "msle_validate_h"]
    print("relative to the default (1.000); top 15 by tuning score\n")
    print(S[cols].head(15).round(4).to_string())
    best = S.index[0]
    v = S.loc[best]
    keep = v.qlike_validate_d <= 1 - BAR and v.qlike_validate_h <= 1 - BAR
    print("\ncandidate:", best)
    print(f"validate daily {1 - v.qlike_validate_d:+.2%}, hourly {1 - v.qlike_validate_h:+.2%} better than the default"
          f" (needs {BAR:.0%} on both)")
    print("verdict:", "kept for the final test" if keep else "default stays")
    print(f"\nflatness: {(S.tune < 1.01).sum()} of {len(S)} configs within 1% of the default on tuning;"
          f" best validation anywhere: daily {1 - S.qlike_validate_d.min():+.2%}, hourly {1 - S.qlike_validate_h.min():+.2%}")
    chosen = best if keep else DEFAULT
    sp, w, kc = chosen
    json.dump(dict(spans=list(eval(sp)), w=list(eval(w)), kclip=kc, candidate=list(best), kept=bool(keep)),
              open(os.path.join(OUT, "risk.json"), "w"), indent=1)
    S[cols].round(5).to_csv(os.path.join(OUT, "risk_relative.csv"))


if __name__ == "__main__":
    main()
