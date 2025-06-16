"""
Google検索情報収集モジュール（Custom Search JSON API使用）
"""

import re
import time
import requests
import random
import os
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from googlesearch import search

from core.interfaces import SearchEngineCollector, CollectionResult, SearchResult
from core.exceptions import SearchEngineError
from utils.api_client import OpenAIClient
from utils.execution_logger import ExecutionLogger
from config import (
    GOOGLE_DELAY, GOOGLE_RESULTS, GOOGLE_API_RESULTS, GOOGLE_PAGE_LIMIT,
    YOUTUBE_MAX_URLS, YOUTUBE_SEARCH_DELAY, GOOGLE_FALLBACK_DELAY_MULTIPLIER,
    GOOGLE_MIN_DELAY, GOOGLE_URL_FETCH_DELAY, GOOGLE_PAGE_DELAY_MULTIPLIER,
    GOOGLE_YOUTUBE_DELAY_MULTIPLIER, GOOGLE_CX_DISPLAY_LENGTH,
    GOOGLE_API_MAX_RESULTS_PER_REQUEST, GOOGLE_FALLBACK_MAX_RETRIES,
    GOOGLE_FALLBACK_RETRY_DELAY, GOOGLE_PATTERN_TIMEOUT, GOOGLE_SEARCH_TIMEOUT,
    GOOGLE_MIN_TEXT_LENGTH_FOR_API, GOOGLE_YOUTUBE_API_RESULTS, REQUEST_TIMEOUT,
    HTTP_STATUS_OK, HTTP_STATUS_FORBIDDEN, HTTP_STATUS_TOO_MANY_REQUESTS,
    SAMPLE_QUALITY_MIN_LENGTH, BING_NAME_LENGTH_CHECK, MAX_RETRIES,
    DEFAULT_USER_AGENT, PREVIEW_LENGTH_LONG, THREAD_POOL_MAX_WORKERS_SINGLE,
    GOOGLE_429_EXTRA_DELAY, GOOGLE_FETCH_PAGE_CONTENT, HTTP_STATUS_NOT_FOUND
)


