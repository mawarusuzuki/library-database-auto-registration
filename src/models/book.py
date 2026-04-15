from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class KindleBook:
    asin: str
    title: str
    amazon_url: str
    author: str | None = None
    cover_url: str | None = None
    type_estimate: str | None = None


@dataclass
class RegisterResult:
    success: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: list[str] = field(default_factory=list)
