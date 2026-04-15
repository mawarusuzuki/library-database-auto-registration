from __future__ import annotations

import logging
import sys

from src.api.google_books_client import GoogleBooksClient
from src.api.notion_client import NotionClient
from src.api.open_library_client import OpenLibraryClient
from src.config import Config
from src.parsers.amazon_parser import AmazonParser
from src.services.cover_fetcher import CoverFetcher
from src.services.register_service import RegisterService
from src.services.type_classifier import TypeClassifier


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _build_service() -> RegisterService:
    if not Config.NOTION_TOKEN:
        print("[エラー] NOTION_TOKEN が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)

    notion = NotionClient(
        token=Config.NOTION_TOKEN,
        database_id=Config.NOTION_DATABASE_ID,
    )
    google = GoogleBooksClient(
        api_key=Config.GOOGLE_BOOKS_API_KEY,
        timeout=Config.API_TIMEOUT_SEC,
    )
    open_library = OpenLibraryClient(timeout=Config.API_TIMEOUT_SEC)

    return RegisterService(
        notion=notion,
        parser=AmazonParser(),
        cover_fetcher=CoverFetcher(google, open_library),
        classifier=TypeClassifier(),
    )


def main() -> None:
    _setup_logging()

    if len(sys.argv) < 2:
        print("使い方: python -m src.main <Amazon注文履歴HTMLファイルパス>")
        print("例:     python -m src.main orders.html")
        sys.exit(1)

    html_path = sys.argv[1]
    service = _build_service()

    print(f"\n--- 書庫DB 自動登録 ---")
    print(f"対象ファイル: {html_path}\n")

    result = service.run(html_path)

    print(f"\n--- 完了 ---")
    print(f"  登録成功  : {result.success} 件")
    print(f"  スキップ  : {result.skipped} 件（登録済み）")
    print(f"  エラー    : {result.errors} 件")

    if result.error_details:
        print("\nエラー詳細:")
        for d in result.error_details:
            print(f"  - {d}")


if __name__ == "__main__":
    main()
