#!/usr/bin/env python3
"""Convert a Codex session JSONL archive into readable Markdown."""

from __future__ import annotations

import argparse
import html
import json
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


def render_message_body(entry: Entry) -> str:
    if not entry.body:
        return "_Empty message_"

    if entry.title == "🙂 Matt":
        escaped = html.escape(entry.body)
        return f'<div style="color: #06c; white-space: pre-wrap;">{escaped}</div>'

    return entry.body


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
            meta = {
                "cwd": payload.get("cwd"),
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
            lines.append(make_fence(entry.body, "bash"))
            lines.append("")

            cwd = entry.meta.get("cwd")
            status = entry.meta.get("status")
            exit_code = entry.meta.get("exit_code")
            if cwd:
                lines.append(f"- CWD: `{cwd}`")
            lines.append(f"- Status: `{status}`")
            lines.append(f"- Exit code: `{exit_code}`")
            lines.append("")

            output = entry.meta.get("output", "")
            if output.strip():
                lines.append("Output:")
                lines.append(make_fence(output, "text"))
            else:
                lines.append("Output: `_none_`")
            lines.append("")

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
