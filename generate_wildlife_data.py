"""
Wildlife Trafficking Simulation Database Generator
Generates realistic simulated relational data for AI model training.
Covers India-Africa trafficking corridors (2024-2026).
"""

import os
import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from faker import Faker

# ── Seeds ─────────────────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)
fake = Faker()
fake.seed_instance(42)

OUTPUT_DIR = "simulated_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── World Model ────────────────────────────────────────────────────────────────
INDIAN_HUBS = ["Chennai Port", "Tuticorin Port", "Kochi Port", "Mumbai Port", "Visakhapatnam"]
AFRICAN_HUBS = ["Mombasa", "Dar es Salaam", "Maputo", "Durban"]

SPECIES_WEIGHTS = {"Pangolin": 0.45, "Elephant": 0.25, "Rhino": 0.15, "Leopard": 0.15}
SPECIES_LIST = list(SPECIES_WEIGHTS.keys())
SPECIES_PROBS = list(SPECIES_WEIGHTS.values())

COMMODITY_MAP = {
    "Pangolin": "scales",
    "Elephant": "ivory tusk",
    "Rhino":    "horn",
    "Leopard":  "skin",
}

ROLES = ["Collector", "Transporter", "Broker", "Exporter", "Buyer"]
TRANSPORT_TYPES = ["Sea Freight", "Air Cargo", "Road", "Rail", "Mixed"]
SEIZURE_STATUSES = ["Seized", "Not Seized", "Under Investigation"]
SEIZURE_PROBS = [0.30, 0.55, 0.15]

PROTECTED_AREAS = [
    "Nilgiri Biosphere",
    "Anamalai Tiger Reserve",
    "Sundarbans",
    "Tsavo Ecosystem",
    "Serengeti Buffer",
]

PROTECTED_AREA_COORDS = {
    "Nilgiri Biosphere":       (10.8, 11.8, 76.0, 77.2),
    "Anamalai Tiger Reserve":  (10.2, 10.9, 76.8, 77.4),
    "Sundarbans":              (21.5, 22.5, 88.5, 89.5),
    "Tsavo Ecosystem":         (-3.8, -1.5, 37.5, 39.5),
    "Serengeti Buffer":        (-3.5, -1.0, 34.0, 35.5),
}

SLANG_PHRASES = [
    "brown parcel", "blue bird", "ivory tea", "long horn",
    "after rain", "river crossing", "jungle fruit", "grey stone",
    "forest gift", "night delivery",
]

NORMAL_PHRASES = [
    "When does the shipment arrive?",
    "Confirm the meeting time.",
    "Payment received, proceed.",
    "Documents are ready.",
    "Wait for my signal.",
    "The weather looks good today.",
    "Call me when you land.",
    "Everything is on schedule.",
    "Do not contact me on this number again.",
    "Send the updated manifest.",
    "All clear from my end.",
    "The contact has been verified.",
    "Delivery confirmed.",
    "We need to move faster.",
    "Port clearance obtained.",
    "Customs officer confirmed.",
    "Truck is loaded.",
    "Coordinates sent separately.",
    "Be at the location by midnight.",
    "Use the secondary channel.",
]


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))


def uid() -> str:
    return str(uuid.uuid4())[:8].upper()


def make_alias(name: str) -> str:
    """Create a slightly varied alias for entity-resolution challenges."""
    parts = name.split()
    if len(parts) < 2:
        return name + " Jr."
    strategies = [
        lambda p: p[0][0] + ". " + " ".join(p[1:]),
        lambda p: " ".join(p[:-1]) + " " + p[-1][:3] + ".",
        lambda p: p[0] + " " + p[-1][0] + ".",
        lambda p: " ".join(reversed(p)),
    ]
    strategy = random.choice(strategies)
    try:
        return strategy(parts)
    except Exception:
        return parts[0] + " " + parts[-1][:2] + "."


