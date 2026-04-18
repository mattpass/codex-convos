# Codex Convos

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
- `fzf` if you want the interactive `getcc` selector function

## OS Compatibility

The scripts are intended to work on both Linux and macOS.

- `--open` prefers Google Chrome on both platforms and falls back to the platform default opener if Chrome is unavailable
- the `getcc` shell helper below is written to work in `zsh` as well as `bash`


## Basic Usage - Shell Integration

Add this to your shell config, for example `~/.bashrc` or `~/.zshrc` and change `~/Projects/codex-convos` as needed:

```bash
function getcc() {
    local repo=~/Projects/codex-convos
    local selected
    local convo_path

    selected="$("$repo/list-codex-convos.sh" | fzf --ansi --no-sort --layout=reverse-list --delimiter=$'\t' --with-nth=1)" || return 1
    [[ -n "$selected" ]] || return 1

    convo_path="${selected##*$'\t'}"
    "$repo/get-codex-convo.sh" --open "$convo_path"
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

The `fzf` list is newest-first, with the newest session at the top and initially selected. The orange timestamp shown is the session file's modified time, so the displayed order matches the sort order. Each entry is shown like:

```text
12th Apr @ 14:59:32 : When I do this and that...
```

## Basic Usage - Individual Files

Convert a specific session file:

```bash
~/Projects/codex-convos/get-codex-convo.sh \
  ~/.codex/sessions/2026/04/11/<filename>..jsonl
```

Export the newest available session file:

```bash
~/Projects/codex-convos/get-codex-convo.sh
```

Export a session and open the generated Markdown in Chrome:

```bash
~/Projects/codex-convos/get-codex-convo.sh --open \
  ~/.codex/sessions/2026/04/11/<filename>..jsonl
```

List the 10 newest session files with a readable label and the underlying path:

```bash
~/Projects/codex-convos/list-codex-convos.sh
```

If you want direct control of the underlying Python converter, it still works:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/<filename>..jsonl \
  -o ~/Projects/codex-convos/convos/session.md
```

You can also skip command history and export only the conversation:

```bash
python3 ~/Projects/codex-convos/codex_session_to_markdown.py \
  ~/.codex/sessions/2026/04/11/<filename>.jsonl \
  --skip-commands \
  -o ~/Projects/codex-convos/convos/session.md
```

