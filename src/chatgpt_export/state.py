"""Export state persistence for resume capability."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ExportState:
    exported_ids: set[str] = field(default_factory=set)
    root_offset: int = 0
    project_cursors: dict[str, int] = field(default_factory=dict)
    started_at: str = ""
    last_updated: str = ""

    @classmethod
    def load(cls, path: Path) -> ExportState:
        """Load state from a JSON file, or return a fresh state."""
        if not path.exists():
            return cls._new()

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            state = cls(
                exported_ids=set(data.get("exported_ids", [])),
                root_offset=data.get("root_offset", 0),
                project_cursors=data.get("project_cursors", {}),
                started_at=data.get("started_at", ""),
                last_updated=data.get("last_updated", ""),
            )
            return state
        except (json.JSONDecodeError, KeyError):
            print("  Warning: corrupt state file, starting fresh.")
            return cls._new()

    @classmethod
    def _new(cls) -> ExportState:
        now = _now_iso()
        return cls(started_at=now, last_updated=now)

    def save(self, path: Path) -> None:
        """Save state to a JSON file."""
        self.last_updated = _now_iso()
        data = {
            "exported_ids": sorted(self.exported_ids),
            "root_offset": self.root_offset,
            "project_cursors": self.project_cursors,
            "started_at": self.started_at,
            "last_updated": self.last_updated,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def mark_exported(self, conversation_id: str) -> None:
        self.exported_ids.add(conversation_id)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
