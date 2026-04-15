from __future__ import annotations

import click

from src.models.book import Book
from src.services.book_service import BookService


def run_search(service: BookService) -> None:
    click.echo("=== 書籍検索 ===")
    keyword = click.prompt("キーワード（タイトル / 著者 / ISBN、空白で全件）", default="").strip()
    genre = click.prompt("ジャンルフィルタ（任意）", default="").strip()
    year_str = click.prompt("出版年フィルタ（任意）", default="").strip()

    year: int | None = None
    if year_str:
        try:
            year = int(year_str)
        except ValueError:
            click.secho("出版年は数値で入力してください。無視します。", fg="yellow")

    books = service.search(keyword=keyword, genre=genre, year=year)

    if not books:
        click.echo("該当する書籍が見つかりませんでした。")
        return

    click.echo(f"\n{len(books)} 件見つかりました。\n")
    _print_table(books)


def run_list(service: BookService) -> None:
    books = service.find_all()
    if not books:
        click.echo("登録されている書籍はありません。")
        return
    click.echo(f"\n全 {len(books)} 件\n")
    _print_table(books)


def _print_table(books: list[Book]) -> None:
    header = f"{'ID':>4}  {'ISBN':<15}  {'タイトル':<30}  {'著者':<18}  {'出版社':<12}  {'年':>4}  棚"
    click.echo(header)
    click.echo("-" * len(header))
    for b in books:
        isbn_str = (b.isbn or "")[:15]
        title_str = (b.title or "")[:30]
        author_str = (b.author or "—")[:18]
        pub_str = (b.publisher or "—")[:12]
        year_str = str(b.published_year) if b.published_year else "—"
        shelf_str = b.shelf_location or "—"
        click.echo(
            f"{b.id:>4}  {isbn_str:<15}  {title_str:<30}  {author_str:<18}  {pub_str:<12}  {year_str:>4}  {shelf_str}"
        )
