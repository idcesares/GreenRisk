"""Phase 5 Step 2 - Bingler (2022) cheap-talk baseline + validity comparison.

Bingler et al., "Cheap Talk and Cherry-Picking," use the SAME ClimateBERT
specificity model we do. Their construct: non-specific disclosure = "cheap talk".
We operationalize the per-paragraph baseline as cheap_talk = 1 - P('spec'),
read straight from the locked corpus run (no model re-run needed).

Asks two questions of the locked instrument vs. this baseline:
  CONVERGENT  - does GreenRisk risk track cheap-talk? (Spearman + decile bins)
  DISCRIMINANT- does GreenRisk add beyond raw specificity? (risk spread WITHIN
                a fixed cheap-talk level, driven by claim strength/commitment)

Inputs:  artifacts/corpus_run/tcfd_scored.csv
Outputs: artifacts/figures/bingler_convergence.png
         artifacts/figures/bingler_discriminant.png
         prints correlation + decile + category tables

Run:  uv run python scripts/bingler_baseline.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, pearsonr

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV = ROOT / "artifacts" / "corpus_run" / "tcfd_scored.csv"
FIG = ROOT / "artifacts" / "figures"


def main():
    df = pd.read_csv(CSV)
    df["cheap_talk"] = 1.0 - df["specificity"]          # Bingler baseline
    n = len(df)
    print(f"loaded {n} gated paragraphs from {CSV.name}\n")

    # --- CONVERGENT VALIDITY -------------------------------------------------
    rho, p_s = spearmanr(df["cheap_talk"], df["risk"])
    r, p_p = pearsonr(df["cheap_talk"], df["risk"])
    print("CONVERGENT VALIDITY (cheap_talk vs GreenRisk risk)")
    print(f"  Spearman rho = {rho:+.3f}  (p={p_s:.1e})   <- primary, robust to ties")
    print(f"  Pearson  r   = {r:+.3f}  (p={p_p:.1e})\n")

    # Decile bins of cheap-talk -> mean risk (monotone rise = convergence)
    df["ct_decile"] = pd.qcut(df["cheap_talk"], 10, labels=False, duplicates="drop")
    decile = df.groupby("ct_decile").agg(
        cheap_talk_mid=("cheap_talk", "mean"),
        mean_risk=("risk", "mean"),
        std_risk=("risk", "std"),
        n=("risk", "size"),
    ).round(2)
    print("cheap-talk decile -> GreenRisk risk")
    print(decile.to_string(), "\n")

    # --- DISCRIMINANT VALIDITY ----------------------------------------------
    # Within the HIGH cheap-talk band (vague text), does risk still vary?
    # If yes, GreenRisk separates "quiet vagueness" from "loud vague pledges".
    hi = df[df["cheap_talk"] >= df["cheap_talk"].quantile(0.75)]
    print("DISCRIMINANT VALIDITY (top-quartile cheap-talk = most vague text)")
    print(f"  n = {len(hi)}   cheap_talk range here is narrow by construction")
    print(f"  cheap_talk: mean={hi['cheap_talk'].mean():.3f} std={hi['cheap_talk'].std():.3f}")
    print(f"  GreenRisk risk: mean={hi['risk'].mean():.2f} std={hi['risk'].std():.2f}"
          f"  min={hi['risk'].min():.1f} max={hi['risk'].max():.1f}")
    rho_c, _ = spearmanr(hi["commitment"], hi["risk"])
    print(f"  within this band, Spearman(commitment, risk) = {rho_c:+.3f}"
          "  <- the claim-strength axis cheap-talk is blind to\n")

    # --- CHERRY-PICKING CUT (by TCFD category) ------------------------------
    cat = df.groupby("tcfd_category").agg(
        n=("risk", "size"),
        mean_cheap_talk=("cheap_talk", "mean"),
        mean_risk=("risk", "mean"),
    ).round(3).sort_values("mean_risk")
    print("cherry-picking view (by TCFD category)")
    print(cat.to_string(), "\n")

    # --- FIGURES -------------------------------------------------------------
    FIG.mkdir(parents=True, exist_ok=True)

    # Fig 1: convergence - decile of cheap-talk vs mean risk
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(decile["cheap_talk_mid"], decile["mean_risk"],
                yerr=decile["std_risk"], marker="o", capsize=3)
    ax.set_xlabel("cheap-talk = 1 - P(specific)  [Bingler baseline]")
    ax.set_ylabel("GreenRisk risk (mean +/- sd per decile)")
    ax.set_title(f"Convergent validity: GreenRisk tracks cheap-talk "
                 f"(Spearman rho={rho:+.2f})")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "bingler_convergence.png", dpi=150)
    plt.close(fig)

    # Fig 2: discriminant - scatter cheap-talk vs risk, colored by commitment
    fig, ax = plt.subplots(figsize=(7.5, 5))
    sc = ax.scatter(df["cheap_talk"], df["risk"], c=df["commitment"],
                    cmap="viridis", s=14, alpha=0.6)
    ax.set_xlabel("cheap-talk = 1 - P(specific)  [Bingler baseline]")
    ax.set_ylabel("GreenRisk risk")
    ax.set_title("Discriminant validity: at fixed cheap-talk, "
                 "risk rises with commitment")
    cb = fig.colorbar(sc, ax=ax)
    cb.set_label("commitment  P('yes')")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "bingler_discriminant.png", dpi=150)
    plt.close(fig)

    print(f"wrote {FIG / 'bingler_convergence.png'}")
    print(f"wrote {FIG / 'bingler_discriminant.png'}")


if __name__ == "__main__":
    main()