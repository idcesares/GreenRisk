"""W2 Phase 4 Step 2 — membership-function experiment (triangular vs trapezoidal).

Settles the last open instrument decision. The rule base is held FIXED; the only
thing that varies is the specificity input MF:
  - triangular  : Low = trimf  [0, 0, 0.4]         (the locked instrument)
  - trapezoidal : Low = trapmf [0, 0, 0.15, 0.4]   (plateau over the near-0 pile-up)
Medium/High and the other three inputs are identical in both. We score the SAME
gated TCFD batch under each and compare distribution, per-band counts, and the
decision-relevant number: how many paragraphs change band.

Default: triangular wins unless trapezoidal materially changes discrimination.

Run:  uv run python scripts/validation/mf_experiment.py -n 200 --gate 0.5
"""
import argparse
import functools
import operator
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import skfuzzy as fuzz
from datasets import load_dataset
from skfuzzy import control as ctrl

from models import all_signals_batch, score_batch
from rule_base import RULES, RISK, ANTS as TRI_ANTS, score_paragraph
from linguistic_variables import (
    specificity_trap, commitment, sentiment_asymmetry, netzero, risk,
)

# Trapezoidal antecedent set: specificity swapped, the other three unchanged.
TRAP_ANTS = {
    "specificity": specificity_trap,
    "commitment": commitment,
    "sentiment_asymmetry": sentiment_asymmetry,
    "netzero": netzero,
}

BANDS = ["Low", "Moderate", "Elevated", "High"]


def build_system(ants):
    """Compile RULES against a given antecedent set (same rules, swapped MFs)."""
    rules = []
    for rid, terms, consequent, _note in RULES:
        ant = functools.reduce(operator.and_, [ants[v][t] for v, t in terms])
        rules.append(ctrl.Rule(ant, RISK[consequent], label=rid))
    return ctrl.ControlSystem(rules)


def score_with(system, ants, signals):
    """Defuzzified risk under `system`. Feeds each input by its antecedent's
    real label, so specificity_trap (label 'specificity_trap') wires up too."""
    sim = ctrl.ControlSystemSimulation(system)
    for var, value in signals.items():
        sim.input[ants[var].label] = value
    sim.compute()
    return round(float(sim.output["risk"]), 2)


def band(score):
    """Linguistic band = output term with highest membership at this score."""
    memb = {t: fuzz.interp_membership(risk.universe, risk[t].mf, score) for t in BANDS}
    return max(memb, key=memb.get)


def main(n, gate):
    ds = load_dataset("climatebert/tcfd_recommendations")["train"]
    texts = ds["text"][:n]

    climate = [r["yes"] for r in score_batch("detector", texts)]
    kept_texts = [t for t, c in zip(texts, climate) if c >= gate]
    print(f"gate>={gate}: {len(kept_texts)}/{len(texts)} climate paras\n")

    cols = all_signals_batch(kept_texts)
    signals = [{v: cols[v][j] for v in TRI_ANTS} for j in range(len(kept_texts))]

    trap_system = build_system(TRAP_ANTS)

    tri_scores, trap_scores, crossings = [], [], []
    tri_bands = {b: 0 for b in BANDS}
    trap_bands = {b: 0 for b in BANDS}

    for j, sig in enumerate(signals):
        s_tri, _ = score_paragraph(sig)              # locked triangular instrument
        s_trap = score_with(trap_system, TRAP_ANTS, sig)
        b_tri, b_trap = band(s_tri), band(s_trap)
        tri_scores.append(s_tri); trap_scores.append(s_trap)
        tri_bands[b_tri] += 1; trap_bands[b_trap] += 1
        if b_tri != b_trap:
            crossings.append((j, sig["specificity"], s_tri, s_trap, b_tri, b_trap))

    def stats(xs):
        return (statistics.mean(xs), statistics.pstdev(xs), min(xs), max(xs))

    m1, sd1, lo1, hi1 = stats(tri_scores)
    m2, sd2, lo2, hi2 = stats(trap_scores)
    print("score distribution (spread matters more than mean):")
    print(f"  triangular   mean={m1:6.2f}  sd={sd1:5.2f}  range=[{lo1:.2f}, {hi1:.2f}]")
    print(f"  trapezoidal  mean={m2:6.2f}  sd={sd2:5.2f}  range=[{lo2:.2f}, {hi2:.2f}]")

    print("\nper-band counts:")
    print(f"  {'band':<10}{'triangular':>12}{'trapezoidal':>13}")
    for b in BANDS:
        print(f"  {b:<10}{tri_bands[b]:>12}{trap_bands[b]:>13}")

    print(f"\nboundary crossings (THE decision number): {len(crossings)}/{len(signals)}")
    for j, spec, s_tri, s_trap, b_tri, b_trap in crossings:
        print(f"  #{j:<3} spec={spec:.3f}  {s_tri:6.2f} ({b_tri}) -> "
              f"{s_trap:6.2f} ({b_trap})")
    if not crossings:
        print("  none — trapezoidal leaves band assignments unchanged.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=200, help="paragraphs to consider (pre-gate)")
    ap.add_argument("--gate", type=float, default=0.5)
    a = ap.parse_args()
    main(a.n, a.gate)