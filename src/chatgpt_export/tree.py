"""Flatten a ChatGPT conversation mapping tree into an ordered message list."""

from __future__ import annotations

from chatgpt_export.models import Message


def flatten_conversation(mapping: dict) -> list[Message]:
    """Walk the mapping tree from root to leaf, always following the last child.

    The "last child" heuristic follows the most recently active branch,
    matching ChatGPT's own UI behavior.
    """
    if not mapping:
        return []

    # Find root: node whose parent is None or not in mapping
    root_id = _find_root(mapping)
    if root_id is None:
        return []

    messages: list[Message] = []
    current_id: str | None = root_id

    while current_id is not None:
        node = mapping[current_id]
        msg_data = node.get("message")
        if msg_data and _is_visible_message(msg_data):
            messages.append(_parse_message(current_id, msg_data))

        children = node.get("children", [])
        current_id = children[-1] if children else None

    return messages


def _find_root(mapping: dict) -> str | None:
    """Find the root node (parent is None or parent not in mapping)."""
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent is None or parent not in mapping:
            return node_id
    return None


def _is_visible_message(msg: dict) -> bool:
    """Filter out system scaffolding, empty messages, and tool internals."""
    role = msg.get("author", {}).get("role", "")
    if role == "system":
        return False

    content = msg.get("content", {})
    parts = content.get("parts", [])

    if not parts:
        return False

    # Check if any part has actual content
    for part in parts:
        if isinstance(part, str) and part.strip():
            return True
        if isinstance(part, dict):
            return True

    return False


def _parse_message(node_id: str, msg: dict) -> Message:
    """Parse a raw message dict into a Message object."""
    author = msg.get("author", {})
    content = msg.get("content", {})
    metadata = msg.get("metadata", {})

    parts: list[str | dict] = []
    for part in content.get("parts", []):
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict):
            parts.append(part)

    return Message(
        id=node_id,
        role=author.get("role", "unknown"),
        content_type=content.get("content_type", "text"),
        parts=parts,
        model_slug=metadata.get("model_slug"),
        create_time=msg.get("create_time"),
    )
