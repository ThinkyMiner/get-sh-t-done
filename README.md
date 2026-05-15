# Flow2API

Flow2API converts screen-recorded internal workflows into reusable APIs.

This integration branch combines:

- `mock-dashboard/` static target app
- `engine/` Playwright runner
- `api/` FastAPI backend
- `video/` frame extraction and keyframe curation
- `analyzer/` vision-LLM workflow generation and validation
- `frontend/` Streamlit UI
- `examples/` shared workflow fixtures

## Quick start

1. Create a Python 3.12 virtualenv and install dependencies from `requirements.txt`.
2. Ensure `ffmpeg` is installed.
3. Install the Playwright browser:

```bash
python -m playwright install chromium
```

4. Run the mock dashboard:

```bash
python3 -m http.server 5500 --directory mock-dashboard
```

5. Run the backend:

```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

6. Run the frontend:

```bash
streamlit run frontend/app.py --server.port 8501
```

## Notes

- The frontend works with the real backend or falls back to local storage/testing mode.
- `analyzer/llm_analyzer.py` exposes `analyze_video(video_id, video_path, user_context="")` for backend integration.
- Swagger docs are available at `http://localhost:8000/docs`.
- The backend seeds example workflows into `storage/flow2api.db` on startup.
