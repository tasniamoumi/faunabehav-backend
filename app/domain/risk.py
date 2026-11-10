"""Risk assessment: behaviour class + detection confidence -> risk level.

Behaviour classes are the ones the FaunaBehav behaviour model outputs.
The mapping is deliberately simple and explicit so it can be reviewed by
non-programmers (the farm operators the system is built for).
"""
from typing import Literal

RiskLevel = Literal["Low", "Medium", "High"]

HIGH_RISK_BEHAVIOURS = frozenset({"aggressive_destructive", "vigilance_alert"})
MEDIUM_RISK_BEHAVIOURS = frozenset({"feeding_foraging", "locomotion"})
KNOWN_BEHAVIOURS = HIGH_RISK_BEHAVIOURS | MEDIUM_RISK_BEHAVIOURS | {"resting", "unknown"}

MEDIUM_CONFIDENCE_THRESHOLD = 0.70


def calculate_risk(behaviour: str, confidence: float, min_confidence: float = 0.50) -> RiskLevel:
    """Return the risk level for one detection.

    - Detections below `min_confidence` are always Low: a siren should never
      fire on a guess.
    - High-risk behaviours are High once the detection is trustworthy.
    - Medium-risk behaviours need a stronger detection (>= 0.70) to be Medium.
    """
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if confidence < min_confidence:
        return "Low"
    if behaviour in HIGH_RISK_BEHAVIOURS:
        return "High"
    if behaviour in MEDIUM_RISK_BEHAVIOURS and confidence >= MEDIUM_CONFIDENCE_THRESHOLD:
        return "Medium"
    return "Low"
