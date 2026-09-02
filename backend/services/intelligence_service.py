"""
intelligence_service.py
-----------------------
Reads pre-computed intelligence outputs. Does NOT recalculate scores.
"""

from __future__ import annotations
from typing import Optional
from data_loader import AppData

VALID_TYPES = {"INCIDENT", "ACTOR", "ROUTE", "LOCATION"}

KNOWN_SLANG = [
    "brown parcel", "blue bird", "ivory tea", "long horn",
    "after rain", "river crossing", "jungle fruit", "grey stone",
    "forest gift", "night delivery",
]


def _split_pipe(val) -> list[str]:
    if not val or (isinstance(val, float)):
        return []
    return [v.strip() for v in str(val).split("|") if v.strip()]


def get_intelligence(target_type: str, target_id: str, d: AppData) -> Optional[dict]:
    key = f"{target_type.upper()}:{target_id}"
    row = d.intelligence_by_target.get(key)
    if not row:
        return None

    return {
        "target_type": target_type.upper(),
        "target_id": target_id,
        "risk_score": _sf(row.get("risk_score")),
        "intelligence_confidence": _sf(row.get("intelligence_confidence")),
        "investigation_priority": row.get("investigation_priority"),
        "trade_score": _sf(row.get("trade_score")),
        "route_score": _sf(row.get("route_score")),
        "entity_score": _sf(row.get("entity_score")),
        "linguistic_score": _sf(row.get("linguistic_score")),
        "animal_score": _sf(row.get("animal_score")),
        "cross_evidence_alignment": _sf(row.get("cross_evidence_alignment")),
        "evidence_stream_count": _si(row.get("evidence_stream_count")),
        "evidence_streams": _split_pipe(row.get("evidence_streams")),
        "supporting_incidents": _split_pipe(row.get("supporting_incidents")),
        "supporting_routes": _split_pipe(row.get("supporting_routes")),
        "supporting_actors": _split_pipe(row.get("supporting_actors")),
        "explanation": row.get("explanation", ""),
        "uncertainties": _build_uncertainties(row),
    }


