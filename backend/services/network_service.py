"""
network_service.py
------------------
Builds frontend-ready graph (nodes + edges) and resolves hidden links,
all from pre-loaded in-memory data. Never touches raw CSV files directly.
"""

from __future__ import annotations
from typing import Optional
from data_loader import AppData


def _sf(v, default=0.0) -> float:
    try:
        import math
        f = float(v)
        return default if math.isnan(f) else round(f, 2)
    except Exception:
        return default


# ── Hidden-link discovery ─────────────────────────────────────────────────────

def get_hidden_links(
    target_type: str,
    target_id: str,
    d: AppData,
    max_depth: int = 2,
    limit: int = 10,
) -> dict:
    raw_links = d.hidden_links_by_entity.get(target_id, [])

    scored = []
    for lnk in raw_links:
        # determine the "other" end relative to our target
        if str(lnk.get("source_id")) == target_id:
            other_type = str(lnk.get("target_entity", ""))
            other_id   = str(lnk.get("target_id", ""))
        else:
            other_type = str(lnk.get("source_entity", ""))
            other_id   = str(lnk.get("source_id", ""))

        confidence = _sf(lnk.get("confidence"))
        risk_score = _sf(lnk.get("risk_score"))

        # rank weight: 60% confidence + 40% risk
        weight = confidence * 0.6 + risk_score * 0.4

        scored.append({
            "weight": weight,
            "entity_type": other_type,
            "entity_id": other_id,
            "relationship_type": str(lnk.get("link_type", "UNKNOWN")),
            "confidence": confidence,
            "risk_score": risk_score,
            "explanation": str(lnk.get("supporting_evidence", "")),
            "supporting_evidence": [str(lnk.get("link_id", ""))],
        })

    # If max_depth > 1 add second-hop links
    if max_depth >= 2:
        seen_ids = {target_id} | {r["entity_id"] for r in scored}
        second_hop = []
        for r in scored:
            for lnk2 in d.hidden_links_by_entity.get(r["entity_id"], []):
                if str(lnk2.get("source_id")) == r["entity_id"]:
                    hop_type = str(lnk2.get("target_entity", ""))
                    hop_id   = str(lnk2.get("target_id", ""))
                else:
                    hop_type = str(lnk2.get("source_entity", ""))
                    hop_id   = str(lnk2.get("source_id", ""))

                if hop_id in seen_ids:
                    continue
                seen_ids.add(hop_id)

                c2 = _sf(lnk2.get("confidence")) * 0.7  # discounted for depth
                rs2 = _sf(lnk2.get("risk_score")) * 0.7
                second_hop.append({
                    "weight": c2 * 0.6 + rs2 * 0.4,
                    "entity_type": hop_type,
                    "entity_id": hop_id,
                    "relationship_type": f"INDIRECT_{lnk2.get('link_type', 'UNKNOWN')}",
                    "confidence": round(c2, 2),
                    "risk_score": round(rs2, 2),
                    "explanation": f"Second-hop link via {r['entity_id']}: {lnk2.get('supporting_evidence', '')}",
                    "supporting_evidence": [str(lnk2.get("link_id", ""))],
                })
        scored.extend(second_hop)

    # sort by weight descending, rank, and cap
    scored.sort(key=lambda x: x["weight"], reverse=True)
    results = []
    for rank, item in enumerate(scored[:limit], start=1):
        results.append({
            "rank": rank,
            "entity_type": item["entity_type"],
            "entity_id": item["entity_id"],
            "relationship_type": item["relationship_type"],
            "confidence": item["confidence"],
            "risk_score": item["risk_score"],
            "explanation": item["explanation"],
            "supporting_evidence": item["supporting_evidence"],
        })

    return {
        "target_type": target_type,
        "target_id": target_id,
        "results": results,
    }


# ── Network graph ─────────────────────────────────────────────────────────────

def get_network(
    target_type: str,
    target_id: str,
    d: AppData,
    max_depth: int = 2,
    max_nodes: int = 50,
) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def _add_node(nid: str, label: str, ntype: str, risk: float = 0.0):
        if nid not in nodes and len(nodes) < max_nodes:
            nodes[nid] = {"id": nid, "label": label, "type": ntype, "risk_score": round(risk, 2)}

    def _add_edge(src: str, tgt: str, rel: str, conf: float = 0.0, risk: float = 0.0):
        edges.append({
            "source": src, "target": tgt,
            "relationship_type": rel,
            "confidence": round(conf, 2),
            "risk_score": round(risk, 2),
        })

    # Seed node
    seed_label = _resolve_label(target_type, target_id, d)
    seed_risk  = _resolve_risk(target_type, target_id, d)
    _add_node(target_id, seed_label, target_type.upper(), seed_risk)

    # Expand by type
    if target_type == "INCIDENT":
        _expand_incident(target_id, d, _add_node, _add_edge, max_nodes, depth=1, max_depth=max_depth)
    elif target_type == "ACTOR":
        _expand_actor(target_id, d, _add_node, _add_edge, max_nodes, depth=1, max_depth=max_depth)
    elif target_type == "ROUTE":
        _expand_route(target_id, d, _add_node, _add_edge, max_nodes, depth=1, max_depth=max_depth)
    elif target_type == "LOCATION":
        _expand_location(target_id, d, _add_node, _add_edge, max_nodes, depth=1, max_depth=max_depth)

    # Add hidden-link edges
    for lnk in d.hidden_links_by_entity.get(target_id, []):
        src_id = str(lnk.get("source_id", ""))
        tgt_id = str(lnk.get("target_id", ""))
        ltype  = str(lnk.get("link_type", "HIDDEN_LINK"))
        conf   = _sf(lnk.get("confidence"))
        risk   = _sf(lnk.get("risk_score"))
        if src_id in nodes or tgt_id in nodes:
            _add_edge(src_id, tgt_id, ltype, conf, risk)

    return {"nodes": list(nodes.values()), "edges": edges}