def get_source_coords(source: str):
    """Return approximate lat/lon for a given port."""
    coord_map = {
        "Chennai Port":   (13.0827,  80.2707),
        "Tuticorin Port": (8.7642,   78.1348),
        "Kochi Port":     (9.9312,   76.2673),
        "Mumbai Port":    (18.9388,  72.8354),
        "Visakhapatnam":  (17.6868,  83.2185),
        "Mombasa":        (-4.0435,  39.6682),
        "Dar es Salaam":  (-6.7924,  39.2083),
        "Maputo":         (-25.9692, 32.5732),
        "Durban":         (-29.8587, 31.0218),
    }
    base = coord_map.get(source, (0.0, 0.0))
    jitter_lat = np.random.uniform(-0.5, 0.5)
    jitter_lon = np.random.uniform(-0.5, 0.5)
    return base[0] + jitter_lat, base[1] + jitter_lon


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 1 – actors.csv  (120 rows)
# ══════════════════════════════════════════════════════════════════════════════

def generate_actors(n: int = 120) -> pd.DataFrame:
    # Focus: India and East/Southern Africa only — no SE/East Asian nationals.
    # Indian actors operate from source ports; African actors operate at
    # destination hubs.  Nationality pool weighted to reflect real trafficking
    # demographics on this corridor.
    nat_pool = (
        ["Indian"] * 50          # largest bloc — source country operators
        + ["Kenyan"] * 14        # Mombasa hub
        + ["Tanzanian"] * 14     # Dar es Salaam hub
        + ["Mozambican"] * 12    # Maputo hub
        + ["South African"] * 12 # Durban hub
        + ["Ugandan"] * 10       # inland collector routes
        + ["Somali"] * 8         # transit corridor actors
        + ["Rwandan"] * 5        # great-lakes inland brokers
        + ["Ethiopian"] * 5      # Horn-of-Africa transit
    )
    regions_indian  = ["Tamil Nadu", "Kerala", "Andhra Pradesh", "Maharashtra", "West Bengal"]
    regions_african = ["Kenya", "Tanzania", "Mozambique", "South Africa", "Uganda",
                       "Somalia", "Rwanda", "Ethiopia"]

    records = []
    for i in range(n):
        nat = nat_pool[i % len(nat_pool)]
        if nat == "Indian":
            region = random.choice(regions_indian)
        else:
            region = random.choice(regions_african)

        name = fake.name()
        records.append({
            "actor_id":       f"ACT-{uid()}",
            "full_name":      name,
            "alias":          make_alias(name),
            "nationality":    nat,
            "role":           random.choice(ROLES),
            "primary_region": region,
            "threat_score":   random.randint(10, 100),
        })

    # Elevate 15 network leaders to high threat scores
    for idx in random.sample(range(n), 15):
        records[idx]["threat_score"] = random.randint(70, 100)

    # ── Deliberate duplicate actors (10 shadow identities) ───────────────────
    # Each entry is a near-clone of a real actor with a new ID, subtly mutated
    # name/alias, and identical nationality + region → guarantees high ER score.
    # The "_source_idx" key is used later by generate_incidents / generate_shipments
    # to route some incidents through these shadow IDs so shared-route points fire.
    #
    # Mutation strategies used:
    #   • Swap first/last name order         (Amber Kidd  → Kidd Amber)
    #   • Drop middle initial or title        (Jeffrey Chandler → Jeff Chandler)
    #   • Slight misspelling / transliteration (Zachary → Zackary)
    #   • Alias kept near-identical to original alias
    #
    DUPLICATE_TEMPLATES = [
        # (new_id,        full_name variant,       alias variant,          nat,            role,        region,          threat)
        # Amber Kidd duplicates — Mozambican, South Africa
        ("ACT-DUP-0001", "Ambar Kidd",             "A. Kidd",              "Mozambican",   "Exporter",  "South Africa",  97),
        ("ACT-DUP-0002", "Kidd Amber",             "Kidd A.",              "Mozambican",   "Exporter",  "South Africa",  94),
        # Zachary Hicks duplicates — Indian, Tamil Nadu
        ("ACT-DUP-0003", "Zackary Hicks",          "Zackary H.",           "Indian",       "Transporter","Tamil Nadu",   88),
        ("ACT-DUP-0004", "Zachary Hix",            "Z. Hix",               "Indian",       "Transporter","Tamil Nadu",   91),
        # Carol Tucker duplicates — Mozambican, Mozambique
        ("ACT-DUP-0005", "Carol Tukker",           "Carol Tuk.",           "Mozambican",   "Collector", "Mozambique",   82),
        ("ACT-DUP-0006", "Carrol Tucker",          "C. Tucker",            "Mozambican",   "Collector", "Mozambique",   85),
        # Fred Smith duplicates — Kenyan, Kenya
        ("ACT-DUP-0007", "Fred Smyth",             "F. Smyth",             "Kenyan",       "Transporter","Kenya",        91),
        ("ACT-DUP-0008", "Frederick Smith",        "Fred S.",              "Kenyan",       "Transporter","Kenya",        88),
        # Victoria Garcia duplicates — Mozambican, Uganda
        ("ACT-DUP-0009", "Victoria Gracia",        "V. Gracia",            "Mozambican",   "Collector", "Uganda",       80),
        ("ACT-DUP-0010", "Victoriya Garcia",       "Garcia V.",            "Mozambican",   "Collector", "Uganda",       83),
    ]

    for (nid, fname, alias, nat, role, region, threat) in DUPLICATE_TEMPLATES:
        records.append({
            "actor_id":       nid,
            "full_name":      fname,
            "alias":          alias,
            "nationality":    nat,
            "role":           role,
            "primary_region": region,
            "threat_score":   threat,
        })

    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 2 – routes.csv  (60 rows)
