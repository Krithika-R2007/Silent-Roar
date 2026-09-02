"""
investigation_service.py
------------------------
Builds a structured investigation brief using deterministic templates.
No external AI API required — works fully offline.
"""

from __future__ import annotations
import math
from typing import Optional
from data_loader import AppData


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


THREAT_LABELS = {
    "IMMEDIATE": "CRITICAL",
    "HIGH":      "HIGH",
    "MEDIUM":    "MODERATE",
    "LOW":       "LOW",
}


def get_investigation_brief(target_type: str, target_id: str, d: AppData) -> Optional[dict]:
    key = f"{target_type.upper()}:{target_id}"
    intel = d.intelligence_by_target.get(key)

    # Resolve basic metadata
    case_title, entity_name = _resolve_title(target_type, target_id, d, intel)

    risk_score  = _sf(intel.get("risk_score")) if intel else 0.0
    confidence  = _sf(intel.get("intelligence_confidence")) if intel else 0.0
    priority    = intel.get("investigation_priority", "MEDIUM") if intel else "MEDIUM"
    threat_level = THREAT_LABELS.get(priority, "MODERATE")

    supporting_incs    = _split_pipe(intel.get("supporting_incidents")) if intel else []
    supporting_routes  = _split_pipe(intel.get("supporting_routes"))    if intel else []
    supporting_actors  = _split_pipe(intel.get("supporting_actors"))    if intel else []

    # Key evidence bullets
    key_evidence = _build_key_evidence(
        target_type, target_id, intel, risk_score, confidence, d,
        supporting_incs, supporting_routes, supporting_actors
    )

    # Linguistic signals
    ling_signals = _collect_linguistic_signals(target_type, target_id, d)

    # Animal signals
    animal_signals = _collect_animal_signals(target_type, target_id, d)

    # Explanation text
    explanation = intel.get("explanation", "") if intel else ""
    if not explanation:
        explanation = _default_explanation(target_type, target_id, risk_score, confidence, len(supporting_incs))

    # Uncertainties
    uncertainties = _build_uncertainties(intel, risk_score, confidence)

    return {
        "case_title": case_title,
        "threat_level": threat_level,
        "target_type": target_type.upper(),
        "target_id": target_id,
        "risk_score": risk_score,
        "confidence": confidence,
        "key_evidence": key_evidence,
        "related_incidents": supporting_incs[:10],
        "actors": supporting_actors[:10],
        "routes": supporting_routes[:5],
        "linguistic_signals": ling_signals,
        "animal_signals": animal_signals,
        "explanation": explanation,
        "uncertainties": uncertainties,
        "investigation_priority": priority,
    }


def _resolve_title(target_type: str, target_id: str, d: AppData, intel) -> tuple[str, str]:
    if target_type == "ACTOR":
        actor = d.actor_by_id.get(target_id, {})
        name  = actor.get("full_name", target_id)
        title = f"Actor Intelligence Brief — {name}"
        return title, name
    if target_type == "ROUTE":
        route = d.route_by_id.get(target_id, {})
        src   = route.get("source", "?")
        dst   = route.get("destination", "?")
        name  = f"{src} → {dst}"
        title = f"Route Intelligence Brief — {name}"
        return title, name
    if target_type == "INCIDENT":
        inc   = d.incident_by_id.get(target_id, {})
        name  = f"{inc.get('species','?')} incident at {inc.get('source_location','?')}"
        title = f"Incident Intelligence Brief — {target_id}"
        return title, name
    # LOCATION
    title = f"Location Intelligence Brief — {target_id}"
    return title, target_id


def _build_key_evidence(
    target_type, target_id, intel, risk_score, confidence, d,
    incs, routes, actors
) -> list[str]:
    ev = []
    if incs:
        ev.append(f"{len(incs)} supporting incident(s) identified across intelligence streams.")
    if actors:
        ev.append(f"{len(actors)} actor(s) potentially associated based on intelligence analysis.")
    if routes:
        ev.append(f"Activity observed across {len(routes)} trafficking corridor(s).")

    streams = _split_pipe(intel.get("evidence_streams")) if intel else []
    if "LINGUISTIC" in streams:
        ev.append("Coded communication signals detected in associated message traffic.")
    if "ANIMAL" in streams:
        ev.append("Correlated animal movement anomalies observed in proximity to target area.")
    if "ENTITY" in streams:
        ev.append("Entity resolution analysis indicates possible identity overlap or alias usage.")

    if risk_score >= 80:
        ev.append(f"Risk score {risk_score:.0f}/100 — immediate investigative attention recommended.")
    elif risk_score >= 65:
        ev.append(f"Risk score {risk_score:.0f}/100 — elevated risk profile warrants active monitoring.")
    else:
        ev.append(f"Risk score {risk_score:.0f}/100 — flagged for intelligence monitoring.")

    return ev


def _collect_linguistic_signals(target_type: str, target_id: str, d: AppData) -> list[str]:
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

    slang_msgs = [m for m in msgs if str(m.get("contains_slang", "")).lower() == "true"]
    signals = []
    for m in slang_msgs[:5]:
        signals.append(
            f"Message {m.get('message_id','?')}: potential coded terminology in group "
            f"{m.get('chat_group','?')} — intelligence indicator, not confirmed."
        )
    return signals


def _collect_animal_signals(target_type: str, target_id: str, d: AppData) -> list[str]:
    signals = []
    if d.animal_events.empty:
        return signals
    # Just report high-anomaly events generically per area
    high_anomaly = d.animal_events[
        d.animal_events["anomaly_score"] >= 0.5
    ] if "anomaly_score" in d.animal_events.columns else d.animal_events.iloc[0:0]
    for _, ae in high_anomaly.head(3).iterrows():
        signals.append(
            f"Anomalous animal movement in {ae.get('protected_area','?')} "
            f"on {str(ae.get('event_date','?'))[:10]} (anomaly score {ae.get('anomaly_score',0):.2f})."
        )
    return signals


def _default_explanation(target_type, target_id, risk_score, confidence, inc_count) -> str:
    return (
        f"Intelligence analysis for {target_type} {target_id} indicates a risk score of "
        f"{risk_score:.0f}/100 with {confidence:.0f}% confidence, based on {inc_count} "
        "supporting incident(s). Multiple evidence streams have been evaluated. "
        "All findings represent intelligence signals and potential associations — "
        "not confirmed evidence of criminal activity."
    )


def _build_uncertainties(intel, risk_score, confidence) -> list[str]:
    u = []
    if confidence < 70:
        u.append("Intelligence confidence is below 70%. Additional corroboration recommended.")
    if risk_score < 65:
        u.append("Risk score below HIGH threshold. Monitor rather than action at this stage.")
    if intel:
        streams = _split_pipe(intel.get("evidence_streams"))
        if len(streams) < 3:
            u.append("Fewer than three independent evidence streams. Findings are indicative only.")
        if "ANIMAL" not in streams:
            u.append("No direct animal movement corroboration available for this target.")
    else:
        u.append("No pre-computed intelligence record found. Signals are derived from raw data only.")
    if not u:
        u.append("Standard intelligence uncertainty applies. All data is simulated for prototype purposes.")
    return u
