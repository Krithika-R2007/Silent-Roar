"""
Cross-Evidence Correlation Engine
Wildlife Trafficking Intelligence Platform — Phase 4
"""

import os
import json
import math
import uuid
import random
import itertools
import collections
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import networkx as nx

# ── reproducibility ──────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

DATA_DIR = "simulated_data"

KNOWN_SLANG = [
    "brown parcel", "blue bird", "ivory tea", "long horn",
    "after rain", "river crossing", "jungle fruit", "grey stone",
    "forest gift", "night delivery",
]

PROTECTED_AREAS = {
    "Nilgiri Biosphere":     {"lat": (10.8, 11.8), "lon": (76.0, 77.2)},
    "Anamalai Tiger Reserve":{"lat": (10.2, 10.9), "lon": (76.8, 77.4)},
    "Sundarbans":            {"lat": (21.5, 22.5), "lon": (88.5, 89.5)},
    "Tsavo Ecosystem":       {"lat": (-3.8, -1.5), "lon": (37.5, 39.5)},
    "Serengeti Buffer":      {"lat": (-3.5, -1.0), "lon": (34.0, 35.5)},
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. load_data
# ─────────────────────────────────────────────────────────────────────────────

def _load_csv(filename, date_cols=None):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, low_memory=False)
        # normalise column names
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        if date_cols:
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception:
        return pd.DataFrame()


def load_data():
    tables = {}
    tables["actors"]           = _load_csv("actors.csv")
    tables["incidents"]        = _load_csv("incidents.csv",
                                           date_cols=["incident_date"])
    tables["shipments"]        = _load_csv("shipments.csv",
                                           date_cols=["departure_date", "arrival_date"])
    tables["routes"]           = _load_csv("routes.csv")
    tables["messages"]         = _load_csv("messages.csv",
                                           date_cols=["timestamp"])
    tables["animal_events"]    = _load_csv("animal_events.csv",
                                           date_cols=["event_date"])
    tables["entity_matches"]   = _load_csv("entity_matches.csv")
    tables["pattern_alerts"]   = _load_csv("pattern_alerts.csv")
    tables["route_intelligence"]= _load_csv("route_intelligence.csv")
    tables["hidden_links"]     = _load_csv("hidden_links.csv")
    return tables


# ─────────────────────────────────────────────────────────────────────────────
# 2. prepare_indexes
# ─────────────────────────────────────────────────────────────────────────────

def prepare_indexes(tables):
    inc  = tables.get("incidents",      pd.DataFrame())
    shp  = tables.get("shipments",      pd.DataFrame())
    msg  = tables.get("messages",       pd.DataFrame())
    em   = tables.get("entity_matches", pd.DataFrame())
    hl   = tables.get("hidden_links",   pd.DataFrame())
    pa   = tables.get("pattern_alerts", pd.DataFrame())
    ri   = tables.get("route_intelligence", pd.DataFrame())
    ae   = tables.get("animal_events",  pd.DataFrame())
    act  = tables.get("actors",         pd.DataFrame())

    def _groupby(df, col):
        result = collections.defaultdict(list)
        if df.empty or col not in df.columns:
            return result
        for row in df.to_dict("records"):
            key = row.get(col)
            if pd.notna(key):
                result[key].append(row)
        return result

    idx = {}
    idx["inc_by_actor"]   = _groupby(inc, "lead_actor")
    idx["inc_by_route"]   = _groupby(inc, "route_id")
    idx["shp_by_incident"]= _groupby(shp, "incident_id")
    idx["shp_by_actor"]   = _groupby(shp, "actor_id")

    # messages: actor appears as sender OR receiver
    msg_by_actor = collections.defaultdict(list)
    if not msg.empty:
        for row in msg.to_dict("records"):
            s = row.get("sender_actor")
            r = row.get("receiver_actor")
            if pd.notna(s):
                msg_by_actor[s].append(row)
            if pd.notna(r) and r != s:
                msg_by_actor[r].append(row)
    idx["msg_by_actor"] = msg_by_actor

    idx["em_by_actor"]    = _groupby(em, "actor_1")
    # also add actor_2 side
    if not em.empty and "actor_2" in em.columns:
        for row in em.to_dict("records"):
            k = row.get("actor_2")
            if pd.notna(k):
                idx["em_by_actor"][k].append(row)

    # hidden_links: index by source_id AND target_id
    hl_by_entity = collections.defaultdict(list)
    if not hl.empty:
        for row in hl.to_dict("records"):
            for fld in ("source_id", "target_id"):
                k = row.get(fld)
                if pd.notna(k):
                    hl_by_entity[k].append(row)
    idx["hl_by_entity"] = hl_by_entity

    idx["alert_by_entity"] = _groupby(pa, "entity_id")
    idx["animal_by_area"]  = _groupby(ae, "protected_area")

    # route_intelligence: route_id → dict
    route_intel = {}
    if not ri.empty and "route_id" in ri.columns:
        for row in ri.to_dict("records"):
            route_intel[row["route_id"]] = row
    idx["route_intel"] = route_intel

    # ── pre-computed dataset-wide stats for fast normalisation ───────────────
    # actor-level stats
    stats = {}
    stats["all_actor_inc_counts"]   = [len(v) for v in idx["inc_by_actor"].values()]
    stats["all_actor_sp_counts"]    = [len({r.get("species") for r in v}) for v in idx["inc_by_actor"].values()]
    stats["all_actor_rte_breadths"] = [len({r.get("route_id") for r in v}) for v in idx["inc_by_actor"].values()]
    _all_spans = []
    for v in idx["inc_by_actor"].values():
        ds = [r["incident_date"] for r in v if pd.notna(r.get("incident_date"))]
        if len(ds) >= 2:
            _all_spans.append((max(ds) - min(ds)).days)
    stats["all_actor_time_spans"] = _all_spans

    # route-level stats
    stats["all_route_inc_counts"]   = [len(v) for v in idx["inc_by_route"].values()]
    stats["all_route_actor_counts"] = [len({r.get("lead_actor") for r in v}) for v in idx["inc_by_route"].values()]
    stats["all_route_sp_counts"]    = [len({r.get("species") for r in v}) for v in idx["inc_by_route"].values()]

    # route_intelligence stats
    stats["all_rrs"] = [_safe_float(v.get("route_risk_score", 0)) for v in idx["route_intel"].values()]
    stats["all_hl_counts"] = [len(v) for v in idx["hl_by_entity"].values()]
    stats["all_pa_scores"] = [
        _safe_float(al.get("risk_score", 0))
        for eid_alerts in idx["alert_by_entity"].values()
        for al in eid_alerts
    ]

    # location-level stats (from inc df)
    if not inc.empty:
        src_vc = inc["source_location"].value_counts() if "source_location" in inc.columns else pd.Series(dtype=int)
        dst_vc = inc["destination"].value_counts()      if "destination"      in inc.columns else pd.Series(dtype=int)
        stats["all_loc_counts"]       = src_vc.tolist() + dst_vc.tolist()
        stats["loc_actor_counts"]     = (
            inc.groupby("source_location")["lead_actor"].nunique().tolist()
            if "source_location" in inc.columns else [1]
        )
    else:
        stats["all_loc_counts"]   = [1]
        stats["loc_actor_counts"] = [1]

    # entity match stats per actor
    actor_ids_list = act.get("actor_id", pd.Series()).dropna().tolist() if not act.empty else []
    stats["all_match_counts"] = [
        len([m for m in idx["em_by_actor"].get(a, []) if _safe_float(m.get("confidence_score", 0)) >= 60])
        for a in actor_ids_list
    ]
    stats["all_hc_counts"] = [
        sum(1 for m in idx["em_by_actor"].get(a, []) if _safe_float(m.get("confidence_score", 0)) >= 80)
        for a in actor_ids_list
    ]

    # co-incident network (build once)
    G = nx.Graph()
    if not inc.empty and "route_id" in inc.columns:
        for rid, grp in inc.groupby("route_id"):
            actors_in_route = grp["lead_actor"].dropna().unique().tolist()
            for a1, a2 in itertools.combinations(actors_in_route, 2):
                G.add_edge(a1, a2)
    stats["co_incident_graph"] = G
    stats["all_degrees"]       = [d for _, d in G.degree()] if G.number_of_nodes() > 0 else [0]

    idx["stats"] = stats
    return idx


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_float(v, default=0.0):
    try:
        f = float(v)
        return 0.0 if math.isnan(f) else f
    except Exception:
        return default


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))


