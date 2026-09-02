"""
routers/network.py
"""

from fastapi import APIRouter, HTTPException, Query
from schemas import NetworkResponse, HiddenLinksResponse, TimelineResponse
from data_loader import get_data
from services.network_service import get_hidden_links, get_network

router = APIRouter(tags=["Network"])

VALID_TARGET_TYPES = {"INCIDENT", "ACTOR", "ROUTE", "LOCATION"}


@router.get(
    "/api/hidden-links/{target_type}/{target_id}",
    response_model=HiddenLinksResponse,
    summary="Discover hidden links for a target",
)
def hidden_links(
    target_type: str,
    target_id: str,
    max_depth: int = Query(2, ge=1, le=3),
    limit: int = Query(10, ge=1, le=50),
):
    if target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{target_type}'",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    return get_hidden_links(target_type.upper(), target_id, d, max_depth=max_depth, limit=limit)


@router.get(
    "/api/network/{target_type}/{target_id}",
    response_model=NetworkResponse,
    summary="Local network graph for a target",
)
def network_graph(
    target_type: str,
    target_id: str,
    max_depth: int = Query(2, ge=1, le=3),
    max_nodes: int = Query(50, ge=5, le=200),
):
    if target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{target_type}'",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    result = get_network(target_type.upper(), target_id, d, max_depth=max_depth, max_nodes=max_nodes)
    if not result["nodes"]:
        raise HTTPException(status_code=404, detail={
            "error": True, "message": "No network data found for target", "code": "NETWORK_NOT_FOUND"
        })
    return result


@router.get(
    "/api/timeline/{target_type}/{target_id}",
    response_model=TimelineResponse,
    summary="Chronological timeline for a target",
)
def get_timeline(target_type: str, target_id: str):
    if target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{target_type}'",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    events = _build_timeline(target_type.upper(), target_id, d)
    return {
        "target_type": target_type.upper(),
        "target_id": target_id,
        "events": events,
    }


def _build_timeline(target_type: str, target_id: str, d) -> list[dict]:
    events = []

    if target_type == "INCIDENT":
        inc = d.incident_by_id.get(target_id, {})
        if inc:
            events.append({
                "date": str(inc.get("incident_date", "")),
                "event_type": "INCIDENT",
                "title": f"{inc.get('species', '?')} incident",
                "description": f"Commodity: {inc.get('commodity','?')}, Qty: {inc.get('quantity','?')}, "
                               f"Seizure: {inc.get('seizure_status','?')}",
                "related_entity": target_id,
                "source": "incidents.csv",
            })
        for s in d.shipments_by_incident.get(target_id, []):
            events.append({
                "date": str(s.get("departure_date", "")),
                "event_type": "SHIPMENT",
                "title": f"Shipment {str(s.get('shipment_id',''))[-6:]}",
                "description": f"Transport: {s.get('transport_type','?')}, Status: {s.get('status','?')}",
                "related_entity": str(s.get("shipment_id", "")),
                "source": "shipments.csv",
            })

    elif target_type == "ACTOR":
        for inc in d.incidents_by_actor.get(target_id, []):
            events.append({
                "date": str(inc.get("incident_date", "")),
                "event_type": "INCIDENT",
                "title": f"{inc.get('species','?')} incident at {inc.get('source_location','?')}",
                "description": f"Route: {inc.get('route_id','?')}, Seizure: {inc.get('seizure_status','?')}",
                "related_entity": str(inc.get("incident_id", "")),
                "source": "incidents.csv",
            })
        for msg in d.messages_by_actor.get(target_id, []):
            events.append({
                "date": str(msg.get("timestamp", "")),
                "event_type": "MESSAGE",
                "title": f"Message in {msg.get('chat_group','?')}",
                "description": f"Slang: {msg.get('contains_slang','?')}, Route link: {msg.get('linked_route','none')}",
                "related_entity": str(msg.get("message_id", "")),
                "source": "messages.csv",
            })

    elif target_type == "ROUTE":
        for inc in d.incidents_by_route.get(target_id, []):
            events.append({
                "date": str(inc.get("incident_date", "")),
                "event_type": "ROUTE_ACTIVITY",
                "title": f"{inc.get('species','?')} incident on route",
                "description": f"Actor: {inc.get('lead_actor','?')}, Seizure: {inc.get('seizure_status','?')}",
                "related_entity": str(inc.get("incident_id", "")),
                "source": "incidents.csv",
            })
        for msg in d.messages_by_route.get(target_id, []):
            events.append({
                "date": str(msg.get("timestamp", "")),
                "event_type": "MESSAGE",
                "title": f"Linked message in {msg.get('chat_group','?')}",
                "description": f"Slang detected: {msg.get('contains_slang','?')}",
                "related_entity": str(msg.get("message_id", "")),
                "source": "messages.csv",
            })
        for alt in d.alerts_by_entity.get(target_id, []):
            events.append({
                "date": str(alt.get("first_detected", "")),
                "event_type": "ALERT",
                "title": str(alt.get("pattern_type", "Alert")),
                "description": str(alt.get("explanation", ""))[:120],
                "related_entity": str(alt.get("alert_id", "")),
                "source": "pattern_alerts.csv",
            })

    elif target_type == "LOCATION":
        if not d.incidents.empty and "source_location" in d.incidents.columns:
            loc_incs = d.incidents[
                (d.incidents["source_location"] == target_id) |
                (d.incidents["destination"] == target_id)
            ]
            for _, inc in loc_incs.iterrows():
                events.append({
                    "date": str(inc.get("incident_date", "")),
                    "event_type": "INCIDENT",
                    "title": f"{inc.get('species','?')} incident",
                    "description": f"Route: {inc.get('route_id','?')}, Actor: {inc.get('lead_actor','?')}",
                    "related_entity": str(inc.get("incident_id", "")),
                    "source": "incidents.csv",
                })

    # Add animal events (for all types — proximity check omitted for speed)
    if not d.animal_events.empty:
        for _, ae in d.animal_events.head(3).iterrows():
            events.append({
                "date": str(ae.get("event_date", "")),
                "event_type": "ANIMAL_SIGNAL",
                "title": f"Animal movement anomaly: {ae.get('protected_area','?')}",
                "description": f"Anomaly score: {ae.get('anomaly_score',0):.2f}",
                "related_entity": str(ae.get("event_id", "")),
                "source": "animal_events.csv",
            })

    events.sort(key=lambda x: str(x.get("date", "")))
    return events
