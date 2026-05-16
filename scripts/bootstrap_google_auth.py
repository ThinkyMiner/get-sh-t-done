from __future__ import annotations

import asyncio
import os

from playwright.async_api import async_playwright


LOGIN_URL = "http://indiamart.savvyhrms.in/SavvyHRMS/LoginPage.aspx"


async def main() -> None:
    profile_dir = os.getenv(
        "FLOW2API_BROWSER_USER_DATA_DIR",
        "storage/browser_profiles/chrome_default",
    )
    browser_channel = os.getenv("FLOW2API_BROWSER_CHANNEL", "chrome")
    browser_executable_path = os.getenv("FLOW2API_BROWSER_EXECUTABLE_PATH", "").strip() or None

    print(f"Using persistent profile: {profile_dir}")
    print("A browser window will open. Complete Google sign-in there if needed.")
    print("After you confirm the HRMS dashboard is reachable, press Enter here to close the bootstrap browser.")

    async with async_playwright() as playwright:
        launch_options = {
            "user_data_dir": profile_dir,
            "headless": False,
            "viewport": {"width": 1280, "height": 900},
        }
        if browser_executable_path:
            launch_options["executable_path"] = browser_executable_path
        elif browser_channel:
            launch_options["channel"] = browser_channel

        context = await playwright.chromium.launch_persistent_context(**launch_options)
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto(LOGIN_URL, wait_until="domcontentloaded")
        await page.get_by_text("Login With Google").click()
        await asyncio.to_thread(input)
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
