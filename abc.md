# PERSON A — "The Engine" — Full Build Prompt

You are building the backend engine for a hackathon project called **Flow2API**.

> Flow2API converts screen-recorded internal workflows into reusable APIs. A user uploads a video showing how a task is done, the system extracts the steps, turns them into an editable workflow JSON, executes the workflow using browser automation, and exposes it as an API endpoint.

Your job covers: **Mock Dashboard, Playwright Runner, FastAPI Backend, Database, Generated API Endpoints, AI Self-Healing Skill.**

Your partner (Person B) is independently building: Video Processing, Vision LLM Analyzer, and the Streamlit Frontend. You will not be in contact except at brief sync points. Everything you build must work standalone using hand-written workflow JSONs.

---

## TASK 1: Mock Internal Dashboard (Do this FIRST)

Build a simple standalone web app that pretends to be a company's internal tool. This is the TARGET website that the automation engine will run against.

**Tech:** Plain HTML + CSS + vanilla JS. Serve with Python's `http.server` or Flask on port 5500.

**Build 3 pages:**

### Page 1: Supplier Dashboard (`/dashboard` or `/dashboard.html`)
- A heading: "Supplier Verification Dashboard"
- A text input labeled "Supplier ID" with `data-testid="supplier-id-input"`
- A "Search" button with `data-testid="search-btn"`
- A results area (hidden until search) with `data-testid="results-area"` showing:
  - Supplier Name (`data-testid="supplier-name"`)
  - Verification Status (`data-testid="verification-status"`)
  - Last Verified Date (`data-testid="last-verified"`)
  - Contact Email (`data-testid="contact-email"`)
- Seed with at least 20 fake suppliers in a JS object or JSON file
- Searching an ID that exists shows the result. Searching one that doesn't shows "No supplier found."

### Page 2: API Score Checker (`/api-scores` or `/api-scores.html`)
- A heading: "API Documentation Score Checker"
- A dropdown/select labeled "Select API" with `data-testid="api-select"` containing 8–10 fake API names
- A "Check Score" button with `data-testid="check-btn"`
- Results area showing:
  - API Score (out of 100) (`data-testid="api-score"`)
  - Issues Found (`data-testid="issues-count"`)
  - Last Checked (`data-testid="last-checked"`)

### Page 3: Reports Table (`/reports` or `/reports.html`)
- A heading: "Monthly Reports"
- A table with columns: Report Name, Department, Date, Status
- `data-testid="reports-table"` on the `<table>`
- 15–20 rows of fake data
- Each row is clickable, opening a detail view showing the full report info

**Critical requirements:**
- Every interactive element MUST have `data-testid` attributes AND clear visible `<label>` tags on form inputs
- Use semantic HTML: `<button>`, `<label for="...">`, `<input>`, `<select>`, `<table>`
- The app must look like a real (simple) internal dashboard — add a nav bar linking all 3 pages, use a clean CSS style
- Add a small artificial delay (300–500ms) to search/check actions to simulate real app behavior

**Deliverable:** A folder `mock-dashboard/` that runs on `http://localhost:5500` with all 3 pages working.

---

## TASK 2: Playwright Automation Runner

Build a Python module that takes a workflow JSON + input values, launches a browser, executes each step, and returns structured results.

**The Workflow JSON Schema (this is the shared contract with Person B):**

