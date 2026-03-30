"""Render conversations as markdown."""

from __future__ import annotations

import re
from datetime import datetime, timezone

from chatgpt_export.models import Conversation, Message


def render_conversation(conv: Conversation) -> str:
    """Render a full conversation as a markdown string with YAML frontmatter."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f'title: "{_escape_yaml(conv.title)}"')
    if conv.create_time:
        lines.append(f"date: {_format_timestamp(conv.create_time)}")
    if conv.update_time:
        lines.append(f"updated: {_format_timestamp(conv.update_time)}")
    if conv.model_slug:
        lines.append(f"model: {conv.model_slug}")
    lines.append(f"conversation_id: {conv.id}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {conv.title}")
    lines.append("")

    for msg in conv.messages:
        role_label = _role_label(msg.role)
        lines.append(f"## {role_label}")
        lines.append("")
        lines.extend(_render_parts(msg))
        lines.append("")

    return "\n".join(lines)


def safe_filename(title: str, conversation_id: str) -> str:
    """Create a safe filename from a conversation title."""
    clean = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "-", title).strip()
    clean = re.sub(r"-{2,}", "-", clean)
    clean = clean.strip("-. ")
    if not clean:
        clean = "Untitled"
    clean = clean[:200]
    short_hash = conversation_id[:8]
    return f"{clean} [{short_hash}].md"


def safe_dirname(name: str) -> str:
    """Create a safe directory name from a project name."""
    clean = re.sub(r'[\\/:*?"<>|\x00-\x1f]', "-", name).strip()
    clean = re.sub(r"-{2,}", "-", clean)
    clean = clean.strip("-. ")
    return clean or "Unnamed Project"


def _role_label(role: str) -> str:
    labels = {
        "user": "User",
        "assistant": "Assistant",
        "tool": "Tool",
    }
    return labels.get(role, role.capitalize())


def _render_parts(msg: Message) -> list[str]:
    """Render message parts to markdown lines."""
    lines: list[str] = []

    for part in msg.parts:
        if isinstance(part, str):
            lines.append(part)
        elif isinstance(part, dict):
            lines.extend(_render_structured_part(part))

    return lines


def _render_structured_part(part: dict) -> list[str]:
    """Render a structured (dict) content part."""
    content_type = part.get("content_type", "")

    if content_type == "image_asset_pointer":
        metadata = part.get("metadata") or {}
        dalle = metadata.get("dalle") or {}
        prompt = dalle.get("prompt", "image")
        return [f"![{prompt}](generated-image)", ""]

    if content_type == "tether_browsing_display":
        result = part.get("result", "")
        return [f"> {result}", ""] if result else []

    if content_type == "tether_quote":
        title = part.get("title", "")
        text = part.get("text", "")
        url = part.get("url", "")
        lines = []
        if title:
            lines.append(f"> **{title}**")
        if text:
            for line in text.splitlines():
                lines.append(f"> {line}")
        if url:
            lines.append(f"> Source: {url}")
        lines.append("")
        return lines

    # Fallback: render as JSON code block
    import json

    return [f"```json", json.dumps(part, indent=2), "```", ""]


def _escape_yaml(s: str) -> str:
    """Escape a string for use in YAML double-quoted value."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _format_timestamp(ts: float) -> str:
    """Format a Unix timestamp as ISO 8601."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
