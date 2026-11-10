"""In-memory storage: used by the test suite and by STORAGE=memory demo runs."""
from datetime import UTC, datetime
from itertools import count

from app.storage.base import Row


def _now() -> str:
    return datetime.now(UTC).isoformat()


class MemoryStorage:
    def __init__(self) -> None:
        self.events: list[Row] = []
        self.alerts: list[Row] = []
        self.devices: list[Row] = []
        self.feedback: list[Row] = []
        self.users: list[Row] = []
        self._ids = {name: count(1) for name in ("event", "alert", "device", "feedback", "user")}

    def _next(self, name: str) -> int:
        return next(self._ids[name])

    # events
    def insert_event(self, data: Row) -> Row:
        row = {"event_id": self._next("event"), "created_at": _now(), **data}
        self.events.append(row)
        return row

    def list_events(self, limit: int = 100) -> list[Row]:
        return sorted(self.events, key=lambda r: r["event_id"], reverse=True)[:limit]

    def get_event(self, event_id: int) -> Row | None:
        return next((e for e in self.events if e["event_id"] == event_id), None)

    # alerts
    def insert_alert(self, data: Row) -> Row:
        row = {"alert_id": self._next("alert"), "triggered_at": _now(), "acknowledged_by": None, **data}
        self.alerts.append(row)
        return row

    def list_alerts(self, limit: int = 100) -> list[Row]:
        return sorted(self.alerts, key=lambda r: r["alert_id"], reverse=True)[:limit]

    def update_alert(self, alert_id: int, data: Row) -> Row | None:
        for a in self.alerts:
            if a["alert_id"] == alert_id:
                a.update(data)
                return a
        return None

    # devices
    def list_devices(self) -> list[Row]:
        return [{k: v for k, v in d.items() if k != "api_key_hash"} for d in self.devices]

    def insert_device(self, data: Row) -> Row:
        row = {"device_id": self._next("device"), "status": "Active", "created_at": _now(), **data}
        self.devices.append(row)
        return row

    def get_device_by_key_hash(self, key_hash: str) -> Row | None:
        return next((d for d in self.devices if d.get("api_key_hash") == key_hash), None)

    # feedback
    def insert_feedback(self, data: Row) -> Row:
        row = {"feedback_id": self._next("feedback"), "created_at": _now(), **data}
        self.feedback.append(row)
        return row

    # users
    def get_user_by_username(self, username: str) -> Row | None:
        return next((u for u in self.users if u["username"] == username), None)

    def insert_user(self, data: Row) -> Row:
        row = {"user_id": self._next("user"), "role": "operator", "created_at": _now(), **data}
        self.users.append(row)
        return row
