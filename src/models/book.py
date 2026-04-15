from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Book:
    title: str
    id: int | None = None
    isbn: str | None = None
    author: str | None = None
    publisher: str | None = None
    published_year: int | None = None
    genre: str | None = None
    shelf_location: str | None = None
    memo: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None


@dataclass
class ImportResult:
    success: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: list[str] = field(default_factory=list)
