# 設計書 — 書庫DB自動登録スクリプト

| 項目 | 内容 |
|---|---|
| ドキュメントバージョン | 1.0.0 |
| 作成日 | 2026-04-15 |
| ステータス | ドラフト |

---

## 1. アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────┐
│                   CLI エントリポイント                    │
│                     src/main.py                          │
└───────────────┬────────────────────┬────────────────────┘
                │                    │
        ┌───────▼──────┐    ┌────────▼────────┐
        │  RegisterCmd │    │   SearchCmd     │
        │  ImportCmd   │    │   ExportCmd     │
        └───────┬──────┘    └────────┬────────┘
                │                    │
        ┌───────▼──────────────────▼────────┐
        │           BookService              │
        │  (登録・検索・更新・削除ロジック)   │
        └────┬───────────────────┬──────────┘
             │                   │
    ┌────────▼───────┐  ┌────────▼────────┐
    │  BookRepository│  │   ApiClient     │
    │  (SQLite CRUD) │  │ (NDL / Google)  │
    └────────┬───────┘  └─────────────────┘
             │
    ┌────────▼───────┐
    │   SQLite DB    │
    │  library.db    │
    └────────────────┘
```

### レイヤー責務

| レイヤー | モジュール | 責務 |
|---|---|---|
| CLI | `src/main.py`, `src/commands/` | コマンド解析・入出力表示 |
| サービス | `src/services/book_service.py` | ビジネスロジック・バリデーション |
| リポジトリ | `src/repositories/book_repository.py` | DB アクセスの抽象化 |
| API クライアント | `src/api/ndl_client.py`, `src/api/google_books_client.py` | 外部 API 通信 |
| モデル | `src/models/book.py` | データクラス定義 |

---

## 2. ディレクトリ構成（実装時）

```
.
├── README.md
├── docs/
│   ├── spec.md
│   └── design.md
├── src/
│   ├── main.py                        # エントリポイント
│   ├── config.py                      # 設定読み込み
│   ├── models/
│   │   └── book.py                    # Book データクラス
│   ├── commands/
│   │   ├── register_command.py        # 登録コマンド
│   │   ├── import_command.py          # CSV インポートコマンド
│   │   ├── search_command.py          # 検索コマンド
│   │   └── export_command.py          # CSV エクスポートコマンド
│   ├── services/
│   │   └── book_service.py            # ビジネスロジック
│   ├── repositories/
│   │   └── book_repository.py         # SQLite リポジトリ
│   └── api/
│       ├── base_client.py             # API クライアント基底クラス
│       ├── ndl_client.py              # 国立国会図書館 API
│       └── google_books_client.py     # Google Books API
├── tests/
│   ├── test_book_service.py
│   ├── test_book_repository.py
│   └── test_api_clients.py
├── logs/                              # 実行時に自動生成
│   └── register.log
├── .env.example                       # 環境変数サンプル
├── requirements.txt
└── pyproject.toml
```

---

## 3. データベース設計

### 3.1 ER 図

```
┌──────────────────────────┐
│          books            │
├──────────────────────────┤
│ id             INTEGER PK│
│ isbn           TEXT      │
│ title          TEXT  NN  │
│ author         TEXT      │
│ publisher      TEXT      │
│ published_year INTEGER   │
│ genre          TEXT      │
│ shelf_location TEXT      │
│ memo           TEXT      │
│ created_at     TEXT  NN  │
│ updated_at     TEXT  NN  │
│ deleted_at     TEXT      │ ← NULL = 有効, 値あり = 論理削除
└──────────────────────────┘
```

### 3.2 DDL

```sql
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

