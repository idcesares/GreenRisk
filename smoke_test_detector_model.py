"""Sanity check: load the climate detector and run it on one paragraph.
Expected outcome: detector says 'yes' with high confidence."""

import torch
from models import load

model, tokenizer = load("detector")
model.eval()  # tells PyTorch we're doing inference, not training

# A clearly climate-related paragraph
paragraph = (
    "We are committed to reducing our Scope 1 and Scope 2 greenhouse gas "
    "emissions by 50% by 2030, relative to a 2019 baseline. This commitment "
    "is aligned with the Science Based Targets initiative and verified annually "
    "by an independent third party."
)

# Tokenize: convert text into the integer IDs the model expects
inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, max_length=512)

# Inference: no gradient computation needed
with torch.no_grad():
    outputs = model(**inputs)

# outputs.logits is a tensor of raw scores; softmax converts to probabilities
probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

print("Label mapping:", model.config.id2label)
print("Probabilities:", probs[0].tolist())