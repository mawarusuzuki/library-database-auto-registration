from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Generator

from src.models.book import Book

DDL = """
CREATE TABLE IF NOT EXISTS books (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn            TEXT,
    title           TEXT    NOT NULL,
    author          TEXT,
    publisher       TEXT,
    published_year  INTEGER,
    genre           TEXT,
    shelf_location  TEXT,
    memo            TEXT,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    deleted_at      TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_books_isbn
    ON books (isbn) WHERE isbn IS NOT NULL AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_books_title  ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books (author);
"""


class BookRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(DDL)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _row_to_book(row: sqlite3.Row) -> Book:
        return Book(
            id=row["id"],
            isbn=row["isbn"],
            title=row["title"],
            author=row["author"],
            publisher=row["publisher"],
            published_year=row["published_year"],
            genre=row["genre"],
            shelf_location=row["shelf_location"],
            memo=row["memo"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            deleted_at=row["deleted_at"],
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(self, book: Book) -> Book:
        sql = """
            INSERT INTO books
                (isbn, title, author, publisher, published_year,
                 genre, shelf_location, memo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._connect() as conn:
            cur = conn.execute(
                sql,
                (
                    book.isbn,
                    book.title,
                    book.author,
                    book.publisher,
                    book.published_year,
                    book.genre,
                    book.shelf_location,
                    book.memo,
                ),
            )
            book.id = cur.lastrowid
        return book

    def find_by_id(self, book_id: int) -> Book | None:
        sql = "SELECT * FROM books WHERE id = ? AND deleted_at IS NULL"
        with self._connect() as conn:
            row = conn.execute(sql, (book_id,)).fetchone()
        return self._row_to_book(row) if row else None

    def find_by_isbn(self, isbn: str) -> Book | None:
        sql = "SELECT * FROM books WHERE isbn = ? AND deleted_at IS NULL"
        with self._connect() as conn:
            row = conn.execute(sql, (isbn,)).fetchone()
        return self._row_to_book(row) if row else None

    def search(
        self,
        keyword: str = "",
        genre: str = "",
        year: int | None = None,
    ) -> list[Book]:
        conditions = ["deleted_at IS NULL"]
        params: list = []

        if keyword:
            conditions.append("(title LIKE ? OR author LIKE ? OR isbn = ?)")
            like = f"%{keyword}%"
            params.extend([like, like, keyword])
        if genre:
            conditions.append("genre = ?")
            params.append(genre)
        if year is not None:
            conditions.append("published_year = ?")
            params.append(year)

        sql = f"SELECT * FROM books WHERE {' AND '.join(conditions)} ORDER BY id"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_book(r) for r in rows]

    def find_all(self) -> list[Book]:
        sql = "SELECT * FROM books WHERE deleted_at IS NULL ORDER BY id"
        with self._connect() as conn:
            rows = conn.execute(sql).fetchall()
        return [self._row_to_book(r) for r in rows]

    def update(self, book: Book) -> Book:
        sql = """
            UPDATE books SET
                isbn           = ?,
                title          = ?,
                author         = ?,
                publisher      = ?,
                published_year = ?,
                genre          = ?,
                shelf_location = ?,
                memo           = ?,
                updated_at     = datetime('now', 'localtime')
            WHERE id = ? AND deleted_at IS NULL
        """
        with self._connect() as conn:
            conn.execute(
                sql,
                (
                    book.isbn,
                    book.title,
                    book.author,
                    book.publisher,
                    book.published_year,
                    book.genre,
                    book.shelf_location,
                    book.memo,
                    book.id,
                ),
            )
        return book

    def soft_delete(self, book_id: int) -> None:
        sql = """
            UPDATE books
            SET deleted_at = datetime('now', 'localtime'),
                updated_at = datetime('now', 'localtime')
            WHERE id = ? AND deleted_at IS NULL
        """
        with self._connect() as conn:
            conn.execute(sql, (book_id,))
