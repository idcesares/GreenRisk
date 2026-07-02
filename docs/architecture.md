# Architecture

This document is the complete, self-contained description of the GreenRisk
scoring pipeline: what each stage does, why it is built this way, and how the
pieces fit together. It assumes no prior context beyond the [README](../README.md).

## 1. What GreenRisk does

GreenRisk reads a single paragraph of corporate climate disclosure and returns
an **explainable greenwashing-risk score from 0 to 100**, together with:

- an **activation trace** — the exact set of rules that fired and how strongly,
  so the score is re-derivable by inspection rather than trusted as a black box;
- a **W3C PROV-O provenance graph** — a machine-readable record of which model
  revisions, inputs, and instrument version produced that score.

The scoring instrument is a five-stage pipeline: a relevance gate, four
independent language-model signals, a translation of those signals into fuzzy
linguistic terms, a Mamdani rule base, and centroid defuzzification into the
final score.

```
raw paragraph
   │
   ▼  1. climate gate      is this paragraph about climate at all?         (models.is_climate)
   ▼  2. four signals      four independent ClimateBERT reads              (models.all_signals_batch)
   ▼  3. fuzzification     4 probabilities → 4 linguistic-variable degrees (linguistic_variables.py)
   ▼  4. rule base         17-rule Mamdani inference, AND = min            (rule_base.score_paragraph)
   ▼  5. defuzzification   centroid → risk ∈ [0, 100] + fired-rule trace
   ▼  (parallel) provenance   PROV-O graph of the whole run                (scripts/provenance_*.py)
```

Core modules, at the repository root:

- [`models.py`](../models.py) — the pinned model registry, the scoring layer,
  the signal-to-label mapping (`SIGNAL_MAP`), and the climate-relevance gate.
- [`linguistic_variables.py`](../linguistic_variables.py) — the fuzzy
  variables and their membership functions.
- [`rule_base.py`](../rule_base.py) — the 17-rule Mamdani base,
  `score_paragraph`, and the audit trace.
- [`main.py`](../main.py) — a CLI that scores four precomputed signal values
  through the locked rule base without loading any language model.

## 2. Stage 1 — the climate-relevance gate

Not every paragraph in a disclosure document is about climate at all. Before
any of the four risk signals run, a fifth ClimateBERT classifier
(`climatebert/distilroberta-base-climate-detector`) answers a binary question:
is this paragraph climate-relevant? The gate is `P('yes') ≥ 0.5`; paragraphs
that fail it are dropped before they reach the fuzzy layer. `rule_base.py`
assumes this gating has already happened upstream — it only scores paragraphs
that are already known to be climate-relevant.

## 3. Stage 2 — the four signals

Each signal is read from an independently pinned ClimateBERT classifier (see
[Acknowledgements](acknowledgements.md) for the papers behind each model).
Every signal is **construct-aligned**: it measures its construct directly (a
high specificity score means specific text), and any inversion to a risk
direction happens later, in the rule base — never in the signal itself.

| Fuzzy input | Model | Label read | What it measures |
| --- | --- | --- | --- |
| `specificity` | climate-specificity | `P('spec')` | Whether the text contains concrete figures, dates, or mechanisms, versus vague language |
| `commitment` | climate-commitment | `P('yes')` | Whether the text is making a pledge or claim, versus describing a fact |
| `sentiment_asymmetry` | climate-sentiment | `P('opportunity')` | How opportunity-framed (versus risk-framed or neutral) the text is |
| `netzero` | netzero-reduction | `P('net-zero')` | Whether the text asserts a net-zero target specifically, distinct from a general reduction target |

Two mapping choices are worth stating explicitly, since they are not the only
plausible reading of the underlying models:

- **`netzero` reads `P('net-zero')` alone**, not `P('net-zero') + P('reduction')`.
  The underlying model is a three-way classifier (`none` / `reduction` /
  `net-zero`); reduction targets are quantified against a base year and are
  conceptually the opposite of the vagueness this instrument targets, so
  folding them in would dilute the specific "net-zero pledge with low
  specificity" signature the project is built to catch.
- **`sentiment_asymmetry` reads `P('opportunity')` alone**, not a signed
  combination of opportunity and risk framing. Consequently, risk-framed and
  neutral paragraphs both collapse toward 0 — "balanced" framing does not sit
  at exactly 0.5. This is a deliberate simplification, documented here rather
  than hidden, since it affects how the opportunity-framing rules (Tier 3,
  below) should be read.

## 4. Why fuzzy logic instead of a direct model score

Two more direct alternatives were considered and rejected:

- **Ask a generative model for a 0–100 score directly.** Fast, but
  unauditable: there is no way to independently verify why a given number came
  out, and the same input is not guaranteed to produce the same output.
- **Train a binary greenwashing classifier.** This would need a large,
  reliably labeled greenwashing corpus, which does not exist at scale, and
  would still force a spectrum problem into a binary answer.

GreenRisk instead uses a **Mamdani fuzzy inference system** — the same
inference model used in control engineering, where "how much" matters more
than "on or off." Each of the four signals is expressed not as a single
number but as a **degree of membership** in linguistic terms (Low / Medium /
High), and the final score is produced by combining rules stated in those same
human-readable terms. This makes every step legible: a score is not just a
number, it is a specific, inspectable combination of "specificity is mostly
Low" and "commitment is mostly High," for example.

### Membership functions

All four inputs share the same triangular geometry on `[0, 1]`:

- **Low** — `(0, 0, 0.4)`
- **Medium** — `(0.2, 0.5, 0.8)`
- **High** — `(0.6, 1, 1)`

