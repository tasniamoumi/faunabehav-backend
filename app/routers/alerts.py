from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas import AlertUpdate, AlertView
from app.security import get_storage, require_user
from app.storage.base import Row, Storage

router = APIRouter()


@router.get("", response_model=list[AlertView], summary="Alerts with their event and device details")
def list_alerts(
    limit: int = Query(100, ge=1, le=500),
    status: str | None = Query(None, description="Filter by status, e.g. Active"),
    _: Row = Depends(require_user),
    storage: Storage = Depends(get_storage),
):
    alerts = storage.list_alerts(limit)
    if status:
        alerts = [a for a in alerts if str(a.get("status", "")).lower() == status.lower()]

    # Join in memory with two bulk reads instead of two queries per alert.
    events = {e["event_id"]: e for e in storage.list_events(limit=max(limit * 2, 500))}
    devices = {d["device_id"]: d for d in storage.list_devices()}

    out = []
    for a in alerts:
        e = events.get(a["event_id"]) or storage.get_event(a["event_id"]) or {}
        d = devices.get(e.get("device_id"), {})
        out.append(AlertView(
            alert_id=a["alert_id"], event_id=a["event_id"],
            animal=e.get("animal"), behaviour=e.get("behaviour"), confidence=e.get("confidence"),
            location=d.get("location"),
            risk_level=a["risk_level"], deterrence_action=a["deterrence_action"], status=a["status"],
            triggered_at=a.get("triggered_at"), acknowledged_by=a.get("acknowledged_by"),
        ))
    return out


@router.patch("/{alert_id}", response_model=AlertView, summary="Acknowledge or resolve an alert")
def update_alert(
    alert_id: int,
    body: AlertUpdate,
    user: Row = Depends(require_user),
    storage: Storage = Depends(get_storage),
):
    updated = storage.update_alert(alert_id, {"status": body.status, "acknowledged_by": user["user_id"]})
    if updated is None:
        raise HTTPException(404, "alert not found")
    e = storage.get_event(updated["event_id"]) or {}
    return AlertView(**{k: updated.get(k) for k in ("alert_id", "event_id", "risk_level", "deterrence_action",
                                                     "status", "triggered_at", "acknowledged_by")},
                     animal=e.get("animal"), behaviour=e.get("behaviour"), confidence=e.get("confidence"))