def _norm(value, all_values):
    """Min-max normalise value against a list/series; returns 0-1."""
    vals = [_safe_float(x) for x in all_values if pd.notna(x)]
    if not vals:
        return 0.0
    mn, mx = min(vals), max(vals)
    rng = mx - mn + 1e-6
    return _clamp((value - mn) / rng, 0.0, 1.0)


def _get_incident_latlons(inc_rows):
    pts = []
    for r in inc_rows:
        lat = _safe_float(r.get("latitude", None))
        lon = _safe_float(r.get("longitude", None))
        if lat != 0.0 or lon != 0.0:
            pts.append((lat, lon))
    return pts


def _area_for_point(lat, lon):
    for name, bb in PROTECTED_AREAS.items():
        if bb["lat"][0] <= lat <= bb["lat"][1] and bb["lon"][0] <= lon <= bb["lon"][1]:
            return name
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 3. calculate_trade_score
# ─────────────────────────────────────────────────────────────────────────────

def calculate_trade_score(target_type, target_id, tables, indexes):
    inc = tables.get("incidents", pd.DataFrame())
    if inc.empty:
        return 0.0

    score = 0.0

    if target_type == "INCIDENT":
        row_list = [r for r in inc.to_dict("records") if r.get("incident_id") == target_id]
        if not row_list:
            return 0.0
        row = row_list[0]

        route_id   = row.get("route_id")
        lead_actor = row.get("lead_actor")

        # incident_count on same route (max 20 pts)
        route_incs = indexes["inc_by_route"].get(route_id, [])
        all_route_counts = [len(v) for v in indexes["inc_by_route"].values()]
        inc_norm = _norm(len(route_incs), all_route_counts)
        score += inc_norm * 20

        # seizure (15 pts)
        if str(row.get("seizure_status", "")).strip().lower() == "seized":
            score += 15

        # quantity anomaly (15 pts)
        try:
            all_q = pd.to_numeric(inc["quantity"], errors="coerce").dropna()
            q_val = _safe_float(row.get("quantity", 0))
            if len(all_q) > 1 and q_val > all_q.mean() + 2 * all_q.std():
                score += 15
        except Exception:
            pass

        # recurrence: lead_actor in 3+ incidents (20 pts)
        actor_inc_count = len(indexes["inc_by_actor"].get(lead_actor, []))
        if actor_inc_count >= 3:
            score += 20

        # species diversity on route (10 pts)
        species_on_route = {r.get("species") for r in route_incs if r.get("species")}
        if len(species_on_route) >= 2:
            score += 10

        # temporal_density: incidents on same route within 30 days (20 pts)
        try:
            this_date = row.get("incident_date")
            if pd.notna(this_date):
                td = timedelta(days=30)
                nearby = [r for r in route_incs
                          if r.get("incident_id") != target_id
                          and pd.notna(r.get("incident_date"))
                          and abs((r["incident_date"] - this_date).days) <= 30]
                if nearby:
                    score += 20
        except Exception:
            pass

    elif target_type == "ACTOR":
        actor_incs = indexes["inc_by_actor"].get(target_id, [])
        if not actor_incs:
            return 0.0
        all_actor_counts = [len(v) for v in indexes["inc_by_actor"].values()]
        # incident_frequency (25 pts)
        score += _norm(len(actor_incs), all_actor_counts) * 25
        # commodity_breadth (20 pts)
        species_set = {r.get("species") for r in actor_incs if r.get("species")}
        all_species_counts = [len({r.get("species") for r in v}) for v in indexes["inc_by_actor"].values()]
        score += _norm(len(species_set), all_species_counts) * 20
        # route_breadth (20 pts)
        route_set = {r.get("route_id") for r in actor_incs if r.get("route_id")}
        all_route_breadths = [len({r.get("route_id") for r in v}) for v in indexes["inc_by_actor"].values()]
        score += _norm(len(route_set), all_route_breadths) * 20
        # time_span (20 pts)
        try:
            dates = [r["incident_date"] for r in actor_incs if pd.notna(r.get("incident_date"))]
            if len(dates) >= 2:
                span_days = (max(dates) - min(dates)).days
                all_spans = []
                for v in indexes["inc_by_actor"].values():
                    ds = [r["incident_date"] for r in v if pd.notna(r.get("incident_date"))]
                    if len(ds) >= 2:
                        all_spans.append((max(ds) - min(ds)).days)
                score += _norm(span_days, all_spans if all_spans else [span_days]) * 20
        except Exception:
            pass
        # seizure_rate (15 pts) — higher seizure rate = more caught = higher risk signal
        seized = sum(1 for r in actor_incs if str(r.get("seizure_status","")).strip().lower() == "seized")
        rate = seized / (len(actor_incs) + 1e-6)
        score += rate * 15

    elif target_type == "ROUTE":
        route_incs = indexes["inc_by_route"].get(target_id, [])
        if not route_incs:
            return 0.0
        all_route_counts = [len(v) for v in indexes["inc_by_route"].values()]
        # total_incidents (30 pts)
        score += _norm(len(route_incs), all_route_counts) * 30
        # seizure_rate (20 pts)
        seized = sum(1 for r in route_incs if str(r.get("seizure_status","")).strip().lower() == "seized")
        rate = seized / (len(route_incs) + 1e-6)
        score += rate * 20
        # unique actors (25 pts)
        actors = {r.get("lead_actor") for r in route_incs if r.get("lead_actor")}
        all_actor_counts = [len({r.get("lead_actor") for r in v}) for v in indexes["inc_by_route"].values()]
        score += _norm(len(actors), all_actor_counts) * 25
        # unique species (25 pts)
        species = {r.get("species") for r in route_incs if r.get("species")}
        all_sp_counts = [len({r.get("species") for r in v}) for v in indexes["inc_by_route"].values()]
        score += _norm(len(species), all_sp_counts) * 25

    elif target_type == "LOCATION":
        inc_df_loc = tables.get("incidents", pd.DataFrame())
        if inc_df_loc.empty:
            return 0.0
        mask = (inc_df_loc["source_location"] == target_id) | (inc_df_loc["destination"] == target_id)
        loc_inc_df2 = inc_df_loc[mask]
        loc_incs = loc_inc_df2.to_dict("records")
        if not loc_incs:
            return 0.0

        # all location counts for normalisation (pre-compute from value_counts)
        src_counts_ser = inc_df_loc["source_location"].value_counts() if "source_location" in inc_df_loc.columns else pd.Series(dtype=int)
        dst_counts_ser = inc_df_loc["destination"].value_counts()      if "destination"      in inc_df_loc.columns else pd.Series(dtype=int)
        all_loc_counts = src_counts_ser.tolist() + dst_counts_ser.tolist()

        score += _norm(len(loc_incs), all_loc_counts) * 35  # total incidents
        actors = set(loc_inc_df2["lead_actor"].dropna().tolist())
        all_actor_cnts = list(inc_df_loc.groupby("source_location")["lead_actor"].nunique().tolist()) if "source_location" in inc_df_loc.columns else [len(actors)]
        score += _norm(len(actors), all_actor_cnts if all_actor_cnts else [len(actors)]) * 25
        routes = set(loc_inc_df2["route_id"].dropna().tolist())
        score += _norm(len(routes), [1, 3, 5]) * 20  # route count simple buckets
        # recent growth: last 90 days vs total
        try:
            cutoff = inc_df_loc["incident_date"].max() - timedelta(days=90)
            recent_count = loc_inc_df2[loc_inc_df2["incident_date"] >= cutoff].shape[0]
            growth_rate = recent_count / (len(loc_incs) + 1e-6)
            score += growth_rate * 20
        except Exception:
            pass

    return _clamp(score)