def get_explanation(target_type: str, target_id: str, d: AppData) -> Optional[dict]:
    intel = get_intelligence(target_type, target_id, d)
    if not intel:
        return None

    supporting_incs = intel["supporting_incidents"]
    supporting_routes = intel["supporting_routes"]
    supporting_actors = intel["supporting_actors"]

    trade_ev = [
        {"source_file": "incidents.csv", "source_id": iid, "data_type": "TRADE"}
        for iid in supporting_incs[:5]
    ]
    route_ev = [
        {"source_file": "route_intelligence.csv", "source_id": rid, "data_type": "ROUTE"}
        for rid in supporting_routes[:3]
    ]
    entity_ev = [
        {"source_file": "entity_matches.csv", "source_id": aid, "data_type": "ENTITY"}
        for aid in supporting_actors[:3]
    ]

    # linguistic evidence: messages with slang linked to this target's routes/actors
    ling_ev = _build_linguistic_evidence(target_type, target_id, d)

    # animal evidence
    animal_ev = _build_animal_evidence(target_type, target_id, d)

    source_records = trade_ev + route_ev + entity_ev + ling_ev + animal_ev

    why = intel.get("explanation") or (
        f"Intelligence analysis indicates elevated risk for {target_type} {target_id}. "
        "Multiple evidence streams show correlated activity patterns consistent with "
        "wildlife trafficking indicators."
    )

    return {
        "risk_score": intel["risk_score"],
        "confidence": intel["intelligence_confidence"],
        "why_suspicious": why,
        "evidence": {
            "trade": trade_ev,
            "route": route_ev,
            "entity": entity_ev,
            "linguistic": ling_ev,
            "animal": animal_ev,
        },
        "uncertainties": intel["uncertainties"],
        "source_records": source_records,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

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


def _build_uncertainties(row: dict) -> list[str]:
    u = []
    conf = _sf(row.get("intelligence_confidence"))
    if conf < 70:
        u.append("Intelligence confidence below 70% — findings are indicative only.")
    streams = _si(row.get("evidence_stream_count"))
    if streams < 3:
        u.append("Fewer than 3 corroborating evidence streams — additional signals needed.")
    animal = _sf(row.get("animal_score"))
    if animal == 0.0:
        u.append("No direct animal movement signal detected for this target.")
    ling = _sf(row.get("linguistic_score"))
    if ling == 0.0:
        u.append("No linguistic indicator detected in associated communications.")
    if not u:
        u.append("All evidence streams active. Standard intelligence uncertainty applies.")
    return u


def _build_linguistic_evidence(target_type: str, target_id: str, d: AppData) -> list[dict]:
    ev = []
    msgs: list[dict] = []
    if target_type == "ACTOR":
        msgs = d.messages_by_actor.get(target_id, [])
    elif target_type == "ROUTE":
        msgs = d.messages_by_route.get(target_id, [])
    elif target_type == "INCIDENT":
        inc = d.incident_by_id.get(target_id, {})
        actor = inc.get("lead_actor")
        if actor:
            msgs = d.messages_by_actor.get(str(actor), [])
    elif target_type == "LOCATION":
        if not d.incidents.empty:
            mask = (
                (d.incidents.get("source_location", d.incidents.iloc[:, 0]) == target_id) |
                (d.incidents.get("destination", d.incidents.iloc[:, 0]) == target_id)
            )
            # safe approach
            if "source_location" in d.incidents.columns and "destination" in d.incidents.columns:
                actors = set(
                    d.incidents.loc[
                        (d.incidents["source_location"] == target_id) |
                        (d.incidents["destination"] == target_id),
                        "lead_actor"
                    ].dropna().tolist()
                )
                for a in actors:
                    msgs.extend(d.messages_by_actor.get(str(a), []))

    slang_msgs = [m for m in msgs if str(m.get("contains_slang", "")).lower() == "true"]
    for m in slang_msgs[:5]:
        ev.append({
            "source_file": "messages.csv",
            "source_id": str(m.get("message_id", "")),
            "data_type": "LINGUISTIC",
            "detail": "Potential coded terminology detected in message.",
        })
    return ev


def _build_animal_evidence(target_type: str, target_id: str, d: AppData) -> list[dict]:
    ev = []
    if d.animal_events.empty:
        return ev

    # find lat/lon range for the target
    lats = []
    lons = []
    if target_type == "INCIDENT":
        inc = d.incident_by_id.get(target_id, {})
        lat = inc.get("latitude")
        lon = inc.get("longitude")
        if lat and lon:
            lats, lons = [float(lat)], [float(lon)]
    elif target_type == "ROUTE":
        route_incs = d.incidents_by_route.get(target_id, [])
        lats = [float(r["latitude"]) for r in route_incs if r.get("latitude")]
        lons = [float(r["longitude"]) for r in route_incs if r.get("longitude")]

    if not lats:
        return ev

    lat_min, lat_max = min(lats) - 2, max(lats) + 2
    lon_min, lon_max = min(lons) - 2, max(lons) + 2

    nearby = d.animal_events[
        (d.animal_events["latitude"].between(lat_min, lat_max)) &
        (d.animal_events["longitude"].between(lon_min, lon_max))
    ] if "latitude" in d.animal_events.columns else d.animal_events.iloc[0:0]

    for _, ae in nearby.head(3).iterrows():
        ev.append({
            "source_file": "animal_events.csv",
            "source_id": str(ae.get("event_id", "")),
            "data_type": "ANIMAL_SIGNAL",
            "detail": f"Anomalous movement in {ae.get('protected_area', 'unknown area')} (score {ae.get('anomaly_score', 0):.2f}).",
        })
    return ev
