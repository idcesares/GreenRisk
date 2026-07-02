# Repository Guidelines

## Project Structure & Module Organization

GreenRisk is a Python 3.12 project for explainable greenwashing-risk scoring. `MASTER_PLAN.md` is the canonical architecture and roadmap; read it before changing behavior.

- Core instrument modules are at the repository root: `models.py`, `linguistic_variables.py`, `rule_base.py`, and `main.py`.
- Pipeline scripts live in `scripts/`; locked validation harnesses live in `scripts/validation/`.
- Smoke tests live in `tests/` and are executable Python scripts, not a pytest suite.
- Input data is under `data/`; generated, committed outputs are under `artifacts/`.
- `docs/` is for consolidated public documentation. `development/` is intentionally gitignored process material.

## Build, Test, and Development Commands

Use `uv` for dependency management and command execution.

```powershell
uv sync
uv run python tests/smoke_test_all_models.py
uv run python tests/smoke_test_detector_model.py
uv run python tests/smoke_test_provenance.py
uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
uv run python scripts/plot_linguistic_variables.py
uv run python scripts/first_provenance.py
```

`uv sync` installs dependencies from `pyproject.toml` and `uv.lock`. Smoke tests verify model loading, detector behavior, and provenance basics. Validation scripts re-check the locked instrument and may load large ClimateBERT models.

## Coding Style & Naming Conventions

Follow the existing style: 4-space indentation, type hints where useful, concise docstrings, and explicit data structures for model registries and fuzzy rules. Use `snake_case` for functions and variables, `UPPER_CASE` for constants, and short rule IDs such as `S1`, `N2`, or `G1`.

Keep the scoring instrument explicit over clever abstraction. Changes to `MODEL_REGISTRY`, `SIGNAL_MAP`, membership functions, or `RULES` affect reproducibility and must be treated as instrument changes.

## Testing Guidelines

Run the relevant smoke test before submitting any change. For changes to fuzzy logic, provenance, model mappings, or artifacts, also run the matching script in `scripts/validation/` or the artifact producer you touched. Do not describe tests as pytest-based unless a pytest suite is added.

## Commit & Pull Request Guidelines

Commits use conventional prefixes such as `feat:` and `docs:` with a scoped, imperative summary, for example `feat: add held-out face-validity artifacts`.

Pull requests should include a behavior summary, commands run, artifacts changed, and any linked decision-log entry. Include screenshots only for generated figures or provenance images.

## Architecture & Reproducibility Notes

The instrument is frozen at tag `rulebase-locked-v1`. Any post-lock change to rules, membership functions, model revisions, or signal mappings must be a separate logged ablation, never a silent edit. Preserve pinned ClimateBERT revisions and avoid committing secrets such as `.env` or `HF_TOKEN`.
