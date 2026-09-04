"""Tests for the dependency-light signal-scoring interface."""

import argparse

import pytest

from greenrisk.cli import _score_signals, probability
from greenrisk.rule_base import score_paragraph


def test_signal_cli_payload() -> None:
    args = argparse.Namespace(
        specificity=0.2,
        commitment=0.9,
        sentiment_asymmetry=0.4,
        netzero=0.7,
    )
    payload = _score_signals(args)
    assert payload["status"] == "scored"
    assert payload["instrument"]["tag"] == "rulebase-locked-v1"
    assert payload["risk"] == 88.33
    assert payload["trace"][0]["rule"] in {"S3", "N1"}


@pytest.mark.parametrize("value", ["-0.01", "1.01", "nan", "inf"])
def test_cli_rejects_invalid_probability(value: str) -> None:
    with pytest.raises((argparse.ArgumentTypeError, ValueError)):
        probability(value)


@pytest.mark.parametrize(
    "signals",
    [
        {
            "specificity": 1.5,
            "commitment": 0.5,
            "sentiment_asymmetry": 0.5,
            "netzero": 0.5,
        },
        {
            "specificity": 0.5,
            "commitment": 0.5,
            "sentiment_asymmetry": 0.5,
        },
    ],
)
def test_scoring_rejects_invalid_signal_contract(signals: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        score_paragraph(signals)
