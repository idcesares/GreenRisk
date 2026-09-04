"""Immutable identifiers used by the locked GreenRisk research instrument."""

INSTRUMENT_TAG = "rulebase-locked-v1"
INSTRUMENT_COMMIT = "a40288ac8eacfe0de1987884ec03bea9457972c5"
INSTRUMENT_RULE_COUNT = 17
INSTRUMENT_METHOD = "Mamdani/centroid"

TCFD_DATASET_ID = "climatebert/tcfd_recommendations"
TCFD_DATASET_REVISION = "aee5c98f0bf7835bfb08308ffc7c17216657976b"
TCFD_TRAIN_SHA256 = "1f16bb38a021aeafad6935eb5aa3f072c2e51b3dcf01eaee88a32ef537029f1f"

# Frozen upstream model coordinates. Keeping them in this dependency-free
# module lets manifests and integrity tests inspect the instrument without
# importing PyTorch or downloading model weights.
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

# Fuzzy input -> (model short name, probability label). These mappings are part
# of the locked instrument and must not change without a logged ablation.
SIGNAL_MAP = {
    "specificity": ("specificity", "spec"),
    "commitment": ("commitment", "yes"),
    "sentiment_asymmetry": ("sentiment", "opportunity"),
    "netzero": ("netzero", "net-zero"),
}
