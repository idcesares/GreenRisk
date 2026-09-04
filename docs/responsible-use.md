# Responsible use

GreenRisk is a research screening instrument for paragraph-level corporate
climate disclosures. It can help researchers and reviewers prioritize passages
for closer inspection and study how a fixed set of linguistic constructs behave.

## Appropriate uses

- exploratory research and method comparison;
- triage that leads to human review of the full disclosure and supporting data;
- reproducibility studies using the pinned models and instrument;
- sensitivity, fairness, robustness, and ablation analysis reported with scope.

## Inappropriate uses

- asserting that an organization has legally or factually committed
  greenwashing based on a score;
- automated enforcement, investment, credit, employment, or other high-impact
  decisions without independent evidence and accountable human review;
- ranking organizations from isolated paragraphs as if the scores measured
  organization-wide conduct;
- removing the climate gate, overriding it, or changing thresholds without
  recording the change;
- presenting the learned ClimateBERT classifiers as fully interpretable.

## Known limitations

GreenRisk operationalizes risk mainly through specificity, commitment,
opportunity framing, and net-zero language. A false but detailed claim may score
low, while a cautious but short legitimate statement may score higher. The
instrument does not verify facts, detect material omissions, assess supplied
evidence, or model the broader reporting context. All upstream classifier
errors flow into the fuzzy layer. Performance can vary by language, sector,
jurisdiction, document type, and time; only English climate-disclosure text is
represented in the committed evaluation.

The reported contrast evaluation is small. Its expectations were not used to
tune the post-lock instrument, but they were published in the same commit as
the first results, so it is not an externally timestamped blind
preregistration. The corpus comparison also shares classifier-derived
constructs with its baseline and is not independent criterion validation.

## Review checklist

Before relying on a score, retain the source paragraph and document context,
inspect the climate-gate decision, review all fired rules rather than only the
top rule, check model/instrument revisions, corroborate claims with external
evidence, and document who made the final judgment. When `--force` is used,
record why the climate gate was overridden.

Security or harmful-use concerns can be reported through GitHub's private
vulnerability-reporting channel if enabled; scientific limitations belong in a
public issue with a minimal reproducible example and no sensitive data.
