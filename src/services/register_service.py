from __future__ import annotations

import logging

from src.models.book import KindleBook, RegisterResult
from src.api.notion_client import NotionClient
from src.parsers.amazon_parser import AmazonParser
from src.services.cover_fetcher import CoverFetcher
from src.services.type_classifier import TypeClassifier

logger = logging.getLogger(__name__)


class RegisterService:
    def __init__(
        self,
        notion: NotionClient,
        parser: AmazonParser,
        cover_fetcher: CoverFetcher,
        classifier: TypeClassifier,
    ) -> None:
        self._notion = notion
        self._parser = parser
        self._cover_fetcher = cover_fetcher
        self._classifier = classifier

    def run(self, html_path: str) -> RegisterResult:
        result = RegisterResult()

        # 1. Amazon HTML 解析
        books = self._parser.parse(html_path)
        if not books:
            logger.warning("Kindle 書籍が見つかりませんでした: %s", html_path)
            return result

        print(f"Kindle 書籍を {len(books)} 件検出しました。")

        # 2. 登録済み URL を取得して未登録書籍を抽出
        print("Notion 書庫DB を確認中...")
        registered_urls = self._notion.get_registered_urls()
        new_books = [
            b for b in books
            if b.amazon_url.rstrip("/") not in registered_urls
        ]
        result.skipped = len(books) - len(new_books)

        if not new_books:
            print("新規登録する書籍はありませんでした。")
            return result

        print(f"新規登録対象: {len(new_books)} 件 / スキップ（登録済み）: {result.skipped} 件\n")

        # 3. 各書籍を処理して登録
        for i, book in enumerate(new_books, start=1):
            print(f"[{i}/{len(new_books)}] {book.title}")

            # 書影取得
            cover_url = self._cover_fetcher.fetch(book.title, book.author)
            book.cover_url = cover_url

            # Type 分類
            book.type_estimate = self._classifier.classify(book.title, book.author)
            if book.type_estimate:
                print(f"  Type: {book.type_estimate}")

            # Notion 登録
            try:
                self._notion.register_book(book)
                result.success += 1
                print(f"  ✓ 登録完了")
            except Exception as e:
                msg = f"{book.title} ({book.asin}): {e}"
                logger.error("登録失敗: %s", msg)
                result.errors += 1
                result.error_details.append(msg)
                print(f"  ✗ 登録失敗: {e}")

        return result
