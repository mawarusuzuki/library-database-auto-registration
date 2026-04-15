# 書庫DB自動登録スクリプト

書籍情報をスキャンまたは入力し、データベースへ自動登録するスクリプトです。  
ISBN バーコードのスキャン・手動入力・CSV 一括インポートに対応し、外部 API（国立国会図書館 / Google Books）から書誌情報を自動取得してデータベースへ登録します。

## ドキュメント

| ドキュメント | 説明 |
|---|---|
| [仕様書](docs/spec.md) | 機能要件・非機能要件・画面仕様 |
| [設計書](docs/design.md) | アーキテクチャ・DB スキーマ・処理フロー |

---

## ローカルでの実行手順

### 必要なもの

- Python 3.10 以上
- インターネット接続（国立国会図書館 API 利用のため。オフライン時は手動入力で動作可能）

### 1. リポジトリを取得する

```bash
git clone https://github.com/mawarusuzuki/claudecode.git
cd claudecode
```

### 2. 仮想環境を作成・有効化する

```bash
# 仮想環境を作成
python -m venv .venv

# 有効化（Mac / Linux）
source .venv/bin/activate

# 有効化（Windows コマンドプロンプト）
.venv\Scripts\activate.bat

# 有効化（Windows PowerShell）
.venv\Scripts\Activate.ps1
```

> 仮想環境を有効化するとプロンプトの先頭に `(.venv)` が付きます。

### 3. 依存パッケージをインストールする

```bash
pip install -r requirements.txt
```

### 4. 設定ファイルを用意する（任意）

`.env.example` をコピーして `.env` を作成します。  
国立国会図書館 API は認証不要なので、最初は何も変更しなくても動きます。

```bash
# Mac / Linux
cp .env.example .env

# Windows
copy .env.example .env
```

Google Books API を使いたい場合（NDL で取得できなかった書籍のフォールバック用）は、  
`.env` を開いて `GOOGLE_BOOKS_API_KEY=` の後にキーを記入してください。

### 5. 動かしてみる

#### 書籍を登録する（ISBN 入力）

```bash
python -m src.main register
```

実行例：
```
=== 書籍登録 ===
登録方法を選択してください (isbn, manual) [isbn]: isbn
ISBN（13桁 or 10桁）: 9784003101803

  ID      : 1
  ISBN    : 9784003101803
  タイトル: 吾輩は猫である
  著者    : 夏目漱石
  出版社  : 岩波書店
  出版年  : 2004
  ジャンル: 小説
  棚番号  : —
登録完了！
```

#### 登録済み書籍を一覧表示する

```bash
python -m src.main list
```

#### キーワードで検索する

```bash
python -m src.main search
```

#### CSV ファイルから一括登録する

```bash
python -m src.main import
```

CSV のフォーマットは以下の通りです（`isbn` 以外は任意項目）：

```csv
isbn,title,author,publisher,published_year,genre,shelf_location,memo
9784000229819,方法序説,ルネ・デカルト,岩波書店,1997,哲学,A-01,
9784003101803,吾輩は猫である,夏目漱石,岩波書店,2004,小説,B-02,初版
```

#### 登録データを CSV に書き出す

```bash
python -m src.main export
```

### 6. テストを実行する

```bash
python -m pytest tests/ -v
```

---

## ディレクトリ構成

```
.
├── README.md
├── docs/
│   ├── spec.md                        # 仕様書
│   └── design.md                      # 設計書
├── src/
│   ├── main.py                        # エントリポイント
│   ├── config.py                      # 設定読み込み
│   ├── models/book.py                 # データクラス
│   ├── repositories/book_repository.py # SQLite CRUD
│   ├── api/                           # 外部 API クライアント
│   ├── services/book_service.py       # ビジネスロジック
│   └── commands/                      # CLI コマンド
├── tests/                             # ユニットテスト
├── .env.example                       # 環境変数サンプル
├── requirements.txt
└── pyproject.toml
```

> データベースファイル（`library.db`）とログ（`logs/`）は初回起動時に自動で作成されます。
