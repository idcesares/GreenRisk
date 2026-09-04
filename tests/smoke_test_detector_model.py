"""Optional sanity check for the pinned climate-relevance detector."""

import pytest

PARAGRAPH = (
    "We are committed to reducing our Scope 1 and Scope 2 greenhouse gas "
    "emissions by 50% by 2030, relative to a 2019 baseline. This commitment "
    "is aligned with the Science Based Targets initiative and verified annually "
    "by an independent third party."
)


@pytest.mark.model
def test_climate_detector_recognizes_climate_paragraph() -> None:
    from greenrisk.models import score

    result = score("detector", PARAGRAPH)
    assert set(result) == {"no", "yes"}
    assert result["yes"] > result["no"]


if __name__ == "__main__":
    test_climate_detector_recognizes_climate_paragraph()
    print("Detector smoke test passed.")
