# GreenRisk

[![CI](https://github.com/idcesares/GreenRisk/actions/workflows/ci.yml/badge.svg)](https://github.com/idcesares/GreenRisk/actions/workflows/ci.yml)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21122389.svg)](https://doi.org/10.5281/zenodo.21122389)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

GreenRisk is a research instrument for screening greenwashing risk in corporate
climate-disclosure paragraphs. It combines pinned ClimateBERT classifiers with
a frozen 17-rule Mamdani fuzzy layer and returns a 0–100 score plus the rules
that fired. W3C PROV-O records bind scores and committed evaluations to model,
dataset, instrument, and artifact identifiers.

The fuzzy decision layer is transparent and independently traceable. The
upstream neural classifiers remain learned models and should not be described
as intrinsically interpretable. The numerical instrument is frozen at
`rulebase-locked-v1` (commit `a40288a`); release 0.2.0 hardens the surrounding
software without changing its membership functions, rules, model revisions, or
signal mappings.

## Use boundaries

GreenRisk is for research, prioritization, and decision support. It is not a
legal finding, assurance opinion, fact checker, or substitute for reviewing the
underlying disclosure and evidence. Scores are construct-dependent, inherit
classifier error, and do not cover all greenwashing forms—especially omission
or misleading claims that are linguistically specific. See
[`docs/responsible-use.md`](docs/responsible-use.md).

## Install and score

Install the fast fuzzy layer and development checks:

```bash
uv sync --frozen --group dev
uv run greenrisk score-signals \
  --specificity 0.20 \
  --commitment 0.90 \
  --sentiment-asymmetry 0.40 \
  --netzero 0.70
```

Raw-text scoring additionally needs the pinned ClimateBERT models:

```bash
uv sync --frozen --extra models
uv run greenrisk score-text --text "We aim to reach net zero by 2050." --json
```

Use `--provenance score.ttl` on `score-text` to write a per-score PROV-O graph.
Text below the climate-relevance gate is explicitly returned as `not_scored`;
`--force` overrides the gate and records that fact. Model downloads are large,
may require network access, and use CUDA automatically when available.

## Evidence and limitations

The paper reports two exploratory validation layers:

- A comparison on 1,009 climate-gated TCFD paragraphs against a specificity-
  and commitment-derived cheap-talk baseline (Spearman ρ = 0.602). This is
  construct-alignment evidence, not independent criterion validation, because
  GreenRisk and the baseline share classifier-derived constructs.
- A 15-case post-lock contrast evaluation, with AUC = 0.867 for the primary
  5-vs-6 subset. The expectations were not used to tune the frozen instrument,
  but they and the first results entered public history in the same commit. The
  repository therefore does not claim an externally timestamped blind
  preregistration.

These results are small-sample, paragraph-level characterization—not a claim of
population-level or organization-level validity. Full interpretation is in
[`docs/validation.md`](docs/validation.md).

## Reproduce and verify

```bash
uv run pytest -m "not model"
uv run python scripts/verify_artifact_integrity.py
uv build

# Optional heavyweight model checks
uv sync --frozen --extra models --group dev
uv run pytest -m model

# Full research environment and artifact producers
uv sync --frozen --extra research --group dev
uv run python scripts/run_full_corpus.py --gate 0.5
uv run python scripts/provenance_corpus_run.py
uv run python scripts/run_contrast_set.py --gate 0.5
uv run python scripts/evaluate_face_validity.py
uv run python scripts/provenance_contrast_run.py
```

The committed historical manifests were expanded from immutable Git and
Hugging Face history. Details unavailable from the original runtime are marked
as unavailable rather than reconstructed speculatively. Dataset and artifact
hashes are checked in CI. See [`MASTER_PLAN.md`](MASTER_PLAN.md) for the complete
repository map and reproduction contract. Current producers use hardened,
higher-precision serialization; byte-identical historical reproduction starts
from each manifest's `source.commit`, while current-code reruns test numerical
equivalence and produce new hashes.

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — pipeline and design rationale
- [`docs/validation.md`](docs/validation.md) — evidence, protocol, and limitations
- [`docs/decisions.md`](docs/decisions.md) — public decision record and freeze
- [`docs/responsible-use.md`](docs/responsible-use.md) — intended and prohibited uses
- [`docs/ai-usage.md`](docs/ai-usage.md) — AI-assistance disclosure
- [`docs/acknowledgements.md`](docs/acknowledgements.md) — upstream work and models
- [`docs/greenrisk_paper.pdf`](docs/greenrisk_paper.pdf) — project paper

## Citation and license

Use [`CITATION.cff`](CITATION.cff) or the Zenodo concept DOI
[`10.5281/zenodo.21122389`](https://doi.org/10.5281/zenodo.21122389). A new
version-specific DOI should be minted when 0.2.0 is released; the existing
`10.5281/zenodo.21122390` identifies v0.1.0.

Apache License 2.0. Upstream model and dataset terms remain applicable.
