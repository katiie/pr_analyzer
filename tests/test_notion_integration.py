#!/usr/bin/env python3
"""Tests for the Notion integration helper."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from notion_client import APIErrorCode, APIResponseError  # type: ignore

import notion_integration as ni


class DummyPages:
    """Capture calls to Notion API."""

    def __init__(self) -> None:
        self.calls: list[Dict[str, Any]] = []
        self.should_raise: Exception | None = None

    def create(self, **payload: Any) -> Dict[str, Any]:
        if self.should_raise:
            raise self.should_raise
        self.calls.append(payload)
        return {"id": "dummy-page-id"}


class DummyClient:
    """Lightweight stand-in for the real Notion client."""

    def __init__(self, auth: str | None = None) -> None:
        self.auth = auth
        self.pages = DummyPages()


def test_notion_integration_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing environment configuration should raise immediately."""
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_PAGE_ID", raising=False)

    with pytest.raises(ValueError, match="Missing Notion API key or page ID"):
        ni.NotionIntegration()


def test_notion_integration_initializes_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """A properly configured instance should wire up the Notion client."""
    monkeypatch.setenv("NOTION_API_KEY", "secret")
    monkeypatch.setenv("NOTION_PAGE_ID", "550e8400e29b41d4a716446655440000")
    created_clients: list[DummyClient] = []

    def client_factory(auth: str | None) -> DummyClient:
        client = DummyClient(auth)
        created_clients.append(client)
        return client

    monkeypatch.setattr(ni, "Client", client_factory)
    integration = ni.NotionIntegration()
    assert created_clients, "Client factory was not invoked"
    client = created_clients[0]
    assert integration.notion is client
    assert client.auth == "secret"


def test_create_page_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Creating a page should call the Notion API and return True on success."""
    monkeypatch.setenv("NOTION_API_KEY", "secret")
    monkeypatch.setenv("NOTION_PAGE_ID", "550e8400e29b41d4a716446655440000")
    monkeypatch.setattr(ni, "Client", lambda auth: DummyClient(auth))
    integration = ni.NotionIntegration()

    assert integration.create_page("Demo Title", "Some content")
    assert len(integration.notion.pages.calls) == 1
    create_payload = integration.notion.pages.calls[0]
    assert create_payload["parent"]["page_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert create_payload["properties"]["title"]["title"][0]["text"]["content"] == "Demo Title"


def test_create_page_propagates_exceptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Errors raised by the Notion client should bubble up."""
    monkeypatch.setenv("NOTION_API_KEY", "secret")
    monkeypatch.setenv("NOTION_PAGE_ID", "550e8400e29b41d4a716446655440000")
    def client_factory(auth: str | None) -> DummyClient:
        client = DummyClient(auth)
        client.pages.should_raise = RuntimeError("Notion failure")
        return client

    monkeypatch.setattr(ni, "Client", client_factory)
    integration = ni.NotionIntegration()

    with pytest.raises(RuntimeError, match="Notion failure"):
        integration.create_page("Fail Title", "Fail Content")


def test_initialization_handles_api_response_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Initialization should swallow APIResponseError, but still keep instance usable."""
    monkeypatch.setenv("NOTION_API_KEY", "secret")
    monkeypatch.setenv("NOTION_PAGE_ID", "550e8400e29b41d4a716446655440000")

    class FailingClient(DummyClient):
        def __init__(self, auth: str | None = None) -> None:
            raise APIResponseError("not found", code=APIErrorCode.ObjectNotFound)

    monkeypatch.setattr(ni, "Client", FailingClient)

    integration = ni.NotionIntegration()
    # The client attribute should not be set when initialization failed.
    assert not hasattr(integration, "notion")
