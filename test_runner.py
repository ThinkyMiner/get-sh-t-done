import asyncio
import json
from pathlib import Path
from uuid import uuid4

from engine.runner import run_workflow


WORKFLOWS = [
    ("examples/check_supplier.json", {"supplier_id": "SUP001"}),
    ("examples/check_api_score.json", {"api_name": "billing_v2"}),
    ("examples/get_reports_table.json", {}),
]


async def run_one(path: str, inputs: dict) -> None:
    workflow = json.loads(Path(path).read_text(encoding="utf-8"))
    execution_id = f"test_{workflow['slug']}_{uuid4().hex[:8]}"
    result = await run_workflow(workflow, inputs, execution_id)
    print(f"\nWorkflow: {workflow['workflow_name']}")
    print("Status:", result.status)
    print("Outputs:", json.dumps(result.outputs, indent=2))
    print("Logs:", [(log.step_id, log.status) for log in result.logs])
    print("Screenshots:", [log.screenshot_path for log in result.logs])
    if result.error_message:
        print("Error:", result.error_message)


async def main() -> None:
    for path, inputs in WORKFLOWS:
        await run_one(path, inputs)


if __name__ == "__main__":
    asyncio.run(main())