```json
{
  "workflow_name": "check_supplier_status",
  "slug": "check-supplier-status",
  "description": "Check supplier verification status from dashboard",
  "inputs": [
    { "name": "supplier_id", "type": "string", "required": true }
  ],
  "steps": [
    {
      "id": "step_1",
      "type": "navigate",
      "url": "http://localhost:5500/dashboard",
      "description": "Open the supplier dashboard"
    },
    {
      "id": "step_2",
      "type": "fill",
      "selector_type": "label",
      "selector_value": "Supplier ID",
      "value": "{{supplier_id}}",
      "description": "Type supplier ID into search box"
    },
    {
      "id": "step_3",
      "type": "click",
      "selector_type": "role",
      "selector_value": "Search",
      "description": "Click the search button"
    },
    {
      "id": "step_4",
      "type": "wait",
      "duration_ms": 1500,
      "description": "Wait for results to load"
    },
    {
      "id": "step_5",
      "type": "extract_text",
      "selector_type": "test_id",
      "selector_value": "verification-status",
      "output_key": "verification_status",
      "description": "Read the verification status"
    }
  ],
  "outputs": [
    { "name": "verification_status", "type": "string" }
  ]
}
```

**Selector types and how they map to Playwright:**

| selector_type | Playwright call |
|---|---|
| `label` | `page.get_by_label(selector_value)` |
| `role` | `page.get_by_role("button", name=selector_value)` (for clicks) or `page.get_by_role("link", name=selector_value)` |
| `text` | `page.get_by_text(selector_value)` |
| `test_id` | `page.get_by_test_id(selector_value)` |
| `css` | `page.locator(selector_value)` |
| `placeholder` | `page.get_by_placeholder(selector_value)` |

**Supported step types:**

| Step Type | Required Fields | What It Does |
|---|---|---|
| `navigate` | `url` | `page.goto(url)` |
| `fill` | `selector_type`, `selector_value`, `value` | Find element, type value into it |
| `click` | `selector_type`, `selector_value` | Find element, click it |
| `select` | `selector_type`, `selector_value`, `option_value` | Select dropdown option |
| `wait` | `duration_ms` | `page.wait_for_timeout(duration_ms)` |
| `extract_text` | `selector_type`, `selector_value`, `output_key` | Get `.inner_text()`, store in outputs[output_key] |
| `extract_table` | `selector_type`, `selector_value`, `output_key` | Extract full table as list of dicts |
| `download_file` | `selector_type`, `selector_value`, `output_key` | Handle download, store file path |

**Runner implementation requirements:**

```
engine/
├── runner.py             # Main run_workflow() function
├── step_handlers.py      # One handler function per step type
├── selector_resolver.py  # resolve(page, selector_type, selector_value) → Locator
├── variable_resolver.py  # Replace {{var}} in step values with actual inputs
├── screenshot.py         # Take + save screenshots
├── ai_fallback.py        # AI self-healing when selectors fail
├── models.py             # ExecutionResult, StepLog dataclasses
└── exceptions.py         # Custom errors
```

**Core logic for runner.py:**

```python
async def run_workflow(workflow: dict, inputs: dict, execution_id: str) -> ExecutionResult:
    # 1. Create screenshot directory: storage/screenshots/{execution_id}/
    # 2. Resolve all {{variable}} references in steps using inputs dict
    # 3. Launch playwright chromium browser (headless=True for prod, headless=False for debug)
    # 4. Create new page
    # 5. For each step in workflow["steps"]:
    #    a. Try to execute the step using the appropriate handler
    #    b. Take screenshot after step: {execution_id}/step_{step_id}.png
    #    c. Record StepLog(step_id, status="success"|"failed"|"ai_fallback", message, screenshot_path, duration_ms)
    #    d. If step fails and AI fallback is enabled:
    #       - Take screenshot of current page
    #       - Call ai_resolve_selector() to get corrected selector
    #       - Retry the step with the new selector
    #       - Log as "ai_fallback" status
    #    e. If step fails completely, log error and stop (or continue based on config)
    # 6. Close browser
    # 7. Return ExecutionResult(outputs=collected_outputs, logs=step_logs, status, error_message)
```

**Variable resolution:**
Scan every string value in each step for `{{variable_name}}` pattern. Replace with `inputs[variable_name]`. If a variable is referenced but not in inputs, raise an error.

**Screenshot capture:**
After EVERY step (success or fail), take a full-page screenshot. Save to `storage/screenshots/{execution_id}/step_{step_id}.png`. This is crucial for the demo — the frontend displays these.

