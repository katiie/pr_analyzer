#!/usr/bin/env python3
"""Tests for the MCP PRAnalyzer server."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Sequence, Tuple

import pytest

import pr_analyzer as pa


class DummyNotionIntegration:
    """Simple stub capturing create_page calls."""

    def __init__(self) -> None:
        self.created: List[Tuple[str, str]] = []

    def create_page(self, title: str, content: str) -> bool:
        self.created.append((title, content))
        return True


class DummyFastMCP:
    """Minimal FastMCP drop-in used for testing registration and run logic."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.tools: Dict[str, Any] = {}
        self.run_calls: List[str] = []
        self.raise_on_run: Exception | None = None

    def tool(self):
        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator

    def run(self, transport: str = "stdio") -> None:
        self.run_calls.append(transport)
        if self.raise_on_run:
            raise self.raise_on_run


@pytest.fixture
def analyzer_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> Tuple[pa.PRAnalyzer, DummyNotionIntegration, DummyFastMCP]:
    """Provide a PRAnalyzer wired to dummy dependencies."""
    notion_stub = DummyNotionIntegration()
    mcp_instances: List[DummyFastMCP] = []

    def fastmcp_factory(name: str) -> DummyFastMCP:
        instance = DummyFastMCP(name)
        mcp_instances.append(instance)
        return instance

    monkeypatch.setattr(pa, "FastMCP", fastmcp_factory)
    monkeypatch.setattr(pa, "NotionIntegration", lambda: notion_stub)

    analyzer = pa.PRAnalyzer()
    assert len(mcp_instances) == 1
    return analyzer, notion_stub, mcp_instances[0]


def run_async(coro):
    """Helper to execute async tools without requiring pytest-asyncio."""
    return asyncio.run(coro)


def test_pr_analyzer_registers_expected_tools(analyzer_fixture) -> None:
    """All expected tools should be registered on initialization."""
    _, _, mcp_stub = analyzer_fixture
    assert set(mcp_stub.tools.keys()) == {"fetch_pr", "create_notion_page", "fetch_repos"}


def test_fetch_pr_tool_success(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """fetch_pr should return data from fetch_pr_changes."""
    analyzer, _, mcp_stub = analyzer_fixture
    expected = {"title": "Example", "changes": []}
    monkeypatch.setattr(pa, "fetch_pr_changes", lambda *args, **kwargs: expected)

    result = run_async(mcp_stub.tools["fetch_pr"]("owner", "repo", 7))
    assert result == expected


def test_fetch_pr_tool_handles_none(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """fetch_pr should return an empty dict when no data is returned."""
    analyzer, _, mcp_stub = analyzer_fixture
    monkeypatch.setattr(pa, "fetch_pr_changes", lambda *args, **kwargs: None)

    result = run_async(mcp_stub.tools["fetch_pr"]("owner", "repo", 7))
    assert result == {}


def test_fetch_pr_tool_handles_exception(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """Exceptions from fetch_pr_changes should be swallowed."""
    analyzer, _, mcp_stub = analyzer_fixture

    def boom(*args, **kwargs):
        raise RuntimeError("fetch failure")

    monkeypatch.setattr(pa, "fetch_pr_changes", boom)

    result = run_async(mcp_stub.tools["fetch_pr"]("owner", "repo", 7))
    assert result == {}


def test_create_notion_page_tool(analyzer_fixture) -> None:
    """create_notion_page should delegate and report success."""
    analyzer, notion_stub, mcp_stub = analyzer_fixture

    result = run_async(mcp_stub.tools["create_notion_page"]("Title", "Content"))
    assert result == "Notion page created successfully"
    assert notion_stub.created == [("Title", "Content")]


def test_fetch_repos_tool_success(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """fetch_repos should surface repository names."""
    analyzer, _, mcp_stub = analyzer_fixture
    monkeypatch.setattr(pa, "fetch_user_repos", lambda: ["one", "two"])

    result = run_async(mcp_stub.tools["fetch_repos"]())
    assert result == ["one", "two"]


def test_fetch_repos_tool_handles_none(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """None results are converted into an empty list."""
    analyzer, _, mcp_stub = analyzer_fixture
    monkeypatch.setattr(pa, "fetch_user_repos", lambda: None)

    result = run_async(mcp_stub.tools["fetch_repos"]())
    assert result == []


def test_fetch_repos_tool_handles_exception(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """Errors fetching repos should be handled gracefully."""
    analyzer, _, mcp_stub = analyzer_fixture

    def boom():
        raise RuntimeError("nope")

    monkeypatch.setattr(pa, "fetch_user_repos", boom)

    result = run_async(mcp_stub.tools["fetch_repos"]())
    assert result == []


def test_run_invokes_fastmcp(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """run should call through to FastMCP with the configured transport."""
    analyzer, _, mcp_stub = analyzer_fixture
    analyzer.run("stdio")
    analyzer.run("sse")

    assert mcp_stub.run_calls == ["stdio", "sse"]


def test_run_exits_for_invalid_transport(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """Providing an unsupported transport should trigger sys.exit(1)."""
    analyzer, _, mcp_stub = analyzer_fixture
    exit_codes: List[int] = []

    def fake_exit(code: int) -> None:
        exit_codes.append(code)
        raise SystemExit(code)

    monkeypatch.setattr(pa.sys, "exit", fake_exit)

    with pytest.raises(SystemExit):
        analyzer.run("websocket")

    assert exit_codes == [1]
    assert mcp_stub.run_calls == []


def test_run_exits_on_fatal_error(monkeypatch: pytest.MonkeyPatch, analyzer_fixture) -> None:
    """Fatal errors should trigger sys.exit(1)."""
    analyzer, _, mcp_stub = analyzer_fixture
    mcp_stub.raise_on_run = RuntimeError("fatal")

    exit_codes: List[int] = []

    def fake_exit(code: int) -> None:
        exit_codes.append(code)
        raise SystemExit(code)

    monkeypatch.setattr(pa.sys, "exit", fake_exit)

    with pytest.raises(SystemExit):
        analyzer.run("stdio")

    assert exit_codes == [1]
