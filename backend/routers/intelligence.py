"""
routers/intelligence.py
"""

from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from schemas import (
    AlertListResponse, AlertItem, MapResponse,
    IntelligenceResponse, ExplanationResponse,
    IncidentListResponse, IncidentSummary,
    ActorListResponse, ActorSummary,
    RouteListResponse, RouteSummary,
    SearchResponse,
)
from data_loader import get_data
from services.intelligence_service import get_intelligence, get_explanation, VALID_TYPES

router = APIRouter(tags=["Intelligence"])

VALID_TARGET_TYPES = {"INCIDENT", "ACTOR", "ROUTE", "LOCATION"}


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get(
    "/api/alerts",
    response_model=AlertListResponse,
    summary="List investigation-relevant alerts",
)
def list_alerts(
    priority: Optional[str] = Query(None, description="CRITICAL | HIGH | WATCH | LOW"),
    pattern_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    d = get_data()
    if d.pattern_alerts.empty:
        return {"total": 0, "alerts": []}

    alerts = d.pattern_alerts.to_dict("records")

    if priority:
        alerts = [a for a in alerts if str(a.get("priority", "")).upper() == priority.upper()]
    if pattern_type:
        alerts = [a for a in alerts if str(a.get("pattern_type", "")).upper() == pattern_type.upper()]

    # default sort: risk_score descending
    alerts.sort(key=lambda x: float(x.get("risk_score") or 0), reverse=True)

    total = len(alerts)
    page  = alerts[offset: offset + limit]

    return {
        "total": total,
        "alerts": [
            AlertItem(
                alert_id=str(a.get("alert_id", "")),
                title=str(a.get("explanation", ""))[:80] or str(a.get("pattern_type", "")),
                pattern_type=a.get("pattern_type"),
                entity_type=a.get("entity_type"),
                entity_id=a.get("entity_id"),
                priority=a.get("priority"),
                risk_score=_sf(a.get("risk_score")),
                confidence=_sf(a.get("confidence")),
                explanation=a.get("explanation"),
                first_detected=str(a.get("first_detected", "")) or None,
                last_detected=str(a.get("last_detected", "")) or None,
            )
            for a in page
        ],
    }


# ── Map ───────────────────────────────────────────────────────────────────────

@router.get("/api/map", response_model=MapResponse, summary="Geographic intelligence layer")
def get_map():
    from services.map_service import get_map as _get_map
    d = get_data()
    return _get_map(d)


# ── Incidents ─────────────────────────────────────────────────────────────────

@router.get("/api/incidents", response_model=IncidentListResponse, summary="List incidents")
def list_incidents(
    search: Optional[str] = Query(None),
    species: Optional[str] = Query(None),
    route_id: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None, description="high | medium | low"),
    date_from: Optional[str] = Query(None),
    date_to:   Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    d = get_data()
    items = d._incident_search[:]

    if search:
        q = search.lower()
        items = [i for i in items if q in i["_search"]]
    if species:
        sp = species.lower()
        items = [i for i in items if sp in str(i.get("species", "")).lower()]
    if route_id:
        items = [i for i in items if str(i.get("route_id", "")) == route_id]
    if date_from:
        items = [i for i in items if str(i.get("incident_date", "")) >= date_from]
    if date_to:
        items = [i for i in items if str(i.get("incident_date", "")) <= date_to]

    total = len(items)
    page  = items[offset: offset + limit]

    return {
        "total": total,
        "incidents": [_to_incident_summary(r) for r in page],
    }


@router.get("/api/incidents/{incident_id}", summary="Incident detail")
def get_incident(incident_id: str):
    d = get_data()
    inc = d.incident_by_id.get(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "Incident not found", "code": "INCIDENT_NOT_FOUND"
        })

    actor_id  = inc.get("lead_actor")
    route_id  = inc.get("route_id")
    actor_row = d.actor_by_id.get(str(actor_id), {}) if actor_id else {}
    route_row = d.route_by_id.get(str(route_id), {}) if route_id else {}
    ri_row    = d.route_intel_by_id.get(str(route_id), {}) if route_id else {}

    intel_key = f"INCIDENT:{incident_id}"
    intel_row = d.intelligence_by_target.get(intel_key, {})
    intel_score = _sf(intel_row.get("risk_score")) if intel_row else None

    hidden = d.hidden_links_by_entity.get(incident_id, [])
    alerts = d.alerts_by_entity.get(incident_id, [])
    shipments = d.shipments_by_incident.get(incident_id, [])

    # Evidence items
    evidence = []
    if actor_row:
        evidence.append({"source_file": "actors.csv", "source_id": str(actor_id), "data_type": "ACTOR"})
    if route_row:
        evidence.append({"source_file": "routes.csv", "source_id": str(route_id), "data_type": "ROUTE"})
    for em in d.entity_matches_by_actor.get(str(actor_id) if actor_id else "", [])[:3]:
        evidence.append({"source_file": "entity_matches.csv", "source_id": str(em.get("actor_1", "")), "data_type": "ENTITY_MATCH"})

    # Timeline
    timeline = _build_incident_timeline(incident_id, inc, shipments, alerts, d)

    return {
        "incident": _to_incident_summary(inc),
        "related_actors": [_clean(actor_row)] if actor_row else [],
        "related_shipments": [_clean(s) for s in shipments],
        "route_info": {**_clean(route_row), **_clean(ri_row)} if route_row else None,
        "related_alerts": [_clean(a) for a in alerts[:5]],
        "intelligence_score": intel_score,
        "supporting_evidence": evidence,
        "hidden_links": [_clean(h) for h in hidden[:5]],
        "timeline": timeline,
    }