CREATE INDEX IF NOT EXISTS idx_books_title   ON books (title);
CREATE INDEX IF NOT EXISTS idx_books_author  ON books (author);
```

### 3.3 カラム仕様

| カラム | 型 | 制約 | 説明 |
|---|---|---|---|
| id | INTEGER | PK / AUTOINCREMENT | 内部 ID |
| isbn | TEXT | UNIQUE（有効レコードのみ） | ISBN-13 正規化形式（ハイフンなし） |
| title | TEXT | NOT NULL | 書名 |
| author | TEXT | - | 著者（複数は `/` 区切り） |
| publisher | TEXT | - | 出版社 |
| published_year | INTEGER | - | 出版年（西暦 4 桁） |
| genre | TEXT | - | ジャンル |
| shelf_location | TEXT | - | 棚番号・保管場所 |
| memo | TEXT | - | 自由記述備考 |
| created_at | TEXT | NOT NULL | 登録日時（ISO 8601） |
| updated_at | TEXT | NOT NULL | 最終更新日時（ISO 8601） |
| deleted_at | TEXT | NULL = 有効 | 論理削除日時（ISO 8601） |

---

## 4. クラス設計

### 4.1 Book データクラス（`src/models/book.py`）

```python
@dataclass
class Book:
    title: str
    id: int | None = None
    isbn: str | None = None
    author: str | None = None
    publisher: str | None = None
    published_year: int | None = None
    genre: str | None = None
    shelf_location: str | None = None
    memo: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    deleted_at: str | None = None
```

### 4.2 BookRepository（`src/repositories/book_repository.py`）

```python
class BookRepository:
    def __init__(self, db_path: str) -> None: ...

    def create(self, book: Book) -> Book: ...
    def find_by_id(self, book_id: int) -> Book | None: ...
    def find_by_isbn(self, isbn: str) -> Book | None: ...
    def search(self, keyword: str = "", genre: str = "",
               year: int | None = None) -> list[Book]: ...
    def update(self, book: Book) -> Book: ...
    def soft_delete(self, book_id: int) -> None: ...
    def find_all(self) -> list[Book]: ...
```

### 4.3 ApiClient 基底クラス（`src/api/base_client.py`）

```python
class BaseApiClient(ABC):
    TIMEOUT_SEC: int = 5
    MAX_RETRY: int = 3

    @abstractmethod
    def fetch_by_isbn(self, isbn: str) -> Book | None: ...

    def _request_with_retry(self, url: str, params: dict) -> dict: ...
```

### 4.4 BookService（`src/services/book_service.py`）

```python
class BookService:
    def __init__(self, repo: BookRepository,
                 api_clients: list[BaseApiClient]) -> None: ...

    def register_by_isbn(self, isbn: str,
                         overwrite: bool = False) -> Book: ...
    def register_manual(self, book: Book) -> Book: ...
    def import_csv(self, csv_path: str) -> ImportResult: ...
    def search(self, keyword: str = "", **filters) -> list[Book]: ...
    def update(self, book: Book) -> Book: ...
    def delete(self, book_id: int) -> None: ...
    def export_csv(self, output_path: str,
                   books: list[Book] | None = None) -> None: ...
```

---

## 5. 処理フロー

### 5.1 ISBN 登録フロー

```
ユーザー入力 (ISBN)
    │
    ▼
ISBN バリデーション
    │ NG → エラーメッセージ表示 → 終了
    │ OK
    ▼
DB に同 ISBN が存在するか？
    │ YES → 上書き確認プロンプト
    │           │ NO  → 終了
    │           │ YES → 更新処理へ
    │ NO
    ▼
NDL API で書誌情報取得
    │ 取得失敗 → Google Books API へフォールバック
    │               │ 取得失敗 → 手動入力モードへ移行
    │               │ 取得成功 ─┐
    │ 取得成功 ────────────────┘
    ▼
Book オブジェクト生成
    ▼
DB へ保存（INSERT or UPDATE）
    ▼
操作ログ記録
    ▼
登録完了メッセージ表示
```

### 5.2 CSV 一括インポートフロー

```
CSV ファイルパス入力
    ▼
ファイル存在・読み取り権限チェック
    │ NG → エラー表示 → 終了
    ▼