class GoogleCollector(SearchEngineCollector):
    """Google Custom Search JSON APIを使用して検索結果から情報を収集するクラス"""
    
    def __init__(self, delay: float = None, google_api_key: str = None, google_cx: str = None, **kwargs):
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（秒）
            google_api_key: Google Custom Search API Key
            google_cx: Google Custom Search Engine ID
        """
        super().__init__(delay or GOOGLE_DELAY, **kwargs)
        self.session = requests.Session()
        
        # Google Custom Search API設定
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.google_cx = google_cx or os.environ.get("GOOGLE_CX")
        
        # Custom Search JSON API URL
        self.api_base_url = "https://www.googleapis.com/customsearch/v1"
        
        # 標準的なHTTPヘッダー
        self.session.headers.update({
            'User-Agent': DEFAULT_USER_AGENT,
            'Accept': 'application/json',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
        })
        
        if self.google_api_key and self.google_cx:
            print(f"  Google Custom Search API: 有効 (CX: {self.google_cx[:GOOGLE_CX_DISPLAY_LENGTH]}...)")
        else:
            print(f"  Google Custom Search API: 無効 (フォールバック検索を使用)")
            print(f"    💡 設定方法: GOOGLE_API_KEY と GOOGLE_CX 環境変数を設定")
    
    
    def collect_info(self, name: str, logger: Optional[ExecutionLogger] = None, api_key: Optional[str] = None, num_results: int = None, **kwargs) -> CollectionResult:
        """
        指定された名前の人物情報をGoogle Custom Search APIから収集
        
        Args:
            name: 検索対象の人物名
            logger: 実行ログ記録用
            api_key: OpenAI API Key（オプション）
            num_results: 取得する検索結果数
            
        Returns:
            収集した情報
        """
        start_time = time.time()
        num_results = num_results or GOOGLE_RESULTS
        
        try:
            all_search_results = []
            
            # Custom Search APIが利用可能かチェック
            if self.google_api_key and self.google_cx:
                print(f"    Google Custom Search APIを使用")
                # Custom Search APIを使用
                search_patterns = self._get_search_patterns(name)
                print(f"    {len(search_patterns)}個の検索パターンを使用")
                results_per_pattern = max(1, min(GOOGLE_API_RESULTS, num_results // len(search_patterns)))  # API制限考慮
                
                for i, pattern in enumerate(search_patterns):
                    print(f"\n    パターン{i+1}/{len(search_patterns)}: '{pattern}'")
                    pattern_results = self._search_with_api(pattern, results_per_pattern, name, api_key, logger)
                    all_search_results.extend(pattern_results)
                    print(f"      ✅ {len(pattern_results)}件の結果を取得")
                    
                    # API制限対策で適度な待機
                    time.sleep(self.delay)
            else:
                # フォールバック: 従来の検索方法
                print("⚠️  Google Custom Search APIが設定されていません。フォールバック検索を使用します。")
                search_patterns = self._get_search_patterns(name)
                print(f"    {len(search_patterns)}個の検索パターンを使用")
                results_per_pattern = max(1, num_results // len(search_patterns))
                
                for i, pattern in enumerate(search_patterns):
                    print(f"\n    パターン{i+1}/{len(search_patterns)}: '{pattern}'")
                    pattern_results = self._search_single_pattern_fallback(pattern, results_per_pattern, name, api_key, logger)
                    all_search_results.extend(pattern_results)
                    print(f"      ✅ {len(pattern_results)}件の結果を取得")
                    
                    # レート制限対策で大幅待機
                    time.sleep(self.delay * GOOGLE_FALLBACK_DELAY_MULTIPLIER)
            
            duration = time.time() - start_time
            query_description = "複数パターン検索（Custom Search API）" if self.google_api_key else "複数パターン検索（フォールバック）"
            
            # SearchResultオブジェクトに変換
            search_result_objects = []
            for result_dict in all_search_results:
                try:
                    search_result = SearchResult(
                        url=result_dict.get("url", ""),
                        title=result_dict.get("title", ""),
                        description=result_dict.get("description", ""),
                        content=result_dict.get("content", ""),
                        domain=result_dict.get("domain", ""),
                        content_length=result_dict.get("content_length", 0),
                        speech_patterns=result_dict.get("speech_patterns", []),
                        source="google",
                        search_query=query_description
                    )
                    search_result_objects.append(search_result)
                except Exception as e:
                    if logger:
                        logger.log_error("search_result_conversion_error", str(e), result_dict)
                    continue
            
            return self._create_success_result(search_result_objects, query_description, duration)
            
        except Exception as e:
            return self._create_error_result(f"Google検索エラー: {str(e)}", "複数パターン検索")
    
    def _get_search_patterns(self, name: str) -> List[str]:
        """検索パターンを生成"""
        patterns = [
            f'"{name}"',
            f'{name} キャラクター',
            f'{name} 口調',
            f'{name} 話し方',
            f'{name} セリフ'
        ]
        return patterns
    
    def _search_with_api(self, search_query: str, max_results: int, character_name: str = "", api_key: str = None, logger=None) -> List[Dict[str, Any]]:
        """
        Google Custom Search APIを使用して検索を実行
        
        Args:
            search_query: 検索クエリ
            max_results: 最大取得結果数
            character_name: キャラクター名
            api_key: OpenAI API Key
            logger: ログ記録用
            
        Returns:
            検索結果のリスト
        """
        search_results = []
        
        try:
            # Custom Search API パラメータ
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': search_query,
                'num': min(max_results, GOOGLE_API_MAX_RESULTS_PER_REQUEST),  # APIは最大件数まで（Google制限）
                'lr': 'lang_ja',  # 日本語結果を優先
                'gl': 'jp',  # 日本からの検索として実行
                'safe': 'off'  # セーフサーチオフ
            }
            
            print(f"      Google Custom Search APIリクエスト送信中...")
            print(f"      API Key: {self.google_api_key[:10]}... (length: {len(self.google_api_key)})")
            print(f"      CX: {self.google_cx[:GOOGLE_CX_DISPLAY_LENGTH] if self.google_cx else 'None'}... (length: {len(self.google_cx) if self.google_cx else 0})")
            
            response = self.session.get(self.api_base_url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == HTTP_STATUS_OK:
                data = response.json()
                
                if 'items' in data:
                    print(f"      APIから{len(data['items'])}件の結果を取得")
                    
                    for item in data['items']:
                        try:
                            url = item.get('link', '')
                            title = item.get('title', '')
                            snippet = item.get('snippet', '')
                            
                            if url and title:
                                if GOOGLE_FETCH_PAGE_CONTENT:
                                    # ページ内容を詳細取得
                                    print(f"        ページ取得中: {url[:50]}...")
                                    content_info = self._extract_page_content(url, character_name, api_key, logger)
                                    if content_info:
                                        # API結果の情報もマージ
                                        content_info['api_title'] = title
                                        content_info['api_snippet'] = snippet
                                        search_results.append(content_info)
                                    else:
                                        # ページ取得に失敗した場合はAPI結果のみ使用
                                        content_info = {
                                            "url": url,
                                            "domain": self._extract_domain(url),
                                            "title": title,
                                            "description": snippet,
                                            "content": snippet,
                                            "content_length": len(snippet),
                                            "speech_patterns": self._extract_basic_patterns(snippet + " " + title, character_name)
                                        }
                                        search_results.append(content_info)
                                else:
                                    # ページ取得をスキップしてAPI結果のみ使用（高速化）
                                    content_info = {
                                        "url": url,
                                        "domain": self._extract_domain(url),
                                        "title": title,
                                        "description": snippet,
                                        "content": snippet,
                                        "content_length": len(snippet),
                                        "speech_patterns": []
                                    }
                                    search_results.append(content_info)
                                
                                # ページ間の適度な待機
                                time.sleep(self.delay)
                                
                        except Exception as e:
                            print(f"    API結果処理エラー: {e}")
                            continue
                else:
                    print(f"      ⚠️ 検索結果がありません")
                    
            elif response.status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                print(f"      ❌ Google Custom Search APIの日次クォータを超過しました（429エラー）")
                print(f"      💡 対処法:")
                print(f"         1. --use-bing フラグでBing検索を使用")
                print(f"         2. --use-chatgpt-search フラグでChatGPT知識ベースを使用")
                print(f"         3. --no-google フラグでGoogle検索を無効化")
                print(f"         4. 翌日まで待つ（クォータは日本時間午前0時にリセット）")
            elif response.status_code == HTTP_STATUS_FORBIDDEN:
                print(f"      ❌ API認証エラー: API Keyが無効または設定ミス")
                if logger:
                    logger.log_error("google_api_quota_error", "Google Custom Search API quota exceeded", {
                        "search_query": search_query,
                        "status_code": response.status_code,
                        "response": response.text[:PREVIEW_LENGTH_LONG]
                    })
            else:
                print(f"      ❌ API検索失敗: HTTP {response.status_code}")
                if response.status_code == HTTP_STATUS_TOO_MANY_REQUESTS:
                    print(f"      ❌ Google Custom Search APIの日次クォータを超過しました")
                    print(f"      💡 対処法:")
                    print(f"         1. --use-bing フラグでBing検索を使用")
                    print(f"         2. --use-chatgpt-search フラグでChatGPT知識ベースを使用")
                    print(f"         3. --no-google フラグでGoogle検索を無効化")
                    print(f"         4. 翌日まで待つ（クォータは日本時間午前0時にリセット）")
                elif response.status_code == HTTP_STATUS_NOT_FOUND:
                    print(f"      ❌ Google Custom Search Engine ID (CX) が無効です")
                    print(f"      💡 対処法:")
                    print(f"         1. Google Custom Search Engineを作成: https://programmablesearchengine.google.com/")
                    print(f"         2. 環境変数 GOOGLE_CX に検索エンジンIDを設定")
                    print(f"         3. または --use-bing / --use-chatgpt-search を使用")
                    print(f"      現在のCX: {self.google_cx if self.google_cx else '未設定'}")
                if logger:
                    logger.log_error("google_api_error", f"Google Custom Search API error: {response.status_code}", {
                        "search_query": search_query,
                        "status_code": response.status_code,
                        "response": response.text[:PREVIEW_LENGTH_LONG]
                    })
                        
        except Exception as e:
            print(f"      ❌ API検索エラー: {e}")
            if logger:
                logger.log_error("google_api_exception", str(e), {
                    "search_query": search_query,
                    "error_type": type(e).__name__
                })
        
        return search_results
    
    
    def _search_single_pattern_fallback(self, search_query: str, max_results: int, character_name: str = "", api_key: str = None, logger=None) -> List[Dict[str, Any]]:
        """
        単一の検索パターンを実行
        
        Args:
            search_query: 検索クエリ
            max_results: 最大取得結果数
            
        Returns:
            検索結果のリスト
        """
        search_results = []
        
        max_retries = GOOGLE_FALLBACK_MAX_RETRIES  # リトライ回数を減らして全体の処理時間を短縮
        retry_delay = GOOGLE_FALLBACK_RETRY_DELAY  # 待機時間
        
        # パターン全体のタイムアウト
        pattern_start_time = time.time()
        pattern_timeout = GOOGLE_PATTERN_TIMEOUT
        
        for retry in range(max_retries):
            # パターン全体のタイムアウトチェック
            if time.time() - pattern_start_time > pattern_timeout:
                print(f"    ⚠️ パターン全体がタイムアウト（{pattern_timeout}秒）のため処理を中断します")
                break
            try:
                # Google検索を実行（User-Agent設定付き）
                search_urls = []
                
                # googlesearch-pythonライブラリに追加の設定を試行
                try:
                    # ランダムな待機時間でより人間らしい動作を模倣
                    base_delay = max(self.delay * GOOGLE_FALLBACK_DELAY_MULTIPLIER, GOOGLE_MIN_DELAY)  # 最低待機時間
                    
                    print(f"      フォールバック検索実行中（{base_delay}秒間隔で慎重に取得）...")
                    
                    # googlesearch-pythonのUser-Agent設定を試行
                    import googlesearch
                    
                    # より保守的な設定で検索（タイムアウト対策強化）
                    search_timeout = False
                    start_search_time = time.time()
                    
                    # タイムアウト付きの検索を実行
                    search_results_iter = None
                    try:
                        # concurrent.futuresを使って検索にタイムアウトを設定
                        import concurrent.futures
                        import signal
                        
                        def search_with_timeout():
                            try:
                                return list(search(
                                    search_query, 
                                    num=max_results, 
                                    stop=max_results, 
                                    pause=base_delay,
                                    lang='ja',  # 日本語検索を明示
                                    safe='off',  # セーフサーチオフ
                                    country='jp'  # 日本からの検索を明示
                                ))
                            except Exception as e:
                                print(f"    検索関数内エラー: {e}")
                                return []
                        
                        # 60秒のタイムアウトで検索実行
                        with concurrent.futures.ThreadPoolExecutor(max_workers=THREAD_POOL_MAX_WORKERS_SINGLE) as executor:
                            future = executor.submit(search_with_timeout)
                            try:
                                search_results = future.result(timeout=GOOGLE_SEARCH_TIMEOUT)
                                print(f"      {len(search_results)}件のURLを取得")
                                
                                for url in search_results:
                                    search_urls.append(url)
                                    print(f"    URL取得: {url}")
                                    
                                    if len(search_urls) >= max_results:
                                        break
                                    
                                    # 適度な待機
                                    time.sleep(GOOGLE_URL_FETCH_DELAY)
                                    
                            except concurrent.futures.TimeoutError:
                                print(f"    ⚠️ 検索処理がタイムアウト（{GOOGLE_SEARCH_TIMEOUT}秒）のため中断します")
                                search_timeout = True
                                future.cancel()
                                
                    except Exception as search_setup_error:
                        print(f"    検索セットアップエラー: {search_setup_error}")
                        search_timeout = True
                    
                    if search_timeout:
                        print(f"    ⚠️ 検索がタイムアウトしました。取得済みURL: {len(search_urls)}件")
                        if logger:
                            logger.log_error("google_search_timeout", f"検索処理が{GOOGLE_SEARCH_TIMEOUT}秒でタイムアウト", {
                                "search_query": search_query,
                                "urls_collected": len(search_urls)
                            })
                        
                except Exception as search_lib_error:
                    print(f"    googlesearch-pythonライブラリエラー: {search_lib_error}")
                    # フォールバック：直接Google検索を試行
                    search_urls = self._fallback_google_search(search_query, max_results)
                
                # 各URLから情報を取得
                for url in search_urls:
                    try:
                        # ページ内容を取得
                        content_info = self._extract_page_content(url, character_name, api_key, logger)
                        if content_info:
                            search_results.append(content_info)
                        
                        # レート制限対策で大幅待機
                        time.sleep(self.delay * GOOGLE_PAGE_DELAY_MULTIPLIER)
                        
                    except Exception as e:
                        print(f"        ⚠️ URL取得エラー: {url[:50]}... - {e}")
                        if logger:
                            logger.log_error("url_extraction_error", str(e), {"url": url, "search_query": search_query})
                        continue
                
                # 成功した場合はループを抜ける
                break
                        
            except Exception as search_error:
                error_str = str(search_error)
                print(f"検索パターン実行エラー ({search_query}): {search_error}")
                
                # レート制限エラーの場合
                if str(HTTP_STATUS_TOO_MANY_REQUESTS) in error_str or "Too Many Requests" in error_str or "429" in error_str:
                    if logger:
                        logger.log_error("google_rate_limit", f"Google検索レート制限 (試行{retry+1}/{max_retries})", {
                            "search_query": search_query,
                            "retry_attempt": retry + 1,
                            "max_retries": max_retries,
                            "error_details": error_str
                        })
                        
                    print(f"⚠️  Google検索で429エラー（レート制限）が発生しました")
                    print(f"    検索クエリ: {search_query}")
                    print(f"    試行回数: {retry + 1}/{max_retries}")
                    
                    if retry < max_retries - 1:
                        # 429エラー時は特別に長い待機時間を設定
                        wait_time = GOOGLE_429_EXTRA_DELAY + (retry_delay * (retry + 1))
                        print(f"    429エラーのため{wait_time}秒待機してからリトライします...")
                        print(f"    💡 頻繁にエラーが出る場合は以下をお試しください:")
                        print(f"       - --use-bing フラグでBing検索を使用")
                        print(f"       - --use-chatgpt-search フラグでChatGPT知識ベースを使用")
                        print(f"       - Google Custom Search APIの設定（推奨）")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ 最大リトライ回数に達しました。検索パターンをスキップします: {search_query}")
                        print(f"    💡 Google検索が継続的に失敗する場合の対処法:")
                        print(f"       1. --use-bing フラグを使用してBing検索に切り替え")
                        print(f"       2. --no-google フラグでWeb検索を完全に無効化")
                        print(f"       3. 数時間後に再試行（Google側の制限リセット待ち）")
                        if logger:
                            logger.log_error("google_rate_limit_exceeded", f"Google検索の最大リトライ回数を超過", {
                                "search_query": search_query,
                                "max_retries": max_retries
                            })
                        break
                else:
                    # レート制限以外のエラーの場合はリトライしない
                    if logger:
                        logger.log_error("google_search_error", str(search_error), {"search_query": search_query})
                    break
        
        return search_results
    
    def _fallback_google_search(self, query: str, max_results: int) -> List[str]:
        """
        googlesearch-pythonライブラリが失敗した場合のフォールバック検索
        
        Args:
            query: 検索クエリ
            max_results: 最大結果数
            
        Returns:
            検索結果URLのリスト
        """
        print(f"    フォールバック検索を実行中: {query}")
        urls = []
        
        try:
            # 基本的なGoogle検索URL構築
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            google_url = f"https://www.google.com/search?q={encoded_query}&num={max_results}&hl=ja"
            
            print(f"    直接Google検索URL: {google_url}")
            
            response = self.session.get(google_url, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == HTTP_STATUS_OK:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Google検索結果のリンクを抽出
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and href.startswith('/url?q='):
                        # Googleの内部URLから実際のURLを抽出
                        actual_url = href.split('/url?q=')[1].split('&')[0]
                        actual_url = urllib.parse.unquote(actual_url)
                        
                        # 有効なURLのみを追加
                        if actual_url.startswith('http') and 'google.com' not in actual_url:
                            urls.append(actual_url)
                            if len(urls) >= max_results:
                                break
                
                print(f"    フォールバック検索結果: {len(urls)}件")
            else:
                print(f"    フォールバック検索失敗: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"    フォールバック検索エラー: {e}")
        
        return urls
    
    def _extract_page_content(self, url: str, character_name: str = "", api_key: str = None, logger=None) -> Dict[str, Any]:
        """
        指定されたURLからページ内容を抽出
        
        Args:
            url: 対象URL
            
        Returns:
            抽出した内容の辞書
        """
        try:
            # URLの検証と修正
            if not url.startswith(('http://', 'https://')):
                if url.startswith('//'):
                    url = 'https:' + url
                elif url.startswith('/'):
                    return None  # 相対URLは無効として除外
                else:
                    url = 'https://' + url
            
            # 共通HTTPクライアントを使用してリクエストを実行
            from utils.http_client import safe_http_get
            response = safe_http_get(url, max_retries=MAX_RETRIES, timeout=REQUEST_TIMEOUT, logger=None, quiet=True)  # 一般的なHTTPエラーはログに記録せず、出力も抑制
            
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            domain = self._extract_domain(url)  # ドメイン情報を先に取得
            
            # タイトルを取得
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "不明"
            
            # メタ説明を取得
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ''
            
            # 本文テキストを抽出（主要な部分のみ）
            # スクリプトやスタイルを除去
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # 本文テキストを取得
            body_text = soup.get_text()
            # 余分な空白を除去
            lines = (line.strip() for line in body_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            body_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # テキストを制限
            body_text = body_text[:GOOGLE_PAGE_LIMIT] if body_text else ""
            
            # 口調・セリフ関連の文をChatGPT APIで抽出（API keyがある場合のみ）
            speech_patterns = []
            if api_key and len(body_text.strip()) > GOOGLE_MIN_TEXT_LENGTH_FOR_API:  # 十分なテキストがある場合のみ
                try:
                    openai_client = OpenAIClient(api_key)
                    speech_patterns = openai_client.extract_speech_patterns(body_text, character_name, logger)
                except Exception as api_error:
                    print(f"    API抽出スキップ ({domain}): {api_error}")
                    if logger:
                        logger.log_error("speech_pattern_api_error", str(api_error), {
                            "url": url,
                            "domain": domain,
                            "character_name": character_name,
                            "content_length": len(body_text)
                        })
                    speech_patterns = []
            
            return {
                "url": url,
                "domain": domain,
                "title": title_text,
                "description": description,
                "content": body_text,
                "content_length": len(body_text),
                "speech_patterns": speech_patterns
            }
            
        except requests.RequestException as e:
            print(f"HTTP取得エラー ({url}): {e}")
            if logger:
                logger.log_error("http_request_error", str(e), {"url": url, "error_type": "RequestException"})
            return None
        except Exception as e:
            print(f"コンテンツ抽出エラー ({url}): {e}")
            if logger:
                logger.log_error("content_extraction_error", str(e), {"url": url, "error_type": type(e).__name__})
            return None
    
    def search_youtube_videos(self, name: str) -> List[str]:
        """
        YouTube動画を検索（動画URLを優先的に取得）
        
        Args:
            name: 検索対象の名前
            
        Returns:
            YouTube動画URLのリスト
        """
        try:
            # より精密な検索クエリを構築
            search_queries = []
            
            # キャラクター名のみの単純な検索
            if len(name) > BING_NAME_LENGTH_CHECK:  # 名前が短すぎる場合の誤ヒット防止
                search_queries.extend([
                    f'"{name}" site:youtube.com'
                ])
            
            # 一般的なキャラクター検索のみ（キャラクター特有の情報は含めない）
            
            # 除外キーワードを廃止（ユーザー要求により）
            
            youtube_urls = []
            
            for search_query in search_queries:
                if len(youtube_urls) >= YOUTUBE_MAX_URLS:
                    break
                    
                print(f"YouTube検索中: {search_query}")
                
                try:
                    # Custom Search APIが利用可能な場合はAPIを使用
                    if self.google_api_key and self.google_cx:
                        api_urls = self._search_youtube_with_api(search_query)
                        for url in api_urls:
                            if url not in youtube_urls:
                                youtube_urls.append(url)
                                print(f"  - 動画URL発見（API）: {url}")
                            if len(youtube_urls) >= YOUTUBE_MAX_URLS:
                                break
                    else:
                        # フォールバック: 従来の検索方法
                        for url in search(search_query):
                            # 動画URLを収集
                            if 'youtube.com/watch?v=' in url and url not in youtube_urls:
                                youtube_urls.append(url)
                                print(f"  - 動画URL発見: {url}")
                            
                            if len(youtube_urls) >= YOUTUBE_MAX_URLS:
                                break
                            time.sleep(YOUTUBE_SEARCH_DELAY)
                        
                except Exception as search_error:
                    print(f"YouTube検索実行エラー ({search_query}): {search_error}")
                    # YouTube検索エラーはloggerに記録しない（通常のオペレーションではないため）
                    continue
                
                # クエリ間の大幅待機（レート制限対策）
                time.sleep(self.delay * GOOGLE_YOUTUBE_DELAY_MULTIPLIER)
            
            print(f"YouTube動画URL取得完了: {len(youtube_urls)}件")
            return youtube_urls
            
        except Exception as e:
            print(f"YouTube検索エラー: {e}")
            # YouTube検索エラーはloggerに記録しない（通常のオペレーションではないため）
            return []
    
    def _search_youtube_with_api(self, search_query: str) -> List[str]:
        """
        Custom Search APIを使用してYouTube動画を検索
        
        Args:
            search_query: 検索クエリ
            
        Returns:
            YouTube動画URLのリスト
        """
        youtube_urls = []
        
        try:
            # Custom Search API パラメータ（YouTube検索）
            params = {
                'key': self.google_api_key,
                'cx': self.google_cx,
                'q': search_query,
                'num': GOOGLE_YOUTUBE_API_RESULTS,  # APIでの取得件数
                'lr': 'lang_ja',  # 日本語結果を優先
                'gl': 'jp',  # 日本からの検索として実行
                'safe': 'off',
                'siteSearch': 'youtube.com'  # YouTube限定検索
            }
            
            response = self.session.get(self.api_base_url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == HTTP_STATUS_OK:
                data = response.json()
                
                if 'items' in data:
                    for item in data['items']:
                        url = item.get('link', '')
                        if 'youtube.com/watch?v=' in url:
                            youtube_urls.append(url)
                        
                        if len(youtube_urls) >= YOUTUBE_MAX_URLS:
                            break
                            
        except Exception as e:
            print(f"    YouTube API検索エラー: {e}")
        
        return youtube_urls
    
    def _extract_title_from_url(self, url: str) -> str:
        """
        URLから簡単にタイトル情報を抽出（可能な場合）
        
        Args:
            url: YouTube URL
            
        Returns:
            タイトル文字列（取得できない場合は空文字）
        """
        # 実際のページタイトル取得は重すぎるので、空文字を返す
        return ""
    
    
