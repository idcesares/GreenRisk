# Data

`contrast_set.csv` contains 15 short excerpts and source metadata used in the
post-lock contrast evaluation. The file SHA-256 is recorded in
`artifacts/contrast_run/run_manifest.json` and verified in CI.

The TCFD corpus is not vendored. Research scripts load
`climatebert/tcfd_recommendations` at revision
`aee5c98f0bf7835bfb08308ffc7c17216657976b`; the train Parquet LFS object has
SHA-256 `1f16bb38a021aeafad6935eb5aa3f072c2e51b3dcf01eaee88a32ef537029f1f`.
Consult the upstream dataset card for provenance, licensing, and limitations.

Contrast excerpts remain subject to their underlying source terms. Their
inclusion supports research reproducibility and does not imply endorsement or
a new adjudication by the GreenRisk authors. Do not use this small set as a
general benchmark or split it further for model fitting.
