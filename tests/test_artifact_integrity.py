"""Committed research outputs remain bound to their provenance records."""

from scripts.verify_artifact_integrity import verify_run


def test_corpus_artifacts() -> None:
    verify_run("corpus_run", "corpus_run")


def test_contrast_artifacts() -> None:
    verify_run("contrast_run", "contrast_run")