The output `risk`, on `[0, 100]`, uses four triangular terms for finer
resolution: **Low** `(0, 0, 30)`, **Moderate** `(15, 35, 55)`, **Elevated**
`(45, 65, 85)`, **High** `(70, 100, 100)`.

The `0.4` / `0.6` breakpoints are a theory-driven default, symmetric around the
0.5 calibration midpoint of the underlying binary classifiers, rather than a
value fit to any particular corpus — a corpus-quantile boundary would be
circular (it would define "vague" relative to whatever the sample happens to
contain, rather than in absolute terms). A trapezoidal alternative for the
`specificity` "Low" term — giving it a flat plateau near zero instead of a
single-point peak — was evaluated against the same 162-paragraph validation
sample and produced identical per-band counts and zero band-boundary
crossings; the simpler triangular form is used everywhere. The trapezoidal
variant remains in `linguistic_variables.py` (`specificity_trap`) as a
documented, reproducible comparison point, not as part of the scoring path.

Rule combination uses **AND = min**; the final score is obtained by **centroid
defuzzification** over the aggregated output membership.

## 5. Stage 3–4 — the 17-rule base

The central design principle is:

> **Risk = vagueness × claim-strength.**

A vague paragraph that makes **no claim** is a weak disclosure, not
greenwashing — it simply has nothing to evaluate. A vague paragraph that makes
a **confident, unspecific claim** is the classic greenwashing signature: the
promise without the substance behind it. The rule base is built so that risk
is monotone **non-increasing** in specificity, and monotone **non-decreasing**
in commitment specifically when specificity is low — a loud, unsubstantiated
pledge is scored higher than either a quiet non-claim or a specific,
substantiated one.

The 17 rules are organized into four tiers:

**Tier 1 — the spine (S1–S9).** All nine combinations of `specificity` ×
`commitment`:

| Rule | Specificity | Commitment | Result | Rationale |
| --- | --- | --- | --- | --- |
| S1 | Low | Low | Moderate | Vague with no claim — a weak disclosure, not greenwashing |
| S2 | Low | Medium | Elevated | Vague, some commitment |
| S3 | Low | High | **High** | Loud pledge, no substance — the core greenwashing signature |
| S4 | Medium | Low | Moderate | Partially specific, no claim |
| S5 | Medium | Medium | Moderate | Genuinely middling (rarely fires on real text) |
| S6 | Medium | High | Elevated | Committed, partially backed |
| S7 | High | Low | Low | Specific, factual disclosure, no claim |
| S8 | High | Medium | Low | Specific, some commitment |
| S9 | High | High | Low | Rigorous, substantiated disclosure |

**Tier 2 — net-zero amplifiers (N1–N3).** Escalate or exonerate specifically
around net-zero claims: a net-zero pledge with no detail (N1) or no
commitment language (N2) escalates; a net-zero claim paired with high
specificity (N3) is exonerated.

**Tier 3 — opportunity-framing amplifiers (O1–O3).** Escalate when strongly
opportunity-framed text is also vague (O1) or uncommitted (O2); explicitly
does not escalate when opportunity framing is paired with both high
specificity and high commitment (O3 — "earned optimism").

**Tier 4 — named signatures (G1–G2).** Two rules that fire on the classic
composite patterns — a vague, uncommitted net-zero pledge (G1), and a vague,
optimistically-framed net-zero pledge (G2) — kept separate from the spine so
that the audit trace can point directly at "this matched the classic
greenwashing pattern" in case studies, in addition to the graded spine score.

### Worked example

Two short paragraphs illustrate why the spine is shaped this way:

- *"Climate change could exacerbate threats to our business, including
  exposure to severe storms, drought, fires, and floods."* Low specificity
  (no figures), but also low commitment — this is a factual risk statement,
  not a pledge. Rule S1 fires: **Moderate**, not High. This is a weak
  disclosure, not greenwashing.
- *"We are committed to a net-zero future for all."* Low specificity, but
  high commitment — a confident claim with nothing concrete behind it. Rule
  S3 fires: **High**. This is the greenwashing signature.

An earlier version of the rule base scored both examples as maximal risk,
because it treated "vague" and "greenwashing" as synonyms without checking
whether a claim was actually being made. The spine above is the corrected
version, and is the one implemented in `rule_base.py`.

### A documented limitation of the commitment signal

The commitment classifier can fire strongly on generic policy or framework
language (e.g. "our policy is...") even when no substantive pledge is being
made. Combined with low specificity, this produces a small false-positive
tail: in a systematic check against gated TCFD text, this pattern accounted
for roughly 1.4% of paragraphs, concentrated in the Elevated band with a
single High-band case. This is a bounded, known limitation of the upstream
classifier — the fuzzy layer does not attempt to correct for it, since doing
so would require distinguishing genuine boilerplate from genuine commitment at
the language-model level, not the rule level.

## 6. Stage 5 — output and provenance

`rule_base.score_paragraph` returns the final centroid score together with a
trace of every rule that fired, sorted by firing strength, independently
re-derived from the locked membership functions (not read from the inference
library's internal state) — so the trace and the library's own computation can
be checked against each other. `scripts/provenance_*.py` wrap a scoring run in
a W3C PROV-O graph that binds the results to the exact pinned model revisions
and the instrument version tag, so any score can be traced back to precisely
what produced it.

## 7. The locked instrument

The rule base and membership functions described above are frozen under the
tag `rulebase-locked-v1`. After that point, any change to the rules,
membership functions, model revisions, or signal mappings is treated as a
separate, explicitly logged instrument change — never a silent edit. This
matters because the validation evidence in [`docs/validation.md`](validation.md)
was collected against this exact, unchanging instrument, including a
held-out test set that was not read or scored until after the freeze. See
[`MASTER_PLAN.md`](../MASTER_PLAN.md) for the repository map and reproduction
commands.
