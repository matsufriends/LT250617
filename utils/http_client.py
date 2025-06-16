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
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2, **kwargs) -> requests.Response:
        """
        リトライ機能付きGETリクエストを実行
        
        Args:
            url: リクエスト先URL
            params: クエリパラメータ
            max_retries: 最大リトライ回数
            **kwargs: その他のrequestsパラメータ
            
        Returns:
            HTTPレスポンス
            
        Raises:
            requests.exceptions.RequestException: リトライ後も失敗した場合
        """
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('allow_redirects', True)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = self.session.get(url, params=params, **kwargs)
                response.raise_for_status()
                
                # レート制限対策で待機
                if self.delay > 0:
                    time.sleep(self.delay)
                
                return response
                
            except requests.exceptions.HTTPError as http_err:
                last_exception = http_err
                status_code = http_err.response.status_code if http_err.response else 'unknown'
                
                # 特定のHTTPエラーは即座にスキップ（リトライしない）
                if status_code in [404, 403, 406, 410, 503]:
                    raise http_err
                
                # 他のHTTPエラーはリトライ
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2
                    print(f"    HTTP {status_code}エラー - {wait_time}秒後にリトライ (試行 {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise http_err
                    
            except requests.exceptions.Timeout as timeout_err:
                last_exception = timeout_err
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 3
                    print(f"    タイムアウト - {wait_time}秒後にリトライ (試行 {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise timeout_err
                    
            except requests.exceptions.ConnectionError as conn_err:
                last_exception = conn_err
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 4
                    print(f"    接続エラー - {wait_time}秒後にリトライ (試行 {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise conn_err
                    
            except requests.exceptions.RequestException as req_err:
                last_exception = req_err
                if attempt < max_retries:
                    wait_time = (attempt + 1) * 2
                    print(f"    リクエストエラー - {wait_time}秒後にリトライ (試行 {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    continue
                else:
                    raise req_err
        
        # ここに到達することはないはずだが、念のため
        if last_exception:
            raise last_exception
    
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


def safe_http_get(url: str, max_retries: int = 2, timeout: int = 15, logger=None, quiet: bool = False) -> Optional[requests.Response]:
    """
    安全なHTTP GETリクエスト（エラーハンドリング付き）
    
    Args:
        url: リクエスト先URL
        max_retries: 最大リトライ回数
        timeout: タイムアウト時間（秒）
        logger: ログ記録用（オプション）
        
    Returns:
        HTTPレスポンス（失敗時はNone）
    """
    # URLを検証・修正
    validated_url = validate_url(url)
    if not validated_url:
        if logger:
            logger.log_error("invalid_url", f"無効なURL: {url}", {"original_url": url})
        return None
    
    client = BaseHTTPClient(delay=0, timeout=timeout)
    
    try:
        response = client.get(validated_url, max_retries=max_retries)
        return response
        
    except requests.exceptions.HTTPError as http_err:
        status_code = http_err.response.status_code if http_err.response else 'unknown'
        
        # よくあるエラーは詳細ログを控える（ログにも記録しない）
        if status_code in [404, 403, 406, 410, 503]:
            if not quiet:
                print(f"    HTTP {status_code}エラー - URL: {validated_url} (スキップ)")
            # これらのエラーは一般的でログに記録する価値が低いためスキップ
        else:
            print(f"    HTTP {status_code}エラー - URL: {validated_url}")
            if logger:
                logger.log_error("http_error", f"HTTP {status_code}: {str(http_err)}", {
                    "url": validated_url,
                    "status_code": status_code,
                    "error_type": "HTTPError"
                })
        return None
        
    except requests.exceptions.Timeout:
        if not quiet:
            print(f"    タイムアウトエラー - URL: {validated_url} (スキップ)")
        if logger:
            logger.log_error("http_timeout", f"タイムアウト（{timeout}秒）", {
                "url": validated_url,
                "timeout": timeout
            })
        return None
        
    except requests.exceptions.ConnectionError:
        if not quiet:
            print(f"    接続エラー - URL: {validated_url} (スキップ)")
        if logger:
            logger.log_error("http_connection_error", "接続エラー", {"url": validated_url})
        return None
        
    except Exception as e:
        if not quiet:
            print(f"    予期しないエラー - URL: {validated_url}: {e}")
        if logger:
            logger.log_error("http_unexpected_error", str(e), {
                "url": validated_url,
                "error_type": type(e).__name__
            })
        return None
        
    finally:
        client.close()