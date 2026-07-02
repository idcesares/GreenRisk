# GreenRisk — Master Plan

> Canonical map of the repository: what exists, where it lives, and how to
> reproduce every committed artifact. For the pipeline design and the
> reasoning behind it, see [`docs/architecture.md`](docs/architecture.md).
> For the validity evidence, see [`docs/validation.md`](docs/validation.md).

Instrument status: **frozen at tag `rulebase-locked-v1`.** After this freeze,
any change to the rules, membership functions, model revisions, or signal
mappings is a separate, explicitly logged instrument change — never a silent
edit. The validity evidence in `docs/validation.md` was produced against this
exact, unchanging instrument, including a held-out case set that was not
inspected or scored until after the freeze.

## 1. Locked instrument at a glance

**Signals** (construct-direct; risk-direction inversion happens in the rule
base, not the signal):

| Fuzzy input | Model | Label read |
| --- | --- | --- |
| `specificity` | climate-specificity | `P('spec')` |
| `commitment` | climate-commitment | `P('yes')` |
| `sentiment_asymmetry` | climate-sentiment | `P('opportunity')` |
| `netzero` | netzero-reduction | `P('net-zero')` |
| *(gate)* | climate-detector | `P('yes') ≥ 0.5` — relevance gate, not a fuzzy axis |

**Membership functions** — all triangular:
- inputs on `[0, 1]`: Low `(0, 0, 0.4)` · Medium `(0.2, 0.5, 0.8)` · High `(0.6, 1, 1)`
- output `risk` on `[0, 100]`: Low `(0, 0, 30)` · Moderate `(15, 35, 55)` · Elevated `(45, 65, 85)` · High `(70, 100, 100)`

**Rules** — 17, `risk = vagueness × claim-strength`:
- Tier 1 spine S1–S9 (specificity × commitment)
- Tier 2 net-zero amplifiers N1–N3
- Tier 3 opportunity amplifiers O1–O3
- Tier 4 named signatures G1–G2 (trace legibility for case studies)

Defuzzification: centroid. The full rationale for every choice above —
including the design alternatives that were tested and not adopted — is in
[`docs/architecture.md`](docs/architecture.md).

## 2. Repository map

```
GreenRisk/
├── MASTER_PLAN.md              this file — the repository map
├── README.md
├── LICENSE
├── models.py  linguistic_variables.py  rule_base.py  main.py   core instrument modules
├── scripts/                    pipeline & artifact producers
│   ├── pin_models.py           pin ClimateBERT revisions for reproducibility
│   ├── first_provenance.py     minimal PROV-O example → artifacts/provenance/
│   ├── plot_linguistic_variables.py   → artifacts/figures/ (membership-function plots)
│   ├── sanity_check_distributions.py  → artifacts/figures/ (signal distributions)
│   ├── run_full_corpus.py, bingler_baseline.py, provenance_corpus_run.py
│   │     → artifacts/corpus_run/ — Layer 1 validation (docs/validation.md)
│   ├── run_contrast_set.py, evaluate_face_validity.py, provenance_contrast_run.py
│   │     → artifacts/contrast_run/ — Layer 2 validation (docs/validation.md)
│   └── validation/              locked-instrument evidence harnesses
│       ├── integration_seam_test.py   end-to-end seam test + PROV-O
│       ├── mf_experiment.py           triangular vs. trapezoidal membership-function comparison
│       ├── anchor_verify.py           calibration-anchor verification
│       └── hash3_characterize.py      sizes the commitment-classifier false-positive tail
├── tests/                       smoke tests (models, detector, provenance)
├── data/                        contrast_set.csv — the held-out Layer 2 case set
├── artifacts/                   figures/ (plots) · provenance/ (.ttl/.json/.png) · corpus_run/ · contrast_run/
├── docs/                        architecture.md · validation.md · acknowledgements.md
└── development/                 internal working record (design notes, decision log);
                                  gitignored, not part of the public release
```

## 3. Reproducibility

```powershell
# pin + verify models (writes pinned_model_hashes.md, gitignored)
uv run python scripts/pin_models.py
uv run python tests/smoke_test_all_models.py

# regenerate committed artifacts
uv run python scripts/plot_linguistic_variables.py
uv run python scripts/first_provenance.py

# re-run the locked-instrument evidence
uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
uv run python scripts/validation/mf_experiment.py -n 200 --gate 0.5
uv run python scripts/validation/anchor_verify.py
uv run python scripts/validation/hash3_characterize.py -n 500 --gate 0.5

# Layer 1 — full-corpus run + baseline comparison + run-level provenance
uv run python scripts/run_full_corpus.py --gate 0.5
uv run python scripts/bingler_baseline.py
uv run python scripts/provenance_corpus_run.py

# Layer 2 — held-out face validity (contrast set) + provenance
uv run python scripts/run_contrast_set.py --gate 0.5
uv run python scripts/evaluate_face_validity.py
uv run python scripts/provenance_contrast_run.py

# smoke tests
uv run python tests/smoke_test_all_models.py
uv run python tests/smoke_test_detector_model.py
uv run python tests/smoke_test_provenance.py
```

All corpus-scale runs use `climatebert/tcfd_recommendations` (TCFD only). The
contrast set (`data/contrast_set.csv`) is reserved for the one-shot,
held-out Layer 2 evaluation described in `docs/validation.md`.

Model inference runs on GPU automatically if a CUDA-capable device is
available (`torch.cuda.is_available()`), and falls back to CPU otherwise — see
`models.py`. No GPU is required to run the pipeline; it is only faster with
one.

## 4. Conventions

- **Production vs. process split.** Tracked: core modules, `scripts/`,
  `tests/`, `data/`, `artifacts/`, `docs/`, this file. Gitignored:
  `development/` (design notes, decision log, internal working material).
- **The decision log is append-only.** Every instrument change gets a
  logged entry before it is relied on, in `development/decisions/` (internal;
  the resulting rationale is written up for public consumption in
  `docs/architecture.md` and `docs/validation.md`).
- **Models are pinned** by commit revision in `models.MODEL_REGISTRY` for
  bit-identical reproducibility; PROV-O graphs record the resulting hashes.
