"""Score the held-out contrast set through the frozen instrument.

ONE-SHOT held-out evaluation. The instrument (rulebase-locked-v1) has never seen
this set. The pre-registration (stratum + expectation per case) is hardcoded below
and was fixed BEFORE this script was run, so the held-out line is auditable. See
docs/validation.md for the stratification rationale.

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
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import pandas as pd
from datasets import logging as _hf_logging  # noqa: F401  (quiet import parity)

from models import score_batch, all_signals_batch, MODEL_REGISTRY
from rule_base import score_paragraph, ANTS

INSTRUMENT_TAG = "rulebase-locked-v1"

# --- PRE-REGISTRATION (fixed before scoring; see docs/validation.md) ----------
# id -> (stratum, expectation). Frozen before scoring; NOT revised after scores.
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


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def main(gate: float, batch_size: int):
    root = pathlib.Path(__file__).resolve().parents[1]
    df = pd.read_csv(root / "data" / "contrast_set.csv")
    texts = df["paragraph"].tolist()
    print(f"contrast set: {len(texts)} paragraphs (held-out, first instrument contact)")

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
        stratum, expect = PREREG.get(df["id"][i], ("?", "?"))
        rows.append({
            "id": df["id"][i],
            "group": df["group"][i],
            "stratum": stratum,
            "expectation": expect,
            "company": df["source_company"][i],
            "climate_p": round(climate[i], 4),
            "gate_pass": bool(climate[i] >= gate),
            "specificity": round(sig["specificity"], 4),
            "commitment": round(sig["commitment"], 4),
            "sentiment_asymmetry": round(sig["sentiment_asymmetry"], 4),
            "netzero": round(sig["netzero"], 4),
            "risk": risk_score,
            "top_rule": trace[0]["rule"] if trace else "",
            "fired_rules": "|".join(f"{x['rule']}:{x['fire']:.2f}" for x in trace),
            "sha12": sha12(t),
        })

    out = pd.DataFrame(rows)
    out_dir = root / "artifacts" / "contrast_run"
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / "contrast_scored.csv", index=False)

    manifest = {
        "instrument_tag": INSTRUMENT_TAG,
        "dataset": "data/contrast_set.csv (held-out)",
        "gate": gate,
        "batch_size": batch_size,
        "n": len(texts),
        "n_gate_pass": int(out["gate_pass"].sum()),
        "prereg_ratified": "2026-06-17",
        "model_hashes": {k: v["revision"] for k, v in MODEL_REGISTRY.items()},
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"\nwrote {out_dir / 'contrast_scored.csv'}  ({len(out)} rows)")
    print(f"gate>={gate}: {int(out['gate_pass'].sum())}/{len(out)} passed\n")
    print("risk by stratum:")
    print(out.groupby("stratum")["risk"].agg(["count", "mean", "min", "max"]).round(2).to_string())
    print("\nper-case (pre-registration vs. observed):")
    cols_show = ["id", "stratum", "expectation", "gate_pass",
                 "specificity", "commitment", "netzero", "risk", "top_rule"]
    print(out[cols_show].to_string(index=False))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", type=float, default=0.5)
    ap.add_argument("--batch-size", type=int, default=32)
    a = ap.parse_args()
    main(a.gate, a.batch_size)