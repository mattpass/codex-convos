# codexconvos

Convert local Codex session archives from `~/.codex/sessions` into readable Markdown transcripts.

The converter reads a Codex `.jsonl` session file and renders:

- user messages
- assistant messages
- shell commands run
- command status, exit code, and captured output

This is useful when you want a readable record of a Codex session after restarting your machine, resuming a session, or closing the TUI.

## Repository Layout

- `codex_session_to_markdown.py`: converts one Codex session `.jsonl` file into Markdown
- `convos/`: default output directory for generated Markdown transcripts

## Requirements

- Python 3
- Codex CLI sessions already present under `~/.codex/sessions`

## Basic Usage

Convert a specific session file:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl \
  -o ~/Projects/codex-convos/convos/session.md
```

Print the Markdown to stdout instead of writing a file:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl
```

Skip command history and only export the conversation:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl \
  --skip-commands \
  -o ~/Projects/codex-convos/convos/session.md
```

## Shell Function

Add this to your shell config, for example `~/.bashrc`:

```bash
function getcodexconvo() {
    local converter=~/Projects/codex-convos/codex_session_to_markdown.py
    local sessions_root=~/.codex/sessions
    local output_dir=~/Projects/codex-convos/convos
    local input_jsonl
    local output_md
    local latest

    if [[ ! -f "$converter" ]]; then
        echo "Converter script not found: $converter" >&2
        return 1
    fi

    if [[ $# -gt 1 ]]; then
        echo "Usage: getcodexconvo [session.jsonl]" >&2
        return 1
    fi

    if [[ $# -eq 1 ]]; then
        input_jsonl="$1"
    else
        latest=$(
            find "$sessions_root" -type f -name '*.jsonl' -printf '%T@ %p\n' 2>/dev/null \
            | sort -nr \
            | head -n1 \
            | cut -d' ' -f2-
        )

        if [[ -z "$latest" ]]; then
            echo "No session .jsonl files found under $sessions_root" >&2
            return 1
        fi

        input_jsonl="$latest"
    fi

    if [[ ! -f "$input_jsonl" ]]; then
        echo "Input file not found: $input_jsonl" >&2
        return 1
    fi

    mkdir -p "$output_dir" || return 1

    output_md="$output_dir/$(basename "${input_jsonl%.jsonl}").md"

    python3 "$converter" "$input_jsonl" -o "$output_md" || return 1

    echo "$output_md"
}
```

After reloading your shell:

```bash
getcodexconvo
```

That exports the newest session under `~/.codex/sessions` to:

```text
~/Projects/codex-convos/convos/<same-session-name>.md
```

You can also pass a specific `.jsonl` file:

```bash
getcodexconvo ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl
```

To list the 10 most recent Codex session files, add this function as well:

```bash
function listcodexconvos() {
    local sessions_root=~/.codex/sessions

    find "$sessions_root" -type f -name '*.jsonl' -printf '%T@ %p\n' 2>/dev/null \
        | sort -nr \
        | head -n 10 \
        | cut -d' ' -f2-
}
```

Usage:

```bash
listcodexconvos
```

## Git Setup

Initialize and connect the repo:

```bash
cd ~/Projects/codex-convos
git remote add origin git@github.com:mattpass/codexconvos.git
```

Then commit and push:

```bash
git add .
git commit -m "Initial codex session exporter"
git push -u origin main
```

If your default branch is still `master`, rename it first:

```bash
git branch -M main
```
