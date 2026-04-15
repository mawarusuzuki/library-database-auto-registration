from __future__ import annotations

import csv
import logging
import re
from pathlib import Path

from src.api.base_client import BaseApiClient
from src.models.book import Book, ImportResult
from src.repositories.book_repository import BookRepository

logger = logging.getLogger(__name__)

_ISBN_RE = re.compile(r"^(?:97[89])?\d{9}[\dXx]$")


def _normalize_isbn(raw: str) -> str:
    return raw.replace("-", "").replace(" ", "")


def _is_valid_isbn(isbn: str) -> bool:
    normalized = _normalize_isbn(isbn)
    return bool(_ISBN_RE.match(normalized))


class DuplicateIsbnError(Exception):
    pass


class InvalidIsbnError(Exception):
    pass


class BookService:
    def __init__(
        self,
        repo: BookRepository,
        api_clients: list[BaseApiClient],
    ) -> None:
        self._repo = repo
        self._api_clients = api_clients

    # ------------------------------------------------------------------
    # ISBN バリデーション
    # ------------------------------------------------------------------

    def _validate_isbn(self, isbn: str) -> str:
        if not _is_valid_isbn(isbn):
            raise InvalidIsbnError(f"ISBN フォーマットが不正です: {isbn}")
        return _normalize_isbn(isbn)

    # ------------------------------------------------------------------
    # 外部 API から書誌情報を取得
    # ------------------------------------------------------------------

    def _fetch_book_info(self, isbn: str) -> Book | None:
        for client in self._api_clients:
            try:
                book = client.fetch_by_isbn(isbn)
                if book:
                    return book
            except Exception as e:
                logger.warning("API fetch failed (%s): %s", type(client).__name__, e)
        return None

    # ------------------------------------------------------------------
    # 登録
    # ------------------------------------------------------------------

    def register_by_isbn(self, isbn: str, overwrite: bool = False) -> Book:
        isbn = self._validate_isbn(isbn)

        existing = self._repo.find_by_isbn(isbn)
        if existing and not overwrite:
            raise DuplicateIsbnError(f"ISBN {isbn} は既に登録済みです")

        book = self._fetch_book_info(isbn)
        if book is None:
            raise ValueError(f"ISBN {isbn} の書誌情報を取得できませんでした")

        if existing and overwrite:
            book.id = existing.id
            book.shelf_location = existing.shelf_location
            book.memo = existing.memo
            result = self._repo.update(book)
            logger.info("UPDATE isbn=%s title=%s", isbn, book.title)
            return result

        result = self._repo.create(book)
        logger.info("REGISTER isbn=%s title=%s", isbn, book.title)
        return result

    def register_manual(self, book: Book) -> Book:
        if book.isbn:
            book.isbn = self._validate_isbn(book.isbn)
            existing = self._repo.find_by_isbn(book.isbn)
            if existing:
                raise DuplicateIsbnError(f"ISBN {book.isbn} は既に登録済みです")

        result = self._repo.create(book)
        logger.info("REGISTER isbn=%s title=%s", book.isbn, book.title)
        return result

    # ------------------------------------------------------------------
    # CSV 一括インポート
    # ------------------------------------------------------------------

    def import_csv(self, csv_path: str) -> ImportResult:
        result = ImportResult()
        path = Path(csv_path)

        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {csv_path}")

        with path.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for line_no, row in enumerate(reader, start=2):
                title = (row.get("title") or "").strip()
                if not title:
                    msg = f"行 {line_no}: title が空のためスキップ"
                    logger.warning(msg)
                    result.errors += 1
                    result.error_details.append(msg)
                    continue

                isbn_raw = (row.get("isbn") or "").strip()
                isbn: str | None = None
                if isbn_raw:
                    if not _is_valid_isbn(isbn_raw):
                        msg = f"行 {line_no}: ISBN フォーマット不正 ({isbn_raw})"
                        logger.warning(msg)
                        result.errors += 1
                        result.error_details.append(msg)
                        continue
                    isbn = _normalize_isbn(isbn_raw)
                    if self._repo.find_by_isbn(isbn):
                        logger.warning("DUPLICATE isbn=%s → skipped", isbn)
                        result.skipped += 1
                        continue

                year: int | None = None
                year_raw = (row.get("published_year") or "").strip()
                if year_raw:
                    try:
                        year = int(year_raw)
                    except ValueError:
                        pass

                book = Book(
                    isbn=isbn,
                    title=title,
                    author=(row.get("author") or "").strip() or None,
                    publisher=(row.get("publisher") or "").strip() or None,
                    published_year=year,
                    genre=(row.get("genre") or "").strip() or None,
                    shelf_location=(row.get("shelf_location") or "").strip() or None,
                    memo=(row.get("memo") or "").strip() or None,
                )
                try:
                    self._repo.create(book)
                    logger.info("IMPORT isbn=%s title=%s", isbn, title)
                    result.success += 1
                except Exception as e:
                    msg = f"行 {line_no}: DB 登録失敗 ({e})"
                    logger.error(msg)
                    result.errors += 1
                    result.error_details.append(msg)

        return result

    # ------------------------------------------------------------------
    # 検索
    # ------------------------------------------------------------------

    def search(
        self,
        keyword: str = "",
        genre: str = "",
        year: int | None = None,
    ) -> list[Book]:
        return self._repo.search(keyword=keyword, genre=genre, year=year)

    def find_all(self) -> list[Book]:
        return self._repo.find_all()

    # ------------------------------------------------------------------
    # 更新・削除
    # ------------------------------------------------------------------

    def update(self, book: Book) -> Book:
        if book.isbn:
            book.isbn = self._validate_isbn(book.isbn)
        result = self._repo.update(book)
        logger.info("UPDATE id=%s title=%s", book.id, book.title)
        return result

    def delete(self, book_id: int) -> None:
        self._repo.soft_delete(book_id)
        logger.info("DELETE id=%s", book_id)

    # ------------------------------------------------------------------
    # CSV エクスポート
    # ------------------------------------------------------------------

    def export_csv(
        self,
        output_path: str,
        books: list[Book] | None = None,
    ) -> int:
        if books is None:
            books = self._repo.find_all()

        fieldnames = [
            "id", "isbn", "title", "author", "publisher",
            "published_year", "genre", "shelf_location", "memo",
            "created_at", "updated_at",
        ]
        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for book in books:
                writer.writerow(
                    {
                        "id": book.id,
                        "isbn": book.isbn or "",
                        "title": book.title,
                        "author": book.author or "",
                        "publisher": book.publisher or "",
                        "published_year": book.published_year or "",
                        "genre": book.genre or "",
                        "shelf_location": book.shelf_location or "",
                        "memo": book.memo or "",
                        "created_at": book.created_at or "",
                        "updated_at": book.updated_at or "",
                    }
                )
        return len(books)
