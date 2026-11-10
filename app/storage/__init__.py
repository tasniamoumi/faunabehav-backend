from app.config import Settings
from app.storage.base import Storage
from app.storage.memory import MemoryStorage


def build_storage(settings: Settings) -> Storage:
    if settings.storage == "memory":
        return MemoryStorage()
    from app.storage.supabase_storage import SupabaseStorage

    return SupabaseStorage(settings.supabase_url, settings.supabase_key)
