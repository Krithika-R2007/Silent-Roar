"""
map_service.py
--------------
Builds frontend-ready geographic intelligence layer from in-memory data.
"""

from __future__ import annotations
import math
from data_loader import AppData


def _sf(v, default=0.0) -> float:
    try:
        f = float(v)
        return default if math.isnan(f) else round(f, 2)
    except Exception:
        return default


def get_map(d: AppData) -> dict:
    points = []
    seen_ids: set[str] = set()

    # ── Incidents with lat/lon ────────────────────────────────────────────
    if not d.incidents.empty:
        for inc in d.incidents.to_dict("records"):
            lat = _sf(inc.get("latitude"))
            lon = _sf(inc.get("longitude"))
            if lat == 0.0 and lon == 0.0:
                continue
            inc_id = str(inc.get("incident_id", ""))
            seen_ids.add(inc_id)
            # count related alerts
            alert_count = len(d.alerts_by_entity.get(inc_id, []))
            points.append({
                "id": inc_id,
                "type": "INCIDENT",
                "latitude": lat,
                "longitude": lon,
                "name": f"{inc.get('species','?')} – {inc.get('source_location','?')}",
                "risk_score": None,
                "priority": None,
                "related_count": alert_count,
            })

    # ── Pattern alerts with lat/lon ───────────────────────────────────────
    if not d.pattern_alerts.empty:
        for alt in d.pattern_alerts.to_dict("records"):
            # Alerts are linked to entities; resolve lat/lon from incident if entity is incident
            eid = str(alt.get("entity_id", ""))
            etype = str(alt.get("entity_type", ""))
            lat = lon = None

            if etype == "INCIDENT" and eid in d.incident_by_id:
                inc = d.incident_by_id[eid]
                lat = _sf(inc.get("latitude"))
                lon = _sf(inc.get("longitude"))
            elif etype == "ROUTE":
                route_incs = d.incidents_by_route.get(eid, [])
                lats = [_sf(r.get("latitude")) for r in route_incs if _sf(r.get("latitude"))]
                lons = [_sf(r.get("longitude")) for r in route_incs if _sf(r.get("longitude"))]
                if lats:
                    lat = sum(lats) / len(lats)
                    lon = sum(lons) / len(lons)

            if lat is None or (lat == 0.0 and lon == 0.0):
                continue

            alt_id = str(alt.get("alert_id", ""))
            if alt_id in seen_ids:
                continue
            seen_ids.add(alt_id)
            points.append({
                "id": alt_id,
                "type": "ALERT",
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "name": f"{alt.get('pattern_type','?')} – {eid}",
                "risk_score": _sf(alt.get("risk_score")),
                "priority": alt.get("priority"),
                "related_count": _si(alt.get("incident_count")),
            })

    # ── Animal events ─────────────────────────────────────────────────────
    if not d.animal_events.empty:
        for ae in d.animal_events.to_dict("records"):
            lat = _sf(ae.get("latitude"))
            lon = _sf(ae.get("longitude"))
            if lat == 0.0 and lon == 0.0:
                continue
            eid = str(ae.get("event_id", ""))
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            points.append({
                "id": eid,
                "type": "ANIMAL_SIGNAL",
                "latitude": lat,
                "longitude": lon,
                "name": f"{ae.get('protected_area','?')} – anomaly {_sf(ae.get('anomaly_score')):.2f}",
                "risk_score": _sf(ae.get("anomaly_score")) * 100,
                "priority": "WATCH" if _sf(ae.get("anomaly_score")) > 0.5 else None,
                "related_count": 0,
            })

    # ── Route lines ───────────────────────────────────────────────────────
    route_lines = []
    if not d.route_intelligence.empty:
        for ri in d.route_intelligence.to_dict("records"):
            route_lines.append({
                "route_id": str(ri.get("route_id", "")),
                "source": ri.get("source"),
                "transit": ri.get("transit"),
                "destination": ri.get("destination"),
                "risk_score": _sf(ri.get("route_risk_score")),
            })
    elif not d.routes.empty:
        for r in d.routes.to_dict("records"):
            route_lines.append({
                "route_id": str(r.get("route_id", "")),
                "source": r.get("source"),
                "transit": r.get("transit"),
                "destination": r.get("destination"),
                "risk_score": _sf(r.get("historical_risk")),
            })

    return {"points": points, "routes": route_lines}


def _si(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default