def _expand_incident(inc_id, d, add_node, add_edge, max_nodes, depth, max_depth):
    inc = d.incident_by_id.get(inc_id, {})
    if not inc:
        return
    actor_id = inc.get("lead_actor")
    route_id = inc.get("route_id")

    if actor_id:
        actor = d.actor_by_id.get(str(actor_id), {})
        label = actor.get("full_name", str(actor_id))
        risk  = _sf(actor.get("threat_score"))
        add_node(str(actor_id), label, "ACTOR", risk)
        add_edge(inc_id, str(actor_id), "LEAD_ACTOR", 90.0, risk)

        if depth < max_depth:
            _expand_actor(str(actor_id), d, add_node, add_edge, max_nodes, depth + 1, max_depth)

    if route_id:
        route = d.route_by_id.get(str(route_id), {})
        label = f"{route.get('source','?')}→{route.get('destination','?')}"
        ri = d.route_intel_by_id.get(str(route_id), {})
        risk = _sf(ri.get("route_risk_score"))
        add_node(str(route_id), label, "ROUTE", risk)
        add_edge(inc_id, str(route_id), "ON_ROUTE", 85.0, risk)

    # shipments
    for shp in d.shipments_by_incident.get(inc_id, []):
        shp_id = str(shp.get("shipment_id", ""))
        add_node(shp_id, f"Shipment {shp_id[-6:]}", "SHIPMENT", 0.0)
        add_edge(inc_id, shp_id, "HAS_SHIPMENT", 80.0, 0.0)


def _expand_actor(actor_id, d, add_node, add_edge, max_nodes, depth, max_depth):
    for inc in d.incidents_by_actor.get(actor_id, [])[:5]:
        inc_id = str(inc.get("incident_id", ""))
        add_node(inc_id, f"INC {inc_id[-6:]}", "INCIDENT", 50.0)
        add_edge(actor_id, inc_id, "INVOLVED_IN", 85.0, 50.0)
        if depth < max_depth:
            _expand_incident(inc_id, d, add_node, add_edge, max_nodes, depth + 1, max_depth)

    for em in d.entity_matches_by_actor.get(actor_id, [])[:3]:
        other = str(em.get("actor_2") if em.get("actor_1") == actor_id else em.get("actor_1", ""))
        if other:
            actor2 = d.actor_by_id.get(other, {})
            add_node(other, actor2.get("full_name", other), "ACTOR", _sf(actor2.get("threat_score")))
            add_edge(actor_id, other, "ENTITY_MATCH", _sf(em.get("confidence_score")), 0.0)


def _expand_route(route_id, d, add_node, add_edge, max_nodes, depth, max_depth):
    for inc in d.incidents_by_route.get(route_id, [])[:5]:
        inc_id = str(inc.get("incident_id", ""))
        add_node(inc_id, f"INC {inc_id[-6:]}", "INCIDENT", 50.0)
        add_edge(route_id, inc_id, "INCIDENT_ON_ROUTE", 80.0, 50.0)
        if depth < max_depth:
            actor_id = inc.get("lead_actor")
            if actor_id:
                actor = d.actor_by_id.get(str(actor_id), {})
                add_node(str(actor_id), actor.get("full_name", str(actor_id)), "ACTOR", _sf(actor.get("threat_score")))
                add_edge(str(actor_id), inc_id, "LEAD_ACTOR", 85.0, _sf(actor.get("threat_score")))


def _expand_location(loc_id, d, add_node, add_edge, max_nodes, depth, max_depth):
    if d.incidents.empty:
        return
    if "source_location" not in d.incidents.columns:
        return
    loc_incs = d.incidents[
        (d.incidents["source_location"] == loc_id) | (d.incidents["destination"] == loc_id)
    ].head(5)
    for _, inc in loc_incs.iterrows():
        inc_id = str(inc.get("incident_id", ""))
        add_node(inc_id, f"INC {inc_id[-6:]}", "INCIDENT", 50.0)
        add_edge(loc_id, inc_id, "LOCATION_INCIDENT", 75.0, 50.0)


def _resolve_label(target_type: str, target_id: str, d: AppData) -> str:
    if target_type == "ACTOR":
        actor = d.actor_by_id.get(target_id, {})
        return actor.get("full_name", target_id)
    if target_type == "ROUTE":
        route = d.route_by_id.get(target_id, {})
        return f"{route.get('source','?')}→{route.get('destination','?')}"
    if target_type == "INCIDENT":
        return f"INC {target_id[-6:]}"
    return target_id


def _resolve_risk(target_type: str, target_id: str, d: AppData) -> float:
    key = f"{target_type.upper()}:{target_id}"
    intel = d.intelligence_by_target.get(key, {})
    return _sf(intel.get("risk_score"))
