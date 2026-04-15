"""Tests for the EdStem MCP server tools."""

from unittest.mock import patch

from mcp_servers.edstem.server import (
    get_ed_announcements,
    get_ed_pinned,
    get_ed_unread,
    search_ed,
)


@patch.dict("os.environ", {"ED_API_TOKEN": "", "ED_COURSE_ID": "0"})
def test_search_ed_not_configured():
    result = search_ed("test")
    assert "not configured" in result


@patch.dict("os.environ", {"ED_API_TOKEN": "", "ED_COURSE_ID": "0"})
def test_announcements_not_configured():
    result = get_ed_announcements()
    assert "not configured" in result


@patch.dict("os.environ", {"ED_API_TOKEN": "", "ED_COURSE_ID": "0"})
def test_pinned_not_configured():
    result = get_ed_pinned()
    assert "not configured" in result


@patch.dict("os.environ", {"ED_API_TOKEN": "", "ED_COURSE_ID": "0"})
def test_unread_not_configured():
    result = get_ed_unread()
    assert "not configured" in result
