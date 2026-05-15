from __future__ import annotations

from playwright.async_api import Locator, Page

from .exceptions import SelectorResolutionError


def resolve(
    page: Page,
    selector_type: str,
    selector_value: str,
    role_hint: str | None = None,
) -> Locator:
    if selector_type == "label":
        return page.get_by_label(selector_value)
    if selector_type == "role":
        return page.get_by_role(role_hint or "button", name=selector_value)
    if selector_type == "text":
        return page.get_by_text(selector_value)
    if selector_type == "test_id":
        return page.get_by_test_id(selector_value)
    if selector_type == "css":
        return page.locator(selector_value)
    if selector_type == "placeholder":
        return page.get_by_placeholder(selector_value)

    raise SelectorResolutionError(f"Unsupported selector_type: {selector_type}")

