"""Main export orchestration: fetch conversations and write markdown files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from chatgpt_export.client import APIClient, APIError, FatalAPIError
from chatgpt_export.markdown import render_conversation, safe_dirname, safe_filename
from chatgpt_export.models import Conversation
from chatgpt_export.state import ExportState
from chatgpt_export.tree import flatten_conversation


@dataclass
class ExportConfig:
    output_dir: str
    skip_projects: bool = False
    skip_root: bool = False


def export_all(client: APIClient, config: ExportConfig) -> None:
    """Export all conversations (projects + root) to markdown files."""
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / ".export-state.json"
    state = ExportState.load(state_path)

    total_exported = len(state.exported_ids)
    total_skipped = 0

    # Phase 1: Export project conversations
    if not config.skip_projects:
        try:
            projects = client.list_projects()
        except APIError as e:
            print(f"Warning: could not list projects: {e}")
            projects = []

        print(f"Found {len(projects)} project(s).")

        for i, proj_data in enumerate(projects, 1):
            gizmo = proj_data.get("gizmo", proj_data)
            gizmo_id = gizmo.get("id", "")
            proj_name = gizmo.get("display", {}).get("name", "Unnamed Project")
            project_dir = output_dir / safe_dirname(proj_name)
            project_dir.mkdir(parents=True, exist_ok=True)

            print(f"\nProject ({i}/{len(projects)}): {proj_name}")

            cursor = state.project_cursors.get(gizmo_id, 0)
            page_num = 0

            while True:
                try:
                    page = client.list_project_conversations(gizmo_id, cursor)
                except APIError as e:
                    print(f"  Error listing project conversations: {e}")
                    break

                items = page.get("items", [])
                if not items:
                    break

                for conv_summary in items:
                    conv_id = conv_summary.get("id", "")
                    if conv_id in state.exported_ids:
                        total_skipped += 1
                        continue

                    exported = _export_one(client, conv_id, project_dir)
                    if exported:
                        state.mark_exported(conv_id)
                        total_exported += 1
                        print(f"  [{total_exported}] {exported}")

                cursor = page.get("cursor")
                state.project_cursors[gizmo_id] = cursor if cursor else 0
                state.save(state_path)

                if not page.get("has_more") and cursor is None:
                    break
                if cursor is None:
                    break
                page_num += 1

    # Phase 2: Export root conversations
    if not config.skip_root:
        root_dir = output_dir / "_root"
        root_dir.mkdir(parents=True, exist_ok=True)

        print("\nExporting root conversations...")
        offset = state.root_offset

        while True:
            try:
                page = client.list_conversations(offset=offset)
            except FatalAPIError:
                raise
            except APIError as e:
                print(f"  Error listing conversations: {e}")
                break

            items = page.get("items", [])
            if not items:
                break

            total_count = page.get("total", "?")

            for conv_summary in items:
                conv_id = conv_summary.get("id", "")
                if conv_id in state.exported_ids:
                    total_skipped += 1
                    continue

                exported = _export_one(client, conv_id, root_dir)
                if exported:
                    state.mark_exported(conv_id)
                    total_exported += 1
                    print(f"  [{total_exported}/{total_count}] {exported}")

            offset += len(items)
            state.root_offset = offset
            state.save(state_path)

    print(f"\nDone. {total_exported} conversations exported, {total_skipped} skipped (already exported).")


def _export_one(
    client: APIClient, conv_id: str, target_dir: Path
) -> str | None:
    """Fetch and export a single conversation. Returns filename on success."""
    try:
        raw = client.get_conversation(conv_id)
    except FatalAPIError:
        raise
    except APIError as e:
        print(f"  Warning: skipping {conv_id}: {e}")
        return None

    mapping = raw.get("mapping", {})
    if not mapping:
        return None

    messages = flatten_conversation(mapping)
    if not messages:
        return None

    title = raw.get("title") or "Untitled"
    model_slug = _extract_model(raw, messages)

    conv = Conversation(
        id=conv_id,
        title=title,
        create_time=raw.get("create_time"),
        update_time=raw.get("update_time"),
        messages=messages,
        model_slug=model_slug,
    )

    md = render_conversation(conv)
    filename = safe_filename(title, conv_id)
    (target_dir / filename).write_text(md, encoding="utf-8")
    return filename


def _extract_model(raw: dict, messages: list) -> str | None:
    """Try to extract the model slug from conversation metadata or messages."""
    # Check conversation-level metadata
    model = raw.get("default_model_slug")
    if model:
        return model

    # Fall back to first assistant message's metadata
    for msg in messages:
        if msg.role == "assistant" and msg.model_slug:
            return msg.model_slug

    return None
