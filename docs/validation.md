# Validation and evidence

GreenRisk has two exploratory evidence layers, both produced with the numerical
instrument frozen at `rulebase-locked-v1`. They characterize whether the
instrument behaves consistently with its intended construct and expose its
failure modes. Neither layer establishes organization-level, causal, legal, or
population-wide validity.

## Evidence hierarchy

| Layer | Data | What it supports | What it does not support |
| --- | --- | --- | --- |
| Corpus characterization | 1,009 climate-gated TCFD paragraphs | construct alignment and incremental differentiation | independent criterion validity or firm-level accuracy |
| Post-lock contrast evaluation | 15 sourced paragraph cases | face validity and concrete boundary failures | a general benchmark or externally preregistered estimate |
| Property tests | 4,158 fuzzy-grid evaluations plus trace checks | implementation consistency of locked rule behavior | empirical truth of the construct |

## Layer 1 — corpus characterization

The full train split of pinned dataset `climatebert/tcfd_recommendations`
(revision `aee5c98f0bf7835bfb08308ffc7c17216657976b`) contains 1,300
paragraphs. The climate gate retained 1,009 at `P(yes) ≥ 0.5`.

GreenRisk was compared with the Bingler et al. cheap-talk measure,
`1 - P(spec)`. Spearman correlation was ρ = 0.602 (p ≈ 1.4×10⁻¹⁰⁰,
n = 1,009). Within the baseline's vaguest quartile (n = 253; cheap-talk mean
0.961, sd 0.010), GreenRisk ranged from 35 to 90 and correlated with commitment
at ρ = 0.433. This is consistent with the intended distinction between quiet
vagueness and confident, unsupported pledges.

This comparison is not an independent validation target: the baseline uses the
same specificity classifier that supplies one GreenRisk input. The findings
are best interpreted as convergent construct alignment plus evidence that the
additional commitment/rule structure differentiates passages the baseline
treats similarly. TCFD category cuts are descriptive only because the dataset
has no firm or document identifiers and no greenwashing labels.

The non-monotone bend in the highest cheap-talk deciles is expected. Rule S1
assigns vague text with no claim to Moderate risk; louder vague claims reach
higher terms. This is a frozen design property, not an empirical correction.

## Layer 2 — post-lock contrast evaluation

`data/contrast_set.csv` contains 15 sourced excerpts: nine passages associated
with public greenwashing enforcement/rulings involving DWS, Volkswagen, and
HSBC, and six reference passages from Microsoft and Ørsted disclosures. It is
a hand-curated diagnostic set, not a representative sample.

The numerical instrument had been frozen before this evaluation and the case
expectations were not used to tune it. However, the expectations and first
results were introduced together in public Git commit `8b2f461`. The repository
therefore cannot independently demonstrate an externally timestamped blind
preregistration. The table in
[`decisions.md`](decisions.md#appendix-a--recorded-phase-6-expectations) is
retained as the recorded protocol, with this chronology limitation explicit.

For the primary in-scope comparison—five vagueness-based cases versus six
reference passages—the observed AUC was 0.867 (Mann–Whitney U = 26, one-sided
p = 0.026). At threshold 50, sensitivity was 3/5 and specificity 5/6. Because
the sample is tiny, selected, and paragraph-level, these values are descriptive
effect estimates rather than general performance guarantees.

All four cases outside the primary scope scored below 50: three detailed but
misleading/omissive passages and one promotional boundary case. This is useful
negative evidence. It shows that linguistic specificity can route a passage to
low risk even when external facts make it misleading.

## Documented failure modes

- `RD-006` scored 72.7: process-oriented reporting language had strong
  commitment but few paragraph-level specifics, producing a false positive.
- `GW-004` and `GW-008` scored near 10: concrete numbers appeared specific even
  though the broader adjudicated context involved corrupted measurement or
  omission.
- `GW-007` scored 10.88: a short advertisement with a dollar figure was read as
  specific.
- `GW-002` scored 35.0: the upstream commitment classifier returned 0.006 on
  generic ESG prose.

The defensible scope is therefore narrow: GreenRisk screens for patterns of
vagueness, claim strength, opportunity framing, and net-zero language. It does
not establish truth, detect material omission, or verify whether numbers and
actions match. See [`responsible-use.md`](responsible-use.md).

## Reproducibility

Committed outputs are bound by SHA-256 in versioned manifests and PROV-O:

- `artifacts/corpus_run/` and `artifacts/provenance/corpus_run.*`
- `artifacts/contrast_run/` and `artifacts/provenance/contrast_run.*`

Run `uv run python scripts/verify_artifact_integrity.py` to verify these links.
The historical manifests identify exact pipeline/instrument commits, model and
dataset revisions, lockfile hash, and result hashes. Runtime details not
captured by the original scripts are explicitly marked unavailable. New runs
record Python, PyTorch, Transformers, device, lockfile, input, and output
coordinates automatically.

The locked fuzzy behavior is asserted by pytest: rule integrity, rule-term
ordering, bounded centroid artifacts, bounded amplifier exceptions, and
agreement between independently re-derived and scikit-fuzzy firing strengths.
