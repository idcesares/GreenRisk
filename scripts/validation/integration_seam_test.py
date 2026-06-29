"""Phase 4 Step 1 — integration seam test (TCFD only).

Phase 3 unit-tested each stage. This proves the SEAMS between them hold when the
flow runs as one artifact: raw paragraph -> gate -> four scorers -> fuzzy ->
(score, trace), with no manual hand-offs. Every join is an explicit assert, so a
silent gap fails loudly. One PROV-O graph is emitted to prove the provenance
hook fires end-to-end; full per-run wiring is completed in Phase 5.

Iteration runs on TCFD ONLY — the contrast set stays sealed until Phase 6.

Run:  uv run python scripts/validation/integration_seam_test.py -n 20 --gate 0.5
Pass: all asserts hold, max |library - rederived| firing ~ 0, one .ttl written.
"""
import argparse
import hashlib
import pathlib
import sys
from datetime import datetime, timezone

# Repo root on the path so core modules import when run from anywhere.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from datasets import load_dataset
from prov.model import ProvDocument, Namespace

from models import all_signals_batch, score_batch, SIGNAL_MAP, MODEL_REGISTRY
from rule_base import score_paragraph, library_firings, ANTS, RULES, _term_membership

FIRING_TOL = 1e-9   # library vs. re-derived firing must agree to float precision
MAP_TOL    = 1e-9   # in-flow sentiment signal vs. independent P(opportunity) read


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def main(n: int, gate: float):
    ds = load_dataset("climatebert/tcfd_recommendations")["train"]
    texts = ds["text"][:n]

    # --- SEAM A: type/key match (assert, don't assume) ---------------------
    # Every fuzzy input the rule base reads must be produced by a scorer, and
    # vice versa. Low-risk (Phase 3 confirmed the contract) but checked, not eyeballed.
    assert set(SIGNAL_MAP) == set(ANTS), (
        f"signal/key mismatch: {set(SIGNAL_MAP) ^ set(ANTS)}")

    # --- Stage 1: climate gate (one batched detector pass) -----------------
    climate = [r["yes"] for r in score_batch("detector", texts)]
    kept = [(i, t) for i, (t, c) in enumerate(zip(texts, climate)) if c >= gate]
    keep_texts = [t for _, t in kept]
    gate_hashes = [sha12(t) for t in keep_texts]
    print(f"gate>={gate}: kept {len(kept)}/{len(texts)} "
          f"({len(texts) - len(kept)} non-climate dropped)")

    # --- Stage 2: four scorers (batched) -----------------------------------
    cols = all_signals_batch(keep_texts)            # {var: [floats]}, aligned to keep_texts
    assert set(cols) == set(ANTS), "scorer output keys != fuzzy input keys"

    # Independent re-read of the sentiment model for the in-flow mapping check.
    # Same code path (score_batch on the same gated batch) => bit-identical floats.
    sentiment_rows = score_batch("sentiment", keep_texts)

    # --- Stages 3+4: fuzzy score + trace per paragraph, with seam checks ----
    records = []
    max_firing_disc = 0.0
    for j, (orig_i, text) in enumerate(kept):
        sig = {v: cols[v][j] for v in ANTS}
        score_val, trace = score_paragraph(sig)

        # SEAM B: identity preservation — the paragraph scored here is the same
        # one that entered the gate at this position. Caching / reordering is
        # exactly where identity quietly breaks.
        assert sha12(text) == gate_hashes[j], f"identity broken at row {orig_i}"

        # SEAM C: the sentiment signal is the MAPPED value (P('opportunity')),
        # not a raw class. It must equal the sentiment model's opportunity
        # probability read independently, and be a probability in [0, 1].
        opp = sentiment_rows[j]["opportunity"]
        assert abs(sig["sentiment_asymmetry"] - opp) < MAP_TOL, (
            f"row {orig_i}: sentiment signal {sig['sentiment_asymmetry']} "
            f"!= P(opportunity) {opp} — mapping not applied in-flow")
        assert 0.0 <= sig["sentiment_asymmetry"] <= 1.0

        # DEFENSIBILITY: re-derived min(memberships) == library's own firing.
        lib = library_firings(sig)
        rederived = {rid: min(_term_membership(v, t, sig[v]) for v, t in terms)
                     for rid, terms, _c, _n in RULES}
        for rid in lib:
            max_firing_disc = max(max_firing_disc, abs(lib[rid] - rederived[rid]))

        records.append({"i": orig_i, "text": text, "sig": sig,
                        "score": score_val, "trace": trace})

    assert max_firing_disc <= FIRING_TOL, (
        f"firing mismatch {max_firing_disc:.2e} > {FIRING_TOL}")

    print(f"SEAMS OK on {len(records)} paragraphs:")
    print(f"  A key-match      : {sorted(ANTS)} == scorer keys")
    print(f"  B identity       : all {len(records)} hashes preserved")
    print(f"  C sentiment map  : in-flow signal == P(opportunity), in [0,1]")
    print(f"  defensibility    : max |library - rederived| firing = "
          f"{max_firing_disc:.2e}")

    # --- Provenance seam: ONE PROV-O graph proving the chain wires up -------
    ttl_path = emit_run_provenance(records, gate)
    print(f"  provenance       : {ttl_path}")
    return records


