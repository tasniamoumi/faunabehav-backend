from collections import Counter

from fastapi import APIRouter, Depends

from app.schemas import DashboardSummary
from app.security import get_storage, require_user
from app.storage.base import Row, Storage

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def summary(_: Row = Depends(require_user), storage: Storage = Depends(get_storage)):
    events = storage.list_events(limit=500)
    alerts = storage.list_alerts(limit=500)
    devices = storage.list_devices()

    by_risk = Counter(str(e.get("risk_level") or "Low").capitalize() for e in events)
    animals = Counter(str(e.get("animal") or "unknown").replace(" ", "_").lower() for e in events)
    return DashboardSummary(
        total_events=len(events),
        high_risk_events=by_risk.get("High", 0),
        active_alerts=sum(1 for a in alerts if str(a.get("status", "")).lower() == "active"),
        active_devices=sum(1 for d in devices if str(d.get("status", "")).lower() == "active"),
        events_by_risk={k: by_risk.get(k, 0) for k in ("Low", "Medium", "High")},
        top_animals=[{"animal": a, "count": n} for a, n in animals.most_common(5)],
    )
