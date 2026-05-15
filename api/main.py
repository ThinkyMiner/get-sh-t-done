from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api import database
from api.routes import executions, generated, videos, workflows
from api.storage import FRAMES_DIR, SCREENSHOTS_DIR, ensure_storage_dirs

app = FastAPI(
    title="Flow2API Backend",
    description="Convert recorded internal workflows into runnable generated APIs.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    ensure_storage_dirs()
    database.init_db()
    database.load_example_workflows()


app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")
app.mount("/frames", StaticFiles(directory=str(FRAMES_DIR)), name="frames")

app.include_router(workflows.router)
app.include_router(executions.router)
app.include_router(generated.router)
app.include_router(videos.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "name": "Flow2API",
        "docs": "/docs",
        "generated_api": "/api/generated/{slug}/run",
    }

