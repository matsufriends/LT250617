"""
設定ファイル - アプリケーション全体の設定を一元管理（定数版）
"""

import os
from typing import List
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

# ==============================================================================
# API関連の設定
# ==============================================================================

# OpenAI設定
OPENAI_MODEL = "gpt-4o"
OPENAI_MAX_TOKENS = 4000
OPENAI_TEMPERATURE = 0.7
OPENAI_FILTER_MAX_TOKENS = 1000
OPENAI_FILTER_TEMPERATURE = 0.3
OPENAI_SEARCH_MAX_TOKENS = 2000
OPENAI_SEARCH_TEMPERATURE = 0.1

# Google Custom Search API設定
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_CX = os.environ.get("GOOGLE_CX", "")

# ==============================================================================
# 検索関連の設定
# ==============================================================================

# Google検索設定
GOOGLE_RESULTS = 10  # 検索結果数を調整（20 → 10に減らして高速化）
GOOGLE_API_RESULTS = 5  # Google Custom Search API での取得件数（8 → 3に減らして高速化）
GOOGLE_DELAY = 10.0  # 遅延時間を増加（429エラー対策）
GOOGLE_PAGE_LIMIT = 4000  # ページ内容の取得文字数を増加（1000→5000）

# YouTube検索設定
YOUTUBE_MAX_URLS = 20
YOUTUBE_MAX_VIDEOS = 15
YOUTUBE_MAX_TRANSCRIPTS = 10
YOUTUBE_TRANSCRIPT_LIMIT = 3000
YOUTUBE_SEARCH_DELAY = 1.0

# ==============================================================================
# コレクター設定
# ==============================================================================

# Wikipedia設定
WIKIPEDIA_SUMMARY_LIMIT = 1000
WIKIPEDIA_FALLBACK_LIMIT = 500

# 共通設定
DEFAULT_DELAY = 2.0
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
RETRY_DELAY = 30.0

# ==============================================================================
# 処理関連の設定
# ==============================================================================

# サンプルフレーズ設定
SAMPLE_PHRASES_MAX = 20
SAMPLE_PHRASE_MIN_LENGTH = 3
SAMPLE_PHRASE_MAX_LENGTH = 60
SAMPLE_QUALITY_MIN_LENGTH = 3
SAMPLE_QUALITY_MAX_LENGTH = 100

# 表示設定
MAX_KEY_INFORMATION = 5
MAX_SAMPLE_PHRASES_DISPLAY = 15

# テキスト処理制限
CHATGPT_FILTER_TEXT_LIMIT = 3000

# ==============================================================================
# 検索エンジン固有の設定
# ==============================================================================

# Bing検索設定
BING_DEFAULT_DELAY = 4.0
BING_PATTERN_DELAY_MULTIPLIER = 2
BING_DEFAULT_RESULTS = 10  # 20から10に減らして高速化
BING_MAX_RESULTS = 20  # 50から20に減らして高速化
BING_MIN_TEXT_LENGTH_FOR_API = 50
BING_NAME_LENGTH_CHECK = 2
BING_YOUTUBE_RESULTS = 20
BING_API_TEXT_LIMIT = 2000
BING_MAX_SPEECH_PATTERNS = 10
BING_TEXT_LENGTH_CHECK = 200

# ChatGPT検索設定
CHATGPT_DEFAULT_DELAY = 1.0
CHATGPT_SEARCH_MAX_TOKENS = 2000
CHATGPT_MAX_QUOTES = 5
CHATGPT_MIN_QUOTE_LENGTH = 3
CHATGPT_MAX_PATTERNS = 10
CHATGPT_TOP_KEYWORDS = 3
CHATGPT_KEYWORD_MAX_TOKENS = 500
CHATGPT_MAX_KEYWORDS = 5

