"""Calibration Anchor 1 verification (locked instrument).

Anchor 1 = the classic vague net-zero pledge signature (specificity Low,
commitment Low, netzero High). Its original expectation, 'fires
highest-risk', predates the rule that demotes S1 for claim-less vague text
(see docs/architecture.md). This runs it on the locked (triangular)
instrument and reports the three things a calibration check needs: does it
still max, via which rules, and is it spine- or signature-driven.

Contrast set stays sealed — Anchor 1 is a pre-registered signal profile, not a
corpus paragraph.

Run:  uv run python scripts/validation/anchor_verify.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from rule_base import score_paragraph, format_trace

# Pre-registered profile + expectation.
# sentiment is Low and inert here (the net-zero/spine rules cap the score); set
# Low for a clean 'bare pledge'. Score is 60.38 for any sentiment value.
ANCHOR1 = {"specificity": 0.05, "commitment": 0.05,
           "sentiment_asymmetry": 0.05, "netzero": 0.95}
REGISTERED = "fires highest-risk (maximal, ~90) — the original, pre-lock expectation"

HIGH_BAND = 80.0   # 'maxes' threshold


def main():
    score, trace = score_paragraph(ANCHOR1)
    print("CALIBRATION ANCHOR 1 — vague net-zero pledge")
    print(f"pre-registered expectation: {REGISTERED}\n")
    print(format_trace(ANCHOR1, score, trace))

    fired = {t["rule"]: t for t in trace}
    maxes = score >= HIGH_BAND
    spine = [r for r in fired if r.startswith("S")]          # graded spine cells
    signatures = [r for r in fired if r.startswith("G")]     # named signatures
    high_drivers = [r for r, t in fired.items() if t["consequent"] == "High"]

    print("\n--- resolution ---")
    print(f"still maxes (>= {HIGH_BAND:.0f})? : {maxes}  (RISK={score})")
    print(f"High-consequent rules firing : {high_drivers}")
    print(f"named signatures firing      : {signatures}")
    print(f"graded spine co-firing       : {spine}")
    if signatures and spine:
        verdict = ("spine + signature: graded logic engaged (S-rules co-fire), "
                   "named signature legible but NOT sole driver — healthy anchor")
    elif signatures and not spine:
        verdict = ("signature-driven ONLY: calibration depends on a hardcoded "
                   "signature firing, not the graded logic — weaker anchor")
    else:
        verdict = "spine-driven: no named signature fired"
    print(f"verdict                      : {verdict}")


if __name__ == "__main__":
    main()
