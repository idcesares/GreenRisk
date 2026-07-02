# GreenRisk

Explainable greenwashing-risk scoring for corporate climate disclosures:
pinned ClimateBERT signals → a Mamdani fuzzy rule base → an auditable 0–100 risk
score with a W3C PROV-O provenance graph.

Every score ships with an activation trace showing exactly which rules fired
and why, and a provenance graph binding the result to the exact model
revisions and instrument version that produced it. Nothing is a black box.

Instrument status: frozen at tag `rulebase-locked-v1`.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — the full pipeline: the
  climate-relevance gate, the four signals, the fuzzy rule base, and the
  design rationale behind it.
- [`docs/validation.md`](docs/validation.md) — the validity evidence: a
  large-scale statistical comparison against a published baseline, and a
  held-out test against real, regulator-adjudicated cases, including the
  instrument's documented scope limitation.
- [`docs/acknowledgements.md`](docs/acknowledgements.md) — citations for the
  ClimateBERT models, datasets, and standards this project builds on.
- [`MASTER_PLAN.md`](MASTER_PLAN.md) — the repository map, the locked
  instrument at a glance, and exact reproduction commands.

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
- `docs/` — public documentation (architecture, validation, acknowledgements).

## Quick Start

```powershell
uv sync
uv run python main.py --specificity 0.20 --commitment 0.90 --sentiment-asymmetry 0.40 --netzero 0.70
uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
```

The CLI path does not load ClimateBERT; it scores four precomputed signal values
through the locked Mamdani rule base and prints the rule-activation trace. Scripts
that call `models.py` may download/load the pinned Hugging Face model revisions on
first run. Inference uses a GPU automatically if one is available and falls back to
CPU otherwise — a GPU is not required.

## Citation

If you use GreenRisk, please cite it using [`CITATION.cff`](CITATION.cff)
(GitHub renders a "Cite this repository" button from this file). See
[`docs/acknowledgements.md`](docs/acknowledgements.md) for the papers and
models this project is built on.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE). The underlying ClimateBERT
models are also Apache 2.0 licensed; see
[`docs/acknowledgements.md`](docs/acknowledgements.md) for full citations.
