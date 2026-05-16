from __future__ import annotations

import shutil
import os
from pathlib import Path


SOURCE_ROOT = Path("/Users/kartik/Library/Application Support/Arc/User Data")
SOURCE_PROFILE_NAME = os.getenv("FLOW2API_ARC_SOURCE_PROFILE", "Default")
SOURCE_PROFILE = SOURCE_ROOT / SOURCE_PROFILE_NAME
TARGET_ROOT = Path(os.getenv("FLOW2API_ARC_TARGET_ROOT", "storage/browser_profiles/arc_default"))
TARGET_PROFILE = TARGET_ROOT / "Default"

COPY_NAMES = [
    "Cookies",
    "Login Data",
    "Login Data For Account",
    "Account Web Data",
    "Preferences",
    "Web Data",
    "History",
    "Sessions",
    "Local Storage",
    "Session Storage",
    "Service Worker",
]


def copy_item(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> None:
    if not SOURCE_PROFILE.exists():
        raise FileNotFoundError(f"Arc profile not found: {SOURCE_PROFILE}")

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    local_state = SOURCE_ROOT / "Local State"
    if local_state.exists():
        copy_item(local_state, TARGET_ROOT / "Local State")

    TARGET_PROFILE.mkdir(parents=True, exist_ok=True)
    for name in COPY_NAMES:
        source = SOURCE_PROFILE / name
        if source.exists():
            copy_item(source, TARGET_PROFILE / name)
            print(f"copied {name}")

    print(f"prepared Arc profile from {SOURCE_PROFILE_NAME} at {TARGET_ROOT.resolve()}")


if __name__ == "__main__":
    main()
