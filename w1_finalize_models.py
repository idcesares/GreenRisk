# ===========================================================================
# GreenRisk W1 Finalization — Part 1: Multi-Model Smoke Test
# ===========================================================================
#
# WHAT THIS DOES:
#   Loads ALL FIVE ClimateBERT models and runs each on a single test paragraph,
#   printing the raw output so you can verify each model works and understand
#   what its output looks like.
#
# WHY THIS MATTERS:
#   The smoke_test.py you already ran only tested the climate-detector model.
#   Before building the fuzzy layer in W2, you need to confirm three things
#   for each of the four scoring dimensions:
#     1. The model loads without errors using the pinned commit hash.
#     2. You understand what the output labels are (they differ per model).
#     3. The output makes intuitive sense on a test paragraph.
#
# HOW TO RUN:
#   uv run python w1_finalize_models.py
#
# CONCEPT — id2label:
#   Each classification model has a small dictionary called id2label that
#   maps integer IDs to human-readable label names. For the detector it's
#   {0: "no", 1: "yes"}. For other models the labels differ. We print
#   these so you know what each probability refers to. This is NOT something
#   you need to memorize — the code reads it from the model config. But you
#   DO need to understand it to write the fuzzy layer mappings in W2.
# ===========================================================================

import torch
from models import load  # your models.py from the walkthrough

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
    print("GreenRisk W1 — Multi-Model Smoke Test")
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

    # === INTERPRETATION GUIDE ===
    # Print a summary that maps each model's output to a risk signal.
    # This is the mapping you'll encode in the fuzzy layer in W2.
    print("=" * 70)
    print("INTERPRETATION FOR FUZZY LAYER (keep this for W2)")
    print("=" * 70)

    print("""
    DETECTOR:
      Output: probability of "yes" (climate-related).
      Usage:  Gate filter. If P(yes) < threshold (e.g. 0.5), skip paragraph.

    SPECIFICITY:
      Output: depends on labels — likely "specific" vs "not specific" or 0/1.
      Risk mapping: LOW specificity → HIGHER greenwashing risk.
      For fuzzy input: use P(not_specific) or 1 - P(specific).

    COMMITMENT:
      Output: depends on labels — likely "commitment" vs "no commitment".
      Risk mapping: ABSENT commitment → HIGHER greenwashing risk.
      For fuzzy input: use P(no_commitment) or 1 - P(commitment).

    SENTIMENT:
      Output: likely three classes: "opportunity", "neutral", "risk".
      Risk mapping: PURE opportunity framing → HIGHER greenwashing risk.
      For fuzzy input: use P(opportunity) directly, or P(opportunity) - P(risk)
      to capture the asymmetry.

    NETZERO:
      Output: depends on labels — likely "reduction" / "netzero" related.
      Risk mapping: net-zero pledge alone is neutral. Net-zero + low specificity
      + low commitment = CLASSIC greenwashing signature. This dimension
      acts as a MODIFIER in the rule base, not a standalone axis.
    """)

    print("NOTE: After you run this, record the EXACT label names each model")
    print("returns in its id2label field. You'll need them in W2 to wire the")
    print("fuzzy layer correctly. Don't guess — read them from the output above.")