"""FaunaBehav API — wildlife behaviour monitoring and deterrence backend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.domain.inference import LabelledAdapter
from app.routers import alerts, auth, dashboard, devices, events, feedback
from app.storage import build_storage

__version__ = "1.0.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.storage = build_storage(settings)
        app.state.inference = LabelledAdapter()
        yield

    app = FastAPI(
        title="FaunaBehav API",
        version=__version__,
        description=(
            "Receives labelled wildlife detections from edge devices, assesses risk, "
            "decides a deterrence action, raises alerts and serves dashboard data."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router, prefix="/auth", tags=["Auth"])
    app.include_router(events.router, prefix="/events", tags=["Events"])
    app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
    app.include_router(devices.router, prefix="/devices", tags=["Devices"])
    app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
    app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

    @app.get("/", tags=["Meta"])
    def root():
        return {"name": "FaunaBehav API", "version": __version__, "docs": "/docs"}

    @app.get("/health", tags=["Meta"])
    def health():
        return {"status": "ok", "storage": settings.storage}

    return app


app = create_app()
