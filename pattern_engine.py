"""
pattern_engine.py
=================
Wildlife Intelligence Platform — Phase 3
Suspicious Pattern Detection + Hidden Trafficking Network Discovery

Detects meaningful patterns from simulated_data/ and entity_matches.csv,
assigns explainable risk scores, and exports four artefacts:
  simulated_data/pattern_alerts.csv
  simulated_data/route_intelligence.csv
  simulated_data/hidden_links.csv
  simulated_data/trafficking_network.graphml
  simulated_data/trafficking_network.json

All findings are framed as INDICATORS / SIGNALS — not proof of criminal activity.

Usage:
  python pattern_engine.py
"""

import os
import json
import math
import itertools
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd
import networkx as nx

# ── Output directory ───────────────────────────────────────────────────────────
DATA_DIR   = "simulated_data"
OUTPUT_DIR = "simulated_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Intelligence priority thresholds ──────────────────────────────────────────
CRITICAL  = 80
HIGH      = 65
WATCH     = 45
# below WATCH → LOW (not emitted as alerts, but tracked)

# ── Temporal window sizes (days) ──────────────────────────────────────────────
WINDOW_RECENT   = 30
WINDOW_BASELINE = 90
EMERGING_RATIO  = 2.5   # recent-rate / baseline-rate to flag EMERGING


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING & NORMALISATION
# ══════════════════════════════════════════════════════════════════════════════

