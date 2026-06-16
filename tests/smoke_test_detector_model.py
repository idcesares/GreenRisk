""" This is a Sanity check: load the climate detector and run it on one paragraph.
Expected outcome: detector says 'yes' with high confidence."""

import pathlib
import sys

# Repo root on the path so core modules import when run from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import torch
from models import load

model, tokenizer = load("detector")
model.eval()

paragraph = (
    "We are committed to reducing our Scope 1 and Scope 2 greenhouse gas "
    "emissions by 50% by 2030, relative to a 2019 baseline. This commitment "
    "is aligned with the Science Based Targets initiative and verified annually "
    "by an independent third party."
)

inputs = tokenizer(paragraph, return_tensors="pt", truncation=True, max_length=512)

with torch.no_grad():
    outputs = model(**inputs)

probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

print("Label mapping:", model.config.id2label)
print("Probabilities:", probs[0].tolist())