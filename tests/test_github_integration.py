#!/usr/bin/env python3
"""Tests for GitHub integration helpers."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, List

import pytest
from requests.exceptions import HTTPError, RequestException

import github_integration as gi


@dataclass
class DummyResponse:
    """Simple response stand-in that mimics the ``requests`` interface we use."""

    json_payload: Any
    status_code: int = 200

    def json(self) -> Any:
        return self.json_payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise HTTPError(f"http {self.status_code} error")


def _iter_responses(responses: List[DummyResponse]) -> Iterator[DummyResponse]:
    """Yield responses sequentially to simulate multiple HTTP calls."""
    for response in responses:
        yield response


def test_fetch_user_repos_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """When GitHub returns repositories, we should return the list of names."""
    monkeypatch.setattr(gi, "GITHUB_TOKEN", "dummy-token")

    payload = [{"full_name": "owner/repo1"}, {"full_name": "owner/repo2"}]
    monkeypatch.setattr(gi.requests, "get", lambda url, headers: DummyResponse(payload))

    repos = gi.fetch_user_repos()
    assert repos == ["owner/repo1", "owner/repo2"]


def test_fetch_user_repos_handles_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP failures should be caught and translated into ``None``."""
    monkeypatch.setattr(gi.requests, "get", lambda url, headers: DummyResponse([], status_code=500))

    assert gi.fetch_user_repos() is None


def test_fetch_user_repos_handles_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Network issues should be logged and surfaced as ``None``."""

    def boom(url: str, headers: dict) -> None:
        raise RequestException("network down")

    monkeypatch.setattr(gi.requests, "get", boom)
    assert gi.fetch_user_repos() is None


def test_fetch_user_repos_handles_unexpected_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any unexpected exception should also be caught and return ``None``."""

    def boom(url: str, headers: dict) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(gi.requests, "get", boom)
    assert gi.fetch_user_repos() is None


def test_fetch_pr_changes_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful PR fetch should combine metadata and file data."""
    pr_payload = {
        "title": "Update README",
        "body": "Some description",
        "user": {"login": "octocat"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "state": "open",
    }
    files_payload = [
        {
            "filename": "README.md",
            "status": "modified",
            "additions": 5,
            "deletions": 1,
            "changes": 6,
            "patch": "@@ -1 +1 @@",
            "raw_url": "https://raw/README.md",
            "contents_url": "https://contents/README.md",
        }
    ]

    response_iter = _iter_responses([DummyResponse(pr_payload), DummyResponse(files_payload)])
    monkeypatch.setattr(
        gi.requests,
        "get",
        lambda url, headers: next(response_iter),
    )

    result = gi.fetch_pr_changes("owner", "repo", 123)
    assert result is not None
    assert result["title"] == pr_payload["title"]
    assert result["author"] == pr_payload["user"]["login"]
    assert result["total_changes"] == 1
    assert result["changes"][0]["filename"] == "README.md"


def test_fetch_pr_changes_handles_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """HTTP errors should log and return ``None``."""
    monkeypatch.setattr(
        gi.requests,
        "get",
        lambda url, headers: DummyResponse({}, status_code=404),
    )

    assert gi.fetch_pr_changes("owner", "repo", 1) is None


def test_fetch_pr_changes_handles_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Network issues while fetching PR data should return ``None``."""

    def boom(url: str, headers: dict) -> None:
        raise RequestException("timeout")

    monkeypatch.setattr(gi.requests, "get", boom)
    assert gi.fetch_pr_changes("owner", "repo", 1) is None


def test_fetch_pr_changes_handles_unexpected_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unexpected exceptions should be caught and return ``None``."""

    def boom(url: str, headers: dict) -> None:
        raise ValueError("bad coding")

    monkeypatch.setattr(gi.requests, "get", boom)
    assert gi.fetch_pr_changes("owner", "repo", 1) is None
