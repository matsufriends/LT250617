"""
Bing検索情報収集モジュール
"""

import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urlparse, quote_plus
from config import config


class BingCollector:
    """Bing検索結果から情報を収集するクラス"""
    
    def __init__(self, delay: float = 4.0):  # レート制限対策で大幅延長
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（秒）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def collect_info(self, name: str, num_results: int = 20, logger=None, api_key: str = None) -> Dict[str, Any]:
        """
        指定された名前の人物情報をBing検索から収集
        
        Args:
            name: 検索対象の人物名
            num_results: 取得する検索結果数
            logger: 実行ログ記録用
            api_key: OpenAI API Key（オプション）
            
        Returns:
            収集した情報の辞書
        """
        try:
            all_search_results = []
            
            # 共通の検索パターンを使用
            search_patterns = config.search.get_search_patterns(name)
            
            results_per_pattern = max(1, num_results // len(search_patterns))
            
            for pattern in search_patterns:
                print(f"Bing検索中: {pattern}")
                pattern_results = self._search_single_pattern(pattern, results_per_pattern, name, api_key)
                all_search_results.extend(pattern_results)
                
                # パターン間で大幅待機（レート制限対策）
                time.sleep(self.delay * 2)
            
            return {
                "found": len(all_search_results) > 0,
                "error": None,
                "query": "複数パターン検索（Bing）",
                "results": all_search_results,
                "total_results": len(all_search_results)
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": f"Bing検索エラー: {str(e)}",
                "query": "複数パターン検索（Bing）",
                "results": [],
                "total_results": 0
            }
    
    def _search_single_pattern(self, search_query: str, max_results: int, character_name: str = "", api_key: str = None) -> List[Dict[str, Any]]:
        """
        単一の検索パターンを実行
        
        Args:
            search_query: 検索クエリ
            max_results: 最大取得結果数
            character_name: キャラクター名
            api_key: OpenAI API Key
            
        Returns:
            検索結果のリスト
        """
        search_results = []
        
        max_retries = 3
        retry_delay = 30  # 30秒待機
        
        for retry in range(max_retries):
            try:
                # Bing検索を実行
                bing_results = self._perform_bing_search(search_query, max_results)
                
                # 各結果から情報を取得
                for result in bing_results:
                    try:
                        # ページ内容を取得
                        content_info = self._extract_page_content(result["url"], character_name, api_key)
                        if content_info:
                            # Bingの検索結果情報も含める
                            content_info["title"] = result.get("title", content_info.get("title", ""))
                            content_info["description"] = result.get("description", content_info.get("description", ""))
                            search_results.append(content_info)
                        
                        # レート制限対策
                        time.sleep(self.delay)
                        
                    except Exception as e:
                        print(f"URL取得エラー ({result.get('url', 'unknown')}): {e}")
                        continue
                
                # 成功した場合はループを抜ける
                break
                        
            except Exception as search_error:
                error_str = str(search_error)
                print(f"検索パターン実行エラー ({search_query}): {search_error}")
                
                # レート制限エラーの場合
                if "429" in error_str or "Too Many Requests" in error_str:
                    if retry < max_retries - 1:
                        wait_time = retry_delay * (retry + 1)  # 段階的に待機時間を増加
                        print(f"レート制限のため {wait_time} 秒待機してからリトライします (試行 {retry + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"最大リトライ回数に達しました。検索パターンをスキップします: {search_query}")
                        break
                else:
                    # レート制限以外のエラーの場合はリトライしない
                    break
        
        return search_results
    
    def _perform_bing_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Bing検索を実行してURLリストを取得
        
        Args:
            query: 検索クエリ
            max_results: 最大取得結果数
            
        Returns:
            検索結果のリスト（URLとタイトル、説明を含む辞書のリスト）
        """
        results = []
        
        try:
            # Bing検索URL
            search_url = "https://www.bing.com/search"
            params = {
                'q': query,
                'setlang': 'ja',  # 日本語設定
                'count': min(max_results, 50)  # 最大50件まで
            }
            
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Bingの検索結果要素を探す
            # Bingの検索結果は複数のセレクタパターンがある
            result_selectors = [
                'li.b_algo',  # 通常の検索結果
                '.b_algo',    # 代替パターン
                'ol#b_results li'  # より広範なパターン
            ]
            
            result_elements = []
            for selector in result_selectors:
                elements = soup.select(selector)
                if elements:
                    result_elements = elements
                    break
            
            for element in result_elements[:max_results]:
                try:
                    # タイトルとURL
                    title_element = element.select_one('h2 a, h3 a, .b_title a')
                    if not title_element:
                        continue
                    
                    title = title_element.get_text(strip=True)
                    url = title_element.get('href', '')
                    
                    # 相対URLを修正
                    if url.startswith('/'):
                        url = 'https://www.bing.com' + url
                    elif not url.startswith(('http://', 'https://')):
                        continue
                    
                    # 説明文
                    desc_element = element.select_one('.b_caption p, .b_snippet, .b_descript')
                    description = desc_element.get_text(strip=True) if desc_element else ""
                    
                    if title and url:
                        results.append({
                            "title": title,
                            "url": url,
                            "description": description
                        })
                        
                except Exception as e:
                    print(f"Bing結果解析エラー: {e}")
                    continue
                    
        except Exception as e:
            print(f"Bing検索実行エラー ({query}): {e}")
        
        return results
    
    def _extract_page_content(self, url: str, character_name: str = "", api_key: str = None) -> Dict[str, Any]:
        """
        指定されたURLからページ内容を抽出
        
        Args:
            url: 対象URL
            character_name: キャラクター名
            api_key: OpenAI API Key
            
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
            response = safe_http_get(url, max_retries=2, timeout=15, logger=None, quiet=True)  # 一般的なHTTPエラーはログに記録せず、出力も抑制
            
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            domain = urlparse(url).netloc  # ドメイン情報を先に取得
            
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
            body_text = body_text[:config.search.google_page_limit] if body_text else ""
            
            # 口調・セリフ関連の文をChatGPT APIで抽出（API keyがある場合のみ）
            speech_patterns = []
            if api_key and len(body_text.strip()) > 50:  # 十分なテキストがある場合のみ
                try:
                    speech_patterns = self._extract_speech_patterns(body_text, character_name, api_key)
                except Exception as api_error:
                    print(f"    API抽出スキップ ({domain}): {api_error}")
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
            return None
        except Exception as e:
            print(f"コンテンツ抽出エラー ({url}): {e}")
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
            if len(name) > 2:  # 名前が短すぎる場合の誤ヒット防止
                search_queries.extend([
                    f'"{name}" site:youtube.com'
                ])
            
            youtube_urls = []
            
            for search_query in search_queries:
                if len(youtube_urls) >= config.search.youtube_max_urls:
                    break
                    
                print(f"YouTube検索中（Bing）: {search_query}")
                
                try:
                    bing_results = self._perform_bing_search(search_query, 20)
                    
                    for result in bing_results:
                        url = result.get("url", "")
                        # 動画URLを収集
                        if 'youtube.com/watch?v=' in url and url not in youtube_urls:
                            youtube_urls.append(url)
                            print(f"  - 動画URL発見: {url}")
                        
                        if len(youtube_urls) >= config.search.youtube_max_urls:
                            break
                        
                except Exception as search_error:
                    print(f"YouTube検索実行エラー ({search_query}): {search_error}")
                    continue
                
                # クエリ間の待機
                time.sleep(self.delay)
            
            print(f"YouTube動画URL取得完了（Bing）: {len(youtube_urls)}件")
            return youtube_urls
            
        except Exception as e:
            print(f"YouTube検索エラー（Bing）: {e}")
            return []
    
    def _extract_speech_patterns(self, text: str, character_name: str = "", api_key: str = None) -> List[str]:
        """
        テキストから口調・セリフパターンをChatGPT APIで抽出
        
        Args:
            text: 対象テキスト
            character_name: キャラクター名（オプション）
            api_key: OpenAI API Key（オプション）
            
        Returns:
            抽出されたセリフパターンのリスト
        """
        try:
            if not text or not api_key:
                return []
            
            # テキストが長すぎる場合は切り詰め
            if len(text) > 2000:
                text = text[:2000]
            
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            system_prompt = """あなたは日本語テキストから言語的特徴を中立的に抽出する専門家です。
事前の知識や推測に頼らず、提供されたテキストに実際に含まれている言語的特徴のみを抽出してください。"""
            
            context_info = f"キャラクター名: {character_name}" if character_name else "キャラクター名: 不明"
            
            user_prompt = f"""以下のテキストから、話し方や言語的特徴を中立的に抽出してください。

{context_info}

【抽出対象】
1. 一人称（実際にテキストで使用されているもののみ）
2. 語尾パターン（実際にテキストで使用されているもののみ）
   - あらゆる形の語尾を見逃さずに抽出
   - ひらがな・カタカナ・記号の組み合わせも正確に保持
   - 短い語尾、長い語尾、珍しい語尾も含む
3. 特徴的な表現や決まり文句（実際にテキストで使用されているもののみ）
4. 呼び方や敬語の使用パターン（実際にテキストで使用されているもののみ）

【重要な原則】
- テキストに実際に書かれていることのみを抽出
- 推測や一般的な知識は使用しない
- 特定の表現様式を排除しない
- 特殊語尾や珍しい語尾も見逃さずに抽出
- テキストに含まれる全ての文字・記号を完全な形で保持
- 語尾の変化形も含めて抽出
- 見つからない場合は出力しない

【出力形式】
各項目を1行ずつ、以下の形式で出力：
一人称: [実際に使用されていた一人称]
語尾: [実際に使用されていた語尾]
表現: [実際に使用されていた特徴的表現]
呼び方: [実際に使用されていた呼び方]

見つからない項目は出力しないでください。

分析対象テキスト:
{text}"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.1  # より厳密に入力に従う
            )
            
            result_text = response.choices[0].message.content.strip()
            speech_patterns = []
            
            # 結果を解析
            for line in result_text.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    speech_patterns.append(line)
            
            # デバッグ用（少量のテキストの場合のみ表示）
            if len(text) < 200 and speech_patterns:
                print(f"    ChatGPT抽出結果（Bing）: {len(speech_patterns)}件")
            
            return speech_patterns[:10]  # 最大10個まで
            
        except Exception as e:
            print(f"ChatGPT音声パターン抽出エラー（Bing）: {e}")
            return []