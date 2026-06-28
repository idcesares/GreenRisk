# GreenRisk — Master Plan

> **Canonical, end-to-end map of the project.** Single source of truth for *what
> exists, where it lives, and what's next.* This is a structural spine and index —
> not a content copy. Detailed reasoning lives once, in the decision logs and phase
> docs under `development/`; this file links to them. Supersedes the retired
> `development/archive/GreenRisk_MasterPlan.docx`.
>
> Instrument status: **frozen at tag `rulebase-locked-v1`** (W2 close-out, 2026-06-16).

---

## 1. What GreenRisk is

An **explainable greenwashing-risk scorer** for corporate climate disclosures.
Each paragraph is mapped to four construct-aligned signals by pinned ClimateBERT
models, aggregated by a **Mamdani fuzzy rule base** into a 0–100 risk score that
ships with an **auditable activation trace** and a **W3C PROV-O** provenance graph.
The design goal is defensibility: every score is re-derivable and every instrument
decision is logged.

## 2. End-to-end pipeline

```
raw paragraph
   │
   ▼  climate gate          detector P('yes') ≥ 0.5            (models.is_climate)
   ▼  four scorers          ClimateBERT × 4 → {label: prob}    (models.all_signals_batch)
   ▼  signal mapping        4 probabilities → 4 fuzzy inputs   (models.SIGNAL_MAP)
   ▼  fuzzy inference       Mamdani, 17 rules, centroid        (rule_base.score_paragraph)
   ▼  output                risk ∈ [0,100] + fired-rule trace
   ▼  provenance            PROV-O graph (.ttl)                (scripts/provenance_*)
```

Core modules (repo root, authoritative source of truth for the instrument):
- [`models.py`](models.py) — model registry (pinned revisions), scoring layer, `SIGNAL_MAP`, climate gate.
- [`linguistic_variables.py`](linguistic_variables.py) — fuzzy variables + membership functions.
- [`rule_base.py`](rule_base.py) — the 17-rule Mamdani base, `score_paragraph`, audit trace, `library_firings`.

## 3. The locked instrument (`rulebase-locked-v1`)

**Signals** (construct-direct; the rule base inverts to risk where needed):

| Fuzzy input | Model | Label read | Note |
| --- | --- | --- | --- |
| `specificity` | climate-specificity | `P('spec')` | |
| `commitment` | climate-commitment | `P('yes')` | |
| `sentiment_asymmetry` | climate-sentiment | `P('opportunity')` | locked simplification (Phase 2) |
| `netzero` | netzero-reduction | `P('net-zero')` | |
| *(gate)* | climate-detector | `P('yes') ≥ 0.5` | relevance gate, not a fuzzy axis |

**Membership functions** — all-triangular (trapezoidal tested & rejected, DL-002):
- inputs on [0,1]: Low (0,0,0.4) · Medium (0.2,0.5,0.8) · High (0.6,1,1)
- output `risk` on [0,100]: Low (0,0,30) · Moderate (15,35,55) · Elevated (45,65,85) · High (70,100,100)

**Rules** — 17, `risk = vagueness × claim-strength` (DL-001):
- Tier 1 **spine** S1–S9 (specificity × commitment)
- Tier 2 **net-zero amplifiers** N1–N3
- Tier 3 **opportunity amplifiers** O1–O3
- Tier 4 **named signatures** G1–G2 (trace legibility for case studies)

Defuzzification: centroid. The trace independently re-derives each rule's firing as
`min(memberships)` and matches the library exactly (verified end-to-end, Phase 4).

## 4. Repository map

```
GreenRisk/
├── MASTER_PLAN.md              ← this file (the spine)
├── README.md
├── models.py  linguistic_variables.py  rule_base.py  main.py   core modules
├── scripts/                    tracked — pipeline & artifact producers
│   ├── pin_models.py           pin ClimateBERT revisions (reproducibility)
│   ├── first_provenance.py     foundation PROV-O example → artifacts/provenance/
│   ├── plot_linguistic_variables.py   → artifacts/figures/ (MF plots)
│   ├── sanity_check_distributions.py  → artifacts/figures/ (signal distributions)
│   └── validation/             locked-evidence harnesses (re-run the W2 close-out)
│       ├── integration_seam_test.py   end-to-end seam test + PROV-O
│       ├── mf_experiment.py           triangular vs. trapezoidal (DL-002)
│       ├── anchor_verify.py           Calibration Anchor 1
│       └── hash3_characterize.py      #3 commitment false-positive (DL-003)
├── tests/                      smoke tests (models, detector, provenance)
├── data/                       contrast_set.csv  ← held-out Phase 6 face-validity set
├── artifacts/                  figures/ (plots) · provenance/ (.ttl/.json/.png)
├── docs/                       consolidated public docs
└── development/                process record — GITIGNORED (raw material for the paper)
    ├── 0_foundations/  1_mamdani_primer/  2_linguistic_variables/
    ├── 3_rule_base/    4_pipeline_and_lock/  5_corpus_and_baseline/
    ├── 6_face_validity/
    ├── decisions/      decision_log.md · decisions_Phase2.md · calibration_anchors.md
    ├── scripts/        eval_phase3.py · inspect_corpus.py · iterate_tcfd.py
    └── archive/        GreenRisk_MasterPlan.docx (retired)
```

## 5. Phase roadmap

Numbered by project phase (calendar-week labels retired). Phases 0–4 are complete
and frozen in `rulebase-locked-v1`; Phases 5–6 (full-corpus run + Bingler baseline;
held-out face validity) are complete and run against that frozen instrument. Phase 7
(consolidated write-up) is next.