# ══════════════════════════════════════════════════════════════════════════════

def generate_routes() -> pd.DataFrame:
    core_corridors = [
        ("Chennai Port",   "Colombo",       "Mombasa",       "Chennai-Mombasa"),
        ("Kochi Port",     "Aden",           "Dar es Salaam", "Kochi-DarEsSalaam"),
        ("Tuticorin Port", "Colombo",        "Maputo",        "Tuticorin-Maputo"),
        ("Mumbai Port",    "Dubai",          "Durban",        "Mumbai-Durban"),
        ("Visakhapatnam",  "Singapore",      "Mombasa",       "Vizag-Mombasa"),
        ("Chennai Port",   "Kuala Lumpur",   "Dar es Salaam", "Chennai-DarEsSalaam"),
        ("Kochi Port",     "Dubai",          "Maputo",        "Kochi-Maputo"),
        ("Tuticorin Port", "Singapore",      "Durban",        "Tuticorin-Durban"),
        ("Mumbai Port",    "Aden",           "Mombasa",       "Mumbai-Mombasa"),
        ("Visakhapatnam",  "Bangkok",        "Dar es Salaam", "Vizag-DarEsSalaam"),
    ]

    extra_transits = [
        "Colombo", "Dubai", "Singapore", "Bangkok", "Kuala Lumpur",
        "Aden", "Nairobi (Air)", "Addis Ababa", "Muscat", "Port Louis",
    ]

    records = []
    for src, transit, dst, corridor in core_corridors:
        records.append({
            "route_id":        f"RTE-{uid()}",
            "source":          src,
            "transit":         transit,
            "destination":     dst,
            "corridor":        corridor,
            "historical_risk": random.randint(65, 95),
        })

    while len(records) < 60:
        src     = random.choice(INDIAN_HUBS)
        dst     = random.choice(AFRICAN_HUBS)
        transit = random.choice(extra_transits)
        corridor = f"{src.split()[0]}-{dst.replace(' ', '')}-{transit.split()[0]}"
        records.append({
            "route_id":        f"RTE-{uid()}",
            "source":          src,
            "transit":         transit,
            "destination":     dst,
            "corridor":        corridor,
            "historical_risk": random.randint(20, 85),
        })

    df = pd.DataFrame(records[:60])

    # Boost risk on the first 5 core corridors (most trafficked)
    core_names = [c[3] for c in core_corridors[:5]]
    mask = df["corridor"].isin(core_names)
    df.loc[mask, "historical_risk"] = df.loc[mask, "historical_risk"].clip(lower=78)

    return df


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 3 – incidents.csv  (300 rows)
# ══════════════════════════════════════════════════════════════════════════════

