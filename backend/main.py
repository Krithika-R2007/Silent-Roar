"""
main.py
-------
Supply Chain Ghost — FastAPI application entry point.

Startup:
  1. Load all CSV/JSON intelligence outputs into memory.
  2. Seed SQLite with structured data (incidents, actors, routes, etc.).
  3. Mount all routers.

Run:
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import math
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Internal modules ──────────────────────────────────────────────────────────
from database import engine, SessionLocal, Base
from models import (
    Incident, Actor, Route, Shipment, Message, AnimalEvent, Alert
)
from data_loader import load_all, get_data
from schemas import HealthResponse, ErrorResponse

# ── Routers ───────────────────────────────────────────────────────────────────
from routers.dashboard import router as dashboard_router
from routers.intelligence import router as intelligence_router
from routers.network import router as network_router
from routers.messages import router as messages_router
from routers.investigations import router as investigations_router


# ── Lifespan: data loading + DB seed ─────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all tables
    Base.metadata.create_all(bind=engine)

    # 2. Load CSV/JSON into memory (idempotent — safe to call multiple times)
    d = load_all()

    # 3. Seed SQLite (only if tables are empty)
    with SessionLocal() as db:
        _seed_if_empty(db, d)

    # Print startup banner
    print()
    print("=" * 52)
    print("FASTAPI INTEGRATION COMPLETE")
    print("=" * 52)
    print(f"  Server command:          uvicorn main:app --reload --port 8000")
    print(f"  API base URL:            http://localhost:8000")
    print(f"  Swagger URL:             http://localhost:8000/docs")
    print(f"  Loaded incidents:        {len(d.incidents)}")
    print(f"  Loaded intelligence:     {len(d.intelligence_scores)}")
    print(f"  Loaded alerts:           {len(d.pattern_alerts)}")
    print("=" * 52)
    print()

    yield  # application is live

    # Shutdown (nothing to clean up for SQLite)


def _seed_if_empty(db, d):
    """Insert rows into SQLite only on first run (idempotent)."""
    from sqlalchemy import inspect
    inspector = inspect(engine)

    # Check actor count as proxy for 'already seeded'
    from sqlalchemy import text
    try:
        count = db.execute(text("SELECT COUNT(*) FROM actors")).scalar()
        if count and count > 0:
            return
    except Exception:
        pass

    def _safe(v):
        """Convert pandas NaT / NaN to None for SQLAlchemy."""
        if v is None:
            return None
        if isinstance(v, float) and math.isnan(v):
            return None
        if hasattr(v, "_value") and v._value is None:
            return None
        if hasattr(v, "isoformat"):
            return v
        return v

    # Actors
    if not d.actors.empty:
        for r in d.actors.to_dict("records"):
            db.add(Actor(
                actor_id=str(r.get("actor_id", "")),
                full_name=r.get("full_name"),
                alias=r.get("alias"),
                nationality=r.get("nationality"),
                role=r.get("role"),
                primary_region=r.get("primary_region"),
                threat_score=_safe(r.get("threat_score")),
            ))

    # Routes
    if not d.routes.empty:
        for r in d.routes.to_dict("records"):
            db.add(Route(
                route_id=str(r.get("route_id", "")),
                source=r.get("source"),
                transit=r.get("transit"),
                destination=r.get("destination"),
                corridor=r.get("corridor"),
                historical_risk=_safe(r.get("historical_risk")),
            ))

    db.flush()  # routes + actors must exist before incidents (FK)

    # Incidents
    if not d.incidents.empty:
        for r in d.incidents.to_dict("records"):
            db.add(Incident(
                incident_id=str(r.get("incident_id", "")),
                incident_date=_safe(r.get("incident_date")),
                species=r.get("species"),
                commodity=r.get("commodity"),
                quantity=_safe(r.get("quantity")),
                source_location=r.get("source_location"),
                destination=r.get("destination"),
                route_id=r.get("route_id"),
                lead_actor=r.get("lead_actor"),
                seizure_status=r.get("seizure_status"),
                latitude=_safe(r.get("latitude")),
                longitude=_safe(r.get("longitude")),
                network_id=r.get("network_id"),
            ))

    # Shipments
    if not d.shipments.empty:
        for r in d.shipments.to_dict("records"):
            db.add(Shipment(
                shipment_id=str(r.get("shipment_id", "")),
                incident_id=r.get("incident_id"),
                actor_id=r.get("actor_id"),
                vehicle_id=r.get("vehicle_id"),
                transport_type=r.get("transport_type"),
                departure_date=_safe(r.get("departure_date")),
                arrival_date=_safe(r.get("arrival_date")),
                shipment_weight=_safe(r.get("shipment_weight")),
                status=r.get("status"),
            ))

    # Messages
    if not d.messages.empty:
        for r in d.messages.to_dict("records"):
            slang_raw = r.get("contains_slang")
            slang_val = str(slang_raw).lower() == "true" if slang_raw is not None else None
            linked = r.get("linked_route")
            db.add(Message(
                message_id=str(r.get("message_id", "")),
                sender_actor=r.get("sender_actor"),
                receiver_actor=r.get("receiver_actor"),
                timestamp=_safe(r.get("timestamp")),
                chat_group=r.get("chat_group"),
                message_text=r.get("message_text"),
                contains_slang=slang_val,
                linked_route=linked if linked and str(linked).lower() != "nan" else None,
            ))

    # Animal events
    if not d.animal_events.empty:
        for r in d.animal_events.to_dict("records"):
            db.add(AnimalEvent(
                event_id=str(r.get("event_id", "")),
                protected_area=r.get("protected_area"),
                event_date=_safe(r.get("event_date")),
                normal_movement=_safe(r.get("normal_movement")),
                observed_movement=_safe(r.get("observed_movement")),
                anomaly_score=_safe(r.get("anomaly_score")),
                latitude=_safe(r.get("latitude")),
                longitude=_safe(r.get("longitude")),
            ))

    # Alerts
    if not d.pattern_alerts.empty:
        for r in d.pattern_alerts.to_dict("records"):
            db.add(Alert(
                alert_id=str(r.get("alert_id", "")),
                pattern_type=r.get("pattern_type"),
                priority=r.get("priority"),
                entity_type=r.get("entity_type"),
                entity_id=r.get("entity_id"),
                risk_score=_safe(r.get("risk_score")),
                confidence=_safe(r.get("confidence")),
                first_detected=_safe(r.get("first_detected")),
                last_detected=_safe(r.get("last_detected")),
                incident_count=r.get("incident_count"),
                related_actor_count=r.get("related_actor_count"),
                related_route_count=r.get("related_route_count"),
                related_location_count=r.get("related_location_count"),
                explanation=r.get("explanation"),
            ))

    db.commit()
    print("SQLite seed complete.")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Supply Chain Ghost",
    description=(
        "Wildlife intelligence REST API for the Supply Chain Ghost platform. "
        "All findings are intelligence signals and potential associations — "
        "not confirmed evidence of criminal activity."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React (Create React App)
        "http://localhost:5173",   # Vite
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global exception handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Do not expose stack traces
    return JSONResponse(
        status_code=500,
        content={"error": True, "message": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# ── Health ────────────────────────────────────────────────────────────────────

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
)
def health():
    d = get_data()
    return HealthResponse(status="ok", service="Supply Chain Ghost", data_loaded=d.loaded)


# ── Mount routers ─────────────────────────────────────────────────────────────

app.include_router(dashboard_router)
app.include_router(intelligence_router)
app.include_router(network_router)
app.include_router(messages_router)
app.include_router(investigations_router)
