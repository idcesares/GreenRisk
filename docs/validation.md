# Validation

This document lays out the evidence for GreenRisk's validity, in two
independent layers: a large-scale statistical comparison against a validated
baseline, and a held-out, case-level face-validity test against real,
regulator-adjudicated examples. It also states the instrument's scope limit
plainly, with the specific cases that expose it.

Both layers were run against the same **frozen instrument**
(`rulebase-locked-v1`, see [Architecture §7](architecture.md#7-the-locked-instrument)).
The held-out case set (Layer 2) was not inspected or scored until after the
instrument was frozen, and its evaluation criteria were fixed in advance of
scoring — the point of freezing the instrument first is that neither layer of
evidence could have been produced by tuning the rules to fit the answer.

## Layer 1 — large-scale comparison against a validated baseline

**Setup.** 1,300 paragraphs from the `climatebert/tcfd_recommendations` corpus
were passed through the climate-relevance gate; 1,009 passed and were scored
by the full pipeline. Each paragraph's score was compared against an
established external baseline: the "cheap talk" measure from Bingler et al.
(`1 - P('spec')`, i.e. one minus the specificity model's own output), the
metric introduced and validated in the paper the specificity classifier itself
comes from (see [Acknowledgements](acknowledgements.md)).

**Convergent validity.** GreenRisk's score correlates strongly with cheap
talk: Spearman ρ = 0.60 (p ≈ 1.4×10⁻¹⁰⁰, n = 1,009). This establishes that
GreenRisk is tracking the same underlying signal as an already-validated
method, not measuring noise.

**Discriminant validity.** Restricting to the most vague quartile of text by
the cheap-talk measure (n = 253, cheap-talk mean 0.96, standard deviation
0.01 — a group the baseline treats as essentially uniform), GreenRisk's score
still spans 35–90 (mean 38.6, sd 13.1), correlated with the commitment signal
at Spearman ρ = 0.43. Where the baseline sees a single undifferentiated mass
of vague text, GreenRisk separates "vague and quiet" (a weak disclosure) from
"vague and loud" (a confident, unsubstantiated pledge). This is the concrete,
measured value the four-signal design adds over the single-signal baseline.

**The convergence curve is not monotone, and that is by design.** Mean risk
climbs with cheap talk through the middle deciles but bends down in the most
vague decile (cheap-talk ≈ 0.94–0.97 → mean risk drops to the high 30s/low
40s, versus roughly 50 at cheap-talk ≈ 0.82–0.90). This is exactly the
Tier-1 spine's S1 rule surfacing at scale: maximally vague text that makes no
claim is deliberately scored lower than moderately vague text that does. The
divergence from a naively monotone baseline is a designed property of the
rule base, not an artifact.

**Descriptive cut by disclosure category.** Scored by TCFD category, metrics
sections are concrete (mean cheap-talk 0.20, mean risk 21.0) while strategy,
risk, and governance sections are markedly more vague (cheap-talk 0.65–0.87,
risk 37–44) — a pattern consistent with prior "cherry-picking" findings in the
climate-disclosure literature, reproduced here on GreenRisk's own score.

## Layer 2 — held-out face validity against real, adjudicated cases

**The case set.** `data/contrast_set.csv` contains 15 paragraph-level cases
built entirely from public sources, each with its own citation:

- 9 greenwashing cases, drawn from enforcement actions and rulings against
  **DWS Group** (SEC settlement; German Frankfurt Public Prosecutor's Office
  fine), **Volkswagen AG** (U.S. EPA/DOJ "Dieselgate" action), and **HSBC UK
  Bank plc** (UK Advertising Standards Authority ruling);
- 6 reference cases of rigorous disclosure, from **Microsoft** (CDP A-list,
  SBTi-validated) and **Ørsted A/S** (CDP A-list, SBTi-validated).

**Two mechanisms, one in scope.** Inspecting the case set before scoring
surfaced an important structural fact: the greenwashing cases split into two
distinct mechanisms. **Vagueness-based greenwashing** ("cheap talk" —
aspirational language with no specifics) is exactly what the four-signal
design targets. **Specificity-based greenwashing** — concrete, detailed
figures that are nonetheless selective, corrupted, or misleading in what they
omit — works through a mechanism the instrument's signals cannot see, since
`specificity` reads a paragraph's surface form, not the truthfulness of its
numbers. The case set was stratified into **in-scope** (vagueness-based),
**boundary** (a promotional/awards case, probing the opportunity-framing
tier), and **out-of-scope** (specificity-based) groups before any scoring took
place, so that out-of-scope misses are read as a documented scope limit rather
than as a failure of the primary claim.

**Primary result.** In-scope greenwashing separates cleanly from the rigorous
reference group: AUC = 0.87 (n = 5 vs. 6; Mann-Whitney U = 26, one-sided
p = 0.026). The sample is small by design — held-out, hand-curated,
regulator-grounded case sets do not scale the way a corpus run does — so this
is reported as a demonstration with a large effect size, not as a
statistically definitive result on its own; it is the second, independent
layer of evidence alongside Layer 1's corpus-scale statistics, not a
replacement for it.

**Boundary result.** All 4 of the out-of-scope, specificity-based
greenwashing cases scored below the flag threshold, exactly as predicted in
advance — confirming that the instrument's blind spot is precise and
predictable rather than arbitrary.

## Scope limitation: specificity is a proxy, and proxies can be fooled

`specificity` measures whether a paragraph *reads* as concrete — numbers,
dates, named mechanisms — not whether those numbers are honest or complete.
That proxy can fail in both directions, and both failure modes are visible in
the held-out cases rather than hypothetical:

- **Low specificity does not always mean low substance.** Case `RD-006`
  (Ørsted, describing its preparation for EU CSRD/ESRS reporting) scored 72.7
  — Elevated — because it uses confident commitment language while describing
  a *process* rather than citing figures. It is a false positive against a
  rigorous discloser, produced by the same signature (vague-but-committed)
  that correctly flags genuine greenwashing elsewhere.
- **High specificity does not always mean good faith.** Cases `GW-004` and
  `GW-008` — Volkswagen's tailpipe-emissions figures published during the
  period its defeat-device software was active, and HSBC's tree-planting
  commitment set against financed fossil-fuel emissions roughly fifty times
  larger — both scored Low. The paragraphs are specific; what they omit is
  not visible to a paragraph-level text classifier.

Two further upstream-signal cases are documented for completeness: `GW-007`
(a short advertising sentence, below the typical training-length paragraph,
where the specificity model misread a dollar figure) and `GW-002` (generic
ESG prose where the commitment classifier read near-zero commitment despite
the surrounding case being part of a documented misrepresentation).

**The resulting, precisely bounded claim:** GreenRisk detects
vagueness-based ("cheap talk") greenwashing, with measured effect sizes at
both corpus scale and case-study scale. It is not designed to detect, and
does not reliably detect, omission- or fraud-based greenwashing where the
disclosed numbers themselves are the problem. Catching that second mechanism
would require verifying claims against external data, not just reading the
paragraph — a different problem from the one this instrument solves.