def generate_incidents(actors_df: pd.DataFrame, routes_df: pd.DataFrame) -> pd.DataFrame:
    start_dt = datetime(2024, 1, 1)
    end_dt   = datetime(2026, 12, 31)

    route_ids  = routes_df["route_id"].tolist()
    actor_ids  = actors_df["actor_id"].tolist()
    route_lookup = routes_df.set_index("route_id")[["source", "destination"]].to_dict("index")

    # ── 5 hidden networks ────────────────────────────────────────────────────
    high_threat    = actors_df.nlargest(25, "threat_score")["actor_id"].tolist()
    network_actors = [high_threat[i * 5:(i + 1) * 5] for i in range(5)]

    core_route_ids   = routes_df.head(10)["route_id"].tolist()
    network_routes   = [core_route_ids[i * 2] for i in range(5)]
    network_dst      = [route_lookup[r]["destination"] for r in network_routes]
    network_species  = ["Pangolin", "Elephant", "Rhino", "Leopard", "Pangolin"]

    hidden_records = []
    incidents_per_net = [18, 16, 18, 20, 18]  # 90 total ≈ 30%

    for net_idx in range(5):
        for _ in range(incidents_per_net[net_idx]):
            rid     = network_routes[net_idx]
            src     = route_lookup[rid]["source"]
            dst     = network_dst[net_idx]
            species = network_species[net_idx]
            lat, lon = get_source_coords(src)

            hidden_records.append({
                "incident_id":     f"INC-{uid()}",
                "incident_date":   random_date(start_dt, end_dt).strftime("%Y-%m-%d"),
                "species":         species,
                "commodity":       COMMODITY_MAP[species],
                "quantity":        max(1, int(np.random.lognormal(2.5, 0.8))),
                "source_location": src,
                "destination":     dst,
                "route_id":        rid,
                "lead_actor":      random.choice(network_actors[net_idx]),
                "seizure_status":  np.random.choice(SEIZURE_STATUSES, p=SEIZURE_PROBS),
                "latitude":        round(lat, 5),
                "longitude":       round(lon, 5),
                "network_id":      f"NET-{net_idx + 1:02d}",
            })

    # ── Isolated incidents (~210 rows) ───────────────────────────────────────
    isolated_records = []
    for _ in range(300 - len(hidden_records)):
        species = np.random.choice(SPECIES_LIST, p=SPECIES_PROBS)
        rid     = random.choice(route_ids)
        src     = route_lookup[rid]["source"]
        dst     = route_lookup[rid]["destination"]
        lat, lon = get_source_coords(src)

        isolated_records.append({
            "incident_id":     f"INC-{uid()}",
            "incident_date":   random_date(start_dt, end_dt).strftime("%Y-%m-%d"),
            "species":         species,
            "commodity":       COMMODITY_MAP[species],
            "quantity":        max(1, int(np.random.lognormal(2.0, 1.0))),
            "source_location": src,
            "destination":     dst,
            "route_id":        rid,
            "lead_actor":      random.choice(actor_ids),
            "seizure_status":  np.random.choice(SEIZURE_STATUSES, p=SEIZURE_PROBS),
            "latitude":        round(lat, 5),
            "longitude":       round(lon, 5),
            "network_id":      None,
        })

    # ── Shadow-actor incidents ────────────────────────────────────────────────
    # Each duplicate actor is sent on the SAME routes as its original so that
    # the entity-resolution engine's shared-route signal (15 pts) fires for
    # both name similarity AND route overlap → pushes scores above 80.
    #
    # Pairs: (duplicate_id, original_id, route_id, species)
    # Route IDs are the first two core routes (always generated deterministically).
    shadow_pairs = [
        # Amber Kidd duplicates  (Mozambican, South Africa)
        ("ACT-DUP-0001", "Pangolin"),
        ("ACT-DUP-0002", "Pangolin"),
        # Zachary Hicks duplicates (Indian, Tamil Nadu)
        ("ACT-DUP-0003", "Rhino"),
        ("ACT-DUP-0004", "Rhino"),
        # Carol Tucker duplicates (Mozambican, Mozambique)
        ("ACT-DUP-0005", "Pangolin"),
        ("ACT-DUP-0006", "Pangolin"),
        # Fred Smith duplicates (Kenyan, Kenya)
        ("ACT-DUP-0007", "Elephant"),
        ("ACT-DUP-0008", "Elephant"),
        # Victoria Garcia duplicates (Mozambican, Uganda)
        ("ACT-DUP-0009", "Leopard"),
        ("ACT-DUP-0010", "Leopard"),
    ]

    shadow_records = []
    # Each shadow actor appears in 4 incidents on the first 4 core routes
    for dup_id, species in shadow_pairs:
        for rid in core_route_ids[:4]:
            src  = route_lookup[rid]["source"]
            dst  = route_lookup[rid]["destination"]
            lat, lon = get_source_coords(src)
            shadow_records.append({
                "incident_id":     f"INC-{uid()}",
                "incident_date":   random_date(start_dt, end_dt).strftime("%Y-%m-%d"),
                "species":         species,
                "commodity":       COMMODITY_MAP[species],
                "quantity":        max(1, int(np.random.lognormal(2.0, 0.7))),
                "source_location": src,
                "destination":     dst,
                "route_id":        rid,
                "lead_actor":      dup_id,
                "seizure_status":  np.random.choice(SEIZURE_STATUSES, p=SEIZURE_PROBS),
                "latitude":        round(lat, 5),
                "longitude":       round(lon, 5),
                "network_id":      None,
            })

    all_records = hidden_records + isolated_records + shadow_records
    random.shuffle(all_records)
    df = pd.DataFrame(all_records).sort_values("incident_date").reset_index(drop=True)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 4 – shipments.csv  (500 rows)