# ─────────────────────────────────────────────────────────────────────────────
# 4. calculate_route_score
# ─────────────────────────────────────────────────────────────────────────────

def calculate_route_score(target_type, target_id, tables, indexes):
    score = 0.0
    ri = indexes.get("route_intel", {})

    # determine route_id set relevant to target
    if target_type == "ROUTE":
        route_ids = {target_id}
        route_incs = indexes["inc_by_route"].get(target_id, [])
    elif target_type == "INCIDENT":
        row_list = [r for r in tables.get("incidents", pd.DataFrame()).to_dict("records")
                    if r.get("incident_id") == target_id]
        if not row_list:
            return 0.0
        route_ids = {row_list[0].get("route_id")}
        route_incs = indexes["inc_by_route"].get(row_list[0].get("route_id"), [])
    elif target_type == "ACTOR":
        actor_incs = indexes["inc_by_actor"].get(target_id, [])
        route_ids  = {r.get("route_id") for r in actor_incs if r.get("route_id")}
        route_incs = []
        for rid in route_ids:
            route_incs.extend(indexes["inc_by_route"].get(rid, []))
    elif target_type == "LOCATION":
        inc_df = tables.get("incidents", pd.DataFrame())
        if not inc_df.empty:
            loc_incs = inc_df[(inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)]
            route_ids = set(loc_incs["route_id"].dropna().tolist())
            route_incs = loc_incs.to_dict("records")
        else:
            return 0.0
    else:
        return 0.0

    if not route_ids:
        return 0.0

    # 1) route_risk_score from route_intelligence (30%)
    rrs_vals = [_safe_float(ri[rid].get("route_risk_score", 0)) for rid in route_ids if rid in ri]
    rrs = (sum(rrs_vals) / len(rrs_vals)) if rrs_vals else 0.0
    all_rrs = indexes.get("stats", {}).get("all_rrs", [rrs])
    score += _norm(rrs, all_rrs if all_rrs else [rrs]) * 30

    # 2) hidden_link_density (20%)
    all_inc_ids  = {r.get("incident_id") for r in route_incs}
    hl_count = sum(len(indexes["hl_by_entity"].get(rid, [])) for rid in route_ids)
    hl_count += sum(len(indexes["hl_by_entity"].get(iid, [])) for iid in all_inc_ids)
    all_hl_counts = indexes.get("stats", {}).get("all_hl_counts", [hl_count])
    score += _norm(hl_count, all_hl_counts if all_hl_counts else [hl_count]) * 20

    # 3) vehicle_sharing (20%)
    shp = tables.get("shipments", pd.DataFrame())
    vehicle_sharing = 0
    if not shp.empty and route_incs:
        inc_ids = list(all_inc_ids)
        route_shp = shp[shp["incident_id"].isin(inc_ids)] if "incident_id" in shp.columns else pd.DataFrame()
        if not route_shp.empty and "vehicle_id" in route_shp.columns:
            vc = route_shp["vehicle_id"].value_counts()
            vehicle_sharing = int((vc > 1).sum())
    all_veh = []
    if not shp.empty and "vehicle_id" in shp.columns and "incident_id" in shp.columns:
        for rid_i in indexes["inc_by_route"]:
            iids = {r.get("incident_id") for r in indexes["inc_by_route"][rid_i]}
            sub  = shp[shp["incident_id"].isin(iids)]
            if not sub.empty:
                vc2 = sub["vehicle_id"].value_counts()
                all_veh.append(int((vc2 > 1).sum()))
    score += _norm(vehicle_sharing, all_veh if all_veh else [vehicle_sharing]) * 20

    # 4) actor_network_size (15%)
    actors = {r.get("lead_actor") for r in route_incs if r.get("lead_actor")}
    all_actor_net = [len({r.get("lead_actor") for r in v}) for v in indexes["inc_by_route"].values()]
    score += _norm(len(actors), all_actor_net if all_actor_net else [len(actors)]) * 15

    # 5) pattern_alert_score (15%)
    pa_scores = []
    for rid in route_ids:
        for al in indexes["alert_by_entity"].get(rid, []):
            pa_scores.append(_safe_float(al.get("risk_score", 0)))
    pa_max = max(pa_scores) if pa_scores else 0.0
    all_pa = indexes.get("stats", {}).get("all_pa_scores", [pa_max])
    score += _norm(pa_max, all_pa if all_pa else [pa_max]) * 15

    return _clamp(score)


# ─────────────────────────────────────────────────────────────────────────────
# 5. calculate_entity_score
# ─────────────────────────────────────────────────────────────────────────────

def calculate_entity_score(target_type, target_id, tables, indexes):
    score = 0.0

    # resolve actor set
    if target_type == "ACTOR":
        actor_set = {target_id}
    elif target_type == "INCIDENT":
        row_list = [r for r in tables.get("incidents", pd.DataFrame()).to_dict("records")
                    if r.get("incident_id") == target_id]
        actor_set = {row_list[0]["lead_actor"]} if row_list else set()
    elif target_type == "ROUTE":
        route_incs = indexes["inc_by_route"].get(target_id, [])
        actor_set  = {r.get("lead_actor") for r in route_incs if r.get("lead_actor")}
    elif target_type == "LOCATION":
        inc_df = tables.get("incidents", pd.DataFrame())
        if not inc_df.empty:
            mask = (inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)
            actor_set = set(inc_df.loc[mask, "lead_actor"].dropna().tolist())
        else:
            actor_set = set()
    else:
        return 0.0

    if not actor_set:
        return 0.0

    em_all = tables.get("entity_matches", pd.DataFrame())
    total_match_count = 0
    total_conf = []
    high_conf   = 0

    for actor_id in actor_set:
        matches = indexes["em_by_actor"].get(actor_id, [])
        conf60  = [m for m in matches if _safe_float(m.get("confidence_score", 0)) >= 60]
        total_match_count += len(conf60)
        for m in conf60:
            c = _safe_float(m.get("confidence_score", 0))
            total_conf.append(c)
            if c >= 80:
                high_conf += 1

    # entity_match_count (25 pts)
    all_match_counts = indexes.get("stats", {}).get("all_match_counts", [total_match_count])
    score += _norm(total_match_count, all_match_counts if all_match_counts else [total_match_count]) * 25

    # avg_match_confidence (20 pts)
    avg_conf = (sum(total_conf) / len(total_conf)) if total_conf else 0.0
    score += _norm(avg_conf, [0, 100]) * 20

    # high_conf_matches (15 pts)
    all_hc = indexes.get("stats", {}).get("all_hc_counts", [high_conf])
    score += _norm(high_conf, all_hc if all_hc else [high_conf]) * 15

    # incident_overlap: matched entities appear in same incidents/routes (20 pts)
    matched_actors = set()
    for actor_id in actor_set:
        for m in indexes["em_by_actor"].get(actor_id, []):
            other = m.get("actor_2") if m.get("actor_1") == actor_id else m.get("actor_1")
            if other:
                matched_actors.add(other)
    overlap = 0
    actor_routes = set()
    for actor_id in actor_set:
        actor_routes |= {r.get("route_id") for r in indexes["inc_by_actor"].get(actor_id, []) if r.get("route_id")}
    for ma in matched_actors:
        ma_routes = {r.get("route_id") for r in indexes["inc_by_actor"].get(ma, []) if r.get("route_id")}
        if actor_routes & ma_routes:
            overlap += 1
    overlap_rate = overlap / (len(matched_actors) + 1e-6) if matched_actors else 0.0
    score += overlap_rate * 20

    # network_position: degree in co-incident network (20 pts)
    try:
        G = indexes.get("stats", {}).get("co_incident_graph", nx.Graph())
        all_degrees = indexes.get("stats", {}).get("all_degrees", [0])
        degrees = []
        for actor_id in actor_set:
            if actor_id in G:
                degrees.append(G.degree(actor_id))
        avg_degree = (sum(degrees) / len(degrees)) if degrees else 0.0
        score += _norm(avg_degree, all_degrees if all_degrees else [avg_degree]) * 20
    except Exception:
        pass

    return _clamp(score)


