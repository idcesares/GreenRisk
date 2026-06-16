# Smoke test script to verify that all models can be loaded and run on a sample paragraph.
# It also prints the label mappings and probabilities for each model

import pathlib
import sys

# Repo root on the path so core modules import when run from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch
from models import load

# A paragraph designed to trigger interesting signals across all dimensions:
# - clearly climate-related (detector → yes)
# - somewhat vague on specifics (specificity → could go either way)
# - has commitment language (commitment → yes)
# - opportunity-framing (sentiment → opportunity)
# - contains a net-zero pledge (netzero → yes)

TEST_PARAGRAPH = (
    "We are committed to achieving net-zero greenhouse gas emissions across "
    "our entire value chain by 2050. Our sustainability strategy places "
    "climate action at the core of our business, creating long-term value "
    "for shareholders while contributing to a more sustainable future. We "
    "continue to explore innovative solutions to reduce our environmental "
    "footprint and seize the opportunities presented by the transition to "
    "a low-carbon economy."
)

MODEL_NAMES = ["detector", "specificity", "commitment", "sentiment", "netzero"]


def run_single(model_name: str, paragraph: str) -> dict:
    """Load a model, run inference on one paragraph, return structured results."""
    model, tokenizer = load(model_name)
    model.eval()

    inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, max_length=512)

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    id2label = model.config.id2label

    # Build a label→probability mapping
    label_probs = {}
    for idx, prob in enumerate(probs[0].tolist()):
        label = id2label.get(idx, f"class_{idx}")
        label_probs[label] = round(prob, 4)

    return {
        "model": model_name,
        "id2label": id2label,
        "probabilities": label_probs,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("GreenRisk Multi-Model Smoke Test")
    print("=" * 70)
    print(f"\nTest paragraph ({len(TEST_PARAGRAPH.split())} words):")
    print(f"  '{TEST_PARAGRAPH[:120]}...'\n")

    results = {}
    for name in MODEL_NAMES:
        print(f"Loading {name}...")
        result = run_single(name, TEST_PARAGRAPH)
        results[name] = result
        print(f"  Labels:       {result['id2label']}")
        print(f"  Probabilities: {result['probabilities']}")
        print()