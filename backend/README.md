# Supply Chain Ghost — FastAPI Backend

Intelligence REST API gateway for the **Supply Chain Ghost** wildlife trafficking analysis platform.

---

## Quick Start

```bash
# From the backend/ directory
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API:     http://localhost:8000  
Swagger: http://localhost:8000/docs  
ReDoc:   http://localhost:8000/redoc

---

## Project Layout

```
backend/
├── main.py                  # FastAPI app, CORS, lifespan, DB seed
├── database.py              # SQLAlchemy engine + session
├── models.py                # ORM table definitions (SQLite / PostgreSQL-ready)
├── schemas.py               # Pydantic v2 request/response models
├── data_loader.py           # Loads all CSVs/JSON; builds in-memory indexes
├── requirements.txt
├── test_api.py              # Integration tests (pytest + TestClient)
│
├── services/
│   ├── dashboard_service.py
│   ├── intelligence_service.py
│   ├── network_service.py
│   ├── map_service.py
│   ├── message_service.py
│   └── investigation_service.py
│
└── routers/
    ├── dashboard.py
    ├── intelligence.py      # alerts, map, incidents, actors, routes, intel, search
    ├── network.py           # hidden-links, network graph, timeline
    ├── messages.py
    └── investigations.py
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/dashboard/summary` | Dashboard KPIs |
| GET | `/api/alerts` | Alerts (filter: priority, pattern_type) |
| GET | `/api/map` | Geographic intelligence layer |
| GET | `/api/incidents` | List incidents (filter: search, species, route_id, dates) |
| GET | `/api/incidents/{id}` | Incident detail + timeline + evidence |
| GET | `/api/actors` | List actors (filter: name, alias, nationality, role) |
| GET | `/api/actors/{id}` | Actor profile + linked intelligence |
| GET | `/api/routes` | List routes |
| GET | `/api/routes/{id}` | Route detail + hidden links + alerts |
| GET | `/api/intelligence/{type}/{id}` | Pre-computed intelligence scores |
| GET | `/api/intelligence/{type}/{id}/explanation` | "Why suspicious?" panel |
| GET | `/api/hidden-links/{type}/{id}` | Ranked hidden-link discovery |
| GET | `/api/network/{type}/{id}` | Local network graph (nodes + edges) |
| GET | `/api/timeline/{type}/{id}` | Chronological timeline |
| GET | `/api/investigation/{type}/{id}` | Investigation brief (offline, deterministic) |
| POST | `/api/messages/analyze` | Analyze a message for linguistic signals |
| POST | `/api/messages/link` | Link a message to an investigation target |
| GET | `/api/messages/{id}/map-context` | Map context for a message |
| GET | `/api/search?q=` | Cross-entity search |

Target types: `INCIDENT` · `ACTOR` · `ROUTE` · `LOCATION`

---

## Running Tests

```bash
cd backend
pytest test_api.py -v
```

No external database server required. Tests use FastAPI `TestClient` with the in-memory data.

---

## Database

SQLite (`supply_chain_ghost.db`) is the default.  
To switch to PostgreSQL/Supabase:

```bash
export DATABASE_URL="postgresql+psycopg2://user:pass@host/dbname"
uvicorn main:app --reload --port 8000
```

No API code changes needed — SQLAlchemy handles the rest.

---

## Design Notes

- **No scores are recalculated inside FastAPI.** Intelligence outputs from the existing engines are loaded once at startup and served from memory.
- All responses use intelligence-appropriate language: "potentially associated", "intelligence signal", "possible network relationship" — never "confirmed criminal".
- Evidence items include `source_file`, `source_id`, and `data_type` for full provenance tracing.
- CORS allows `localhost:3000` (CRA) and `localhost:5173` (Vite) for local development.
