"""
Google検索情報収集モジュール
"""

import re
import time
import requests
from googlesearch import search
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urlparse
from config import (
    GOOGLE_SEARCH_RESULTS, GOOGLE_REQUEST_DELAY, GOOGLE_PAGE_CONTENT_LIMIT,
    YOUTUBE_MAX_URLS, YOUTUBE_SEARCH_DELAY
)


class GoogleCollector:
    """Google検索結果から情報を収集するクラス"""
    
    def __init__(self, delay: float = GOOGLE_REQUEST_DELAY):
        """
        初期化
        
        Args:
            delay: リクエスト間の待機時間（秒）
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect_info(self, name: str, num_results: int = GOOGLE_SEARCH_RESULTS, logger=None, api_key: str = None) -> Dict[str, Any]:
        """
        指定された名前の人物情報をGoogle検索から収集
        
        Args:
            name: 検索対象の人物名
            num_results: 取得する検索結果数
            
        Returns:
            収集した情報の辞書
        """
        try:
            all_search_results = []
            
            # より多様なキャラクター類型に対応した検索パターン
            search_patterns = [
                f'"{name}" 人物 プロフィール',
                f'"{name}" 名台詞集',
                f'"{name}" セリフ一覧', 
                f'"{name}" 口癖 語尾',
                f'"{name}" 話し方 特徴',
                f'"{name}" キャラクター 性格',
                f'"{name}" 一人称 呼び方',
                f'"{name}" 決まり文句',
                f'"{name}" とは 特徴',
                f'"{name}" 解説 まとめ'
            ]
            
            results_per_pattern = max(1, num_results // len(search_patterns))
            
            for pattern in search_patterns:
                print(f"Google検索中: {pattern}")
                pattern_results = self._search_single_pattern(pattern, results_per_pattern, name, api_key)
                all_search_results.extend(pattern_results)
                
                # パターン間で少し待機
                time.sleep(self.delay)
            
            return {
                "found": len(all_search_results) > 0,
                "error": None,
                "query": "複数パターン検索",
                "results": all_search_results,
                "total_results": len(all_search_results)
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": f"Google検索エラー: {str(e)}",
                "query": "複数パターン検索",
                "results": [],
                "total_results": 0
            }
    
    def _search_single_pattern(self, search_query: str, max_results: int, character_name: str = "", api_key: str = None) -> List[Dict[str, Any]]:
        """
        単一の検索パターンを実行
        
        Args:
            search_query: 検索クエリ
            max_results: 最大取得結果数
            
        Returns:
            検索結果のリスト
        """
        search_results = []
        
        try:
            # Google検索を実行
            search_urls = []
            for url in search(search_query):
                search_urls.append(url)
                if len(search_urls) >= max_results:
                    break
                time.sleep(self.delay)  # 手動でレート制限
            
            # 各URLから情報を取得
            for url in search_urls:
                try:
                    # ページ内容を取得
                    content_info = self._extract_page_content(url, character_name, api_key)
                    if content_info:
                        search_results.append(content_info)
                    
                    # レート制限対策
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"URL取得エラー ({url}): {e}")
                    continue
                    
        except Exception as search_error:
            print(f"検索パターン実行エラー ({search_query}): {search_error}")
        
        return search_results
    
    def _extract_page_content(self, url: str, character_name: str = "", api_key: str = None) -> Dict[str, Any]:
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
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
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
            body_text = body_text[:GOOGLE_PAGE_CONTENT_LIMIT] if body_text else ""
            
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
            
            # 一般的なキャラクター検索のみ（キャラクター特有の情報は含めない）
            
            # 除外キーワードを廃止（ユーザー要求により）
            
            youtube_urls = []
            
            for search_query in search_queries:
                if len(youtube_urls) >= YOUTUBE_MAX_URLS:
                    break
                    
                print(f"YouTube検索中: {search_query}")
                
                try:
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
                    continue
                
                # クエリ間の待機
                time.sleep(self.delay)
            
            print(f"YouTube動画URL取得完了: {len(youtube_urls)}件")
            return youtube_urls
            
        except Exception as e:
            print(f"YouTube検索エラー: {e}")
            return []
    
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
3. 特徴的な表現や決まり文句（実際にテキストで使用されているもののみ）
4. 呼び方や敬語の使用パターン（実際にテキストで使用されているもののみ）

【重要な原則】
- テキストに実際に書かれていることのみを抽出
- 推測や一般的な知識は使用しない
- 特定の表現様式を排除しない
- 見つからない場合は「なし」と回答

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
                temperature=0.3
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
                print(f"    ChatGPT抽出結果: {len(speech_patterns)}件")
            
            return speech_patterns[:10]  # 最大10個まで
            
        except Exception as e:
            print(f"ChatGPT音声パターン抽出エラー: {e}")
            return []
    
