"""ClimateBERT model registry. Hashes pinned for reproducibility."""

from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_REGISTRY = {
    "detector": {
        "repo": "climatebert/distilroberta-base-climate-detector",
        "revision": "2c3bc660d45a59e31b35f5d3e365ee4f59fdf76c",
    },
    "specificity": {
        "repo": "climatebert/distilroberta-base-climate-specificity",
        "revision": "4ada96ed4bf5c3a7a711282e41f1ab9b29f0ddea",
    },
    "commitment": {
        "repo": "climatebert/distilroberta-base-climate-commitment",
        "revision": "17337c3292df16a8fe93b1505dfe4122d50a4c91",
    },
    "sentiment": {
        "repo": "climatebert/distilroberta-base-climate-sentiment",
        "revision": "e9f9a94ee4263f5ad5cfc97b8539a497fc88aa7d",
    },
    "netzero": {
        "repo": "climatebert/netzero-reduction",
        "revision": "25cf57e30613a2156fee1fe3f917036df4a5c0d1",
    },
}


def load(name: str):
    """Load a model + tokenizer by short name. Returns (model, tokenizer)."""
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {name}. Known: {list(MODEL_REGISTRY)}")
    spec = MODEL_REGISTRY[name]
    model = AutoModelForSequenceClassification.from_pretrained(
        spec["repo"], revision=spec["revision"]
    )
    tokenizer = AutoTokenizer.from_pretrained(
        spec["repo"], revision=spec["revision"]
    )
    return model, tokenizer