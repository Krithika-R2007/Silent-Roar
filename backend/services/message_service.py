"""
message_service.py
------------------
Linguistic analysis and message → investigation linking.
Uses the same KNOWN_SLANG list as the original intelligence engine.
Does NOT claim that keywords prove trafficking — contextual language only.
"""

from __future__ import annotations
import json
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from data_loader import AppData
from models import LinguisticSignal

KNOWN_SLANG = [
    "brown parcel", "blue bird", "ivory tea", "long horn",
    "after rain", "river crossing", "jungle fruit", "grey stone",
    "forest gift", "night delivery",
]

# Terms that may indicate location references
LOCATION_HINTS = ["port", "border", "bay", "coast", "airport", "harbour", "hub"]

# Terms that may indicate route coordination
ROUTE_HINTS    = ["transit", "corridor", "crossing", "route", "delivery", "shipment", "cargo"]


def analyze_message(sender: str, receiver: str, message: str, d: AppData) -> dict:
    text_lower = message.lower()

    # Detect slang terms
    detected_terms = [term for term in KNOWN_SLANG if term in text_lower]

    # Generic indicators
    indicators: list[str] = []
    for hint in LOCATION_HINTS:
        if hint in text_lower:
            indicators.append(f"Possible geographic reference: '{hint}'")
    for hint in ROUTE_HINTS:
        if hint in text_lower:
            indicators.append(f"Possible logistics reference: '{hint}'")

    # Score calculation
    slang_score = min(len(detected_terms) * 25, 60)  # max 60 from slang
    ind_score   = min(len(indicators) * 5, 20)        # max 20 from indicators

    # Boost if sender/receiver are known high-risk actors
    actor_boost = 0.0
    sender_actor = d.actor_by_id.get(sender, {})
    receiver_actor = d.actor_by_id.get(receiver, {})
    for ac in (sender_actor, receiver_actor):
        ts = ac.get("threat_score", 0)
        try:
            ts = float(ts)
            if not math.isnan(ts) and ts >= 70:
                actor_boost = 20.0
                break
        except Exception:
            pass

    linguistic_risk = min(slang_score + ind_score + actor_boost, 100.0)
    confidence      = min(linguistic_risk + 5, 95.0) if detected_terms else max(linguistic_risk - 10, 5.0)

    # Possible location guess from route data
    possible_location: Optional[str] = None
    possible_route: Optional[str] = None

    for hint in LOCATION_HINTS:
        words = text_lower.split()
        for i, w in enumerate(words):
            if hint in w and i > 0:
                candidate = words[i - 1]
                if len(candidate) > 3 and candidate.isalpha():
                    possible_location = candidate.title()
                    break

    # Check if any known route location appears in message
    if not d.routes.empty:
        for r in d.routes.to_dict("records"):
            for loc in (r.get("source", ""), r.get("destination", ""), r.get("transit", "")):
                if loc and loc.lower() in text_lower:
                    possible_location = possible_location or loc
                    possible_route = str(r.get("route_id", ""))
                    break
            if possible_route:
                break

    explanation = _build_explanation(detected_terms, indicators, linguistic_risk, sender, receiver)

    return {
        "linguistic_risk": round(linguistic_risk, 2),
        "confidence": round(confidence, 2),
        "detected_terms": detected_terms,
        "possible_location": possible_location,
        "possible_route": possible_route,
        "indicators": indicators,
        "explanation": explanation,
    }


def link_message_to_investigation(
    message_id: str,
    target_type: str,
    target_id: str,
    d: AppData,
    db: Session,
) -> dict:
    # Fetch the message
    msg = d.message_by_id.get(message_id)
    text = str(msg.get("message_text", "")) if msg else ""
    slang_flag = str(msg.get("contains_slang", "")).lower() == "true" if msg else False

    detected_terms = [t for t in KNOWN_SLANG if t in text.lower()] if text else []
    ling_risk = min(len(detected_terms) * 25 + (20 if slang_flag else 0), 100.0)
    confidence = min(ling_risk + 5, 95.0)

    signal_id = f"SIG-{str(uuid.uuid4())[:8].upper()}"

    signal = LinguisticSignal(
        signal_id=signal_id,
        message_id=message_id,
        target_type=target_type.upper(),
        target_id=target_id,
        linguistic_risk=ling_risk,
        confidence=confidence,
        detected_terms=json.dumps(detected_terms),
        explanation=f"Linguistic signal linked from message {message_id} to {target_type} {target_id}.",
        created_at=datetime.now(timezone.utc),
    )
    db.add(signal)
    db.commit()

    return {
        "signal_id": signal_id,
        "message_id": message_id,
        "target_type": target_type.upper(),
        "target_id": target_id,
        "linguistic_risk": round(ling_risk, 2),
        "status": "stored",
    }


def get_message_map_context(message_id: str, d: AppData) -> Optional[dict]:
    msg = d.message_by_id.get(message_id)
    if not msg:
        return None

    linked_route = msg.get("linked_route")
    linked_route = str(linked_route) if linked_route and str(linked_route).lower() != "nan" else None

    # Find referenced location from route
    referenced_location: Optional[str] = None
    if linked_route:
        route = d.route_by_id.get(linked_route, {})
        referenced_location = route.get("destination") or route.get("source")

    # Nearby incidents via route
    nearby_incidents = []
    if linked_route:
        nearby_incidents = [
            {"incident_id": r.get("incident_id"), "species": r.get("species"),
             "date": str(r.get("incident_date", ""))}
            for r in d.incidents_by_route.get(linked_route, [])[:5]
        ]

    # Nearby alerts
    nearby_alerts = [
        {"alert_id": a.get("alert_id"), "pattern_type": a.get("pattern_type"),
         "priority": a.get("priority"), "risk_score": a.get("risk_score")}
        for a in d.alerts_by_entity.get(linked_route or "", [])[:5]
    ]

    # Local risk
    ri = d.route_intel_by_id.get(linked_route or "", {})
    local_risk = float(ri.get("route_risk_score", 0.0)) if ri else 0.0

    # Relevant entities
    relevant: list[dict] = []
    sender = msg.get("sender_actor")
    if sender:
        actor = d.actor_by_id.get(str(sender), {})
        if actor:
            relevant.append({"type": "ACTOR", "id": sender, "label": actor.get("full_name", sender)})

    return {
        "message_id": message_id,
        "referenced_location": referenced_location,
        "linked_route": linked_route,
        "nearby_incidents": nearby_incidents,
        "nearby_alerts": nearby_alerts,
        "local_risk": round(local_risk, 2),
        "relevant_entities": relevant,
    }


def _build_explanation(terms, indicators, risk, sender, receiver):
    if not terms and not indicators:
        return (
            f"No coded terminology or logistics indicators detected in this message "
            f"between {sender} and {receiver}. Risk score is low."
        )
    parts = []
    if terms:
        parts.append(
            f"Potential coded terminology detected: {', '.join(repr(t) for t in terms)}. "
            "These terms appear in known wildlife trafficking communication patterns. "
            "Context and corroborating intelligence are required before drawing conclusions."
        )
    if indicators:
        parts.append(
            f"Additional indicators: {'; '.join(indicators)}."
        )
    parts.append(
        f"Overall linguistic risk score: {risk:.0f}/100. "
        "This is an intelligence signal, not a confirmed finding."
    )
    return " ".join(parts)
