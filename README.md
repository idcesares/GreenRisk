# GreenRisk

Explainable greenwashing-risk scoring for corporate climate disclosures:
pinned ClimateBERT signals → a Mamdani fuzzy rule base → an auditable 0–100 risk
score with a W3C PROV-O provenance graph.

**Start here:** [`MASTER_PLAN.md`](MASTER_PLAN.md) — the canonical end-to-end map
(architecture, the locked instrument, repo layout, phase roadmap, and the
decisions index).

Instrument status: frozen at tag `rulebase-locked-v1`.

## Repository Map

- `models.py`, `linguistic_variables.py`, `rule_base.py` — locked scoring
  instrument.
- `main.py` — small CLI for scoring already-computed signal probabilities.
- `scripts/` — artifact producers for figures, full-corpus runs, contrast-set
  runs, baselines, and provenance.
- `scripts/validation/` — validation harnesses for anchors, hash behavior, and
  integrated scoring.
- `data/contrast_set.csv` — held-out contrast set used after the lock.
- `artifacts/` — committed outputs used by the validity argument.
- `docs/` — reserved for polished public documentation.

## Quick Start

```powershell
uv sync
uv run python main.py --specificity 0.20 --commitment 0.90 --sentiment-asymmetry 0.40 --netzero 0.70
uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
```

The CLI path does not load ClimateBERT; it scores four precomputed signal values
through the locked Mamdani rule base and prints the rule-activation trace. Scripts
that call `models.py` may download/load the pinned Hugging Face model revisions on
first run.