# ─────────────────────────────────────────────────────────────────────────────
# 6. calculate_linguistic_score
# ─────────────────────────────────────────────────────────────────────────────

def calculate_linguistic_score(target_type, target_id, tables, indexes):
    score = 0.0
    msg_df = tables.get("messages", pd.DataFrame())
    if msg_df.empty:
        return 0.0

    # gather relevant messages
    rel_msgs = []
    target_routes = set()

    if target_type == "ACTOR":
        rel_msgs = indexes["msg_by_actor"].get(target_id, [])
        actor_incs = indexes["inc_by_actor"].get(target_id, [])
        target_routes = {r.get("route_id") for r in actor_incs if r.get("route_id")}

    elif target_type == "INCIDENT":
        row_list = [r for r in tables.get("incidents", pd.DataFrame()).to_dict("records")
                    if r.get("incident_id") == target_id]
        if row_list:
            row = row_list[0]
            lead = row.get("lead_actor")
            target_routes = {row.get("route_id")}
            actor_msgs = indexes["msg_by_actor"].get(lead, []) if lead else []
            inc_date = row.get("incident_date")
            if pd.notna(inc_date):
                rel_msgs = [m for m in actor_msgs
                            if pd.notna(m.get("timestamp"))
                            and abs((m["timestamp"] - inc_date).days) <= 30]
            else:
                rel_msgs = actor_msgs

    elif target_type == "ROUTE":
        target_routes = {target_id}
        rel_msgs = [m for m in msg_df.to_dict("records")
                    if str(m.get("linked_route", "")).strip() == target_id]

    elif target_type == "LOCATION":
        inc_df = tables.get("incidents", pd.DataFrame())
        if not inc_df.empty:
            loc_mask = (inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)
            loc_actors = set(inc_df.loc[loc_mask, "lead_actor"].dropna().tolist())
            target_routes = set(inc_df.loc[loc_mask, "route_id"].dropna().tolist())
            for a in loc_actors:
                rel_msgs.extend(indexes["msg_by_actor"].get(a, []))

    if not rel_msgs:
        return 0.0

    # slang_frequency (base: 40 pts)
    slang_msgs = [m for m in rel_msgs if str(m.get("contains_slang", "")).strip().lower() == "true"]
    slang_rate  = len(slang_msgs) / (len(rel_msgs) + 1e-6)
    score += slang_rate * 40

    # route_reference_boost (+20 pts)
    if target_routes:
        route_ref_msgs = [m for m in rel_msgs
                          if str(m.get("linked_route", "")).strip() in target_routes]
        if route_ref_msgs:
            score += 20

    # repetition_boost: same known phrase appears 3+ times (+15 pts)
    phrase_counts = collections.Counter()
    for m in rel_msgs:
        text = str(m.get("message_text", "")).lower()
        for phrase in KNOWN_SLANG:
            if phrase in text:
                phrase_counts[phrase] += 1
    if any(c >= 3 for c in phrase_counts.values()):
        score += 15

    # actor_convergence: 3+ distinct senders with slang (+25 pts)
    slang_senders = {m.get("sender_actor") for m in slang_msgs if m.get("sender_actor")}
    if len(slang_senders) >= 3:
        score += 25

    return _clamp(score)


# ─────────────────────────────────────────────────────────────────────────────
# 7. calculate_animal_score
# ─────────────────────────────────────────────────────────────────────────────

def _resolve_latlons(target_type, target_id, tables, indexes):
    """Return list of (lat, lon) for the target."""
    pts = []
    inc_df = tables.get("incidents", pd.DataFrame())

    if target_type == "INCIDENT":
        rows = [r for r in inc_df.to_dict("records") if r.get("incident_id") == target_id]
        pts = _get_incident_latlons(rows)

    elif target_type == "ACTOR":
        rows = indexes["inc_by_actor"].get(target_id, [])
        pts  = _get_incident_latlons(rows)

    elif target_type == "ROUTE":
        rows = indexes["inc_by_route"].get(target_id, [])
        pts  = _get_incident_latlons(rows)

    elif target_type == "LOCATION":
        if not inc_df.empty:
            mask = (inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)
            rows = inc_df.loc[mask].to_dict("records")
            pts  = _get_incident_latlons(rows)
    return pts


def calculate_animal_score(target_type, target_id, tables, indexes):
    pts = _resolve_latlons(target_type, target_id, tables, indexes)
    if not pts:
        return 0.0

    # find overlapping protected areas
    overlapping_areas = set()
    for lat, lon in pts:
        a = _area_for_point(lat, lon)
        if a:
            overlapping_areas.add(a)

    if not overlapping_areas:
        return 0.0

    ae_idx = indexes.get("animal_by_area", {})
    score = 0.0

    # get incident dates for temporal proximity
    inc_df = tables.get("incidents", pd.DataFrame())
    if target_type == "INCIDENT":
        rows = [r for r in inc_df.to_dict("records") if r.get("incident_id") == target_id]
    elif target_type == "ACTOR":
        rows = indexes["inc_by_actor"].get(target_id, [])
    elif target_type == "ROUTE":
        rows = indexes["inc_by_route"].get(target_id, [])
    elif target_type == "LOCATION":
        mask = (inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)
        rows = inc_df.loc[mask].to_dict("records") if not inc_df.empty else []
    else:
        rows = []

    inc_dates = [r["incident_date"] for r in rows if pd.notna(r.get("incident_date"))]

    area_scores = []
    has_temporal_boost = False

    for area in overlapping_areas:
        ae_rows = ae_idx.get(area, [])
        if not ae_rows:
            continue
        anomaly_vals = [_safe_float(r.get("anomaly_score", 0)) for r in ae_rows]
        mean_anomaly = sum(anomaly_vals) / (len(anomaly_vals) + 1e-6)
        anomaly_rate = sum(1 for v in anomaly_vals if v > 0.3) / (len(anomaly_vals) + 1e-6)

        # geographic_overlap_score
        geo_sc = mean_anomaly * 100

        # temporal_proximity: animal event within 60 days of incident
        for ae_row in ae_rows:
            ev_date = ae_row.get("event_date")
            if pd.notna(ev_date):
                for inc_d in inc_dates:
                    if abs((ev_date - inc_d).days) <= 60:
                        has_temporal_boost = True
                        break

        area_scores.append(geo_sc)

    if not area_scores:
        return 0.0

    base_score = sum(area_scores) / len(area_scores)
    score = base_score

    if has_temporal_boost:
        score += 15

    # cap non-incident targets at 60
    if target_type != "INCIDENT":
        score = min(score, 60.0)

    return _clamp(score)


# ─────────────────────────────────────────────────────────────────────────────
# 8. calculate_alignment
# ─────────────────────────────────────────────────────────────────────────────

