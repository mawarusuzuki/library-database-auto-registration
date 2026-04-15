from __future__ import annotations

import csv
import textwrap

import pytest

from src.models.book import Book
from src.repositories.book_repository import BookRepository
from src.services.book_service import (
    BookService,
    DuplicateIsbnError,
    InvalidIsbnError,
)


class FakeApiClient:
    def __init__(self, book: Book | None = None) -> None:
        self._book = book

    def fetch_by_isbn(self, isbn: str) -> Book | None:
        if self._book:
            self._book.isbn = isbn
        return self._book


@pytest.fixture
def repo(tmp_path):
    return BookRepository(str(tmp_path / "test.db"))


@pytest.fixture
def found_book():
    return Book(title="取得書籍", author="著者A", publisher="出版社A", published_year=2024)


@pytest.fixture
def service(repo, found_book):
    return BookService(repo=repo, api_clients=[FakeApiClient(found_book)])


@pytest.fixture
def service_no_api(repo):
    return BookService(repo=repo, api_clients=[FakeApiClient(None)])


class TestRegisterByIsbn:
    def test_register_success(self, service):
        book = service.register_by_isbn("9784000229819")
        assert book.id is not None
        assert book.title == "取得書籍"
        assert book.isbn == "9784000229819"

    def test_normalize_isbn_hyphens(self, service):
        book = service.register_by_isbn("978-4-00-022981-9")
        assert book.isbn == "9784000229819"

    def test_invalid_isbn_raises(self, service):
        with pytest.raises(InvalidIsbnError):
            service.register_by_isbn("invalid")

    def test_duplicate_raises(self, service):
        service.register_by_isbn("9784000229819")
        with pytest.raises(DuplicateIsbnError):
            service.register_by_isbn("9784000229819")

    def test_overwrite_updates_existing(self, service):
        service.register_by_isbn("9784000229819")
        book = service.register_by_isbn("9784000229819", overwrite=True)
        assert book.id is not None

    def test_api_not_found_raises_value_error(self, service_no_api):
        with pytest.raises(ValueError):
            service_no_api.register_by_isbn("9784000229819")


class TestRegisterManual:
    def test_register_manual_success(self, service):
        book = Book(title="手動登録書籍", isbn="9784003101803")
        result = service.register_manual(book)
        assert result.id is not None

    def test_register_manual_no_isbn(self, service):
        book = Book(title="ISBN無し書籍")
        result = service.register_manual(book)
        assert result.id is not None

    def test_duplicate_isbn_raises(self, service):
        service.register_manual(Book(title="A", isbn="9784003101803"))
        with pytest.raises(DuplicateIsbnError):
            service.register_manual(Book(title="B", isbn="9784003101803"))


class TestImportCsv:
    def _write_csv(self, path, rows: list[dict]) -> str:
        csv_path = str(path / "import.csv")
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["isbn", "title", "author", "publisher",
                            "published_year", "genre", "shelf_location", "memo"],
            )
            writer.writeheader()
            writer.writerows(rows)
        return csv_path

    def test_normal_import(self, service, tmp_path):
        csv_path = self._write_csv(
            tmp_path,
            [
                {"isbn": "9784000229819", "title": "書籍A", "author": "", "publisher": "",
                 "published_year": "", "genre": "", "shelf_location": "", "memo": ""},
                {"isbn": "9784003101803", "title": "書籍B", "author": "", "publisher": "",
                 "published_year": "", "genre": "", "shelf_location": "", "memo": ""},
            ],
        )
        result = service.import_csv(csv_path)
        assert result.success == 2
        assert result.skipped == 0
        assert result.errors == 0

    def test_duplicate_isbn_skipped(self, service, tmp_path):
        service.register_manual(Book(title="既存", isbn="9784000229819"))
        csv_path = self._write_csv(
            tmp_path,
            [{"isbn": "9784000229819", "title": "重複", "author": "", "publisher": "",
              "published_year": "", "genre": "", "shelf_location": "", "memo": ""}],
        )
        result = service.import_csv(csv_path)
        assert result.skipped == 1
        assert result.success == 0

    def test_empty_title_counted_as_error(self, service, tmp_path):
        csv_path = self._write_csv(
            tmp_path,
            [{"isbn": "", "title": "", "author": "", "publisher": "",
              "published_year": "", "genre": "", "shelf_location": "", "memo": ""}],
        )
        result = service.import_csv(csv_path)
        assert result.errors == 1

    def test_file_not_found_raises(self, service):
        with pytest.raises(FileNotFoundError):
            service.import_csv("/nonexistent/path.csv")


class TestSearch:
    def test_search_returns_matching(self, service):
        service.register_manual(Book(title="Python入門", isbn="9784000229819"))
        service.register_manual(Book(title="Java応用", isbn="9784003101803"))
        results = service.search(keyword="Python")
        assert len(results) == 1

    def test_find_all(self, service):
        service.register_manual(Book(title="A", isbn="9784000229819"))
        service.register_manual(Book(title="B", isbn="9784003101803"))
        assert len(service.find_all()) == 2


class TestDelete:
    def test_delete_hides_book(self, service):
        book = service.register_manual(Book(title="削除対象"))
        service.delete(book.id)
        assert service.find_all() == []


class TestExportCsv:
    def test_export_creates_file(self, service, tmp_path):
        service.register_manual(Book(title="エクスポート書籍"))
        out = str(tmp_path / "out.csv")
        count = service.export_csv(out)
        assert count == 1
        with open(out, encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["title"] == "エクスポート書籍"
