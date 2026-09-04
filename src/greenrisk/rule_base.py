"""Mamdani rule base for greenwashing risk scoring.

The rules are defined once, as data (RULES), and consumed twice:
  - build_control_system() compiles them into scikit-fuzzy ctrl.Rule objects
    for defuzzification (centroid).
  - score_paragraph() recomputes each rule's firing strength directly from the
    locked membership functions, independent of the library's internal state,
    so every score ships with an auditable activation trace.

Assumes paragraphs are already climate-gated upstream; this layer only scores
the four construct-aligned signals.
"""
import functools
import math
import operator
from collections.abc import Mapping

import skfuzzy as fuzz
from skfuzzy import control as ctrl

from .linguistic_variables import (
    commitment,
    netzero,
    risk,
    sentiment_asymmetry,
    specificity,
)

ANTS = {
    "specificity": specificity,
    "commitment": commitment,
    "sentiment_asymmetry": sentiment_asymmetry,
    "netzero": netzero,
}
RISK = risk

# (id, [(variable, term), ...], consequent_term, rationale)
RULES = [
    # Tier 1 — Spine: specificity x commitment. Risk = vagueness x CLAIM-strength.
    # Non-increasing in specificity; non-DECREASING in commitment when vague
    # (a loud pledge with no substance is the greenwashing signature, so
    # commitment escalates risk for vague text).
    ("S1", [("specificity", "Low"),    ("commitment", "Low")],    "Moderate", "vague, no claim -> disclosure not greenwashing"),
    ("S2", [("specificity", "Low"),    ("commitment", "Medium")], "Elevated", "some commitment, still vague"),
    ("S3", [("specificity", "Low"),    ("commitment", "High")],   "High",     "loud pledge, no substance -> greenwashing signature"),
    ("S4", [("specificity", "Medium"), ("commitment", "Low")],    "Moderate", "partially specific, no claim"),
    ("S5", [("specificity", "Medium"), ("commitment", "Medium")], "Moderate", "genuinely middling (rarely fires)"),
    ("S6", [("specificity", "Medium"), ("commitment", "High")],   "Elevated", "committed, partially specific"),
    ("S7", [("specificity", "High"),   ("commitment", "Low")],    "Low",      "specific factual disclosure, no claim"),
    ("S8", [("specificity", "High"),   ("commitment", "Medium")], "Low",      "specific, some commitment"),
    ("S9", [("specificity", "High"),   ("commitment", "High")],   "Low",      "rigorous disclosure"),
    # Tier 2 — Net-zero amplifiers (conditional on vagueness; exonerate when specific)
    ("N1", [("netzero", "High"), ("specificity", "Low")],  "High",     "net-zero pledge, no detail"),
    ("N2", [("netzero", "High"), ("commitment", "Low")],   "Elevated", "target asserted, no commitment"),
    ("N3", [("netzero", "High"), ("specificity", "High")], "Low",      "net-zero claim WITH specifics"),
    # Tier 3 — Opportunity-framing amplifiers (only escalate when High)
    ("O1", [("sentiment_asymmetry", "High"), ("specificity", "Low")], "Elevated", "opportunity hype, vague"),
    ("O2", [("sentiment_asymmetry", "High"), ("commitment", "Low")],  "Elevated", "upbeat, no commitment"),
    ("O3", [("sentiment_asymmetry", "High"), ("specificity", "High"), ("commitment", "High")], "Low", "earned optimism"),
    # Tier 4 — Named signatures (trace legibility for case studies)
    ("G1", [("specificity", "Low"), ("commitment", "Low"), ("netzero", "High")], "High", "classic greenwashing signature"),
    ("G2", [("specificity", "Low"), ("sentiment_asymmetry", "High"), ("netzero", "High")], "High", "vague aspirational pledge"),
]

def build_control_system():
    rules = []
    for rid, terms, consequent, _note in RULES:
        antecedent = functools.reduce(operator.and_, [ANTS[v][t] for v, t in terms])
        rules.append(ctrl.Rule(antecedent, RISK[consequent], label=rid))
    return ctrl.ControlSystem(rules)


_SYSTEM = build_control_system()

def _term_membership(variable, term, x):
    a = ANTS[variable]
    return float(fuzz.interp_membership(a.universe, a[term].mf, x))

def _validated_signals(signals: Mapping[str, float]) -> dict[str, float]:
    """Validate and normalize a complete GreenRisk signal mapping.

    scikit-fuzzy clips out-of-universe inputs by default. Silent clipping is
    unsuitable for an auditable scoring API, so values outside [0, 1], missing
    signals, unexpected signals, booleans, and non-finite numbers are rejected
    before they reach the control system.
    """
    if not isinstance(signals, Mapping):
        raise TypeError("signals must be a mapping of signal names to probabilities")

    expected = set(ANTS)
    received = set(signals)
    missing = sorted(expected - received)
    unexpected = sorted(received - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing={missing}")
        if unexpected:
            details.append(f"unexpected={unexpected}")
        raise ValueError("invalid signal keys: " + ", ".join(details))

    validated: dict[str, float] = {}
    for name in ANTS:
        value = signals[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a finite number in [0, 1]")
        value = float(value)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be a finite number in [0, 1], got {value!r}")
        validated[name] = value
    return validated


def score_paragraph(signals: Mapping[str, float]):
    """signals: {input_name: value in [0, 1]} for all four inputs.

    Returns (risk_score, trace), where trace is a list of fired rules sorted by
    firing strength, each {'rule', 'fire', 'consequent', 'note'}.
    """
    signals = _validated_signals(signals)

    # Fresh simulation per call avoids scikit-fuzzy's cross-run state caching.
    sim = ctrl.ControlSystemSimulation(_SYSTEM)
    for name, value in signals.items():
        sim.input[name] = value
    sim.compute()

    trace = []
    for rid, terms, consequent, note in RULES:
        firing = min(_term_membership(v, t, signals[v]) for v, t in terms)  # AND = min
        if firing > 1e-6:
            trace.append({"rule": rid, "fire": firing,
                          "consequent": consequent, "note": note})
    trace.sort(key=lambda d: d["fire"], reverse=True)
    return round(float(sim.output["risk"]), 2), trace

def library_firings(signals: Mapping[str, float]):
    """Read-only audit hook: each rule's firing strength as computed by
    scikit-fuzzy's OWN engine (not our re-derivation).

    score_paragraph's trace re-derives firing independently via min(memberships).
    This returns the library's internal value for the SAME inputs, so a test can
    assert the two agree — the Phase-3 defensibility property, now checkable
    through the full integrated path. Does not alter scoring.

    Returns {rule_id: firing in [0, 1]} for every rule (0.0 if it did not fire).
    """
    signals = _validated_signals(signals)
    sim = ctrl.ControlSystemSimulation(_SYSTEM)
    for name, value in signals.items():
        sim.input[name] = value
    sim.compute()
    return {rule.label: float(rule.aggregate_firing[sim]) for rule in _SYSTEM.rules}


def format_trace(signals, risk_score, trace):
    sig = "  ".join(f"{k}={signals[k]:.3f}" for k in ANTS)
    lines = [f"inputs: {sig}", f"RISK = {risk_score}", "fired rules:"]
    for t in trace:
        lines.append(f"  {t['rule']:>3}  fire={t['fire']:.3f}  -> "
                     f"{t['consequent']:<8}  ({t['note']})")
    return "\n".join(lines)
