#!/usr/bin/env bash

set -euo pipefail

default_limit=1000
default_days=14
limit=""
days=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --limit" >&2
                exit 1
            fi
            limit="$2"
            shift 2
            ;;
        --days)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --days" >&2
                exit 1
            fi
            days="$2"
            shift 2
            ;;
        --refresh)
            shift
            ;;
        *)
            echo "Usage: list-codex-convos.sh [--days N] [--limit N] [--refresh]" >&2
            exit 1
            ;;
    esac
done

history_repo="${CODEX_HISTORY_REPO:-${HOME}/Projects/codex-history}"
history_script="${history_repo}/history.py"

if [[ -z "$days" && -z "$limit" ]]; then
    days="$default_days"
    limit="$default_limit"
fi

if [[ -f "$history_script" ]]; then
    args=(list)
    if [[ -n "$days" ]]; then
        args+=(--days "$days")
    fi
    if [[ -n "$limit" ]]; then
        args+=(--limit "$limit")
    fi
    exec python3 "$history_script" "${args[@]}"
fi

sessions_root="${HOME}/.codex/sessions"

python3 - "$sessions_root" "$limit" "$days" <<'PY'
import json
import re
import sys
from datetime import datetime, timedelta, timezone
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
limit_arg = sys.argv[2]
days_arg = sys.argv[3]
limit = int(limit_arg) if limit_arg else None
cutoff = None
if days_arg:
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(days_arg))

count = 0
for path in sorted(sessions_root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
    if cutoff is not None:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            continue

    print(f"{label_for(path)}\t{path}")
    count += 1
    if limit is not None and count >= limit:
        break
PY
