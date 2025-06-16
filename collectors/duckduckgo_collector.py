"""
DuckDuckGo検索モジュール（Google検索の代替）
"""

import requests
import time
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from config import config

class DuckDuckGoCollector:
    """DuckDuckGo検索でGoogle検索の代替を提供"""
    
    def __init__(self, delay: float = 5.0):  # レート制限対策で大幅延長
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（秒）
        """
        self.delay = delay
        self.session = requests.Session()
        
        # より現実的なブラウザヘッダーを設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
    
    def collect_info(self, name: str, logger=None, api_key: str = None) -> Dict[str, Any]:
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
            search_patterns = config.search.get_search_patterns(name)
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
            
            return {
                "found": len(all_results) > 0,
                "error": None,
                "query": "複数パターン検索（DuckDuckGo）",
                "results": all_results,
                "total_results": len(all_results)
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": f"DuckDuckGo検索エラー: {str(e)}",
                "results": [],
                "total_results": 0
            }
    
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
        
        response = self.session.get(search_url, params=params, timeout=15)
        print(f"      レスポンス: HTTP {response.status_code}")
        print(f"      コンテンツ長: {len(response.text)}文字")
        
        if response.status_code == 200:
            # レスポンスの先頭100文字を表示（デバッグ用）
            response_preview = response.text[:200].replace('\n', ' ').strip()
            print(f"      レスポンス先頭: {response_preview}...")
            
            results = self._parse_duckduckgo_results(response.text, character_name, api_key)
            return results
        elif response.status_code == 202:
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
        response = self.session.get(search_url, params=params, timeout=15)
        print(f"      Lite レスポンス: HTTP {response.status_code}")
        
        if response.status_code == 200:
            response_preview = response.text[:200].replace('\n', ' ').strip()
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
        response = self.session.get(search_url, params=params, timeout=15)
        print(f"      シンプル レスポンス: HTTP {response.status_code}")
        
        if response.status_code == 200:
            response_preview = response.text[:200].replace('\n', ' ').strip()
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
                                print(f"        結果発見: {title[:50]}...")
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
                
                for link in all_links[:20]:  # 最初の20個のリンクをチェック
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    # 有効な外部リンクかチェック
                    if (href.startswith('http') and 
                        'duckduckgo' not in href and 
                        title and len(title) > 5):
                        
                        print(f"        フォールバックリンク: {title[:30]}...")
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
                if href and href.startswith('http') and title and len(title) > 5:
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
                    title and len(title) > 10 and 
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
    
    def _extract_domain(self, url: str) -> str:
        """URLからドメインを抽出"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return "unknown"
    
    def _extract_basic_patterns(self, text: str, character_name: str) -> List[str]:
        """
        テキストから基本的な話し方パターンを抽出
        
        Args:
            text: 対象テキスト
            character_name: キャラクター名
            
        Returns:
            抽出されたパターンのリスト
        """
        patterns = []
        
        try:
            if not text:
                return patterns
            
            # 基本的なパターン抽出（regex不使用で中立的）
            text_lower = text.lower()
            
            # キャラクター名の言及があるかチェック
            if character_name and character_name.lower() in text_lower:
                patterns.append(f"呼び方: {character_name}")
            
            # 簡単な特徴抽出（API不使用）
            if "口調" in text or "語尾" in text:
                patterns.append("表現: 口調・語尾に関する情報")
            
            if "一人称" in text or "話し方" in text:
                patterns.append("表現: 話し方に関する情報")
                
        except Exception as e:
            print(f"パターン抽出エラー: {e}")
        
        return patterns