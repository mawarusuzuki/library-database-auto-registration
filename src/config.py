from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv(
        "NOTION_DATABASE_ID", "fa1efe49-628a-4839-b168-7c729be9660f"
    )
    GOOGLE_BOOKS_API_KEY: str = os.getenv("GOOGLE_BOOKS_API_KEY", "")
    API_TIMEOUT_SEC: int = int(os.getenv("API_TIMEOUT_SEC", "10"))
