from __future__ import annotations

import time
from abc import ABC, abstractmethod

import requests

from src.models.book import Book


class BaseApiClient(ABC):
    TIMEOUT_SEC: int = 5
    MAX_RETRY: int = 3

    @abstractmethod
    def fetch_by_isbn(self, isbn: str) -> Book | None:
        ...

    def _request_with_retry(self, url: str, params: dict) -> dict | None:
        wait = 1
        for attempt in range(self.MAX_RETRY):
            try:
                resp = requests.get(url, params=params, timeout=self.TIMEOUT_SEC)
                resp.raise_for_status()
                return resp
            except requests.exceptions.Timeout:
                if attempt < self.MAX_RETRY - 1:
                    time.sleep(wait)
                    wait *= 2
            except requests.exceptions.RequestException:
                if attempt < self.MAX_RETRY - 1:
                    time.sleep(wait)
                    wait *= 2
        return None
