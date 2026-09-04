# GreenRisk — Master Plan

This is the canonical repository map and reproducibility contract. The
numerical instrument is frozen at `rulebase-locked-v1` (commit
`a40288ac8eacfe0de1987884ec03bea9457972c5`). Changes to `RULES`, membership
functions, model revisions, or signal mappings require a separately identified
and logged ablation. Packaging, validation, provenance, and documentation may
evolve without altering that instrument.

## 1. Locked instrument

| Input | Pinned classifier output |
| --- | --- |
| `specificity` | climate-specificity `P(spec)` |
| `commitment` | climate-commitment `P(yes)` |
| `sentiment_asymmetry` | climate-sentiment `P(opportunity)` |
| `netzero` | netzero-reduction `P(net-zero)` |
| climate gate | climate-detector `P(yes) ≥ 0.5` |

Inputs use triangular Low `(0,0,0.4)`, Medium `(0.2,0.5,0.8)`, and High
`(0.6,1,1)` membership functions. Output risk uses Low `(0,0,30)`, Moderate
`(15,35,55)`, Elevated `(45,65,85)`, and High `(70,100,100)`, with centroid
defuzzification. The 17 rules comprise spine S1–S9, net-zero N1–N3,
opportunity O1–O3, and named signatures G1–G2.

## 2. Repository map

```text
src/greenrisk/              installable package
  metadata.py               frozen identifiers, model registry, signal map
  models.py                 optional ClimateBERT inference adapters
  linguistic_variables.py  membership functions
  rule_base.py              rules, validation, score and trace
  provenance.py             per-score PROV-O
  cli.py                    score-signals and score-text commands
scripts/                    artifact and research-run producers
scripts/validation/         research validation harnesses
tests/                      fast pytest suite and optional model tests
data/                       contrast-set source and data documentation
artifacts/                  committed results, figures, manifests, PROV-O
docs/                       design, evidence, decisions, use policy, paper
.github/workflows/          fast CI and manually triggered model smoke tests
```

## 3. Environments

```bash
# Base fuzzy scorer + tests (no model weights)
uv sync --frozen --group dev
uv run pytest -m "not model"
uv run python scripts/verify_artifact_integrity.py
uv build

# Raw-text model inference
uv sync --frozen --extra models --group dev
uv run pytest -m model
uv run python scripts/verify_model_revisions.py

# Full artifact reproduction
uv sync --frozen --extra research --group dev
```

The model smoke workflow is manual because it downloads several large model
artifacts. The normal CI job remains fast and checks packaging, lint, rule-base
properties, API validation, provenance hashes, and wheel/sdist creation.

## 4. Artifact reproduction

```bash
uv run python scripts/plot_linguistic_variables.py
uv run python scripts/first_provenance.py

uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
uv run python scripts/validation/mf_experiment.py -n 200 --gate 0.5
uv run python scripts/validation/anchor_verify.py
uv run python scripts/validation/hash3_characterize.py -n 500 --gate 0.5

uv run python scripts/run_full_corpus.py --gate 0.5
uv run python scripts/bingler_baseline.py
uv run python scripts/provenance_corpus_run.py

uv run python scripts/run_contrast_set.py --gate 0.5
uv run python scripts/evaluate_face_validity.py
uv run python scripts/provenance_contrast_run.py
uv run python scripts/verify_artifact_integrity.py
```

The TCFD dataset is pinned at revision
`aee5c98f0bf7835bfb08308ffc7c17216657976b`; the train Parquet content SHA-256
is `1f16bb38a021aeafad6935eb5aa3f072c2e51b3dcf01eaee88a32ef537029f1f`.
Manifests record exact model revisions, input/output hashes, the instrument
commit, the lockfile hash, and runtime versions for new runs.

Historical corpus and contrast manifests were expanded using immutable Git and
Hugging Face records. They explicitly mark original runtime details that were
not recorded. Their content hashes use Git's normalized LF bytes, enforced by
`.gitattributes` and verified in CI.

The current producers intentionally retain full input hashes and unrounded
signal/trace values, so their serialized CSV bytes differ from the historical
runs even when numerical scores agree. For byte-identical historical outputs,
check out the `source.commit` in the relevant manifest and use its recorded
lockfile. A current-code rerun is a new run and must keep its new manifest and
PROV-O hashes together.

## 5. Governance

- `docs/decisions.md` is append-only for instrument and evidence decisions.
- Research outputs are immutable evidence. Regenerate them only with the
  producing script and update the manifest and PROV-O records together.
- Never silently float model or dataset revisions.
- Never persist credentials during imports; `HF_TOKEN` is passed only to model
  download requests when present.
- Scores must retain raw-probability precision in machine-readable output;
  rounding is presentation-only except for the locked 2-decimal risk result.
- Claims must distinguish transparent fuzzy reasoning from learned upstream
  classifiers and exploratory characterization from independent validation.
