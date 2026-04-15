from __future__ import annotations

from src.api.base_client import BaseApiClient
from src.models.book import Book

_GOOGLE_URL = "https://www.googleapis.com/books/v1/volumes"


class GoogleBooksClient(BaseApiClient):
    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    def fetch_by_isbn(self, isbn: str) -> Book | None:
        params: dict = {"q": f"isbn:{isbn}", "maxResults": "1"}
        if self._api_key:
            params["key"] = self._api_key

        resp = self._request_with_retry(_GOOGLE_URL, params)
        if resp is None:
            return None

        try:
            data = resp.json()
        except ValueError:
            return None

        items = data.get("items")
        if not items:
            return None

        info = items[0].get("volumeInfo", {})
        title = info.get("title")
        if not title:
            return None

        authors = info.get("authors", [])
        year: int | None = None
        date_str: str = info.get("publishedDate", "")
        if date_str:
            try:
                year = int(date_str[:4])
            except ValueError:
                pass

        categories = info.get("categories", [])

        return Book(
            isbn=isbn,
            title=title,
            author=" / ".join(authors) if authors else None,
            publisher=info.get("publisher"),
            published_year=year,
            genre=categories[0] if categories else None,
        )
