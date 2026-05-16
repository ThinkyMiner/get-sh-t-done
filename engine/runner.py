from __future__ import annotations

import os
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from .ai_fallback import ai_resolve_selector
from .models import ExecutionResult, StepLog
from .selector_resolver import resolve
from .screenshot import screenshot_dir, take_screenshot
from .step_handlers import get_handler
from .variable_resolver import resolve_workflow_variables

SPECIAL_TARGETS = {"", "_self", "_parent", "_top", "_blank"}


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
    target: Any,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    handler = get_handler(step["type"])
    await handler(target, step, outputs, execution_id)


def _step_timeout_ms() -> int:
    return int(os.getenv("FLOW2API_STEP_TIMEOUT_MS", "5000"))


def _scope_is_closed(target: Any) -> bool:
    checker = getattr(target, "is_closed", None)
    if callable(checker):
        try:
            return bool(checker())
        except Exception:
            return True
    page_ref = getattr(target, "page", None)
    if page_ref is not None:
        checker = getattr(page_ref, "is_closed", None)
        if callable(checker):
            try:
                return bool(checker())
            except Exception:
                return True
    return False


async def _wait_for_frame(
    page: Any,
    *,
    name: str | None = None,
    url_contains: str | None = None,
    timeout_ms: int | None = None,
) -> Any:
    timeout_ms = timeout_ms or _step_timeout_ms()
    deadline = time.perf_counter() + (timeout_ms / 1000)
    while time.perf_counter() < deadline:
        for frame in page.frames:
            if name and frame.name == name:
                return frame
            if url_contains and url_contains in frame.url:
                return frame
        await page.wait_for_timeout(200)
    target = f"name={name}" if name else f"url contains {url_contains}"
    raise RuntimeError(f"Timed out waiting for frame with {target}")


async def _resolve_scope(
    root_page: Any,
    active_page: Any,
    current_scope: Any,
    step: dict[str, Any],
) -> Any:
    scope = str(step.get("scope") or "current")
    if scope == "root_page":
        return root_page
    if scope == "active_page":
        return active_page
    if scope == "current":
        return current_scope
    if scope.startswith("frame:"):
        return await _wait_for_frame(active_page, name=scope.split(":", 1)[1])
    if scope.startswith("root_frame:"):
        return await _wait_for_frame(root_page, name=scope.split(":", 1)[1])
    if scope.startswith("frame_url:"):
        return await _wait_for_frame(active_page, url_contains=scope.split(":", 1)[1])
    if scope.startswith("root_frame_url:"):
        return await _wait_for_frame(root_page, url_contains=scope.split(":", 1)[1])
    return current_scope


async def _infer_click_target_frame(target: Any, step: dict[str, Any]) -> str | None:
    if step.get("type") != "click":
        return None
    selector_type = step.get("selector_type")
    selector_value = step.get("selector_value")
    if not selector_type or not selector_value:
        return None
    try:
        locator = resolve(target, selector_type, selector_value, role_hint="button")
        target_attr = await locator.first.get_attribute("target")
    except Exception:
        return None
    if target_attr and target_attr not in SPECIAL_TARGETS:
        return target_attr
    return None


async def _hydrate_target_frame_from_href(
    frame_host_page: Any,
    execution_target: Any,
    step: dict[str, Any],
    frame_name: str | None,
) -> None:
    if not frame_name or step.get("type") != "click":
        return
    selector_type = step.get("selector_type")
    selector_value = step.get("selector_value")
    if not selector_type or not selector_value:
        return
    try:
        locator = resolve(execution_target, selector_type, selector_value, role_hint="button")
        href = await locator.first.get_attribute("href")
    except Exception:
        href = None
    if not href:
        return
    await frame_host_page.evaluate(
        """({ frameName, href }) => {
          const frame = document.querySelector(`iframe[name="${frameName}"], frame[name="${frameName}"]`);
          if (!frame) return;
          const current = frame.getAttribute("src") || "";
          if (!current || current === "about:blank") {
            frame.setAttribute("src", href);
          }
        }""",
        {"frameName": frame_name, "href": href},
    )
    await frame_host_page.wait_for_timeout(800)


