"""Empirical sanity check for the fuzzy-input breakpoints.

Scores ~200 real TCFD paragraphs through the four fuzzy-input signals in
batches (GPU if available, otherwise CPU — see models.DEVICE) and plots each
distribution with the 0.4 / 0.6 breakpoints overlaid. Writes four PNGs and
prints summary stats for classifying each.
"""

import pathlib
import sys

# Repo root on the path so core modules import when run from anywhere.
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FIG_DIR = ROOT / "artifacts" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from datasets import load_dataset

import models
from models import all_signals_batch, SIGNAL_MAP

N = 200

ds = load_dataset("climatebert/tcfd_recommendations")
sample = ds["test"]["text"][:N]
print(f"Scoring {len(sample)} TCFD paragraphs x 4 models on {models.DEVICE} (batched)...")

scores = all_signals_batch(sample, batch_size=32)

for var, values in scores.items():
    values = np.array(values)

    plt.figure()
    plt.hist(values, bins=20, range=(0, 1), edgecolor="black")
    plt.axvline(0.4, color="red", linestyle="--", label="Low / Medium (0.4)")
    plt.axvline(0.6, color="red", linestyle="--", label="Medium / High (0.6)")
    plt.xlabel(f"signal: {var}")
    plt.ylabel("paragraph count")
    plt.title(f"{var} on TCFD sample (n={len(values)})")
    plt.legend()
    plt.savefig(FIG_DIR / f"dist_{var}.png", dpi=150, bbox_inches="tight")
    plt.close()

    low  = (values < 0.4).mean()
    med  = ((values >= 0.4) & (values <= 0.6)).mean()
    high = (values > 0.6).mean()
    print(f"\n{var}: saved dist_{var}.png")
    print(f"  mean={values.mean():.3f}  median={np.median(values):.3f}")
    print(f"  Low(<0.4)={low:.0%}  Medium(0.4-0.6)={med:.0%}  High(>0.6)={high:.0%}")