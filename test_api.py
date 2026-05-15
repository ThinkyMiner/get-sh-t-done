import json
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000"


def request(method: str, path: str, payload: dict | None = None) -> dict | list:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} failed: {exc.code} {body}") from exc


def main() -> None:
    workflow = json.loads(Path("examples/check_supplier.json").read_text(encoding="utf-8"))
    workflow["workflow_name"] = "Check Supplier Status API Smoke"
    created = request("POST", "/api/workflows", workflow)
    slug = created["slug"]
    workflow_id = created["id"]
    print("Created workflow:", workflow_id, slug)

    result = request("POST", f"/api/generated/{slug}/run", {"supplier_id": "SUP001"})
    print("Generated API result:")
    print(json.dumps(result, indent=2))

    logs = request("GET", result["logs_url"])
    print("Execution logs:")
    print(json.dumps(logs, indent=2))


if __name__ == "__main__":
    main()
