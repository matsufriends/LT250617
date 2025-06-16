"""
アプリケーション専用の例外クラス
"""

from typing import Optional, Dict, Any


class CharacterPromptError(Exception):
    """アプリケーション基底例外"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.original_error = original_error
    
    def to_dict(self) -> Dict[str, Any]:
        """例外情報を辞書として返す"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None
        }


class CollectorError(CharacterPromptError):
    """情報収集関連の例外"""
    pass


class APIError(CharacterPromptError):
    """API呼び出し関連の例外"""
    pass


class SearchEngineError(CollectorError):
    """検索エンジン関連の例外"""
    pass


class RateLimitError(SearchEngineError):
    """レート制限エラー"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class WikipediaError(CollectorError):
    """Wikipedia関連の例外"""
    pass


class YouTubeError(CollectorError):
    """YouTube関連の例外"""
    pass


class OpenAIError(APIError):
    """OpenAI API関連の例外"""
    pass


class ConfigurationError(CharacterPromptError):
    """設定関連の例外"""
    pass


class ValidationError(CharacterPromptError):
    """バリデーション関連の例外"""
    pass