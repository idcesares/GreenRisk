"""Score the held-out contrast set through the frozen instrument.

Post-lock contrast-set evaluation. The expectations embedded below were not used
to tune the frozen instrument. They and the first public results were committed
together, however, so this is not described as an externally timestamped blind
pre-registration. See docs/validation.md for the protocol and its limitations.

Evaluated downstream as:
  PRIMARY  - in-scope greenwashing (vagueness-based) vs rigorous: expect separation
  BOUNDARY - out-of-scope greenwashing (specificity/omission): predicted misses

Reuses the same frozen scoring path as the full-corpus run. No instrument change.
All 15 paragraphs are scored; gate status is recorded, NOT used to drop rows (so
gate-outs stay visible).

Inputs:  data/contrast_set.csv  (+ PREREG below)
Outputs: artifacts/contrast_run/contrast_scored.csv + run_manifest.json

Run:  uv run python scripts/run_contrast_set.py --gate 0.5
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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd
from datasets import logging as _hf_logging  # noqa: F401  (quiet import parity)

from greenrisk import __version__
from greenrisk.metadata import INSTRUMENT_COMMIT, INSTRUMENT_TAG, MODEL_REGISTRY
from greenrisk.models import DEVICE, all_signals_batch, score_batch
from greenrisk.rule_base import ANTS, score_paragraph

# --- RECORDED EXPECTATIONS (not used for tuning; see docs/validation.md) ------
# id -> (stratum, expectation). Do not revise these historical expectations.
PREREG = {
    "GW-001": ("in_scope",     "elevated"),
    "GW-002": ("in_scope",     "elevated"),
    "GW-003": ("in_scope",     "elevated"),
    "GW-005": ("in_scope",     "moderate_elevated"),
    "GW-007": ("in_scope",     "elevated"),          # caveat: short text
    "GW-006": ("boundary",     "uncertain"),         # probes O-tier
    "GW-004": ("out_of_scope", "low"),               # predicted miss
    "GW-008": ("out_of_scope", "low"),               # predicted miss
    "GW-009": ("out_of_scope", "low"),               # predicted miss
    "RD-001": ("reference",    "low"),
    "RD-002": ("reference",    "low"),
    "RD-003": ("reference",    "low"),
    "RD-004": ("reference",    "low"),
    "RD-005": ("reference",    "low"),
    "RD-006": ("reference",    "low"),               # caveat: may gate out
}


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
    dataset_path = root / "data" / "contrast_set.csv"
    df = pd.read_csv(dataset_path)
    expected_ids = set(PREREG)
    received_ids = set(df["id"])
    if received_ids != expected_ids:
        raise ValueError(
            "contrast-set IDs do not match the frozen protocol: "
            f"missing={sorted(expected_ids - received_ids)}, "
            f"unexpected={sorted(received_ids - expected_ids)}"
        )
    texts = df["paragraph"].tolist()
    print(f"contrast set: {len(texts)} paragraphs (post-lock evaluation)")

    # Stage 1 - climate gate (recorded, not used to drop)
    climate = [r["yes"] for r in score_batch("detector", texts, batch_size=batch_size)]
    # Stage 2 - four scorers (batched), all paragraphs
    cols = all_signals_batch(texts, batch_size=batch_size)
    assert set(cols) == set(ANTS), "scorer keys != fuzzy input keys"

    # Stages 3+4 - fuzzy score + trace per paragraph
    rows = []
    for i, t in enumerate(texts):
        sig = {v: cols[v][i] for v in ANTS}
        risk_score, trace = score_paragraph(sig)
        stratum, expect = PREREG[df["id"][i]]
        rows.append({
            "id": df["id"][i],
            "group": df["group"][i],
            "stratum": stratum,
            "expectation": expect,
            "company": df["source_company"][i],
            "climate_p": climate[i],
            "gate_pass": bool(climate[i] >= gate),
            "specificity": sig["specificity"],
            "commitment": sig["commitment"],
            "sentiment_asymmetry": sig["sentiment_asymmetry"],
            "netzero": sig["netzero"],
            "risk": risk_score,
            "top_rule": trace[0]["rule"] if trace else "",
            "fired_rules": json.dumps(trace, separators=(",", ":")),
            "text_sha256": sha256_text(t),
        })

    out = pd.DataFrame(rows)
    out_dir = root / "artifacts" / "contrast_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "contrast_scored.csv"
    out.to_csv(csv_path, index=False, lineterminator="\n")

    manifest = {
        "schema_version": "2.0",
        "software_version": __version__,
        "source": git_state(root),
        "instrument_tag": INSTRUMENT_TAG,
        "instrument_commit": INSTRUMENT_COMMIT,
        "dataset": "data/contrast_set.csv",
        "dataset_sha256": sha256_file(dataset_path),
        "gate": gate,
        "batch_size": batch_size,
        "n": len(texts),
        "n_gate_pass": int(out["gate_pass"].sum()),
        "protocol_status": (
            "expectations recorded in the same public commit as first results; "
            "not an externally timestamped preregistration"
        ),
        "expectations_recorded": "2026-06-17",
        "model_repositories": {k: v["repo"] for k, v in MODEL_REGISTRY.items()},
        "model_revisions": {k: v["revision"] for k, v in MODEL_REGISTRY.items()},
        "environment": {
            "python": platform.python_version(),
            "device": DEVICE,
            "torch": importlib.metadata.version("torch"),
            "transformers": importlib.metadata.version("transformers"),
        },
        "uv_lock_sha256": sha256_file(root / "uv.lock"),
        "outputs": {csv_path.name: {"sha256": sha256_file(csv_path), "rows": len(out)}},
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"\nwrote {out_dir / 'contrast_scored.csv'}  ({len(out)} rows)")
    print(f"gate>={gate}: {int(out['gate_pass'].sum())}/{len(out)} passed\n")
    print("risk by stratum:")
    print(out.groupby("stratum")["risk"].agg(["count", "mean", "min", "max"]).round(2).to_string())
    print("\nper-case (recorded expectation vs. observed):")
    cols_show = ["id", "stratum", "expectation", "gate_pass",
                 "specificity", "commitment", "netzero", "risk", "top_rule"]
    print(out[cols_show].to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", type=float, default=0.5)
    ap.add_argument("--batch-size", type=int, default=32)
    a = ap.parse_args()
    main(a.gate, a.batch_size)
