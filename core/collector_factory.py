"""
コレクターのファクトリークラス
"""

from typing import Dict, Any, Optional
from enum import Enum

from core.interfaces import BaseCollector
from core.exceptions import ConfigurationError
from config import config


class SearchEngineType(Enum):
    """検索エンジンの種類"""
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"
    CHATGPT = "chatgpt"


class CollectorFactory:
    """コレクターの生成を管理するファクトリークラス"""
    
    @staticmethod
    def create_search_engine_collector(
        engine_type: SearchEngineType,
        api_key: Optional[str] = None,
        **kwargs
    ) -> BaseCollector:
        """
        検索エンジンコレクターを作成
        
        Args:
            engine_type: 検索エンジンの種類
            api_key: API Key
            **kwargs: その他のパラメータ
            
        Returns:
            コレクターインスタンス
        """
        if engine_type == SearchEngineType.GOOGLE:
            from collectors.google_collector import GoogleCollector
            return GoogleCollector(
                delay=config.search.google_delay,
                google_api_key=config.api.google_api_key,
                google_cx=config.api.google_cx,
                **kwargs
            )
        
        elif engine_type == SearchEngineType.BING:
            from collectors.bing_collector import BingCollector
            return BingCollector(
                delay=config.collector.default_delay,
                **kwargs
            )
        
        elif engine_type == SearchEngineType.DUCKDUCKGO:
            from collectors.duckduckgo_collector import DuckDuckGoCollector
            return DuckDuckGoCollector(
                delay=config.collector.default_delay,
                **kwargs
            )
        
        elif engine_type == SearchEngineType.CHATGPT:
            from collectors.chatgpt_collector import ChatGPTCollector
            if not api_key:
                raise ConfigurationError("ChatGPT検索にはAPI Keyが必要です")
            return ChatGPTCollector(
                delay=config.collector.default_delay,
                **kwargs
            )
        
        else:
            raise ConfigurationError(f"サポートされていない検索エンジン: {engine_type}")
    
    @staticmethod
    def create_wikipedia_collector(**kwargs) -> BaseCollector:
        """Wikipediaコレクターを作成"""
        from collectors.wikipedia_collector import WikipediaCollector
        return WikipediaCollector(**kwargs)
    
    @staticmethod
    def create_youtube_collector(**kwargs) -> BaseCollector:
        """YouTubeコレクターを作成"""
        from collectors.youtube_collector import YouTubeCollector
        return YouTubeCollector(**kwargs)
    
    @staticmethod
    def determine_best_search_engine(
        use_chatgpt: bool = False,
        use_bing: bool = False,
        use_duckduckgo: bool = False,
        use_google: bool = True
    ) -> SearchEngineType:
        """
        最適な検索エンジンを決定
        
        Args:
            use_chatgpt: ChatGPT検索を使用するか
            use_bing: Bing検索を使用するか
            use_duckduckgo: DuckDuckGo検索を使用するか
            use_google: Google検索を使用するか
            
        Returns:
            選択された検索エンジンタイプ
        """
        if use_chatgpt:
            return SearchEngineType.CHATGPT
        elif use_bing:
            return SearchEngineType.BING
        elif use_duckduckgo:
            return SearchEngineType.DUCKDUCKGO
        elif use_google:
            return SearchEngineType.GOOGLE
        else:
            # デフォルトでChatGPTを選択（最も安定）
            return SearchEngineType.CHATGPT