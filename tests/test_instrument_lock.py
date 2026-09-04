"""Machine-readable guardrails for coordinates fixed by rulebase-locked-v1."""

import hashlib
import json

from greenrisk.linguistic_variables import INPUTS, risk
from greenrisk.metadata import (
    INSTRUMENT_COMMIT,
    MODEL_REGISTRY,
    SIGNAL_MAP,
    TCFD_DATASET_REVISION,
)
from greenrisk.rule_base import RULES


def test_locked_coordinates() -> None:
    assert INSTRUMENT_COMMIT == "a40288ac8eacfe0de1987884ec03bea9457972c5"
    assert TCFD_DATASET_REVISION == "aee5c98f0bf7835bfb08308ffc7c17216657976b"
    assert SIGNAL_MAP == {
        "specificity": ("specificity", "spec"),
        "commitment": ("commitment", "yes"),
        "sentiment_asymmetry": ("sentiment", "opportunity"),
        "netzero": ("netzero", "net-zero"),
    }
    assert {name: value["revision"] for name, value in MODEL_REGISTRY.items()} == {
        "detector": "2c3bc660d45a59e31b35f5d3e365ee4f59fdf76c",
        "specificity": "4ada96ed4bf5c3a7a711282e41f1ab9b29f0ddea",
        "commitment": "17337c3292df16a8fe93b1505dfe4122d50a4c91",
        "sentiment": "e9f9a94ee4263f5ad5cfc97b8539a497fc88aa7d",
        "netzero": "25cf57e30613a2156fee1fe3f917036df4a5c0d1",
    }
    assert len(RULES) == 17


def test_locked_numerical_payload_hash() -> None:
    """Hash all numerical/model coordinates while excluding explanatory notes."""
    payload = {
        "models": MODEL_REGISTRY,
        "signals": {name: list(mapping) for name, mapping in SIGNAL_MAP.items()},
        "rules": [
            [rule_id, [list(term) for term in terms], consequent]
            for rule_id, terms, consequent, _note in RULES
        ],
        "inputs": {
            variable.label: {
                term: variable[term].mf.tolist() for term in ("Low", "Medium", "High")
            }
            for variable in INPUTS
        },
        "risk": {
            term: risk[term].mf.tolist()
            for term in ("Low", "Moderate", "Elevated", "High")
        },
    }
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == (
        "841fc8fb5ee2dbe4d3cfd55fa3154cc22cc50907575d878aa3b40a1bdfe2190b"
    )
