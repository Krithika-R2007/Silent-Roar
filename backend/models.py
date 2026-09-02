"""
models.py
---------
SQLAlchemy ORM table definitions for Supply Chain Ghost.
Only tables that benefit from structured querying are stored in SQLite.
Analytical CSV outputs stay in memory (see data_loader.py).

Designed to be forward-compatible with PostgreSQL / Supabase:
- No SQLite-specific types used in business logic.
- Primary keys are string UUIDs so they survive migration unchanged.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey,
)
from database import Base


class Incident(Base):
    __tablename__ = "incidents"

    incident_id    = Column(String, primary_key=True, index=True)
    incident_date  = Column(DateTime, nullable=True)
    species        = Column(String, nullable=True)
    commodity      = Column(String, nullable=True)
    quantity       = Column(Float, nullable=True)
    source_location = Column(String, nullable=True, index=True)
    destination    = Column(String, nullable=True, index=True)
    route_id       = Column(String, ForeignKey("routes.route_id"), nullable=True, index=True)
    lead_actor     = Column(String, ForeignKey("actors.actor_id"), nullable=True, index=True)
    seizure_status = Column(String, nullable=True)
    latitude       = Column(Float, nullable=True)
    longitude      = Column(Float, nullable=True)
    network_id     = Column(String, nullable=True)


class Actor(Base):
    __tablename__ = "actors"

    actor_id       = Column(String, primary_key=True, index=True)
    full_name      = Column(String, nullable=True)
    alias          = Column(String, nullable=True)
    nationality    = Column(String, nullable=True)
    role           = Column(String, nullable=True)
    primary_region = Column(String, nullable=True)
    threat_score   = Column(Float, nullable=True)


class Route(Base):
    __tablename__ = "routes"

    route_id       = Column(String, primary_key=True, index=True)
    source         = Column(String, nullable=True)
    transit        = Column(String, nullable=True)
    destination    = Column(String, nullable=True)
    corridor       = Column(String, nullable=True)
    historical_risk = Column(Float, nullable=True)


class Shipment(Base):
    __tablename__ = "shipments"

    shipment_id      = Column(String, primary_key=True, index=True)
    incident_id      = Column(String, ForeignKey("incidents.incident_id"), nullable=True, index=True)
    actor_id         = Column(String, ForeignKey("actors.actor_id"), nullable=True, index=True)
    vehicle_id       = Column(String, nullable=True)
    transport_type   = Column(String, nullable=True)
    departure_date   = Column(DateTime, nullable=True)
    arrival_date     = Column(DateTime, nullable=True)
    shipment_weight  = Column(Float, nullable=True)
    status           = Column(String, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    message_id     = Column(String, primary_key=True, index=True)
    sender_actor   = Column(String, nullable=True, index=True)
    receiver_actor = Column(String, nullable=True, index=True)
    timestamp      = Column(DateTime, nullable=True)
    chat_group     = Column(String, nullable=True)
    message_text   = Column(Text, nullable=True)
    contains_slang = Column(Boolean, nullable=True)
    linked_route   = Column(String, nullable=True)


class AnimalEvent(Base):
    __tablename__ = "animal_events"

    event_id          = Column(String, primary_key=True, index=True)
    protected_area    = Column(String, nullable=True, index=True)
    event_date        = Column(DateTime, nullable=True)
    normal_movement   = Column(Float, nullable=True)
    observed_movement = Column(Float, nullable=True)
    anomaly_score     = Column(Float, nullable=True)
    latitude          = Column(Float, nullable=True)
    longitude         = Column(Float, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    alert_id                = Column(String, primary_key=True, index=True)
    pattern_type            = Column(String, nullable=True, index=True)
    priority                = Column(String, nullable=True, index=True)
    entity_type             = Column(String, nullable=True)
    entity_id               = Column(String, nullable=True, index=True)
    risk_score              = Column(Float, nullable=True)
    confidence              = Column(Float, nullable=True)
    first_detected          = Column(DateTime, nullable=True)
    last_detected           = Column(DateTime, nullable=True)
    incident_count          = Column(Integer, nullable=True)
    related_actor_count     = Column(Integer, nullable=True)
    related_route_count     = Column(Integer, nullable=True)
    related_location_count  = Column(Integer, nullable=True)
    explanation             = Column(Text, nullable=True)


class LinguisticSignal(Base):
    __tablename__ = "linguistic_signals"

    signal_id       = Column(String, primary_key=True, index=True)
    message_id      = Column(String, nullable=True, index=True)
    target_type     = Column(String, nullable=True)
    target_id       = Column(String, nullable=True, index=True)
    linguistic_risk  = Column(Float, nullable=True)
    confidence      = Column(Float, nullable=True)
    detected_terms  = Column(Text, nullable=True)    # JSON list stored as text
    explanation     = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
