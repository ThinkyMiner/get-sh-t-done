from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


def _assert_keys(payload: dict, required: list[str], label: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise AssertionError(f"{label} missing keys: {missing}")


def main() -> None:
    client = TestClient(app)

    workflow = json.loads(Path("examples/check_supplier.json").read_text(encoding="utf-8"))
    workflow["workflow_name"] = "Contract Smoke Supplier Workflow"

    create_resp = client.post("/api/workflows", json=workflow)
    create_resp.raise_for_status()
    created = create_resp.json()
    _assert_keys(created, ["workflow_id", "id", "slug", "name"], "create_workflow")
    workflow_id = created["workflow_id"]
    slug = created["slug"]
    print("CREATE", workflow_id, slug)

    list_resp = client.get("/api/workflows")
    list_resp.raise_for_status()
    workflows = list_resp.json()
    assert any(item["id"] == workflow_id for item in workflows), "workflow not present in list response"
    print("LIST", len(workflows))

    get_resp = client.get(f"/api/workflows/{workflow_id}")
    get_resp.raise_for_status()
    fetched = get_resp.json()
    _assert_keys(fetched, ["id", "name", "slug", "workflow_json"], "get_workflow")
    print("GET", fetched["slug"])

    updated_workflow = dict(fetched["workflow_json"])
    updated_workflow["description"] = "Updated by contract smoke test"
    update_resp = client.put(f"/api/workflows/{workflow_id}", json=updated_workflow)
    update_resp.raise_for_status()
    updated = update_resp.json()
    _assert_keys(updated, ["status", "workflow_id", "workflow_json"], "update_workflow")
    assert updated["status"] == "updated"
    print("UPDATE", updated["status"])

    test_resp = client.post(f"/api/workflows/{workflow_id}/test", json={"supplier_id": "SUP001"})
    test_resp.raise_for_status()
    test_result = test_resp.json()
    _assert_keys(
        test_result,
        ["execution_id", "status", "outputs", "duration_ms", "logs_url"],
        "test_workflow",
    )
    assert test_result["status"] == "success"
    execution_id = test_result["execution_id"]
    print("TEST", execution_id, test_result["outputs"])

    run_resp = client.post(f"/api/generated/{slug}/run", json={"supplier_id": "SUP001"})
    run_resp.raise_for_status()
    run_result = run_resp.json()
    _assert_keys(
        run_result,
        ["execution_id", "status", "outputs", "duration_ms", "logs_url"],
        "generated_run",
    )
    assert run_result["status"] == "success"
    print("GENERATED", run_result["execution_id"], run_result["outputs"])

    execution_resp = client.get(f"/api/executions/{execution_id}")
    execution_resp.raise_for_status()
    execution = execution_resp.json()
    _assert_keys(execution, ["id", "workflow_id", "status", "logs_url"], "get_execution")
    print("EXECUTION", execution["status"])

    logs_resp = client.get(f"/api/executions/{execution_id}/logs")
    logs_resp.raise_for_status()
    logs = logs_resp.json()
    assert logs, "execution logs missing"
    _assert_keys(
        logs[0],
        ["step_id", "step_type", "status", "message", "screenshot_path", "duration_ms", "screenshot_url"],
        "execution_log",
    )
    print("LOGS", len(logs))

    docs_resp = client.get(f"/api/workflows/{workflow_id}/docs")
    docs_resp.raise_for_status()
    docs = docs_resp.json()
    _assert_keys(
        docs,
        ["endpoint", "curl_example", "python_example", "request_body", "response_body"],
        "docs",
    )
    print("DOCS", docs["endpoint"])

    video_path = Path("storage/videos/smoke_test.mp4")
    if video_path.exists():
        with video_path.open("rb") as handle:
            upload_resp = client.post(
                "/api/videos/upload",
                files={"file": (video_path.name, handle, "video/mp4")},
            )
        upload_resp.raise_for_status()
        upload = upload_resp.json()
        _assert_keys(upload, ["video_id", "status"], "upload_video")
        video_id = upload["video_id"]
        print("UPLOAD", video_id)

        analyze_resp = client.post(
            f"/api/videos/{video_id}/analyze",
            json={"user_context": "Search supplier by ID and return verification status"},
        )
        analyze_resp.raise_for_status()
        analyzed = analyze_resp.json()
        _assert_keys(
            analyzed,
            ["status", "workflow_id", "workflow_json", "confidence"],
            "analyze_video",
        )
        print("ANALYZE", analyzed["workflow_id"], analyzed["workflow_json"]["slug"], analyzed["confidence"])


if __name__ == "__main__":
    main()
