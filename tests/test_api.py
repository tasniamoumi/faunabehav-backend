

def detect(client, key, **overrides):
    body = {"animal": "wild_boar", "behaviour": "feeding_foraging", "confidence": 0.9, "frame_path": "frames/1.jpg"}
    body.update(overrides)
    return client.post("/events/inference", json=body, headers={"X-Device-Key": key})


# ---- auth ----------------------------------------------------------------
def test_inference_requires_device_key(client):
    body = {"animal": "a", "behaviour": "b", "confidence": 0.5}
    assert client.post("/events/inference", json=body).status_code == 422
    r = client.post("/events/inference", json={"animal": "a", "behaviour": "b", "confidence": 0.5},
                    headers={"X-Device-Key": "fb_wrong"})
    assert r.status_code == 401


def test_dashboard_requires_login(client):
    assert client.get("/dashboard/summary").status_code == 401
    assert client.get("/events").status_code == 401


def test_login_and_me(client, auth):
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200 and r.json()["role"] == "admin"


def test_bad_password(client, admin_token):
    r = client.post("/auth/login", data={"username": "admin", "password": "nope"})
    assert r.status_code == 401


# ---- inference & alerts --------------------------------------------------
def test_medium_risk_creates_event_but_no_alert(client, device_key, auth):
    r = detect(client, device_key)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["risk_level"] == "Medium" and body["deterrence_action"] == "Flash Light"
    assert body["alert_id"] is None
    assert client.get("/alerts", headers=auth).json() == []


def test_high_risk_alert_points_at_its_own_event(client, device_key, auth, storage):
    # two detections back to back; the alert must reference the first one, not "the latest"
    first = detect(client, device_key, behaviour="aggressive_destructive", confidence=0.93).json()
    second = detect(client, device_key, behaviour="resting", confidence=0.80).json()
    assert first["alert_id"] is not None and second["alert_id"] is None
    alerts = client.get("/alerts", headers=auth).json()
    assert len(alerts) == 1
    assert alerts[0]["event_id"] == first["event_id"]
    assert alerts[0]["location"] == "North paddock"
    assert alerts[0]["deterrence_action"] == "Siren"


def test_device_cannot_dictate_risk(client, device_key):
    # The old API accepted risk_level from the client; it must now be ignored/rejected.
    r = detect(client, device_key, behaviour="resting", confidence=0.99, risk_level="High")
    assert r.status_code == 201
    assert r.json()["risk_level"] == "Low"


def test_low_confidence_never_sirens(client, device_key):
    r = detect(client, device_key, behaviour="aggressive_destructive", confidence=0.3)
    assert r.json()["risk_level"] == "Low" and r.json()["alert_id"] is None


def test_acknowledge_alert(client, device_key, auth):
    alert_id = detect(client, device_key, behaviour="vigilance_alert", confidence=0.8).json()["alert_id"]
    r = client.patch(f"/alerts/{alert_id}", json={"status": "Acknowledged"}, headers=auth)
    assert r.status_code == 200 and r.json()["status"] == "Acknowledged"
    assert r.json()["acknowledged_by"] == 1
    assert client.get("/alerts", params={"status": "Active"}, headers=auth).json() == []
    assert client.patch("/alerts/999", json={"status": "Resolved"}, headers=auth).status_code == 404


# ---- devices & users -----------------------------------------------------
def test_admin_registers_device_and_key_works(client, auth):
    r = client.post("/devices", json={"device_name": "cam-south", "location": "South fence"}, headers=auth)
    assert r.status_code == 201
    key = r.json()["api_key"]
    assert key.startswith("fb_")
    assert "api_key" not in client.get("/devices", headers=auth).json()[0]
    assert "api_key_hash" not in client.get("/devices", headers=auth).json()[0]
    assert detect(client, key).status_code == 201


def test_operator_cannot_register_devices(client, auth, storage):
    client.post("/auth/users", json={"username": "op1", "password": "operator123"}, headers=auth)
    tok = client.post("/auth/login", data={"username": "op1", "password": "operator123"}).json()["access_token"]
    r = client.post("/devices", json={"device_name": "x", "location": "y"}, headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 403


def test_duplicate_username(client, auth):
    r = client.post("/auth/users", json={"username": "admin", "password": "whatever123"}, headers=auth)
    assert r.status_code == 409


# ---- feedback & dashboard -------------------------------------------------
def test_feedback_validates_event_and_behaviour(client, device_key, auth):
    event_id = detect(client, device_key).json()["event_id"]
    ok = client.post("/feedback", json={"event_id": event_id, "corrected_behaviour": "resting"}, headers=auth)
    assert ok.status_code == 201 and ok.json()["user_id"] == 1
    missing = client.post("/feedback", json={"event_id": 999, "corrected_behaviour": "resting"}, headers=auth)
    assert missing.status_code == 404
    bad = client.post("/feedback", json={"event_id": event_id, "corrected_behaviour": "dancing"}, headers=auth)
    assert bad.status_code == 422


def test_dashboard_summary(client, device_key, auth):
    detect(client, device_key, behaviour="aggressive_destructive", confidence=0.9)
    detect(client, device_key, behaviour="feeding_foraging", confidence=0.9)
    detect(client, device_key, animal="macaque", behaviour="resting", confidence=0.9)
    s = client.get("/dashboard/summary", headers=auth).json()
    assert s["total_events"] == 3 and s["high_risk_events"] == 1 and s["active_alerts"] == 1
    assert s["active_devices"] == 1
    assert s["events_by_risk"] == {"Low": 1, "Medium": 1, "High": 1}
    assert s["top_animals"][0] == {"animal": "wild_boar", "count": 2}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "storage": "memory"}
