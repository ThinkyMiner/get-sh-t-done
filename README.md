# Flow2API Backend Engine

Flow2API converts hand-written workflow JSON into browser automation and exposes each workflow as a generated API endpoint.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

## Run The Mock Dashboard

The Playwright runner expects the target dashboard on port 5500.

```bash
python3 -m http.server 5500 --directory mock-dashboard
```

Open:

- `http://localhost:5500/dashboard.html`
- `http://localhost:5500/api-scores.html`
- `http://localhost:5500/reports.html`

## Run The Backend

In a second terminal:

```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger docs are available at `http://localhost:8000/docs`.

On startup, the backend creates SQLite tables under `storage/flow2api.db`, creates storage directories, and loads the three workflows from `examples/`.

## Useful Commands

Seed the database manually:

```bash
python3 seed_db.py
```

Run all standalone Playwright workflows against the dashboard:

```bash
python3 test_runner.py
```

Run a full API smoke test after both servers are running:

```bash
python3 test_api.py
```

## Generated APIs

Seeded endpoints:

- `POST http://localhost:8000/api/generated/check-supplier-status/run`
- `POST http://localhost:8000/api/generated/check-api-score/run`
- `POST http://localhost:8000/api/generated/get-reports-table/run`

Example:

```bash
curl -X POST http://localhost:8000/api/generated/check-supplier-status/run \
  -H "Content-Type: application/json" \
  -d '{"supplier_id": "SUP001"}'
```

## Project Layout

- `mock-dashboard/` - static internal dashboard target app.
- `engine/` - async Playwright workflow runner and step handlers.
- `api/` - FastAPI app, routes, SQLite persistence, and storage helpers.
- `examples/` - three workflow JSON files matching the shared schema.
- `analyzer/llm_analyzer.py` - placeholder interface for Person B's video analysis module.
- `storage/` - screenshots, videos, frames, downloads, and SQLite database.

