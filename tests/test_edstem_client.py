"""Tests for the EdStem client."""

from unittest.mock import MagicMock, patch

from mcp_servers.edstem.ed_client import EdClient


def test_client_not_configured_without_token():
    client = EdClient(api_token="", course_id=0)
    assert not client.is_configured


def test_client_configured_with_token():
    client = EdClient(api_token="test-token", course_id=12345)
    assert client.is_configured


def test_clean_content_strips_html():
    raw = "<p>Hello <strong>world</strong></p>"
    assert EdClient._clean_content(raw) == "Hello world"


def test_clean_content_unescapes_entities():
    raw = "Tom &amp; Jerry"
    assert EdClient._clean_content(raw) == "Tom & Jerry"


def test_thread_to_dict_builds_url():
    thread = {
        "id": 1,
        "number": 42,
        "course_id": 100,
        "title": "Test Thread",
        "type": "question",
        "category": "General",
        "content": "<p>Body</p>",
        "is_pinned": False,
        "created_at": "2026-01-01T00:00:00Z",
    }
    result = EdClient._thread_to_dict(thread)
    assert result["url"] == "https://edstem.org/us/courses/100/discussion/42"
    assert result["title"] == "Test Thread"
    assert result["content"] == "Body"


def test_search_returns_empty_when_not_configured():
    client = EdClient(api_token="", course_id=0)
    assert client.search_threads("test") == []


def test_get_announcements_returns_empty_when_not_configured():
    client = EdClient(api_token="", course_id=0)
    assert client.get_announcements() == []


def test_get_unread_returns_empty_when_not_configured():
    client = EdClient(api_token="", course_id=0)
    assert client.get_unread_threads() == []


@patch("mcp_servers.edstem.ed_client.requests.Session")
def test_search_threads_calls_api(mock_session_cls):
    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "threads": [
            {
                "id": 1,
                "number": 10,
                "course_id": 100,
                "title": "Paxos question",
                "type": "question",
                "category": "",
                "content": "How does Paxos work?",
                "is_pinned": False,
                "created_at": "2026-01-01",
            }
        ]
    }
    mock_session.get.return_value = mock_response
    mock_session_cls.return_value = mock_session

    client = EdClient(api_token="test-token", course_id=100)
    results = client.search_threads("Paxos")

    assert len(results) == 1
    assert results[0]["title"] == "Paxos question"
