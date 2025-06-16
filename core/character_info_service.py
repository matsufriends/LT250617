"""
キャラクター情報収集を統括するサービスクラス
"""

import time
from typing import Dict, Any, Optional

from core.interfaces import BaseCollector
from core.collector_factory import CollectorFactory, SearchEngineType
from core.exceptions import CollectorError
from utils.execution_logger import ExecutionLogger
from config import (
    YOUTUBE_MAX_VIDEOS, GOOGLE_API_KEY, GOOGLE_CX,
    CONCURRENT_WORKERS, COLLECTION_TIMEOUT_TOTAL,
    COLLECTION_TIMEOUT_WIKIPEDIA, COLLECTION_TIMEOUT_WEB_SEARCH,
    COLLECTION_TIMEOUT_YOUTUBE
)


class CharacterInfoService:
    """キャラクター情報収集を統括するサービス"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger: Optional[ExecutionLogger] = None
    
    def collect_character_info(
        self,
        name: str,
        logger: Optional[ExecutionLogger] = None,
        use_youtube: bool = True,
        use_google: bool = True,
        use_duckduckgo: bool = False,
        use_bing: bool = False,
        use_chatgpt_search: bool = False
    ) -> Dict[str, Any]:
        """
        キャラクター情報を包括的に収集
        
        Args:
            name: キャラクター名
            logger: 実行ログ記録用
            use_youtube: YouTube字幕収集を使用するか
            use_google: Google検索を使用するか
            use_duckduckgo: DuckDuckGo検索を使用するか
            use_bing: Bing検索を使用するか
            use_chatgpt_search: ChatGPT検索を使用するか
            
        Returns:
            収集したキャラクター情報
        """
        self.logger = logger
        character_info = {"name": name}
        
        print("📚 情報収集中... (順次実行)")
        
        # 順次実行でWikipedia、Web検索、YouTube情報収集を実行
        print("\n  📋 タスクを順次実行:")
        
        # 1. Wikipedia情報収集
        print("\n  1️⃣ Wikipedia情報収集を開始...")
        character_info["wikipedia_info"] = self._collect_wikipedia_info(name)
        print("✅ Wikipedia情報収集完了")
        # 即座にログを保存
        if self.logger:
            self.logger._save_log()
        
        # 2. Web検索情報収集  
        print("\n  2️⃣ Web検索情報収集を開始...")
        character_info["google_search_results"] = self._collect_web_search_info(
            name, use_google, use_duckduckgo, use_bing, use_chatgpt_search
        )
        print("✅ Web検索情報収集完了")
        # 即座にログを保存
        if self.logger:
            self.logger._save_log()
        
        # 3. YouTube情報収集
        if use_youtube:
            print("\n  3️⃣ YouTube情報収集を開始...")
            character_info["youtube_transcripts"] = self._collect_youtube_info(
                name, use_chatgpt_search, use_bing, use_duckduckgo, use_google
            )
            print("✅ YouTube情報収集完了")
            # 即座にログを保存
            if self.logger:
                self.logger._save_log()
        else:
            character_info["youtube_transcripts"] = {
                "found": False,
                "error": "YouTube情報収集が無効化されています",
                "transcripts": [],
                "total_videos": 0,
                "sample_phrases": [],
                "skipped": True
            }
        
        return character_info
    
    def _collect_wikipedia_info(self, name: str) -> Dict[str, Any]:
        """Wikipedia情報を収集"""
        try:
            print("📖 Wikipedia情報を収集中...")
            if self.logger:
                self.logger.log_step("wikipedia_collection", "start", {"character_name": name})
                self.logger._save_log()  # 開始時にログを即座に保存
            
            start_time = time.time()
            print(f"    キャラクター名「{name}」でWikipediaを検索中...")
            collector = CollectorFactory.create_wikipedia_collector()
            result = collector.collect_info(name, logger=self.logger)
            duration = time.time() - start_time
            
            if result and hasattr(result, 'found') and result.found:
                print(f"    ✅ Wikipedia記事を発見")
            else:
                print(f"    ⚠️ Wikipedia記事が見つかりませんでした")
            
            if self.logger:
                self.logger.log_step("wikipedia_collection", "success", result.to_dict(), duration)
                self.logger.log_performance_metric("wikipedia_duration", duration, "seconds")
            
            # 後方互換性のため辞書形式で返す
            if hasattr(result, 'to_dict'):
                return result.to_dict()
            elif isinstance(result, dict):
                return result
            else:
                # CollectionResultオブジェクトを辞書に変換
                return {
                    "found": getattr(result, 'found', False),
                    "error": getattr(result, 'error', None),
                    "results": getattr(result, 'results', []),
                    "total_results": getattr(result, 'total_results', 0)
                }
            
        except Exception as e:
            error_msg = f"Wikipedia情報収集エラー: {str(e)}"
            if self.logger:
                self.logger.log_error("wikipedia_collection_error", error_msg, {"character_name": name})
            
            return {
                "found": False,
                "error": error_msg,
                "title": None,
                "summary": None,
                "content": None,
                "url": None,
                "categories": []
            }
    
    def _collect_web_search_info(
        self, 
        name: str, 
        use_google: bool, 
        use_duckduckgo: bool, 
        use_bing: bool, 
        use_chatgpt_search: bool
    ) -> Dict[str, Any]:
        """Web検索情報を収集"""
        try:
            # 検索エンジンを決定
            engine_type = CollectorFactory.determine_best_search_engine(
                use_chatgpt=use_chatgpt_search,
                use_bing=use_bing,
                use_duckduckgo=use_duckduckgo,
                use_google=use_google
            )
            
            # 適切なメッセージを表示
            engine_messages = {
                SearchEngineType.CHATGPT: "🤖 ChatGPT知識ベース検索中...",
                SearchEngineType.BING: "🔍 Bing検索情報を収集中...",
                SearchEngineType.DUCKDUCKGO: "🦆 DuckDuckGo検索情報を収集中...",
                SearchEngineType.GOOGLE: "🔍 Google検索情報を収集中..."
            }
            
            print(engine_messages.get(engine_type, "🔍 Web検索情報を収集中..."))
            print(f"    キャラクター名「{name}」で検索開始...")
            
            if self.logger:
                step_name = f"{engine_type.value}_collection"
                self.logger.log_step(step_name, "start", {"character_name": name})
            
            start_time = time.time()
            collector = CollectorFactory.create_search_engine_collector(
                engine_type, api_key=self.api_key
            )
            result = collector.collect_info(name, logger=self.logger, api_key=self.api_key)
            duration = time.time() - start_time
            
            if result and hasattr(result, 'found') and result.found:
                result_count = getattr(result, 'total_results', 0)
                print(f"    ✅ {result_count}件の検索結果を取得")
            else:
                print(f"    ⚠️ 検索結果が見つかりませんでした")
            
            if self.logger:
                step_name = f"{engine_type.value}_collection"
                self.logger.log_step(step_name, "success", result.to_dict(), duration)
                self.logger.log_performance_metric(f"{engine_type.value}_duration", duration, "seconds")
            
            # 後方互換性のため辞書形式で返す
            if hasattr(result, 'to_dict'):
                return result.to_dict()
            elif isinstance(result, dict):
                return result
            else:
                # CollectionResultオブジェクトを辞書に変換
                return {
                    "found": getattr(result, 'found', False),
                    "error": getattr(result, 'error', None),
                    "results": getattr(result, 'results', []),
                    "total_results": getattr(result, 'total_results', 0)
                }
            
        except Exception as e:
            error_msg = f"Web検索エラー: {str(e)}"
            if self.logger:
                self.logger.log_error("web_search_error", error_msg, {"character_name": name})
            
            return {
                "found": False,
                "error": error_msg,
                "results": [],
                "total_results": 0
            }
    
    def _collect_youtube_info(
        self, 
        name: str, 
        use_chatgpt_search: bool, 
        use_bing: bool, 
        use_duckduckgo: bool, 
        use_google: bool
    ) -> Dict[str, Any]:
        """YouTube情報を収集"""
        try:
            print("🎥 YouTube情報を収集中...")
            if self.logger:
                self.logger.log_step("youtube_collection", "start", {"character_name": name})
            
            start_time = time.time()
            
            # YouTube URL検索用のコレクターを選択
            print(f"    YouTube動画URL検索中...")
            youtube_urls = self._get_youtube_urls(
                name, use_chatgpt_search, use_bing, use_duckduckgo, use_google
            )
            
            if youtube_urls:
                print(f"    {len(youtube_urls)}個のYouTube動画URLを発見")
            else:
                print(f"    ⚠️ YouTube動画URLが見つかりませんでした")
            
            # YouTube字幕収集
            if youtube_urls:
                print(f"    字幕データ収集中（最大{YOUTUBE_MAX_VIDEOS}動画）...")
            youtube_collector = CollectorFactory.create_youtube_collector()
            youtube_info = youtube_collector.collect_info(
                youtube_urls,
                max_videos=YOUTUBE_MAX_VIDEOS,
                logger=self.logger, 
                character_info={"name": name}, 
                api_key=self.api_key
            )
            
            if youtube_info.get('found', False):
                transcript_count = len(youtube_info.get('transcripts', []))
                print(f"    ✅ {transcript_count}個の動画から字幕を取得")
            else:
                print(f"    ⚠️ 字幕データの取得に失敗しました")
            
            duration = time.time() - start_time
            
            if self.logger:
                self.logger.log_step("youtube_collection", "success", youtube_info, duration)
                self.logger.log_performance_metric("youtube_duration", duration, "seconds")
            
            return youtube_info
            
        except Exception as e:
            import traceback
            error_msg = f"YouTube情報収集エラー: {str(e)}"
            error_traceback = traceback.format_exc()
            
            print(f"❌ YouTube情報収集エラーの詳細:")
            print(f"エラー: {error_msg}")
            print(f"トレースバック:\n{error_traceback}")
            
            if self.logger:
                self.logger.log_error("youtube_collection_error", error_msg, {
                    "character_name": name,
                    "error_traceback": error_traceback,
                    "error_type": type(e).__name__
                })
            
            return {
                "found": False,
                "error": error_msg,
                "transcripts": [],
                "total_videos": 0,
                "sample_phrases": []
            }
    
    def _get_youtube_urls(
        self, 
        name: str, 
        use_chatgpt_search: bool, 
        use_bing: bool, 
        use_duckduckgo: bool, 
        use_google: bool
    ) -> list:
        """YouTube動画URLを取得"""
        try:
            if use_chatgpt_search:
                # ChatGPT検索の場合は代替手段でYouTube URLを取得
                print("  YouTube動画URL取得: Web検索を使用（YouTube字幕収集のため）")
                
                # 利用可能な検索エンジンを自動選択
                if GOOGLE_API_KEY and GOOGLE_CX:
                    print("    Google Custom Search APIでYouTube動画を検索")
                    collector = CollectorFactory.create_search_engine_collector(SearchEngineType.GOOGLE)
                else:
                    print("    Bing検索でYouTube動画を検索（Google API未設定のため）")
                    collector = CollectorFactory.create_search_engine_collector(SearchEngineType.BING)
                
                return collector.search_youtube_videos(name)
            
            elif use_bing:
                collector = CollectorFactory.create_search_engine_collector(SearchEngineType.BING)
                return collector.search_youtube_videos(name)
            
            elif use_duckduckgo:
                print("  注意: DuckDuckGo使用時はYouTube動画URLの自動検索はスキップされます")
                return []
            
            elif use_google:
                collector = CollectorFactory.create_search_engine_collector(SearchEngineType.GOOGLE)
                return collector.search_youtube_videos(name)
            
            else:
                print("  注意: Web検索が無効のためYouTube動画URLの自動検索はスキップされます")
                return []
                
        except Exception as e:
            print(f"YouTube URL取得エラー: {e}")
            return []