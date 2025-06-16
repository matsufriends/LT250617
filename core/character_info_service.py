"""
キャラクター情報収集を統括するサービスクラス
"""

import time
import concurrent.futures
from typing import Dict, Any, Optional

from core.interfaces import BaseCollector
from core.collector_factory import CollectorFactory, SearchEngineType
from core.exceptions import CollectorError
from utils.execution_logger import ExecutionLogger
from config import config


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
        
        print("📚 情報収集中... (並列実行)")
        
        # 並列実行でWikipedia、Web検索、YouTube情報収集を同時実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # タスクを同時実行
            wikipedia_future = executor.submit(self._collect_wikipedia_info, name)
            
            web_search_future = executor.submit(
                self._collect_web_search_info,
                name, use_google, use_duckduckgo, use_bing, use_chatgpt_search
            )
            
            youtube_future = None
            if use_youtube:
                youtube_future = executor.submit(
                    self._collect_youtube_info,
                    name, use_chatgpt_search, use_bing, use_duckduckgo, use_google
                )
            
            # 結果を収集（タイムアウト付き）
            try:
                # Wikipedia情報（短時間での完了を期待）
                character_info["wikipedia_info"] = wikipedia_future.result(timeout=30)
                print("✅ Wikipedia情報収集完了")
            except concurrent.futures.TimeoutError:
                print("⚠️ Wikipedia情報収集がタイムアウトしました")
                character_info["wikipedia_info"] = {
                    "found": False,
                    "error": "タイムアウト",
                    "results": [],
                    "total_results": 0
                }
            except Exception as e:
                print(f"❌ Wikipedia情報収集エラー: {e}")
                character_info["wikipedia_info"] = {
                    "found": False,
                    "error": str(e),
                    "results": [],
                    "total_results": 0
                }
            
            try:
                # Web検索情報（適切な時間で制限）
                character_info["google_search_results"] = web_search_future.result(timeout=90)
                print("✅ Web検索情報収集完了")
            except concurrent.futures.TimeoutError:
                print("⚠️ Web検索情報収集がタイムアウトしました（90秒）")
                # タイムアウト時はキャンセルを試行
                try:
                    web_search_future.cancel()
                except:
                    pass
                character_info["google_search_results"] = {
                    "found": False,
                    "error": "タイムアウト（90秒）",
                    "results": [],
                    "total_results": 0
                }
            except Exception as e:
                print(f"❌ Web検索情報収集エラー: {e}")
                character_info["google_search_results"] = {
                    "found": False,
                    "error": str(e),
                    "results": [],
                    "total_results": 0
                }
            
            if youtube_future:
                try:
                    # YouTube情報（長時間の処理を想定）
                    character_info["youtube_transcripts"] = youtube_future.result(timeout=120)
                    print("✅ YouTube情報収集完了")
                except concurrent.futures.TimeoutError:
                    print("⚠️ YouTube情報収集がタイムアウトしました")
                    character_info["youtube_transcripts"] = {
                        "found": False,
                        "error": "タイムアウト",
                        "transcripts": [],
                        "total_videos": 0,
                        "sample_phrases": []
                    }
                except Exception as e:
                    print(f"❌ YouTube情報収集エラー: {e}")
                    character_info["youtube_transcripts"] = {
                        "found": False,
                        "error": str(e),
                        "transcripts": [],
                        "total_videos": 0,
                        "sample_phrases": []
                    }
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
            # print("📖 Wikipedia情報を収集中...")  # 並列実行のため出力を制御
            if self.logger:
                self.logger.log_step("wikipedia_collection", "start", {"character_name": name})
            
            start_time = time.time()
            collector = CollectorFactory.create_wikipedia_collector()
            result = collector.collect_info(name, logger=self.logger)
            duration = time.time() - start_time
            
            if self.logger:
                self.logger.log_step("wikipedia_collection", "success", result.to_dict(), duration)
                self.logger.log_performance_metric("wikipedia_duration", duration, "seconds")
            
            # 後方互換性のため辞書形式で返す
            return result.to_dict() if hasattr(result, 'to_dict') else result
            
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
            
            # print(engine_messages.get(engine_type, "🔍 Web検索情報を収集中..."))  # 並列実行のため出力を制御
            
            if self.logger:
                step_name = f"{engine_type.value}_collection"
                self.logger.log_step(step_name, "start", {"character_name": name})
            
            start_time = time.time()
            collector = CollectorFactory.create_search_engine_collector(
                engine_type, api_key=self.api_key
            )
            result = collector.collect_info(name, logger=self.logger, api_key=self.api_key)
            duration = time.time() - start_time
            
            if self.logger:
                step_name = f"{engine_type.value}_collection"
                self.logger.log_step(step_name, "success", result.to_dict(), duration)
                self.logger.log_performance_metric(f"{engine_type.value}_duration", duration, "seconds")
            
            # 後方互換性のため辞書形式で返す
            return result.to_dict() if hasattr(result, 'to_dict') else result
            
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
            # print("🎥 YouTube情報を収集中...")  # 並列実行のため出力を制御
            if self.logger:
                self.logger.log_step("youtube_collection", "start", {"character_name": name})
            
            start_time = time.time()
            
            # YouTube URL検索用のコレクターを選択
            youtube_urls = self._get_youtube_urls(
                name, use_chatgpt_search, use_bing, use_duckduckgo, use_google
            )
            
            # YouTube字幕収集
            youtube_collector = CollectorFactory.create_youtube_collector()
            youtube_info = youtube_collector.collect_info(
                youtube_urls, 
                logger=self.logger, 
                character_info={"name": name}, 
                api_key=self.api_key
            )
            
            duration = time.time() - start_time
            
            if self.logger:
                self.logger.log_step("youtube_collection", "success", youtube_info, duration)
                self.logger.log_performance_metric("youtube_duration", duration, "seconds")
            
            return youtube_info
            
        except Exception as e:
            error_msg = f"YouTube情報収集エラー: {str(e)}"
            if self.logger:
                self.logger.log_error("youtube_collection_error", error_msg, {"character_name": name})
            
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
                # print("  YouTube動画URL取得: Web検索を使用（YouTube字幕収集のため）")  # 並列実行のため出力を制御
                
                # 利用可能な検索エンジンを自動選択
                if config.api.google_api_key and config.api.google_cx:
                    # print("    Google Custom Search APIでYouTube動画を検索")  # 並列実行のため出力を制御
                    collector = CollectorFactory.create_search_engine_collector(SearchEngineType.GOOGLE)
                else:
                    # print("    Bing検索でYouTube動画を検索（Google API未設定のため）")  # 並列実行のため出力を制御
                    collector = CollectorFactory.create_search_engine_collector(SearchEngineType.BING)
                
                return collector.search_youtube_videos(name)
            
            elif use_bing:
                collector = CollectorFactory.create_search_engine_collector(SearchEngineType.BING)
                return collector.search_youtube_videos(name)
            
            elif use_duckduckgo:
                # print("  注意: DuckDuckGo使用時はYouTube動画URLの自動検索はスキップされます")  # 並列実行のため出力を制御
                return []
            
            elif use_google:
                collector = CollectorFactory.create_search_engine_collector(SearchEngineType.GOOGLE)
                return collector.search_youtube_videos(name)
            
            else:
                # print("  注意: Web検索が無効のためYouTube動画URLの自動検索はスキップされます")  # 並列実行のため出力を制御
                return []
                
        except Exception as e:
            # print(f"YouTube URL取得エラー: {e}")  # 並列実行のため出力を制御（エラーはloggerに記録）
            return []