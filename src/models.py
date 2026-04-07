# 「何を処理するか」ではなく「何のデータが流れるか」から設計するのが一番きれいかもしれない
import datetime
import enum

# 論文1本をそのまま表現するクラス
class Paper:
    def __init__(self, title: str, authors: list[str], url: str, abstract: str, published_at: datetime.datetime, arxiv_id: str):
        self.title = title
        self.authors = authors
        self.url = url
        self.abstract = abstract
        self.published_at = published_at
        self.arxiv_id = arxiv_id

# キーワード判定の結果を持つクラス
class FilterResult:
    def __init__(self, matched_primary_keywords: list[str], score: int, passed: bool, matched_scoring_keywords: list[str]):
        self.matched_primary_keywords = matched_primary_keywords
        self.score = score
        self.passed = passed
        self.matched_scoring_keywords = matched_scoring_keywords

class Category(enum.Enum):
    EXPERIMENT = "実験向き"
    THEORY = "純粋理論"
    NUMERICAL = "数値計算"

class Importance(enum.Enum):
    HIGH = "A"
    MEDIUM = "B"
    LOW = "C"

# Gemini の出力をそのまま受けるためのクラス
# LLM 出力は壊れる前提で設計する
class Summary:
    def __init__(self, core_question: str, novelty: str, stabilizer_connection: str, category: Category, importance: Importance, one_line: str):
        self.core_question = core_question
        self.novelty = novelty
        self.stabilizer_connection = stabilizer_connection
        self.category = category
        self.importance = importance
        self.one_line = one_line

class Status(enum.Enum):
    NEW = "未読"
    READING = "要精読"
    ARCHIVED = "読了"

# Notion 用の統合クラス
class NotionRecord:
    def __init__(self, paper: Paper, filter_result: FilterResult, summary: Summary, status: Status = Status.NEW):
        self.paper = paper
        self.filter_result = filter_result
        self.summary = summary
        self.status = status
