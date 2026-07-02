"""Formal face-validity evaluation of the contrast-set scores.

Reads the one-shot scores (no model re-run) and evaluates per the FROZEN
pre-registration (see docs/validation.md for the stratification rationale):
  PRIMARY  - separation of in-scope greenwashing vs rigorous (AUC + Mann-Whitney)
  BOUNDARY - out-of-scope greenwashing not flagged (all risk < elevated threshold)
Small n: a demonstration, not a benchmark - reported with that caveat. Errors vs.
the pre-registration are logged findings (limitations), never instrument fixes.

Inputs:  artifacts/contrast_run/contrast_scored.csv
Outputs: artifacts/figures/face_validity.png
         artifacts/contrast_run/face_validity_stats.json

Run:  uv run python scripts/evaluate_face_validity.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import mannwhitneyu

ROOT = pathlib.Path(__file__).resolve().parents[1]
CSV = ROOT / "artifacts" / "contrast_run" / "contrast_scored.csv"
FIG = ROOT / "artifacts" / "figures"
FLAG = 50.0  # risk >= FLAG => "flagged as greenwashing" (Elevated-band onset)


def band(r):
    if r < 22.5: return "Low"
    if r < 50.0: return "Moderate"
    if r < 77.5: return "Elevated"
    return "High"


def main():
    df = pd.read_csv(CSV)
    df["band"] = df["risk"].apply(band)

    ins = df[df.stratum == "in_scope"]["risk"].values
    ref = df[df.stratum == "reference"]["risk"].values
    oos = df[df.stratum.isin(["out_of_scope", "boundary"])]

    # PRIMARY separation -----------------------------------------------------
    U, p = mannwhitneyu(ins, ref, alternative="greater")
    auc = U / (len(ins) * len(ref))
    print("PRIMARY - in-scope greenwashing vs rigorous")
    print(f"  n = {len(ins)} vs {len(ref)}")
    print(f"  AUC = {auc:.3f}   Mann-Whitney U = {U:.1f}   one-sided p = {p:.3f}")
    print("  (small n: demonstration, not a benchmark - CI is wide)\n")

    # BOUNDARY ---------------------------------------------------------------
    not_flagged = int((oos["risk"] < FLAG).sum())
    print("BOUNDARY - out-of-scope/boundary should NOT be flagged")
    print(f"  {not_flagged}/{len(oos)} below flag threshold ({FLAG}) -> "
          f"{'CONFIRMED' if not_flagged == len(oos) else 'PARTIAL'}\n")

    # per-case ---------------------------------------------------------------
    print("per-case bands:")
    print(df[["id", "stratum", "expectation", "risk", "band", "top_rule"]].to_string(index=False))

    fp = df[(df.stratum == "reference") & (df.risk >= FLAG)]["id"].tolist()
    fn = df[(df.stratum == "in_scope") & (df.risk < FLAG)]["id"].tolist()
    print("\nlogged findings (limitations, not fixes):")
    print(f"  false positives (rigorous flagged): {fp}")
    print(f"  false negatives (in-scope missed):  {fn}")

    # FIGURE -----------------------------------------------------------------
    FIG.mkdir(parents=True, exist_ok=True)
    order = ["in_scope", "boundary", "out_of_scope", "reference"]
    xmap = {s: i for i, s in enumerate(order)}
    colors = {"greenwashing": "#c0392b", "rigorous": "#27ae60"}
    rng = np.random.default_rng(0)  # deterministic jitter
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for _, row in df.iterrows():
        x = xmap[row.stratum] + (rng.random() - 0.5) * 0.25
        ax.scatter(x, row.risk, c=colors.get(row.group, "#888"), s=70,
                   edgecolor="black", linewidth=0.5, zorder=3)
        if row.id in ("RD-006", "GW-007", "GW-002"):
            ax.annotate(row.id, (x, row.risk), xytext=(6, 0),
                        textcoords="offset points", fontsize=8, va="center")
    for y, lbl in [(22.5, "Low|Mod"), (50, "flag (Elevated)"), (77.5, "Elev|High")]:
        ax.axhline(y, color="grey", ls="--", lw=0.8, alpha=0.6)
        ax.text(3.45, y + 1, lbl, fontsize=7, color="grey", ha="right")
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order)
    ax.set_ylabel("GreenRisk risk")
    ax.set_ylim(0, 100)
    ax.set_title(f"Held-out face validity  (primary AUC={auc:.2f}; boundary {not_flagged}/{len(oos)})")
    ax.legend(handles=[
        Line2D([0], [0], marker='o', color='w', markerfacecolor=colors['greenwashing'],
               markeredgecolor='k', label='greenwashing', markersize=9),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=colors['rigorous'],
               markeredgecolor='k', label='rigorous', markersize=9)],
        loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "face_validity.png", dpi=150)
    plt.close(fig)

    stats = {
        "instrument_tag": "rulebase-locked-v1",
        "primary": {"n_in_scope": int(len(ins)), "n_reference": int(len(ref)),
                    "auc": round(float(auc), 4), "mannwhitney_u": float(U),
                    "p_one_sided": round(float(p), 4)},
        "boundary": {"n": int(len(oos)), "n_below_flag": not_flagged,
                     "flag_threshold": FLAG, "confirmed": not_flagged == len(oos)},
        "findings": {"false_positives": fp, "false_negatives": fn},
        "per_case": df[["id", "stratum", "expectation", "risk", "band", "top_rule"]]
            .to_dict(orient="records"),
    }
    (ROOT / "artifacts" / "contrast_run" / "face_validity_stats.json").write_text(
        json.dumps(stats, indent=2))
    print(f"\nwrote {FIG / 'face_validity.png'}")
    print(f"wrote {ROOT / 'artifacts' / 'contrast_run' / 'face_validity_stats.json'}")


if __name__ == "__main__":
    main()