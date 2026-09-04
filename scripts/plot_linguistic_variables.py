"""Render and save the membership-function plots for all fuzzy variables.

Writes one PNG per variable (methodology figures). Uses the non-interactive
Agg backend so it writes files without opening windows or blocking on show().
"""

import pathlib

import matplotlib

matplotlib.use("Agg")  # render to file; no GUI windows, no blocking
import matplotlib.pyplot as plt

from greenrisk.linguistic_variables import (
    commitment,
    netzero,
    risk,
    sentiment_asymmetry,
    specificity,
    specificity_trap,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "artifacts" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# filename -> the variable to plot
FIGURES = {
    "mf_specificity.png":         specificity,
    "mf_commitment.png":          commitment,
    "mf_sentiment_asymmetry.png": sentiment_asymmetry,
    "mf_netzero.png":             netzero,
    "mf_risk.png":                risk,
    "mf_specificity_trap.png":    specificity_trap,
}

for filename, var in FIGURES.items():
    var.view()                                  # skfuzzy draws the MFs on a new figure
    fig = plt.gcf()                             # grab the figure view() just created
    fig.savefig(FIG_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)                              # free it; don't leak figures in the loop
    print(f"saved {FIG_DIR / filename}")
