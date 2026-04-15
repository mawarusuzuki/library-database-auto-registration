from __future__ import annotations

import pytest

from src.models.book import Book
from src.repositories.book_repository import BookRepository


@pytest.fixture
def repo(tmp_path):
    return BookRepository(str(tmp_path / "test.db"))


def _sample_book(**kwargs) -> Book:
    defaults = dict(isbn="9784000229819", title="テスト書籍", author="テスト著者")
    defaults.update(kwargs)
    return Book(**defaults)


class TestCreate:
    def test_create_returns_book_with_id(self, repo):
        book = repo.create(_sample_book())
        assert book.id is not None
        assert book.id > 0

    def test_create_stores_all_fields(self, repo):
        book = repo.create(
            _sample_book(
                publisher="テスト出版",
                published_year=2024,
                genre="技術",
                shelf_location="A-01",
                memo="備考",
            )
        )
        found = repo.find_by_id(book.id)
        assert found.publisher == "テスト出版"
        assert found.published_year == 2024
        assert found.genre == "技術"
        assert found.shelf_location == "A-01"
        assert found.memo == "備考"

    def test_duplicate_isbn_raises(self, repo):
        repo.create(_sample_book())
        import sqlite3
        with pytest.raises(sqlite3.IntegrityError):
            repo.create(_sample_book())


class TestFindByIsbn:
    def test_find_existing(self, repo):
        repo.create(_sample_book())
        found = repo.find_by_isbn("9784000229819")
        assert found is not None
        assert found.title == "テスト書籍"

    def test_find_nonexistent_returns_none(self, repo):
        assert repo.find_by_isbn("9999999999999") is None

    def test_deleted_book_not_found(self, repo):
        book = repo.create(_sample_book())
        repo.soft_delete(book.id)
        assert repo.find_by_isbn("9784000229819") is None


class TestSearch:
    def test_search_by_title_keyword(self, repo):
        repo.create(_sample_book(title="Python入門"))
        repo.create(_sample_book(isbn="9784003101803", title="Java応用"))
        results = repo.search(keyword="Python")
        assert len(results) == 1
        assert results[0].title == "Python入門"

    def test_search_by_genre(self, repo):
        repo.create(_sample_book(genre="技術"))
        repo.create(_sample_book(isbn="9784003101803", title="小説A", genre="小説"))
        results = repo.search(genre="技術")
        assert len(results) == 1

    def test_search_empty_returns_all(self, repo):
        repo.create(_sample_book())
        repo.create(_sample_book(isbn="9784003101803", title="別の本"))
        assert len(repo.search()) == 2


class TestUpdate:
    def test_update_changes_fields(self, repo):
        book = repo.create(_sample_book())
        book.title = "更新後タイトル"
        book.shelf_location = "B-99"
        repo.update(book)
        found = repo.find_by_id(book.id)
        assert found.title == "更新後タイトル"
        assert found.shelf_location == "B-99"


class TestSoftDelete:
    def test_soft_delete_hides_from_find(self, repo):
        book = repo.create(_sample_book())
        repo.soft_delete(book.id)
        assert repo.find_by_id(book.id) is None

    def test_find_all_excludes_deleted(self, repo):
        book = repo.create(_sample_book())
        repo.soft_delete(book.id)
        assert len(repo.find_all()) == 0
