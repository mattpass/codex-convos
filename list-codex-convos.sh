#!/usr/bin/env bash

set -euo pipefail

sessions_root="${HOME}/.codex/sessions"

find "$sessions_root" -type f -name '*.jsonl' -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr \
    | head -n 10 \
    | cut -d' ' -f2-
