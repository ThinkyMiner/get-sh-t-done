from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from .storage import DB_PATH, ensure_storage_dirs


def connect() -> sqlite3.Connection:
    ensure_storage_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                description TEXT,
                workflow_json TEXT NOT NULL,
                source TEXT DEFAULT 'manual',
                video_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                input_json TEXT NOT NULL,
                output_json TEXT,
                status TEXT DEFAULT 'running',
                error_message TEXT,
                duration_ms INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS execution_logs (
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

            CREATE TABLE IF NOT EXISTS videos (
                id TEXT PRIMARY KEY,
                filename TEXT,
                file_path TEXT,
                status TEXT DEFAULT 'uploaded',
                frame_count INTEGER,
                workflow_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "workflow"


def _workflow_name(workflow: dict[str, Any]) -> str:
    return workflow.get("workflow_name") or workflow.get("name") or "Untitled Workflow"


def _normalize_workflow(
    workflow: dict[str, Any],
    *,
    force_slug: bool = False,
    exclude_id: str | None = None,
) -> tuple[dict[str, Any], str, str, str]:
    normalized = dict(workflow)
    name = _workflow_name(normalized)
    base_slug = slugify(name) if force_slug or not normalized.get("slug") else slugify(normalized["slug"])
    slug = _unique_slug(base_slug, exclude_id=exclude_id)
    normalized["workflow_name"] = name
    normalized["slug"] = slug
    description = normalized.get("description", "")
    return normalized, name, slug, description


def _unique_slug(base_slug: str, exclude_id: str | None = None) -> str:
    with connect() as conn:
        slug = base_slug
        suffix = 2
        while True:
            row = conn.execute("SELECT id FROM workflows WHERE slug = ?", (slug,)).fetchone()
            if row is None or row["id"] == exclude_id:
                return slug
            slug = f"{base_slug}-{suffix}"
            suffix += 1


def _parse_workflow_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    record = dict(row)
    record["workflow_json"] = json.loads(record["workflow_json"])
    return record


def create_workflow(
    workflow: dict[str, Any],
    *,
    source: str = "manual",
    video_id: str | None = None,
    force_slug: bool = True,
) -> dict[str, Any]:
    workflow_id = str(uuid4())
    normalized, name, slug, description = _normalize_workflow(workflow, force_slug=force_slug)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO workflows (id, name, slug, description, workflow_json, source, video_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (workflow_id, name, slug, description, json.dumps(normalized), source, video_id),
        )
    return get_workflow_by_id(workflow_id)


def list_workflows() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, slug, description, source, video_id, created_at
            FROM workflows
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_workflow_by_id(workflow_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
    return _parse_workflow_row(row)


def get_workflow_by_slug(slug: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM workflows WHERE slug = ?", (slug,)).fetchone()
    return _parse_workflow_row(row)


def update_workflow(workflow_id: str, workflow: dict[str, Any]) -> dict[str, Any] | None:
    if get_workflow_by_id(workflow_id) is None:
        return None
    normalized, name, slug, description = _normalize_workflow(
        workflow,
        force_slug=not bool(workflow.get("slug")),
        exclude_id=workflow_id,
    )
    with connect() as conn:
        conn.execute(
            """
            UPDATE workflows
            SET name = ?, slug = ?, description = ?, workflow_json = ?
            WHERE id = ?
            """,
            (name, slug, description, json.dumps(normalized), workflow_id),
        )
    return get_workflow_by_id(workflow_id)


def delete_workflow(workflow_id: str) -> bool:
    with connect() as conn:
        cursor = conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        return cursor.rowcount > 0


def upsert_workflow_by_slug(
    workflow: dict[str, Any],
    *,
    source: str = "example",
    video_id: str | None = None,
) -> dict[str, Any]:
    slug = slugify(workflow.get("slug") or _workflow_name(workflow))
    normalized = dict(workflow)
    normalized["slug"] = slug
    existing = get_workflow_by_slug(slug)
    if existing:
        return update_workflow(existing["id"], normalized)
    return create_workflow(normalized, source=source, video_id=video_id, force_slug=False)


def load_example_workflows(example_dir: str = "examples") -> list[dict[str, Any]]:
    loaded = []
    for path in sorted(Path(example_dir).glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            loaded.append(upsert_workflow_by_slug(json.load(handle), source="example"))
    return loaded


def create_execution(
    workflow_id: str,
    inputs: dict[str, Any],
    *,
    execution_id: str | None = None,
) -> str:
    execution_id = execution_id or str(uuid4())
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO executions (id, workflow_id, input_json, status)
            VALUES (?, ?, ?, 'running')
            """,
            (execution_id, workflow_id, json.dumps(inputs)),
        )
    return execution_id


def update_execution(
    execution_id: str,
    *,
    status: str,
    outputs: dict[str, Any] | None = None,
    error_message: str | None = None,
    duration_ms: int | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE executions
            SET status = ?, output_json = ?, error_message = ?, duration_ms = ?
            WHERE id = ?
            """,
            (
                status,
                json.dumps(outputs) if outputs is not None else None,
                error_message,
                duration_ms,
                execution_id,
            ),
        )


def save_execution_logs(execution_id: str, logs: list[Any]) -> None:
    with connect() as conn:
        for log in logs:
            log_data = log.to_dict() if hasattr(log, "to_dict") else dict(log)
            conn.execute(
                """
                INSERT INTO execution_logs (
                    id, execution_id, step_id, step_type, status,
                    message, screenshot_path, duration_ms
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid4()),
                    execution_id,
                    log_data.get("step_id"),
                    log_data.get("step_type"),
                    log_data.get("status"),
                    log_data.get("message"),
                    log_data.get("screenshot_path"),
                    log_data.get("duration_ms"),
                ),
            )


def get_execution(execution_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM executions WHERE id = ?", (execution_id,)).fetchone()
    if row is None:
        return None
    record = dict(row)
    record["input_json"] = json.loads(record["input_json"])
    record["output_json"] = json.loads(record["output_json"]) if record["output_json"] else None
    return record


def get_execution_logs(execution_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM execution_logs
            WHERE execution_id = ?
            ORDER BY created_at ASC, rowid ASC
            """,
            (execution_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def create_video(video_id: str, filename: str | None, file_path: str) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO videos (id, filename, file_path, status)
            VALUES (?, ?, ?, 'uploaded')
            """,
            (video_id, filename, file_path),
        )
    return get_video(video_id)


def get_video(video_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    return dict(row) if row else None


def update_video(
    video_id: str,
    *,
    status: str | None = None,
    frame_count: int | None = None,
    workflow_id: str | None = None,
) -> dict[str, Any] | None:
    current = get_video(video_id)
    if current is None:
        return None
    with connect() as conn:
        conn.execute(
            """
            UPDATE videos
            SET status = COALESCE(?, status),
                frame_count = COALESCE(?, frame_count),
                workflow_id = COALESCE(?, workflow_id)
            WHERE id = ?
            """,
            (status, frame_count, workflow_id, video_id),
        )
    return get_video(video_id)
