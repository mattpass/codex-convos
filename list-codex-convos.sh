#!/usr/bin/env bash

set -euo pipefail

sessions_root="${HOME}/.codex/sessions"

python3 - "$sessions_root" <<'PY'
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ORANGE = "\033[38;5;208m"
GREY = "\033[38;5;244m"
RESET = "\033[0m"


def ordinal(n: int) -> str:
    if 10 <= (n % 100) <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def label_for(path: Path) -> str:
    first_prompt = ""

    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                obj = json.loads(line)
                payload = obj.get("payload") or {}
                if obj.get("type") == "event_msg" and payload.get("type") == "user_message":
                    first_prompt = payload.get("message", "")
                    break
    except (OSError, json.JSONDecodeError):
        return path.name

    dt = datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    date_part = f"{ordinal(dt.day)} {dt.strftime('%b')} @ {dt.strftime('%H:%M:%S')}"

    prompt = re.sub(r"\s+", " ", first_prompt).strip()
    if len(prompt) > 140:
        prompt = prompt[:137].rstrip() + "..."

    if prompt:
        return f"{ORANGE}{date_part}{RESET}{GREY} : {RESET}{prompt}"
    return f"{ORANGE}{date_part}{RESET}"


sessions_root = Path(sys.argv[1]).expanduser()
paths = sorted(sessions_root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]

for path in paths:
    print(f"{label_for(path)}\t{path}")
PY
