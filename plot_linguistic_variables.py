"""Render and save the membership-function plots for all fuzzy variables.

Writes one PNG per variable (methodology figures). Uses the non-interactive
Agg backend so it writes files without opening windows or blocking on show().
"""

import matplotlib
matplotlib.use("Agg")  # render to file; no GUI windows, no blocking
import matplotlib.pyplot as plt

from linguistic_variables import (
    specificity, commitment, sentiment_asymmetry, netzero, risk,
    specificity_trap,
)

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
    fig.savefig(filename, dpi=150, bbox_inches="tight")
    plt.close(fig)                              # free it; don't leak figures in the loop
    print(f"saved {filename}")