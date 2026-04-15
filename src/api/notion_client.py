from __future__ import annotations

import logging

from notion_client import Client
from notion_client.errors import APIResponseError

from src.models.book import KindleBook

logger = logging.getLogger(__name__)


class NotionClient:
    def __init__(self, token: str, database_id: str) -> None:
        self._client = Client(auth=token)
        self._db_id = database_id

    def get_registered_urls(self) -> set[str]:
        """書庫DB に登録済みの URL をすべて取得して返す。"""
        urls: set[str] = set()
        cursor = None

        while True:
            kwargs: dict = {"database_id": self._db_id}
            if cursor:
                kwargs["start_cursor"] = cursor

            resp = self._client.databases.query(**kwargs)

            for page in resp.get("results", []):
                url_prop = page.get("properties", {}).get("URL", {})
                url = url_prop.get("url")
                if url:
                    urls.add(url.rstrip("/"))

            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")

        return urls

    def register_book(self, book: KindleBook) -> None:
        """書庫DB に1件ページを作成する。"""
        properties: dict = {
            "Title": {"title": [{"text": {"content": book.title}}]},
            "URL": {"url": book.amazon_url},
            "Status": {"status": {"name": "Not started"}},
        }

        if book.author:
            properties["著者"] = {"rich_text": [{"text": {"content": book.author}}]}

        if book.type_estimate:
            properties["Type"] = {"multi_select": [{"name": book.type_estimate}]}

        if book.cover_url:
            properties["表紙"] = {
                "files": [
                    {
                        "name": "cover",
                        "type": "external",
                        "external": {"url": book.cover_url},
                    }
                ]
            }

        try:
            self._client.pages.create(
                parent={"database_id": self._db_id},
                properties=properties,
            )
            logger.info("REGISTERED: %s (%s)", book.title, book.asin)
        except APIResponseError as e:
            logger.error("Notion API error for %s: %s", book.asin, e)
            raise