async def _update_scope_after_step(
    context: Any,
    root_page: Any,
    active_page: Any,
    current_scope: Any,
    step: dict[str, Any],
    popup_page: Any = None,
    inferred_frame_name: str | None = None,
) -> tuple[Any, Any]:
    if popup_page is not None:
        active_page = popup_page
        current_scope = popup_page

    if step.get("switch_to_root_page"):
        return root_page, root_page

    frame_name = step.get("switch_to_frame_name") or inferred_frame_name
    frame_url_contains = step.get("switch_to_frame_url_contains")
    if frame_name or frame_url_contains:
        frame_host_page = root_page if step.get("switch_frame_on_root_page", True) else active_page
        current_scope = await _wait_for_frame(
            frame_host_page,
            name=frame_name,
            url_contains=frame_url_contains,
        )
        active_page = frame_host_page

    if step.get("switch_scope_to_active_page"):
        current_scope = active_page

    return active_page, current_scope


async def _can_skip_failed_step(
    target: Any,
    step: dict[str, Any],
    remaining_steps: list[dict[str, Any]],
) -> bool:
    description = str(step.get("description") or "").lower()
    selector_value = str(step.get("selector_value") or "").lower()
    auth_markers = ("account", "google", "otp", "verify otp", "login otp")
    is_auth_transition = any(marker in description or marker in selector_value for marker in auth_markers)
    if not is_auth_transition:
        return False

    auth_page_checks = [
        ("text", "Sign in with Google"),
        ("text", "Login to WebERP"),
        ("text", "Email or phone"),
        ("text", "Choose an account"),
        ("text", "Use another account"),
        ("css", "#userotp1"),
    ]
    for selector_type, selector in auth_page_checks:
        try:
            candidate = resolve(target, selector_type, selector, role_hint="button")
            if await candidate.first.is_visible(timeout=300):
                return False
        except Exception:
            continue

    for future_step in remaining_steps:
        future_type = future_step.get("type")
        if future_type not in {"click", "extract_text", "fill", "press_key"}:
            continue
        future_selector_type = future_step.get("selector_type")
        future_selector_value = future_step.get("selector_value")
        if not future_selector_type or not future_selector_value:
            continue
        try:
            candidate = resolve(target, future_selector_type, future_selector_value, role_hint="button")
            if await candidate.first.is_visible(timeout=500):
                return True
        except Exception:
            continue
    return False


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
    context = None
    profile_dir = os.getenv("FLOW2API_BROWSER_USER_DATA_DIR", "").strip()
    browser_channel = os.getenv("FLOW2API_BROWSER_CHANNEL", "").strip() or None
    browser_executable_path = os.getenv("FLOW2API_BROWSER_EXECUTABLE_PATH", "").strip() or None
    launch_options: dict[str, Any] = {
        "headless": headless,
        "args": ["--headless=new"] if headless else [],
    }
    if browser_channel:
        launch_options["channel"] = browser_channel
    if browser_executable_path:
        launch_options["executable_path"] = browser_executable_path

    async with async_playwright() as playwright:
        try:
            if profile_dir:
                Path(profile_dir).mkdir(parents=True, exist_ok=True)
                context = await playwright.chromium.launch_persistent_context(
                    user_data_dir=profile_dir,
                    viewport={"width": 1280, "height": 900},
                    **launch_options,
                )
                existing_pages = list(context.pages)
                for existing_page in existing_pages:
                    try:
                        await existing_page.close()
                    except Exception:
                        continue
                page = await context.new_page()
            else:
                browser = await playwright.chromium.launch(**launch_options)
                page = await browser.new_page(viewport={"width": 1280, "height": 900})
            page.set_default_timeout(int(os.getenv("FLOW2API_STEP_TIMEOUT_MS", "5000")))
            root_page = page
            active_page = page
            current_scope = page

            steps = resolved_workflow.get("steps", [])
            for index, step in enumerate(steps):
                step_id = str(step.get("id", f"step_{len(logs) + 1}"))
                step_type = str(step.get("type", "unknown"))
                started = time.perf_counter()
                popup_page = None

                try:
                    if _scope_is_closed(active_page):
                        active_page = root_page
                    if _scope_is_closed(current_scope):
                        current_scope = active_page
                    execution_target = await _resolve_scope(root_page, active_page, current_scope, step)
                    inferred_frame_name = await _infer_click_target_frame(execution_target, step)

                    if step.get("switch_to_popup"):
                        async with context.expect_page(timeout=_step_timeout_ms()) as popup_info:
                            await _execute_step(execution_target, step, outputs, execution_id)
                        popup_page = await popup_info.value
                        await popup_page.wait_for_load_state("domcontentloaded")
                    else:
                        await _execute_step(execution_target, step, outputs, execution_id)

                    frame_host_page = root_page if step.get("switch_frame_on_root_page", True) else active_page
                    await _hydrate_target_frame_from_href(
                        frame_host_page,
                        execution_target,
                        step,
                        step.get("switch_to_frame_name") or inferred_frame_name,
                    )

                    active_page, current_scope = await _update_scope_after_step(
                        context,
                        root_page,
                        active_page,
                        current_scope,
                        step,
                        popup_page=popup_page,
                        inferred_frame_name=inferred_frame_name,
                    )
                    screenshot_path = await _safe_screenshot(active_page, execution_id, step_id)
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
                    failure_screenshot = await _safe_screenshot(active_page, execution_id, f"{step_id}_failed")
                    healed_selector = None
                    retried_on_root_page = False
                    if (
                        "Target page, context or browser has been closed" in str(exc)
                        and not _scope_is_closed(root_page)
                        and execution_target is not root_page
                    ):
                        try:
                            execution_target = root_page
                            active_page = root_page
                            current_scope = root_page
                            await _execute_step(execution_target, step, outputs, execution_id)
                            active_page, current_scope = await _update_scope_after_step(
                                context,
                                root_page,
                                active_page,
                                current_scope,
                                step,
                            )
                            screenshot_path = await _safe_screenshot(active_page, execution_id, step_id)
                            duration_ms = int((time.perf_counter() - started) * 1000)
                            logs.append(
                                StepLog(
                                    step_id=step_id,
                                    step_type=step_type,
                                    status="success",
                                    message=f"{step_type} completed after switching back to root page",
                                    screenshot_path=screenshot_path,
                                    duration_ms=duration_ms,
                                )
                            )
                            retried_on_root_page = True
                        except Exception as retry_on_root_exc:
                            exc = retry_on_root_exc

                    if retried_on_root_page:
                        continue
                    if ai_fallback_enabled and step.get("selector_type") and failure_screenshot:
                        healed_selector = await ai_resolve_selector(
                            execution_target if "execution_target" in locals() else active_page,
                            step,
                            failure_screenshot,
                        )

                    if healed_selector:
                        retry_step = deepcopy(step)
                        retry_step["selector_type"] = healed_selector["selector_type"]
                        retry_step["selector_value"] = healed_selector["selector_value"]
                        try:
                            retry_target = await _resolve_scope(root_page, active_page, current_scope, retry_step)
                            inferred_frame_name = await _infer_click_target_frame(retry_target, retry_step)
                            popup_page = None
                            if retry_step.get("switch_to_popup"):
                                async with context.expect_page(timeout=_step_timeout_ms()) as popup_info:
                                    await _execute_step(retry_target, retry_step, outputs, execution_id)
                                popup_page = await popup_info.value
                                await popup_page.wait_for_load_state("domcontentloaded")
                            else:
                                await _execute_step(retry_target, retry_step, outputs, execution_id)
                            frame_host_page = root_page if retry_step.get("switch_frame_on_root_page", True) else active_page
                            await _hydrate_target_frame_from_href(
                                frame_host_page,
                                retry_target,
                                retry_step,
                                retry_step.get("switch_to_frame_name") or inferred_frame_name,
                            )
                            active_page, current_scope = await _update_scope_after_step(
                                context,
                                root_page,
                                active_page,
                                current_scope,
                                retry_step,
                                popup_page=popup_page,
                                inferred_frame_name=inferred_frame_name,
                            )
                            screenshot_path = await _safe_screenshot(active_page, execution_id, step_id)
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

                    if await _can_skip_failed_step(
                        execution_target if "execution_target" in locals() else active_page,
                        step,
                        steps[index + 1 :],
                    ):
                        duration_ms = int((time.perf_counter() - started) * 1000)
                        logs.append(
                            StepLog(
                                step_id=step_id,
                                step_type=step_type,
                                status="skipped",
                                message=f"{step_type} skipped because a later page state is already visible",
                                screenshot_path=failure_screenshot,
                                duration_ms=duration_ms,
                            )
                        )
                        continue

                    duration_ms = int((time.perf_counter() - started) * 1000)
                    screenshot_path = await _safe_screenshot(active_page, execution_id, step_id)
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
            if context is not None:
                await context.close()
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
