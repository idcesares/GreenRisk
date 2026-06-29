"""Phase 5 Step 1 — full-corpus production run of the locked instrument.

Runs rulebase-locked-v1 over the ENTIRE TCFD corpus (not a sample), persisting
one row per gated paragraph: the four signals, the risk score, and the fired-
rule trace. This is the per-run wiring that follows the Phase 4 seam test.

Output:
  artifacts/corpus_run/tcfd_scored.csv     one row per gated paragraph
  artifacts/corpus_run/run_manifest.json   gate, counts, model hashes, tag, ts

Run:  uv run python scripts/run_full_corpus.py --gate 0.5
"""
import argparse
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

# Repo root on the path so core modules import when run from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd
from datasets import load_dataset

from models import score_batch, all_signals_batch, MODEL_REGISTRY
from rule_base import score_paragraph, ANTS

INSTRUMENT_TAG = "rulebase-locked-v1"


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def main(gate: float, batch_size: int):
    ds = load_dataset("climatebert/tcfd_recommendations")["train"]
    texts = list(ds["text"])
    categories = [ds.features["label"].names[i] for i in ds["label"]]
    print(f"corpus: {len(texts)} paragraphs")

    # Stage 1 - climate gate (one batched detector pass)
    climate = [r["yes"] for r in score_batch("detector", texts, batch_size=batch_size)]
    keep_idx = [i for i, c in enumerate(climate) if c >= gate]
    keep_texts = [texts[i] for i in keep_idx]
    print(f"gate>={gate}: kept {len(keep_idx)}/{len(texts)} "
          f"({len(texts) - len(keep_idx)} non-climate dropped)")

    # Stage 2 - four scorers (batched), aligned to keep_texts
    cols = all_signals_batch(keep_texts, batch_size=batch_size)
    assert set(cols) == set(ANTS), "scorer keys != fuzzy input keys"

    # Stages 3+4 - fuzzy score + trace per gated paragraph
    rows = []
    for j, i in enumerate(keep_idx):
        sig = {v: cols[v][j] for v in ANTS}
        risk_score, trace = score_paragraph(sig)
        trace_str = "|".join(f"{t['rule']}:{t['fire']:.2f}" for t in trace)
        rows.append({
            "row": i,
            "sha12": sha12(texts[i]),
            "tcfd_category": categories[i],
            "climate_p": round(climate[i], 4),
            "specificity": round(sig["specificity"], 4),
            "commitment": round(sig["commitment"], 4),
            "sentiment_asymmetry": round(sig["sentiment_asymmetry"], 4),
            "netzero": round(sig["netzero"], 4),
            "risk": risk_score,
            "n_fired": len(trace),
            "top_rule": trace[0]["rule"] if trace else "",
            "top_fire": trace[0]["fire"] if trace else 0.0,
            "fired_rules": trace_str,
            "text": texts[i],
        })

    df = pd.DataFrame(rows)
    out_dir = pathlib.Path(__file__).resolve().parents[1] / "artifacts" / "corpus_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "tcfd_scored.csv"
    df.to_csv(csv_path, index=False)

    manifest = {
        "instrument_tag": INSTRUMENT_TAG,
        "dataset": "climatebert/tcfd_recommendations",
        "gate": gate,
        "batch_size": batch_size,
        "n_total": len(texts),
        "n_kept": len(keep_idx),
        "model_hashes": {k: v["revision"] for k, v in MODEL_REGISTRY.items()},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Summary
    print(f"\nwrote {csv_path}  ({len(df)} rows)")
    print(f"wrote {manifest_path}")
    print("\nrisk distribution:")
    print(df["risk"].describe()[["mean", "min", "25%", "50%", "75%", "max"]].round(2).to_string())
    print("\nrisk by TCFD category (count, mean):")
    print(df.groupby("tcfd_category")["risk"].agg(["count", "mean"]).round(2).to_string())
    print("\ntop fired rule frequency:")
    print(df["top_rule"].value_counts().to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", type=float, default=0.5)
    ap.add_argument("--batch-size", type=int, default=32)
    a = ap.parse_args()
    main(a.gate, a.batch_size)
