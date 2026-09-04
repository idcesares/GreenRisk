"""Per-score W3C PROV-O construction for GreenRisk outputs."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prov.model import Namespace, ProvDocument

from . import __version__
from .metadata import (
    INSTRUMENT_COMMIT,
    INSTRUMENT_METHOD,
    INSTRUMENT_RULE_COUNT,
    INSTRUMENT_TAG,
    MODEL_REGISTRY,
    SIGNAL_MAP,
)


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_score_provenance(payload: dict[str, Any]) -> ProvDocument:
    """Build a PROV-O graph from a completed ``score-text`` payload."""
    if payload.get("mode") != "text" or payload.get("status") != "scored":
        raise ValueError("PROV-O output requires a completed text score")

    digest = payload["input"]["sha256"]
    now = datetime.now(UTC)
    doc = ProvDocument()
    gr = Namespace("gr", "https://github.com/idcesares/GreenRisk/prov/")
    hf = Namespace("hf", "https://huggingface.co/")
    doc.set_default_namespace("https://github.com/idcesares/GreenRisk/prov/")
    doc.add_namespace(gr)
    doc.add_namespace(hf)

    pipeline = doc.agent(
        f"gr:GreenRiskPipeline_v{__version__}",
        {"prov:type": "prov:SoftwareAgent", "gr:version": __version__},
    )
    paragraph = doc.entity(
        f"gr:paragraph_{digest}",
        {
            "prov:type": "gr:InputParagraph",
            "gr:text_sha256": digest,
            "gr:char_count": payload["input"]["char_count"],
        },
    )
    instrument = doc.entity(
        f"gr:instrument_{INSTRUMENT_TAG}",
        {
            "prov:type": "gr:FuzzyInstrument",
            "gr:tag": INSTRUMENT_TAG,
            "gr:commit": INSTRUMENT_COMMIT,
            "gr:n_rules": INSTRUMENT_RULE_COUNT,
            "gr:method": INSTRUMENT_METHOD,
        },
    )
    activity = doc.activity(
        f"gr:score_{digest}",
        now,
        now,
        {
            "prov:type": "gr:GreenRiskScoring",
            "gr:gate": payload["gate"]["threshold"],
            "gr:climate_probability": payload["gate"]["probability"],
        },
    )
    risk = doc.entity(
        f"gr:risk_{digest}",
        {"prov:type": "gr:RiskScore", "gr:value": payload["risk"]},
    )
    doc.wasAssociatedWith(activity, pipeline)
    doc.used(activity, paragraph)
    doc.used(activity, instrument)

    for short_name in ["detector", *[SIGNAL_MAP[key][0] for key in SIGNAL_MAP]]:
        model = MODEL_REGISTRY[short_name]
        entity = doc.entity(
            f"hf:{model['repo']}",
            {
                "prov:type": "gr:PretrainedModel",
                "gr:short_name": short_name,
                "gr:commit_hash": model["revision"],
            },
        )
        doc.used(activity, entity)

    doc.wasGeneratedBy(risk, activity)
    doc.wasDerivedFrom(risk, paragraph)
    doc.wasDerivedFrom(risk, instrument)
    return doc


def write_score_provenance(payload: dict[str, Any], path: Path) -> None:
    """Serialize a score graph as Turtle or PROV-JSON based on the suffix."""
    document = build_score_provenance(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".ttl":
        document.serialize(str(path), format="rdf", rdf_format="ttl")
    elif path.suffix.lower() == ".json":
        document.serialize(str(path), format="json")
    else:
        raise ValueError("provenance path must end in .ttl or .json")
