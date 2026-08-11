# Decision Record

This is the public record of every instrument decision that shaped GreenRisk,
in the order the decisions were taken. Each entry states what triggered it,
what the evidence showed, what was decided, and what was ruled out.

The decision identifiers used here (`DL-001`, `DL-002`, …) are the ones cited
in the GreenRisk paper and in [`architecture.md`](architecture.md), so a claim
about *why* the instrument is shaped the way it is can be traced to the entry
that shaped it. Entries are reproduced from the project's append-only working
log; the working log itself carries additional internal process material and is
not part of the released repository.

Two properties hold across the whole record:

- **Everything before the lock was decided on TCFD evidence only.** The
  held-out contrast set stayed sealed until after `rulebase-locked-v1`.
- **Nothing after the lock changed the instrument.** DL-004 and DL-005 are
  analyses against a frozen artifact, not edits to it.

| Entry | Date | Subject | Instrument changed? |
| --- | --- | --- | --- |
| [DL-Phase 2](#dl-phase-2--signal-mappings-and-breakpoints) | 2026-06 | Signal mappings; 0.4/0.6 breakpoints | Yes (initial design) |
| [DL-001](#dl-001--demoting-the-absence-corner) | 2026-06-16 | Risk = vagueness × claim-strength | Yes (5 spine cells) |
| [DL-002](#dl-002--membership-function-shape-triangular-kept) | 2026-06-16 | Triangular vs. trapezoidal MFs | No (variant rejected) |
| [DL-003](#dl-003--the-commitment-false-positive-tail-isolated) | 2026-06-16 | Commitment false-positive tail | No (logged limitation) |
| [LOCK](#lock--rulebase-locked-v1) | 2026-06-16 | Instrument frozen | Frozen |
| [DL-004](#dl-004--convergent-and-discriminant-validity-vs-the-cheap-talk-baseline) | 2026-06-16 | Layer 1 corpus validity | No (analysis only) |
| [DL-005](#dl-005--held-out-face-validity-and-the-symmetric-specificity-limitation) | 2026-06-17 | Layer 2 held-out validity | No (analysis only) |

---

## DL-Phase 2 — signal mappings and breakpoints

**Subject:** how each model's output becomes a fuzzy input, and where the
Low/Medium/High boundaries sit.

### Signal mappings

| Fuzzy input | Model | Label read |
| --- | --- | --- |
| `specificity` | climate-specificity | `P('spec')` |
| `commitment` | climate-commitment | `P('yes')` |
| `sentiment_asymmetry` | climate-sentiment | `P('opportunity')` |
| `netzero` | netzero-reduction | `P('net-zero')` |

Every variable is **construct-aligned**: it measures its construct directly, and
the inversion to a risk direction lives in the rule base, never in the signal.
There are no `1 - P(...)` inversions at the signal layer.

Two mappings were chosen over defensible alternatives:

- **`netzero` reads `P('net-zero')` alone**, not `P('net-zero') + P('reduction')`.
  The underlying model is three-class (`none` / `reduction` / `net-zero`) and
  separates cleanly in practice — on a genuine net-zero pledge it returned
  `net-zero = 0.9987`, `reduction = 0.0007`, `none = 0.0006`. Reduction targets
  are quantified against a base year and are conceptually the *opposite* of the
  vagueness this instrument hunts, so folding them in would dilute the
  "net-zero pledge × low specificity" signature.
- **`sentiment_asymmetry` reads `P('opportunity')` alone**, not a signed
  balance of opportunity and risk framing. Accepted simplification, with a
  documented consequence: risk-framed and neutral paragraphs both collapse
  toward 0, so "balanced" framing does not sit at 0.5. The Tier-3 rules must be
  read as detecting *opportunity hype*, not as a general sentiment axis.

### Breakpoints: theory-driven, not corpus-fitted

Boundaries at **0.4** (Low/Medium) and **0.6** (Medium/High), symmetric around
the binary classifiers' 0.5 calibration midpoint.

An empirical sanity check on 200 TCFD paragraphs (`test` split) before locking:

| Variable | mean | median | <0.4 | 0.4–0.6 | >0.6 | Shape |
| --- | --- | --- | --- | --- | --- | --- |
| `specificity` | 0.317 | 0.157 | 70% | 6% | 24% | skewed-Low + High tail |
| `commitment` | 0.389 | 0.031 | 60% | 2% | 37% | bimodal, Low-leaning |
| `sentiment_asymmetry` | 0.256 | 0.018 | 72% | 4% | 24% | bimodal, strongly Low |
| `netzero` | 0.033 | 0.000 | 96% | 0% | 3% | sparse, hard Low |

**Decision: breakpoints not adjusted.** Moving them to corpus quantiles was
rejected as circular — it would define "vague" relative to whatever the sample
happens to contain rather than in absolute terms. The failure is concrete:
`netzero`'s empirical median is ≈ 0, so a quantile boundary would label a
paragraph with `P(net-zero) = 0.05` as "Medium netzero," which is nonsensical.
The theory-driven boundary ("Low = the model assigns < 0.4 to the label") is a
substantive, reviewable claim; the quantile boundary is not.

**Carried forward:** every input is bimodal, so the Medium term carries 0–6% of
paragraphs and rarely fires strongly. That is a property of confident binary
classifiers on heterogeneous disclosure text, not a breakpoint defect — it is
documented rather than tuned away, and it is why spine rule S5 is empirically
rare. Distribution plots: `artifacts/figures/dist_*.png`
(`uv run python scripts/sanity_check_distributions.py`).

---

## DL-001 — demoting the "absence" corner

**Date:** 2026-06-16 · **Trigger:** the first traced inference run, on 21
climate-gated TCFD paragraphs. **This is the design's central correction.**

### Finding

14 of those 21 genuine climate paragraphs (`is_climate ≈ 0.998`) maxed out at
`risk ≈ 90` through rule **S1** alone. Reading them showed they were sober
climate risk-factor disclosures — *"climate change could exacerbate threats to
our business, including exposure to severe storms, drought, fires, and
floods"* — precisely the reporting TCFD exists to encourage.

Root cause: S1's original premise, that *vague + uncommitted = cheap talk*, is
false for risk-disclosure text. Such text is non-specific and uncommitted
because **it is not a pledge at all**. Greenwashing is a hollow claim; a risk
disclosure is not a claim. The original rule base could not tell an empty
pledge from no pledge.

The same run surfaced a gating bug: non-climate rows (`is_climate ≈ 0.004`)
were reaching the fuzzy layer. The climate gate removes them cleanly.

### Decision — fix at the rule level

**High risk now requires a claim signal**: commitment High, netzero High, or
opportunity High. Five spine cells changed:

| Rule | Antecedent | Was | Now | Why |
| --- | --- | --- | --- | --- |
| S1 | spec Low ∧ comm Low | High | **Moderate** | vague, no claim → a weak disclosure, not greenwashing |
| S3 | spec Low ∧ comm High | Elevated | **High** | loud pledge, no substance → the real signature |
| S4 | spec Med ∧ comm Low | Elevated | **Moderate** | partially specific, no claim |
| S6 | spec Med ∧ comm High | Moderate | **Elevated** | claim with partial backing |
| S7 | spec High ∧ comm Low | Moderate | **Low** | specific factual disclosure |

An alternative fix at the *signal* level (rescaling or gating the inputs) was
rejected: it would have moved the correction out of the inspectable layer and
into a threshold, which is exactly what this instrument is built to avoid.

### Evidence

| Metric | Before | After |
| --- | --- | --- |
| paragraphs maxed out (> 80) | 14/21 | 1/21 |
| mean risk | 77.3 | 36.9 |
| risk-disclosure probe | 89.86 | 35.00 |
| rigorous-disclosure probe | 10.14 | 10.14 |
| loud-pledge probe | 65.00 | 75.49 |

The pattern held at scale on a 162-paragraph validation sample: maxed-out cases
fell to **1/162**, mean risk 25.9, with a full spread across the bands
(S9 → Low ≈ 10, S1 → Moderate 35, S6 → Elevated 54–65, S3 → High 75–89). The
instrument discriminates across the range instead of pegging at 90.

### Surface property, stated precisely

DL-001 defines the ordering the spine encodes: **the risk term assigned by the
spine is monotone non-increasing in specificity, and monotone non-decreasing in
commitment when specificity is Low.** This *reverses* an earlier design
assumption that commitment should always lower risk; the evidence refuted it —
a loud claim with no substance is worse than no claim.

Two caveats apply to the defuzzified 0–100 surface, both verified by
`tests/property_test_rule_base.py`:

1. Within the spine, the ordering survives defuzzification up to small centroid
   artifacts where two input terms overlap — largest observed **1.77 risk
   points**, at specificity 0.35 as commitment crosses the Low/Medium boundary,
   with **no band crossings**.
2. The amplifier tiers introduce **intentional** exceptions. Rules conditioned
   on *low* commitment (N2, O2) necessarily withdraw as commitment rises, so
   where opportunity framing or a net-zero claim is High the aggregate score can
   dip by up to **6.35 risk points** as commitment increases. This is the
   amplifier tiers doing their job, not a defect in the spine — but the
   monotonicity claim belongs to the spine, not to the whole surface.

### Consequences ratified with the decision

- A bare net-zero pledge with **no** commitment language now lands Elevated
  (≈ 60), not maximal, because S1's demoted Moderate consequent co-fires and
  drags the centroid down. Maximal risk is reserved for *loud, committed*
  pledges (S3) and the named signatures (G1/G2). See the calibration anchor
  under [LOCK](#lock--rulebase-locked-v1).
- **Watch item:** one paragraph scored 89 on the strength of `commitment =
  0.997` for generic "our policy" language. Carried into DL-003.

---

## DL-002 — membership-function shape: triangular kept

**Date:** 2026-06-16 · **Trigger:** the last open instrument decision before the
lock. Harness: `scripts/validation/mf_experiment.py -n 200 --gate 0.5`.

### Question

Triangular input MFs fully activate `Low` only at exactly `specificity = 0`. A
trapezoidal `Low` with a plateau (`trapmf [0, 0, 0.15, 0.4]`) would treat the
whole near-zero pile-up of vague text as *fully* Low. Does the plateau sharpen
discrimination, or is it a parameter to defend for no gain?

### Experiment

Rule base and the other three inputs held fixed; **only** the `specificity`
`Low` MF varied. The same 162 gated TCFD paragraphs scored under each.

| Metric | Triangular (locked) | Trapezoidal |
| --- | --- | --- |
| mean risk | 25.92 | 25.94 |
| sd | 16.37 | 16.41 |
| range | [10.01, 89.20] | [10.01, 90.00] |
| band counts (Low/Mod/Elev/High) | 73 / 78 / 10 / 1 | 73 / 78 / 10 / 1 |
| **band-boundary crossings** | — | **0 / 162** |

### Decision — keep triangular

Identical per-band counts, near-identical spread, zero crossings. The only
movement anywhere was a single paragraph edging 89.20 → 90.00, still inside the
High band. Triangular uses fewer parameters for no measurable gain in
discrimination, so parsimony decides.

**Why the plateau is inert here:** under AND = min, raising `Low` membership
changes a rule's firing only when specificity is the *smallest* antecedent
*and* the result sits near a band edge. On TCFD that joint condition is never
decision-relevant — vagueness is typically co-bounded by low commitment, which
caps the minimum regardless of the specificity MF shape.

`specificity_trap` remains in [`linguistic_variables.py`](../linguistic_variables.py)
as a documented, reproducible counterfactual, outside the scoring path. It is
the overlay in the paper's membership-function figure
(`artifacts/figures/mf_specificity_trap.png`).

---

## DL-003 — the commitment false-positive tail: isolated

**Date:** 2026-06-16 · **Trigger:** sizing DL-001's watch item before the lock.
Harness: `scripts/validation/hash3_characterize.py -n 500 --gate 0.5`
(419 climate-gated paragraphs).

### Finding

The signature is **commitment High ∧ specificity Low**. Sized on TCFD:

- `commitment ≥ 0.90`: **173/419 (41%)** — the commitment model fires strongly,
  often.
- …**and** `specificity ≤ 0.40`: **6/419 (1.4%)** — bands: Elevated 5, High 1.

DL-001's vagueness requirement already absorbs ~97% of the commitment model's
over-confidence: the 167 high-commitment *specific* paragraphs route to S8/S9
and land Low or Moderate regardless of how strong the commitment signal is. The
false positive survives only where high commitment coincides with low
specificity.

**The 6 residual cases are heterogeneous, not one failure mode:**

| Cause | Cases | Reading |
| --- | --- | --- |
| Commitment fires on boilerplate | 2 | "our policy…" investment talk; recitation of UN SDG-13 target text — the true false positives |
| Genuinely vague aspiration | 2 | e.g. "we want to contribute to the circular economy" — Elevated is arguably correct |
| Specificity model **under**-scored substantive text | 2 | concrete exclusion-list disclosures scored `spec ≈ 0.28`; these land Elevated on low specificity, not on commitment over-firing |

### Verdict — isolated, no rule change

1.4% of the gated sample, one case at High, mixed causes, and the bulk of the
over-firing already contained by the spine. This does not rise to a systematic
band. Recorded as a limitation of the upstream classifiers rather than a
fuzzy-layer defect: correcting it would require distinguishing genuine
boilerplate from genuine commitment at the language-model level, which no rule
edit can do.

**Secondary observation, logged not actioned:** the specificity model
under-scores some substantive exclusion-policy disclosures, inflating their risk
through low specificity. Distinct from the commitment tail, also upstream.

---

## LOCK — `rulebase-locked-v1`

**Date:** 2026-06-16 · **Annotated tag:** `rulebase-locked-v1` · **Commit:** `a40288a`

The rules and the membership functions are frozen together, once, before any
contact with the held-out contrast set. Anything changed after this point is a
separate, logged instrument version — never a silent edit.

**Locked state**

- **Rules:** 17-rule Mamdani base; spine per DL-001 (`risk = vagueness ×
  claim-strength`; S1 → Moderate; High requires a claim signal).
- **MFs:** all-triangular inputs (DL-002); trapezoidal variant tested and
  rejected.
- **Signals:** `specificity = P('spec')`, `commitment = P('yes')`,
  `sentiment_asymmetry = P('opportunity')`, `netzero = P('net-zero')`; climate
  gate = detector `P('yes') ≥ 0.5`.
- **Models:** five pinned ClimateBERT revisions, recorded in
  [`models.py`](../models.py) and re-recorded in every run manifest and PROV-O
  graph.

**Calibration anchor, re-verified on the locked instrument**
(`scripts/validation/anchor_verify.py`)

A vague net-zero pledge (`specificity = 0.05`, `commitment = 0.05`,
`sentiment_asymmetry = 0.05`, `netzero = 0.95`) scores **60.38 — Elevated**,
through four rules co-firing at strength 0.875: S1 (Moderate), N1 (High),
N2 (Elevated), G1 (High).

This anchor's pre-DL-001 expectation was "fires highest-risk (≈ 90)"; DL-001
made that expectation stale and it was updated **before** the lock rather than
left to be quietly reinterpreted afterwards. The result is also the healthy
one: the graded spine is engaged and actively pulls the score below maximal, so
the calibration is not a hardcoded-signature pass/fail. The named signature G1
fires — keeping the trace legible for case studies — but as one of four
contributors, not the sole driver.

**Verified before locking**

- End-to-end seam test green: key-match, identity, sentiment mapping in-flow,
  and defensibility `max |library − re-derived firing| = 0`, with a PROV-O graph
  emitted (`artifacts/provenance/phase4_seam_run.ttl`).
- DL-002 decided, calibration anchor updated, DL-003 characterized.

---

## DL-004 — convergent and discriminant validity vs. the cheap-talk baseline

**Date:** 2026-06-16 · **Trigger:** the first full-corpus run of the frozen
instrument, plus the external-baseline comparison the lock was built to enable.
Harnesses: `scripts/run_full_corpus.py --gate 0.5`, `scripts/bingler_baseline.py`,
`scripts/provenance_corpus_run.py`. Instrument unchanged — analysis only.

### Baseline definition

Bingler et al. use the **same** ClimateBERT specificity model, so the
per-paragraph baseline is read straight from the saved corpus scores with no
model re-run: `cheap_talk = 1 − P('spec')`.

Firm-level aggregation is **foreclosed by the data**:
`climatebert/tcfd_recommendations` carries only `text` and `label`, where
`label` is the TCFD *category* (`none` / `metrics` / `strategy` / `risk` /
`governance`) and not a greenwashing label, and it has no firm or document
identifiers. Decision: per-paragraph baseline as primary, with the TCFD-category
breakdown as the descriptive "cherry-picking" cut.

### Results

The complete corpus train split (1,300 paragraphs) → climate gate kept
**1,009** (291 dropped as non-climate).

- **Convergent:** Spearman ρ = **0.602** (p ≈ 1.4×10⁻¹⁰⁰, n = 1,009);
  Pearson r = 0.597 for comparison. The distribution is clustered at the output
  MF centroids (≈ 11 / 35 / 65 / 90) — a property of single-term Mamdani
  firing — with S1 the top-firing rule for **428** paragraphs and S9 for 282,
  creating heavy ties at 35. Spearman plus decile bins is therefore the
  appropriate reporting choice.
- **Discriminant:** within the top cheap-talk quartile (n = 253, cheap-talk mean
  0.961, **sd 0.010** — vagueness effectively fixed), GreenRisk still spans
  **35 → 90** (mean 38.6, sd 13.1), with Spearman(commitment, risk) = **0.433**.
  The baseline is blind to claim strength; GreenRisk separates quiet vagueness
  (S1 → ≈ 35) from loud vague pledges (S3 → ≈ 85). This is the four-signal
  design's contribution made measurable.

### The DL-001 signature, visible at corpus scale

The decile curve **bends down** in the vaguest deciles: cheap talk 0.94 / 0.96 /
0.97 → mean risk 38.3 / 40.4 / 36.8, against ≈ 50 at cheap talk 0.82–0.90. The
one place GreenRisk disagrees with a naively monotone cheap-talk reading is
exactly where DL-001 made a principled call. The divergence is a logged design
decision surfacing at scale, not noise.

### Cherry-picking cut (by TCFD category)

metrics (cheap talk 0.204, risk 21.0) ≪ strategy (0.651, 37.4) < risk (0.865,
42.0) ≈ governance (0.850, 43.9). Firms are concrete about the numbers and
vague about the surrounding narrative — a pattern from the cherry-picking
literature, reproduced on GreenRisk's own score without using the category
labels as inputs. The residual `none` category (n = 13, mean risk 50.7) is left
out of the comparison as too small to read.

**Watch-item re-check:** DL-003's commitment tail remains a small residual on
the full 1,009-paragraph run, with no escalation to a systematic band. The
"isolated → documented limitation" verdict holds. No rule change.

**Artifacts:** `artifacts/corpus_run/{tcfd_scored.csv, run_manifest.json,
bingler_stats.json}`, `artifacts/figures/bingler_{convergence,discriminant}.png`,
`artifacts/provenance/corpus_run.{ttl,json}`.

---

## DL-005 — held-out face validity and the symmetric specificity limitation

**Date:** 2026-06-17 · **Trigger:** the one-shot held-out test against the
contrast set — the payoff of the lock discipline. Harnesses:
`scripts/run_contrast_set.py`, `scripts/evaluate_face_validity.py`,
`scripts/provenance_contrast_run.py`. Instrument unchanged — analysis only.

### Adequacy gate, performed blind

The contrast set (15 paragraph-level cases: 9 greenwashing from DWS,
Volkswagen and HSBC, regulator-adjudicated; 6 rigorous from Microsoft and
Ørsted, CDP A-list and SBTi-validated) was inspected **read-only, with no model
run**, before scoring. Three findings shaped the test:

1. Granularity is already paragraph-level — score directly, no aggregation rule
   needed.
2. Expectations are construct-level, so no stale numeric band rubric had to be
   discarded.
3. **Decisive:** the greenwashing group spans *two distinct mechanisms*, only
   one of which the four signals can see.

That third finding is why the set was **stratified before scoring**. Lumping
all 9 greenwashing cases against all 6 reference cases would conflate two
constructs and misread predictable, in-principle misses as failures of the
primary claim. The full pre-registered stratification is reproduced in
[Appendix A](#appendix-a--phase-6-pre-registration-ratified-blind).

### Results, one-shot, against the frozen instrument

- **Primary** — in-scope greenwashing vs. rigorous reference:
  **AUC = 0.867** (n = 5 vs. 6; Mann-Whitney U = 26, one-sided p = 0.026).
  Reported as a demonstration with a large effect size: n is tiny and the
  confidence interval wide, so the argument rests on the AUC and the
  regulator-grounded sourcing, not on the p-value.
- **Boundary** — the 4 greenwashing cases held outside the primary comparison
  (3 out-of-scope specificity-based, 1 boundary promotional) all scored
  **below the flag threshold of 50**, as predicted in advance. The blind spot is
  bounded and predictable.
- At that threshold, sensitivity within the in-scope group is 3/5 (0.60) and
  specificity within the reference group is 5/6 (0.83).

### The limitation this pins

`specificity` is a proxy for substance, and it is foolable **in both
directions** — one root cause, two error modes, both demonstrated on real cases
rather than hypothesised:

- **Low specificity ≠ no substance.** `RD-006` (Ørsted, describing its ESRS
  preparation) is a false positive at 72.7 via S6: confident commitment language
  about a *process*, with no figures, reads as the hollow-pledge signature. The
  curator had pre-flagged it as an edge case.
- **High specificity ≠ good faith.** `GW-004` and `GW-008` are under-flagged
  at ≈ 10 via S9: selective or corrupted numbers route to the low-risk cells
  because the paragraph *reads* concrete.

Two further misses were pre-registered as upstream-signal caveats, and are what
sensitivity 3/5 is made of: **`GW-007`**, a two-sentence advertisement well
below the models' typical training length, where the specificity model read the
"$1 trillion" figure as substance (10.88, S9); and **`GW-002`**, generic ESG
prose where the commitment classifier returned 0.006 and routed the paragraph to
S1 (35.0).

### Verdict

Face validity is supported **within a precisely bounded scope**: GreenRisk
detects vagueness-based ("cheap talk") greenwashing, and is out of scope for
omission- or fraud-based greenwashing where the disclosed numbers themselves are
the problem. All three error classes are logged limitations, not fixes — the
instrument was not changed, and the stratification was not revised after the
scores were seen.

**Artifacts:** `artifacts/contrast_run/{contrast_scored.csv, run_manifest.json,
face_validity_stats.json}`, `artifacts/figures/face_validity.png`,
`artifacts/provenance/contrast_run.{ttl,json}` (which records
`prereg_ratified`).

---

## Appendix A — Phase-6 pre-registration, ratified blind

Ratified **2026-06-17**, from the curator notes and the locked design
philosophy, with **no model run on the contrast set** and the instrument already
frozen. The date is recorded independently in
`artifacts/contrast_run/run_manifest.json` (`prereg_ratified`) and in the
contrast-run PROV-O graph.

| Case | Company | Mechanism | Stratum | Pre-registered expectation |
| --- | --- | --- | --- | --- |
| GW-001, GW-002, GW-003 | DWS | vague aspirational | **in_scope** | elevated |
| GW-005 | Volkswagen | process-talk, no commitment | **in_scope** | moderate–elevated |
| GW-007 | HSBC | vague net-zero pledge | **in_scope** | elevated *(caveat: short, sub-training-length text)* |
| GW-006 | Volkswagen | promotional / awards | **boundary** | uncertain — probes the opportunity-framing tier |
| GW-004 | Volkswagen | specific, corrupted measurement | **out_of_scope** | low (predicted miss) |
| GW-008, GW-009 | HSBC | specific, omission | **out_of_scope** | low (predicted miss) |
| RD-001 … RD-006 | Microsoft, Ørsted | rigorous | **reference** | low *(caveat: RD-006 is process-about-reporting; may not pass the climate gate)* |

**Evaluation rules fixed at the same time:** one-shot scoring on the frozen
instrument, where the first score is the score; the primary test is the in-scope
vs. reference separation, with the boundary probe reported separately;
disagreements inside a stratum are logged as limitations, never as instrument
edits; and the stratification is not revised after the scores are seen.

Both pre-registered caveats — GW-007's length and RD-006's process framing —
turned out to be exactly where the instrument failed. They are recorded here as
predictions made before the fact, not as explanations found afterwards.
