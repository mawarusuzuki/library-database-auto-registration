from __future__ import annotations

import click

from src.models.book import Book
from src.services.book_service import BookService, DuplicateIsbnError, InvalidIsbnError


def run_register(service: BookService) -> None:
    click.echo("=== 書籍登録 ===")
    mode = click.prompt(
        "登録方法を選択してください",
        type=click.Choice(["isbn", "manual"], case_sensitive=False),
        default="isbn",
    )

    if mode == "isbn":
        _register_by_isbn(service)
    else:
        _register_manual(service)


def _register_by_isbn(service: BookService) -> None:
    isbn = click.prompt("ISBN（13桁 or 10桁）").strip()

    try:
        book = service.register_by_isbn(isbn, overwrite=False)
        _print_book(book)
        click.secho("登録完了！", fg="green")
    except InvalidIsbnError as e:
        click.secho(f"[エラー] {e}", fg="red")
    except DuplicateIsbnError:
        if click.confirm("この ISBN は既に登録されています。上書きしますか？"):
            try:
                book = service.register_by_isbn(isbn, overwrite=True)
                _print_book(book)
                click.secho("上書き更新しました。", fg="yellow")
            except ValueError as e:
                click.secho(f"[エラー] {e}", fg="red")
        else:
            click.echo("キャンセルしました。")
    except ValueError as e:
        if click.confirm(f"[警告] {e}\n手動入力に切り替えますか？"):
            _register_manual(service, isbn=isbn)


def _register_manual(service: BookService, isbn: str = "") -> None:
    click.echo("--- 手動入力 ---")
    if not isbn:
        isbn = click.prompt("ISBN（任意、不明な場合は Enter をスキップ）", default="").strip()
    title = click.prompt("タイトル").strip()
    author = click.prompt("著者（任意）", default="").strip() or None
    publisher = click.prompt("出版社（任意）", default="").strip() or None
    year_str = click.prompt("出版年（任意、西暦4桁）", default="").strip()
    genre = click.prompt("ジャンル（任意）", default="").strip() or None
    shelf = click.prompt("棚番号（任意）", default="").strip() or None
    memo = click.prompt("備考（任意）", default="").strip() or None

    year: int | None = None
    if year_str:
        try:
            year = int(year_str)
        except ValueError:
            click.secho("出版年は数値で入力してください。無視します。", fg="yellow")

    book = Book(
        isbn=isbn or None,
        title=title,
        author=author,
        publisher=publisher,
        published_year=year,
        genre=genre,
        shelf_location=shelf,
        memo=memo,
    )

    try:
        result = service.register_manual(book)
        _print_book(result)
        click.secho("登録完了！", fg="green")
    except (DuplicateIsbnError, InvalidIsbnError) as e:
        click.secho(f"[エラー] {e}", fg="red")


def _print_book(book: Book) -> None:
    click.echo(f"\n  ID      : {book.id}")
    click.echo(f"  ISBN    : {book.isbn or '—'}")
    click.echo(f"  タイトル: {book.title}")
    click.echo(f"  著者    : {book.author or '—'}")
    click.echo(f"  出版社  : {book.publisher or '—'}")
    click.echo(f"  出版年  : {book.published_year or '—'}")
    click.echo(f"  ジャンル: {book.genre or '—'}")
    click.echo(f"  棚番号  : {book.shelf_location or '—'}")
