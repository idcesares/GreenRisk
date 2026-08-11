# AI Usage

This statement covers the **software artifact in this repository**: the locked
instrument, the scripts, the tests, the provenance wiring, and this
documentation. The accompanying paper
([`greenrisk_paper.pdf`](greenrisk_paper.pdf)) carries its own AI usage
statement covering the manuscript.

It is published here for the same reason every score in this project ships with
an activation trace and a provenance graph: a result should carry a record of
what produced it.

## Where generative AI was used

Generative-AI tools were used as an **execution and review layer**, under author
direction:

- **Agent-based coding assistants** supported implementation, debugging,
  testing, and the reproducibility engineering of the pipeline — the artifact
  producers under `scripts/`, the smoke and property tests under `tests/`, the
  PROV-O serialization, and the consolidation of internal working notes into the
  public documentation under `docs/`.
- **Language models accessed through APIs** assisted with organizing and
  analyzing a large body of candidate references, and with reviewing prose for
  clarity, structure, and internal consistency.

All AI-assisted code, analyses, and text were reviewed by the authors before
inclusion. All cited sources were checked against the original publications.

## Where it was not used

The following were determined by the authors and are not AI-generated
judgments:

- the research question, the domain analysis, and the selection of the four
  constructs;
- the signal mappings, the membership functions, and the 17-rule Mamdani base,
  including the DL-001 correction that reshaped the spine;
- the evaluation protocol — the decision to freeze the instrument, the blind
  pre-registration of the held-out contrast set, and the one-shot scoring
  discipline;
- the interpretation of the evidence, the scope limitation the results expose,
  and the conclusions drawn from them.

Every one of these decisions is recorded in [`decisions.md`](decisions.md) with
the evidence that produced it and the date it was ratified. The AI systems did
not act as autonomous researchers or authors, and were not treated as a source
of evidence.

## Why this is checkable rather than merely asserted

The project's existing discipline is what makes the division above verifiable
rather than a claim about intent:

- every instrument decision was logged **before** it was relied on, and the
  alternatives that were rejected are logged with it;
- the instrument was frozen at `rulebase-locked-v1` (commit `a40288a`) before
  the held-out case set was inspected, so no post-hoc adjustment — by a human or
  a model — could have fitted it to the test;
- the held-out set was scored **once**, against the pre-registered
  stratification published in
  [Appendix A of the decision record](decisions.md#appendix-a--phase-6-pre-registration-ratified-blind);
- the five ClimateBERT classifiers are pinned by revision, and every run emits a
  W3C PROV-O graph binding its results to those revisions and to the instrument
  tag;
- the claims this documentation makes about the rule base are asserted in
  [`tests/property_test_rule_base.py`](../tests/property_test_rule_base.py), so
  a change that breaks them fails rather than passing silently.

[`AGENTS.md`](../AGENTS.md) exists for the same reason: it constrains what an
agent contributing to this repository may treat as a routine change, and states
explicitly that any edit to `MODEL_REGISTRY`, `SIGNAL_MAP`, the membership
functions, or `RULES` is an instrument change subject to the logging and
re-validation discipline above.

## Responsibility

The authors retain full responsibility for the software, the reported results,
and the citations in this repository.
