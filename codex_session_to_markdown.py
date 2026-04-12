#!/usr/bin/env python3
"""Convert a Codex session JSONL archive into readable Markdown."""

from __future__ import annotations

import argparse
import html
import json
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Entry:
    timestamp: str
    kind: str
    title: str
    body: str
    meta: dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Codex session JSONL file into Markdown."
    )
    parser.add_argument("session_file", type=Path, help="Path to a Codex session .jsonl file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write Markdown to this file instead of stdout",
    )
    parser.add_argument(
        "--skip-commands",
        action="store_true",
        help="Only include user/assistant conversation",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON on line {line_number}: {exc}") from exc
    return rows


def format_ts(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return raw
    return dt.isoformat(sep=" ", timespec="seconds")


def format_command(command: Any) -> str:
    if isinstance(command, list):
        return shlex.join(str(part) for part in command)
    if isinstance(command, str):
        return command
    return repr(command)


def make_fence(text: str, info: str = "") -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    header = fence + info if info else fence
    return f"{header}\n{text.rstrip()}\n{fence}"


def extract_shell_inner(command_text: str) -> str:
    shell_prefix = "/bin/bash -lc "
    if command_text.startswith(shell_prefix):
        quoted = command_text[len(shell_prefix) :]
        try:
            parts = shlex.split(quoted)
            if parts:
                return parts[0]
        except ValueError:
            return quoted
    return command_text


def extract_command_names(command_text: str) -> list[str]:
    inner = extract_shell_inner(command_text).strip()
    if not inner:
        return []

    lexer = shlex.shlex(inner, posix=True, punctuation_chars="|;&")
    lexer.whitespace_split = True
    lexer.commenters = ""
    tokens = list(lexer)

    segments: list[list[str]] = [[]]
    separators = {"|", "||", ";", "&&"}

    for token in tokens:
        if token in separators:
            if segments[-1]:
                segments.append([])
            continue
        segments[-1].append(token)

    names: list[str] = []

    for segment in segments:
        if not segment:
            continue

        for token in segment:
            if "=" in token and not token.startswith(("/", "./")) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
                continue
            if token in {"sudo", "env", "command", "builtin", "nohup", "time"}:
                continue
            names.append(Path(token).name)
            break

    deduped: list[str] = []
    seen: set[str] = set()
    for name in names:
        if name not in seen:
            deduped.append(name)
            seen.add(name)
    return deduped


def is_collapsible_low_signal_command(command_text: str) -> bool:
    inner = extract_shell_inner(command_text).strip()
    if not inner:
        return False

    command_names = extract_command_names(command_text)
    if not command_names:
        return False

    allowed = {"sed", "cat", "head", "tail", "rg", "find", "ls", "pwd", "nl", "sort"}
    if all(name in allowed for name in command_names):
        return True

    patterns = (
        r"^sed\s+-n\s+['\"]?\d",
        r"^cat\s+",
        r"^head\s+",
        r"^tail\s+",
        r"^rg\s+--files(?:\s|$)",
        r"^find\s+",
        r"^ls(?:\s|$)",
        r"^pwd(?:\s|$)",
        r"^nl\s+",
    )
    return any(re.match(pattern, inner) for pattern in patterns)


def render_message_body(entry: Entry) -> str:
    if not entry.body:
        return "_Empty message_"

    if entry.title == "🙂 Matt":
        escaped = html.escape(entry.body)
        return f'<div style="color: #06c; white-space: pre-wrap;">{escaped}</div>'

    if entry.title == "🤖 Codex":
        escaped = html.escape(entry.body)
        return f'<div style="color: #c90; white-space: pre-wrap;">{escaped}</div>'

    return entry.body


def render_command_heading(title: str, command_names: list[str]) -> str:
    if not command_names:
        return f"### {title}"

    rendered_names = ", ".join(
        f'<span style="color: #c90;">{html.escape(name)}</span>' for name in command_names
    )
    return f"### {title} [{rendered_names}]"


def build_entries(rows: list[dict[str, Any]], skip_commands: bool) -> tuple[dict[str, Any], list[Entry]]:
    session_meta: dict[str, Any] = {}
    entries: list[Entry] = []

    for row in rows:
        row_type = row.get("type")
        payload = row.get("payload") or {}
        timestamp = row.get("timestamp", "")
        payload_type = payload.get("type")

        if row_type == "session_meta":
            session_meta = payload
            continue

        if row_type == "event_msg" and payload_type == "user_message":
            entries.append(
                Entry(
                    timestamp=timestamp,
                    kind="message",
                    title="🙂 Matt",
                    body=payload.get("message", "").strip(),
                    meta={},
                )
            )
            continue

        if row_type == "event_msg" and payload_type == "agent_message":
            entries.append(
                Entry(
                    timestamp=timestamp,
                    kind="message",
                    title="🤖 Codex",
                    body=payload.get("message", "").strip(),
                    meta={"phase": payload.get("phase")},
                )
            )
            continue

        if skip_commands:
            continue

        if row_type == "event_msg" and payload_type == "exec_command_end":
            command_text = format_command(payload.get("command"))
            output = payload.get("aggregated_output") or ""
            command_names = extract_command_names(command_text)
            meta = {
                "cwd": payload.get("cwd"),
                "command_names": command_names,
                "exit_code": payload.get("exit_code"),
                "status": payload.get("status"),
            }
            entries.append(
                Entry(
                    timestamp=timestamp,
                    kind="command",
                    title="Command",
                    body=command_text,
                    meta={**meta, "output": output},
                )
            )
            continue

        if row_type == "response_item" and payload_type == "message":
            if payload.get("role") not in {"user", "assistant"}:
                continue

            # Prefer event_msg conversation items to avoid duplicates.
            continue

    return session_meta, entries


def render_markdown(
    source_file: Path,
    session_meta: dict[str, Any],
    entries: list[Entry],
) -> str:
    lines: list[str] = []
    lines.append("# Codex Session Export")
    lines.append("")
    lines.append(f"- Source: `{source_file}`")

    session_id = session_meta.get("id")
    if session_id:
        lines.append(f"- Session ID: `{session_id}`")

    started = format_ts(session_meta.get("timestamp"))
    if started:
        lines.append(f"- Started: `{started}`")

    cwd = session_meta.get("cwd")
    if cwd:
        lines.append(f"- CWD: `{cwd}`")

    cli_version = session_meta.get("cli_version")
    if cli_version:
        lines.append(f"- Codex CLI: `{cli_version}`")

    lines.append("")
    lines.append("## Timeline")
    lines.append("")

    if not entries:
        lines.append("_No transcript entries found._")
        return "\n".join(lines) + "\n"

    for entry in entries:
        if entry.kind == "command":
            command_names = entry.meta.get("command_names") or []
            prefix = "🔍 Command" if is_collapsible_low_signal_command(entry.body) else "✏️ Command"
            lines.append(render_command_heading(prefix, command_names))
        else:
            lines.append(f"### {entry.title}")
        lines.append("")

        ts = format_ts(entry.timestamp)
        if ts:
            lines.append(f"_{ts}_")
            lines.append("")

        if entry.kind == "message":
            lines.append(render_message_body(entry))
            lines.append("")
            continue

        if entry.kind == "command":
            command_lines: list[str] = []
            command_lines.append(make_fence(entry.body, "bash"))
            command_lines.append("")

            cwd = entry.meta.get("cwd")
            status = entry.meta.get("status")
            exit_code = entry.meta.get("exit_code")
            if cwd:
                command_lines.append(f"- CWD: `{cwd}`")
            command_lines.append(f"- Status: `{status}`")
            command_lines.append(f"- Exit code: `{exit_code}`")
            command_lines.append("")

            output = entry.meta.get("output", "")
            if output.strip():
                command_lines.append("Output:")
                command_lines.append(make_fence(output, "text"))
            else:
                command_lines.append("Output: `_none_`")
            command_lines.append("")

            if is_collapsible_low_signal_command(entry.body):
                lines.append("<details>")
                lines.append("<summary>Low-signal read/discovery command</summary>")
                lines.append("")
                lines.extend(command_lines)
                lines.append("</details>")
                lines.append("")
            else:
                lines.extend(command_lines)

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    rows = load_jsonl(args.session_file)
    session_meta, entries = build_entries(rows, skip_commands=args.skip_commands)
    markdown = render_markdown(args.session_file, session_meta, entries)

    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
