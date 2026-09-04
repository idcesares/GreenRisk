"""GreenRisk: explainable-by-construction greenwashing-risk scoring."""

__version__ = "0.2.0"

__all__ = ["__version__", "format_trace", "score_paragraph"]


def __getattr__(name: str):
    """Load the fuzzy scorer lazily so metadata remains dependency-light."""
    if name in {"format_trace", "score_paragraph"}:
        from . import rule_base

        return getattr(rule_base, name)
    raise AttributeError(name)
