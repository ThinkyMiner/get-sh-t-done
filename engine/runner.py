from __future__ import annotations

import os
import time
from copy import deepcopy
from typing import Any

from playwright.async_api import async_playwright

from .ai_fallback import ai_resolve_selector
from .models import ExecutionResult, StepLog
from .screenshot import screenshot_dir, take_screenshot
from .step_handlers import get_handler
from .variable_resolver import resolve_workflow_variables


def _validate_required_inputs(workflow: dict[str, Any], inputs: dict[str, Any]) -> None:
    missing = [
        item["name"]
        for item in workflow.get("inputs", [])
        if item.get("required", True) and item.get("name") not in inputs
    ]
    if missing:
        raise ValueError(f"Missing required input(s): {', '.join(missing)}")


async def _safe_screenshot(page: Any, execution_id: str, step_id: str) -> str | None:
    try:
        return await take_screenshot(page, execution_id, step_id)
    except Exception:
        return None


async def _execute_step(
    page: Any,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    handler = get_handler(step["type"])
    await handler(page, step, outputs, execution_id)


async def run_workflow(
    workflow: dict[str, Any],
    inputs: dict[str, Any],
    execution_id: str,
    *,
    headless: bool | None = None,
    ai_fallback_enabled: bool = True,
    continue_on_error: bool = False,
) -> ExecutionResult:
    total_started = time.perf_counter()
    outputs: dict[str, Any] = {}
    logs: list[StepLog] = []
    status = "success"
    error_message: str | None = None

    _validate_required_inputs(workflow, inputs)
    resolved_workflow = resolve_workflow_variables(workflow, inputs)
    screenshot_dir(execution_id)

    if headless is None:
        headless = os.getenv("FLOW2API_HEADLESS", "true").lower() not in {"0", "false", "no"}

    browser = None
    async with async_playwright() as playwright:
        try:
            browser = await playwright.chromium.launch(headless=headless)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})
            page.set_default_timeout(int(os.getenv("FLOW2API_STEP_TIMEOUT_MS", "5000")))

            for step in resolved_workflow.get("steps", []):
                step_id = str(step.get("id", f"step_{len(logs) + 1}"))
                step_type = str(step.get("type", "unknown"))
                started = time.perf_counter()

                try:
                    await _execute_step(page, step, outputs, execution_id)
                    screenshot_path = await _safe_screenshot(page, execution_id, step_id)
                    duration_ms = int((time.perf_counter() - started) * 1000)
                    logs.append(
                        StepLog(
                            step_id=step_id,
                            step_type=step_type,
                            status="success",
                            message=f"{step_type} completed",
                            screenshot_path=screenshot_path,
                            duration_ms=duration_ms,
                        )
                    )
                    continue
                except Exception as exc:
                    failure_screenshot = await _safe_screenshot(page, execution_id, f"{step_id}_failed")
                    healed_selector = None
                    if ai_fallback_enabled and step.get("selector_type") and failure_screenshot:
                        healed_selector = await ai_resolve_selector(page, step, failure_screenshot)

                    if healed_selector:
                        retry_step = deepcopy(step)
                        retry_step["selector_type"] = healed_selector["selector_type"]
                        retry_step["selector_value"] = healed_selector["selector_value"]
                        try:
                            await _execute_step(page, retry_step, outputs, execution_id)
                            screenshot_path = await _safe_screenshot(page, execution_id, step_id)
                            duration_ms = int((time.perf_counter() - started) * 1000)
                            logs.append(
                                StepLog(
                                    step_id=step_id,
                                    step_type=step_type,
                                    status="ai_fallback",
                                    message=(
                                        f"{step_type} completed using AI fallback selector "
                                        f"{healed_selector['selector_type']}={healed_selector['selector_value']}"
                                    ),
                                    screenshot_path=screenshot_path,
                                    duration_ms=duration_ms,
                                )
                            )
                            continue
                        except Exception as retry_exc:
                            exc = retry_exc

                    duration_ms = int((time.perf_counter() - started) * 1000)
                    screenshot_path = await _safe_screenshot(page, execution_id, step_id)
                    logs.append(
                        StepLog(
                            step_id=step_id,
                            step_type=step_type,
                            status="failed",
                            message=str(exc),
                            screenshot_path=screenshot_path or failure_screenshot,
                            duration_ms=duration_ms,
                        )
                    )
                    status = "failed"
                    error_message = f"Step {step_id} failed: {exc}"
                    if not continue_on_error:
                        break
        except Exception as exc:
            status = "failed"
            error_message = str(exc)
        finally:
            if browser is not None:
                await browser.close()

    duration_ms = int((time.perf_counter() - total_started) * 1000)
    return ExecutionResult(
        execution_id=execution_id,
        status=status,
        outputs=outputs,
        logs=logs,
        error_message=error_message,
        duration_ms=duration_ms,
    )