# Google検索設定（追加）
GOOGLE_FALLBACK_DELAY_MULTIPLIER = 4  # 429エラー対策で増加
GOOGLE_MIN_DELAY = 20.0  # 429エラー対策で増加
GOOGLE_URL_FETCH_DELAY = 3.0  # ページ取得間隔を増加
GOOGLE_FETCH_PAGE_CONTENT = True  # ページコンテンツ取得を有効化
GOOGLE_PAGE_DELAY_MULTIPLIER = 3  # ページ取得時の追加待機を増加
GOOGLE_YOUTUBE_DELAY_MULTIPLIER = 5  # YouTube検索時の追加待機を増加
GOOGLE_CX_DISPLAY_LENGTH = 10
GOOGLE_API_MAX_RESULTS_PER_REQUEST = 10
GOOGLE_FALLBACK_MAX_RETRIES = 2
GOOGLE_FALLBACK_RETRY_DELAY = 30  # リトライ時の待機を増加
GOOGLE_429_EXTRA_DELAY = 60.0  # 429エラー発生時の追加待機時間
GOOGLE_PATTERN_TIMEOUT = 90
GOOGLE_SEARCH_TIMEOUT = 60
GOOGLE_MIN_TEXT_LENGTH_FOR_API = 50
GOOGLE_YOUTUBE_API_RESULTS = 10

# ==============================================================================
# HTTPクライアント設定
# ==============================================================================

# HTTPクライアント基本設定
HTTP_DEFAULT_DELAY = 2.0
HTTP_DEFAULT_TIMEOUT = 10  # 15から10秒に減らしてハングを防止
HTTP_DEFAULT_MAX_RETRIES = 1  # 2から1に減らして高速化
HTTP_RETRY_WAIT_MULTIPLIER = 2
HTTP_TIMEOUT_WAIT_MULTIPLIER = 3
HTTP_CONNECTION_ERROR_WAIT_MULTIPLIER = 4
HTTP_SKIP_RETRY_STATUS_CODES = [404, 403, 406, 410, 503]

# ==============================================================================
# YouTube処理設定
# ==============================================================================

# YouTube表示設定
YOUTUBE_VIDEO_ID_DISPLAY_LENGTH = 11
YOUTUBE_PREVIEW_TEXT_LENGTH = 100
YOUTUBE_SAMPLE_DISPLAY_LIMIT = 5
YOUTUBE_MIN_SENTENCE_LENGTH = 1
YOUTUBE_MAX_SINGLE_CHAR_LENGTH = 3
YOUTUBE_MAX_PERIOD_COUNT = 3
YOUTUBE_FILTER_PHRASE_LIMIT = 10
YOUTUBE_ANALYSIS_TEXT_LIMIT = 3000
YOUTUBE_ANALYSIS_MAX_TOKENS = 800

# ==============================================================================
# プロンプト生成設定
# ==============================================================================

# プロンプト生成設定
PROMPT_MAX_WEB_SPEECH_PATTERNS = 10
PROMPT_TOP_WEB_RESULTS_FOR_RAW = 3
PROMPT_CONTENT_EXCERPT_LIMIT = 1000
PROMPT_RAW_CONTENT_DISPLAY_LIMIT = 2
PROMPT_FALLBACK_PATTERN_LIMIT = 5
PROMPT_FALLBACK_PHRASE_LIMIT = 5
PROMPT_INTRODUCTION_CHAR_LIMIT = 200
PROMPT_INTRODUCTION_MAX_TOKENS = 300
PROMPT_INTRODUCTION_TEMPERATURE = 0.8
PROMPT_POLICY_SAFE_TEMPERATURE = 0.3
PROMPT_MAX_CHARACTER_QUOTES = 30  # プロンプトに含める最大セリフ数

# ==============================================================================
# API処理設定
# ==============================================================================

# API処理設定
API_PROMPT_SLICE_LENGTH = 200
API_MAX_EXTRACTED_PATTERNS = 10
API_MAX_EXTRACTED_QUOTES = 10  # 1回のAPIコールで抽出する最大セリフ数
API_MIN_QUOTE_LENGTH = 5  # セリフの最小文字数

