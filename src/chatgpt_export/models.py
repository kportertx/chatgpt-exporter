"""Data models for ChatGPT conversations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Message:
    id: str
    role: str  # "user", "assistant", "system", "tool"
    content_type: str  # "text", "multimodal_text", "code", etc.
    parts: list[str | dict]
    model_slug: str | None = None
    create_time: float | None = None

    @property
    def has_content(self) -> bool:
        return any(
            (isinstance(p, str) and p.strip()) or isinstance(p, dict)
            for p in self.parts
        )


@dataclass
class Conversation:
    id: str
    title: str
    create_time: float | None
    update_time: float | None
    messages: list[Message]
    model_slug: str | None = None


@dataclass
class Project:
    id: str  # gizmo ID like "g-xxxxxxxxxxxxxxxx"
    name: str
    conversation_ids: list[str] = field(default_factory=list)
