"""Command-line interfaces for signal-level and raw-text GreenRisk scoring."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import __version__
from .metadata import INSTRUMENT_COMMIT, INSTRUMENT_TAG
from .rule_base import ANTS, format_trace, score_paragraph


def probability(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("expected a probability in [0, 1]")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="greenrisk",
        description="Score climate disclosures with the locked GreenRisk instrument.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    signals = subparsers.add_parser(
        "score-signals", help="score four already-computed signal probabilities"
    )
    signals.add_argument("--specificity", required=True, type=probability)
    signals.add_argument("--commitment", required=True, type=probability)
    signals.add_argument(
        "--sentiment-asymmetry",
        dest="sentiment_asymmetry",
        required=True,
        type=probability,
    )
    signals.add_argument("--netzero", required=True, type=probability)
    signals.add_argument("--json", action="store_true", help="emit structured JSON")

    text = subparsers.add_parser(
        "score-text", help="run the climate gate, four pinned models, and fuzzy scorer"
    )
    source = text.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="paragraph text to score")
    source.add_argument("--file", type=Path, help="UTF-8 text file to score")
    text.add_argument("--gate", default=0.5, type=probability)
    text.add_argument(
        "--force",
        action="store_true",
        help="score text below the climate-relevance gate and mark it as forced",
    )
    text.add_argument("--json", action="store_true", help="emit structured JSON")
    text.add_argument(
        "--provenance",
        type=Path,
        help="write per-score W3C PROV-O as .ttl or .json (scored text only)",
    )
    return parser


def _score_signals(args: argparse.Namespace) -> dict:
    signals = {name: getattr(args, name) for name in ANTS}
    risk, trace = score_paragraph(signals)
    return {
        "schema_version": "1.0",
        "software_version": __version__,
        "instrument": {"tag": INSTRUMENT_TAG, "commit": INSTRUMENT_COMMIT},
        "mode": "signals",
        "status": "scored",
        "signals": signals,
        "risk": risk,
        "trace": trace,
    }


def _read_text(args: argparse.Namespace) -> str:
    value = args.text if args.text is not None else args.file.read_text(encoding="utf-8")
    if not value.strip():
        raise ValueError("input text must not be empty")
    return value


def _score_text(args: argparse.Namespace) -> dict:
    from .models import all_signals, is_climate

    text = _read_text(args)
    climate_probability = is_climate(text)
    passed = climate_probability >= args.gate
    payload = {
        "schema_version": "1.0",
        "software_version": __version__,
        "instrument": {"tag": INSTRUMENT_TAG, "commit": INSTRUMENT_COMMIT},
        "mode": "text",
        "input": {
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "char_count": len(text),
        },
        "gate": {
            "probability": climate_probability,
            "threshold": args.gate,
            "passed": passed,
            "forced": bool(args.force and not passed),
        },
    }
    if not passed and not args.force:
        payload.update({"status": "not_scored", "signals": None, "risk": None, "trace": []})
        return payload

    signals = all_signals(text)
    risk, trace = score_paragraph(signals)
    payload.update(
        {"status": "scored", "signals": signals, "risk": risk, "trace": trace}
    )
    return payload


def _print_payload(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if payload["status"] != "scored":
        gate = payload["gate"]
        print(
            f"NOT SCORED: climate probability {gate['probability']:.3f} "
            f"is below gate {gate['threshold']:.3f}"
        )
        return
    print(format_trace(payload["signals"], payload["risk"], payload["trace"]))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        payload = _score_signals(args) if args.command == "score-signals" else _score_text(args)
        if getattr(args, "provenance", None):
            if payload["status"] != "scored":
                parser.error("--provenance requires a scored paragraph; use --force if appropriate")
            from .provenance import write_score_provenance

            write_score_provenance(payload, args.provenance)
        _print_payload(payload, args.json)
    except (OSError, TypeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
