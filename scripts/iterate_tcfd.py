"""W2 Phase 3 — first traced inference over real TCFD paragraphs.

Scores climate-gated paragraphs of climatebert/tcfd_recommendations through the
locked fuzzy rule base and prints each paragraph's activation trace. This is the
§6 step-2 deliverable and the raw input to the Phase 3 decision log.

Iteration runs on TCFD ONLY — the contrast set stays sealed until W4 (§6.3).
"""
import argparse
import pathlib
import sys

# Repo root on the path so core modules import when run from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from datasets import load_dataset

from models import all_signals_batch, score_batch
from rule_base import score_paragraph, format_trace, ANTS


def main(n: int, gate: float):
    ds = load_dataset("climatebert/tcfd_recommendations")["train"]
    texts = ds["text"][:n]

    # Climate-relevance gate — rule_base assumes this happened upstream.
    # One batched detector pass; keep only paragraphs that ARE climate text.
    climate = [r["yes"] for r in score_batch("detector", texts)]
    kept = [(i, t) for i, (t, c) in enumerate(zip(texts, climate)) if c >= gate]
    print(f"gate>={gate}: kept {len(kept)}/{len(texts)} "
          f"({len(texts) - len(kept)} non-climate dropped)")

    keep_texts = [t for _, t in kept]
    cols = all_signals_batch(keep_texts)                  # {var: [...]}, gated only
    signals = [{v: cols[v][j] for v in ANTS} for j in range(len(keep_texts))]

    for (orig_i, text), sig in zip(kept, signals):
        score, trace = score_paragraph(sig)
        print(f"\n===== TCFD #{orig_i}  (RISK={score}) =====")
        print(text[:300].encode("ascii", "replace").decode()
              + ("..." if len(text) > 300 else ""))
        print(format_trace(sig, score, trace))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=30, help="paragraphs to consider (pre-gate)")
    ap.add_argument("--gate", type=float, default=0.5, help="min is_climate to score")
    main(ap.parse_args().n, ap.parse_args().gate)