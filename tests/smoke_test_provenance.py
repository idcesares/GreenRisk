"""Smoke test the foundation PROV-O graph without rewriting committed artifacts."""

import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from scripts.first_provenance import (  # noqa: E402
    MODEL_NAME,
    MODEL_REVISION,
    OUTPUT_LABEL,
    OUTPUT_PROBABILITY,
    TEST_PARAGRAPH,
    build_first_provenance,
)


def main() -> None:
    doc = build_first_provenance(
        paragraph_text=TEST_PARAGRAPH,
        model_name=MODEL_NAME,
        model_revision=MODEL_REVISION,
        output_label=OUTPUT_LABEL,
        output_probability=OUTPUT_PROBABILITY,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        ttl_path = pathlib.Path(tmpdir) / "first_provenance.ttl"
        json_path = pathlib.Path(tmpdir) / "first_provenance.json"
        doc.serialize(str(ttl_path), format="rdf", rdf_format="ttl")
        doc.serialize(str(json_path), format="json")

        ttl_text = ttl_path.read_text(encoding="utf-8")
        json_text = json_path.read_text(encoding="utf-8")

    required_terms = (
        "gr:InputParagraph",
        "gr:PretrainedModel",
        "gr:ClassificationScore",
        MODEL_REVISION,
    )
    missing = [term for term in required_terms if term not in ttl_text]
    if missing:
        raise AssertionError(f"Missing provenance terms: {missing}")
    if "GreenRiskPipeline_v0.1" not in json_text:
        raise AssertionError("Missing pipeline agent in PROV-JSON output")

    print("Provenance smoke test passed.")


if __name__ == "__main__":
    main()
