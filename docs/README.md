# GreenRisk — Documentation

- [`greenrisk_paper.pdf`](greenrisk_paper.pdf) — the final project paper,
  *GreenRisk: An Explainable-by-Construction Fuzzy Instrument for Scoring
  Greenwashing Risk in Corporate Climate Disclosures*.
- [`architecture.md`](architecture.md) — the full scoring pipeline: the
  climate-relevance gate, the four ClimateBERT signals, why the project uses
  fuzzy inference, the membership functions, and the 17-rule Mamdani base,
  worked through with examples.
- [`validation.md`](validation.md) — the validity evidence, in two
  independent layers: a 1,009-paragraph statistical comparison against a
  published baseline, and a held-out, case-level test against real,
  regulator-adjudicated companies. Includes the instrument's documented scope
  limitation.
- [`decisions.md`](decisions.md) — the decision record: every instrument
  decision in the order it was taken, with the evidence behind it, the
  alternatives that were rejected, the lock itself, and the blind
  pre-registration of the held-out test. The `DL-00x` identifiers cited in the
  paper resolve here.
- [`ai-usage.md`](ai-usage.md) — how generative AI was and was not used in
  building this artifact, and what makes that division checkable.
- [`acknowledgements.md`](acknowledgements.md) — citations for the ClimateBERT
  models, the TCFD framework, the fuzzy-inference and provenance standards
  this project builds on, and the sources behind the held-out case set.

For the repository layout, the locked-instrument specification, and the exact
commands to reproduce every artifact in `artifacts/`, see
[`../MASTER_PLAN.md`](../MASTER_PLAN.md). For a quick start, see
[`../README.md`](../README.md).
