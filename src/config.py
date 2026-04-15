from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    DB_PATH: str = os.getenv("DB_PATH", "library.db")
    LOG_PATH: str = os.getenv("LOG_PATH", "logs/register.log")
    API_TIMEOUT_SEC: int = int(os.getenv("API_TIMEOUT_SEC", "5"))
    GOOGLE_BOOKS_API_KEY: str = os.getenv("GOOGLE_BOOKS_API_KEY", "")
    API_PRIORITY: list[str] = [
        s.strip()
        for s in os.getenv("API_PRIORITY", "ndl,google_books").split(",")
        if s.strip()
    ]

    @classmethod
    def ensure_log_dir(cls) -> None:
        Path(cls.LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