CSV 行ごとにループ
    ├─ ヘッダ行 → スキップ
    ├─ フォーマット不正行 → エラーログ記録・カウント → 次行へ
    └─ 正常行
          ▼
         ISBN あり → DB 重複チェック
         │             │ 重複 → WARN ログ・スキップカウント → 次行へ
         │             │ 新規 → API 書誌情報取得（任意）
         │
         ISBN なし → タイトル必須チェック
                       │ NG → エラーカウント → 次行へ
                       │ OK → Book オブジェクト生成 → DB 保存
    ▼
全行処理完了
    ▼
インポート結果レポート出力（成功/スキップ/エラー件数）
```

---

## 6. 外部 API 仕様

### 6.1 国立国会図書館サーチ API（NDL SRU）

| 項目 | 内容 |
|---|---|
| ベース URL | `https://ndlsearch.ndl.go.jp/api/sru` |
| 認証 | 不要（無料） |
| リクエスト形式 | GET クエリパラメータ |
| レスポンス形式 | XML（Dublin Core） |
| レート制限 | 公式未明記（1 req/s を目安に実装） |

主要クエリパラメータ：

```
operation=searchRetrieve
version=1.2
recordSchema=dcndl
query=isbn="{isbn}"
maximumRecords=1
```

### 6.2 Google Books API

| 項目 | 内容 |
|---|---|
| ベース URL | `https://www.googleapis.com/books/v1/volumes` |
| 認証 | API キー（環境変数 `GOOGLE_BOOKS_API_KEY`） |
| リクエスト形式 | GET クエリパラメータ |
| レスポンス形式 | JSON |
| レート制限 | 1,000 req/日（無料枠） |

主要クエリパラメータ：

```
q=isbn:{isbn}
key={GOOGLE_BOOKS_API_KEY}
maxResults=1
```

---

## 7. 設定ファイル

### `.env.example`

```dotenv
# Google Books API キー（オプション：NDL で取得できない場合のフォールバック用）
GOOGLE_BOOKS_API_KEY=

# DB ファイルパス（デフォルト: library.db）
DB_PATH=library.db

# ログファイルパス（デフォルト: logs/register.log）
LOG_PATH=logs/register.log

# API タイムアウト秒（デフォルト: 5）
API_TIMEOUT_SEC=5

# 使用する API の優先順位（カンマ区切り: ndl, google_books）
API_PRIORITY=ndl,google_books
```

---

## 8. エラーコード一覧

| コード | 定数名 | 説明 |
|---|---|---|
| E001 | `ERR_INVALID_ISBN` | ISBN フォーマット不正 |
| E002 | `ERR_DUPLICATE_ISBN` | ISBN が既に登録済み |
| E003 | `ERR_API_TIMEOUT` | 外部 API タイムアウト |
| E004 | `ERR_API_NOT_FOUND` | 外部 API に書誌情報なし |
| E005 | `ERR_DB_WRITE` | DB 書き込み失敗 |
| E006 | `ERR_CSV_FORMAT` | CSV フォーマット不正 |
| E007 | `ERR_FILE_NOT_FOUND` | 指定ファイルが存在しない |

---

## 9. 依存ライブラリ

| ライブラリ | バージョン | 用途 |
|---|---|---|
| `requests` | >=2.31 | HTTP クライアント |
| `python-dotenv` | >=1.0 | .env ファイル読み込み |
| `click` | >=8.1 | CLI フレームワーク |

> 標準ライブラリ（`sqlite3`, `csv`, `xml.etree.ElementTree`, `logging`, `dataclasses`）は追加インストール不要。

---

## 10. テスト方針

| テスト種別 | ツール | 対象 |
|---|---|---|
| 単体テスト | `pytest` | `BookService`, `BookRepository`, `ApiClient` |
| モックテスト | `pytest-mock` / `responses` | 外部 API（実通信しない） |
| 統合テスト | `pytest` | インポート→登録→検索の一連フロー（インメモリ SQLite 使用） |

カバレッジ目標：80% 以上
