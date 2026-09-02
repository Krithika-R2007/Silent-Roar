"""
data_loader.py
--------------
Loads all CSV/JSON intelligence outputs once at startup.
Builds fast in-memory lookup dictionaries so endpoints never scan DataFrames
row-by-row and avoid repeated disk I/O.

Called from main.py lifespan; exposes a single AppData singleton.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any, Dict, List

import pandas as pd

# Path resolution: data lives two directories up from this file
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_THIS_DIR, "..", "simulated_data")


def _csv(filename: str, date_cols: list[str] | None = None) -> pd.DataFrame:
    path = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  [WARN] {filename} not found — returning empty DataFrame.")
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, low_memory=False)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        if date_cols:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception as exc:
        print(f"  [ERROR] loading {filename}: {exc}")
        return pd.DataFrame()


def _json_file(filename: str) -> Any:
    path = os.path.join(_DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"  [WARN] {filename} not found.")
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _groupby_dict(df: pd.DataFrame, col: str) -> Dict[str, List[dict]]:
    """Build a defaultdict(list) keyed by `col` values for fast lookups."""
    result: Dict[str, List[dict]] = defaultdict(list)
    if df.empty or col not in df.columns:
        return result
    for row in df.to_dict("records"):
        key = row.get(col)
        if key is not None and not (isinstance(key, float) and key != key):  # skip NaN
            result[str(key)].append(row)
    return result


def _safe_float(v, default: float = 0.0) -> float:
    try:
        f = float(v)
        import math
        return default if math.isnan(f) else f
    except Exception:
        return default


class AppData:
    """Singleton holding all in-memory data and indexes."""

    # ── Raw DataFrames (kept for advanced queries) ────────────────────────
    incidents: pd.DataFrame
    actors: pd.DataFrame
    routes: pd.DataFrame
    shipments: pd.DataFrame
    messages: pd.DataFrame
    animal_events: pd.DataFrame
    entity_matches: pd.DataFrame
    pattern_alerts: pd.DataFrame
    route_intelligence: pd.DataFrame
    hidden_links: pd.DataFrame
    intelligence_scores: pd.DataFrame
    investigation_targets: pd.DataFrame
    trafficking_network: dict

    # ── Fast lookup dicts ─────────────────────────────────────────────────
    incident_by_id: Dict[str, dict]
    actor_by_id: Dict[str, dict]
    route_by_id: Dict[str, dict]
    shipment_by_id: Dict[str, dict]
    message_by_id: Dict[str, dict]

    # grouped indexes
    incidents_by_route: Dict[str, List[dict]]
    incidents_by_actor: Dict[str, List[dict]]
    shipments_by_incident: Dict[str, List[dict]]
    shipments_by_actor: Dict[str, List[dict]]
    alerts_by_entity: Dict[str, List[dict]]
    alert_by_id: Dict[str, dict]
    hidden_links_by_entity: Dict[str, List[dict]]
    entity_matches_by_actor: Dict[str, List[dict]]
    intelligence_by_target: Dict[str, dict]   # key = "TYPE:ID"
    evidence_by_target: Dict[str, dict]        # key = "TYPE:ID"
    route_intel_by_id: Dict[str, dict]

    # message indexes
    messages_by_actor: Dict[str, List[dict]]
    messages_by_route: Dict[str, List[dict]]

    # search helpers (pre-lowercased)
    _incident_search: List[dict]
    _actor_search: List[dict]
    _route_search: List[dict]
    _locations: List[str]

    # stats for the dashboard
    loaded: bool = False


_app_data = AppData()


def get_data() -> AppData:
    """Return the singleton. Auto-loads on first call if not already loaded."""
    if not _app_data.loaded:
        load_all()
    return _app_data


def load_all() -> AppData:
    d = _app_data

    print("Loading data files…")

    # ── Raw tables ────────────────────────────────────────────────────────
    d.incidents = _csv(
        "incidents.csv",
        date_cols=["incident_date"],
    )
    d.actors = _csv("actors.csv")
    d.routes = _csv("routes.csv")
    d.shipments = _csv("shipments.csv", date_cols=["departure_date", "arrival_date"])
    d.messages = _csv("messages.csv", date_cols=["timestamp"])
    d.animal_events = _csv("animal_events.csv", date_cols=["event_date"])
    d.entity_matches = _csv("entity_matches.csv")
    d.pattern_alerts = _csv("pattern_alerts.csv", date_cols=["first_detected", "last_detected"])
    d.route_intelligence = _csv("route_intelligence.csv")
    d.hidden_links = _csv("hidden_links.csv")
    d.intelligence_scores = _csv("intelligence_scores.csv")
    d.investigation_targets = _csv("investigation_targets.csv")
    d.trafficking_network = _json_file("trafficking_network.json")

    # ── Primary key lookups ───────────────────────────────────────────────
    def _pk(df: pd.DataFrame, col: str) -> Dict[str, dict]:
        if df.empty or col not in df.columns:
            return {}
        return {str(r[col]): r for r in df.to_dict("records") if r.get(col) is not None}

    d.incident_by_id = _pk(d.incidents, "incident_id")
    d.actor_by_id = _pk(d.actors, "actor_id")
    d.route_by_id = _pk(d.routes, "route_id")
    d.shipment_by_id = _pk(d.shipments, "shipment_id")
    d.message_by_id = _pk(d.messages, "message_id")

    # ── Grouped indexes ───────────────────────────────────────────────────
    d.incidents_by_route = _groupby_dict(d.incidents, "route_id")
    d.incidents_by_actor = _groupby_dict(d.incidents, "lead_actor")
    d.shipments_by_incident = _groupby_dict(d.shipments, "incident_id")
    d.shipments_by_actor = _groupby_dict(d.shipments, "actor_id")

    d.alerts_by_entity = _groupby_dict(d.pattern_alerts, "entity_id")
    d.alert_by_id = _pk(d.pattern_alerts, "alert_id")

    d.hidden_links_by_entity = defaultdict(list)
    if not d.hidden_links.empty:
        for row in d.hidden_links.to_dict("records"):
            for fld in ("source_id", "target_id"):
                k = row.get(fld)
                if k is not None:
                    d.hidden_links_by_entity[str(k)].append(row)

    d.entity_matches_by_actor = defaultdict(list)
    if not d.entity_matches.empty:
        for row in d.entity_matches.to_dict("records"):
            for fld in ("actor_1", "actor_2"):
                k = row.get(fld)
                if k is not None:
                    d.entity_matches_by_actor[str(k)].append(row)

    # intelligence scores: keyed as "TYPE:ID"
    d.intelligence_by_target = {}
    d.evidence_by_target = {}
    if not d.intelligence_scores.empty:
        for row in d.intelligence_scores.to_dict("records"):
            tt = str(row.get("target_type", "")).upper()
            tid = str(row.get("target_id", ""))
            key = f"{tt}:{tid}"
            d.intelligence_by_target[key] = row

    d.route_intel_by_id = _pk(d.route_intelligence, "route_id")

    # messages per actor and per route
    d.messages_by_actor = defaultdict(list)
    d.messages_by_route = defaultdict(list)
    if not d.messages.empty:
        for row in d.messages.to_dict("records"):
            s = row.get("sender_actor")
            r = row.get("receiver_actor")
            lr = row.get("linked_route")
            if s:
                d.messages_by_actor[str(s)].append(row)
            if r and r != s:
                d.messages_by_actor[str(r)].append(row)
            if lr and str(lr).strip() and str(lr).strip().lower() != "nan":
                d.messages_by_route[str(lr)].append(row)

    # ── Search helpers ────────────────────────────────────────────────────
    d._incident_search = [
        {**r, "_search": " ".join(
            str(r.get(c, "")).lower()
            for c in ("incident_id", "species", "commodity", "source_location", "destination", "lead_actor")
        )}
        for r in d.incidents.to_dict("records")
    ]

    d._actor_search = [
        {**r, "_search": " ".join(
            str(r.get(c, "")).lower()
            for c in ("actor_id", "full_name", "alias", "nationality", "role", "primary_region")
        )}
        for r in d.actors.to_dict("records")
    ]

    d._route_search = [
        {**r, "_search": " ".join(
            str(r.get(c, "")).lower()
            for c in ("route_id", "source", "transit", "destination", "corridor")
        )}
        for r in d.routes.to_dict("records")
    ]

    # unique locations from incidents
    locs: set[str] = set()
    if not d.incidents.empty:
        for col in ("source_location", "destination"):
            if col in d.incidents.columns:
                locs.update(d.incidents[col].dropna().unique().tolist())
    d._locations = sorted(locs)

    d.loaded = True

    # ── Startup summary ───────────────────────────────────────────────────
    print("Data loading complete")
    print(f"  Incidents:             {len(d.incidents)}")
    print(f"  Actors:                {len(d.actors)}")
    print(f"  Routes:                {len(d.routes)}")
    print(f"  Shipments:             {len(d.shipments)}")
    print(f"  Messages:              {len(d.messages)}")
    print(f"  Alerts:                {len(d.pattern_alerts)}")
    print(f"  Intelligence targets:  {len(d.intelligence_scores)}")

    return d
