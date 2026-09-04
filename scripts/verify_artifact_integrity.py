"""Verify committed result files against manifests and PROV-O records."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from greenrisk.metadata import INSTRUMENT_COMMIT, INSTRUMENT_TAG, MODEL_REGISTRY

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int:
    with path.open(encoding="utf-8", newline="") as stream:
        return sum(1 for _ in csv.reader(stream)) - 1


def verify_run(run_name: str, provenance_stem: str) -> None:
    run_dir = ROOT / "artifacts" / run_name
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "2.0"
    assert manifest["instrument_tag"] == INSTRUMENT_TAG
    assert manifest["instrument_commit"] == INSTRUMENT_COMMIT
    assert manifest["model_repositories"] == {
        name: value["repo"] for name, value in MODEL_REGISTRY.items()
    }
    assert manifest["model_revisions"] == {
        name: value["revision"] for name, value in MODEL_REGISTRY.items()
    }

    if "dataset_sha256" in manifest:
        dataset_path = ROOT / manifest["dataset"]
        actual = sha256_file(dataset_path)
        assert actual == manifest["dataset_sha256"], (
            f"{dataset_path}: expected {manifest['dataset_sha256']}, got {actual}"
        )

    provenance_paths = [
        ROOT / "artifacts" / "provenance" / f"{provenance_stem}.ttl",
        ROOT / "artifacts" / "provenance" / f"{provenance_stem}.json",
    ]
    provenance_text = [path.read_text(encoding="utf-8") for path in provenance_paths]

    for filename, record in manifest["outputs"].items():
        output_path = run_dir / filename
        actual = sha256_file(output_path)
        assert actual == record["sha256"], (
            f"{output_path}: expected {record['sha256']}, got {actual}"
        )
        if "rows" in record:
            actual_rows = row_count(output_path)
            assert actual_rows == record["rows"], (
                f"{output_path}: expected {record['rows']} rows, got {actual_rows}"
            )
        for provenance_path, text in zip(provenance_paths, provenance_text, strict=True):
            assert actual in text, f"{provenance_path} does not bind {filename} to {actual}"

    print(f"verified {run_name}: {len(manifest['outputs'])} output(s)")


def main() -> None:
    verify_run("corpus_run", "corpus_run")
    verify_run("contrast_run", "contrast_run")
    print("artifact manifests and provenance records are internally consistent")


if __name__ == "__main__":
    main()