**AI Self-Healing Fallback (the "skill" in the pipeline):**

```python
# ai_fallback.py
# When a selector fails to find an element:
# 1. Capture screenshot of current page
# 2. Send to a vision LLM (Claude/GPT-4V) with this prompt:
#
#    "I am automating a browser task. I need to {step.description}.
#     The step type is '{step.type}'.
#     I tried to find an element using {step.selector_type}='{step.selector_value}' but it wasn't found.
#     
#     Look at this screenshot of the current page state.
#     Identify the correct element I should interact with.
#     
#     Return ONLY a JSON object:
#     {
#       "selector_type": "css" | "text" | "test_id" | "label" | "role",
#       "selector_value": "the correct selector"
#     }"
#
# 3. Parse the response
# 4. Return the new selector for retry
```

**Write 3 test workflow JSON files:**

1. `examples/check_supplier.json` — Navigate → Fill → Click → Wait → Extract (against /dashboard)
2. `examples/check_api_score.json` — Navigate → Select dropdown → Click → Wait → Extract 3 fields (against /api-scores)
3. `examples/get_reports_table.json` — Navigate → Extract table (against /reports)

**Test the runner standalone:**

```python
# test_runner.py
import asyncio
from engine.runner import run_workflow
import json

async def main():
    with open("examples/check_supplier.json") as f:
        workflow = json.load(f)
    
    result = await run_workflow(workflow, {"supplier_id": "SUP001"}, "test_exec_001")
    
    print("Status:", result.status)
    print("Outputs:", result.outputs)
    print("Logs:", [(log.step_id, log.status) for log in result.logs])
    print("Screenshots:", [log.screenshot_path for log in result.logs])

asyncio.run(main())
```

All 3 test workflows should pass against the mock dashboard before moving to Task 3.

---

## TASK 3: FastAPI Backend + Database

Wrap the runner in an HTTP API.

**File structure:**

```
api/
├── main.py              # FastAPI app, CORS, static files, startup
├── database.py          # SQLite init + query functions
├── models.py            # Pydantic request/response models
├── routes/
│   ├── workflows.py     # Workflow CRUD
│   ├── executions.py    # Execution results + logs
│   ├── generated.py     # Dynamic /api/generated/{slug}/run
│   └── videos.py        # Video upload (receives file, saves, returns ID)
└── storage.py           # File path helpers
```

**Database — SQLite (use aiosqlite or plain sqlite3):**

```sql
CREATE TABLE workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    description TEXT,
    workflow_json TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    video_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE executions (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    input_json TEXT NOT NULL,
    output_json TEXT,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE execution_logs (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    step_type TEXT,
    status TEXT,
    message TEXT,
    screenshot_path TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE videos (
    id TEXT PRIMARY KEY,
    filename TEXT,
    file_path TEXT,
    status TEXT DEFAULT 'uploaded',
    frame_count INTEGER,
    workflow_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Endpoints to implement (in this exact order):**

### Workflow CRUD
```
POST   /api/workflows              — Save workflow JSON, auto-generate slug from name
GET    /api/workflows              — List all workflows
GET    /api/workflows/{id}         — Get single workflow with full JSON
PUT    /api/workflows/{id}         — Update workflow (for editing)
DELETE /api/workflows/{id}         — Delete workflow
```

### Execution
```
POST   /api/workflows/{id}/test    — Run workflow with provided inputs, return results
GET    /api/executions/{id}        — Get execution with outputs
GET    /api/executions/{id}/logs   — Get step-by-step logs with screenshot URLs
```

### Generated API (THE core feature)
```
POST   /api/generated/{slug}/run   — Accept inputs matching workflow's input schema,
                                      execute workflow, return outputs