# ══════════════════════════════════════════════════════════════════════════════

def generate_shipments(incidents_df: pd.DataFrame, actors_df: pd.DataFrame) -> pd.DataFrame:
    actor_ids    = actors_df["actor_id"].tolist()
    incident_ids = incidents_df["incident_id"].tolist()

    # Vehicle pool: 80 IDs; 5 groups of 3 are shared across network incidents
    vehicle_pool    = [f"VEH-{uid()}" for _ in range(80)]
    network_vehicles = [[vehicle_pool[i * 3 + j] for j in range(3)] for i in range(5)]

    # Map incident_id → network index
    net_incident_map: dict[str, int] = {}
    for _, row in incidents_df.iterrows():
        if pd.notna(row.get("network_id")):
            net_incident_map[row["incident_id"]] = int(str(row["network_id"]).split("-")[1]) - 1

    # Duplicate-actor IDs paired with their originals' actor IDs so shipments
    # can deliberately share vehicle IDs to strengthen hidden links.
    # (dup_id, original_id) — vehicles shared between these pairs
    DUP_ORIGINAL_PAIRS = [
        ("ACT-DUP-0001", "ACT-DUP-0002"),   # both Amber Kidd variants
        ("ACT-DUP-0003", "ACT-DUP-0004"),   # both Jeffrey Chandler variants
        ("ACT-DUP-0005", "ACT-DUP-0006"),   # both Zachary Hicks variants
        ("ACT-DUP-0007", "ACT-DUP-0008"),   # both Carol Tucker variants
        ("ACT-DUP-0009", "ACT-DUP-0010"),   # both Brian Rodriguez variants
    ]
    # Shared vehicles for each duplicate pair (3 per pair)
    dup_shared_vehicles = {
        pair: [f"VEH-DUP-{i:02d}{j}" for j in range(3)]
        for i, pair in enumerate(DUP_ORIGINAL_PAIRS)
    }
    # Build fast lookup: dup_id → shared vehicle list
    dup_vehicle_map: dict[str, list[str]] = {}
    for pair, vehs in dup_shared_vehicles.items():
        dup_vehicle_map[pair[0]] = vehs
        dup_vehicle_map[pair[1]] = vehs

    records = []
    for i in range(500):
        inc_id  = incident_ids[i % len(incident_ids)]
        inc_row = incidents_df[incidents_df["incident_id"] == inc_id].iloc[0]
        dep_dt  = datetime.strptime(inc_row["incident_date"], "%Y-%m-%d")
        arr_dt  = dep_dt + timedelta(days=random.randint(7, 45))

        if inc_id in net_incident_map:
            vehicle_id = random.choice(network_vehicles[net_incident_map[inc_id]])
        else:
            vehicle_id = random.choice(vehicle_pool)

        records.append({
            "shipment_id":     f"SHP-{uid()}",
            "incident_id":     inc_id,
            "actor_id":        random.choice(actor_ids),
            "vehicle_id":      vehicle_id,
            "transport_type":  random.choice(TRANSPORT_TYPES),
            "departure_date":  dep_dt.strftime("%Y-%m-%d"),
            "arrival_date":    arr_dt.strftime("%Y-%m-%d"),
            "shipment_weight": round(max(0.5, np.random.lognormal(3.5, 0.9)), 2),
            "status":          random.choice(["In Transit", "Delivered", "Intercepted", "Delayed"]),
        })

    # Extra shipments for shadow/duplicate actors using shared vehicles
    # so the route-overlap signal in entity_resolution also fires via shipments.
    shadow_inc_ids = incidents_df[
        incidents_df["lead_actor"].str.startswith("ACT-DUP-", na=False)
    ]["incident_id"].tolist()

    for inc_id in shadow_inc_ids:
        inc_row    = incidents_df[incidents_df["incident_id"] == inc_id].iloc[0]
        dup_actor  = inc_row["lead_actor"]
        dep_dt     = datetime.strptime(inc_row["incident_date"], "%Y-%m-%d")
        arr_dt     = dep_dt + timedelta(days=random.randint(7, 45))
        vehicle_id = random.choice(dup_vehicle_map.get(dup_actor, vehicle_pool))

        records.append({
            "shipment_id":     f"SHP-{uid()}",
            "incident_id":     inc_id,
            "actor_id":        dup_actor,
            "vehicle_id":      vehicle_id,
            "transport_type":  random.choice(TRANSPORT_TYPES),
            "departure_date":  dep_dt.strftime("%Y-%m-%d"),
            "arrival_date":    arr_dt.strftime("%Y-%m-%d"),
            "shipment_weight": round(max(0.5, np.random.lognormal(3.5, 0.9)), 2),
            "status":          random.choice(["In Transit", "Delivered", "Intercepted", "Delayed"]),
        })

    return pd.DataFrame(records)


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 5 – animal_events.csv  (150 rows)
# ══════════════════════════════════════════════════════════════════════════════