# ==============================================================================
# 表示フォーマット設定
# ==============================================================================

# 表示フォーマット
DISPLAY_SEPARATOR_LENGTH = 60
DISPLAY_EMOJI_REPEAT_COUNT = 20

# ==============================================================================
# 温度設定（OpenAI API）
# ==============================================================================

# 特殊な温度設定
SPEECH_PATTERN_EXTRACTION_TEMPERATURE = 0.1

# ==============================================================================
# HTTPステータスコード
# ==============================================================================

# HTTPステータスコード
HTTP_STATUS_OK = 200
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_NOT_ACCEPTABLE = 406
HTTP_STATUS_GONE = 410
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_SERVICE_UNAVAILABLE = 503

# ==============================================================================
# その他の定数
# ==============================================================================

# エラーメッセージの待機時間（時間）
ERROR_WAIT_TIME_HOURS_MIN = 1
ERROR_WAIT_TIME_HOURS_MAX = 2

# 並列処理設定
CONCURRENT_WORKERS = 3
COLLECTION_TIMEOUT_TOTAL = 180  # 全体のタイムアウト（秒）
COLLECTION_TIMEOUT_WIKIPEDIA = 30  # Wikipedia収集のタイムアウト（秒）
COLLECTION_TIMEOUT_WEB_SEARCH = 90  # Web検索収集のタイムアウト（秒）
COLLECTION_TIMEOUT_YOUTUBE = 120  # YouTube収集のタイムアウト（秒）

# User-Agent設定
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
WINDOWS_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# OpenAIモデル名（追加）
OPENAI_MODEL_GPT4O = "gpt-4o"

# APIキー検証
API_KEY_MIN_LENGTH = 45
API_KEY_MAX_LENGTH = 60
API_KEY_MASK_START_LENGTH = 7
API_KEY_MASK_END_LENGTH = 11
API_KEY_DISPLAY_START_LENGTH = 10
API_KEY_DISPLAY_END_LENGTH = 4

# JSON書き込み設定
JSON_INDENT_LEVEL = 2

# テキストプレビュー長（文字数）
PREVIEW_LENGTH_SHORT = 10
PREVIEW_LENGTH_TITLE = 30
PREVIEW_LENGTH_MEDIUM = 50
PREVIEW_LENGTH_STANDARD = 100
PREVIEW_LENGTH_LONG = 200
PREVIEW_LENGTH_EXTENDED = 300
PREVIEW_LENGTH_FULL = 400

# 表示用区切り文字設定
DISPLAY_SEPARATOR_CHAR = "="
DISPLAY_SEPARATOR_LENGTH_SHORT = 50
DISPLAY_EMOJI_SHIELD = "🛡️"
DISPLAY_EMOJI_MASK = "🎭"

# HTTPステータスコード（追加）
HTTP_STATUS_ACCEPTED = 202

# 正規表現パターン用定数
REGEX_JAPANESE_CHAR_MIN = 1
REGEX_JAPANESE_CHAR_MAX = 3

# ThreadPoolExecutor設定
THREAD_POOL_MAX_WORKERS_SINGLE = 1

# 数値計算用定数
FRACTION_THREE_HALVES = 1.5
MULTIPLIER_DOUBLE = 2

# リスト項目番号の最大値
LIST_ITEM_MAX_NUMBER = 10

# タイトル長チェック
TITLE_MIN_LENGTH = 10

# 特殊なトークン設定
BING_FILTER_MAX_TOKENS = 500

# ==============================================================================
# 検索パターン関数
# ==============================================================================

def get_search_patterns(name: str) -> List[str]:
    """キャラクター名を適用した検索パターンを取得"""
    patterns = [
        '"{name}" 口癖 語尾',
        '"{name}" 話し方 特徴'
    ]  # 3パターンから2パターンに減らして高速化
    return [pattern.format(name=name) for pattern in patterns]