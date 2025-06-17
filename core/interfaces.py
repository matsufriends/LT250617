"""
共通インターフェースの定義
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from utils.execution_logger import ExecutionLogger


@dataclass
class CollectionResult:
    """情報収集結果の標準データクラス"""
    found: bool
    error: Optional[str]
    results: List[Dict[str, Any]]
    total_results: int
    query: Optional[str] = None
    source: Optional[str] = None
    duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "found": self.found,
            "error": self.error,
            "results": self.results,
            "total_results": self.total_results,
            "query": self.query,
            "source": self.source,
            "duration": self.duration
        }


@dataclass
class CharacterQuote:
    """キャラクターのセリフデータクラス"""
    text: str  # セリフ本文
    source: str  # "wikipedia", "web", "youtube" など
    source_url: Optional[str] = None  # ソースのURL
    confidence_score: float = 0.5  # 信頼性スコア (0.0-1.0)
    context: Optional[str] = None  # セリフの文脈
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "text": self.text,
            "source": self.source,
            "source_url": self.source_url,
            "confidence_score": self.confidence_score,
            "context": self.context
        }


@dataclass
class SearchResult:
    """個別検索結果の標準データクラス"""
    url: str
    title: str
    description: str
    content: str
    domain: str
    content_length: int
    speech_patterns: List[str]
    character_quotes: Optional[List[CharacterQuote]] = None  # キャラクターの具体的なセリフ
    source: Optional[str] = None
    search_query: Optional[str] = None
    api_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "domain": self.domain,
            "content_length": self.content_length,
            "speech_patterns": self.speech_patterns,
            "source": self.source,
            "search_query": self.search_query,
            "api_duration": self.api_duration
        }
        if self.character_quotes:
            result["character_quotes"] = [quote.to_dict() for quote in self.character_quotes]
        return result


class BaseCollector(ABC):
    """情報収集クラスの基底クラス"""
    
    def __init__(self, delay: float = 2.0, **kwargs):
        self.delay = delay
        self.source_name = self.__class__.__name__.replace("Collector", "").lower()
    
    @abstractmethod
    def collect_info(self, name: str, logger: Optional[ExecutionLogger] = None, api_key: Optional[str] = None, **kwargs) -> CollectionResult:
        """
        情報を収集する（抽象メソッド）
        
        Args:
            name: 検索対象の名前
            logger: 実行ログ記録用
            api_key: API Key（必要に応じて）
            **kwargs: その他のパラメータ
            
        Returns:
            収集結果
        """
        pass
    
    def _create_error_result(self, error_message: str, query: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> CollectionResult:
        """エラー結果を作成するヘルパーメソッド"""
        return CollectionResult(
            found=False,
            error=error_message,
            results=[],
            total_results=0,
            query=query,
            source=self.source_name
        )
    
    def _create_success_result(self, results: List[SearchResult], query: Optional[str] = None, duration: Optional[float] = None) -> CollectionResult:
        """成功結果を作成するヘルパーメソッド"""
        return CollectionResult(
            found=len(results) > 0,
            error=None,
            results=[result.to_dict() for result in results],
            total_results=len(results),
            query=query,
            source=self.source_name,
            duration=duration
        )


class SearchEngineCollector(BaseCollector):
    """検索エンジン系コレクターの基底クラス"""
    
    @abstractmethod
    def search_youtube_videos(self, name: str, **kwargs) -> List[str]:
        """
        YouTube動画URLを検索する（抽象メソッド）
        
        Args:
            name: 検索対象の名前
            **kwargs: その他のパラメータ
            
        Returns:
            YouTube動画URLのリスト
        """
        pass
    
    def _extract_domain(self, url: str) -> str:
        """URLからドメインを抽出するヘルパーメソッド"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except Exception:
            return "unknown"
    
    def _extract_basic_patterns(self, text: str, character_name: str) -> List[str]:
        """基本的な話し方パターンを抽出するヘルパーメソッド"""
        patterns = []
        
        try:
            if not text:
                return patterns
            
            text_lower = text.lower()
            
            # キャラクター名の言及があるかチェック
            if character_name and character_name.lower() in text_lower:
                patterns.append(f"呼び方: {character_name}")
            
            # 簡単な特徴抽出
            if "口調" in text or "語尾" in text:
                patterns.append("表現: 口調・語尾に関する情報")
            
            if "一人称" in text or "話し方" in text:
                patterns.append("表現: 話し方に関する情報")
                
        except Exception as e:
            print(f"パターン抽出エラー: {e}")
        
        return patterns


class Generator(ABC):
    """生成クラスの基底クラス"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    @abstractmethod
    def generate(self, character_info: Dict[str, Any], logger: Optional[ExecutionLogger] = None, **kwargs) -> Dict[str, Any]:
        """
        生成処理を実行する（抽象メソッド）
        
        Args:
            character_info: キャラクター情報
            logger: 実行ログ記録用
            **kwargs: その他のパラメータ
            
        Returns:
            生成結果
        """
        pass