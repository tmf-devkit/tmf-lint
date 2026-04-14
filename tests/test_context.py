"""Tests for tmf_lint.context — LintContext."""
from tmf_lint.context import LintContext


def test_set_and_get():
    ctx = LintContext(base_url="http://x", apis=[638])
    ctx.set("key", "value")
    assert ctx.get("key") == "value"


def test_get_missing_returns_default():
    ctx = LintContext(base_url="http://x", apis=[638])
    assert ctx.get("missing") is None
    assert ctx.get("missing", "fallback") == "fallback"


def test_has():
    ctx = LintContext(base_url="http://x", apis=[638])
    ctx.set("present", 1)
    assert ctx.has("present")
    assert not ctx.has("absent")


def test_get_str_returns_string():
    ctx = LintContext(base_url="http://x", apis=[638])
    ctx.set("sid", "abc-123")
    assert ctx.get_str("sid") == "abc-123"


def test_get_str_missing_returns_none():
    ctx = LintContext(base_url="http://x", apis=[638])
    assert ctx.get_str("missing") is None


def test_get_list_returns_list():
    ctx = LintContext(base_url="http://x", apis=[638])
    ctx.set("ids", ["a", "b"])
    assert ctx.get_list("ids") == ["a", "b"]


def test_get_list_missing_returns_empty():
    ctx = LintContext(base_url="http://x", apis=[638])
    assert ctx.get_list("missing") == []


def test_append_creates_list():
    ctx = LintContext(base_url="http://x", apis=[638])
    ctx.append("ids", "a")
    ctx.append("ids", "b")
    assert ctx.get_list("ids") == ["a", "b"]


def test_append_to_existing_list():
    ctx = LintContext(base_url="http://x", apis=[638])
    ctx.set("ids", ["existing"])
    ctx.append("ids", "new")
    assert ctx.get_list("ids") == ["existing", "new"]
