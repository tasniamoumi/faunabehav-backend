"""Inference pipeline.

In the full FaunaBehav system an edge device runs two models:

    camera frame -> YOLOv8 (animal detection) -> R3D-18 (behaviour over a clip)

and sends the labelled result to this API. The model weights are not part of
this repository, so the API accepts *labelled detections* through an
`InferenceAdapter`. `LabelledAdapter` is the production path for devices that
run the models themselves; a model-hosting adapter can be added later by
implementing the same two-method interface without touching the routers.
"""
from dataclasses import dataclass
from typing import Protocol

from app.domain.deterrence import get_deterrence_action
from app.domain.risk import calculate_risk


@dataclass(frozen=True)
class Detection:
    animal: str
    behaviour: str
    confidence: float


@dataclass(frozen=True)
class Assessment:
    animal: str
    behaviour: str
    confidence: float
    risk_level: str
    deterrence_action: str


class InferenceAdapter(Protocol):
    """Anything that can turn an incoming request into a Detection."""

    name: str

    def detect(self, *, animal: str, behaviour: str, confidence: float) -> Detection: ...


class LabelledAdapter:
    """Trusts labels produced by the models running on the edge device."""

    name = "labelled"

    def detect(self, *, animal: str, behaviour: str, confidence: float) -> Detection:
        return Detection(animal=animal.strip().lower(), behaviour=behaviour.strip().lower(), confidence=confidence)


def assess(detection: Detection, min_confidence: float) -> Assessment:
    risk = calculate_risk(detection.behaviour, detection.confidence, min_confidence)
    return Assessment(
        animal=detection.animal,
        behaviour=detection.behaviour,
        confidence=detection.confidence,
        risk_level=risk,
        deterrence_action=get_deterrence_action(risk),
    )
