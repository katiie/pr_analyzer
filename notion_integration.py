import os
import traceback

from notion_client import Client
from dotenv import load_dotenv
from notion_client import APIErrorCode, APIResponseError
from utils import format_uuid_string
from logger_config import get_logger


load_dotenv()  # pyright: ignore[reportUnusedCallResult]
logger = get_logger(__name__)

class NotionIntegration:
    def __init__(self) -> None:
        self.notion_api_key: str | None = os.getenv("NOTION_API_KEY")
        self.notion_page_id: str | None = os.getenv("NOTION_PAGE_ID")

        if not self.notion_api_key or not self.notion_page_id:
            raise ValueError("Missing Notion API key or page ID in environment variables")

        try:
            self.notion: Client = Client(auth=self.notion_api_key)
            logger.info("Notion client initialized successfully")
            logger.info("Using Notion page ID: %s", self.notion_page_id)
        except APIResponseError as error:
            if error.code == APIErrorCode.ObjectNotFound:
                logger.error("Configured Notion page was not found")
            else:
                logger.error("Failed to initialize Notion client: %s", error)
        except Exception as e:
            logger.error("Failed to initialize Notion client: %s", e)
            traceback.print_exc()
            raise


    def create_page(self, title: str, content: str) -> bool:
        try:
            page_id = format_uuid_string(self.notion_page_id)
            logger.info("Creating Notion page in %s", page_id)

            _ = self.notion.pages.create(
                parent={"type": "page_id", "page_id": page_id},
                properties={"title": {"title": [{"text": {"content": title}}]}},
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{
                            "type": "text",
                            "text": {"content": content}
                        }]
                    }
                }]
            )
            return True
        except Exception as e:
            logger.error("Failed to create Notion page: %s", e)
            traceback.print_exc()
            raise

if __name__ == "__main__":
    notion_integration = NotionIntegration()
    notion_integration.create_page("Test Title", "Test Content")
