"""Run the API with in-memory storage and seeded demo data. No credentials needed.

    python -m scripts.demo            # then open http://localhost:8000/docs
    login: admin / demo-password      device key is printed on start-up
"""
from contextlib import asynccontextmanager

import uvicorn

from app.config import Settings
from app.main import create_app
from app.security import hash_password, new_device_key


def seed(app):
    s = app.state.storage
    s.insert_user({"username": "admin", "password_hash": hash_password("demo-password"), "role": "admin"})
    key, key_hash = new_device_key()
    dev = s.insert_device({"device_name": "cam-north", "location": "North paddock", "status": "Active",
                           "api_key_hash": key_hash})
    samples = [("wild_boar", "feeding_foraging", 0.91, "Medium", "Flash Light"),
               ("macaque", "resting", 0.84, "Low", "Monitor"),
               ("wild_boar", "aggressive_destructive", 0.95, "High", "Siren")]
    for animal, beh, conf, risk, action in samples:
        e = s.insert_event({"device_id": dev["device_id"], "animal": animal, "behaviour": beh, "confidence": conf,
                            "risk_level": risk, "deterrence_action": action, "frame_path": None})
        if risk == "High":
            s.insert_alert({"event_id": e["event_id"], "risk_level": risk,
                            "deterrence_action": action, "status": "Active"})
    print("\n  Demo ready.  login: admin / demo-password")
    print(f"  device key for POST /events/inference:  {key}\n")


if __name__ == "__main__":
    app = create_app(Settings(storage="memory", jwt_secret="demo-only-secret", _env_file=None))

    inner = app.router.lifespan_context

    @asynccontextmanager
    async def lifespan(a):  # seed once the app's own lifespan has built the storage
        async with inner(a):
            seed(a)
            yield

    app.router.lifespan_context = lifespan

    uvicorn.run(app, host="0.0.0.0", port=8000)
