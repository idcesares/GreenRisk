"""Check whether pinned model commits still resolve and report upstream HEADs.

This command is deliberately read-only. Updating a revision would change the
frozen instrument and therefore requires a separately logged ablation.
"""

from __future__ import annotations

import json

from huggingface_hub import HfApi

from greenrisk.metadata import MODEL_REGISTRY


def main() -> None:
    api = HfApi()
    report = {}
    for name, coordinates in MODEL_REGISTRY.items():
        pinned = api.model_info(coordinates["repo"], revision=coordinates["revision"])
        current = api.model_info(coordinates["repo"])
        report[name] = {
            "repo": coordinates["repo"],
            "pinned_revision": coordinates["revision"],
            "pinned_resolves_to": pinned.sha,
            "upstream_head": current.sha,
            "upstream_changed": current.sha != coordinates["revision"],
        }
        if pinned.sha != coordinates["revision"]:
            raise RuntimeError(f"{name}: pinned revision did not resolve exactly")

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