def calculate_alignment(target_type, target_id, scores_dict, tables, indexes):
    score = 0.0
    inc_df = tables.get("incidents", pd.DataFrame())
    msg_df = tables.get("messages",  pd.DataFrame())

    # gather incidents for target
    if target_type == "INCIDENT":
        target_rows = [r for r in inc_df.to_dict("records") if r.get("incident_id") == target_id]
    elif target_type == "ACTOR":
        target_rows = indexes["inc_by_actor"].get(target_id, [])
    elif target_type == "ROUTE":
        target_rows = indexes["inc_by_route"].get(target_id, [])
    elif target_type == "LOCATION":
        if not inc_df.empty:
            mask = (inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)
            target_rows = inc_df.loc[mask].to_dict("records")
        else:
            target_rows = []
    else:
        target_rows = []

    # 1. geographic_alignment (+20): do lat/lons cluster within 2 degrees?
    pts = _get_incident_latlons(target_rows)
    if len(pts) >= 2:
        lats = [p[0] for p in pts]
        lons = [p[1] for p in pts]
        if (max(lats) - min(lats)) <= 2.0 and (max(lons) - min(lons)) <= 2.0:
            score += 20
        elif (max(lats) - min(lats)) <= 5.0 and (max(lons) - min(lons)) <= 5.0:
            score += 10
    elif len(pts) == 1:
        score += 10

    # 2. temporal_alignment (+20): incidents + messages + animal events cluster within 30 days
    inc_dates = [r["incident_date"] for r in target_rows if pd.notna(r.get("incident_date"))]
    actors    = {r.get("lead_actor") for r in target_rows if r.get("lead_actor")}
    msg_dates = []
    for a in actors:
        msg_dates.extend([m["timestamp"] for m in indexes["msg_by_actor"].get(a, [])
                          if pd.notna(m.get("timestamp"))])

    all_dates = inc_dates + msg_dates
    if len(all_dates) >= 2:
        try:
            span = (max(all_dates) - min(all_dates)).days
            if span <= 30:
                score += 20
            elif span <= 90:
                score += 10
        except Exception:
            pass

    # 3. actor_alignment (+20): same actors appear in trade + linguistic evidence
    trade_actors   = actors
    target_routes  = {r.get("route_id") for r in target_rows if r.get("route_id")}
    slang_senders  = set()
    if not msg_df.empty:
        slang_msgs = msg_df[msg_df["contains_slang"].astype(str).str.lower() == "true"]
        slang_senders = set(slang_msgs["sender_actor"].dropna().tolist())
    overlap_actors = trade_actors & slang_senders
    if len(overlap_actors) >= 2:
        score += 20
    elif len(overlap_actors) == 1:
        score += 10

    # 4. route_alignment (+20): same route in trade + route + linguistic
    linguistic_routes = set()
    if not msg_df.empty and "linked_route" in msg_df.columns:
        for a in actors:
            for m in indexes["msg_by_actor"].get(a, []):
                lr = m.get("linked_route")
                if pd.notna(lr):
                    linguistic_routes.add(str(lr).strip())
    if target_routes & linguistic_routes:
        score += 20
    elif target_routes:
        score += 5

    # 5. species_alignment (+20): species in trade evidence + animal area overlap
    # observed_movement in animal_events is numeric (movement counts), not species names.
    # Use geographic overlap as the proxy: if animal anomalies exist near trade incidents,
    # award points based on whether there is any detected animal score.
    species_in_incs = {r.get("species") for r in target_rows if r.get("species")}
    if scores_dict.get("animal_score", 0) > 20 and species_in_incs:
        score += 20
    elif scores_dict.get("animal_score", 0) > 10 and species_in_incs:
        score += 10

    return _clamp(score)


# ─────────────────────────────────────────────────────────────────────────────
# 9. calculate_risk
# ─────────────────────────────────────────────────────────────────────────────

def calculate_risk(scores, evidence_stream_count):
    raw = (
        scores.get("trade_score",      0) * 0.25 +
        scores.get("route_score",      0) * 0.25 +
        scores.get("entity_score",     0) * 0.15 +
        scores.get("linguistic_score", 0) * 0.15 +
        scores.get("animal_score",     0) * 0.10 +
        scores.get("cross_alignment",  0) * 0.10
    )
    boost_map = {2: 3, 3: 7, 4: 12, 5: 16}
    boost = boost_map.get(evidence_stream_count, 0)
    final = min(raw + boost, 97.0)
    return _clamp(final)


# ─────────────────────────────────────────────────────────────────────────────
# 10. calculate_confidence
# ─────────────────────────────────────────────────────────────────────────────

def calculate_confidence(scores, evidence_stream_count, tables, indexes, target_type, target_id):
    stream_scores = [
        scores.get("trade_score",      0),
        scores.get("route_score",      0),
        scores.get("entity_score",     0),
        scores.get("linguistic_score", 0),
        scores.get("animal_score",     0),
    ]

    # data_completeness (40 pts)
    active = sum(1 for s in stream_scores if s > 10)
    data_completeness = (active / 5.0) * 40

    # score_consistency (30 pts) — low variance = high consistency
    nonzero = [s for s in stream_scores if s > 0]
    if len(nonzero) >= 2:
        mean_nz = sum(nonzero) / len(nonzero)
        std_nz  = (sum((x - mean_nz) ** 2 for x in nonzero) / len(nonzero)) ** 0.5
        consistency = 1.0 - (std_nz / (mean_nz + 1e-6))
        consistency = max(0.0, min(1.0, consistency))
    elif len(nonzero) == 1:
        consistency = 0.5
    else:
        consistency = 0.0
    score_consistency = consistency * 30

    # corroboration (30 pts)
    corroboration = (evidence_stream_count / 5.0) * 30

    total = data_completeness + score_consistency + corroboration
    return _clamp(total)


# ─────────────────────────────────────────────────────────────────────────────
# 11. generate_explanation
# ─────────────────────────────────────────────────────────────────────────────

