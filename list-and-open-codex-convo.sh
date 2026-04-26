#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
list_script="${script_dir}/list-codex-convos.sh"
get_script="${script_dir}/get-codex-convo.sh"

if [[ ! -x "$list_script" ]]; then
    echo "List script not found or not executable: $list_script" >&2
    exit 1
fi

if [[ ! -x "$get_script" ]]; then
    echo "Get script not found or not executable: $get_script" >&2
    exit 1
fi

if ! command -v fzf >/dev/null 2>&1; then
    echo "fzf is required for interactive session selection" >&2
    exit 1
fi

selected="$("$list_script" "$@" | fzf --ansi --no-sort --layout=reverse-list --delimiter=$'\t' --with-nth=1)" || exit 1
[[ -n "$selected" ]] || exit 1

convo_path="${selected##*$'\t'}"
exec "$get_script" --open "$convo_path"