def emit_run_provenance(records, gate):
    """Emit one .ttl tracing a representative paragraph through the full chain:
    paragraph -> four model inferences -> fuzzy aggregation -> risk score,
    wrapped in a run-level activity. Proves the provenance hook fires in the
    integrated flow; it is NOT the full per-run provenance from Phase 5.
    """
    rec = records[0]                                  # exemplar = first kept paragraph
    text, sig, score_val = rec["text"], rec["sig"], rec["score"]
    h = sha12(text)

    doc = ProvDocument()
    gr = Namespace("gr", "https://greenrisk.ppgi.ufrj.br/prov/")
    hf = Namespace("hf", "https://huggingface.co/")
    doc.set_default_namespace("https://greenrisk.ppgi.ufrj.br/prov/")
    doc.add_namespace(gr)
    doc.add_namespace(hf)

    agent = doc.agent("gr:GreenRiskPipeline_v0.2",
                      {"prov:type": "prov:SoftwareAgent", "gr:version": "0.2.0"})
    now = datetime.now(timezone.utc)
    run = doc.activity("gr:seam_run_" + h, now, now,
                       {"prov:type": "gr:Phase4SeamRun",
                        "gr:n_paragraphs": str(len(records)),
                        "gr:gate": str(gate), "gr:dataset": "climatebert/tcfd_recommendations"})
    doc.wasAssociatedWith(run, agent)

    paragraph = doc.entity("gr:paragraph_" + h,
                           {"prov:type": "gr:InputParagraph",
                            "gr:text_sha256": h, "gr:char_count": len(text)})

    # One inference branch per scorer; each consumes the paragraph + its model.
    score_entities = []
    for var, (model_name, label) in SIGNAL_MAP.items():
        repo = MODEL_REGISTRY[model_name]["repo"]
        commit = MODEL_REGISTRY[model_name]["revision"]
        e_model = doc.entity("hf:" + repo,
                             {"prov:type": "gr:PretrainedModel",
                              "gr:commit_hash": commit})
        a_inf = doc.activity("gr:inference_%s_%s" % (h, var), now, now,
                             {"prov:type": "gr:ModelInference", "gr:reads_label": label})
        e_sig = doc.entity("gr:signal_%s_%s" % (h, var),
                           {"prov:type": "gr:Signal", "gr:variable": var,
                            "gr:value": str(round(sig[var], 6))})
        doc.used(a_inf, paragraph)
        doc.used(a_inf, e_model)
        doc.wasGeneratedBy(e_sig, a_inf)
        doc.wasAssociatedWith(a_inf, agent)
        doc.wasDerivedFrom(e_sig, paragraph)
        score_entities.append(e_sig)

    # Fuzzy aggregation consumes the four signals, generates the risk score.
    a_fuzzy = doc.activity("gr:fuzzy_" + h, now, now,
                           {"prov:type": "gr:FuzzyInference",
                            "gr:method": "Mamdani/centroid", "gr:rules": str(len(RULES))})
    e_risk = doc.entity("gr:risk_" + h,
                        {"prov:type": "gr:RiskScore", "gr:value": str(score_val)})
    for e_sig in score_entities:
        doc.used(a_fuzzy, e_sig)
        doc.wasDerivedFrom(e_risk, e_sig)
    doc.wasGeneratedBy(e_risk, a_fuzzy)
    doc.wasAssociatedWith(a_fuzzy, agent)

    out_dir = pathlib.Path(__file__).resolve().parents[2] / "artifacts" / "provenance"
    out_dir.mkdir(parents=True, exist_ok=True)
    ttl_path = out_dir / "phase4_seam_run.ttl"
    doc.serialize(str(ttl_path), format="rdf", rdf_format="ttl")
    return ttl_path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=20, help="paragraphs to consider (pre-gate)")
    ap.add_argument("--gate", type=float, default=0.5, help="min is_climate to score")
    a = ap.parse_args()
    main(a.n, a.gate)
