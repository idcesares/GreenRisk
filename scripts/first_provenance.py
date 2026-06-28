"""Emit the foundation PROV-O graph for one detector inference example."""

import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from prov.dot import prov_to_dot
from prov.model import Namespace, ProvDocument


TEST_PARAGRAPH = (
    "We are committed to achieving net-zero greenhouse gas emissions across "
    "our entire value chain by 2050. Our sustainability strategy places "
    "climate action at the core of our business, creating long-term value "
    "for shareholders while contributing to a more sustainable future."
)
MODEL_NAME = "climatebert/distilroberta-base-climate-detector"
MODEL_REVISION = "2c3bc660d45a59e31b35f5d3e365ee4f59fdf76c"
OUTPUT_LABEL = "yes"
OUTPUT_PROBABILITY = 0.99


def _graphviz_install_hint() -> str:
    if shutil.which("winget"):
        return "Install Graphviz binary (Windows): winget install Graphviz.Graphviz"
    return "Install Graphviz and ensure the 'dot' executable is on PATH."


def _ensure_dot_on_path() -> bool:
    if shutil.which("dot"):
        return True

    windows_candidates = (
        Path("C:/Program Files/Graphviz/bin"),
        Path("C:/Program Files (x86)/Graphviz/bin"),
    )
    for candidate in windows_candidates:
        dot_exe = candidate / "dot.exe"
        if dot_exe.exists():
            os.environ["PATH"] = f"{candidate}{os.pathsep}{os.environ.get('PATH', '')}"
            return shutil.which("dot") is not None

    return False


def build_first_provenance(
    paragraph_text: str,
    model_name: str,
    model_revision: str,
    output_label: str,
    output_probability: float,
) -> ProvDocument:
    """Build a minimal PROV-O graph for one paragraph-level model inference."""

    doc = ProvDocument()
    gr = Namespace("gr", "https://greenrisk.ppgi.ufrj.br/prov/")
    hf = Namespace("hf", "https://huggingface.co/")
    doc.set_default_namespace("https://greenrisk.ppgi.ufrj.br/prov/")
    doc.add_namespace(gr)
    doc.add_namespace(hf)

    para_hash = hashlib.sha256(paragraph_text.encode()).hexdigest()[:12]
    model_slug = model_name.split("/")[-1]

    paragraph = doc.entity(
        f"gr:paragraph_{para_hash}",
        {
            "prov:type": "gr:InputParagraph",
            "gr:text_preview": paragraph_text[:100] + "...",
            "gr:text_sha256": para_hash,
            "gr:char_count": len(paragraph_text),
        },
    )
    model = doc.entity(
        f"hf:{model_name}",
        {
            "prov:type": "gr:PretrainedModel",
            "gr:huggingface_repo": model_name,
            "gr:commit_hash": model_revision,
        },
    )
    score = doc.entity(
        f"gr:score_{para_hash}_{model_slug}",
        {
            "prov:type": "gr:ClassificationScore",
            "gr:label": output_label,
            "gr:probability": str(output_probability),
            "gr:model_used": model_name,
        },
    )

    timestamp = datetime.now(timezone.utc)
    inference = doc.activity(
        f"gr:inference_{para_hash}_{model_slug}",
        timestamp,
        timestamp,
        {
            "prov:type": "gr:ModelInference",
            "gr:model_repo": model_name,
            "gr:model_commit": model_revision,
            "gr:truncation": "True",
            "gr:max_length": "512",
        },
    )
    pipeline = doc.agent(
        "gr:GreenRiskPipeline_v0.1",
        {
            "prov:type": "prov:SoftwareAgent",
            "gr:version": "0.1.0",
        },
    )

    doc.wasGeneratedBy(score, inference)
    doc.used(inference, paragraph)
    doc.used(inference, model)
    doc.wasAssociatedWith(inference, pipeline)
    doc.wasDerivedFrom(score, paragraph)

    return doc


def write_outputs(doc: ProvDocument, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    ttl_path = output_dir / "first_provenance.ttl"
    json_path = output_dir / "first_provenance.json"
    doc.serialize(str(ttl_path), format="rdf", rdf_format="ttl")
    doc.serialize(str(json_path), format="json")
    print(f"Wrote {ttl_path}")
    print(f"Wrote {json_path}")

    try:
        if not _ensure_dot_on_path():
            raise RuntimeError(_graphviz_install_hint())

        png_path = output_dir / "first_provenance.png"
        prov_to_dot(doc).write_png(str(png_path))
        print(f"Wrote {png_path}")
    except Exception as exc:
        print(f"PNG render skipped: {exc}")


def main() -> None:
    doc = build_first_provenance(
        paragraph_text=TEST_PARAGRAPH,
        model_name=MODEL_NAME,
        model_revision=MODEL_REVISION,
        output_label=OUTPUT_LABEL,
        output_probability=OUTPUT_PROBABILITY,
    )
    output_dir = Path(__file__).resolve().parents[1] / "artifacts" / "provenance"
    write_outputs(doc, output_dir)


if __name__ == "__main__":
    main()
