# Repository Guidelines

`MASTER_PLAN.md` is the canonical repository map. GreenRisk is an installable
Python 3.12 `src`-layout project; package code lives in `src/greenrisk/`,
research producers in `scripts/`, tests in `tests/`, inputs in `data/`, and
committed evidence in `artifacts/`.

Use `uv` and the lockfile:

```bash
uv sync --frozen --group dev
uv run ruff check .
uv run pytest -m "not model"
uv run python scripts/verify_artifact_integrity.py
uv build
```

Tests marked `model` download and execute the pinned ClimateBERT revisions;
run them with `uv sync --frozen --extra models --group dev` when model adapters
change. Full research scripts require `--extra research`.

Use 4-space indentation, type hints where useful, concise docstrings, and
explicit data structures. Keep the scoring instrument readable. Input
probabilities must be finite and in `[0,1]`; do not rely on implicit clipping.
Avoid import-time network, login, filesystem, or credential side effects.

The numerical instrument is frozen at `rulebase-locked-v1`. Any change to
`MODEL_REGISTRY`, `SIGNAL_MAP`, membership functions, or `RULES` is an
instrument change and must be a separate logged ablation. Do not rewrite
historical artifacts without running their producer and updating manifest and
PROV-O hashes. Preserve secrets such as `.env` and `HF_TOKEN`.

Use conventional commit prefixes. Pull requests should state behavior changes,
commands run, artifact changes, evidence/claim implications, and any decision
record entry.
