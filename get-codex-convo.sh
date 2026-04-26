#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_dir="$script_dir"
converter="${repo_dir}/codex_session_to_markdown.py"
list_script="${repo_dir}/list-codex-convos.sh"
cache_root="${XDG_CACHE_HOME:-${HOME}/.cache}"
output_dir="${cache_root}/codex-convos/convos"
open_browser=0
picker_args=()
input_jsonl=""

if [[ "${1:-}" == "--open" ]]; then
    open_browser=1
    shift
fi

if [[ ! -f "$converter" ]]; then
    echo "Converter script not found: $converter" >&2
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --limit|--days)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for $1" >&2
                exit 1
            fi
            picker_args+=("$1" "$2")
            shift 2
            ;;
        --refresh)
            picker_args+=("$1")
            shift
            ;;
        -*)
            echo "Usage: get-codex-convo.sh [--open] [session.jsonl] [--days N] [--limit N] [--refresh]" >&2
            exit 1
            ;;
        *)
            if [[ -n "$input_jsonl" ]]; then
                echo "Usage: get-codex-convo.sh [--open] [session.jsonl] [--days N] [--limit N] [--refresh]" >&2
                exit 1
            fi
            input_jsonl="$1"
            shift
            ;;
    esac
done

if [[ -z "$input_jsonl" ]]; then
    if [[ ! -x "$list_script" ]]; then
        echo "List script not found or not executable: $list_script" >&2
        exit 1
    fi

    selected_line="$("$list_script" "${picker_args[@]}" | head -n 1)"
    input_jsonl="${selected_line##*$'\t'}"

    if [[ -z "$input_jsonl" ]]; then
        echo "No session .jsonl files found under ${HOME}/.codex/sessions" >&2
        exit 1
    fi
fi

if [[ ! -f "$input_jsonl" ]]; then
    echo "Input file not found: $input_jsonl" >&2
    exit 1
fi

mkdir -p "$output_dir"

output_md="${output_dir}/$(basename "${input_jsonl%.jsonl}").md"

python3 "$converter" "$input_jsonl" -o "$output_md"

if [[ $open_browser -eq 1 ]]; then
    if [[ "$(uname -s)" == "Darwin" ]]; then
        if [[ -d "/Applications/Google Chrome.app" ]] || [[ -d "${HOME}/Applications/Google Chrome.app" ]]; then
            nohup open -a "Google Chrome" "$output_md" >/dev/null 2>&1 &
        elif command -v open >/dev/null 2>&1; then
            nohup open "$output_md" >/dev/null 2>&1 &
        fi
    else
        if command -v google-chrome >/dev/null 2>&1; then
            nohup google-chrome "$output_md" >/dev/null 2>&1 &
        elif command -v google-chrome-stable >/dev/null 2>&1; then
            nohup google-chrome-stable "$output_md" >/dev/null 2>&1 &
        elif command -v xdg-open >/dev/null 2>&1; then
            nohup xdg-open "$output_md" >/dev/null 2>&1 &
        fi
    fi
fi

echo "$output_md"
