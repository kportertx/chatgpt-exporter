"""Tests for conversation tree flattening."""

from chatgpt_export.tree import flatten_conversation


def _make_node(node_id, parent=None, children=None, role="user", text="hello"):
    """Helper to build a mapping node."""
    node = {
        "id": node_id,
        "parent": parent,
        "children": children or [],
    }
    if role and text:
        node["message"] = {
            "author": {"role": role},
            "content": {"content_type": "text", "parts": [text]},
            "create_time": 1000000.0,
            "metadata": {},
        }
    return node


def test_empty_mapping():
    assert flatten_conversation({}) == []


def test_single_message():
    mapping = {
        "root": {
            "id": "root",
            "parent": None,
            "children": ["msg1"],
            "message": None,
        },
        "msg1": _make_node("msg1", parent="root", role="user", text="hi"),
    }
    result = flatten_conversation(mapping)
    assert len(result) == 1
    assert result[0].role == "user"
    assert result[0].parts == ["hi"]


def test_linear_conversation():
    mapping = {
        "root": {
            "id": "root",
            "parent": None,
            "children": ["u1"],
            "message": {"author": {"role": "system"}, "content": {"parts": [""]}, "metadata": {}},
        },
        "u1": _make_node("u1", parent="root", children=["a1"], role="user", text="question"),
        "a1": _make_node("a1", parent="u1", children=["u2"], role="assistant", text="answer"),
        "u2": _make_node("u2", parent="a1", role="user", text="follow-up"),
    }
    result = flatten_conversation(mapping)
    assert len(result) == 3
    assert [m.role for m in result] == ["user", "assistant", "user"]
    assert [m.parts[0] for m in result] == ["question", "answer", "follow-up"]


def test_branching_follows_last_child():
    """When a user edits a message, the original is child[0] and the edit is child[1].
    We should follow the last child (the edit)."""
    mapping = {
        "root": {
            "id": "root",
            "parent": None,
            "children": ["u1"],
            "message": None,
        },
        "u1": _make_node("u1", parent="root", children=["a1_orig", "a1_edit"], role="user", text="question"),
        "a1_orig": _make_node("a1_orig", parent="u1", role="assistant", text="original answer"),
        "a1_edit": _make_node("a1_edit", parent="u1", children=["u2"], role="assistant", text="edited answer"),
        "u2": _make_node("u2", parent="a1_edit", role="user", text="thanks"),
    }
    result = flatten_conversation(mapping)
    assert len(result) == 3
    assert result[1].parts == ["edited answer"]
    assert result[2].parts == ["thanks"]


def test_system_messages_filtered():
    mapping = {
        "sys": {
            "id": "sys",
            "parent": None,
            "children": ["u1"],
            "message": {
                "author": {"role": "system"},
                "content": {"content_type": "text", "parts": ["system prompt"]},
                "metadata": {},
            },
        },
        "u1": _make_node("u1", parent="sys", role="user", text="hello"),
    }
    result = flatten_conversation(mapping)
    assert len(result) == 1
    assert result[0].role == "user"


def test_empty_message_filtered():
    mapping = {
        "root": {
            "id": "root",
            "parent": None,
            "children": ["empty", "u1"],
            "message": None,
        },
        "empty": {
            "id": "empty",
            "parent": "root",
            "children": [],
            "message": {
                "author": {"role": "user"},
                "content": {"content_type": "text", "parts": [""]},
                "metadata": {},
            },
        },
        "u1": _make_node("u1", parent="root", role="user", text="actual message"),
    }
    # Follows last child (u1), skips empty
    result = flatten_conversation(mapping)
    assert len(result) == 1
    assert result[0].parts == ["actual message"]


def test_model_slug_preserved():
    mapping = {
        "root": {
            "id": "root",
            "parent": None,
            "children": ["a1"],
            "message": None,
        },
        "a1": {
            "id": "a1",
            "parent": "root",
            "children": [],
            "message": {
                "author": {"role": "assistant"},
                "content": {"content_type": "text", "parts": ["response"]},
                "create_time": 1000000.0,
                "metadata": {"model_slug": "gpt-4o"},
            },
        },
    }
    result = flatten_conversation(mapping)
    assert len(result) == 1
    assert result[0].model_slug == "gpt-4o"
