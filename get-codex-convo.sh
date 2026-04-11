#!/usr/bin/env bash

set -euo pipefail

repo_dir="${HOME}/Projects/codex-convos"
converter="${repo_dir}/codex_session_to_markdown.py"
list_script="${repo_dir}/list-codex-convos.sh"
output_dir="${repo_dir}/convos"

if [[ ! -f "$converter" ]]; then
    echo "Converter script not found: $converter" >&2
    exit 1
fi

if [[ $# -gt 1 ]]; then
    echo "Usage: get-codex-convo.sh [session.jsonl]" >&2
    exit 1
fi

if [[ $# -eq 1 ]]; then
    input_jsonl="$1"
else
    if [[ ! -x "$list_script" ]]; then
        echo "List script not found or not executable: $list_script" >&2
        exit 1
    fi

    input_jsonl="$("$list_script" | head -n 1)"

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

echo "$output_md"
