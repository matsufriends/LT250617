"""
DuckDuckGo検索モジュール（Google検索の代替）
"""

import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from core.interfaces import SearchEngineCollector, CollectionResult, SearchResult
from utils.execution_logger import ExecutionLogger
from config import (
    get_search_patterns,
    DEFAULT_DELAY,
    REQUEST_TIMEOUT,
    HTTP_STATUS_OK,
    SAMPLE_QUALITY_MIN_LENGTH,
    SAMPLE_PHRASES_MAX,
    DEFAULT_USER_AGENT,
    PREVIEW_LENGTH_LONG,
    PREVIEW_LENGTH_MEDIUM,
    PREVIEW_LENGTH_TITLE,
    TITLE_MIN_LENGTH,
    HTTP_STATUS_ACCEPTED
)

class DuckDuckGoCollector(SearchEngineCollector):
    """DuckDuckGo検索でGoogle検索の代替を提供"""
    
    def __init__(self, delay: float = DEFAULT_DELAY, **kwargs):  # レート制限対策で大幅延長
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（秒）
        """
        super().__init__(delay, **kwargs)
        self.session = requests.Session()
        
        # より現実的なブラウザヘッダーを設定
        self.session.headers.update({
            'User-Agent': DEFAULT_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        })
    
    def collect_info(self, name: str, logger: Optional[ExecutionLogger] = None, api_key: Optional[str] = None, **kwargs) -> CollectionResult:
        """
        DuckDuckGoからキャラクター情報を収集
        
        Args:
            name: 検索対象のキャラクター名
            logger: 実行ログ記録用
            api_key: OpenAI API Key（オプション）
            
        Returns:
            収集結果の辞書
        """
        try:
            search_patterns = get_search_patterns(name)
            all_results = []
            
            print(f"  DuckDuckGo検索パターン: {len(search_patterns)}個")
            
            for i, pattern in enumerate(search_patterns, 1):
                print(f"DuckDuckGo検索中 ({i}/{len(search_patterns)}): {pattern}")
                
                try:
                    results = self._search_pattern(pattern, name, api_key)
                    all_results.extend(results)
                    
                    # レート制限対策
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"検索パターンエラー ({pattern}): {e}")
                    continue
            
            print(f"  DuckDuckGo検索結果: {len(all_results)}件取得")
            
            # SearchResultオブジェクトに変換
            search_result_objects = []
            for result_dict in all_results:
                try:
                    search_result = SearchResult(
                        url=result_dict.get("url", ""),
                        title=result_dict.get("title", ""),
                        description=result_dict.get("description", ""),
                        content=result_dict.get("content", ""),
                        domain=result_dict.get("domain", ""),
                        content_length=result_dict.get("content_length", 0),
                        speech_patterns=result_dict.get("speech_patterns", []),
                        source="duckduckgo",
                        search_query="複数パターン検索（DuckDuckGo）"
                    )
                    search_result_objects.append(search_result)
                except Exception as e:
                    if logger:
                        logger.log_error("search_result_conversion_error", str(e), result_dict)
                    continue
            
            return self._create_success_result(search_result_objects, "複数パターン検索（DuckDuckGo）")
            
        except Exception as e:
            return self._create_error_result(f"DuckDuckGo検索エラー: {str(e)}", "複数パターン検索（DuckDuckGo）")
    
    def _search_pattern(self, query: str, character_name: str = "", api_key: str = None) -> List[Dict[str, Any]]:
        """
        単一の検索パターンを実行
        
        Args:
            query: 検索クエリ
            character_name: キャラクター名
            api_key: OpenAI API Key
            
        Returns:
            検索結果のリスト
        """
        results = []
        
        try:
            print(f"  DuckDuckGo検索開始: {query}")
            
            # 複数の検索手法を順次試行
            methods = [
                ("HTML検索", self._try_html_search),
                ("Lite検索", self._try_lite_search),
                ("シンプル検索", self._try_simple_search)
            ]
            
            for method_name, method_func in methods:
                print(f"    {method_name}を試行中...")
                try:
                    results = method_func(query, character_name, api_key)
                    if results:
                        print(f"    {method_name}成功: {len(results)}件取得")
                        break
                    else:
                        print(f"    {method_name}: 結果なし")
                except Exception as method_error:
                    print(f"    {method_name}エラー: {method_error}")
                    continue
            
            if not results:
                print(f"  DuckDuckGo検索完了: 全ての手法で結果なし")
            else:
                print(f"  DuckDuckGo検索完了: {len(results)}件取得")
                
        except Exception as e:
            print(f"DuckDuckGo検索エラー ({query}): {e}")
        
        return results
    
    def _try_html_search(self, query: str, character_name: str, api_key: str) -> List[Dict[str, Any]]:
        """
        標準のHTML検索を試行
        """
        search_url = "https://duckduckgo.com/html/"
        params = {
            'q': query,
            'kl': 'jp-jp'  # 日本語地域設定
        }
        
        print(f"      リクエストURL: {search_url}")
        print(f"      パラメータ: {params}")
        
        response = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT)
        print(f"      レスポンス: HTTP {response.status_code}")
        print(f"      コンテンツ長: {len(response.text)}文字")
        
        if response.status_code == HTTP_STATUS_OK:
            # レスポンスの先頭100文字を表示（デバッグ用）
            response_preview = response.text[:PREVIEW_LENGTH_LONG].replace('\n', ' ').strip()
            print(f"      レスポンス先頭: {response_preview}...")
            
            results = self._parse_duckduckgo_results(response.text, character_name, api_key)
            return results
        elif response.status_code == HTTP_STATUS_ACCEPTED:
            print(f"      HTTP 202: 処理中（結果は後で利用可能）")
            return []
        else:
            print(f"      HTTP {response.status_code}: 検索失敗")
            return []
    
    def _try_lite_search(self, query: str, character_name: str, api_key: str) -> List[Dict[str, Any]]:
        """
        DuckDuckGo Lite検索を試行
        """
        search_url = "https://duckduckgo.com/lite/"
        params = {
            'q': query,
            'kl': 'jp-jp'
        }
        
        print(f"      Lite URL: {search_url}")
        response = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT)
        print(f"      Lite レスポンス: HTTP {response.status_code}")
        
        if response.status_code == HTTP_STATUS_OK:
            response_preview = response.text[:PREVIEW_LENGTH_LONG].replace('\n', ' ').strip()
            print(f"      Lite レスポンス先頭: {response_preview}...")
            
            results = self._parse_lite_results(response.text, character_name, api_key)
            return results
        else:
            return []
    
    def _try_simple_search(self, query: str, character_name: str, api_key: str) -> List[Dict[str, Any]]:
        """
        シンプルな検索を試行
        """
        search_url = "https://duckduckgo.com/"
        params = {
            'q': query,
            'ia': 'web'
        }
        
        print(f"      シンプル URL: {search_url}")
        response = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT)
        print(f"      シンプル レスポンス: HTTP {response.status_code}")
        
        if response.status_code == HTTP_STATUS_OK:
            response_preview = response.text[:PREVIEW_LENGTH_LONG].replace('\n', ' ').strip()
            print(f"      シンプル レスポンス先頭: {response_preview}...")
            
            results = self._parse_simple_results(response.text, character_name)
            return results
        else:
            return []
    
    def _parse_duckduckgo_results(self, html: str, character_name: str = "", api_key: str = None) -> List[Dict[str, Any]]:
        """
        DuckDuckGoの検索結果HTMLを解析
        
        Args:
            html: 検索結果のHTML
            character_name: キャラクター名
            api_key: OpenAI API Key
            
        Returns:
            解析された結果のリスト
        """
        results = []
        
        try:
            print(f"      HTML解析開始: {len(html)}文字")
            soup = BeautifulSoup(html, 'html.parser')
            
            # 複数のセレクタパターンを試行
            selectors = [
                ('div.result', 'a.result__a', 'a.result__snippet'),
                ('div.web-result', 'a.result__link', '.result__snippet'),
                ('div.results_links', 'a', '.result__snippet'),
                ('.result', 'a', '.snippet')
            ]
            
            for container_sel, title_sel, desc_sel in selectors:
                print(f"      セレクタ試行: {container_sel}")
                result_elements = soup.select(container_sel)
                print(f"      {container_sel}で{len(result_elements)}件見つかりました")
                
                if result_elements:
                    for element in result_elements[:10]:  # 上位10件
                        try:
                            # タイトルとURL
                            title_element = element.select_one(title_sel)
                            if not title_element:
                                continue
                            
                            title = title_element.get_text(strip=True)
                            url = title_element.get('href', '')
                            
                            # DuckDuckGoのリダイレクトURLから実際のURLを抽出
                            if url.startswith('//duckduckgo.com/l/?uddg='):
                                import urllib.parse
                                # URLデコードして実際のURLを取得
                                encoded_url = url.split('uddg=')[1].split('&')[0]
                                url = urllib.parse.unquote(encoded_url)
                            
                            # 説明文
                            desc_element = element.select_one(desc_sel)
                            description = desc_element.get_text(strip=True) if desc_element else ""
                            
                            if title and url:
                                print(f"        結果発見: {title[:PREVIEW_LENGTH_MEDIUM]}...")
                                content_info = {
                                    "url": url,
                                    "domain": self._extract_domain(url),
                                    "title": title,
                                    "description": description,
                                    "content": description,  # DuckDuckGoでは詳細コンテンツは取得困難
                                    "content_length": len(description),
                                    "speech_patterns": self._extract_basic_patterns(description + " " + title, character_name)
                                }
                                
                                results.append(content_info)
                                
                        except Exception as e:
                            print(f"        要素解析エラー: {e}")
                            continue
                    
                    if results:  # 結果が見つかったらループを抜ける
                        break
            
            # 結果が見つからない場合、任意のリンクを探す
            if not results:
                print(f"      フォールバック: 任意のリンクを検索")
                all_links = soup.find_all('a', href=True)
                print(f"      全リンク数: {len(all_links)}")
                
                for link in all_links[:SAMPLE_PHRASES_MAX]:  # 最初のリンクをチェック
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    # 有効な外部リンクかチェック
                    if (href.startswith('http') and 
                        'duckduckgo' not in href and 
                        title and len(title) > SAMPLE_QUALITY_MIN_LENGTH):
                        
                        print(f"        フォールバックリンク: {title[:PREVIEW_LENGTH_TITLE]}...")
                        content_info = {
                            "url": href,
                            "domain": self._extract_domain(href),
                            "title": title,
                            "description": title,
                            "content": title,
                            "content_length": len(title),
                            "speech_patterns": self._extract_basic_patterns(title, character_name)
                        }
                        
                        results.append(content_info)
                        
                        if len(results) >= 5:  # 最大5件
                            break
            
            print(f"      HTML解析完了: {len(results)}件抽出")
                    
        except Exception as e:
            print(f"      HTML解析エラー: {e}")
            import traceback
            print(f"      詳細エラー: {traceback.format_exc()}")
        
        return results
    
    def _parse_lite_results(self, html: str, character_name: str, api_key: str) -> List[Dict[str, Any]]:
        """
        DuckDuckGo Liteの検索結果HTMLを解析
        """
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Lite版の結果要素を探す
            for link in soup.find_all('a'):
                href = link.get('href', '')
                title = link.get_text(strip=True)
                
                # 有効なURLのみを処理
                if href and href.startswith('http') and title and len(title) > SAMPLE_QUALITY_MIN_LENGTH:
                    content_info = {
                        "url": href,
                        "domain": self._extract_domain(href),
                        "title": title,
                        "description": title,  # Lite版は説明が限定的
                        "content": title,
                        "content_length": len(title),
                        "speech_patterns": self._extract_basic_patterns(title, character_name)
                    }
                    
                    results.append(content_info)
                    
                    if len(results) >= 10:  # 上位10件まで
                        break
                        
        except Exception as e:
            print(f"      Lite結果解析エラー: {e}")
        
        return results
    
    def _parse_simple_results(self, html: str, character_name: str) -> List[Dict[str, Any]]:
        """
        シンプルな検索結果を解析
        """
        results = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 一般的なリンクを探す
            for link in soup.find_all('a', href=True):
                href = link['href']
                title = link.get_text(strip=True)
                
                # 外部リンクのみを処理
                if (href.startswith('http') and 
                    'duckduckgo' not in href and 
                    title and len(title) > TITLE_MIN_LENGTH and 
                    character_name.lower() in title.lower()):
                    
                    content_info = {
                        "url": href,
                        "domain": self._extract_domain(href),
                        "title": title,
                        "description": title,
                        "content": title,
                        "content_length": len(title),
                        "speech_patterns": self._extract_basic_patterns(title, character_name)
                    }
                    
                    results.append(content_info)
                    
                    if len(results) >= 5:  # 限定的な結果数
                        break
                        
        except Exception as e:
            print(f"      シンプル結果解析エラー: {e}")
        
        return results
    
    
