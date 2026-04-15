from __future__ import annotations

_RULES: list[tuple[str, list[str]]] = [
    ("技術", [
        "プログラム", "プログラミング", "python", "java", "javascript", "typescript",
        "aws", "gcp", "azure", "インフラ", "アルゴリズム", "エンジニア", "linux",
        "docker", "kubernetes", "クラウド", "データベース", "ネットワーク", "セキュリティ",
        "機械学習", "深層学習", "ディープラーニング", "ai", "データサイエンス",
        "web開発", "フロントエンド", "バックエンド", "devops", "git", "sql",
        "rust", "go言語", "swift", "kotlin", "c言語", "c++",
    ]),
    ("教養", [
        "歴史", "哲学", "経済学", "科学", "数学", "物理", "化学", "心理学",
        "社会学", "文化", "地理", "生物学", "宇宙", "倫理", "論理学",
        "認知", "脳科学", "進化", "統計学", "行動経済",
    ]),
    ("自己啓発", [
        "自己啓発", "習慣", "成功", "リーダーシップ", "マネジメント", "仕事術",
        "思考法", "時間管理", "コミュニケーション", "メンタル", "モチベーション",
        "生産性", "ストレス", "マインドフルネス", "キャリア",
    ]),
    ("Novel", [
        "小説", "文庫", "物語", "ミステリ", "ファンタジー", r"\bsf\b", "ラノベ",
        "ライトノベル", "恋愛", "推理", "サスペンス", "ホラー",
    ]),
    ("Comic", [
        "漫画", "マンガ", "コミック", r"\d+巻", r"（\d+）", "コミカライズ",
    ]),
]


class TypeClassifier:
    def classify(self, title: str, author: str | None = None) -> str | None:
        text = (title + " " + (author or "")).lower()

        for type_name, keywords in _RULES:
            for kw in keywords:
                import re
                if re.search(kw, text, re.IGNORECASE):
                    return type_name

        return None
