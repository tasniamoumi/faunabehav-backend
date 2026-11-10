import pytest

from app.domain.deterrence import get_deterrence_action
from app.domain.risk import calculate_risk


@pytest.mark.parametrize("behaviour,confidence,expected", [
    ("aggressive_destructive", 0.95, "High"),
    ("vigilance_alert", 0.60, "High"),
    ("feeding_foraging", 0.90, "Medium"),
    ("feeding_foraging", 0.65, "Low"),      # medium behaviour, weak detection
    ("locomotion", 0.70, "Medium"),
    ("resting", 0.99, "Low"),
    ("aggressive_destructive", 0.40, "Low"),  # below min confidence: never escalate
    ("made_up_behaviour", 0.99, "Low"),
])
def test_risk_matrix(behaviour, confidence, expected):
    assert calculate_risk(behaviour, confidence) == expected


def test_confidence_out_of_range_rejected():
    with pytest.raises(ValueError):
        calculate_risk("resting", 1.5)


def test_deterrence_mapping():
    assert get_deterrence_action("Low") == "Monitor"
    assert get_deterrence_action("Medium") == "Flash Light"
    assert get_deterrence_action("High") == "Siren"
    assert get_deterrence_action("???") == "Monitor"