def generate_animal_events(incidents_df: pd.DataFrame) -> pd.DataFrame:
    start_dt = datetime(2024, 1, 1)
    end_dt   = datetime(2026, 12, 31)

    records = []
    for i in range(150):
        area  = random.choice(PROTECTED_AREAS)
        bbox  = PROTECTED_AREA_COORDS[area]
        lat   = round(random.uniform(bbox[0], bbox[1]), 5)
        lon   = round(random.uniform(bbox[2], bbox[3]), 5)

        is_anomaly      = (i < 30)  # first 30 rows → 20% abnormal
        normal_movement = round(random.uniform(2.0, 8.0), 2)

        if is_anomaly:
            anomaly_type = random.choice(["drop", "spike"])
            if anomaly_type == "drop":
                observed_movement = round(random.uniform(0.0, 1.0), 2)
            else:
                observed_movement = round(random.uniform(15.0, 30.0), 2)
        else:
            observed_movement = round(
                max(0.1, normal_movement + random.uniform(-1.5, 1.5)), 2
            )

        deviation    = abs(observed_movement - normal_movement) / max(normal_movement, 0.01)
        anomaly_score = round(min(1.0, deviation / 5.0) if is_anomaly else min(0.3, deviation / 5.0), 3)

        records.append({
            "event_id":          f"EVT-{uid()}",
            "protected_area":    area,
            "event_date":        random_date(start_dt, end_dt).strftime("%Y-%m-%d"),
            "normal_movement":   normal_movement,
            "observed_movement": observed_movement,
            "anomaly_score":     anomaly_score,
            "latitude":          lat,
            "longitude":         lon,
        })

    random.shuffle(records)
    return pd.DataFrame(records).sort_values("event_date").reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABLE 6 – messages.csv  (400 rows)
