# This script builds a minimal PROV-O graph for one paragraph and one model.

import json
import hashlib
import os
import shutil
from datetime import datetime
from datetime import timezone
from pathlib import Path
from prov.model import ProvDocument, Namespace, PROV_TYPE
from prov.dot import prov_to_dot


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
    model_commit_hash: str,
    output_label: str,
    output_probability: float,
) -> ProvDocument:
    
    # Build a minimal PROV-O document tracing one paragraph through one model.

    doc = ProvDocument()
    gr = Namespace("gr", "https://greenrisk.ppgi.ufrj.br/prov/")
    hf = Namespace("hf", "https://huggingface.co/")
    doc.set_default_namespace("https://greenrisk.ppgi.ufrj.br/prov/")
    doc.add_namespace(gr)
    doc.add_namespace(hf)

    para_hash = hashlib.sha256(paragraph_text.encode()).hexdigest()[:12]
    e_paragraph = doc.entity(
        f"gr:paragraph_{para_hash}",
        {
            "prov:type": "gr:InputParagraph",
            "gr:text_preview": paragraph_text[:100] + "...",
            "gr:text_sha256": para_hash,
            "gr:char_count": len(paragraph_text),
        },
    )

    e_model = doc.entity(
        f"hf:{model_name}",
        {
            "prov:type": "gr:PretrainedModel",
            "gr:huggingface_repo": model_name,
            "gr:commit_hash": model_commit_hash,
        },
    )

    e_score = doc.entity(
        f"gr:score_{para_hash}_{model_name.split('/')[-1]}",
        {
            "prov:type": "gr:ClassificationScore",
            "gr:label": output_label,
            "gr:probability": str(output_probability),
            "gr:model_used": model_name,
        },
    )


    a_inference = doc.activity(
        f"gr:inference_{para_hash}_{model_name.split('/')[-1]}",
        datetime.now(timezone.utc),
        datetime.now(timezone.utc),
        {
            "prov:type": "gr:ModelInference",
            "gr:model_repo": model_name,
            "gr:model_commit": model_commit_hash,
            "gr:truncation": "True",
            "gr:max_length": "512",
        },
    )


    ag_pipeline = doc.agent(
        "gr:GreenRiskPipeline_v0.1",
        {
            "prov:type": "prov:SoftwareAgent",
            "gr:version": "0.1.0",
        },
    )


    doc.wasGeneratedBy(e_score, a_inference)

    doc.used(a_inference, e_paragraph)
    doc.used(a_inference, e_model)

    doc.wasAssociatedWith(a_inference, ag_pipeline)

    doc.wasDerivedFrom(e_score, e_paragraph)

    return doc


if __name__ == "__main__":

    TEST_PARAGRAPH = (
        "We are committed to achieving net-zero greenhouse gas emissions across "
        "our entire value chain by 2050. Our sustainability strategy places "
        "climate action at the core of our business, creating long-term value "
        "for shareholders while contributing to a more sustainable future."
    )
    MODEL_NAME = "climatebert/distilroberta-base-climate-detector"
    MODEL_HASH = "2c3bc660d45a59e31b35f5d3e365ee4f59fdf76c"

    OUTPUT_LABEL = "yes"
    OUTPUT_PROB = 0.99

    print("Building PROV-O document...")
    doc = build_first_provenance(
        paragraph_text=TEST_PARAGRAPH,
        model_name=MODEL_NAME,
        model_commit_hash=MODEL_HASH,
        output_label=OUTPUT_LABEL,
        output_probability=OUTPUT_PROB,
    )

    output_dir = Path(__file__).resolve().parents[1] / "artifacts" / "provenance"
    output_dir.mkdir(parents=True, exist_ok=True)
    ttl_path = output_dir / "first_provenance.ttl"
    doc.serialize(str(ttl_path), format="rdf", rdf_format="ttl")
    print(f"\nTurtle file written: {ttl_path}")

    print("\n" + "=" * 70)
    print("PROV-O GRAPH (Turtle format)")
    print("=" * 70)
    with open(ttl_path, encoding="utf-8") as f:
        print(f.read())

    try:
        if not _ensure_dot_on_path():
            raise RuntimeError(_graphviz_install_hint())

        dot = prov_to_dot(doc)
        png_path = output_dir / "first_provenance.png"
        dot.write_png(str(png_path))
        print(f"Visualization written: {png_path}")
        print("(Open it to see the graph visually — entities are yellow ovals,")
        print(" activities are blue rectangles, agents are orange pentagons.)")
    except Exception as e:
        print(f"\nVisualization skipped: {e}")
        if "graphviz" not in str(e).lower() and "dot" not in str(e).lower():
            print(_graphviz_install_hint())
        print("Not required — the .ttl file is the actual deliverable.")

    json_path = output_dir / "first_provenance.json"
    doc.serialize(str(json_path), format="json")
    print(f"\nJSON file written: {json_path}")