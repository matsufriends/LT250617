"""
設定ファイル - 全てのマジックナンバーを一箇所に集約
"""

# Google検索設定
GOOGLE_SEARCH_RESULTS = 20  # Google検索結果の取得数
GOOGLE_REQUEST_DELAY = 1.0  # リクエスト間の待機時間（秒）
GOOGLE_PAGE_CONTENT_LIMIT = 1000  # ページコンテンツの文字数制限

# YouTube検索設定
YOUTUBE_MAX_URLS = 20  # YouTube動画の最大検索数
YOUTUBE_MAX_VIDEOS = 20  # 字幕取得を試行する最大動画数
YOUTUBE_MAX_TRANSCRIPTS = 13  # 十分とみなす字幕取得数
YOUTUBE_TRANSCRIPT_CHAR_LIMIT = 2500  # 字幕テキストの文字数制限
YOUTUBE_SEARCH_DELAY = 0.5  # 検索間の待機時間（秒）

# サンプルフレーズ抽出設定
SAMPLE_PHRASES_MAX = 20  # 抽出する最大サンプルフレーズ数
SAMPLE_PHRASE_MIN_LENGTH = 3  # サンプルフレーズの最小文字数
SAMPLE_PHRASE_MAX_LENGTH = 60  # サンプルフレーズの最大文字数
SAMPLE_QUALITY_MIN_LENGTH = 3  # 品質チェック時の最小文字数
SAMPLE_QUALITY_MAX_LENGTH = 100  # 品質チェック時の最大文字数

# ChatGPT API設定
CHATGPT_MODEL = "gpt-3.5-turbo"  # 使用するChatGPTモデル
CHATGPT_MAX_TOKENS = 4000  # プロンプト生成時の最大トークン数（詳細プロンプト対応）
CHATGPT_TEMPERATURE = 0.7  # プロンプト生成時のTemperature
CHATGPT_FILTER_MAX_TOKENS = 1000  # フィルタリング時の最大トークン数
CHATGPT_FILTER_TEMPERATURE = 0.3  # フィルタリング時のTemperature
CHATGPT_FILTER_TEXT_LIMIT = 3000  # フィルタリング用テキストの文字数制限

# Wikipedia設定
WIKIPEDIA_SUMMARY_LIMIT = 1000  # Wikipediaサマリーの文字数制限
WIKIPEDIA_FALLBACK_LIMIT = 500  # フォールバック時のサマリー文字数制限

# その他設定
MAX_KEY_INFORMATION = 5  # 重要情報の最大表示数
MAX_SAMPLE_PHRASES_DISPLAY = 15  # 表示する最大サンプルフレーズ数（プロンプト生成時）
# PRIORITY_PHRASES_RATIO は廃止（優先順位付けを削除）