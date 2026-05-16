from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: estimate_speaking_time.py <text-file>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    text = path.read_text()
    words = [word for word in text.split() if word.strip()]
    count = len(words)

    for wpm in (130, 140, 150):
        minutes = count / wpm
        seconds = round(minutes * 60)
        print(f"{wpm} wpm: {seconds}s")

    print(f"word_count: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