def generate_explanation(target_type, target_id, scores, tables, indexes):
    trade_s   = scores.get("trade_score",      0)
    route_s   = scores.get("route_score",      0)
    entity_s  = scores.get("entity_score",     0)
    ling_s    = scores.get("linguistic_score", 0)
    anim_s    = scores.get("animal_score",     0)
    align_s   = scores.get("cross_alignment",  0)
    risk      = scores.get("risk_score",       0)
    conf      = scores.get("confidence",       0)

    # build why_suspicious
    parts = []
    if risk >= 65:
        parts.append(f"This {target_type.lower()} shows a high-risk pattern (score {risk:.1f})")
    else:
        parts.append(f"This {target_type.lower()} exhibits risk indicators (score {risk:.1f})")

    if align_s > 70:
        parts.append("with strong cross-evidence convergence across multiple intelligence streams")
    if ling_s > 50:
        parts.append("with coded communication signals detected in associated messages")
    if anim_s > 30:
        parts.append("alongside environmental anomalies in overlapping protected areas")
    why_suspicious = " ".join(parts) + "."

    # supporting evidence bullets
    supporting = []
    if trade_s > 10:
        supporting.append(f"+ Trade evidence score {trade_s:.1f}: trafficking activity signals in incident and shipment data")
    if route_s > 10:
        supporting.append(f"+ Route intelligence score {route_s:.1f}: elevated risk on associated transport corridors")
    if entity_s > 10:
        supporting.append(f"+ Entity resolution score {entity_s:.1f}: possible links to known actors or alias networks")
    if ling_s > 10:
        supporting.append(f"+ Linguistic intelligence score {ling_s:.1f}: coded slang or route references in communications")
    if anim_s > 10:
        supporting.append(f"+ Environmental signal score {anim_s:.1f}: animal movement anomalies in geographic overlap zone")
    if align_s > 30:
        supporting.append(f"+ Cross-evidence alignment {align_s:.1f}: multiple independent streams point to same entity/location/time")

    # convergence summary
    active_streams = [k for k, v in {
        "Trade": trade_s, "Route": route_s, "Entity": entity_s,
        "Linguistic": ling_s, "Animal": anim_s
    }.items() if v > 10]
    if len(active_streams) >= 3:
        convergence_summary = f"Strong convergence: {', '.join(active_streams)} streams independently corroborate risk indicators."
    elif len(active_streams) == 2:
        convergence_summary = f"Moderate convergence: {' and '.join(active_streams)} streams show alignment."
    elif len(active_streams) == 1:
        convergence_summary = f"Single-stream signal ({active_streams[0]}); additional corroboration needed."
    else:
        convergence_summary = "Insufficient evidence streams for convergence assessment."

    # uncertainties
    uncertainties = []
    if trade_s <= 10:
        uncertainties.append("Trade evidence is limited or absent — incident data may be incomplete")
    if ling_s <= 10:
        uncertainties.append("No significant linguistic signals detected — communications data may be sparse")
    if anim_s <= 10:
        uncertainties.append("No environmental overlap detected — geographic coordinates may not align with protected areas")
    if conf < 50:
        uncertainties.append("Confidence is moderate — evidence streams are inconsistent or incomplete")
    if not uncertainties:
        uncertainties.append("Evidence appears consistent but field verification is recommended")

    # recommended_priority
    if risk >= 80 and conf >= 65:
        priority = "IMMEDIATE"
    elif risk >= 80 and conf < 65:
        priority = "HIGH"
    elif risk >= 65 and conf >= 60:
        priority = "HIGH"
    elif risk >= 65 and conf < 60:
        priority = "MONITOR"
    elif risk >= 45:
        priority = "MONITOR"
    else:
        priority = "LOW"

    return {
        "why_suspicious":       why_suspicious,
        "supporting_evidence":  supporting,
        "evidence_scores": {
            "trade_score":      round(trade_s, 2),
            "route_score":      round(route_s, 2),
            "entity_score":     round(entity_s, 2),
            "linguistic_score": round(ling_s, 2),
            "animal_score":     round(anim_s, 2),
            "cross_alignment":  round(align_s, 2),
            "risk_score":       round(risk, 2),
            "confidence":       round(conf, 2),
        },
        "convergence_summary":  convergence_summary,
        "uncertainties":        uncertainties,
        "recommended_priority": priority,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 12. generate_alerts
# ─────────────────────────────────────────────────────────────────────────────

def generate_alerts(all_scores, tables):
    alerts = []
    for entry in all_scores:
        risk   = _safe_float(entry.get("risk_score",             0))
        conf   = _safe_float(entry.get("intelligence_confidence", 0))
        n_str  = int(entry.get("evidence_stream_count",           0))
        t_type = entry.get("target_type", "")
        t_id   = entry.get("target_id",   "")
        expl   = entry.get("explanation", {})

        if risk >= 80 and n_str >= 3:
            priority = "CRITICAL"
        elif risk >= 65 and n_str >= 2:
            priority = "HIGH"
        else:
            continue

        alerts.append({
            "alert_id":             f"ALT-{uuid.uuid4().hex[:8].upper()}",
            "target_type":          t_type,
            "target_id":            t_id,
            "priority":             priority,
            "risk_score":           round(risk, 2),
            "confidence":           round(conf, 2),
            "evidence_stream_count":n_str,
            "explanation":          expl.get("why_suspicious", "") if isinstance(expl, dict) else str(expl),
        })
    return alerts


# ─────────────────────────────────────────────────────────────────────────────
# 13. analyze_target  (full intelligence profile)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_target(target_type, target_id, tables, indexes):
    trade_s   = calculate_trade_score(target_type, target_id, tables, indexes)
    route_s   = calculate_route_score(target_type, target_id, tables, indexes)
    entity_s  = calculate_entity_score(target_type, target_id, tables, indexes)
    ling_s    = calculate_linguistic_score(target_type, target_id, tables, indexes)
    anim_s    = calculate_animal_score(target_type, target_id, tables, indexes)

    stream_names = []
    if trade_s  > 10: stream_names.append("TRADE")
    if route_s  > 10: stream_names.append("ROUTE")
    if entity_s > 10: stream_names.append("ENTITY")
    if ling_s   > 10: stream_names.append("LINGUISTIC")
    if anim_s   > 10: stream_names.append("ANIMAL")
    n_streams = len(stream_names)

    scores_dict = {
        "trade_score":      trade_s,
        "route_score":      route_s,
        "entity_score":     entity_s,
        "linguistic_score": ling_s,
        "animal_score":     anim_s,
    }
    align_s = calculate_alignment(target_type, target_id, scores_dict, tables, indexes)
    scores_dict["cross_alignment"] = align_s

    risk_s = calculate_risk(scores_dict, n_streams)
    conf_s = calculate_confidence(scores_dict, n_streams, tables, indexes, target_type, target_id)
    scores_dict["risk_score"]  = risk_s
    scores_dict["confidence"]  = conf_s

    # investigation_priority
    if risk_s >= 80 and conf_s >= 65:
        priority = "IMMEDIATE"
    elif risk_s >= 80 and conf_s < 65:
        priority = "HIGH"
    elif risk_s >= 65 and conf_s >= 60:
        priority = "HIGH"
    elif risk_s >= 65 and conf_s < 60:
        priority = "MONITOR"
    elif risk_s >= 45:
        priority = "MONITOR"
    else:
        priority = "LOW"

    # supporting entities
    inc_df = tables.get("incidents", pd.DataFrame())
    supporting_incidents = []
    supporting_routes    = []
    supporting_actors    = []

    if target_type == "INCIDENT":
        supporting_incidents = [target_id]
        rows = [r for r in inc_df.to_dict("records") if r.get("incident_id") == target_id]
        if rows:
            supporting_routes = [rows[0].get("route_id")] if rows[0].get("route_id") else []
            supporting_actors = [rows[0].get("lead_actor")] if rows[0].get("lead_actor") else []
    elif target_type == "ACTOR":
        actor_incs = indexes["inc_by_actor"].get(target_id, [])
        supporting_incidents = [r.get("incident_id") for r in actor_incs if r.get("incident_id")][:10]
        supporting_routes    = list({r.get("route_id") for r in actor_incs if r.get("route_id")})[:5]
        supporting_actors    = [target_id]
    elif target_type == "ROUTE":
        route_incs = indexes["inc_by_route"].get(target_id, [])
        supporting_incidents = [r.get("incident_id") for r in route_incs if r.get("incident_id")][:10]
        supporting_routes    = [target_id]
        supporting_actors    = list({r.get("lead_actor") for r in route_incs if r.get("lead_actor")})[:5]
    elif target_type == "LOCATION":
        if not inc_df.empty:
            mask = (inc_df["source_location"] == target_id) | (inc_df["destination"] == target_id)
            loc_inc_df = inc_df.loc[mask]
            supporting_incidents = loc_inc_df["incident_id"].dropna().tolist()[:10]
            supporting_routes    = loc_inc_df["route_id"].dropna().unique().tolist()[:5]
            supporting_actors    = loc_inc_df["lead_actor"].dropna().unique().tolist()[:5]

    expl = generate_explanation(target_type, target_id, scores_dict, tables, indexes)

    # per-target alerts
    entry = {
        "target_type":            target_type,
        "target_id":              target_id,
        "risk_score":             risk_s,
        "intelligence_confidence":conf_s,
        "evidence_stream_count":  n_streams,
        "explanation":            expl,
    }
    alerts = generate_alerts([entry], tables)

    return {
        "target_type":             target_type,
        "target_id":               target_id,
        "risk_score":              round(risk_s, 2),
        "intelligence_confidence": round(conf_s, 2),
        "investigation_priority":  priority,
        "trade_score":             round(trade_s, 2),
        "route_score":             round(route_s, 2),
        "entity_score":            round(entity_s, 2),
        "linguistic_score":        round(ling_s, 2),
        "animal_score":            round(anim_s, 2),
        "cross_evidence_alignment":round(align_s, 2),
        "evidence_stream_count":   n_streams,
        "evidence_streams":        stream_names,
        "supporting_incidents":    supporting_incidents,
        "supporting_routes":       supporting_routes,
        "supporting_actors":       supporting_actors,
        "explanation":             expl,
        "alerts":                  alerts,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 14. save_outputs
# ─────────────────────────────────────────────────────────────────────────────

def _generate_title(entry):
    t_type = entry.get("target_type", "")
    t_id   = entry.get("target_id",   "")
    risk   = _safe_float(entry.get("risk_score", 0))
    streams = entry.get("evidence_streams", [])

    if t_type == "INCIDENT":
        if "LINGUISTIC" in streams and "TRADE" in streams:
            return "Coded Commodity Trafficking Event"
        if "ANIMAL" in streams:
            return "Wildlife Corridor Incident"
        return "High-Risk Trafficking Incident"
    elif t_type == "ACTOR":
        if "ENTITY" in streams and "TRADE" in streams:
            return "High-Risk Broker Network"
        if "LINGUISTIC" in streams:
            return "Coded-Communication Suspect"
        return "Elevated-Threat Actor Profile"
    elif t_type == "ROUTE":
        if risk >= 80:
            return "Critical Trafficking Corridor"
        if "ANIMAL" in streams:
            return "Recurring Wildlife Corridor"
        return "High-Activity Transport Route"
    elif t_type == "LOCATION":
        if risk >= 75:
            return "Strategic Trafficking Hub"
        return "Active Transit Location"
    return "Intelligence Target"


def save_outputs(all_scores, all_explanations, alerts, tables):
    os.makedirs(DATA_DIR, exist_ok=True)

    # ── Output 1: intelligence_scores.csv ────────────────────────────────────
    rows = []
    for e in all_scores:
        expl = all_explanations.get(e["target_id"], {})
        rows.append({
            "target_type":             e.get("target_type"),
            "target_id":               e.get("target_id"),
            "risk_score":              round(_safe_float(e.get("risk_score", 0)), 2),
            "intelligence_confidence": round(_safe_float(e.get("intelligence_confidence", 0)), 2),
            "investigation_priority":  e.get("investigation_priority", "LOW"),
            "trade_score":             round(_safe_float(e.get("trade_score", 0)), 2),
            "route_score":             round(_safe_float(e.get("route_score", 0)), 2),
            "entity_score":            round(_safe_float(e.get("entity_score", 0)), 2),
            "linguistic_score":        round(_safe_float(e.get("linguistic_score", 0)), 2),
            "animal_score":            round(_safe_float(e.get("animal_score", 0)), 2),
            "cross_evidence_alignment":round(_safe_float(e.get("cross_evidence_alignment", 0)), 2),
            "evidence_stream_count":   e.get("evidence_stream_count", 0),
            "evidence_streams":        "|".join(e.get("evidence_streams", [])),
            "supporting_incidents":    "|".join(e.get("supporting_incidents", [])),
            "supporting_routes":       "|".join(e.get("supporting_routes", [])),
            "supporting_actors":       "|".join(e.get("supporting_actors", [])),
            "explanation":             expl.get("why_suspicious", "") if isinstance(expl, dict) else "",
        })
    scores_df = pd.DataFrame(rows).sort_values("risk_score", ascending=False)
    scores_df.to_csv(os.path.join(DATA_DIR, "intelligence_scores.csv"), index=False)

    # ── Output 2: evidence_breakdown.json ────────────────────────────────────
    breakdown = []
    for e in all_scores:
        if _safe_float(e.get("risk_score", 0)) < 45:
            continue
        expl = all_explanations.get(e["target_id"], {})
        t_type = e.get("target_type", "")
        t_id   = e.get("target_id",   "")

        def _make_signal(stream_name, score_key):
            val = _safe_float(e.get(score_key, 0))
            return {"signal": stream_name, "value": round(val, 2),
                    "source": score_key, "source_id": t_id}

        evidence = {
            "trade":      [_make_signal("trade_evidence",      "trade_score")],
            "route":      [_make_signal("route_intelligence",  "route_score")],
            "entity":     [_make_signal("entity_resolution",   "entity_score")],
            "linguistic": [_make_signal("linguistic_analysis", "linguistic_score")],
            "animal":     [_make_signal("animal_events",       "animal_score")],
        }
        breakdown.append({
            "target_type":     t_type,
            "target_id":       t_id,
            "risk_score":      round(_safe_float(e.get("risk_score", 0)), 2),
            "confidence":      round(_safe_float(e.get("intelligence_confidence", 0)), 2),
            "evidence":        evidence,
            "why_suspicious":  expl.get("why_suspicious", "") if isinstance(expl, dict) else "",
            "uncertainties":   expl.get("uncertainties", []) if isinstance(expl, dict) else [],
        })

    with open(os.path.join(DATA_DIR, "evidence_breakdown.json"), "w") as f:
        json.dump(breakdown, f, indent=2, default=str)

    # ── Output 3: investigation_targets.csv ──────────────────────────────────
    inv_rows = []
    rank = 1
    for e in sorted(all_scores, key=lambda x: _safe_float(x.get("risk_score", 0)), reverse=True):
        if _safe_float(e.get("risk_score", 0)) < 45:
            continue
        expl  = all_explanations.get(e["target_id"], {})
        title = _generate_title(e)
        why   = expl.get("why_suspicious", "") if isinstance(expl, dict) else ""
        # trim to 1 sentence
        summary = why.split(".")[0] + "." if "." in why else why
        inv_rows.append({
            "rank":       rank,
            "target_type":e.get("target_type"),
            "target_id":  e.get("target_id"),
            "priority":   e.get("investigation_priority", "LOW"),
            "risk_score": round(_safe_float(e.get("risk_score", 0)), 2),
            "confidence": round(_safe_float(e.get("intelligence_confidence", 0)), 2),
            "title":      title,
            "summary":    summary,
        })
        rank += 1

    pd.DataFrame(inv_rows).to_csv(os.path.join(DATA_DIR, "investigation_targets.csv"), index=False)
    print(f"[SAVE] Outputs written to {DATA_DIR}/")


# ─────────────────────────────────────────────────────────────────────────────
# 15. print_summary
# ─────────────────────────────────────────────────────────────────────────────

def print_summary(all_scores, alerts, tables):
    total = len(all_scores)
    critical  = sum(1 for e in all_scores if e.get("investigation_priority") == "IMMEDIATE")
    high      = sum(1 for e in all_scores if e.get("investigation_priority") == "HIGH")
    monitor   = sum(1 for e in all_scores if e.get("investigation_priority") == "MONITOR")
    low       = sum(1 for e in all_scores if e.get("investigation_priority") == "LOW")
    avg_risk  = sum(_safe_float(e.get("risk_score", 0)) for e in all_scores) / (total + 1e-6)
    multi_src = sum(1 for e in all_scores if e.get("evidence_stream_count", 0) >= 2)
    three_str = sum(1 for e in all_scores if e.get("evidence_stream_count", 0) >= 3)

    by_risk  = sorted(all_scores, key=lambda x: _safe_float(x.get("risk_score", 0)), reverse=True)
    by_conf  = sorted(all_scores, key=lambda x: _safe_float(x.get("intelligence_confidence", 0)), reverse=True)
    by_align = sorted(all_scores, key=lambda x: _safe_float(x.get("cross_evidence_alignment", 0)), reverse=True)

    sep = "=" * 72

    print(f"\n{sep}")
    print(" CROSS-EVIDENCE CORRELATION ENGINE — INTELLIGENCE SUMMARY")
    print(sep)
    print(f"  Total targets analysed : {total}")
    print(f"  IMMEDIATE (critical)   : {critical}")
    print(f"  HIGH priority          : {high}")
    print(f"  MONITOR                : {monitor}")
    print(f"  LOW                    : {low}")
    print(f"  Average risk score     : {avg_risk:.1f}")
    print(f"  Multi-source targets   : {multi_src}  (≥2 evidence streams)")
    print(f"  3+ stream convergence  : {three_str}")
    print(f"  Total alerts generated : {len(alerts)}")

    if by_risk:
        top = by_risk[0]
        print(f"\n  Highest-risk target    : [{top['target_type']}] {top['target_id']}  risk={_safe_float(top['risk_score']):.1f}")
    if by_conf:
        top = by_conf[0]
        print(f"  Highest-confidence     : [{top['target_type']}] {top['target_id']}  conf={_safe_float(top['intelligence_confidence']):.1f}")
    if by_align:
        top = by_align[0]
        print(f"  Strongest cross-evidence correlation: [{top['target_type']}] {top['target_id']}  alignment={_safe_float(top['cross_evidence_alignment']):.1f}")

    print(f"\n{'─'*72}")
    print("  TOP 10 INTELLIGENCE TARGETS")
    print(f"{'─'*72}")
    hdr = f"  {'#':>3}  {'Type':<10} {'ID':<22} {'Priority':<10} {'Risk':>6} {'Conf':>6} {'Stms':>5}"
    print(hdr)
    print(f"  {'─'*67}")
    for i, e in enumerate(by_risk[:10], 1):
        t_type = e.get("target_type", "")[:9]
        t_id   = str(e.get("target_id", ""))[:20]
        prio   = e.get("investigation_priority", "LOW")[:9]
        risk   = _safe_float(e.get("risk_score", 0))
        conf   = _safe_float(e.get("intelligence_confidence", 0))
        stms   = e.get("evidence_stream_count", 0)
        print(f"  {i:>3}  {t_type:<10} {t_id:<22} {prio:<10} {risk:>6.1f} {conf:>6.1f} {stms:>5}")

    print(f"\n{sep}")
    print("  PHASE 4 COMPLETE")
    print(sep)


# ─────────────────────────────────────────────────────────────────────────────
# 16. main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("[INIT] Loading data...")
    tables  = load_data()
    indexes = prepare_indexes(tables)

    inc_df = tables.get("incidents", pd.DataFrame())
    act_df = tables.get("actors",    pd.DataFrame())
    rte_df = tables.get("routes",    pd.DataFrame())

    # ── build target lists ───────────────────────────────────────────────────
    incident_ids = inc_df["incident_id"].dropna().unique().tolist() if not inc_df.empty else []
    actor_ids    = act_df["actor_id"].dropna().unique().tolist()    if not act_df.empty else []
    route_ids    = rte_df["route_id"].dropna().unique().tolist()    if not rte_df.empty else []

    locations = []
    if not inc_df.empty:
        src  = inc_df["source_location"].dropna().unique().tolist() if "source_location" in inc_df.columns else []
        dest = inc_df["destination"].dropna().unique().tolist()      if "destination"      in inc_df.columns else []
        locations = list(set(src + dest))

    print(f"[TARGETS] Incidents={len(incident_ids)}  Actors={len(actor_ids)}  "
          f"Routes={len(route_ids)}  Locations={len(locations)}")

    # ── scoring loop ─────────────────────────────────────────────────────────
    all_scores    = []
    all_expl_dict = {}

    def _score_targets(t_type, t_list):
        print(f"[SCORING] {t_type}s: {len(t_list)}...")
        for t_id in t_list:
            profile = analyze_target(t_type, t_id, tables, indexes)
            flat    = {
                "target_type":             t_type,
                "target_id":               t_id,
                "risk_score":              profile["risk_score"],
                "intelligence_confidence": profile["intelligence_confidence"],
                "investigation_priority":  profile["investigation_priority"],
                "trade_score":             profile["trade_score"],
                "route_score":             profile["route_score"],
                "entity_score":            profile["entity_score"],
                "linguistic_score":        profile["linguistic_score"],
                "animal_score":            profile["animal_score"],
                "cross_evidence_alignment":profile["cross_evidence_alignment"],
                "evidence_stream_count":   profile["evidence_stream_count"],
                "evidence_streams":        profile["evidence_streams"],
                "supporting_incidents":    profile["supporting_incidents"],
                "supporting_routes":       profile["supporting_routes"],
                "supporting_actors":       profile["supporting_actors"],
                "explanation":             profile["explanation"],
            }
            all_scores.append(flat)
            if profile["risk_score"] >= 45:
                all_expl_dict[t_id] = profile["explanation"]

    _score_targets("INCIDENT", incident_ids)
    _score_targets("ACTOR",    actor_ids)
    _score_targets("ROUTE",    route_ids)
    _score_targets("LOCATION", locations)

    # ── alerts ───────────────────────────────────────────────────────────────
    alerts = generate_alerts(all_scores, tables)
    print(f"[ALERTS] Generated {len(alerts)} alerts.")

    # ── save ─────────────────────────────────────────────────────────────────
    save_outputs(all_scores, all_expl_dict, alerts, tables)

    # ── summary ──────────────────────────────────────────────────────────────
    print_summary(all_scores, alerts, tables)

    # ── DEMO: full profiles for top incident and top actor ───────────────────
    by_risk = sorted(all_scores, key=lambda x: _safe_float(x.get("risk_score", 0)), reverse=True)

    top_inc = next((e for e in by_risk if e["target_type"] == "INCIDENT"), None)
    top_act = next((e for e in by_risk if e["target_type"] == "ACTOR"),    None)

    sep = "=" * 72

    if top_inc:
        print(f"\n{sep}")
        print(" DEMO — FULL PROFILE: HIGHEST-RISK INCIDENT")
        print(sep)
        profile = analyze_target("INCIDENT", top_inc["target_id"], tables, indexes)
        _print_profile(profile)

    if top_act:
        print(f"\n{sep}")
        print(" DEMO — FULL PROFILE: HIGHEST-RISK ACTOR")
        print(sep)
        profile = analyze_target("ACTOR", top_act["target_id"], tables, indexes)
        _print_profile(profile)


def _print_profile(p):
    print(f"  Target : [{p['target_type']}] {p['target_id']}")
    print(f"  Priority: {p['investigation_priority']}   "
          f"Risk: {p['risk_score']:.1f}   Confidence: {p['intelligence_confidence']:.1f}")
    print(f"  Evidence streams ({p['evidence_stream_count']}): {', '.join(p['evidence_streams']) if p['evidence_streams'] else 'none'}")
    print(f"  Trade={p['trade_score']:.1f}  Route={p['route_score']:.1f}  Entity={p['entity_score']:.1f}  "
          f"Ling={p['linguistic_score']:.1f}  Animal={p['animal_score']:.1f}  Align={p['cross_evidence_alignment']:.1f}")

    expl = p.get("explanation", {})
    if expl:
        print(f"\n  Why suspicious: {expl.get('why_suspicious', '')}")
        print(f"  Convergence: {expl.get('convergence_summary', '')}")
        print("  Supporting evidence:")
        for bullet in expl.get("supporting_evidence", []):
            print(f"    {bullet}")
        print("  Uncertainties:")
        for u in expl.get("uncertainties", []):
            print(f"    - {u}")

    inc_list = p.get("supporting_incidents", [])
    if inc_list:
        print(f"  Supporting incidents: {', '.join(inc_list[:5])}")
    rte_list = p.get("supporting_routes", [])
    if rte_list:
        print(f"  Supporting routes  : {', '.join(rte_list[:5])}")
    act_list = p.get("supporting_actors", [])
    if act_list:
        print(f"  Supporting actors  : {', '.join(act_list[:5])}")

    alerts = p.get("alerts", [])
    if alerts:
        print(f"  Alerts ({len(alerts)}):")
        for al in alerts:
            print(f"    [{al['priority']}] {al['alert_id']}  risk={al['risk_score']}")


if __name__ == "__main__":
    main()
