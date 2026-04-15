from __future__ import annotations

import logging
import sys

import click

from src.api.google_books_client import GoogleBooksClient
from src.api.ndl_client import NdlClient
from src.commands.export_command import run_export
from src.commands.import_command import run_import
from src.commands.register_command import run_register
from src.commands.search_command import run_list, run_search
from src.config import Config
from src.repositories.book_repository import BookRepository
from src.services.book_service import BookService


def _setup_logging() -> None:
    Config.ensure_log_dir()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(Config.LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _build_service() -> BookService:
    repo = BookRepository(Config.DB_PATH)

    clients = []
    for name in Config.API_PRIORITY:
        if name == "ndl":
            clients.append(NdlClient())
        elif name == "google_books":
            clients.append(GoogleBooksClient(api_key=Config.GOOGLE_BOOKS_API_KEY))

    return BookService(repo=repo, api_clients=clients)


@click.group()
def cli() -> None:
    """書庫DB自動登録スクリプト"""


@cli.command("register")
def cmd_register() -> None:
    """書籍を登録する（ISBN / 手動入力）"""
    _setup_logging()
    service = _build_service()
    run_register(service)


@cli.command("import")
def cmd_import() -> None:
    """CSV ファイルから書籍を一括登録する"""
    _setup_logging()
    service = _build_service()
    run_import(service)


@cli.command("search")
def cmd_search() -> None:
    """書籍を検索する"""
    _setup_logging()
    service = _build_service()
    run_search(service)


@cli.command("list")
def cmd_list() -> None:
    """登録済み書籍を一覧表示する"""
    _setup_logging()
    service = _build_service()
    run_list(service)


@cli.command("export")
def cmd_export() -> None:
    """登録済み書籍を CSV に出力する"""
    _setup_logging()
    service = _build_service()
    run_export(service)


if __name__ == "__main__":
    cli()