def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case, strip, collapse internal spaces in all column names."""
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def load_data() -> dict[str, pd.DataFrame]:
    """Load all CSVs; normalise column names; parse dates; handle missing."""
    files = {
        "actors":         "actors.csv",
        "incidents":      "incidents.csv",
        "shipments":      "shipments.csv",
        "routes":         "routes.csv",
        "messages":       "messages.csv",
        "animal_events":  "animal_events.csv",
        "entity_matches": "entity_matches.csv",
    }

    tables: dict[str, pd.DataFrame] = {}
    for key, fname in files.items():
        path = os.path.join(DATA_DIR, fname)
        try:
            df = pd.read_csv(path, low_memory=False)
            df = _norm_cols(df)
            tables[key] = df
        except FileNotFoundError:
            print(f"  [WARN] {fname} not found — skipping.")
            tables[key] = pd.DataFrame()

    # Parse date columns
    for col in ("incident_date",):
        if col in tables["incidents"].columns:
            tables["incidents"][col] = pd.to_datetime(
                tables["incidents"][col], errors="coerce"
            )
    for col in ("departure_date", "arrival_date"):
        if col in tables["shipments"].columns:
            tables["shipments"][col] = pd.to_datetime(
                tables["shipments"][col], errors="coerce"
            )
    if "timestamp" in tables["messages"].columns:
        tables["messages"]["timestamp"] = pd.to_datetime(
            tables["messages"]["timestamp"], errors="coerce"
        )
    if "event_date" in tables["animal_events"].columns:
        tables["animal_events"]["event_date"] = pd.to_datetime(
            tables["animal_events"]["event_date"], errors="coerce"
        )

    return tables


# ══════════════════════════════════════════════════════════════════════════════
# 2. SHARED UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _uid(prefix: str) -> str:
    import uuid
    return f"{prefix}-{str(uuid.uuid4())[:8].upper()}"


def _priority(score: float) -> str:
    if score >= CRITICAL: return "CRITICAL"
    if score >= HIGH:     return "HIGH"
    if score >= WATCH:    return "WATCH"
    return "LOW"


def _clamp(v) -> float:
    """Clamp a scalar or Series element to [0, 100]."""
    if isinstance(v, pd.Series):
        return v.clip(0.0, 100.0).round(2)
    return round(float(max(0.0, min(100.0, float(v)))), 2)


def _reference_date(incidents: pd.DataFrame) -> datetime:
    """Use the latest incident date as the analysis reference point."""
    valid = incidents["incident_date"].dropna()
    return valid.max() if len(valid) else datetime(2026, 12, 31)


def _recent_mask(incidents: pd.DataFrame, ref: datetime, days: int) -> pd.Series:
    cutoff = ref - timedelta(days=days)
    return incidents["incident_date"] >= cutoff


def _actor_route_map(incidents: pd.DataFrame,
                     shipments: pd.DataFrame) -> dict[str, set]:
    """actor_id → set of route_ids (from both incidents & shipments)."""
    result: dict[str, set] = defaultdict(set)
    for _, r in incidents.dropna(subset=["lead_actor", "route_id"]).iterrows():
        result[r["lead_actor"]].add(r["route_id"])
    merged = shipments.merge(
        incidents[["incident_id", "route_id"]].dropna(),
        on="incident_id", how="left"
    )
    for _, r in merged.dropna(subset=["actor_id", "route_id"]).iterrows():
        result[r["actor_id"]].add(r["route_id"])
    return dict(result)


# ══════════════════════════════════════════════════════════════════════════════
# 3. PATTERN A — RECURRING ACTORS
# ══════════════════════════════════════════════════════════════════════════════

def detect_recurring_actors(tables: dict) -> list[dict]:
    """
    Score every actor on five axes then emit alerts for those above WATCH threshold.
    Score = 25*freq_norm + 20*route_div + 20*loc_div + 20*time_span_norm + 15*commodity_div
    All normalised to 0–100 before weighting.
    """
    incidents  = tables["incidents"]
    shipments  = tables["shipments"]
    actors     = tables["actors"]

    ref        = _reference_date(incidents)
    actor_info = actors.set_index("actor_id").to_dict("index") if not actors.empty else {}

    # Incidents per actor (lead_actor)
    inc_grp = incidents.groupby("lead_actor")
    inc_cnt   = inc_grp.size().rename("inc_count")
    inc_routes= inc_grp["route_id"].nunique().rename("route_div")
    inc_dests = inc_grp["destination"].nunique().rename("dest_div")
    inc_spec  = inc_grp["species"].nunique().rename("spec_div")
    inc_span  = (
        inc_grp["incident_date"].agg(lambda x: (x.max() - x.min()).days)
        .rename("span_days")
    )

    # Shipments per actor
    shp_cnt = shipments.groupby("actor_id").size().rename("shp_count")

    stats = (
        pd.concat([inc_cnt, inc_routes, inc_dests, inc_spec, inc_span], axis=1)
        .fillna(0)
        .join(shp_cnt, how="left")
        .fillna(0)
        .reset_index()
        .rename(columns={"lead_actor": "actor_id"})
    )

    # Normalise each axis against the dataset maximum
    def _norm(series):
        mx = series.max()
        return (series / mx * 100) if mx > 0 else series * 0

    stats["freq_score"]     = _norm(stats["inc_count"])
    stats["route_score"]    = _norm(stats["route_div"])
    stats["loc_score"]      = _norm(stats["dest_div"])
    stats["time_score"]     = _norm(stats["span_days"])
    stats["commodity_score"]= _norm(stats["spec_div"])

    stats["risk_score"] = _clamp(
        0.25 * stats["freq_score"]
        + 0.20 * stats["route_score"]
        + 0.20 * stats["loc_score"]
        + 0.20 * stats["time_score"]
        + 0.15 * stats["commodity_score"]
    )

    alerts = []
    for _, row in stats[stats["risk_score"] >= WATCH].iterrows():
        aid   = row["actor_id"]
        info  = actor_info.get(aid, {})
        name  = info.get("full_name", aid)
        role  = info.get("role", "Unknown")
        nat   = info.get("nationality", "Unknown")

        parts = []
        if row["inc_count"] >= 3:
            parts.append(f"involved in {int(row['inc_count'])} incidents")
        if row["route_div"] >= 2:
            parts.append(f"{int(row['route_div'])} distinct trafficking corridors")
        if row["dest_div"] >= 2:
            parts.append(f"{int(row['dest_div'])} destination locations")
        if row["spec_div"] >= 2:
            parts.append(f"{int(row['spec_div'])} species/commodity types")
        if row["span_days"] >= 30:
            parts.append(f"activity spanning {int(row['span_days'])} days")
        explanation = (
            f"Recurring actor signal for {name} ({role}, {nat}): "
            + ("; ".join(parts) if parts else "repeated involvement detected")
            + "."
        )

        alerts.append({
            "alert_id":             _uid("ALT"),
            "pattern_type":         "RECURRING_ACTOR",
            "priority":             _priority(row["risk_score"]),
            "entity_type":          "ACTOR",
            "entity_id":            aid,
            "risk_score":           row["risk_score"],
            "confidence":           round(min(row["risk_score"] + 5, 100), 2),
            "first_detected":       incidents[incidents["lead_actor"] == aid]["incident_date"].min(),
            "last_detected":        incidents[incidents["lead_actor"] == aid]["incident_date"].max(),
            "incident_count":       int(row["inc_count"]),
            "related_actor_count":  0,
            "related_route_count":  int(row["route_div"]),
            "related_location_count": int(row["dest_div"]),
            "explanation":          explanation,
            # sub-scores for frontend "WHY?" panel
            "frequency_score":      round(row["freq_score"], 2),
            "temporal_score":       round(row["time_score"], 2),
            "geographic_score":     round(row["loc_score"], 2),
            "network_score":        0.0,
            "recurrence_score":     round(row["route_score"], 2),
        })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# 4. PATTERN B — EMERGING / HIGH-RISK ROUTES
# ══════════════════════════════════════════════════════════════════════════════

def detect_emerging_routes(tables: dict) -> list[dict]:
    """
    For every route compute:
      baseline_rate  = incidents in (ref-90d, ref-30d]  / 60 days
      recent_rate    = incidents in (ref-30d, ref]       / 30 days
    Flag EMERGING when recent_rate >= EMERGING_RATIO * baseline_rate (and recent >= 2).
    Flag RECURRING when total incidents is in the top quartile.
    """
    incidents = tables["incidents"]
    routes    = tables["routes"]
    shipments = tables["shipments"]
    ref       = _reference_date(incidents)

    cutoff_recent   = ref - timedelta(days=WINDOW_RECENT)
    cutoff_baseline = ref - timedelta(days=WINDOW_BASELINE)

    grp = incidents.groupby("route_id")

    total_inc   = grp.size().rename("total_inc")
    recent_inc  = incidents[incidents["incident_date"] >= cutoff_recent].groupby("route_id").size().rename("recent_inc")
    base_inc    = incidents[
        (incidents["incident_date"] >= cutoff_baseline) &
        (incidents["incident_date"] <  cutoff_recent)
    ].groupby("route_id").size().rename("base_inc")
    uniq_actors = grp["lead_actor"].nunique().rename("unique_actors")
    uniq_spec   = grp["species"].nunique().rename("unique_species")

    shp_cnt = shipments.merge(
        incidents[["incident_id", "route_id"]], on="incident_id", how="left"
    ).groupby("route_id").size().rename("shp_count")

    route_stats = (
        pd.concat([total_inc, recent_inc, base_inc, uniq_actors, uniq_spec, shp_cnt], axis=1)
        .fillna(0)
        .reset_index()
    )
    route_stats.columns = [c if c != "route_id" else c for c in route_stats.columns]

    # Merge route metadata
    if not routes.empty:
        route_meta = routes[["route_id", "source", "transit", "destination",
                              "corridor", "historical_risk"]].copy()
        route_stats = route_stats.merge(route_meta, on="route_id", how="left")
    else:
        for c in ("source", "transit", "destination", "corridor", "historical_risk"):
            route_stats[c] = ""

    # Rates
    route_stats["recent_rate"]   = route_stats["recent_inc"] / WINDOW_RECENT
    route_stats["baseline_rate"] = route_stats["base_inc"]   / (WINDOW_BASELINE - WINDOW_RECENT)

    q75 = route_stats["total_inc"].quantile(0.75)

    alerts = []
    for _, row in route_stats.iterrows():
        rid    = row["route_id"]
        recent = int(row["recent_inc"])
        total  = int(row["total_inc"])
        base   = int(row["base_inc"])
        actors = int(row["unique_actors"])
        spec   = int(row["unique_species"])
        hr     = float(row.get("historical_risk", 50))

        # Route risk score
        freq_s = _clamp((total / max(route_stats["total_inc"].max(), 1)) * 100)
        recency_s = _clamp((recent / max(route_stats["recent_inc"].max(), 1)) * 100)
        actor_s   = _clamp((actors / max(route_stats["unique_actors"].max(), 1)) * 100)
        risk_score = _clamp(
            0.35 * freq_s + 0.30 * recency_s + 0.20 * actor_s + 0.15 * (hr)
        )

        # Determine status
        b_rate = row["baseline_rate"]
        r_rate = row["recent_rate"]
        if b_rate > 0 and r_rate >= EMERGING_RATIO * b_rate and recent >= 2:
            status = "EMERGING"
        elif total >= q75 and hr >= 70:
            status = "HIGH_RISK"
        elif total >= q75:
            status = "RECURRING"
        else:
            status = "STABLE"

        if risk_score < WATCH and status == "STABLE":
            continue   # suppress low-noise stable routes

        corridor = row.get("corridor", rid)
        src      = row.get("source", "?")
        dst      = row.get("destination", "?")

        parts = []
        if status == "EMERGING":
            parts.append(
                f"activity increased from {base} incidents (baseline) to "
                f"{recent} incidents in the last {WINDOW_RECENT} days"
            )
        if actors >= 3:
            parts.append(f"{actors} distinct actors involved")
        if spec >= 2:
            parts.append(f"{spec} species detected on this corridor")
        if hr >= 70:
            parts.append(f"historical risk score {int(hr)}/100")
        explanation = (
            f"{status.title()} route signal for corridor {corridor} "
            f"({src} → {dst}): "
            + ("; ".join(parts) if parts else "elevated activity detected")
            + "."
        )

        alerts.append({
            "alert_id":             _uid("ALT"),
            "pattern_type":         f"ROUTE_{status}",
            "priority":             _priority(risk_score),
            "entity_type":          "ROUTE",
            "entity_id":            rid,
            "risk_score":           risk_score,
            "confidence":           round(min(risk_score + 3, 100), 2),
            "first_detected":       incidents[incidents["route_id"] == rid]["incident_date"].min(),
            "last_detected":        incidents[incidents["route_id"] == rid]["incident_date"].max(),
            "incident_count":       total,
            "related_actor_count":  actors,
            "related_route_count":  1,
            "related_location_count": 2,
            "explanation":          explanation,
            "frequency_score":      round(freq_s, 2),
            "temporal_score":       round(recency_s, 2),
            "geographic_score":     round(actor_s, 2),
            "network_score":        0.0,
            "recurrence_score":     round(hr, 2),
            # extra columns for route_intelligence.csv
            "_total_incidents":     total,
            "_recent_incidents":    recent,
            "_historical_incidents":base,
            "_unique_actors":       actors,
            "_unique_species":      spec,
            "_route_status":        status,
            "_source":              src,
            "_transit":             row.get("transit", ""),
            "_destination":         dst,
        })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# 5. PATTERN C — EMERGING HUBS
# ══════════════════════════════════════════════════════════════════════════════

def detect_emerging_hubs(tables: dict) -> list[dict]:
    """
    Treat every source_location and destination as a hub node.
    Score by:  recent growth rate, number of connected routes, unique actors, total volume.
    """
    incidents = tables["incidents"]
    ref       = _reference_date(incidents)
    cutoff_r  = ref - timedelta(days=WINDOW_RECENT)
    cutoff_b  = ref - timedelta(days=WINDOW_BASELINE)

    def _hub_stats(col: str, label: str) -> pd.DataFrame:
        grp       = incidents.groupby(col)
        total     = grp.size().rename("total")
        recent    = incidents[incidents["incident_date"] >= cutoff_r].groupby(col).size().rename("recent")
        base      = incidents[
            (incidents["incident_date"] >= cutoff_b) &
            (incidents["incident_date"] <  cutoff_r)
        ].groupby(col).size().rename("base")
        u_actors  = grp["lead_actor"].nunique().rename("unique_actors")
        u_routes  = grp["route_id"].nunique().rename("unique_routes")
        df = pd.concat([total, recent, base, u_actors, u_routes], axis=1).fillna(0).reset_index()
        df.rename(columns={col: "location"}, inplace=True)
        df["hub_type"] = label
        return df

    src_stats = _hub_stats("source_location", "SOURCE")
    dst_stats = _hub_stats("destination",      "DESTINATION")
    hub_stats = pd.concat([src_stats, dst_stats], ignore_index=True)

    # Aggregate if a location appears as both source and destination
    hub_stats = hub_stats.groupby("location", as_index=False).agg({
        "total":        "sum",
        "recent":       "sum",
        "base":         "sum",
        "unique_actors":"max",
        "unique_routes":"max",
        "hub_type":     "first",
    })

    q75_total  = hub_stats["total"].quantile(0.75)
    q75_actors = hub_stats["unique_actors"].quantile(0.75)

    alerts = []
    for _, row in hub_stats.iterrows():
        loc     = row["location"]
        total   = int(row["total"])
        recent  = int(row["recent"])
        base    = int(row["base"])
        actors  = int(row["unique_actors"])
        routes  = int(row["unique_routes"])

        b_rate = base / (WINDOW_BASELINE - WINDOW_RECENT) if base > 0 else 0
        r_rate = recent / WINDOW_RECENT if recent > 0 else 0

        is_emerging = (b_rate > 0 and r_rate >= EMERGING_RATIO * b_rate and recent >= 2)
        is_high     = (total >= q75_total and actors >= q75_actors)

        if not is_emerging and not is_high:
            continue

        # Score
        freq_s   = _clamp((total   / max(hub_stats["total"].max(),  1)) * 100)
        recency_s= _clamp((recent  / max(hub_stats["recent"].max(), 1)) * 100)
        actor_s  = _clamp((actors  / max(hub_stats["unique_actors"].max(), 1)) * 100)
        route_s  = _clamp((routes  / max(hub_stats["unique_routes"].max(), 1)) * 100)
        risk_score = _clamp(0.30*freq_s + 0.30*recency_s + 0.25*actor_s + 0.15*route_s)

        if risk_score < WATCH:
            continue

        tag = "EMERGING_HUB" if is_emerging else "HIGH_CONNECTIVITY_HUB"
        parts = []
        if is_emerging:
            parts.append(f"activity rose from {base} (baseline period) to {recent} incidents in the last {WINDOW_RECENT} days")
        if actors >= 3:
            parts.append(f"{actors} distinct actors observed")
        if routes >= 2:
            parts.append(f"connected to {routes} trafficking corridors")
        explanation = (
            f"{tag.replace('_', ' ').title()} signal for {loc}: "
            + ("; ".join(parts) if parts else "elevated connectivity detected")
            + "."
        )

        alerts.append({
            "alert_id":             _uid("ALT"),
            "pattern_type":         tag,
            "priority":             _priority(risk_score),
            "entity_type":          "LOCATION",
            "entity_id":            loc,
            "risk_score":           risk_score,
            "confidence":           round(min(risk_score + 4, 100), 2),
            "first_detected":       incidents[
                (incidents["source_location"] == loc) | (incidents["destination"] == loc)
            ]["incident_date"].min(),
            "last_detected":        incidents[
                (incidents["source_location"] == loc) | (incidents["destination"] == loc)
            ]["incident_date"].max(),
            "incident_count":       total,
            "related_actor_count":  actors,
            "related_route_count":  routes,
            "related_location_count": 1,
            "explanation":          explanation,
            "frequency_score":      round(freq_s, 2),
            "temporal_score":       round(recency_s, 2),
            "geographic_score":     round(route_s, 2),
            "network_score":        0.0,
            "recurrence_score":     round(actor_s, 2),
        })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# 6. PATTERN D — TEMPORAL CLUSTERS
# ══════════════════════════════════════════════════════════════════════════════

def detect_temporal_clusters(tables: dict) -> list[dict]:
    """
    Slide windows of 7, 14, 30 days across the incident timeline.
    A cluster fires when >= 3 incidents share 2+ attributes (route, species,
    source) within the window.
    Score strengthens with attribute overlap count.
    """
    incidents = tables["incidents"].dropna(subset=["incident_date"]).copy()
    incidents = incidents.sort_values("incident_date").reset_index(drop=True)

    windows   = [7, 14, 30]
    seen      = set()  # avoid duplicate cluster alerts
    alerts    = []
    MIN_CLUSTER_SIZE = {7: 5, 14: 6, 30: 8}   # stricter minimums per window

    for window_days in windows:
        n = len(incidents)
        for i in range(n):
            anchor = incidents.loc[i, "incident_date"]
            cutoff = anchor + timedelta(days=window_days)
            group  = incidents[
                (incidents["incident_date"] >= anchor) &
                (incidents["incident_date"] <= cutoff)
            ]
            if len(group) < MIN_CLUSTER_SIZE.get(window_days, 4):
                continue

            # Shared attribute counts
            route_mode   = group["route_id"].mode()
            species_mode = group["species"].mode()
            src_mode     = group["source_location"].mode()

            shared_route   = len(route_mode) > 0 and (group["route_id"] == route_mode[0]).sum() >= 2
            shared_species = len(species_mode) > 0 and (group["species"] == species_mode[0]).sum() >= 2
            shared_src     = len(src_mode) > 0 and (group["source_location"] == src_mode[0]).sum() >= 2

            overlap = sum([shared_route, shared_species, shared_src])
            if overlap < 2:
                continue

            # Deduplicate by (anchor_date_str, window, primary_route)
            primary_route = route_mode[0] if shared_route else "MIXED"
            key = (str(anchor.date()), window_days, primary_route)
            if key in seen:
                continue
            seen.add(key)

            count     = len(group)
            actors    = group["lead_actor"].nunique()
            species   = group["species"].nunique()
            start_dt  = group["incident_date"].min()
            end_dt    = group["incident_date"].max()

            # Score
            density_s = _clamp((count / window_days) * 100 * 3)
            overlap_s = _clamp(overlap / 3 * 100)
            actor_s   = _clamp(min(actors / 5, 1) * 100)
            risk_score = _clamp(0.40*density_s + 0.35*overlap_s + 0.25*actor_s)

            if risk_score < WATCH:
                continue

            shared_attrs = []
            if shared_route:   shared_attrs.append(f"route {primary_route}")
            if shared_species: shared_attrs.append(f"species {species_mode[0]}")
            if shared_src:     shared_attrs.append(f"source {src_mode[0]}")

            explanation = (
                f"Temporal trafficking cluster: {count} incidents within {window_days} days "
                f"({start_dt.date()} – {end_dt.date()}) sharing "
                f"{', '.join(shared_attrs)}; {actors} actor(s) involved."
            )

            alerts.append({
                "alert_id":             _uid("ALT"),
                "pattern_type":         "TEMPORAL_CLUSTER",
                "priority":             _priority(risk_score),
                "entity_type":          "CLUSTER",
                "entity_id":            f"CLUSTER_{start_dt.date()}_{window_days}d",
                "risk_score":           risk_score,
                "confidence":           round(min(risk_score + 2, 100), 2),
                "first_detected":       start_dt,
                "last_detected":        end_dt,
                "incident_count":       count,
                "related_actor_count":  actors,
                "related_route_count":  int(group["route_id"].nunique()),
                "related_location_count": int(group["source_location"].nunique()),
                "explanation":          explanation,
                "frequency_score":      round(density_s, 2),
                "temporal_score":       round(overlap_s, 2),
                "geographic_score":     0.0,
                "network_score":        0.0,
                "recurrence_score":     round(actor_s, 2),
            })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# 6b. CLUSTER RANKING — raw signals → investigation-worthy tier
# ══════════════════════════════════════════════════════════════════════════════

def rank_clusters(raw_clusters: list[dict],
                  tables: dict,
                  top_n: int = 20) -> list[dict]:
    """
    Takes the full list of raw temporal-cluster alerts and re-scores each one
    using five explicit dimensions, then returns the top-N for the dashboard.

    Ranking formula (0-100):
        35%  incident density   (incidents ÷ window_days, normalised)
        25%  actor overlap      (unique actors in cluster, normalised)
        20%  route overlap      (unique routes, normalised)
        10%  species overlap    (unique species, normalised)
        10%  network confidence (mean entity-match confidence for actors in
                                 this cluster, where available)

    Each cluster also gets an 'investigation_rank' field (1 = highest priority)
    and a 'ranking_explanation' that lists the five dimension scores so an
    investigator immediately sees WHY it was promoted.
    """
    if not raw_clusters:
        return []

    incidents      = tables["incidents"]
    entity_matches = tables["entity_matches"]

    # Build actor → max entity-match confidence lookup
    em_conf: dict[str, float] = {}
    if not entity_matches.empty and "confidence_score" in entity_matches.columns:
        for _, row in entity_matches.iterrows():
            for aid in (row["actor_1"], row["actor_2"]):
                em_conf[aid] = max(em_conf.get(aid, 0), float(row["confidence_score"]))

    # Pre-compute per-cluster dimensions
    enriched = []
    for c in raw_clusters:
        entity_id = c["entity_id"]
        # Parse dates embedded in entity_id: "CLUSTER_2024-03-22_7d"
        parts     = entity_id.split("_")
        try:
            window_days = int(parts[-1].replace("d", ""))
        except ValueError:
            window_days = 30

        start_dt = c["first_detected"]
        end_dt   = c["last_detected"]
        if pd.isna(start_dt) or pd.isna(end_dt):
            continue

        # Pull incidents in this cluster's window
        grp = incidents[
            (incidents["incident_date"] >= start_dt) &
            (incidents["incident_date"] <= end_dt)
        ]

        n_inc      = len(grp)
        n_actors   = grp["lead_actor"].nunique()
        n_routes   = grp["route_id"].nunique()
        n_species  = grp["species"].nunique()
        density    = n_inc / max(window_days, 1)

        # Network confidence: mean entity-match score for actors in this cluster
        actor_ids  = grp["lead_actor"].dropna().unique().tolist()
        net_confs  = [em_conf[a] for a in actor_ids if a in em_conf]
        net_score  = float(np.mean(net_confs)) if net_confs else 0.0

        enriched.append({
            **c,
            "_density":    density,
            "_n_actors":   n_actors,
            "_n_routes":   n_routes,
            "_n_species":  n_species,
            "_net_score":  net_score,
            "_window":     window_days,
        })

    if not enriched:
        return []

    df = pd.DataFrame(enriched)

    # Normalise each axis to 0–100
    def _n(col):
        mx = df[col].max()
        return (df[col] / mx * 100) if mx > 0 else df[col] * 0

    df["dim_density"]  = _n("_density")
    df["dim_actors"]   = _n("_n_actors")
    df["dim_routes"]   = _n("_n_routes")
    df["dim_species"]  = _n("_n_species")
    df["dim_network"]  = df["_net_score"].clip(0, 100)

    df["investigation_score"] = (
        0.35 * df["dim_density"]
        + 0.25 * df["dim_actors"]
        + 0.20 * df["dim_routes"]
        + 0.10 * df["dim_species"]
        + 0.10 * df["dim_network"]
    ).round(2)

    df = df.sort_values("investigation_score", ascending=False).reset_index(drop=True)
    df["investigation_rank"] = df.index + 1

    # Build ranking explanation for each row
    ranked = []
    for _, row in df.head(top_n).iterrows():
        row_dict = {k: v for k, v in row.items() if not k.startswith("_")}
        row_dict["ranking_explanation"] = (
            f"Investigation score {row['investigation_score']:.1f}/100: "
            f"density={row['dim_density']:.0f}, "
            f"actor_overlap={row['dim_actors']:.0f}, "
            f"route_overlap={row['dim_routes']:.0f}, "
            f"species_overlap={row['dim_species']:.0f}, "
            f"network_confidence={row['dim_network']:.0f}."
        )
        ranked.append(row_dict)

    return ranked
# ══════════════════════════════════════════════════════════════════════════════

def detect_route_displacement(tables: dict) -> list[dict]:
    """
    Compare incident counts per route in the recent window vs baseline.
    Find pairs where one route declined while a structurally similar route rose.
    Similarity = shared source OR shared destination OR shared actors.
    """
    incidents = tables["incidents"]
    routes    = tables["routes"]
    ref       = _reference_date(incidents)
    cutoff_r  = ref - timedelta(days=WINDOW_RECENT)
    cutoff_b  = ref - timedelta(days=WINDOW_BASELINE)

    def _rate(df_filt, col="route_id"):
        return df_filt.groupby(col).size()

    recent_counts = _rate(incidents[incidents["incident_date"] >= cutoff_r])
    base_counts   = _rate(
        incidents[(incidents["incident_date"] >= cutoff_b) &
                  (incidents["incident_date"] <  cutoff_r)]
    )

    all_routes = set(incidents["route_id"].dropna())
    route_meta = routes.set_index("route_id").to_dict("index") if not routes.empty else {}

    alerts = []

    for r_a, r_b in itertools.combinations(all_routes, 2):
        r_a_recent = recent_counts.get(r_a, 0)
        r_a_base   = base_counts.get(r_a,   0)
        r_b_recent = recent_counts.get(r_b, 0)
        r_b_base   = base_counts.get(r_b,   0)

        # One declined, one rose — both must have had some activity
        declined = (r_a_base >= 3 and r_a_recent <= r_a_base * 0.4)
        rose     = (r_b_recent >= 3 and r_b_recent >= r_b_base * 2.0)
        if not (declined and rose):
            # swap direction
            declined = (r_b_base >= 3 and r_b_recent <= r_b_base * 0.4)
            rose     = (r_a_recent >= 3 and r_a_recent >= r_a_base * 2.0)
            if declined and rose:
                r_a, r_b = r_b, r_a   # r_a = declined, r_b = rose
            else:
                continue

        # Check structural similarity
        meta_a = route_meta.get(r_a, {})
        meta_b = route_meta.get(r_b, {})
        shared_src  = meta_a.get("source", "X") == meta_b.get("source", "Y")
        shared_dst  = meta_a.get("destination", "X") == meta_b.get("destination", "Y")

        actors_a = set(incidents[incidents["route_id"] == r_a]["lead_actor"].dropna())
        actors_b = set(incidents[incidents["route_id"] == r_b]["lead_actor"].dropna())
        shared_actors = bool(actors_a & actors_b)

        if not (shared_src or shared_dst or shared_actors):
            continue

        sim_count = sum([shared_src, shared_dst, shared_actors])
        drop_pct  = ((r_a_base - r_a_recent) / max(r_a_base, 1)) * 100
        rise_pct  = ((r_b_recent - r_b_base) / max(r_b_base + 1, 1)) * 100

        risk_score = _clamp(
            0.35 * min(rise_pct, 100)
            + 0.35 * min(drop_pct, 100)
            + 0.30 * (sim_count / 3 * 100)
        )

        if risk_score < WATCH:
            continue

        sim_str = []
        if shared_src:    sim_str.append("same source port")
        if shared_dst:    sim_str.append("same destination")
        if shared_actors: sim_str.append("overlapping actors")

        corr_a = meta_a.get("corridor", r_a)
        corr_b = meta_b.get("corridor", r_b)
        explanation = (
            f"Potential route displacement signal: activity on '{corr_a}' appears to have "
            f"declined (from {r_a_base} to {recent_counts.get(r_a, 0)} incidents) while "
            f"'{corr_b}' shows increased activity "
            f"(from {r_b_base} to {recent_counts.get(r_b, 0)} incidents). "
            f"Routes share: {', '.join(sim_str)}. "
            "Activity may have shifted toward an alternative corridor."
        )

        alerts.append({
            "alert_id":             _uid("ALT"),
            "pattern_type":         "ROUTE_DISPLACEMENT",
            "priority":             _priority(risk_score),
            "entity_type":          "ROUTE_PAIR",
            "entity_id":            f"{r_a}|{r_b}",
            "risk_score":           risk_score,
            "confidence":           round(min(risk_score, 95), 2),
            "first_detected":       incidents[
                incidents["route_id"].isin([r_a, r_b])
            ]["incident_date"].min(),
            "last_detected":        incidents[
                incidents["route_id"].isin([r_a, r_b])
            ]["incident_date"].max(),
            "incident_count":       r_a_base + r_b_recent,
            "related_actor_count":  len(actors_a | actors_b),
            "related_route_count":  2,
            "related_location_count": len({
                meta_a.get("source",""), meta_a.get("destination",""),
                meta_b.get("source",""), meta_b.get("destination","")
            }),
            "explanation":          explanation,
            "frequency_score":      round(min(rise_pct, 100), 2),
            "temporal_score":       round(min(drop_pct, 100), 2),
            "geographic_score":     round(sim_count / 3 * 100, 2),
            "network_score":        0.0,
            "recurrence_score":     0.0,
        })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# 8. PATTERN F — NETWORK EXPANSION
# ══════════════════════════════════════════════════════════════════════════════

def detect_network_expansion(tables: dict) -> list[dict]:
    """
    For each actor, split their activity into a baseline and recent window.
    If connections (routes, co-actors, destinations) grew significantly → alert.
    Also incorporate entity match confidence as a relationship signal.
    """
    incidents     = tables["incidents"]
    entity_matches= tables["entity_matches"]
    ref           = _reference_date(incidents)
    cutoff_r      = ref - timedelta(days=WINDOW_RECENT)
    cutoff_b      = ref - timedelta(days=WINDOW_BASELINE)

    def _actor_profile(df_filt):
        g = df_filt.groupby("lead_actor")
        return pd.DataFrame({
            "routes":  g["route_id"].apply(set),
            "dests":   g["destination"].apply(set),
            "species": g["species"].apply(set),
        })

    recent_profile = _actor_profile(incidents[incidents["incident_date"] >= cutoff_r])
    base_profile   = _actor_profile(
        incidents[(incidents["incident_date"] >= cutoff_b) &
                  (incidents["incident_date"] <  cutoff_r)]
    )

    # Build co-actor network from entity matches
    em_map: dict[str, set] = defaultdict(set)
    if not entity_matches.empty and "confidence_score" in entity_matches.columns:
        for _, row in entity_matches[entity_matches["confidence_score"] >= 60].iterrows():
            em_map[row["actor_1"]].add(row["actor_2"])
            em_map[row["actor_2"]].add(row["actor_1"])

    actors_in_both = set(recent_profile.index) & set(base_profile.index)

    alerts = []
    for aid in actors_in_both:
        r_prof = recent_profile.loc[aid]
        b_prof = base_profile.loc[aid]

        new_routes = r_prof["routes"] - b_prof["routes"]
        new_dests  = r_prof["dests"]  - b_prof["dests"]
        new_spec   = r_prof["species"]- b_prof["species"]

        if not (new_routes or new_dests or new_spec):
            continue

        expansion = len(new_routes)*2 + len(new_dests)*2 + len(new_spec)
        em_links  = len(em_map.get(aid, set()))

        route_growth = len(new_routes) / max(len(b_prof["routes"]), 1)
        dest_growth  = len(new_dests)  / max(len(b_prof["dests"]),  1)

        risk_score = _clamp(
            0.35 * min(route_growth * 100, 100)
            + 0.30 * min(dest_growth * 100, 100)
            + 0.20 * min(expansion * 10, 100)
            + 0.15 * min(em_links * 20, 100)
        )

        if risk_score < WATCH:
            continue

        parts = []
        if new_routes: parts.append(f"{len(new_routes)} new trafficking corridor(s)")
        if new_dests:  parts.append(f"{len(new_dests)} new destination(s)")
        if new_spec:   parts.append(f"{len(new_spec)} new species/commodity type(s)")
        if em_links:   parts.append(f"{em_links} entity-match relationship(s) detected")

        explanation = (
            f"Network expansion signal for actor {aid}: "
            + ("; ".join(parts) if parts else "increased connectivity detected")
            + "."
        )

        alerts.append({
            "alert_id":             _uid("ALT"),
            "pattern_type":         "NETWORK_EXPANSION",
            "priority":             _priority(risk_score),
            "entity_type":          "ACTOR",
            "entity_id":            aid,
            "risk_score":           risk_score,
            "confidence":           round(min(risk_score + 5, 100), 2),
            "first_detected":       incidents[incidents["lead_actor"] == aid]["incident_date"].min(),
            "last_detected":        incidents[incidents["lead_actor"] == aid]["incident_date"].max(),
            "incident_count":       int((incidents["lead_actor"] == aid).sum()),
            "related_actor_count":  em_links,
            "related_route_count":  len(r_prof["routes"]),
            "related_location_count": len(r_prof["dests"]),
            "explanation":          explanation,
            "frequency_score":      0.0,
            "temporal_score":       0.0,
            "geographic_score":     round(min(dest_growth * 100, 100), 2),
            "network_score":        round(min(em_links * 20, 100), 2),
            "recurrence_score":     round(min(route_growth * 100, 100), 2),
        })

    return alerts


# ══════════════════════════════════════════════════════════════════════════════
# 9. HIDDEN LINKS
# ══════════════════════════════════════════════════════════════════════════════

def build_hidden_links(tables: dict) -> list[dict]:
    """
    Discover cross-record relationships not explicit in the raw data.

    Link types:
      SHARED_ROUTE      — two incidents on the same route
      SHARED_VEHICLE    — two shipments using the same vehicle
      SHARED_ACTOR      — two incidents with the same lead_actor
      TEMPORAL_OVERLAP  — two incidents within 14 days on the same corridor
      ENTITY_MATCH      — actor pair from Phase 2 entity resolution
      SHARED_LOCATION   — two incidents at the same source
    """
    incidents     = tables["incidents"]
    shipments     = tables["shipments"]
    entity_matches= tables["entity_matches"]

    links = []

    # ── SHARED_ROUTE ──────────────────────────────────────────────────────────
    route_grp = incidents.dropna(subset=["route_id"]).groupby("route_id")["incident_id"].apply(list)
    for rid, inc_list in route_grp.items():
        if len(inc_list) < 2:
            continue
        # Sample up to 6 pairs per route to keep output manageable
        pairs = list(itertools.combinations(inc_list, 2))[:6]
        for i1, i2 in pairs:
            links.append({
                "link_id":           _uid("LNK"),
                "source_entity":     "INCIDENT",
                "source_id":         i1,
                "target_entity":     "INCIDENT",
                "target_id":         i2,
                "link_type":         "SHARED_ROUTE",
                "confidence":        65,
                "supporting_evidence": f"Both incidents recorded on route {rid}.",
                "risk_score":        65,
            })

    # ── SHARED_VEHICLE ────────────────────────────────────────────────────────
    veh_grp = shipments.dropna(subset=["vehicle_id"]).groupby("vehicle_id")["shipment_id"].apply(list)
    for vid, shp_list in veh_grp.items():
        if len(shp_list) < 2:
            continue
        pairs = list(itertools.combinations(shp_list, 2))[:4]
        for s1, s2 in pairs:
            links.append({
                "link_id":           _uid("LNK"),
                "source_entity":     "SHIPMENT",
                "source_id":         s1,
                "target_entity":     "SHIPMENT",
                "target_id":         s2,
                "link_type":         "SHARED_VEHICLE",
                "confidence":        75,
                "supporting_evidence": f"Both shipments used vehicle {vid}.",
                "risk_score":        72,
            })

    # ── SHARED_ACTOR ──────────────────────────────────────────────────────────
    actor_grp = incidents.dropna(subset=["lead_actor"]).groupby("lead_actor")["incident_id"].apply(list)
    for aid, inc_list in actor_grp.items():
        if len(inc_list) < 2:
            continue
        pairs = list(itertools.combinations(inc_list, 2))[:4]
        for i1, i2 in pairs:
            links.append({
                "link_id":           _uid("LNK"),
                "source_entity":     "INCIDENT",
                "source_id":         i1,
                "target_entity":     "INCIDENT",
                "target_id":         i2,
                "link_type":         "SHARED_ACTOR",
                "confidence":        78,
                "supporting_evidence": f"Both incidents share lead actor {aid}.",
                "risk_score":        75,
            })

    # ── TEMPORAL_OVERLAP ──────────────────────────────────────────────────────
    inc_sorted = incidents.dropna(subset=["incident_date", "route_id"]).sort_values("incident_date")
    inc_records = inc_sorted[["incident_id", "incident_date", "route_id", "species"]].to_dict("records")
    for i, r1 in enumerate(inc_records):
        for r2 in inc_records[i+1:]:
            if (r2["incident_date"] - r1["incident_date"]).days > 14:
                break
            if r1["route_id"] == r2["route_id"]:
                days_apart = (r2["incident_date"] - r1["incident_date"]).days
                same_spec  = r1["species"] == r2["species"]
                conf = 80 if same_spec else 70
                links.append({
                    "link_id":           _uid("LNK"),
                    "source_entity":     "INCIDENT",
                    "source_id":         r1["incident_id"],
                    "target_entity":     "INCIDENT",
                    "target_id":         r2["incident_id"],
                    "link_type":         "TEMPORAL_OVERLAP",
                    "confidence":        conf,
                    "supporting_evidence": (
                        f"Same route, {days_apart}-day temporal proximity"
                        + (", same species." if same_spec else ".")
                    ),
                    "risk_score":        conf,
                })

    # ── ENTITY_MATCH ──────────────────────────────────────────────────────────
    if not entity_matches.empty:
        for _, row in entity_matches[entity_matches["confidence_score"] >= 60].iterrows():
            links.append({
                "link_id":           _uid("LNK"),
                "source_entity":     "ACTOR",
                "source_id":         row["actor_1"],
                "target_entity":     "ACTOR",
                "target_id":         row["actor_2"],
                "link_type":         "ENTITY_MATCH",
                "confidence":        round(row["confidence_score"], 2),
                "supporting_evidence": str(row.get("matched_features", "")),
                "risk_score":        round(row["confidence_score"] * 0.9, 2),
            })

    return links


# ══════════════════════════════════════════════════════════════════════════════
# 10. NETWORK GRAPH
# ══════════════════════════════════════════════════════════════════════════════

def build_network_graph(tables: dict, hidden_links: list[dict],
                        all_alerts: list[dict]) -> nx.Graph:
    """
    Nodes: actors, incidents, routes, locations.
    Edges: hidden_links + entity_matches + actor→incident edges.
    Node attributes include risk_score where available.
    """
    G = nx.Graph()

    actors    = tables["actors"]
    incidents = tables["incidents"]
    routes    = tables["routes"]

    # Build risk lookup from alerts
    alert_risk: dict[str, float] = {}
    for a in all_alerts:
        alert_risk[a["entity_id"]] = max(alert_risk.get(a["entity_id"], 0), a["risk_score"])

    # Actor nodes
    for _, row in actors.iterrows():
        G.add_node(row["actor_id"],
                   node_type="ACTOR",
                   label=row.get("full_name", row["actor_id"]),
                   role=row.get("role", ""),
                   nationality=row.get("nationality", ""),
                   threat_score=int(row.get("threat_score", 0)),
                   risk_score=alert_risk.get(row["actor_id"], 0))

    # Incident nodes
    for _, row in incidents.iterrows():
        G.add_node(row["incident_id"],
                   node_type="INCIDENT",
                   label=row["incident_id"],
                   species=row.get("species", ""),
                   date=str(row.get("incident_date", "")),
                   risk_score=alert_risk.get(row["incident_id"], 0))

    # Route nodes
    if not routes.empty:
        for _, row in routes.iterrows():
            G.add_node(row["route_id"],
                       node_type="ROUTE",
                       label=row.get("corridor", row["route_id"]),
                       source=row.get("source", ""),
                       destination=row.get("destination", ""),
                       historical_risk=float(row.get("historical_risk", 0)),
                       risk_score=alert_risk.get(row["route_id"], 0))

    # Actor → Incident edges
    for _, row in incidents.dropna(subset=["lead_actor"]).iterrows():
        if G.has_node(row["lead_actor"]) and G.has_node(row["incident_id"]):
            G.add_edge(row["lead_actor"], row["incident_id"],
                       relationship_type="LEAD_ACTOR",
                       confidence=90,
                       risk_score=0)

    # Incident → Route edges
    for _, row in incidents.dropna(subset=["route_id"]).iterrows():
        if G.has_node(row["incident_id"]) and G.has_node(row["route_id"]):
            G.add_edge(row["incident_id"], row["route_id"],
                       relationship_type="USED_ROUTE",
                       confidence=90,
                       risk_score=0)

    # Hidden link edges
    for lnk in hidden_links:
        src = lnk["source_id"]
        tgt = lnk["target_id"]
        if G.has_node(src) and G.has_node(tgt):
            # Only add if not already connected or if new link has higher confidence
            if not G.has_edge(src, tgt):
                G.add_edge(src, tgt,
                           relationship_type=lnk["link_type"],
                           confidence=lnk["confidence"],
                           risk_score=lnk["risk_score"])

    return G


# ══════════════════════════════════════════════════════════════════════════════
# 11. find_hidden_links()  — signal-aware, per-connection reasoning
# ══════════════════════════════════════════════════════════════════════════════

def find_hidden_links(entity_id: str, G: nx.Graph,
                      tables: dict,
                      max_depth: int = 2, top_n: int = 10) -> list[dict]:
    """
    Given an incident or actor ID, return the top-N connected entities ranked
    by composite evidence strength rather than a single fixed edge weight.

    For each neighbour we collect every distinct signal that connects it to the
    query entity and compute a composite confidence from those signals:

    Signals tracked
    ───────────────
    shared_route        +30 pts  (same route_id in incidents)
    same_species        +20 pts  (same species in incidents)
    temporal_proximity  +20 pts  (within 14 days, decaying linearly to 0 at 30d)
    shared_actor        +25 pts  (same lead_actor)
    shared_vehicle      +20 pts  (same vehicle_id in shipments)
    entity_match        +up to 40 pts (Phase-2 confidence score × 0.4)
    route_risk_bonus    +10 pts  (if the connecting route is flagged CRITICAL/HIGH)

    Composite = min(sum(signals), 100)
    Ties broken by number of distinct signal types.
    """
    if not G.has_node(entity_id):
        return []

    incidents      = tables.get("incidents",      pd.DataFrame())
    shipments      = tables.get("shipments",       pd.DataFrame())
    entity_matches = tables.get("entity_matches",  pd.DataFrame())
    routes         = tables.get("routes",          pd.DataFrame())

    # ── Pre-build lookup tables for fast signal computation ──────────────────

    # route_id → set of incident_ids
    route_to_incs: dict[str, set] = defaultdict(set)
    if not incidents.empty:
        for _, r in incidents.dropna(subset=["route_id", "incident_id"]).iterrows():
            route_to_incs[r["route_id"]].add(r["incident_id"])

    # incident_id → {route_id, species, lead_actor, date}
    inc_meta: dict[str, dict] = {}
    if not incidents.empty:
        for _, r in incidents.iterrows():
            inc_meta[r["incident_id"]] = {
                "route_id":   r.get("route_id"),
                "species":    r.get("species"),
                "actor":      r.get("lead_actor"),
                "date":       r.get("incident_date"),
            }

    # shipment_id → vehicle_id; vehicle_id → set of shipment_ids
    veh_to_shps: dict[str, set] = defaultdict(set)
    shp_to_veh:  dict[str, str] = {}
    if not shipments.empty:
        for _, r in shipments.dropna(subset=["vehicle_id", "shipment_id"]).iterrows():
            veh_to_shps[r["vehicle_id"]].add(r["shipment_id"])
            shp_to_veh[r["shipment_id"]] = r["vehicle_id"]

    # entity-match lookup: actor_id → [(other_actor_id, score)]
    em_lookup: dict[str, list] = defaultdict(list)
    if not entity_matches.empty and "confidence_score" in entity_matches.columns:
        for _, r in entity_matches.iterrows():
            em_lookup[r["actor_1"]].append((r["actor_2"], float(r["confidence_score"])))
            em_lookup[r["actor_2"]].append((r["actor_1"], float(r["confidence_score"])))

    # route risk bonus: route_id → True if high-risk
    high_risk_routes: set = set()
    if not routes.empty and "historical_risk" in routes.columns:
        high_risk_routes = set(routes[routes["historical_risk"] >= 70]["route_id"].tolist())

    # ── Query entity's own attributes ────────────────────────────────────────
    q_type    = G.nodes[entity_id].get("node_type", "UNKNOWN")
    q_meta    = inc_meta.get(entity_id, {})
    q_actor   = (entity_id if q_type == "ACTOR"
                 else q_meta.get("actor"))
    q_route   = q_meta.get("route_id")
    q_species = q_meta.get("species")
    q_date    = q_meta.get("date")

    # If the query entity is an ACTOR, derive representative attributes
    # from its incident history (most-common route, most-common species, latest date)
    if q_type == "ACTOR" and not incidents.empty:
        actor_incs = incidents[incidents["lead_actor"] == entity_id]
        if not actor_incs.empty:
            q_route   = actor_incs["route_id"].mode().iloc[0]   if actor_incs["route_id"].notna().any()  else None
            q_species = actor_incs["species"].mode().iloc[0]    if actor_incs["species"].notna().any()   else None
            q_date    = actor_incs["incident_date"].dropna().max() if actor_incs["incident_date"].notna().any() else None

    def _compute_signals(nbr: str) -> tuple[float, list[str]]:
        """
        Return (composite_confidence_0_100, [human_readable_signal_strings]).

        Signal point budget (sums to 100 when all fire for strong connections):

        INCIDENT neighbours
          shared_route            40 pts  (+15 bonus if high-risk corridor)
          same_species            25 pts
          temporal_proximity      20 pts  (linear decay over 30 days)
          shared_lead_actor       30 pts
          shared_vehicle          20 pts

        ACTOR neighbours
          entity_match            em_score × 0.75  (up to 75 pts for 100% match)
          shared_corridors        min(n × 15, 45)
          co_shipments            min(n × 10, 30)

        ROUTE neighbours
          primary_corridor        40 pts
          actor_incidents_on_route min(n × 12, 36)
          high_risk_bonus         20 pts (≥80) / 12 pts (≥60)
          volume_bonus            min(n_total × 2, 24)

        Depth-2 penalty applied only to genuine depth-2 hops (not direct neighbours).
        """
        pts    = 0.0
        signals: list[str] = []
        n_type = G.nodes[nbr].get("node_type", "UNKNOWN")

        # cache direct-neighbour set for depth penalty check
        direct_neighbours = set(G.neighbors(entity_id))

        # ── Neighbour is an INCIDENT ──────────────────────────────────────────
        if n_type == "INCIDENT":
            n_meta = inc_meta.get(nbr, {})

            # shared route (core signal)
            if q_route and n_meta.get("route_id") == q_route:
                bonus = 15 if q_route in high_risk_routes else 0
                pts  += 40 + bonus
                signals.append(
                    f"Shared route {q_route}"
                    + (" (high-risk corridor)" if bonus else "")
                )

            # same species
            if q_species and n_meta.get("species") == q_species:
                pts += 25
                signals.append(f"Same species ({q_species})")

            # temporal proximity — linear decay 20→0 over 30 days
            n_date = n_meta.get("date")
            if q_date and n_date and not pd.isna(q_date) and not pd.isna(n_date):
                gap = abs((n_date - q_date).days)
                if gap <= 30:
                    t_pts = round(20 * (1 - gap / 30), 1)
                    pts  += t_pts
                    signals.append(f"{gap}-day temporal proximity")

            # shared lead actor
            if (q_meta.get("actor") and n_meta.get("actor")
                    and q_meta["actor"] == n_meta["actor"]):
                pts += 30
                signals.append(f"Same lead actor ({q_meta['actor']})")

            # shared vehicle
            q_veh = shp_to_veh.get(entity_id)
            n_veh = shp_to_veh.get(nbr)
            if q_veh and n_veh and q_veh == n_veh:
                pts += 20
                signals.append(f"Shared vehicle ({q_veh})")

        # ── Neighbour is an ACTOR ─────────────────────────────────────────────
        elif n_type == "ACTOR":
            # entity-match from Phase-2 (strongest single signal)
            for (other, em_score) in em_lookup.get(q_actor or "", []):
                if other == nbr:
                    em_pts = round(em_score * 0.75, 1)   # 95% match → 71 pts
                    pts   += em_pts
                    signals.append(
                        f"Entity-match link (Phase-2 score {em_score:.0f}%)"
                    )
                    break

            # shared route history
            if not incidents.empty:
                q_routes_set = set(
                    incidents[incidents["lead_actor"] == (q_actor or "")]["route_id"].dropna()
                )
                n_routes_set = set(
                    incidents[incidents["lead_actor"] == nbr]["route_id"].dropna()
                )
                shared_rts = q_routes_set & n_routes_set
                if shared_rts:
                    rt_pts = min(len(shared_rts) * 15, 45)
                    pts   += rt_pts
                    signals.append(
                        f"{len(shared_rts)} shared trafficking corridor(s)"
                    )

            # co-occurring shipments
            if not shipments.empty:
                q_incs = set(
                    shipments[shipments["actor_id"] == (q_actor or "")]["incident_id"].dropna()
                )
                n_incs = set(
                    shipments[shipments["actor_id"] == nbr]["incident_id"].dropna()
                )
                common = q_incs & n_incs
                if common:
                    co_pts = min(len(common) * 10, 30)
                    pts   += co_pts
                    signals.append(f"{len(common)} co-occurring shipment(s)")

        # ── Neighbour is a ROUTE ──────────────────────────────────────────────
        elif n_type == "ROUTE":
            # primary corridor used by query actor
            if q_route == nbr:
                pts += 40
                signals.append("Query entity's primary corridor")
            elif not incidents.empty and q_actor:
                actor_on_route = incidents[
                    (incidents["lead_actor"] == q_actor) &
                    (incidents["route_id"]   == nbr)
                ]
                if len(actor_on_route) > 0:
                    pts += min(len(actor_on_route) * 12, 36)
                    signals.append(
                        f"{len(actor_on_route)} incident(s) by this actor on route"
                    )

            # route risk level
            r_meta = G.nodes[nbr]
            hr = float(r_meta.get("historical_risk", 0))
            if hr >= 80:
                pts += 20
                signals.append(f"High-risk corridor (risk score {int(hr)})")
            elif hr >= 60:
                pts += 12
                signals.append(f"Elevated-risk corridor (risk score {int(hr)})")

            # volume
            if not incidents.empty:
                n_on_route = int((incidents["route_id"] == nbr).sum())
                if n_on_route >= 5:
                    pts += min(n_on_route * 2, 24)
                    signals.append(f"{n_on_route} total incidents on this route")

        # ── Fallback ──────────────────────────────────────────────────────────
        else:
            edge = G.get_edge_data(entity_id, nbr)
            if edge and not signals:
                base_conf = edge.get("confidence", 50)
                pts += base_conf * 0.6
                signals.append(f"Structural link (edge confidence {base_conf})")

        # Depth-2 penalty: only for nodes NOT directly connected to query entity
        if nbr not in direct_neighbours:
            pts *= 0.72

        return round(min(pts, 100.0), 1), signals

    # ── Collect all reachable nodes up to max_depth ───────────────────────────
    visited    = {entity_id}
    frontier   = list(G.neighbors(entity_id))
    depth2     = set()
    for n in list(frontier):
        visited.add(n)
    if max_depth >= 2:
        for n in frontier:
            for nn in G.neighbors(n):
                if nn not in visited:
                    depth2.add(nn)
                    visited.add(nn)

    candidates = set(frontier) | depth2

    # Score every candidate
    scored = []
    for nbr in candidates:
        conf, signals = _compute_signals(nbr)
        if conf < 10 or not signals:
            continue
        n_data = G.nodes[nbr]
        scored.append({
            "entity_id":   nbr,
            "node_type":   n_data.get("node_type", "UNKNOWN"),
            "label":       n_data.get("label", nbr),
            "confidence":  conf,
            "signal_count":len(signals),
            "signals":     signals,
        })

    # Sort by confidence desc, break ties by signal count
    scored.sort(key=lambda x: (x["confidence"], x["signal_count"]), reverse=True)
    results = []
    for rank, item in enumerate(scored[:top_n], 1):
        results.append({"rank": rank, **item})
    return results


# ══════════════════════════════════════════════════════════════════════════════
# 12. OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

def save_outputs(all_alerts: list[dict], route_alerts: list[dict],
                 hidden_links: list[dict], G: nx.Graph) -> None:
    """Write the four output artefacts to OUTPUT_DIR."""

    # ── pattern_alerts.csv ────────────────────────────────────────────────────
    ALERT_COLS = [
        "alert_id", "pattern_type", "priority", "entity_type", "entity_id",
        "risk_score", "confidence", "first_detected", "last_detected",
        "incident_count", "related_actor_count", "related_route_count",
        "related_location_count", "explanation",
    ]
    alerts_df = pd.DataFrame(all_alerts)
    if not alerts_df.empty:
        for c in ALERT_COLS:
            if c not in alerts_df.columns:
                alerts_df[c] = ""
        alerts_df = alerts_df[ALERT_COLS].sort_values("risk_score", ascending=False)
    alerts_df.to_csv(os.path.join(OUTPUT_DIR, "pattern_alerts.csv"), index=False)
    print(f"  [SAVE] pattern_alerts.csv      → {len(alerts_df)} alerts")

    # ── route_intelligence.csv ────────────────────────────────────────────────
    RI_COLS = [
        "route_id", "source", "transit", "destination",
        "total_incidents", "recent_incidents", "historical_incidents",
        "unique_actors", "unique_species", "route_risk_score", "route_status",
    ]
    ri_rows = []
    for a in route_alerts:
        ri_rows.append({
            "route_id":            a["entity_id"],
            "source":              a.get("_source", ""),
            "transit":             a.get("_transit", ""),
            "destination":         a.get("_destination", ""),
            "total_incidents":     a.get("_total_incidents", 0),
            "recent_incidents":    a.get("_recent_incidents", 0),
            "historical_incidents":a.get("_historical_incidents", 0),
            "unique_actors":       a.get("_unique_actors", 0),
            "unique_species":      a.get("_unique_species", 0),
            "route_risk_score":    a["risk_score"],
            "route_status":        a.get("_route_status", "STABLE"),
        })
    ri_df = pd.DataFrame(ri_rows, columns=RI_COLS) if ri_rows else pd.DataFrame(columns=RI_COLS)
    ri_df = ri_df.sort_values("route_risk_score", ascending=False)
    ri_df.to_csv(os.path.join(OUTPUT_DIR, "route_intelligence.csv"), index=False)
    print(f"  [SAVE] route_intelligence.csv  → {len(ri_df)} routes")

    # ── hidden_links.csv ──────────────────────────────────────────────────────
    LINK_COLS = [
        "link_id", "source_entity", "source_id", "target_entity", "target_id",
        "link_type", "confidence", "supporting_evidence", "risk_score",
    ]
    links_df = pd.DataFrame(hidden_links, columns=LINK_COLS) if hidden_links else pd.DataFrame(columns=LINK_COLS)
    links_df = links_df.sort_values("risk_score", ascending=False)
    links_df.to_csv(os.path.join(OUTPUT_DIR, "hidden_links.csv"), index=False)
    print(f"  [SAVE] hidden_links.csv        → {len(links_df)} links")

    # ── trafficking_network.graphml ───────────────────────────────────────────
    graphml_path = os.path.join(OUTPUT_DIR, "trafficking_network.graphml")
    nx.write_graphml(G, graphml_path)
    print(f"  [SAVE] trafficking_network.graphml → {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # ── trafficking_network.json ──────────────────────────────────────────────
    json_data = {
        "nodes": [
            {"id": n, **{k: str(v) for k, v in G.nodes[n].items()}}
            for n in G.nodes
        ],
        "edges": [
            {"source": u, "target": v,
             **{k: str(v2) for k, v2 in G.get_edge_data(u, v, {}).items()}}
            for u, v in G.edges
        ],
    }
    json_path = os.path.join(OUTPUT_DIR, "trafficking_network.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)
    print(f"  [SAVE] trafficking_network.json    → written")


# ══════════════════════════════════════════════════════════════════════════════
# 13. SUMMARY PRINTER
# ══════════════════════════════════════════════════════════════════════════════

def print_summary(tables: dict, all_alerts: list[dict],
                  hidden_links: list[dict], G: nx.Graph) -> None:
    sep = "=" * 66

    incidents     = tables["incidents"]
    actors        = tables["actors"]
    routes        = tables["routes"]
    shipments     = tables["shipments"]
    entity_matches= tables["entity_matches"]

    pat_counts = defaultdict(int)
    for a in all_alerts:
        pat_counts[a["pattern_type"]] += 1

    print(f"\n{sep}")
    print("  PATTERN ENGINE — INTELLIGENCE SUMMARY")
    print(sep)
    print(f"\n  Dataset")
    print(f"    Total incidents          : {len(incidents)}")
    print(f"    Total actors             : {len(actors)}")
    print(f"    Total routes             : {len(routes)}")
    print(f"    Total shipments          : {len(shipments)}")
    print(f"    Entity relationships     : {len(entity_matches)}")

    print(f"\n  Detected Patterns")
    print(f"    Recurring actor alerts   : {pat_counts['RECURRING_ACTOR']}")
    print(f"    Emerging route alerts    : {pat_counts['ROUTE_EMERGING']}")
    print(f"    High-risk route alerts   : {pat_counts['ROUTE_HIGH_RISK']}")
    print(f"    Recurring route alerts   : {pat_counts['ROUTE_RECURRING']}")
    print(f"    Emerging hub alerts      : {pat_counts['EMERGING_HUB'] + pat_counts['HIGH_CONNECTIVITY_HUB']}")
    print(f"    Temporal clusters        : {pat_counts['TEMPORAL_CLUSTER']} (investigation-worthy; {sum(1 for a in all_alerts if a.get('pattern_type')=='TEMPORAL_CLUSTER')} shown in alerts)")
    print(f"    Route displacement       : {pat_counts['ROUTE_DISPLACEMENT']}")
    print(f"    Network expansion        : {pat_counts['NETWORK_EXPANSION']}")
    print(f"    Hidden links discovered  : {len(hidden_links)}")
    print(f"    Total alerts             : {len(all_alerts)}")

    # Highest-risk items
    if all_alerts:
        df_a = pd.DataFrame(all_alerts)

        def _top(ptype_filter):
            sub = df_a[df_a["entity_type"] == ptype_filter] if ptype_filter else df_a
            if sub.empty: return ("—", 0)
            row = sub.loc[sub["risk_score"].idxmax()]
            return (row["entity_id"], row["risk_score"])

        top_actor_id,    top_actor_score    = _top("ACTOR")
        top_route_id,    top_route_score    = _top("ROUTE")
        top_loc_id,      top_loc_score      = _top("LOCATION")
        top_any_id,      top_any_score      = _top(None)

        actor_info = actors.set_index("actor_id")["full_name"].to_dict() if not actors.empty else {}

        print(f"\n  Highest Risk")
        print(f"    Actor    : {actor_info.get(top_actor_id, top_actor_id):<35} score={top_actor_score:.1f}")
        print(f"    Route    : {top_route_id:<35} score={top_route_score:.1f}")
        print(f"    Location : {str(top_loc_id):<35} score={top_loc_score:.1f}")
        print(f"    Overall  : {top_any_id:<35} score={top_any_score:.1f}")

        # Top 10 alerts
        print(f"\n  Top 10 Intelligence Alerts")
        print(f"  {'#':<3} {'Priority':<10} {'Type':<25} {'Entity':<28} {'Score':>6}")
        print("  " + "-" * 74)
        top10 = df_a.nlargest(10, "risk_score")
        for rank, (_, row) in enumerate(top10.iterrows(), 1):
            eid = str(row["entity_id"])[:27]
            print(
                f"  {rank:<3} {row['priority']:<10} {row['pattern_type']:<25} "
                f"{eid:<28} {row['risk_score']:>6.1f}"
            )
            # Print explanation indented
            expl = str(row.get("explanation", ""))
            for chunk in [expl[i:i+90] for i in range(0, len(expl), 90)]:
                print(f"       {chunk}")

    print(f"\n{sep}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    sep = "=" * 66
    print(sep)
    print("  Wildlife Intelligence Platform — Pattern Detection Engine")
    print(sep)

    print("\n[LOAD] Reading data ...")
    tables = load_data()
    print(f"       Loaded {sum(len(v) for v in tables.values())} total records across {len(tables)} tables")

    print("\n[A] Detecting recurring actors ...")
    actor_alerts   = detect_recurring_actors(tables)
    print(f"    → {len(actor_alerts)} alerts")

    print("[B] Detecting emerging / high-risk routes ...")
    route_alerts   = detect_emerging_routes(tables)
    print(f"    → {len(route_alerts)} alerts")

    print("[C] Detecting emerging hubs ...")
    hub_alerts     = detect_emerging_hubs(tables)
    print(f"    → {len(hub_alerts)} alerts")

    print("[D] Detecting temporal clusters ...")
    cluster_alerts = detect_temporal_clusters(tables)
    print(f"    → {len(cluster_alerts)} raw signals")
    ranked_clusters = rank_clusters(cluster_alerts, tables, top_n=20)
    print(f"    → {len(ranked_clusters)} investigation-worthy clusters (ranked)")

    print("[E] Detecting route displacement ...")
    displace_alerts= detect_route_displacement(tables)
    print(f"    → {len(displace_alerts)} alerts")

    print("[F] Detecting network expansion ...")
    expand_alerts  = detect_network_expansion(tables)
    print(f"    → {len(expand_alerts)} alerts")

    print("[G] Building hidden links ...")
    hidden_links   = build_hidden_links(tables)
    print(f"    → {len(hidden_links)} links")

    all_alerts = (
        actor_alerts + route_alerts + hub_alerts +
        ranked_clusters + displace_alerts + expand_alerts
    )
    # De-duplicate by entity_id keeping highest risk_score
    seen_ids: dict[str, dict] = {}
    for a in all_alerts:
        key = f"{a['pattern_type']}|{a['entity_id']}"
        if key not in seen_ids or a["risk_score"] > seen_ids[key]["risk_score"]:
            seen_ids[key] = a
    all_alerts = list(seen_ids.values())

    print(f"\n[NET] Building network graph ...")
    G = build_network_graph(tables, hidden_links, all_alerts)

    print("\n[SAVE] Writing outputs ...")
    save_outputs(all_alerts, route_alerts, hidden_links, G)

    print_summary(tables, all_alerts, hidden_links, G)

    # ── Demo: find_hidden_links — actor query + incident query ───────────────
    if all_alerts:
        actor_info = tables["actors"].set_index("actor_id")["full_name"].to_dict() \
                     if not tables["actors"].empty else {}

        def _print_fhl(eid: str, label: str) -> None:
            results = find_hidden_links(eid, G, tables, max_depth=2, top_n=8)
            print(f"\n  ┌─ Query: {label} ({eid})")
            if not results:
                print("  │  (no connections found)")
                return
            for r in results:
                ntype = r["node_type"]
                nlabel = r.get("label", r["entity_id"])[:40]
                conf   = r["confidence"]
                sigs   = r.get("signals", [])
                print(f"  ├── [{ntype}] {nlabel}")
                for s in sigs:
                    print(f"  │     {s}")
                print(f"  │     Confidence: {conf:.1f}%")
            print("  └" + "─" * 50)

        # Pick top actor alert
        actor_alerts_only = [a for a in all_alerts if a["entity_type"] == "ACTOR"]
        top_actor_id = (
            max(actor_alerts_only, key=lambda x: x["risk_score"])["entity_id"]
            if actor_alerts_only else None
        )

        # Pick an incident that belongs to a high-risk cluster
        cluster_alerts_only = [a for a in all_alerts if a["pattern_type"] == "TEMPORAL_CLUSTER"]
        top_inc_id = None
        if cluster_alerts_only:
            top_cluster = max(cluster_alerts_only, key=lambda x: x["risk_score"])
            c_start = top_cluster["first_detected"]
            c_end   = top_cluster["last_detected"]
            cluster_incs = tables["incidents"][
                (tables["incidents"]["incident_date"] >= c_start) &
                (tables["incidents"]["incident_date"] <= c_end)
            ]
            if not cluster_incs.empty:
                top_inc_id = cluster_incs.iloc[0]["incident_id"]

        print(f"\n{'='*66}")
        print("  DEMO — find_hidden_links()")
        print(f"{'='*66}")

        if top_actor_id:
            _print_fhl(top_actor_id, actor_info.get(top_actor_id, top_actor_id))
        if top_inc_id:
            _print_fhl(top_inc_id, f"Incident {top_inc_id}")
        print()


if __name__ == "__main__":
    main()
