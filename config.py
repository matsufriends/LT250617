"""
設定ファイル - アプリケーション全体の設定を一元管理
"""

import os
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API関連の設定"""
    # OpenAI設定
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.7
    openai_filter_max_tokens: int = 1000
    openai_filter_temperature: float = 0.3
    openai_search_max_tokens: int = 2000
    openai_search_temperature: float = 0.1
    
    # Google Custom Search API設定
    google_api_key: str = ""
    google_cx: str = ""
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """環境変数から設定を読み込み"""
        return cls(
            google_api_key=os.environ.get("GOOGLE_API_KEY", ""),
            google_cx=os.environ.get("GOOGLE_CX", "")
        )


@dataclass  
class SearchConfig:
    """検索関連の設定"""
    # Google検索設定
    google_results: int = 20  # 検索結果数を調整（安定性重視）
    google_api_results: int = 8  # Google Custom Search API での取得件数
    google_delay: float = 8.0  # 遅延時間を増加（タイムアウト対策）
    google_page_limit: int = 1000
    
    # YouTube検索設定
    youtube_max_urls: int = 20
    youtube_max_videos: int = 15
    youtube_max_transcripts: int = 10
    youtube_transcript_limit: int = 3000
    youtube_search_delay: float = 1.0
    
    # 検索パターン
    search_patterns: List[str] = None
    
    def __post_init__(self):
        if self.search_patterns is None:
            self.search_patterns = [
                '"{name}" 口癖 語尾',
                '"{name}" 話し方 特徴', 
                '"{name}" 口調 喋り方'
            ]
    
    def get_search_patterns(self, name: str) -> List[str]:
        """キャラクター名を適用した検索パターンを取得"""
        return [pattern.format(name=name) for pattern in self.search_patterns]


@dataclass
class CollectorConfig:
    """コレクター設定"""
    # Wikipedia設定
    wikipedia_summary_limit: int = 1000
    wikipedia_fallback_limit: int = 500
    
    # 共通設定
    default_delay: float = 2.0
    request_timeout: int = 15
    max_retries: int = 3
    retry_delay: float = 30.0


@dataclass  
class ProcessingConfig:
    """処理関連の設定"""
    # サンプルフレーズ設定
    sample_phrases_max: int = 20
    sample_phrase_min_length: int = 3
    sample_phrase_max_length: int = 60
    sample_quality_min_length: int = 3
    sample_quality_max_length: int = 100
    
    # 表示設定
    max_key_information: int = 5
    max_sample_phrases_display: int = 15
    
    # テキスト処理制限
    chatgpt_filter_text_limit: int = 3000


@dataclass
class AppConfig:
    """アプリケーション全体の設定"""
    api: APIConfig
    search: SearchConfig  
    collector: CollectorConfig
    processing: ProcessingConfig
    
    @classmethod
    def load(cls) -> 'AppConfig':
        """デフォルト設定をロード"""
        return cls(
            api=APIConfig.from_env(),
            search=SearchConfig(),
            collector=CollectorConfig(),
            processing=ProcessingConfig()
        )


# グローバル設定インスタンス
config = AppConfig.load()

