## GitHub PR Reviewer MCP

### Overview
- `pr_analyzer.py` exposes MCP tools for fetching GitHub PR metadata, generating Notion reports, and listing repos.
- `github_integration.py`, `notion_integration.py`, and `logger_config.py` handle external APIs with shared logging.
- Tests live in `tests/` and cover integration helpers, logging config, the MCP server, and UUID utilities.

### Project Structure
- `pr_analyzer.py` — MCP entry point registering all tools.
- `github_integration.py` — GitHub REST helpers for PRs and repo listings.
- `notion_integration.py` — Wrapper around the Notion SDK for creating report pages.
- `logger_config.py` — Shared logging configuration writing to `mcp_server.log`.
- `utils.py` — UUID helpers used by Notion integration and tests.
- `tests/` — Pytest suites for all modules (`test_*.py`).
- `.env` (ignored) — Set GitHub and Notion credentials locally.
- `mcp_server.log` (ignored) — Combined file/stdout logging target.

### Requirements
- Python 3.11+ (repo uses `uv` for toolchain management).
- Environment variables:
  - `GITHUB_TOKEN` — personal access token with repo scope.
  - `NOTION_API_KEY` — integration access token.
  - `NOTION_PAGE_ID` — destination page for generated analysis.

### Setup & Running
- Install dependencies: `uv sync`
- Export secrets in `.env` (or your shell) before running.
- Start the MCP server: `uv run python pr_analyzer.py`
- Client transports:
  - `stdio` (default): `uv run python pr_analyzer.py`
  - `sse`: `uv run python pr_analyzer.py --transport sse` (custom CLI wrapper required).

### Testing
- CLI: `uv run pytest`
- With Claude Code:
  - Open the project in Claude Code.
  - Run `uv run pytest` in the Claude terminal to reuse the same virtual environment.
  - For individual tests: `uv run pytest tests/test_github_integration.py -k fetch_user_repos`

### Logging & Troubleshooting
- All modules share the same handlers via `logger_config.get_logger`.
- Logs stream to stderr and append to `mcp_server.log` in the repo root.
- If API calls fail, log entries will include stack traces; rerun tests with `-vv` for extra detail.
