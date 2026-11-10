# FaunaBehav Backend

Backend for a wildlife behaviour monitoring and deterrence system for farms.
Edge cameras detect animals and classify their behaviour; this API decides how
risky each event is, tells the device what to do about it (monitor, flash a
light, sound a siren), raises alerts for operators and feeds a dashboard.

Built as my final-year capstone project (BSc Computer Science (Hons), Taylor's
University, supervised by Dr Mohsen Marjani), then hardened into a complete,
tested service. FaunaBehav was a five-person team project; I was the
**System & Backend Engineer**: system architecture, the FastAPI backend, the
behaviour-to-risk mapping and deterrence decision logic, data flow between
components, and backend testing. Teammates owned the models, the dataset and
the React dashboard.

[![CI](https://github.com/tasniamoumi/faunabehav-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/tasniamoumi/faunabehav-backend/actions/workflows/ci.yml)

## What's here, and what isn't

| Included | Not included |
|---|---|
| FastAPI service: inference endpoint, events, alerts, devices, feedback, dashboard, auth | The detection and behaviour models (YOLOv8, R3D-18). Weights and training data from the capstone were not preserved. |
| Risk engine and deterrence policy, unit-tested | The React dashboard that consumed this API |
| Postgres schema (`schema.sql`) matching the original capstone database, with RLS | |
| Device API keys and JWT user auth with roles | |
| In-memory mode for tests and demos, 25 tests, CI, Docker | |

The API accepts **labelled detections** from devices that run the models
themselves. The model boundary is a small interface (`app/domain/inference.py`),
so a model-hosting adapter can be added without touching the routes.

**About the data.** The capstone's Supabase database survived and is the
source of truth for the schema. It shows the full system as it ran in
June–August 2026: 14 registered cameras across farms, over a hundred events
with YOLO bounding boxes and species confidence, 73 alerts, and an operator
review workflow (`outcome`, `farmer_notes`, `escalation`). The code in the
original upload was an earlier snapshot; v1.0 is written against the real
columns.

**How the full system worked.** Operators uploaded wildlife video through the
React dashboard; YOLOv8 identified the species, R3D-18 classified the behaviour
from the clip, and the backend mapped the result to a risk level and a
recommended deterrence action (the capstone recommended actions, it did not
drive hardware). The design defined a five-level taxonomy (Neutral Movement →
Field Approach → Crop Proximity → Crop Consumption → Aggressive/Destructive,
mapped Low → Critical); the implementation shipped with the simpler behaviour
classes listed at the end of this file. Known limitations from the project
report: recorded video rather than live streams, a limited test-footage set,
and no physical device control.

## Architecture

```
  edge device (camera)                       this service                          operators
 ┌───────────────────┐   POST /events/inference  ┌──────────────┐  JWT   ┌───────────────────┐
 │ YOLOv8 detection  │ ───────────────────────▶  │ risk engine  │ ◀───── │ dashboard / app   │
 │ R3D-18 behaviour  │   X-Device-Key            │ deterrence   │        │ alerts, feedback  │
 └───────────────────┘ ◀───────────────────────  │ alerts       │        └───────────────────┘
       Monitor / Flash Light / Siren             └──────┬───────┘
                                                        │ Storage interface
                                                 ┌──────▼───────┐
                                                 │ Supabase     │   or in-memory (tests, demo)
                                                 │ (Postgres)   │
                                                 └──────────────┘
```

**Risk policy** (`app/domain/risk.py`): a detection below the confidence
threshold is always Low, so a siren never fires on a guess. `aggressive_destructive`
and `vigilance_alert` are High; `feeding_foraging` and `locomotion` are Medium
when confidence ≥ 0.70; everything else is Low. High-risk events raise an alert
tied to that exact event.

## Run it

**Demo, no credentials** (in-memory storage with seeded data):

```bash
pip install -r requirements-dev.txt
python -m scripts.demo
# open http://localhost:8000/docs   login: admin / demo-password
```

**Against Supabase:**

```bash
cp .env.example .env        # SUPABASE_URL, SUPABASE_KEY (service-role key, server-side only), JWT_SECRET
# run schema.sql once in the Supabase SQL editor (creates tables, or upgrades the capstone ones, and enables RLS)
python -m scripts.bootstrap admin  tasnia <password>        # first admin user
python -m scripts.bootstrap device cam-north "North paddock" # prints the device key once
uvicorn app.main:app --reload
```

**Docker:** `docker build -t faunabehav . && docker run --env-file .env -p 8000:8000 faunabehav`

**Tests:** `pytest -q` (runs entirely in memory).

## API

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/events/inference` | device key | Submit a labelled detection; returns risk, action and any alert id |
| GET | `/events`, `/events/{id}` | user | Recent events |
| GET | `/alerts?status=Active` | user | Alerts joined with event and device details |
| PATCH | `/alerts/{id}` | user | Acknowledge or resolve |
| GET | `/devices` | user | Registered cameras |
| POST | `/devices` | admin | Register a camera; returns its API key once |
| POST | `/feedback` | user | Correct a misclassified behaviour (retraining signal) |
| GET | `/dashboard/summary` | user | Counts by risk, active alerts, top animals |
| POST | `/auth/login` · GET `/auth/me` · POST `/auth/users` | – / user / admin | Auth |
| GET | `/health` | – | Liveness |

Example device call:

```bash
curl -X POST http://localhost:8000/events/inference \
  -H "X-Device-Key: fb_..." -H "Content-Type: application/json" \
  -d '{"animal":"wild_boar","behaviour":"aggressive_destructive","confidence":0.92}'
# {"event_id":4,"risk_level":"High","deterrence_action":"Siren","alert_id":2,...}
```

## Project layout

```
app/
  main.py          app factory, lifespan, routers
  config.py        settings from env / .env
  security.py      device keys (sha256), passwords (bcrypt), JWT
  schemas.py       request/response models
  domain/          risk.py · deterrence.py · inference.py   (pure logic, no I/O)
  storage/         base.py (interface) · memory.py · supabase_storage.py
  routers/         auth · events · alerts · devices · feedback · dashboard
scripts/           demo.py · bootstrap.py
tests/             25 tests against the in-memory storage
schema.sql         Postgres tables, constraints and indexes
```

## What changed in v1.0 (from the capstone build)

- **Alerts attach to the right event.** The original looked up "the latest
  event" after inserting; two cameras reporting together could attach an alert
  to the wrong one. Inserts now return the stored row.
- **The device can no longer dictate risk.** `/observations` accepted a
  `risk_level` from the client; risk is now computed server-side only.
- **Authentication.** Every route was open. Devices now use hashed API keys,
  users use JWTs, device registration and user creation are admin-only.
- **Confidence gate.** High-risk behaviours at low confidence no longer trigger the siren.
- **One storage layer** instead of a Supabase client created in four files,
  and the alerts list makes two bulk reads instead of two queries per alert.
- **Row Level Security** on every table; only the API's service-role key can reach the data.
- Tests, CI, Docker, a schema file and a credential-free demo mode.

## Behaviour classes

`aggressive_destructive`, `vigilance_alert`, `feeding_foraging`, `locomotion`,
`resting`, `unknown`. Operators can correct a classification through
`/feedback`; the corrections are stored as retraining data.

## Licence

MIT