```

This endpoint is special. Implementation:

```python
@router.post("/api/generated/{slug}/run")
async def run_generated_api(slug: str, body: dict):
    # 1. Look up workflow by slug
    # 2. If not found, return 404 with helpful message
    # 3. Validate that body contains all required inputs
    # 4. Create execution record with status="running"
    # 5. Call run_workflow(workflow_json, body, execution_id)
    # 6. Update execution record with results
    # 7. Save step logs
    # 8. Return:
    #    {
    #      "execution_id": "...",
    #      "status": "success" | "failed",
    #      "outputs": { ... },
    #      "duration_ms": 3400,
    #      "logs_url": "/api/executions/{execution_id}/logs"
    #    }
```

### Video Upload (receives from Person B's frontend)
```
POST   /api/videos/upload          — Accept video file, save to storage/videos/, return video_id
POST   /api/videos/{id}/analyze    — This will call Person B's analysis function.
                                      For now, return a stub response:
                                      { "status": "pending", "message": "Analysis module not yet connected" }
                                      Person B will provide the actual function to wire in.
```

### API Documentation Generator
```
GET    /api/workflows/{id}/docs    — Return auto-generated API documentation
```

```python
def generate_docs(workflow):
    slug = workflow["slug"]
    return {
        "endpoint": f"POST /api/generated/{slug}/run",
        "method": "POST",
        "description": workflow.get("description", ""),
        "request_body": {
            inp["name"]: {"type": inp["type"], "required": inp.get("required", True)}
            for inp in workflow.get("inputs", [])
        },
        "response_body": {
            out["name"]: {"type": out["type"]}
            for out in workflow.get("outputs", [])
        },
        "curl_example": f'''curl -X POST http://localhost:8000/api/generated/{slug}/run \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps({inp["name"]: f"<{inp['type']}>" for inp in workflow.get("inputs", [])})}\'''',
        "python_example": f'''import requests

response = requests.post(
    "http://localhost:8000/api/generated/{slug}/run",
    json={json.dumps({inp["name"]: f"<{inp['type']}>" for inp in workflow.get("inputs", [])}, indent=4)}
)
print(response.json())'''
    }
```

**Additional requirements:**
- Enable CORS for all origins (hackathon, no security needed)
- Mount `storage/screenshots/` as static files at `/screenshots/`
- Mount `storage/frames/` as static files at `/frames/`
- Run on port 8000
- On startup, create all database tables if they don't exist
- On startup, load the 3 example workflow JSONs into the database

**Deliverable:** A running FastAPI server at `http://localhost:8000` with Swagger docs at `/docs`, where you can:
1. Save workflows
2. Call `POST /api/generated/{slug}/run` with inputs and get browser-automated results back
3. View execution logs with screenshot URLs

---

## TASK 4: Integration Prep

Prepare these for when Person B connects their work:

### Wire video analysis endpoint
Create a clear interface that Person B's code needs to implement:

```python
# This is the function signature Person B must provide:
# File: analyzer/llm_analyzer.py

async def analyze_video(video_id: str, frames_dir: str, user_context: str = "") -> dict:
    """
    Takes a video_id and path to extracted frames.
    Returns a workflow JSON matching the shared schema.
    """
    pass  # Person B implements this
```

In your `/api/videos/{id}/analyze` endpoint, import and call this function. If it doesn't exist yet, catch the import error and return the stub.

### Seed the database
Write a script `seed_db.py` that loads all 3 example workflows into the database so the frontend has data to show immediately.

### Test the full backend
Write a simple script that:
1. Creates a workflow via API
2. Calls the generated endpoint
3. Fetches the execution logs
4. Prints everything

---

## Important Notes

- Use `async` Playwright (`from playwright.async_api import async_playwright`) since FastAPI is async
- Use `uuid4()` for all IDs
- Store all files under a `storage/` directory: `storage/videos/`, `storage/frames/`, `storage/screenshots/`
- The mock dashboard must be running on port 5500 for the runner to work. Add a note about this in a README.
- Person B will send API requests to `http://localhost:8000` from Streamlit. Make sure CORS allows it.
