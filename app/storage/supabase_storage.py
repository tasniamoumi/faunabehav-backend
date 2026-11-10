"""Supabase (Postgres) storage. Tables are defined in schema.sql."""
from supabase import Client, create_client

from app.storage.base import Row


class SupabaseStorage:
    def __init__(self, url: str, key: str) -> None:
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set (or use STORAGE=memory)")
        self.client: Client = create_client(url, key)

    def _insert(self, table: str, data: Row) -> Row:
        res = self.client.table(table).insert(data).execute()
        if not res.data:
            raise RuntimeError(f"insert into {table} returned no row")
        return res.data[0]

    # events
    def insert_event(self, data: Row) -> Row:
        return self._insert("events", data)

    def list_events(self, limit: int = 100) -> list[Row]:
        return self.client.table("events").select("*").order("event_id", desc=True).limit(limit).execute().data

    def get_event(self, event_id: int) -> Row | None:
        res = self.client.table("events").select("*").eq("event_id", event_id).limit(1).execute()
        return res.data[0] if res.data else None

    # alerts
    def insert_alert(self, data: Row) -> Row:
        return self._insert("alerts", data)

    def list_alerts(self, limit: int = 100) -> list[Row]:
        return self.client.table("alerts").select("*").order("alert_id", desc=True).limit(limit).execute().data

    def update_alert(self, alert_id: int, data: Row) -> Row | None:
        res = self.client.table("alerts").update(data).eq("alert_id", alert_id).execute()
        return res.data[0] if res.data else None

    # devices
    def list_devices(self) -> list[Row]:
        cols = "device_id, device_name, location, status, created_at"
        return self.client.table("devices").select(cols).order("device_id").execute().data

    def insert_device(self, data: Row) -> Row:
        return self._insert("devices", data)

    def get_device_by_key_hash(self, key_hash: str) -> Row | None:
        res = self.client.table("devices").select("*").eq("api_key_hash", key_hash).limit(1).execute()
        return res.data[0] if res.data else None

    # feedback
    def insert_feedback(self, data: Row) -> Row:
        return self._insert("feedback", data)

    # users
    def get_user_by_username(self, username: str) -> Row | None:
        res = self.client.table("users").select("*").eq("username", username).limit(1).execute()
        return res.data[0] if res.data else None

    def insert_user(self, data: Row) -> Row:
        return self._insert("users", data)