# ── Actors ────────────────────────────────────────────────────────────────────

@router.get("/api/actors", response_model=ActorListResponse, summary="List actors")
def list_actors(
    name: Optional[str] = Query(None),
    alias: Optional[str] = Query(None),
    nationality: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    d = get_data()
    items = d._actor_search[:]

    for param, field in ((name, "full_name"), (alias, "alias"), (nationality, "nationality"), (role, "role")):
        if param:
            pq = param.lower()
            items = [i for i in items if pq in str(i.get(field, "")).lower()]

    total = len(items)
    page  = items[offset: offset + limit]
    return {"total": total, "actors": [_to_actor_summary(r) for r in page]}


@router.get("/api/actors/{actor_id}", summary="Actor detail")
def get_actor(actor_id: str):
    d = get_data()
    actor = d.actor_by_id.get(actor_id)
    if not actor:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "Actor not found", "code": "ACTOR_NOT_FOUND"
        })

    incidents   = d.incidents_by_actor.get(actor_id, [])
    route_ids   = list({str(r.get("route_id")) for r in incidents if r.get("route_id")})
    shipments   = d.shipments_by_actor.get(actor_id, [])
    em          = d.entity_matches_by_actor.get(actor_id, [])

    intel_key   = f"ACTOR:{actor_id}"
    intel_row   = d.intelligence_by_target.get(intel_key, {})
    risk_score  = _sf(intel_row.get("risk_score")) if intel_row else _sf(actor.get("threat_score"))
    confidence  = _sf(intel_row.get("intelligence_confidence")) if intel_row else None

    net_stats = {
        "incident_count": len(incidents),
        "route_count": len(route_ids),
        "shipment_count": len(shipments),
        "entity_match_count": len(em),
    }

    return {
        "actor": _to_actor_summary(actor),
        "risk_score": risk_score,
        "confidence": confidence,
        "linked_incidents": [_clean(i) for i in incidents[:10]],
        "routes": route_ids,
        "shipments": [_clean(s) for s in shipments[:10]],
        "entity_matches": [_clean(e) for e in em[:10]],
        "network_statistics": net_stats,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/api/routes", response_model=RouteListResponse, summary="List routes")
def list_routes(limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
    d = get_data()
    items = d._route_search[:]
    total = len(items)
    page  = items[offset: offset + limit]

    results = []
    for r in page:
        rid = str(r.get("route_id", ""))
        ri  = d.route_intel_by_id.get(rid, {})
        incs = d.incidents_by_route.get(rid, [])
        actors = {str(i.get("lead_actor")) for i in incs if i.get("lead_actor")}
        results.append(RouteSummary(
            route_id=rid,
            source=r.get("source"),
            transit=r.get("transit"),
            destination=r.get("destination"),
            risk_score=_sf(ri.get("route_risk_score")) or _sf(r.get("historical_risk")),
            route_status=ri.get("route_status"),
            incident_count=len(incs),
            actor_count=len(actors),
        ))
    return {"total": total, "routes": results}


@router.get("/api/routes/{route_id}", summary="Route detail")
def get_route(route_id: str):
    d = get_data()
    route = d.route_by_id.get(route_id)
    if not route:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "Route not found", "code": "ROUTE_NOT_FOUND"
        })

    ri     = d.route_intel_by_id.get(route_id, {})
    incs   = d.incidents_by_route.get(route_id, [])
    alerts = d.alerts_by_entity.get(route_id, [])
    hlinks = d.hidden_links_by_entity.get(route_id, [])
    actors = list({str(i.get("lead_actor")) for i in incs if i.get("lead_actor")})

    summary = RouteSummary(
        route_id=route_id,
        source=route.get("source"),
        transit=route.get("transit"),
        destination=route.get("destination"),
        risk_score=_sf(ri.get("route_risk_score")) or _sf(route.get("historical_risk")),
        route_status=ri.get("route_status"),
        incident_count=len(incs),
        actor_count=len(actors),
    )

    activity_summary = {
        "total_incidents": len(incs),
        "recent_incidents": _si(ri.get("recent_incidents")),
        "unique_actors": len(actors),
        "unique_species": len({i.get("species") for i in incs if i.get("species")}),
    }

    return {
        "route": summary,
        "risk_score": summary.risk_score,
        "recent_activity": [_clean(i) for i in incs[-5:]],
        "related_incidents": [_clean(i) for i in incs[:10]],
        "recurring_actors": actors[:10],
        "hidden_links": [_clean(h) for h in hlinks[:5]],
        "pattern_alerts": [_clean(a) for a in alerts[:5]],
        "activity_summary": activity_summary,
    }


