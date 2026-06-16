"""Look up current commit hashes for all five ClimateBERT models we depend on.
Run this once at project setup. Pin the resulting hashes in models.py."""

from huggingface_hub import HfApi

MODELS = [
    "climatebert/distilroberta-base-climate-detector",
    "climatebert/distilroberta-base-climate-specificity",
    "climatebert/distilroberta-base-climate-commitment",
    "climatebert/distilroberta-base-climate-sentiment",
    "climatebert/netzero-reduction",
]

api = HfApi()
print("Current commit hashes (copy these into models.py):\n")
for repo_id in MODELS:
    info = api.model_info(repo_id)
    print(f'    "{repo_id}": "{info.sha}",')