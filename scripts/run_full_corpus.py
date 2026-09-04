"""Full-corpus production run of the locked instrument.

Runs rulebase-locked-v1 over the ENTIRE TCFD corpus (not a sample), persisting
one row per gated paragraph: the four signals, the risk score, and the fired-
rule trace. This is the per-run wiring that follows
scripts/validation/integration_seam_test.py.

Output:
  artifacts/corpus_run/tcfd_scored.csv     one row per gated paragraph
  artifacts/corpus_run/run_manifest.json   gate, counts, model hashes, tag, ts

Run:  uv run python scripts/run_full_corpus.py --gate 0.5
"""
import argparse
import hashlib
import importlib.metadata
import json
import pathlib
import platform
import subprocess
import sys
from datetime import UTC, datetime

# Repo root on the path so core modules import when run from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd
from datasets import load_dataset

from greenrisk import __version__
from greenrisk.metadata import (
    INSTRUMENT_COMMIT,
    INSTRUMENT_TAG,
    MODEL_REGISTRY,
    TCFD_DATASET_ID,
    TCFD_DATASET_REVISION,
    TCFD_TRAIN_SHA256,
)
from greenrisk.models import DEVICE, all_signals_batch, score_batch
from greenrisk.rule_base import ANTS, score_paragraph


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_state(root: pathlib.Path) -> dict[str, str | bool]:
    """Return the exact source revision when running from a Git checkout."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": "unavailable", "dirty": "unavailable"}


def main(gate: float, batch_size: int):
    root = pathlib.Path(__file__).resolve().parents[1]
    ds = load_dataset(TCFD_DATASET_ID, revision=TCFD_DATASET_REVISION)["train"]
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
        rows.append({
            "row": i,
            "text_sha256": sha256_text(texts[i]),
            "tcfd_category": categories[i],
            "climate_p": climate[i],
            "specificity": sig["specificity"],
            "commitment": sig["commitment"],
            "sentiment_asymmetry": sig["sentiment_asymmetry"],
            "netzero": sig["netzero"],
            "risk": risk_score,
            "n_fired": len(trace),
            "top_rule": trace[0]["rule"] if trace else "",
            "top_fire": trace[0]["fire"] if trace else 0.0,
            "fired_rules": json.dumps(trace, separators=(",", ":")),
            "text": texts[i],
        })

    df = pd.DataFrame(rows)
    out_dir = root / "artifacts" / "corpus_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "tcfd_scored.csv"
    df.to_csv(csv_path, index=False, lineterminator="\n")

    manifest = {
        "schema_version": "2.0",
        "software_version": __version__,
        "source": git_state(root),
        "instrument_tag": INSTRUMENT_TAG,
        "instrument_commit": INSTRUMENT_COMMIT,
        "dataset": TCFD_DATASET_ID,
        "dataset_revision": TCFD_DATASET_REVISION,
        "dataset_train_sha256": TCFD_TRAIN_SHA256,
        "gate": gate,
        "batch_size": batch_size,
        "n_total": len(texts),
        "n_kept": len(keep_idx),
        "model_repositories": {k: v["repo"] for k, v in MODEL_REGISTRY.items()},
        "model_revisions": {k: v["revision"] for k, v in MODEL_REGISTRY.items()},
        "environment": {
            "python": platform.python_version(),
            "device": DEVICE,
            "torch": importlib.metadata.version("torch"),
            "transformers": importlib.metadata.version("transformers"),
        },
        "uv_lock_sha256": sha256_file(root / "uv.lock"),
        "outputs": {csv_path.name: {"sha256": sha256_file(csv_path), "rows": len(df)}},
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")

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
