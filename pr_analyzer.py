import sys
import traceback
from typing import Any, Dict, Sequence

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from github_integration import fetch_pr_changes, fetch_user_repos
from logger_config import get_logger
from notion_integration import NotionIntegration

logger = get_logger(__name__)


class PRAnalyzer:
    def __init__(self) -> None:
        """Initialize the PR analyzer service and register MCP tools."""
        load_dotenv()

        self.mcp = FastMCP("github_pr_analysis")
        logger.info("MCP Server initialized")

        self.notion_integration = NotionIntegration()
        self._register_tools()

    def _register_tools(self) -> None:
        """Register MCP tools for PR analysis and Notion integration."""

        @self.mcp.tool()
        async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
            """Fetch metadata and file diffs for a GitHub pull request."""
            logger.info("Fetching PR %s from %s/%s", pr_number, repo_owner, repo_name)
            try:
                pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
            except Exception as exc:
                logger.error("Error fetching PR: %s", exc)
                traceback.print_exc(file=sys.stderr)
                return {}

            if pr_info is None:
                logger.warning("No PR data returned for %s/%s#%s", repo_owner, repo_name, pr_number)
                return {}

            logger.info("Fetched PR details successfully")
            return pr_info

        @self.mcp.tool()
        async def create_notion_page(title: str, content: str) -> str:
            """Create a Notion page containing the supplied content."""
            self.notion_integration.create_page(title, content)
            return "Notion page created successfully"

        @self.mcp.tool()
        async def fetch_repos() -> Sequence[str]:
            """Return repositories visible to the authenticated GitHub user."""
            try:
                repo_names = fetch_user_repos()
            except Exception as exc:
                logger.error("Error fetching user repositories: %s", exc)
                traceback.print_exc(file=sys.stderr)
                return []

            if not repo_names:
                logger.warning("No repositories found for the authenticated user")
                return []

            logger.info("Fetched %s repositories for the authenticated user", len(repo_names))
            return repo_names

    def run(self, transport: str = "stdio") -> None:
        """Start the MCP server with the requested transport."""
        try:
            if transport == "stdio":
                logger.info("Starting MCP server with stdio transport")
                self.mcp.run(transport="stdio")
            elif transport == "sse":
                logger.info("Starting MCP server with sse transport")
                self.mcp.run(transport="sse")
            else:
                raise ValueError(f"Invalid transport: {transport}")
        except Exception as exc:
            logger.error("Fatal error in MCP server: %s", exc)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    analyzer = PRAnalyzer()
    analyzer.run()
