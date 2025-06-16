"""
HTTP クライアント用の共通ユーティリティ
"""

import requests
import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse

from config import config


class BaseHTTPClient:
    """HTTP リクエスト用の基底クラス"""
    
    def __init__(self, delay: float = 2.0, timeout: int = 15):
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（秒）
            timeout: リクエストタイムアウト（秒）
        """
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        
        # 標準的なHTTPヘッダーを設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        GETリクエストを実行
        
        Args:
            url: リクエスト先URL
            params: クエリパラメータ
            **kwargs: その他のrequestsパラメータ
            
        Returns:
            HTTPレスポンス
        """
        kwargs.setdefault('timeout', self.timeout)
        response = self.session.get(url, params=params, **kwargs)
        
        # レート制限対策で待機
        if self.delay > 0:
            time.sleep(self.delay)
        
        return response
    
    def post(self, url: str, data: Optional[Dict[str, Any]] = None, json: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """
        POSTリクエストを実行
        
        Args:
            url: リクエスト先URL
            data: フォームデータ
            json: JSONデータ
            **kwargs: その他のrequestsパラメータ
            
        Returns:
            HTTPレスポンス
        """
        kwargs.setdefault('timeout', self.timeout)
        response = self.session.post(url, data=data, json=json, **kwargs)
        
        # レート制限対策で待機
        if self.delay > 0:
            time.sleep(self.delay)
        
        return response
    
    def close(self):
        """セッションを閉じる"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SearchHTTPClient(BaseHTTPClient):
    """検索エンジン専用のHTTPクライント"""
    
    def __init__(self, delay: float = None, **kwargs):
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（デフォルトは設定値）
        """
        super().__init__(delay or config.collector.default_delay, **kwargs)
        
        # 検索エンジン用のヘッダーに調整
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })


def validate_url(url: str) -> str:
    """
    URLの検証と修正
    
    Args:
        url: 検証対象のURL
        
    Returns:
        修正されたURL（無効な場合は空文字）
    """
    if not url:
        return ""
    
    if not url.startswith(('http://', 'https://')):
        if url.startswith('//'):
            return 'https:' + url
        elif url.startswith('/'):
            return ""  # 相対URLは無効として除外
        else:
            return 'https://' + url
    
    return url


def extract_domain(url: str) -> str:
    """
    URLからドメインを抽出
    
    Args:
        url: 対象URL
        
    Returns:
        ドメイン名（取得できない場合は"unknown"）
    """
    try:
        return urlparse(url).netloc
    except Exception:
        return "unknown"