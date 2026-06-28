"""Command-line scorer for already-computed GreenRisk signals."""

from __future__ import annotations

import argparse

from rule_base import ANTS, format_trace, score_paragraph


def probability(value: str) -> float:
    parsed = float(value)
    if not 0.0 <= parsed <= 1.0:
        raise argparse.ArgumentTypeError("expected a probability in [0, 1]")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Score one paragraph from precomputed GreenRisk signal probabilities."
    )
    parser.add_argument("--specificity", required=True, type=probability)
    parser.add_argument("--commitment", required=True, type=probability)
    parser.add_argument(
        "--sentiment-asymmetry",
        dest="sentiment_asymmetry",
        required=True,
        type=probability,
    )
    parser.add_argument("--netzero", required=True, type=probability)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    signals = {name: getattr(args, name) for name in ANTS}
    risk, trace = score_paragraph(signals)
    print(format_trace(signals, risk, trace))


if __name__ == "__main__":
    main()
