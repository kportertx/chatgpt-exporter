"""Tests for markdown rendering."""

from chatgpt_export.markdown import render_conversation, safe_dirname, safe_filename
from chatgpt_export.models import Conversation, Message


def test_safe_filename_basic():
    result = safe_filename("My Chat Title", "abcd1234-5678")
    assert result == "My Chat Title [abcd1234].md"


def test_safe_filename_special_chars():
    result = safe_filename('What is "AI"?', "abcd1234-5678")
    assert "/" not in result
    assert '"' not in result
    assert result.endswith(".md")


def test_safe_filename_empty_title():
    result = safe_filename("", "abcd1234-5678")
    assert result == "Untitled [abcd1234].md"


def test_safe_filename_long_title():
    long_title = "A" * 300
    result = safe_filename(long_title, "abcd1234-5678")
    assert len(result) < 220  # 200 + hash + extension


def test_safe_dirname():
    assert safe_dirname("My Project") == "My Project"
    assert safe_dirname('Weird/Name:"here"') == "Weird-Name-here"


def test_render_conversation_basic():
    conv = Conversation(
        id="abc123",
        title="Test Chat",
        create_time=1700000000.0,
        update_time=1700001000.0,
        messages=[
            Message(
                id="m1",
                role="user",
                content_type="text",
                parts=["What is Python?"],
                create_time=1700000000.0,
            ),
            Message(
                id="m2",
                role="assistant",
                content_type="text",
                parts=["Python is a programming language."],
                model_slug="gpt-4o",
                create_time=1700000500.0,
            ),
        ],
        model_slug="gpt-4o",
    )

    md = render_conversation(conv)

    assert "---" in md
    assert 'title: "Test Chat"' in md
    assert "conversation_id: abc123" in md
    assert "model: gpt-4o" in md
    assert "# Test Chat" in md
    assert "## User" in md
    assert "What is Python?" in md
    assert "## Assistant" in md
    assert "Python is a programming language." in md


def test_render_conversation_no_timestamps():
    conv = Conversation(
        id="abc123",
        title="Minimal",
        create_time=None,
        update_time=None,
        messages=[],
        model_slug=None,
    )
    md = render_conversation(conv)
    assert "date:" not in md
    assert "model:" not in md
    assert "# Minimal" in md
