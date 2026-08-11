"""Property test for the locked rule base — the claims docs/paper make about it.

Unlike the smoke tests, this loads no ClimateBERT model: it exercises the fuzzy
layer alone, so it runs in seconds on CPU. Four properties, each corresponding
to a statement made in docs/architecture.md or docs/decisions.md:

  1. INTEGRITY      17 rules, unique ids, spine tiles the full 3x3 plane, every
                    antecedent names a real variable and term.
  2. TERM ORDER     the spine's assigned risk TERM is monotone non-increasing in
                    specificity and non-decreasing in commitment (DL-001). Exact,
                    checked on the rule table itself.
  3. SPINE SURFACE  after defuzzification, with the amplifier tiers inactive, the
                    same ordering survives up to sub-point centroid artifacts at
                    term transitions, and never crosses a risk band.
  4. AMPLIFIERS     with the amplifier tiers active the ordering has bounded,
                    intentional exceptions (N2/O2 withdraw as commitment rises).
                    The bound is asserted so a future change cannot widen it
                    silently.

Also re-checks the defensibility property end-to-end within the fuzzy layer: the
trace's independently re-derived firing strengths equal scikit-fuzzy's own.

Run:  uv run python tests/property_test_rule_base.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from rule_base import RULES, ANTS, RISK, score_paragraph, library_firings  # noqa: E402

TOL = 1e-6
# Small movement from centroid aggregation where two input terms overlap.
# Observed max inside the spine is 1.77 risk points (specificity 0.35, commitment
# crossing the Low/Medium boundary); anything beyond 2.5 is a real change.
SPINE_TOL = 2.5
# The amplifier tiers deliberately break monotonicity where a rule conditioned on
# LOW commitment (N2, O2) withdraws as commitment rises. Observed max is 6.35.
AMPLIFIER_BOUND = 8.0

BANDS = ((22.5, "Low"), (50.0, "Moderate"), (77.5, "Elevated"), (101.0, "High"))
TERM_ORDER = {"Low": 0, "Moderate": 1, "Elevated": 2, "High": 3}
GRID = [round(0.05 * i, 2) for i in range(21)]
# The Low term's support ends at 0.4; 0.39 is where centroid artifacts are largest.
LOW_SPEC = [0.0, 0.1, 0.2, 0.3, 0.35, 0.39]

_cache = {}


def band(risk_score):
    return next(name for edge, name in BANDS if risk_score < edge)


def risk_at(spec, comm, opp=0.0, nz=0.0):
    key = (spec, comm, opp, nz)
    if key not in _cache:
        _cache[key] = score_paragraph({
            "specificity": spec, "commitment": comm,
            "sentiment_asymmetry": opp, "netzero": nz,
        })[0]
    return _cache[key]


def check_integrity():
    ids = [rid for rid, _, _, _ in RULES]
    assert len(RULES) == 17, f"expected 17 rules, found {len(RULES)}"
    assert len(set(ids)) == len(ids), "duplicate rule ids"
    for rid, terms, consequent, _note in RULES:
        assert consequent in TERM_ORDER, f"{rid}: unknown consequent {consequent}"
        RISK[consequent]  # raises if the output term does not exist
        for var, term in terms:
            assert var in ANTS, f"{rid}: unknown variable {var}"
            ANTS[var][term]  # raises if the input term does not exist

    spine = {tuple(t[1] for t in terms) for rid, terms, _, _ in RULES if rid.startswith("S")}
    expected = {(s, c) for s in ("Low", "Medium", "High") for c in ("Low", "Medium", "High")}
    assert spine == expected, f"spine does not tile the 3x3 plane: {expected - spine}"
    print(f"  integrity: 17 rules, unique ids, spine tiles 3x3        OK")


def check_term_order():
    spine = {tuple(t[1] for t in terms): consequent
             for rid, terms, consequent, _ in RULES if rid.startswith("S")}
    levels = ("Low", "Medium", "High")
    for comm in levels:  # non-increasing in specificity
        seq = [TERM_ORDER[spine[(s, comm)]] for s in levels]
        assert seq == sorted(seq, reverse=True), f"commitment={comm}: {seq}"
    seq = [TERM_ORDER[spine[("Low", c)]] for c in levels]  # non-decreasing in commitment when vague
    assert seq == sorted(seq), f"specificity=Low: {seq}"
    print("  term order: DL-001 ordering holds exactly on the rule table  OK")


def _sweep(fixed_opp, fixed_nz):
    """Return (worst rise in specificity, worst fall in commitment, band crossings)."""
    worst_spec = worst_comm = 0.0
    crossings = 0
    for comm in GRID:
        prev = None
        for spec in GRID:
            r = risk_at(spec, comm, fixed_opp, fixed_nz)
            if prev is not None and r > prev + TOL:
                worst_spec = max(worst_spec, r - prev)
                crossings += band(r) != band(prev)
            prev = r
    for spec in LOW_SPEC:
        prev = None
        for comm in GRID:
            r = risk_at(spec, comm, fixed_opp, fixed_nz)
            if prev is not None and r < prev - TOL:
                worst_comm = max(worst_comm, prev - r)
                crossings += band(r) != band(prev)
            prev = r
    return worst_spec, worst_comm, crossings


def check_spine_surface():
    rise, fall, crossings = _sweep(0.0, 0.0)
    assert rise <= SPINE_TOL, f"risk rises {rise:.2f} with specificity inside the spine"
    assert fall <= SPINE_TOL, f"risk falls {fall:.2f} with commitment inside the spine"
    assert crossings == 0, f"{crossings} band crossings inside the spine"
    print(f"  spine surface: max deviation {max(rise, fall):.2f} pts, 0 band crossings  OK")


def check_amplifier_bound():
    worst = 0.0
    for opp in (0.0, 0.7, 1.0):
        for nz in (0.0, 0.7, 1.0):
            if opp == 0.0 and nz == 0.0:
                continue
            rise, fall, _ = _sweep(opp, nz)
            worst = max(worst, rise, fall)
    assert worst <= AMPLIFIER_BOUND, (
        f"amplifier-tier non-monotonicity is {worst:.2f} pts, above the documented "
        f"bound of {AMPLIFIER_BOUND}")
    print(f"  amplifiers: exceptions bounded at {worst:.2f} pts (limit {AMPLIFIER_BOUND})  OK")


def check_trace_matches_library():
    worst = 0.0
    for spec, comm, opp, nz in [
        (0.05, 0.05, 0.05, 0.95), (0.9, 0.9, 0.1, 0.1), (0.3, 0.7, 0.8, 0.2),
        (0.5, 0.5, 0.5, 0.5), (0.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 0.0),
    ]:
        signals = {"specificity": spec, "commitment": comm,
                   "sentiment_asymmetry": opp, "netzero": nz}
        rederived = {t["rule"]: t["fire"] for t in score_paragraph(signals)[1]}
        for rule_id, lib_fire in library_firings(signals).items():
            worst = max(worst, abs(lib_fire - rederived.get(rule_id, 0.0)))
    assert worst < 1e-3, f"trace disagrees with scikit-fuzzy by {worst}"
    print(f"  defensibility: max |library - re-derived| = {worst:.1e}         OK")


def main():
    print("Locked rule base — property test (rulebase-locked-v1)")
    check_integrity()
    check_term_order()
    check_spine_surface()
    check_amplifier_bound()
    check_trace_matches_library()
    print(f"All properties hold ({len(_cache)} grid points evaluated).")


if __name__ == "__main__":
    main()
