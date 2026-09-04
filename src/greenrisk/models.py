"""GreenRisk ClimateBERT model registry and inference adapters."""

# Use the GPU if a CUDA-enabled torch sees one; otherwise CPU. Auto-detected.

import os

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from .metadata import MODEL_REGISTRY, SIGNAL_MAP

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load(name: str):
    """Load a model + tokenizer by short name. Returns (model, tokenizer)."""
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {name}. Known: {list(MODEL_REGISTRY)}")
    spec = MODEL_REGISTRY[name]
    # These models are public. If a token is present, pass it to the individual
    # requests without invoking huggingface_hub.login() or persisting credentials
    # as an import-time side effect.
    token = os.environ.get("HF_TOKEN") or None
    model = AutoModelForSequenceClassification.from_pretrained(
        spec["repo"], revision=spec["revision"], token=token
    )
    tokenizer = AutoTokenizer.from_pretrained(
        spec["repo"], revision=spec["revision"], token=token
    )
    return model, tokenizer

# ---------------------------------------------------------------------------
# Uniform scoring layer
# ---------------------------------------------------------------------------

# Lazy cache: each model is loaded from disk at most once, then reused.
# Without this, scoring many paragraphs across several models would
# re-instantiate ~330 MB models on every call. The cache keeps it cheap.
_MODELS = {}  # name -> (model, tokenizer)


def _get(name: str):
    """Return a cached (model, tokenizer), loaded + eval + on DEVICE, once."""
    if name not in _MODELS:
        model, tokenizer = load(name)
        model.eval()
        model.to(DEVICE)          # weights live on DEVICE (GPU or CPU) after this
        _MODELS[name] = (model, tokenizer)
    return _MODELS[name]


def clear_model_cache() -> None:
    """Release cached model references, for long-running or memory-bound hosts."""
    _MODELS.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def score(name: str, text: str) -> dict[str, float]:
    """Run one model on one paragraph; return {label: probability}.

    The single generic inference path, reused by every adapter and the
    downstream pipeline. Loads via the cache so repeated calls are cheap.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    model, tokenizer = _get(name)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
    id2label = model.config.id2label
    return {id2label[i]: float(p) for i, p in enumerate(probs.tolist())}


# Fuzzy input variable -> (model short-name, label string to read).
# Single source of truth for the signal-mapping decisions. Change a label
# in one place if a model ever changes its id2label.
def signal(var: str, text: str) -> float:
    """Return the [0, 1] signal for one fuzzy input variable."""
    if var not in SIGNAL_MAP:
        raise KeyError(f"Unknown signal: {var}. Known: {list(SIGNAL_MAP)}")
    name, label = SIGNAL_MAP[var]
    return score(name, text)[label]


def all_signals(text: str) -> dict[str, float]:
    """Return all four fuzzy input signals for a paragraph."""
    return {var: signal(var, text) for var in SIGNAL_MAP}


def is_climate(text: str) -> float:
    """Climate-relevance gate: P('yes') from the detector model."""
    return score("detector", text)["yes"]

def score_batch(name: str, texts: list[str], batch_size: int = 32) -> list[dict[str, float]]:
    """Score many paragraphs through one model in GPU-friendly batches.

    Returns one {label: prob} dict per input text, in order. Batching is where
    the GPU actually parallelizes: each forward pass processes `batch_size`
    paragraphs at once. `padding=True` makes a batch's sequences equal length;
    the attention mask ensures padded tokens don't affect the result.
    """
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {name}. Known: {list(MODEL_REGISTRY)}")
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    if not isinstance(texts, list) or any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("texts must be a list of non-empty strings")
    if not texts:
        return []

    model, tokenizer = _get(name)
    id2label = model.config.id2label
    results: list[dict[str, float]] = []

    for start in range(0, len(texts), batch_size):
        chunk = texts[start:start + batch_size]
        inputs = tokenizer(
            chunk, return_tensors="pt",
            truncation=True, max_length=512, padding=True,
        )
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
        with torch.inference_mode():                       # like no_grad, a touch faster
            logits = model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=-1).cpu().tolist()
        results.extend({id2label[i]: float(p) for i, p in enumerate(row)} for row in probs)
    return results


def all_signals_batch(texts: list[str], batch_size: int = 32) -> dict[str, list[float]]:
    """Return {var: [values...]} for all four fuzzy signals over many paragraphs."""
    out = {}
    for var, (name, label) in SIGNAL_MAP.items():
        rows = score_batch(name, texts, batch_size=batch_size)
        out[var] = [r[label] for r in rows]
    return out
