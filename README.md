# GreenRisk

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21122389.svg)](https://doi.org/10.5281/zenodo.21122389)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

Explainable greenwashing-risk scoring for corporate climate disclosures:
pinned ClimateBERT signals → a Mamdani fuzzy rule base → an auditable 0–100 risk
score with a W3C PROV-O provenance graph.

Every score ships with an activation trace showing exactly which rules fired
and why, and a provenance graph binding the result to the exact model
revisions and instrument version that produced it. Nothing is a black box.

Instrument status: frozen at tag `rulebase-locked-v1`.

## Paper

**GreenRisk: An Explainable-by-Construction Fuzzy Instrument for Scoring
Greenwashing Risk in Corporate Climate Disclosures.** Isaac D'Césares de
Carvalho Lima, Maria Luiza Machado Campos, and Sérgio Manuel Serra da Cruz.
Programa de Pós-Graduação em Informática (PPGI), Universidade Federal do Rio de
Janeiro, 2026. → [`docs/greenrisk_paper.pdf`](docs/greenrisk_paper.pdf)

The paper reports the instrument's design and its two-layer evaluation: a
convergent/discriminant comparison against the Bingler et al. cheap-talk
baseline on 1,009 climate-gated TCFD paragraphs (Spearman ρ = 0.602; ρ = 0.433
between risk and commitment inside the baseline's vaguest quartile), and a
held-out, one-shot test on 15 regulator-adjudicated and third-party-verified
cases (AUC = 0.867, n = 5 vs. 6). Every figure it reports is reproducible from
this repository — see [`MASTER_PLAN.md`](MASTER_PLAN.md) for the commands and
[`docs/decisions.md`](docs/decisions.md) for the `DL-00x` decisions it cites.

## Documentation

- [`docs/greenrisk_paper.pdf`](docs/greenrisk_paper.pdf) — the final project
  paper (see [Paper](#paper) above).
- [`docs/architecture.md`](docs/architecture.md) — the full pipeline: the
  climate-relevance gate, the four signals, the fuzzy rule base, and the
  design rationale behind it.
- [`docs/validation.md`](docs/validation.md) — the validity evidence: a
  large-scale statistical comparison against a published baseline, and a
  held-out test against real, regulator-adjudicated cases, including the
  instrument's documented scope limitation.
- [`docs/decisions.md`](docs/decisions.md) — the decision record: every
  instrument decision with the evidence behind it, the alternatives rejected,
  the lock, and the blind pre-registration of the held-out test.
- [`docs/ai-usage.md`](docs/ai-usage.md) — how generative AI was and was not
  used in building this artifact, and what makes that division checkable.
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
- `tests/` — smoke tests, plus `property_test_rule_base.py`, which checks the
  locked rule base's stated properties without downloading any model.
- `docs/` — public documentation, the decision record, and the project paper.

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

If you use GreenRisk, cite the paper:

> Isaac D'Césares de Carvalho Lima, Maria Luiza Machado Campos, and Sérgio
> Manuel Serra da Cruz. *GreenRisk: An Explainable-by-Construction Fuzzy
> Instrument for Scoring Greenwashing Risk in Corporate Climate Disclosures.*
> Programa de Pós-Graduação em Informática (PPGI), Universidade Federal do Rio
> de Janeiro, 2026.

To cite the software itself, use [`CITATION.cff`](CITATION.cff)
(GitHub renders a "Cite this repository" button from this file), or its
Zenodo archive: **10.5281/zenodo.21122389** — this concept DOI always
resolves to the latest release; see the
[Zenodo record](https://doi.org/10.5281/zenodo.21122389) for version-specific
DOIs (e.g. v0.1.0 is `10.5281/zenodo.21122390`). See
[`docs/acknowledgements.md`](docs/acknowledgements.md) for the papers and
models this project is built on.

## AI Usage

Generative-AI tools were used as an execution and review layer in building this
software — implementation, debugging, testing, and reproducibility engineering —
under author direction and with author review. The instrument's design, its rule
base, the evaluation protocol, and the interpretation of the evidence were
determined by the authors, and each decision is logged with its evidence in
[`docs/decisions.md`](docs/decisions.md). See
[`docs/ai-usage.md`](docs/ai-usage.md) for the full statement.

## License

Apache License 2.0 — see [`LICENSE`](LICENSE). The underlying ClimateBERT
models are also Apache 2.0 licensed; see
[`docs/acknowledgements.md`](docs/acknowledgements.md) for full citations.
