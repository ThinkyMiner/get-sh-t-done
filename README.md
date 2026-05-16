# Flow2API

Flow2API converts repeatable UI workflows into reusable APIs.

The project takes a screen recording, extracts keyframes, asks a vision-capable model to infer the workflow, validates the generated steps, and runs the result through a Playwright-based execution engine. For known apps, the pipeline can apply a folder-backed skill that injects app-specific guidance and a canonical workflow fallback.

## Why This Exists

Many internal workflows are still trapped in dashboards:
- search a record
- open a detail view
- read a status
- repeat that same sequence again and again

Flow2API turns those repeated clicks into machine-readable, callable interfaces.

## Repo Layout

- `api/` FastAPI backend and generated API endpoints
- `engine/` Playwright runner, step handlers, selector resolution, screenshots
- `video/` frame extraction, deduplication, and keyframe curation
- `analyzer/` timeline extraction, workflow generation, skill loading, validation
- `frontend/` Streamlit app
- `workflow_skills/` app/domain skills used by the analyzer pipeline
- `examples/` runnable workflow fixtures
- `mock-dashboard/` local mock target app
- `storage/` runtime DB, uploads, screenshots, browser profiles, frames

## Pipeline

1. Video ingestion
2. Frame extraction and deduplication
3. Timeline inference from ordered screenshots
4. Skill detection from timeline plus user context
5. Workflow generation with skill-aware prompt guidance
6. Schema validation and sanitization
7. Skill postprocessing for known app families
8. Execution through the browser runner
9. Logs, screenshots, and structured outputs

## Skill System

The pipeline now uses real skill folders under `workflow_skills/`.

Each skill folder contains:
- `SKILL.md`
- `references/timeline-guidance.md`
- `references/workflow-guidance.md`
- optional `references/runtime-guidance.md`
- optional `references/failure-patterns.md`
- optional `assets/workflow-template.json`

Current shipped skills:
- `weberp-company-verification`
- `savvyhrms-attendance`

### Why Skills Matter

Generic vision prompting is good enough for many simple flows, but enterprise apps often fail in repeatable ways:
- auth happens in popups
- OTP runs on a different page than the main app
- clicks target named frames instead of the top-level page
- visible business outputs live in secondary frames, not where the user first clicked
- direct URL navigation is blocked, while in-app frame hydration works

Those patterns should not be rediscovered from scratch every run. Skills provide that domain knowledge.

### Where Skills Fit

Skills are applied in three places:
- before timeline generation, to shape what the model notices
- before workflow generation, to shape selectors, auth, frames, and outputs
- after workflow generation, to apply a canonical fallback template when the generic model output is still weak

## WebERP Notes

The WebERP skill is based on actual observed failure modes during development.

Handled patterns include:
- Google sign-in popup handling
- popup auto-close after cached auth
- OTP field execution on the popup page
- company-detail frame hydration into `IframeSTS`
- summary controls in `TopBar1_topbarIframe`
- summary extraction from `viewmoreIframe`
- separation between summary frames and KYC analytics frames

This is important because a normal top-level click model was not sufficient for the real WebERP flow.

## Quick Start

### 1. Create the environment

```bash
python3.12 -m venv .venv312
source .venv312/bin/activate
pip install -r requirements.txt
```

### 2. Install system dependencies

- `ffmpeg` must be installed
- Playwright browser must be installed

```bash
./.venv312/bin/python -m playwright install chromium
```

### 3. Start the mock dashboard

```bash
python3 -m http.server 5500 --directory mock-dashboard
```

### 4. Start the backend

```bash
./.venv312/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. Start the frontend

```bash
./.venv312/bin/streamlit run frontend/app.py --server.port 8501
```

### 6. Open the app

- frontend: `http://localhost:8501`
- backend docs: `http://localhost:8000/docs`

## Running the Analyzer Directly

```python
import asyncio
from analyzer.llm_analyzer import analyze_video

result = asyncio.run(
    analyze_video(
        video_id="demo_video",
        video_path="/absolute/path/to/video.mp4",
        user_context="Search a company by GLID and extract verification statuses"
    )
)
print(result)
```

## Persistent Browser Sessions

For SSO-backed workflows, use a persistent browser profile.

Environment variables:

```bash
export FLOW2API_BROWSER_USER_DATA_DIR=/absolute/path/to/profile_dir
export FLOW2API_BROWSER_CHANNEL=chrome
export FLOW2API_HEADLESS=false
```

Utilities:

```bash
python scripts/prepare_chrome_profile.py
python scripts/bootstrap_google_auth.py
```

Recommended flow:
1. Prepare a local profile copy
2. Complete login once in the opened browser
3. Reuse the same profile for API runs

## LLM Configuration

Supported providers in the analyzer:
- `mock`
- `anthropic`
- `openai`
- `litellm_proxy`

Relevant environment variables:

```bash
export FLOW2API_LLM_PROVIDER=litellm_proxy
export FLOW2API_LITELLM_MODEL=openai/gpt-4o
export LITELLM_PROXY_API_BASE=https://your-proxy/v1
export LITELLM_PROXY_API_KEY=your-key
```

## Example Workflows

- `examples/weberp_company_gst_popup.json`
- other shared fixtures in `examples/`

These are useful both for smoke testing and for demonstrating execution independent of the full video pipeline.

## Verification

Useful checks:

```bash
python3 -m compileall analyzer api engine frontend video
./.venv312/bin/python test_runner.py
./.venv312/bin/python test_api.py
./.venv312/bin/python test_contract.py
```

## Known Limits

- Pure video understanding is still weaker than video plus DOM or browser telemetry.
- SSO-backed workflows are inherently more brittle than public-page flows.
- Some enterprise apps use layered frames and delayed iframe hydration, which require app-specific skills to run reliably.

## Practical Summary

Without skills, the system can produce a first draft.

With skills, the system becomes much more useful on real enterprise apps because it can carry forward:
- app-specific auth behavior
- frame structure
- extraction targets
- known failure corrections

That is the current design direction of this repo.
