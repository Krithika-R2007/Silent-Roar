"""
entity_resolution.py
====================
Wildlife Intelligence Platform – Phase 2
Entity Resolution Engine

Loads simulated_data/ CSVs and discovers duplicate / related actors
using a transparent 100-point weighted scoring system.

Score breakdown
---------------
  Name similarity      40 pts   (rapidfuzz ratio on full_name)
  Alias similarity     20 pts   (rapidfuzz ratio on alias)
  Same nationality     10 pts   (exact match)
  Same primary region  15 pts   (exact match)
  Shared route         15 pts   (shared route_id via incidents/shipments)

Outputs
-------
  simulated_data/entity_matches.csv   – all matches ≥ 60
  simulated_data/actor_network.graphml – NetworkX graph

Usage
-----
  python entity_resolution.py
"""

import os
import itertools

import pandas as pd
import numpy as np
import networkx as nx
from rapidfuzz import fuzz

# ── Configuration ─────────────────────────────────────────────────────────────
DATA_DIR    = "simulated_data"
OUTPUT_DIR  = "simulated_data"

ACTORS_CSV    = os.path.join(DATA_DIR, "actors.csv")
INCIDENTS_CSV = os.path.join(DATA_DIR, "incidents.csv")
SHIPMENTS_CSV = os.path.join(DATA_DIR, "shipments.csv")
ROUTES_CSV    = os.path.join(DATA_DIR, "routes.csv")
MESSAGES_CSV  = os.path.join(DATA_DIR, "messages.csv")

MATCHES_OUT  = os.path.join(OUTPUT_DIR, "entity_matches.csv")
GRAPHML_OUT  = os.path.join(OUTPUT_DIR, "actor_network.graphml")

# Scoring weights (must sum to 100)
W_NAME       = 40   # full_name fuzzy similarity
W_ALIAS      = 20   # alias fuzzy similarity
W_NATIONAL   = 10   # same nationality
W_REGION     = 15   # same primary_region
W_ROUTE      = 15   # shared trafficking route

