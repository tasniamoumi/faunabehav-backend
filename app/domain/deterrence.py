"""Deterrence policy: risk level -> action the edge device should take."""
from typing import Literal

DeterrenceAction = Literal["Monitor", "Flash Light", "Siren"]

ACTIONS: dict[str, DeterrenceAction] = {
    "Low": "Monitor",
    "Medium": "Flash Light",
    "High": "Siren",
}


def get_deterrence_action(risk_level: str) -> DeterrenceAction:
    return ACTIONS.get(risk_level, "Monitor")
