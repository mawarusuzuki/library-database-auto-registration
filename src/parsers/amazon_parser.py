from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.models.book import KindleBook

# ASIN は10桁の英数字（Kindle は B から始まることが多い）
_ASIN_RE = re.compile(r"/(?:dp|gp/product)/([A-Z0-9]{10})", re.IGNORECASE)
_KINDLE_WORDS = ("kindle", "kindle版", "デジタル")
_AUTHOR_RE = re.compile(
    r"([^,\n]+?)\s*(?:著|訳|翻訳|編著|監修|イラスト|画|著者|原作|著/訳|著・訳)",
    re.IGNORECASE,
)


def _normalize_url(asin: str) -> str:
    return f"https://www.amazon.co.jp/dp/{asin.upper()}"


class AmazonParser:
    """Amazon.co.jp 注文履歴の保存 HTML から Kindle 書籍を抽出する。"""

    def parse(self, html_path: str) -> list[KindleBook]:
        path = Path(html_path)
        if not path.exists():
            raise FileNotFoundError(f"HTML ファイルが見つかりません: {html_path}")

        html = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "lxml")

        books: dict[str, KindleBook] = {}

        for a_tag in soup.find_all("a", href=True):
            href: str = a_tag["href"]
            asin = self._extract_asin(href)
            if not asin:
                continue

            # 周辺テキストを収集して Kindle 判定
            surrounding = self._surrounding_text(a_tag)
            if not self._is_kindle(href, surrounding):
                continue

            # タイトル取得
            title = a_tag.get_text(strip=True)
            title = self._clean_title(title)
            if not title:
                continue

            # 著者取得
            author = self._extract_author(a_tag)

            asin_upper = asin.upper()
            if asin_upper not in books:
                books[asin_upper] = KindleBook(
                    asin=asin_upper,
                    title=title,
                    amazon_url=_normalize_url(asin_upper),
                    author=author,
                )

        return list(books.values())

    # ------------------------------------------------------------------

    def _extract_asin(self, href: str) -> str | None:
        m = _ASIN_RE.search(href)
        return m.group(1) if m else None

    def _is_kindle(self, href: str, surrounding: str) -> bool:
        lower = surrounding.lower()
        if any(w in lower for w in _KINDLE_WORDS):
            return True
        # Kindle ASIN は B から始まることが多い（完全一致ではないが有力なヒント）
        asin = self._extract_asin(href)
        if asin and asin.upper().startswith("B"):
            return True
        return False

    def _surrounding_text(self, tag) -> str:
        """タグ自身・親・兄弟要素のテキストを結合して返す。"""
        texts = [tag.get_text(" ", strip=True)]
        parent = tag.parent
        if parent:
            texts.append(parent.get_text(" ", strip=True))
            grandparent = parent.parent
            if grandparent:
                texts.append(grandparent.get_text(" ", strip=True))
        return " ".join(texts)

    def _clean_title(self, title: str) -> str:
        # 「Kindle版」などの余分な文字列を除去
        title = re.sub(r"\s*[\(\[（【]?Kindle[版版]?[\)\]）】]?\s*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip()
        return title

    def _extract_author(self, title_tag) -> str | None:
        """タイトルリンクの近傍から著者名を取得する。"""
        # 兄弟・親の兄弟要素を探す
        candidates = []
        parent = title_tag.parent
        for _ in range(3):
            if parent is None:
                break
            for sibling in parent.next_siblings:
                text = sibling.get_text(" ", strip=True) if hasattr(sibling, "get_text") else str(sibling).strip()
                if text:
                    candidates.append(text)
            parent = parent.parent

        for text in candidates:
            m = _AUTHOR_RE.search(text)
            if m:
                return m.group(1).strip()

        # シンプルなフォールバック：「著者：〇〇」パターン
        for text in candidates:
            if "著者" in text or "作者" in text:
                parts = re.split(r"[：:]\s*", text, maxsplit=1)
                if len(parts) == 2:
                    return parts[1].strip()

        return None
