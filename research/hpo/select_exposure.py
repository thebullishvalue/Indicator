"""Stage 3 selection. Pools research and fresh daily per instrument, takes the median Sharpe uplift over buy and
hold per config, picks the candidate by tuning uplift and checks it on validation (needs +0.02 over the default).

    python3 research/hpo/select_exposure.py
"""
import os
import pandas as pd

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
K = ["floor", "power", "band", "tlb"]
DEFAULT = (0.5, 1.0, 0.10, "63-126-252")
BAR = 0.02


def main():
    X = pd.concat([pd.read_csv(os.path.join(OUT, f"exposure_{d}_per_instrument.csv.gz")) for d in ("RD", "FD")])
    G = X.groupby(K + ["split"]).agg(uplift=("uplift", "median"), beats_hold=("uplift", lambda x: (x > 0).mean()),
                                     dd_ratio=("dd_ratio", "median"), sharpe=("sharpe", "median")).unstack("split")
    G.columns = [f"{m}_{s}" for m, s in G.columns]
    d = G.loc[DEFAULT]
    G["vs_default_tune"] = G.uplift_tune - d.uplift_tune
    G["vs_default_validate"] = G.uplift_validate - d.uplift_validate
    G = G.sort_values("uplift_tune", ascending=False)
    print("default:", d.round(4).to_dict(), "\n")
    print(G.head(15).round(4).to_string())
    best = G.index[0]; v = G.loc[best]
    keep = v.vs_default_validate >= BAR
    print("\ncandidate:", dict(zip(K, best)))
    print(f"validate uplift {v.uplift_validate:+.4f} vs default {d.uplift_validate:+.4f}: {v.vs_default_validate:+.4f}"
          f" (needs {BAR:+.2f})")
    print("verdict:", "kept for the final test" if keep else "default stays")
    for k in K:
        print(G.groupby(level=k)[["uplift_tune", "uplift_validate", "dd_ratio_validate"]].median().round(4).to_string())
    G.round(5).to_csv(os.path.join(OUT, "exposure_relative.csv"))


if __name__ == "__main__":
    main()
