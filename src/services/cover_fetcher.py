from __future__ import annotations

import logging

from src.api.google_books_client import GoogleBooksClient
from src.api.open_library_client import OpenLibraryClient

logger = logging.getLogger(__name__)


class CoverFetcher:
    def __init__(
        self,
        google_client: GoogleBooksClient,
        open_library_client: OpenLibraryClient,
    ) -> None:
        self._google = google_client
        self._open_library = open_library_client

    def fetch(self, title: str, author: str | None = None) -> str | None:
        url = self._google.get_cover_url(title, author)
        if url:
            logger.debug("Cover from Google Books: %s", title)
            return url

        url = self._open_library.get_cover_url(title, author)
        if url:
            logger.debug("Cover from Open Library: %s", title)
            return url

        logger.debug("No cover found: %s", title)
        return None
