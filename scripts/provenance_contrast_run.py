"""Run-level PROV-O for the held-out contrast-set evaluation.

Mirrors scripts/provenance_corpus_run.py: binds the held-out results + stats
(by sha256) to the run that produced them + the 5 pinned model commits + the
frozen instrument tag. Reads the run manifest as single source of truth.

Run:  uv run python scripts/provenance_contrast_run.py
"""
import hashlib
import json
import pathlib
from datetime import datetime

from prov.model import Namespace, ProvDocument

from greenrisk.metadata import INSTRUMENT_METHOD, INSTRUMENT_RULE_COUNT

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
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    when = datetime.fromisoformat(manifest["timestamp_utc"])

    doc = ProvDocument()
    gr = Namespace("gr", "https://github.com/idcesares/GreenRisk/prov/")
    hf = Namespace("hf", "https://huggingface.co/")
    doc.set_default_namespace("https://github.com/idcesares/GreenRisk/prov/")
    doc.add_namespace(gr)
    doc.add_namespace(hf)

    version = manifest["software_version"]
    agent = doc.agent(
        f"gr:GreenRiskPipeline_v{version}",
        {"prov:type": "prov:SoftwareAgent", "gr:version": version},
    )
    instrument = doc.entity("gr:instrument_" + manifest["instrument_tag"],
                             {"prov:type": "gr:FuzzyInstrument",
                             "gr:tag": manifest["instrument_tag"],
                             "gr:commit": manifest["instrument_commit"],
                             "gr:n_rules": str(INSTRUMENT_RULE_COUNT),
                             "gr:defuzz": INSTRUMENT_METHOD})
    dataset = doc.entity("gr:contrast_set",
                          {"prov:type": "gr:HeldOutContrastSet",
                           "gr:name": manifest["dataset"],
                          "gr:sha256": manifest["dataset_sha256"],
                          "gr:n": str(manifest["n"]),
                          "gr:protocol_status": manifest["protocol_status"],
                          "gr:expectations_recorded": manifest["expectations_recorded"]})
    run = doc.activity("gr:contrast_run", when, when,
                       {"prov:type": "gr:HeldOutEvaluation",
                        "gr:gate": str(manifest["gate"]),
                        "gr:n": str(manifest["n"]),
                        "gr:n_gate_pass": str(manifest["n_gate_pass"])})
    doc.wasAssociatedWith(run, agent)
    doc.used(run, dataset)
    doc.used(run, instrument)

    for short, commit in manifest["model_revisions"].items():
        repo = manifest["model_repositories"][short]
        e_model = doc.entity("hf:" + repo,
                             {"prov:type": "gr:PretrainedModel",
                              "gr:short_name": short,
                              "gr:commit_hash": commit})
        doc.used(run, e_model)

    for fname, ptype in [("contrast_scored.csv", "gr:ScoredContrastSet"),
                         ("face_validity_stats.json", "gr:FaceValidityStats")]:
        fpath = RUN_DIR / fname
        if not fpath.exists():
            continue
        expected_hash = manifest["outputs"][fname]["sha256"]
        actual_hash = sha256_file(fpath)
        if actual_hash != expected_hash:
            raise ValueError(
                f"artifact integrity failure for {fpath}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
        e = doc.entity("gr:" + fname.replace(".", "_"),
                       {"prov:type": ptype, "gr:filename": fname,
                        "gr:sha256": expected_hash})
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