| # | Milestone | Status | Where |
| --- | --- | --- | --- |
| 0 | Foundations — pinned ClimateBERT models + first PROV-O graph | ✅ | `development/0_foundations/` |
| 1 | Mamdani primer (fuzzy concept) | ✅ | `development/1_mamdani_primer/` |
| 2 | Linguistic variables — MFs, breakpoints, signal distributions | ✅ | `development/2_linguistic_variables/` · `decisions/decisions_Phase2.md` |
| 3 | Rule base — 17-rule Mamdani spine | ✅ **DL-001** | `development/3_rule_base/` · `decisions/decision_log.md` |
| 4 | End-to-end pipeline test + **LOCK** | ✅ **`rulebase-locked-v1`** | `development/4_pipeline_and_lock/` · `decisions/` |
| 5 | Full-corpus run + Bingler cheap-talk baseline *(legacy "W3")* | ✅ **DL-004** | `scripts/run_full_corpus.py` · `scripts/bingler_baseline.py` · `scripts/provenance_corpus_run.py` · `artifacts/corpus_run/` · `development/5_corpus_and_baseline/` |
| 6 | Face validity vs. the contrast set *(legacy "W4")* | ✅ **DL-005** | `scripts/run_contrast_set.py` · `scripts/evaluate_face_validity.py` · `scripts/provenance_contrast_run.py` · `artifacts/contrast_run/` · `development/6_face_validity/` |
| 7 | Consolidated write-up / paper *(legacy "W5")* | ⏭ **next** | `docs/` |

**Lock discipline:** after `rulebase-locked-v1`, any instrument change is a
*separate, logged ablation* — never a silent edit. Phases 5–6 ran against the
frozen instrument; the contrast set stayed sealed until Phase 6 (held-out, one-shot).

## 6. Decisions index

Append-only. Full entries in `development/decisions/`.

| ID | Decision | Phase |
| --- | --- | --- |
| Phase 2 | Signal mappings + symmetric 0.2/0.4/0.6/0.8 breakpoints; `sentiment_asymmetry = P('opportunity')` (accepted simplification) | 2 |
| DL-001 | Demote the "absence" corner — `risk = vagueness × claim-strength`; High requires a claim signal (S1→Moderate, S3→High, …) | 3 |
| DL-002 | Membership shape — **keep triangular** (trapezoidal tested on TCFD: 0/162 boundary crossings) | 4 |
| DL-003 | #3 commitment false-positive — **isolated** (1.4% of gated TCFD); watch item + §7 limitation, no rule change | 4 |
| LOCK | Freeze rules + MFs together → `rulebase-locked-v1` | 4 |
| Anchor 1 | Vague net-zero pledge → Elevated ~60, spine+signature (expectation updated post-DL-001) — `decisions/calibration_anchors.md` | 4 |
| DL-004 | Phase 5 validity — converges with Bingler cheap-talk (Spearman ρ=0.60, n=1009) yet adds a claim-strength axis it is blind to (within top-quartile cheap-talk, ρ(commit,risk)=0.43); the two diverge precisely on maximally-vague low-commitment text, which DL-001 demotes to Moderate | 5 |
| DL-005 | Phase 6 held-out face validity — in-scope (vagueness) greenwashing separates from rigorous (AUC=0.87, n=5v6, p=0.026; demonstration, wide CI); boundary 4/4 (specificity-based greenwashing correctly unflagged). Limitation: `specificity` proxies substance and is foolable both ways — RD-006 over-flagged (process disclosure), GW-004/008 under-flagged (specific bad-faith). No instrument change | 6 |

## 7. Reproducibility

```powershell
# pin + verify models (writes pinned_model_hashes.md, gitignored)
uv run python scripts/pin_models.py
uv run python tests/smoke_test_all_models.py

# regenerate committed artifacts
uv run python scripts/plot_linguistic_variables.py
uv run python scripts/first_provenance.py

# re-run the locked-instrument evidence (W2 close-out)
uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
uv run python scripts/validation/mf_experiment.py -n 200 --gate 0.5
uv run python scripts/validation/anchor_verify.py
uv run python scripts/validation/hash3_characterize.py -n 500 --gate 0.5

# Phase 5 — full-corpus run + Bingler baseline + run-level provenance
uv run python scripts/run_full_corpus.py --gate 0.5
uv run python scripts/bingler_baseline.py
uv run python scripts/provenance_corpus_run.py

# Phase 6 — held-out face validity (contrast set) + provenance
uv run python scripts/run_contrast_set.py --gate 0.5
uv run python scripts/evaluate_face_validity.py
uv run python scripts/provenance_contrast_run.py

# smoke tests
uv run python tests/smoke_test_all_models.py
uv run python tests/smoke_test_detector_model.py
uv run python tests/smoke_test_provenance.py
```

All iteration runs use **TCFD only** (`climatebert/tcfd_recommendations`). The
contrast set was reserved for the one-shot Phase 6 face-validity check.

## 8. Conventions

- **Production vs. process split.** Tracked: core modules, `scripts/`, `tests/`,
  `data/`, `artifacts/`, `docs/`, this file. Gitignored: `development/` (kickoffs,
  decision logs, session summaries, dev harnesses) — raw material for the paper.
- **Decision log is append-only.** Every instrument change gets a dated DL-NNN entry
  before it's relied on.
- **Models are pinned** by commit revision in `models.MODEL_REGISTRY` for bit-identical
  reproducibility; PROV-O graphs record the hashes.
