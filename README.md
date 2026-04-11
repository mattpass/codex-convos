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
- `list-codex-convos.sh`: prints the 10 most recent Codex session `.jsonl` files
- `get-codex-convo.sh`: exports a chosen session, or the newest one by default
- `convos/`: default output directory for generated Markdown transcripts

## Requirements

- Python 3
- Codex CLI sessions already present under `~/.codex/sessions`

## Basic Usage

Convert a specific session file:

```bash
~/Projects/codex-convos/get-codex-convo.sh \
  ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl
```

Export the newest available session file:

```bash
~/Projects/codex-convos/get-codex-convo.sh
```

List the 10 newest session files:

```bash
~/Projects/codex-convos/list-codex-convos.sh
```

If you want direct control of the underlying Python converter, it still works:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl \
  -o ~/Projects/codex-convos/convos/session.md
```

You can also skip command history and export only the conversation:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/rollout-2026-04-11T21-23-11-019d7e36-73aa-7ab1-8853-c88e394d4d13.jsonl \
  --skip-commands \
  -o ~/Projects/codex-convos/convos/session.md
```

## Shell Integration

Add this to your shell config, for example `~/.bashrc`:

```bash
function getcc() {
    local repo=~/Projects/codex-convos
    local selected

    selected="$("$repo/list-codex-convos.sh" | fzf)" || return 1
    [[ -n "$selected" ]] || return 1

    "$repo/get-codex-convo.sh" "$selected"
}
```

After reloading your shell:

```bash
getcc
```

That shows the 10 most recent session files in `fzf`, lets you choose one, then exports it to:

```text
~/Projects/codex-convos/convos/<same-session-name>.md
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