# ── Intelligence ──────────────────────────────────────────────────────────────

@router.get(
    "/api/intelligence/{target_type}/{target_id}",
    response_model=IntelligenceResponse,
    summary="Intelligence record for a target",
)
def get_intel(target_type: str, target_id: str):
    if target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{target_type}'. Use: INCIDENT, ACTOR, ROUTE, LOCATION",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    result = get_intelligence(target_type.upper(), target_id, d)
    if not result:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "Intelligence record not found", "code": "INTEL_NOT_FOUND"
        })
    return result


@router.get(
    "/api/intelligence/{target_type}/{target_id}/explanation",
    response_model=ExplanationResponse,
    summary="Why is this suspicious?",
)
def get_why_suspicious(target_type: str, target_id: str):
    if target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{target_type}'",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    result = get_explanation(target_type.upper(), target_id, d)
    if not result:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "No explanation record found", "code": "EXPLANATION_NOT_FOUND"
        })
    return result


# ── Search ────────────────────────────────────────────────────────────────────

@router.get("/api/search", response_model=SearchResponse, summary="Cross-entity search")
def search(q: str = Query(..., min_length=1)):
    d = get_data()
    ql = q.lower()

    inc_results = [
        {"incident_id": r.get("incident_id"), "species": r.get("species"),
         "source_location": r.get("source_location"), "destination": r.get("destination")}
        for r in d._incident_search if ql in r["_search"]
    ][:20]

    actor_results = [
        {"actor_id": r.get("actor_id"), "full_name": r.get("full_name"),
         "role": r.get("role"), "nationality": r.get("nationality")}
        for r in d._actor_search if ql in r["_search"]
    ][:20]

    route_results = [
        {"route_id": r.get("route_id"), "source": r.get("source"),
         "destination": r.get("destination"), "corridor": r.get("corridor")}
        for r in d._route_search if ql in r["_search"]
    ][:20]

    loc_results = [loc for loc in d._locations if ql in loc.lower()][:20]

    return {
        "incidents": inc_results,
        "actors": actor_results,
        "routes": route_results,
        "locations": loc_results,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sf(v, default=0.0) -> float:
    try:
        import math
        f = float(v)
        return default if math.isnan(f) else round(f, 2)
    except Exception:
        return default


def _si(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def _clean(row: dict) -> dict:
    """Remove pandas Timestamp objects and NaN values for JSON serialisation."""
    import pandas as pd
    result = {}
    for k, v in row.items():
        if k.startswith("_"):
            continue
        if isinstance(v, float) and (v != v):  # NaN check
            result[k] = None
        elif hasattr(v, "isoformat"):
            result[k] = v.isoformat()
        elif isinstance(v, pd.Timestamp):
            result[k] = v.isoformat() if not pd.isna(v) else None
        else:
            result[k] = v
    return result


def _to_incident_summary(r: dict) -> IncidentSummary:
    return IncidentSummary(
        incident_id=str(r.get("incident_id", "")),
        incident_date=str(r.get("incident_date", "")) or None,
        species=r.get("species"),
        commodity=r.get("commodity"),
        quantity=_sf(r.get("quantity")) or None,
        source_location=r.get("source_location"),
        destination=r.get("destination"),
        route_id=r.get("route_id"),
        lead_actor=r.get("lead_actor"),
        seizure_status=r.get("seizure_status"),
        latitude=_sf(r.get("latitude")) or None,
        longitude=_sf(r.get("longitude")) or None,
    )


def _to_actor_summary(r: dict) -> ActorSummary:
    return ActorSummary(
        actor_id=str(r.get("actor_id", "")),
        full_name=r.get("full_name"),
        alias=r.get("alias"),
        nationality=r.get("nationality"),
        role=r.get("role"),
        primary_region=r.get("primary_region"),
        threat_score=_sf(r.get("threat_score")) or None,
    )


def _build_incident_timeline(inc_id: str, inc: dict, shipments, alerts, d) -> list[dict]:
    events = []

    # The incident itself
    events.append({
        "date": str(inc.get("incident_date", "")),
        "event_type": "INCIDENT",
        "title": f"{inc.get('species', '?')} incident",
        "description": f"{inc.get('commodity', '?')} at {inc.get('source_location', '?')}, seizure: {inc.get('seizure_status', '?')}",
        "related_entity": inc_id,
        "source": "incidents.csv",
    })

    # Shipments
    for s in shipments:
        events.append({
            "date": str(s.get("departure_date", "")),
            "event_type": "SHIPMENT",
            "title": f"Shipment {s.get('shipment_id', '')[-6:]}",
            "description": f"{s.get('transport_type', '?')} shipment, status: {s.get('status', '?')}",
            "related_entity": str(s.get("shipment_id", "")),
            "source": "shipments.csv",
        })

    # Alerts
    for a in alerts[:3]:
        events.append({
            "date": str(a.get("first_detected", "")),
            "event_type": "ALERT",
            "title": str(a.get("pattern_type", "Alert")),
            "description": str(a.get("explanation", ""))[:120],
            "related_entity": str(a.get("alert_id", "")),
            "source": "pattern_alerts.csv",
        })

    # Sort by date
    events.sort(key=lambda x: str(x.get("date", "")))
    return events
