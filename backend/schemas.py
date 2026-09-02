"""
schemas.py
----------
Pydantic v2 response models for Supply Chain Ghost FastAPI.
All API responses are typed here so Swagger docs are auto-generated.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Error ─────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    code: str


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    data_loaded: bool


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_incidents: int
    total_actors: int
    total_routes: int
    total_shipments: int
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    watch_alerts: int
    active_investigations: int
    high_risk_routes: int
    emerging_hubs: int


# ── Alerts ────────────────────────────────────────────────────────────────────

class AlertItem(BaseModel):
    alert_id: str
    title: str
    pattern_type: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    priority: Optional[str]
    risk_score: Optional[float]
    confidence: Optional[float]
    explanation: Optional[str]
    first_detected: Optional[Any]
    last_detected: Optional[Any]


class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertItem]


# ── Map ───────────────────────────────────────────────────────────────────────

class MapPoint(BaseModel):
    id: str
    type: str
    latitude: float
    longitude: float
    name: str
    risk_score: Optional[float]
    priority: Optional[str]
    related_count: Optional[int] = 0


class MapRoute(BaseModel):
    route_id: str
    source: Optional[str]
    transit: Optional[str]
    destination: Optional[str]
    risk_score: Optional[float]


class MapResponse(BaseModel):
    points: List[MapPoint]
    routes: List[MapRoute]


# ── Incidents ─────────────────────────────────────────────────────────────────

class IncidentSummary(BaseModel):
    incident_id: str
    incident_date: Optional[Any]
    species: Optional[str]
    commodity: Optional[str]
    quantity: Optional[float]
    source_location: Optional[str]
    destination: Optional[str]
    route_id: Optional[str]
    lead_actor: Optional[str]
    seizure_status: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


class EvidenceItem(BaseModel):
    source_file: str
    source_id: str
    data_type: str
    detail: Optional[str] = None


class IncidentDetail(BaseModel):
    incident: IncidentSummary
    related_actors: List[Dict[str, Any]]
    related_shipments: List[Dict[str, Any]]
    route_info: Optional[Dict[str, Any]]
    related_alerts: List[Dict[str, Any]]
    intelligence_score: Optional[float]
    supporting_evidence: List[EvidenceItem]
    hidden_links: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]


class IncidentListResponse(BaseModel):
    total: int
    incidents: List[IncidentSummary]


# ── Actors ────────────────────────────────────────────────────────────────────

class ActorSummary(BaseModel):
    actor_id: str
    full_name: Optional[str]
    alias: Optional[str]
    nationality: Optional[str]
    role: Optional[str]
    primary_region: Optional[str]
    threat_score: Optional[float]


class ActorDetail(BaseModel):
    actor: ActorSummary
    risk_score: Optional[float]
    confidence: Optional[float]
    linked_incidents: List[Dict[str, Any]]
    routes: List[str]
    shipments: List[Dict[str, Any]]
    entity_matches: List[Dict[str, Any]]
    network_statistics: Dict[str, Any]


class ActorListResponse(BaseModel):
    total: int
    actors: List[ActorSummary]


# ── Routes ────────────────────────────────────────────────────────────────────

class RouteSummary(BaseModel):
    route_id: str
    source: Optional[str]
    transit: Optional[str]
    destination: Optional[str]
    risk_score: Optional[float]
    route_status: Optional[str]
    incident_count: Optional[int]
    actor_count: Optional[int]


class RouteDetail(BaseModel):
    route: RouteSummary
    risk_score: Optional[float]
    recent_activity: List[Dict[str, Any]]
    related_incidents: List[Dict[str, Any]]
    recurring_actors: List[str]
    hidden_links: List[Dict[str, Any]]
    pattern_alerts: List[Dict[str, Any]]
    activity_summary: Dict[str, Any]


class RouteListResponse(BaseModel):
    total: int
    routes: List[RouteSummary]


# ── Intelligence ──────────────────────────────────────────────────────────────

class IntelligenceResponse(BaseModel):
    target_type: str
    target_id: str
    risk_score: Optional[float]
    intelligence_confidence: Optional[float]
    investigation_priority: Optional[str]
    trade_score: Optional[float]
    route_score: Optional[float]
    entity_score: Optional[float]
    linguistic_score: Optional[float]
    animal_score: Optional[float]
    cross_evidence_alignment: Optional[float]
    evidence_stream_count: Optional[int]
    evidence_streams: Optional[List[str]]
    supporting_incidents: Optional[List[str]]
    supporting_routes: Optional[List[str]]
    supporting_actors: Optional[List[str]]
    explanation: Optional[str]
    uncertainties: List[str]


class ExplanationEvidence(BaseModel):
    trade: List[EvidenceItem]
    route: List[EvidenceItem]
    entity: List[EvidenceItem]
    linguistic: List[EvidenceItem]
    animal: List[EvidenceItem]


class ExplanationResponse(BaseModel):
    risk_score: Optional[float]
    confidence: Optional[float]
    why_suspicious: Optional[str]
    evidence: ExplanationEvidence
    uncertainties: List[str]
    source_records: List[EvidenceItem]


# ── Hidden Links ──────────────────────────────────────────────────────────────

class HiddenLinkResult(BaseModel):
    rank: int
    entity_type: str
    entity_id: str
    relationship_type: str
    confidence: float
    risk_score: float
    explanation: str
    supporting_evidence: List[str]


class HiddenLinksResponse(BaseModel):
    target_type: str
    target_id: str
    results: List[HiddenLinkResult]


# ── Network Graph ─────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    risk_score: Optional[float] = 0.0


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship_type: str
    confidence: Optional[float] = 0.0
    risk_score: Optional[float] = 0.0


class NetworkResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# ── Timeline ──────────────────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    date: Optional[Any]
    event_type: str
    title: str
    description: str
    related_entity: Optional[str]
    source: str


class TimelineResponse(BaseModel):
    target_type: str
    target_id: str
    events: List[TimelineEvent]


# ── Investigation Brief ───────────────────────────────────────────────────────

class InvestigationBrief(BaseModel):
    case_title: str
    threat_level: str
    target_type: str
    target_id: str
    risk_score: Optional[float]
    confidence: Optional[float]
    key_evidence: List[str]
    related_incidents: List[str]
    actors: List[str]
    routes: List[str]
    linguistic_signals: List[str]
    animal_signals: List[str]
    explanation: str
    uncertainties: List[str]
    investigation_priority: str


# ── Message Analysis ──────────────────────────────────────────────────────────

class MessageAnalyzeRequest(BaseModel):
    sender: str
    receiver: str
    message: str
    timestamp: Optional[str] = None


class MessageAnalyzeResponse(BaseModel):
    linguistic_risk: float
    confidence: float
    detected_terms: List[str]
    possible_location: Optional[str]
    possible_route: Optional[str]
    indicators: List[str]
    explanation: str


class MessageLinkRequest(BaseModel):
    message_id: str
    target_type: str
    target_id: str


class MessageLinkResponse(BaseModel):
    signal_id: str
    message_id: str
    target_type: str
    target_id: str
    linguistic_risk: float
    status: str


class MessageMapContext(BaseModel):
    message_id: str
    referenced_location: Optional[str]
    linked_route: Optional[str]
    nearby_incidents: List[Dict[str, Any]]
    nearby_alerts: List[Dict[str, Any]]
    local_risk: float
    relevant_entities: List[Dict[str, Any]]


# ── Search ────────────────────────────────────────────────────────────────────

class SearchResponse(BaseModel):
    incidents: List[Dict[str, Any]]
    actors: List[Dict[str, Any]]
    routes: List[Dict[str, Any]]
    locations: List[str]