# ══════════════════════════════════════════════════════════════════════════════

def generate_messages(
    actors_df: pd.DataFrame,
    routes_df: pd.DataFrame,
    incidents_df: pd.DataFrame,
) -> pd.DataFrame:
    start_dt = datetime(2024, 1, 1)
    end_dt   = datetime(2026, 12, 31)

    actor_ids = actors_df["actor_id"].tolist()
    route_ids = routes_df["route_id"].tolist()

    network_groups  = [f"NET_CHANNEL_{i+1}" for i in range(5)]
    general_groups  = [f"LOGISTICS_GRP_{chr(65+i)}" for i in range(8)]
    all_groups      = network_groups + general_groups

    high_threat     = actors_df.nlargest(25, "threat_score")["actor_id"].tolist()
    net_actor_map   = {
        f"NET_CHANNEL_{i+1}": high_threat[i*5:(i+1)*5] for i in range(5)
    }

    slang_templates = [
        "The {s} is ready for pickup at the usual spot.",
        "Confirm {s} delivery before sunrise.",
        "How many {s} units are we moving this week?",
        "The {s} passed through without issues.",
        "Need three more {s} for the next run.",
        "Don't mention the {s} on open channels.",
        "The {s} deal closes after rain.",
        "Waiting for the {s} handover, be patient.",
        "Client confirmed. {s} route is clear.",
        "Extra {s} available, contact me privately.",
    ]

    records    = []
    n_slangy   = int(400 * 0.25)  # exactly 100 coded messages

    for i in range(400):
        is_slang = (i < n_slangy)
        group    = random.choice(network_groups if is_slang else all_groups)

        if group in net_actor_map:
            pool     = net_actor_map[group]
            sender   = random.choice(pool)
            others   = [a for a in pool if a != sender]
            receiver = random.choice(others if others else pool)
        else:
            sender   = random.choice(actor_ids)
            others   = [a for a in actor_ids if a != sender]
            receiver = random.choice(others if others else actor_ids)

        ts           = random_date(start_dt, end_dt)
        linked_route = random.choice(route_ids) if is_slang else None

        if is_slang:
            phrase = random.choice(SLANG_PHRASES)
            text   = random.choice(slang_templates).format(s=phrase)
        else:
            text = random.choice(NORMAL_PHRASES) + " " + fake.sentence(nb_words=6)

        records.append({
            "message_id":     f"MSG-{uid()}",
            "sender_actor":   sender,
            "receiver_actor": receiver,
            "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
            "chat_group":     group,
            "message_text":   text,
            "contains_slang": is_slang,
            "linked_route":   linked_route,
        })

    random.shuffle(records)
    return pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    sep = "=" * 62
    print(sep)
    print("  Wildlife Trafficking Simulation — Data Generator")
    print(sep)

    print("\n[1/6] Generating actors ...")
    actors_df = generate_actors(120)
    actors_df.to_csv(os.path.join(OUTPUT_DIR, "actors.csv"), index=False)

    print("[2/6] Generating routes ...")
    routes_df = generate_routes()
    routes_df.to_csv(os.path.join(OUTPUT_DIR, "routes.csv"), index=False)

    print("[3/6] Generating incidents ...")
    incidents_df = generate_incidents(actors_df, routes_df)
    incidents_df.to_csv(os.path.join(OUTPUT_DIR, "incidents.csv"), index=False)

    print("[4/6] Generating shipments ...")
    shipments_df = generate_shipments(incidents_df, actors_df)
    shipments_df.to_csv(os.path.join(OUTPUT_DIR, "shipments.csv"), index=False)

    print("[5/6] Generating animal events ...")
    animal_df = generate_animal_events(incidents_df)
    animal_df.to_csv(os.path.join(OUTPUT_DIR, "animal_events.csv"), index=False)

    print("[6/6] Generating messages ...")
    messages_df = generate_messages(actors_df, routes_df, incidents_df)
    messages_df.to_csv(os.path.join(OUTPUT_DIR, "messages.csv"), index=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  GENERATION SUMMARY")
    print(sep)

    tables = [
        ("actors.csv",        actors_df),
        ("routes.csv",        routes_df),
        ("incidents.csv",     incidents_df),
        ("shipments.csv",     shipments_df),
        ("animal_events.csv", animal_df),
        ("messages.csv",      messages_df),
    ]
    print(f"\n  {'Table':<25} {'Rows':>6}")
    print("  " + "-" * 32)
    for name, df in tables:
        print(f"  {name:<25} {len(df):>6}")

    # Species distribution
    print("\n  Species Distribution (incidents):")
    spec_dist = incidents_df["species"].value_counts(normalize=True).mul(100).round(1)
    for sp, pct in spec_dist.items():
        bar = "█" * int(pct / 2)
        print(f"    {sp:<15} {pct:>5.1f}%  {bar}")

    # Route distribution (top 10)
    print("\n  Top 10 Routes by Incident Count:")
    route_counts = incidents_df["route_id"].value_counts().head(10)
    route_info   = routes_df.set_index("route_id")
    for rid, cnt in route_counts.items():
        corridor = route_info.loc[rid, "corridor"] if rid in route_info.index else rid
        print(f"    {corridor:<42} {cnt:>4} incidents")

    # Hidden networks
    net_col = incidents_df[incidents_df["network_id"].notna()]
    net_summary = net_col["network_id"].value_counts().sort_index()
    print(f"\n  Number of Hidden Networks Created: {len(net_summary)}")
    for net_id, cnt in net_summary.items():
        print(f"    {net_id}  →  {cnt} incidents")

    # Top 10 recurring actors
    print("\n  Top 10 Recurring Actors (by incident count):")
    actor_counts = incidents_df["lead_actor"].value_counts().head(10)
    actor_info   = actors_df.set_index("actor_id")
    for aid, cnt in actor_counts.items():
        if aid in actor_info.index:
            row = actor_info.loc[aid]
            print(
                f"    {row['full_name']:<30}  role={row['role']:<12} "
                f"threat={row['threat_score']:>3}  incidents={cnt}"
            )
        else:
            print(f"    {aid:<30}  incidents={cnt}")

    print(f"\n  ✓ All CSVs saved to: {os.path.abspath(OUTPUT_DIR)}")
    print(sep + "\n")


if __name__ == "__main__":
    main()
