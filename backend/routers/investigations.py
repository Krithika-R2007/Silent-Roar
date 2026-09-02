"""
routers/investigations.py
"""

from __future__ import annotations
import math
from fastapi import APIRouter, HTTPException
from schemas import InvestigationBrief
from data_loader import get_data
from services.investigation_service import get_investigation_brief

router = APIRouter(prefix="/api/investigation", tags=["Investigations"])

VALID_TARGET_TYPES = {"INCIDENT", "ACTOR", "ROUTE", "LOCATION"}


# ── /api/investigation/all ────────────────────────────────────────────────────

@router.get(
    "/all",
    summary="List all investigations derived from intelligence records",
)
def list_all_investigations():
    """
    Returns a list of investigation objects built from the pre-computed
    intelligence scores. Each row becomes one investigation card in the UI.
    """
    d = get_data()
    results = []

    if d.intelligence_scores.empty:
        return results

    for _, row in d.intelligence_scores.iterrows():
        target_type = str(row.get("target_type", "ROUTE")).upper()
        target_id   = str(row.get("target_id", ""))
        risk_score  = _sf(row.get("risk_score"))
        confidence  = _sf(row.get("intelligence_confidence"))
        priority    = str(row.get("investigation_priority", "MEDIUM"))
        explanation = str(row.get("explanation", ""))

        # Derive a readable codename
        codename = _make_codename(target_type, target_id, d)

        # Collect linked entity / incident IDs
        inc_ids   = _split_pipe(row.get("supporting_incidents"))
        actor_ids = _split_pipe(row.get("supporting_actors"))
        route_ids = _split_pipe(row.get("supporting_routes"))

        status = "ACTIVE" if risk_score >= 60 else "MONITORING"

        results.append({
            "id":               target_id,
            "codename":         codename,
            "target_type":      target_type,
            "target_id":        target_id,
            "riskScore":        risk_score,
            "risk_score":       risk_score,
            "confidence":       confidence,
            "status":           status,
            "lastUpdated":      "Recently",
            "threatSummary":    explanation[:200] if explanation else f"{target_type} {target_id} — intelligence signal detected.",
            "explanation":      explanation,
            "primaryCommodity": _infer_commodity(inc_ids, d),
            "originCountry":    _infer_origin(inc_ids, d),
            "incidentIds":      inc_ids[:20],
            "entityIds":        actor_ids[:20],
            "routeIds":         route_ids[:10],
            "evidenceIds":      [],
            "investigation_priority": priority,
        })

    # Sort by risk score descending
    results.sort(key=lambda x: x["riskScore"], reverse=True)
    return results


# ── /api/investigation/details/{target_id} ────────────────────────────────────

@router.get(
    "/details/{target_id}",
    summary="Full investigation detail by target ID",
)
def investigation_details(target_id: str):
    """
    Returns a full investigation detail object. Tries ROUTE first, then
    ACTOR, INCIDENT, and LOCATION until it finds an intelligence record.
    """
    d = get_data()

    for target_type in ("ROUTE", "ACTOR", "INCIDENT", "LOCATION"):
        brief = get_investigation_brief(target_type, target_id, d)
        if brief:
            # Enrich with list-format fields the frontend expects
            brief["id"]          = target_id
            brief["codename"]    = brief.get("case_title", f"Investigation {target_id}")
            brief["riskScore"]   = brief.get("risk_score", 0)
            brief["status"]      = "ACTIVE"
            brief["lastUpdated"] = "Recently"
            brief["threatSummary"] = brief.get("explanation", "")
            brief["primaryCommodity"] = _infer_commodity(brief.get("related_incidents", []), d)
            brief["originCountry"]    = _infer_origin(brief.get("related_incidents", []), d)
            brief["incidentIds"]  = brief.get("related_incidents", [])
            brief["entityIds"]    = brief.get("actors", [])
            brief["routeIds"]     = brief.get("routes", [])
            brief["evidenceIds"]  = []
            return brief

    raise HTTPException(status_code=404, detail={
        "error":   True,
        "message": f"No investigation record found for ID '{target_id}'",
        "code":    "INVESTIGATION_NOT_FOUND",
    })


# ── /api/investigation/{target_type}/{target_id} ──────────────────────────────

@router.get(
    "/{target_type}/{target_id}",
    response_model=InvestigationBrief,
    summary="Structured investigation brief",
    description=(
        "Returns a deterministic offline investigation brief for the target. "
        "No external AI API required. Uses pre-computed intelligence outputs."
    ),
)
def investigation_brief(target_type: str, target_id: str):
    if target_type.upper() not in VALID_TARGET_TYPES:
        raise HTTPException(status_code=400, detail={
            "error": True,
            "message": f"Invalid target type '{target_type}'. Use: INCIDENT, ACTOR, ROUTE, LOCATION",
            "code": "INVALID_TARGET_TYPE",
        })
    d = get_data()
    brief = get_investigation_brief(target_type.upper(), target_id, d)
    if not brief:
        raise HTTPException(status_code=404, detail={
            "error": True,
            "message": f"{target_type} {target_id} not found",
            "code": "TARGET_NOT_FOUND",
        })
    return brief


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sf(v, default=0.0) -> float:
    try:
        f = float(v)
        return default if math.isnan(f) else round(f, 2)
    except Exception:
        return default


def _split_pipe(val) -> list[str]:
    if not val or (isinstance(val, float)):
        return []
    return [v.strip() for v in str(val).split("|") if v.strip()]


def _make_codename(target_type: str, target_id: str, d) -> str:
    if target_type == "ROUTE":
        route = d.route_by_id.get(target_id, {})
        src = route.get("source", "")
        dst = route.get("destination", "")
        if src and dst:
            return f"{src} → {dst} Corridor"
    if target_type == "ACTOR":
        actor = d.actor_by_id.get(target_id, {})
        name = actor.get("full_name", "")
        if name:
            return f"Actor Network — {name}"
    if target_type == "INCIDENT":
        inc = d.incident_by_id.get(target_id, {})
        species = inc.get("species", "")
        loc = inc.get("source_location", "")
        if species:
            return f"{species} Incident — {loc}"
    return f"Investigation {target_id}"


def _infer_commodity(inc_ids: list[str], d) -> str:
    species_counts: dict[str, int] = {}
    for iid in inc_ids[:10]:
        inc = d.incident_by_id.get(iid, {})
        sp = inc.get("species", "")
        if sp:
            species_counts[sp] = species_counts.get(sp, 0) + 1
    if species_counts:
        return max(species_counts, key=species_counts.get)
    return "Various"


def _infer_origin(inc_ids: list[str], d) -> str:
    locs: list[str] = []
    for iid in inc_ids[:10]:
        inc = d.incident_by_id.get(iid, {})
        loc = inc.get("source_location", "")
        if loc:
            locs.append(loc)
    if locs:
        return locs[0]
    return "Multiple"
