"""Phase 4 Step 4 — size the #3 commitment false-positive (TCFD only).

#3 is an UPSTREAM defect: the ClimateBERT commitment classifier fires ~0.997 on
generic 'our policy' boilerplate, so a vague policy statement scores High via S3
(spec Low and commit High). This is NOT a rule-base bug and is not fixed in the
fuzzy layer. Phase 4's only job: is it isolated or systematic?

Filter the larger gated sample for the signature — high commitment + low
specificity — count it, see where it lands, and print the matches to read.

Run:  uv run python scripts/validation/hash3_characterize.py -n 500 --gate 0.5
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import skfuzzy as fuzz
from datasets import load_dataset

from models import all_signals_batch, score_batch
from rule_base import score_paragraph, ANTS
from linguistic_variables import risk

COMMIT_HI = 0.90   # commitment model firing strong
SPEC_LO   = 0.40   # vague (specificity Low region)
BANDS = ["Low", "Moderate", "Elevated", "High"]


def band(score):
    memb = {t: fuzz.interp_membership(risk.universe, risk[t].mf, score) for t in BANDS}
    return max(memb, key=memb.get)


def ascii_safe(s, n=300):
    return s[:n].encode("ascii", "replace").decode() + ("..." if len(s) > n else "")


def main(n, gate, show):
    ds = load_dataset("climatebert/tcfd_recommendations")["train"]
    texts = ds["text"][:n]

    climate = [r["yes"] for r in score_batch("detector", texts)]
    kept = [(i, t) for i, (t, c) in enumerate(zip(texts, climate)) if c >= gate]
    keep_texts = [t for _, t in kept]
    print(f"gate>={gate}: kept {len(kept)}/{len(texts)} climate paras")

    cols = all_signals_batch(keep_texts)
    signals = [{v: cols[v][j] for v in ANTS} for j in range(len(keep_texts))]

    commit_hi = 0
    flagged = []   # the #3 signature: high commitment AND vague
    band_counts = {b: 0 for b in BANDS}
    for (orig_i, text), sig in zip(kept, signals):
        if sig["commitment"] >= COMMIT_HI:
            commit_hi += 1
            if sig["specificity"] <= SPEC_LO:
                score, trace = score_paragraph(sig)
                b = band(score)
                band_counts[b] += 1
                top = trace[0]["rule"] if trace else "--"
                flagged.append((orig_i, text, sig, score, b, top))

    n_kept = len(kept)
    print(f"\ncommitment >= {COMMIT_HI:.2f} (model fires strong) : {commit_hi}/{n_kept}")
    print(f"  AND specificity <= {SPEC_LO:.2f} (the #3 signature) : {len(flagged)}/{n_kept}")
    print(f"  risk bands among the signature: "
          + ", ".join(f"{b}={band_counts[b]}" for b in BANDS))

    flagged.sort(key=lambda r: r[3], reverse=True)
    print(f"\n--- {min(show, len(flagged))} highest-scoring matches "
          f"(read to confirm same failure mode as #3) ---")
    for orig_i, text, sig, score, b, top in flagged[:show]:
        print(f"\n#{orig_i}  RISK={score} ({b})  top={top}  "
              f"spec={sig['specificity']:.3f} commit={sig['commitment']:.3f}")
        print("  " + ascii_safe(text))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=500, help="paragraphs to consider (pre-gate)")
    ap.add_argument("--gate", type=float, default=0.5)
    ap.add_argument("--show", type=int, default=8, help="how many matches to print")
    a = ap.parse_args()
    main(a.n, a.gate, a.show)
