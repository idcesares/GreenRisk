"""Optional smoke tests for all pinned model adapters."""

import pytest

TEST_PARAGRAPH = (
    "We are committed to achieving net-zero greenhouse gas emissions across "
    "our entire value chain by 2050. Our sustainability strategy places "
    "climate action at the core of our business, creating long-term value "
    "for shareholders while contributing to a more sustainable future."
)


@pytest.mark.model
def test_all_pinned_models_produce_probabilities() -> None:
    from greenrisk.models import MODEL_REGISTRY, score

    for name in MODEL_REGISTRY:
        result = score(name, TEST_PARAGRAPH)
        assert result
        assert all(0.0 <= probability <= 1.0 for probability in result.values())
        assert sum(result.values()) == pytest.approx(1.0, abs=1e-6)


if __name__ == "__main__":
    test_all_pinned_models_produce_probabilities()
    print("All pinned model smoke tests passed.")
