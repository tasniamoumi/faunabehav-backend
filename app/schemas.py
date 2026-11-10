"""Request and response models (the API contract)."""
from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["Low", "Medium", "High"]
AlertStatus = Literal["Active", "Acknowledged", "Resolved"]


# ---- inference ----------------------------------------------------------
class InferenceRequest(BaseModel):
    """A labelled detection sent by an edge device (device identified by its key)."""
    animal: str = Field(..., min_length=1, max_length=64, examples=["wild_boar"])
    behaviour: str = Field(..., min_length=1, max_length=64, examples=["feeding_foraging"])
    confidence: float = Field(..., ge=0.0, le=1.0, examples=[0.87])
    frame_path: str | None = Field(None, max_length=512, description="Storage path of the frame or clip")


class InferenceResponse(BaseModel):
    event_id: int
    animal: str
    behaviour: str
    confidence: float
    risk_level: RiskLevel
    deterrence_action: str
    alert_id: int | None = None


# ---- events / alerts -----------------------------------------------------
class Event(BaseModel):
    event_id: int
    device_id: int
    animal: str | None = None
    behaviour: str | None = None
    confidence: float | None = None
    risk_level: str
    deterrence_action: str | None = None
    frame_path: str | None = None
    created_at: str | None = None


class AlertView(BaseModel):
    alert_id: int
    event_id: int
    animal: str | None = None
    behaviour: str | None = None
    confidence: float | None = None
    location: str | None = None
    risk_level: str
    deterrence_action: str
    status: str
    triggered_at: str | None = None
    acknowledged_by: int | None = None


class AlertUpdate(BaseModel):
    status: AlertStatus


# ---- devices -------------------------------------------------------------
class DeviceCreate(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=64)
    location: str = Field(..., min_length=1, max_length=128)


class Device(BaseModel):
    device_id: int
    device_name: str
    location: str
    status: str
    farm_id: int | None = None
    created_at: str | None = None


class DeviceCreated(Device):
    api_key: str = Field(..., description="Shown once. Store it on the device.")


# ---- feedback ------------------------------------------------------------
class FeedbackCreate(BaseModel):
    event_id: int
    corrected_behaviour: str = Field(..., min_length=1, max_length=64)
    note: str | None = Field(None, max_length=500)


class Feedback(FeedbackCreate):
    feedback_id: int
    user_id: int
    created_at: str | None = None


# ---- auth / users --------------------------------------------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    role: Literal["operator", "admin"] = "operator"


class User(BaseModel):
    user_id: int
    username: str
    role: str


# ---- dashboard -----------------------------------------------------------
class DashboardSummary(BaseModel):
    total_events: int
    high_risk_events: int
    active_alerts: int
    active_devices: int
    events_by_risk: dict[str, int]
    top_animals: list[dict[str, int | str]]
