from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.domain.inference import assess
from app.schemas import Event, InferenceRequest, InferenceResponse
from app.security import get_storage, require_device, require_user
from app.storage.base import Row, Storage

router = APIRouter()


@router.post("/inference", response_model=InferenceResponse, status_code=201,
             summary="Submit a labelled detection from an edge device")
def run_inference(
    body: InferenceRequest,
    request: Request,
    device: Row = Depends(require_device),
    storage: Storage = Depends(get_storage),
):
    """The device runs the detection and behaviour models and sends the labels.
    The API decides the risk level and deterrence action (never the device),
    stores the event, and raises an alert for High-risk events."""
    settings = request.app.state.settings
    detection = request.app.state.inference.detect(
        animal=body.animal, behaviour=body.behaviour, confidence=body.confidence)
    result = assess(detection, settings.min_confidence)

    event = storage.insert_event({
        "device_id": device["device_id"],
        "animal": result.animal,
        "behaviour": result.behaviour,
        "confidence": result.confidence,
        "risk_level": result.risk_level,
        "deterrence_action": result.deterrence_action,
        "frame_path": body.frame_path,
    })

    alert_id = None
    if result.risk_level == "High":
        alert = storage.insert_alert({
            "event_id": event["event_id"],          # the row we just inserted, not "the latest"
            "risk_level": result.risk_level,
            "deterrence_action": result.deterrence_action,
            "status": "Active",
        })
        alert_id = alert["alert_id"]

    return InferenceResponse(event_id=event["event_id"], alert_id=alert_id, **result.__dict__)


@router.get("", response_model=list[Event], summary="List recent events")
def list_events(
    limit: int = Query(100, ge=1, le=500),
    _: Row = Depends(require_user),
    storage: Storage = Depends(get_storage),
):
    return storage.list_events(limit)


@router.get("/{event_id}", response_model=Event)
def get_event(event_id: int, _: Row = Depends(require_user), storage: Storage = Depends(get_storage)):
    event = storage.get_event(event_id)
    if event is None:
        raise HTTPException(404, "event not found")
    return event