THRESHOLD_HIGH     = 80   # High Confidence
THRESHOLD_POSSIBLE = 60   # Possible Match  (ignored below this)


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Read all relevant CSVs from simulated_data/.
    Returns: actors, incidents, shipments, routes, messages DataFrames.
    """
    print("[LOAD] Reading CSVs from:", os.path.abspath(DATA_DIR))

    actors    = pd.read_csv(ACTORS_CSV)
    incidents = pd.read_csv(INCIDENTS_CSV)
    shipments = pd.read_csv(SHIPMENTS_CSV)
    routes    = pd.read_csv(ROUTES_CSV)
    messages  = pd.read_csv(MESSAGES_CSV)

    print(f"       actors={len(actors)}  incidents={len(incidents)}  "
          f"shipments={len(shipments)}  routes={len(routes)}  messages={len(messages)}")
    return actors, incidents, shipments, routes, messages


# ══════════════════════════════════════════════════════════════════════════════
# 2. ROUTE MAP BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_actor_route_map(
    incidents: pd.DataFrame,
    shipments: pd.DataFrame,
) -> dict[str, set[str]]:
    """
    Build a mapping  actor_id → set of route_ids  the actor is linked to.

    Sources considered:
      - incidents.lead_actor  (direct route_id on the incident)
      - shipments.actor_id    → joined to incidents to get route_id
    """
    actor_routes: dict[str, set[str]] = {}

    def _add(actor_id: str, route_id: str) -> None:
        if pd.isna(actor_id) or pd.isna(route_id):
            return
        actor_routes.setdefault(actor_id, set()).add(route_id)

    # From incidents directly
    for _, row in incidents.iterrows():
        _add(row["lead_actor"], row["route_id"])

    # From shipments joined to incidents
    merged = shipments.merge(
        incidents[["incident_id", "route_id"]],
        on="incident_id",
        how="left",
    )
    for _, row in merged.iterrows():
        _add(row["actor_id"], row["route_id"])

    return actor_routes


# ══════════════════════════════════════════════════════════════════════════════
# 3. ROUTE LABEL BUILDER  (for human-readable reasons)
# ══════════════════════════════════════════════════════════════════════════════

def build_route_labels(routes: pd.DataFrame) -> dict[str, str]:
    """
    Returns  route_id → "Source–Destination"  string, e.g.
    "RTE-ABC" → "Chennai Port–Mombasa"
    """
    labels: dict[str, str] = {}
    for _, row in routes.iterrows():
        labels[row["route_id"]] = f"{row['source']}–{row['destination']}"
    return labels


# ══════════════════════════════════════════════════════════════════════════════
# 4. SCORING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def score_pair(
    a1: pd.Series,
    a2: pd.Series,
    actor_routes: dict[str, set[str]],
    route_labels: dict[str, str],
) -> tuple[float, str]:
    """
    Compute a 0–100 confidence score between two actor rows.

    Returns
    -------
    (score, matched_features_string)
    """
    features: list[str] = []
    score: float = 0.0

    # ── Name similarity (40 pts) ──────────────────────────────────────────────
    name_sim = fuzz.ratio(
        str(a1["full_name"]).lower(),
        str(a2["full_name"]).lower(),
    ) / 100.0                          # normalise to 0–1
    name_pts = round(W_NAME * name_sim, 2)
    score += name_pts
    if name_sim >= 0.60:
        features.append(f"Similar name ({int(name_sim*100)}%)")

    # ── Alias similarity (20 pts) ─────────────────────────────────────────────
    alias_sim = fuzz.ratio(
        str(a1["alias"]).lower(),
        str(a2["alias"]).lower(),
    ) / 100.0
    alias_pts = round(W_ALIAS * alias_sim, 2)
    score += alias_pts
    if alias_sim >= 0.60:
        features.append(f"Similar alias ({int(alias_sim*100)}%)")

    # ── Same nationality (10 pts) ─────────────────────────────────────────────
    if (
        pd.notna(a1["nationality"])
        and pd.notna(a2["nationality"])
        and str(a1["nationality"]).strip().lower()
        == str(a2["nationality"]).strip().lower()
    ):
        score += W_NATIONAL
        features.append(f"Same nationality ({a1['nationality']})")

    # ── Same primary region (15 pts) ──────────────────────────────────────────
    if (
        pd.notna(a1["primary_region"])
        and pd.notna(a2["primary_region"])
        and str(a1["primary_region"]).strip().lower()
        == str(a2["primary_region"]).strip().lower()
    ):
        score += W_REGION
        features.append(f"Same region ({a1['primary_region']})")

    # ── Shared trafficking route (15 pts) ─────────────────────────────────────
    routes_1 = actor_routes.get(a1["actor_id"], set())
    routes_2 = actor_routes.get(a2["actor_id"], set())
    shared   = routes_1 & routes_2

    if shared:
        score += W_ROUTE
        # Show at most 2 corridor labels to keep the reason readable
        corridor_labels = [route_labels.get(r, r) for r in list(shared)[:2]]
        features.append(f"Shared corridor ({', '.join(corridor_labels)})")

    matched_features = "; ".join(features) if features else "No strong features"
    return round(score, 2), matched_features


def confidence_level(score: float) -> str:
    """Map numeric score to a human-readable confidence tier."""
    if score >= THRESHOLD_HIGH:
        return "High Confidence"
    if score >= THRESHOLD_POSSIBLE:
        return "Possible Match"
    return "Low"


# ══════════════════════════════════════════════════════════════════════════════
# 5. PAIRWISE COMPARISON LOOP
# ══════════════════════════════════════════════════════════════════════════════

def run_entity_resolution(
    actors: pd.DataFrame,
    actor_routes: dict[str, set[str]],
    route_labels: dict[str, str],
) -> pd.DataFrame:
    """
    Iterate over every unique pair of actors (n choose 2),
    score them, and collect matches above the threshold.

    Returns a DataFrame of matches with columns:
        actor_1, actor_2, confidence_score, confidence_level, matched_features
    """
    actor_records = actors.to_dict("records")
    n_actors      = len(actor_records)
    total_pairs   = n_actors * (n_actors - 1) // 2

    print(f"\n[COMPARE] {n_actors} actors → {total_pairs:,} pairs to evaluate …")

    rows = []
    for idx, (a1, a2) in enumerate(itertools.combinations(actor_records, 2)):
        score, features = score_pair(
            pd.Series(a1),
            pd.Series(a2),
            actor_routes,
            route_labels,
        )
        if score >= THRESHOLD_POSSIBLE:
            rows.append({
                "actor_1":           a1["actor_id"],
                "actor_1_name":      a1["full_name"],
                "actor_2":           a2["actor_id"],
                "actor_2_name":      a2["full_name"],
                "confidence_score":  score,
                "confidence_level":  confidence_level(score),
                "matched_features":  features,
            })

        # Progress every 5 000 comparisons
        if (idx + 1) % 5000 == 0:
            pct = (idx + 1) / total_pairs * 100
            print(f"         … {idx+1:,} / {total_pairs:,} ({pct:.1f}%) done")

    matches_df = pd.DataFrame(rows).sort_values(
        "confidence_score", ascending=False
    ).reset_index(drop=True)

    return matches_df


# ══════════════════════════════════════════════════════════════════════════════
# 6. NETWORKX GRAPH BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def build_graph(
    actors: pd.DataFrame,
    matches_df: pd.DataFrame,
) -> nx.Graph:
    """
    Build an undirected NetworkX graph.

    Nodes  = all actors  (with full_name, role, threat_score as attributes)
    Edges  = matched actor pairs with confidence_score as edge weight
             (only matches at or above THRESHOLD_POSSIBLE are included)
    """
    G = nx.Graph()

    # Add all actors as nodes
    for _, row in actors.iterrows():
        G.add_node(
            row["actor_id"],
            full_name    = str(row["full_name"]),
            alias        = str(row["alias"]),
            nationality  = str(row["nationality"]),
            role         = str(row["role"]),
            primary_region = str(row["primary_region"]),
            threat_score = int(row["threat_score"]),
        )

    # Add edges from the matches table
    for _, row in matches_df.iterrows():
        G.add_edge(
            row["actor_1"],
            row["actor_2"],
            weight           = float(row["confidence_score"]),
            confidence_level = str(row["confidence_level"]),
            matched_features = str(row["matched_features"]),
        )

    return G


# ══════════════════════════════════════════════════════════════════════════════
# 7. ANALYTICS PRINTER
# ══════════════════════════════════════════════════════════════════════════════

def print_analytics(
    actors: pd.DataFrame,
    matches_df: pd.DataFrame,
    G: nx.Graph,
    total_pairs: int,
) -> None:
    """Print a structured summary of the entity-resolution run."""
    sep = "=" * 64

    high_conf = matches_df[matches_df["confidence_level"] == "High Confidence"]
    possible  = matches_df[matches_df["confidence_level"] == "Possible Match"]

    print(f"\n{sep}")
    print("  ENTITY RESOLUTION — ANALYTICS")
    print(sep)

    print(f"\n  Total actors examined      : {len(actors)}")
    print(f"  Total pairs compared       : {total_pairs:,}")
    print(f"  Matches ≥ threshold        : {len(matches_df)}")
    print(f"    High Confidence (≥ 80)   : {len(high_conf)}")
    print(f"    Possible Match  (60–79)  : {len(possible)}")

    # ── Top 10 most connected actors ──────────────────────────────────────────
    print(f"\n  Top 10 Most Connected Actors (degree centrality):")
    degree_cent = nx.degree_centrality(G)
    actor_name_map = actors.set_index("actor_id")["full_name"].to_dict()

    top10 = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n  {'Rank':<5} {'Actor Name':<32} {'Actor ID':<18} {'Centrality':>10}  {'Connections':>11}")
    print("  " + "-" * 78)
    for rank, (actor_id, cent) in enumerate(top10, 1):
        name    = actor_name_map.get(actor_id, actor_id)
        degree  = G.degree(actor_id)
        print(f"  {rank:<5} {name:<32} {actor_id:<18} {cent:>10.4f}  {degree:>11}")

    # ── Sample high-confidence matches ────────────────────────────────────────
    if len(high_conf) > 0:
        print(f"\n  Sample High-Confidence Matches (top 5):")
        print(f"\n  {'Actor 1 Name':<28} {'Actor 2 Name':<28} {'Score':>6}  Reason")
        print("  " + "-" * 100)
        for _, row in high_conf.head(5).iterrows():
            print(
                f"  {row['actor_1_name']:<28} {row['actor_2_name']:<28} "
                f"{row['confidence_score']:>6.1f}  {row['matched_features']}"
            )

    print(f"\n{sep}\n")


# ══════════════════════════════════════════════════════════════════════════════
# 8. EXPORT
# ══════════════════════════════════════════════════════════════════════════════

def export_results(matches_df: pd.DataFrame, G: nx.Graph) -> None:
    """
    Save entity_matches.csv and actor_network.graphml to OUTPUT_DIR.
    The CSV keeps only the six canonical output columns.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Canonical columns only (no helper name columns)
    csv_cols = [
        "actor_1", "actor_2",
        "confidence_score", "confidence_level", "matched_features",
    ]
    matches_df[csv_cols].to_csv(MATCHES_OUT, index=False)
    print(f"[EXPORT] entity_matches.csv   → {os.path.abspath(MATCHES_OUT)}")
    print(f"         Rows saved: {len(matches_df)}")

    nx.write_graphml(G, GRAPHML_OUT)
    print(f"[EXPORT] actor_network.graphml → {os.path.abspath(GRAPHML_OUT)}")
    print(f"         Nodes: {G.number_of_nodes()}   Edges: {G.number_of_edges()}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    sep = "=" * 64
    print(sep)
    print("  Wildlife Intelligence Platform — Entity Resolution Engine")
    print(sep)

    # 1. Load data
    actors, incidents, shipments, routes, messages = load_data()

    # 2. Build lookup structures
    print("\n[BUILD]  Actor → route map …")
    actor_routes = build_actor_route_map(incidents, shipments)
    route_labels = build_route_labels(routes)
    print(f"         {len(actor_routes)} actors have at least one linked route")

    # 3. Run pairwise comparisons
    matches_df  = run_entity_resolution(actors, actor_routes, route_labels)
    n_actors    = len(actors)
    total_pairs = n_actors * (n_actors - 1) // 2

    # 4. Build graph
    print("\n[GRAPH]  Building NetworkX graph …")
    G = build_graph(actors, matches_df)

    # 5. Print analytics
    print_analytics(actors, matches_df, G, total_pairs)

    # 6. Export
    export_results(matches_df, G)

    print("\n✓ Entity resolution complete.\n")


if __name__ == "__main__":
    main()
