"""
test_api.py
-----------
Integration tests for Supply Chain Ghost FastAPI backend.
Uses FastAPI TestClient — no external database server required.

Run:
  cd backend
  pip install -r requirements.txt
  pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ── Health ────────────────────────────────────────────────────────────────────

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["service"] == "Supply Chain Ghost"
    assert isinstance(data["data_loaded"], bool)


# ── Dashboard ─────────────────────────────────────────────────────────────────

def test_dashboard_summary():
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    data = r.json()
    for field in (
        "total_incidents", "total_actors", "total_routes", "total_shipments",
        "total_alerts", "critical_alerts", "high_alerts", "watch_alerts",
        "active_investigations", "high_risk_routes", "emerging_hubs",
    ):
        assert field in data, f"Missing field: {field}"
    assert data["total_incidents"] >= 0
    assert data["total_actors"] >= 0


# ── Alerts ────────────────────────────────────────────────────────────────────

def test_alerts_list():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "alerts" in data
    assert isinstance(data["alerts"], list)


def test_alerts_filter_priority():
    r = client.get("/api/alerts?priority=CRITICAL")
    assert r.status_code == 200
    data = r.json()
    for alert in data["alerts"]:
        assert alert["priority"] == "CRITICAL"


def test_alerts_pagination():
    r = client.get("/api/alerts?limit=5&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert len(data["alerts"]) <= 5


# ── Map ───────────────────────────────────────────────────────────────────────

def test_map():
    r = client.get("/api/map")
    assert r.status_code == 200
    data = r.json()
    assert "points" in data
    assert "routes" in data
    assert isinstance(data["points"], list)
    assert isinstance(data["routes"], list)


# ── Incidents ─────────────────────────────────────────────────────────────────

def test_list_incidents():
    r = client.get("/api/incidents")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "incidents" in data
    assert data["total"] >= 0


def test_incident_search():
    r = client.get("/api/incidents?search=elephant")
    assert r.status_code == 200
    data = r.json()
    assert "incidents" in data


def test_incident_not_found():
    r = client.get("/api/incidents/INC-DOESNOTEXIST")
    assert r.status_code == 404
    data = r.json()
    # FastAPI wraps our dict in "detail"
    detail = data.get("detail", data)
    assert detail.get("error") is True
    assert detail.get("code") == "INCIDENT_NOT_FOUND"


def test_incident_detail_valid():
    """Fetch list first and use first real ID."""
    r = client.get("/api/incidents?limit=1")
    assert r.status_code == 200
    incs = r.json()["incidents"]
    if not incs:
        pytest.skip("No incidents in dataset")
    inc_id = incs[0]["incident_id"]
    r2 = client.get(f"/api/incidents/{inc_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert "incident" in data
    assert "timeline" in data


# ── Actors ────────────────────────────────────────────────────────────────────

def test_list_actors():
    r = client.get("/api/actors")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "actors" in data


def test_actor_detail_valid():
    r = client.get("/api/actors?limit=1")
    assert r.status_code == 200
    actors = r.json()["actors"]
    if not actors:
        pytest.skip("No actors in dataset")
    actor_id = actors[0]["actor_id"]
    r2 = client.get(f"/api/actors/{actor_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert "actor" in data
    assert "network_statistics" in data


# ── Routes ────────────────────────────────────────────────────────────────────

def test_list_routes():
    r = client.get("/api/routes")
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "routes" in data


def test_route_detail_valid():
    r = client.get("/api/routes?limit=1")
    assert r.status_code == 200
    routes = r.json()["routes"]
    if not routes:
        pytest.skip("No routes in dataset")
    route_id = routes[0]["route_id"]
    r2 = client.get(f"/api/routes/{route_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert "route" in data
    assert "activity_summary" in data


# ── Intelligence ──────────────────────────────────────────────────────────────

def test_intelligence_lookup():
    """Use first intelligence target from pre-computed data."""
    from data_loader import get_data
    d = get_data()
    if d.intelligence_scores.empty:
        pytest.skip("No intelligence scores loaded")
    row = d.intelligence_scores.iloc[0]
    tt  = str(row["target_type"]).upper()
    tid = str(row["target_id"])
    r = client.get(f"/api/intelligence/{tt}/{tid}")
    assert r.status_code == 200
    data = r.json()
    assert data["target_type"] == tt
    assert data["target_id"] == tid
    assert "risk_score" in data


def test_intelligence_invalid_type():
    r = client.get("/api/intelligence/BOGUS/some-id")
    assert r.status_code == 400
    detail = r.json().get("detail", r.json())
    assert detail.get("code") == "INVALID_TARGET_TYPE"


def test_intelligence_not_found():
    r = client.get("/api/intelligence/ACTOR/ACT-DOESNOTEXIST")
    assert r.status_code == 404


def test_explanation():
    from data_loader import get_data
    d = get_data()
    if d.intelligence_scores.empty:
        pytest.skip("No intelligence scores loaded")
    row = d.intelligence_scores.iloc[0]
    tt  = str(row["target_type"]).upper()
    tid = str(row["target_id"])
    r = client.get(f"/api/intelligence/{tt}/{tid}/explanation")
    assert r.status_code == 200
    data = r.json()
    assert "why_suspicious" in data
    assert "evidence" in data
    assert "uncertainties" in data


# ── Hidden links ──────────────────────────────────────────────────────────────

def test_hidden_links():
    """Use first entity in hidden_links."""
    from data_loader import get_data
    d = get_data()
    if d.hidden_links.empty:
        pytest.skip("No hidden links loaded")
    row = d.hidden_links.iloc[0]
    sid = str(row.get("source_id", ""))
    r = client.get(f"/api/hidden-links/ACTOR/{sid}")
    # May be 200 with results or 200 with empty list — not 500
    assert r.status_code in (200, 404)


def test_hidden_links_invalid_type():
    r = client.get("/api/hidden-links/INVALID/some-id")
    assert r.status_code == 400


# ── Network graph ─────────────────────────────────────────────────────────────

def test_network_graph():
    from data_loader import get_data
    d = get_data()
    if d.incidents.empty:
        pytest.skip("No incidents loaded")
    inc_id = d.incidents.iloc[0]["incident_id"]
    r = client.get(f"/api/network/INCIDENT/{inc_id}")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert "nodes" in data
        assert "edges" in data


def test_network_invalid_type():
    r = client.get("/api/network/BOGUS/some-id")
    assert r.status_code == 400


# ── Timeline ──────────────────────────────────────────────────────────────────

def test_timeline():
    from data_loader import get_data
    d = get_data()
    if d.incidents.empty:
        pytest.skip("No incidents loaded")
    inc_id = d.incidents.iloc[0]["incident_id"]
    r = client.get(f"/api/timeline/INCIDENT/{inc_id}")
    assert r.status_code == 200
    data = r.json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_timeline_invalid_type():
    r = client.get("/api/timeline/INVALID/some-id")
    assert r.status_code == 400


# ── Message analysis ──────────────────────────────────────────────────────────

def test_message_analysis_clean():
    r = client.post("/api/messages/analyze", json={
        "sender": "ACT-TEST",
        "receiver": "ACT-TEST2",
        "message": "Hi, the package arrived safely yesterday.",
        "timestamp": "2024-06-01T10:00:00",
    })
    assert r.status_code == 200
    data = r.json()
    assert "linguistic_risk" in data
    assert "detected_terms" in data
    assert isinstance(data["detected_terms"], list)


def test_message_analysis_slang():
    r = client.post("/api/messages/analyze", json={
        "sender": "ACT-TEST",
        "receiver": "ACT-TEST2",
        "message": "Extra blue bird available, contact me privately. River crossing confirmed.",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["linguistic_risk"] > 0
    assert len(data["detected_terms"]) >= 1
    # Must not claim confirmed trafficking
    explanation = data.get("explanation", "").lower()
    assert "confirmed traffick" not in explanation
    assert "confirmed criminal" not in explanation


# ── Investigation brief ───────────────────────────────────────────────────────

def test_investigation_brief():
    from data_loader import get_data
    d = get_data()
    if d.intelligence_scores.empty:
        pytest.skip("No intelligence scores loaded")
    row = d.intelligence_scores.iloc[0]
    tt  = str(row["target_type"]).upper()
    tid = str(row["target_id"])
    r = client.get(f"/api/investigation/{tt}/{tid}")
    assert r.status_code == 200
    data = r.json()
    assert "case_title" in data
    assert "threat_level" in data
    assert "key_evidence" in data
    assert "uncertainties" in data


def test_investigation_invalid_type():
    r = client.get("/api/investigation/INVALID/some-id")
    assert r.status_code == 400


# ── Search ────────────────────────────────────────────────────────────────────

def test_search():
    r = client.get("/api/search?q=elephant")
    assert r.status_code == 200
    data = r.json()
    for key in ("incidents", "actors", "routes", "locations"):
        assert key in data


def test_search_missing_query():
    r = client.get("/api/search")
    assert r.status_code == 422  # FastAPI validation: required param missing
