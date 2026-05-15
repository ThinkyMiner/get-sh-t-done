# Flow2API

Hackathon scaffold for turning screen-recorded workflows into reusable APIs.

This branch sets up the shared contract plus the Person B surface area:

- `video/` for frame extraction and keyframe curation
- `analyzer/` for vision-LLM workflow generation and schema validation
- `frontend/` for the Streamlit UI in mock-first mode
- `examples/` for contract-aligned workflow fixtures

## Quick start

1. Create a virtualenv and install dependencies from `requirements.txt`.
2. Ensure `ffmpeg` is installed for video frame extraction.
3. Run the frontend:

```bash
cd frontend
streamlit run app.py
```

## Notes

- The frontend is built to work without Person A's backend by falling back to mock session data.
- `analyzer/llm_analyzer.py` exposes `analyze_video(video_id, video_path, user_context="")` for backend integration.
