"""Run-level PROV-O for the held-out contrast-set evaluation.

Mirrors scripts/provenance_corpus_run.py: binds the held-out results + stats
(by sha256) to the run that produced them + the 5 pinned model commits + the
frozen instrument tag. Reads the run manifest as single source of truth.

Run:  uv run python scripts/provenance_contrast_run.py
"""
import hashlib
import json
import pathlib
import sys
from datetime import datetime

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from prov.model import ProvDocument, Namespace

from models import MODEL_REGISTRY, SIGNAL_MAP
from rule_base import RULES

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "artifacts" / "contrast_run"
MANIFEST = RUN_DIR / "run_manifest.json"
OUT_DIR = ROOT / "artifacts" / "provenance"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    manifest = json.loads(MANIFEST.read_text())
    when = datetime.fromisoformat(manifest["timestamp_utc"])

    doc = ProvDocument()
    gr = Namespace("gr", "https://greenrisk.ppgi.ufrj.br/prov/")
    hf = Namespace("hf", "https://huggingface.co/")
    doc.set_default_namespace("https://greenrisk.ppgi.ufrj.br/prov/")
    doc.add_namespace(gr)
    doc.add_namespace(hf)

    agent = doc.agent("gr:GreenRiskPipeline_v0.2",
                      {"prov:type": "prov:SoftwareAgent", "gr:version": "0.2.0"})
    instrument = doc.entity("gr:instrument_" + manifest["instrument_tag"],
                            {"prov:type": "gr:FuzzyInstrument",
                             "gr:tag": manifest["instrument_tag"],
                             "gr:n_rules": str(len(RULES)),
                             "gr:defuzz": "Mamdani/centroid"})
    dataset = doc.entity("gr:contrast_set",
                         {"prov:type": "gr:HeldOutContrastSet",
                          "gr:name": manifest["dataset"],
                          "gr:n": str(manifest["n"]),
                          "gr:prereg_ratified": manifest["prereg_ratified"]})
    run = doc.activity("gr:contrast_run", when, when,
                       {"prov:type": "gr:HeldOutEvaluation",
                        "gr:gate": str(manifest["gate"]),
                        "gr:n": str(manifest["n"]),
                        "gr:n_gate_pass": str(manifest["n_gate_pass"])})
    doc.wasAssociatedWith(run, agent)
    doc.used(run, dataset)
    doc.used(run, instrument)

    for short in ["detector"] + [SIGNAL_MAP[v][0] for v in SIGNAL_MAP]:
        repo = MODEL_REGISTRY[short]["repo"]
        e_model = doc.entity("hf:" + repo,
                             {"prov:type": "gr:PretrainedModel",
                              "gr:short_name": short,
                              "gr:commit_hash": MODEL_REGISTRY[short]["revision"]})
        doc.used(run, e_model)

    for fname, ptype in [("contrast_scored.csv", "gr:ScoredContrastSet"),
                         ("face_validity_stats.json", "gr:FaceValidityStats")]:
        fpath = RUN_DIR / fname
        if not fpath.exists():
            continue
        e = doc.entity("gr:" + fname.replace(".", "_"),
                       {"prov:type": ptype, "gr:filename": fname,
                        "gr:sha256": sha256_file(fpath)})
        doc.wasGeneratedBy(e, run)
        doc.wasDerivedFrom(e, dataset)
        doc.wasDerivedFrom(e, instrument)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.serialize(str(OUT_DIR / "contrast_run.ttl"), format="rdf", rdf_format="ttl")
    doc.serialize(str(OUT_DIR / "contrast_run.json"), format="json")
    print(f"wrote {OUT_DIR / 'contrast_run.ttl'}")
    print(f"wrote {OUT_DIR / 'contrast_run.json'}")


if __name__ == "__main__":
    main()