from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)
_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksClient:
    def __init__(self, api_key: str = "", timeout: int = 10) -> None:
        self._api_key = api_key
        self._timeout = timeout

    def get_cover_url(self, title: str, author: str | None = None) -> str | None:
        query = f"intitle:{title}"
        if author:
            query += f"+inauthor:{author}"

        params: dict = {"q": query, "maxResults": "1"}
        if self._api_key:
            params["key"] = self._api_key

        try:
            resp = requests.get(_URL, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("Google Books API error: %s", e)
            return None

        items = data.get("items")
        if not items:
            return None

        image_links = items[0].get("volumeInfo", {}).get("imageLinks", {})
        url = image_links.get("thumbnail") or image_links.get("smallThumbnail")
        if url:
            # http → https に統一
            return url.replace("http://", "https://")
        return None
