from __future__ import annotations

from pathlib import Path
from typing import Any, Awaitable, Callable

from playwright.async_api import Page

from .exceptions import UnsupportedStepError
from .selector_resolver import resolve

StepHandler = Callable[[Page, dict[str, Any], dict[str, Any], str], Awaitable[None]]


async def handle_navigate(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    await page.goto(step["url"], wait_until="domcontentloaded")


async def handle_fill(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    locator = resolve(page, step["selector_type"], step["selector_value"])
    await locator.fill(str(step.get("value", "")))


async def handle_click(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    locator = resolve(page, step["selector_type"], step["selector_value"], role_hint="button")
    await locator.click()


async def handle_select(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    locator = resolve(page, step["selector_type"], step["selector_value"])
    await locator.select_option(str(step["option_value"]))


async def handle_wait(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    await page.wait_for_timeout(int(step.get("duration_ms", 1000)))


async def handle_extract_text(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    locator = resolve(page, step["selector_type"], step["selector_value"])
    outputs[step["output_key"]] = (await locator.inner_text()).strip()


async def handle_extract_table(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    locator = resolve(page, step["selector_type"], step["selector_value"])
    rows = await locator.evaluate(
        """(table) => {
          const text = (node) => (node.textContent || '').trim();
          const headerCells = Array.from(table.querySelectorAll('thead th'));
          const headers = headerCells.length
            ? headerCells.map(text)
            : Array.from(table.querySelectorAll('tr:first-child th, tr:first-child td')).map(text);
          const bodyRows = Array.from(table.querySelectorAll('tbody tr'));
          const sourceRows = bodyRows.length ? bodyRows : Array.from(table.querySelectorAll('tr')).slice(1);
          return sourceRows.map((row) => {
            const cells = Array.from(row.querySelectorAll('td'));
            const record = {};
            cells.forEach((cell, index) => {
              record[headers[index] || `column_${index + 1}`] = text(cell);
            });
            return record;
          });
        }"""
    )
    outputs[step["output_key"]] = rows


async def handle_download_file(
    page: Page,
    step: dict[str, Any],
    outputs: dict[str, Any],
    execution_id: str,
) -> None:
    locator = resolve(page, step["selector_type"], step["selector_value"], role_hint="button")
    download_dir = Path("storage/downloads") / execution_id
    download_dir.mkdir(parents=True, exist_ok=True)
    async with page.expect_download() as download_info:
        await locator.click()
    download = await download_info.value
    filename = download.suggested_filename or f"{step['output_key']}.download"
    target = download_dir / filename
    await download.save_as(str(target))
    outputs[step["output_key"]] = str(target)


HANDLERS: dict[str, StepHandler] = {
    "navigate": handle_navigate,
    "fill": handle_fill,
    "click": handle_click,
    "select": handle_select,
    "wait": handle_wait,
    "extract_text": handle_extract_text,
    "extract_table": handle_extract_table,
    "download_file": handle_download_file,
}


def get_handler(step_type: str) -> StepHandler:
    handler = HANDLERS.get(step_type)
    if handler is None:
        raise UnsupportedStepError(f"Unsupported step type: {step_type}")
    return handler
