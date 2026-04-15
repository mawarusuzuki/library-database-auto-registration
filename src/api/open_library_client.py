from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)
_SEARCH_URL = "https://openlibrary.org/search.json"
_COVER_URL = "https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"


class OpenLibraryClient:
    def __init__(self, timeout: int = 10) -> None:
        self._timeout = timeout

    def get_cover_url(self, title: str, author: str | None = None) -> str | None:
        params: dict = {"title": title, "limit": "1"}
        if author:
            params["author"] = author

        try:
            resp = requests.get(_SEARCH_URL, params=params, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("Open Library API error: %s", e)
            return None

        docs = data.get("docs")
        if not docs:
            return None

        cover_id = docs[0].get("cover_i")
        if cover_id:
            return _COVER_URL.format(cover_id=cover_id)
        return None
