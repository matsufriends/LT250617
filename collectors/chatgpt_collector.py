"""
ChatGPT知識ベース検索モジュール
"""

import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from core.interfaces import BaseCollector, CollectionResult, SearchResult
from utils.execution_logger import ExecutionLogger
from config import (
    get_search_patterns, CHATGPT_DEFAULT_DELAY, CHATGPT_SEARCH_MAX_TOKENS,
    CHATGPT_MAX_QUOTES, CHATGPT_MIN_QUOTE_LENGTH, CHATGPT_MAX_PATTERNS,
    CHATGPT_TOP_KEYWORDS, CHATGPT_KEYWORD_MAX_TOKENS, CHATGPT_MAX_KEYWORDS,
    SPEECH_PATTERN_EXTRACTION_TEMPERATURE, API_PROMPT_SLICE_LENGTH,
    OPENAI_MODEL_GPT4O, FRACTION_THREE_HALVES
)

# .envファイルから環境変数を読み込み
load_dotenv()

class ChatGPTCollector(BaseCollector):
    """ChatGPTの知識ベースからキャラクター情報を収集するクラス"""
    
    def __init__(self, delay: float = None, **kwargs):
        """
        初期化
        
        Args:
            delay: API呼び出し間の待機時間（秒）
        """
        super().__init__(delay or CHATGPT_DEFAULT_DELAY, **kwargs)
    
    def collect_info(self, name: str, logger: Optional[ExecutionLogger] = None, api_key: Optional[str] = None, **kwargs) -> CollectionResult:
        """
        ChatGPTの知識ベースからキャラクター情報を収集
        
        Args:
            name: 検索対象のキャラクター名
            logger: 実行ログ記録用
            api_key: OpenAI API Key
            
        Returns:
            収集結果の辞書
        """
        try:
            if not api_key:
                return self._create_error_result("ChatGPT検索にはOpenAI API Keyが必要です")
            
            print(f"  ChatGPT知識ベース検索: {name}")
            
            # 検索パターンを使用してChatGPTに情報を問い合わせ
            search_patterns = get_search_patterns(name)
            all_results = []
            
            for i, pattern in enumerate(search_patterns, 1):
                print(f"ChatGPT検索中 ({i}/{len(search_patterns)}): {pattern}")
                
                try:
                    result = self._search_with_chatgpt(pattern, name, api_key, logger)
                    if result:
                        all_results.append(result)
                    
                    # API制限対策で適度な待機
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"ChatGPT検索エラー ({pattern}): {e}")
                    if logger:
                        logger.log_error("chatgpt_search_error", str(e), {
                            "search_pattern": pattern,
                            "character_name": name
                        })
                    continue
            
            print(f"  ChatGPT知識ベース検索結果: {len(all_results)}件取得")
            
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
                        source="chatgpt",
                        search_query=result_dict.get("search_query", "ChatGPT知識ベース検索"),
                        api_duration=result_dict.get("api_duration")
                    )
                    search_result_objects.append(search_result)
                except Exception as e:
                    if logger:
                        logger.log_error("search_result_conversion_error", str(e), result_dict)
                    continue
            
            return self._create_success_result(search_result_objects, "ChatGPT知識ベース検索")
            
        except Exception as e:
            return self._create_error_result(f"ChatGPT検索エラー: {str(e)}", "ChatGPT知識ベース検索")
    
    def _search_with_chatgpt(self, search_query: str, character_name: str, api_key: str, logger=None) -> Dict[str, Any]:
        """
        ChatGPTに特定の情報を問い合わせ
        
        Args:
            search_query: 検索クエリ
            character_name: キャラクター名
            api_key: OpenAI API Key
            logger: ログ記録用
            
        Returns:
            検索結果の辞書
        """
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # ChatGPTに情報収集を依頼するプロンプト
            system_prompt = """あなたは日本のキャラクター、人物、作品に関する詳細な知識を持つ専門家です。
質問されたキャラクターについて、あなたの知識ベースから正確で詳細な情報を提供してください。
推測や曖昧な情報は避け、確実に知っている情報のみを回答してください。"""
            
            user_prompt = f""""{character_name}"について、以下の観点から詳しく教えてください：

検索クエリ: {search_query}

以下の項目について、知っている情報があれば詳しく説明してください：

1. 基本情報
   - 作品名・出典
   - キャラクターの設定・背景
   - 性格や特徴

2. 話し方・言語的特徴
   - 一人称（「僕」「俺」「私」「ウチ」「ワタクシ」など）
   - 語尾の特徴（「だよ」「なのだ」「ですの」「だっぺ」など）
   - 口癖や決まり文句
   - 敬語の使用パターン
   - 特徴的な表現や話し方

3. セリフの例
   - 実際の発言例があれば具体的に示してください
   - どのような場面でどんな話し方をするか

4. その他の特徴
   - 感情表現の仕方
   - 他キャラクターとの関係性での話し方の変化

知らない情報については「不明」と明記し、推測は行わないでください。
確実に知っている情報のみを、具体例を交えて詳しく説明してください。"""
            
            print(f"    ChatGPT API呼び出し: {search_query}")
            start_time = time.time()
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL_GPT4O,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=CHATGPT_SEARCH_MAX_TOKENS,
                temperature=SPEECH_PATTERN_EXTRACTION_TEMPERATURE  # より正確な情報を得るため低温度設定
            )
            
            api_duration = time.time() - start_time
            result_text = response.choices[0].message.content.strip()
            
            # API呼び出しをログに記録
            if logger:
                logger.log_api_call(
                    "openai_chatgpt_search",
                    {
                        "system_prompt": system_prompt[:API_PROMPT_SLICE_LENGTH] + "...",
                        "user_prompt": user_prompt[:int(API_PROMPT_SLICE_LENGTH * FRACTION_THREE_HALVES)] + "...",
                        "search_query": search_query,
                        "character_name": character_name,
                        "model": OPENAI_MODEL_GPT4O
                    },
                    {
                        "search_result": result_text,
                        "result_length": len(result_text)
                    },
                    api_duration
                )
            
            # 話し方パターンを抽出
            speech_patterns = self._extract_speech_patterns_from_result(result_text, character_name)
            
            return {
                "url": f"chatgpt://knowledge-base/{character_name}",
                "domain": "chatgpt.knowledge-base",
                "title": f"{character_name}に関するChatGPT知識ベース情報",
                "description": f"ChatGPTの知識ベースから取得した{character_name}の詳細情報",
                "content": result_text,
                "content_length": len(result_text),
                "speech_patterns": speech_patterns,
                "search_query": search_query,
                "api_duration": api_duration
            }
            
        except Exception as e:
            print(f"    ChatGPT API検索エラー: {e}")
            if logger:
                logger.log_error("chatgpt_api_search_error", str(e), {
                    "search_query": search_query,
                    "character_name": character_name,
                    "error_type": type(e).__name__
                })
            return None
    
    def _extract_speech_patterns_from_result(self, text: str, character_name: str) -> List[str]:
        """
        ChatGPTの回答から話し方パターンを抽出
        
        Args:
            text: ChatGPTの回答テキスト
            character_name: キャラクター名
            
        Returns:
            抽出された話し方パターンのリスト
        """
        patterns = []
        
        try:
            if not text:
                return patterns
            
            # 一人称の抽出
            import re
            
            # 一人称パターン
            pronoun_matches = re.findall(r'一人称[：:]\s*[「『"]?([^」』"\n。、]+)[」』"]?', text)
            for match in pronoun_matches:
                patterns.append(f"一人称: {match.strip()}")
            
            # 語尾パターン
            ending_matches = re.findall(r'語尾[：:]\s*[「『"]?([^」』"\n。、]+)[」』"]?', text)
            for match in ending_matches:
                patterns.append(f"語尾: {match.strip()}")
            
            # 口癖パターン
            habit_matches = re.findall(r'口癖[：:]\s*[「『"]?([^」』"\n。、]+)[」』"]?', text)
            for match in habit_matches:
                patterns.append(f"口癖: {match.strip()}")
            
            # セリフ例の抽出
            quote_matches = re.findall(r'[「『"]([^」』"]+)[」』"]', text)
            for i, quote in enumerate(quote_matches[:CHATGPT_MAX_QUOTES]):  # 最大5個まで
                if len(quote) > CHATGPT_MIN_QUOTE_LENGTH and character_name.lower() not in quote.lower():
                    patterns.append(f"セリフ例: {quote}")
            
            # 特徴的表現
            if "特徴" in text or "表現" in text:
                patterns.append("表現: 特徴的な話し方に関する情報")
                
        except Exception as e:
            print(f"パターン抽出エラー: {e}")
        
        return patterns[:CHATGPT_MAX_PATTERNS]  # 最大10個まで
    
    def search_youtube_videos(self, name: str, api_key: str = None) -> List[str]:
        """
        ChatGPTに人気のYouTube動画について質問してキーワードを取得し、
        一般的な検索でYouTube URLを探す
        
        Args:
            name: 検索対象の名前
            api_key: OpenAI API Key
            
        Returns:
            YouTube動画URLのリスト
        """
        try:
            if not api_key:
                print(f"  ChatGPT検索: API Keyがないため、YouTube動画検索をスキップ")
                return []
            
            print(f"  ChatGPTからYouTube動画情報を取得中...")
            
            # ChatGPTに人気動画について質問
            video_keywords = self._get_youtube_keywords_from_chatgpt(name, api_key)
            
            if not video_keywords:
                print(f"  ChatGPT: {name}に関するYouTube動画キーワードが見つかりませんでした")
                return []
            
            # 取得したキーワードで実際にYouTube動画を検索
            # 簡単な検索URLパターンを生成（実際のURL取得は困難なため、代表的なものを想定）
            youtube_urls = []
            for keyword in video_keywords[:CHATGPT_TOP_KEYWORDS]:  # 上位3つまで
                # 実際の検索は困難なので、想定される一般的なパターンを返す
                print(f"    YouTube検索キーワード: {keyword}")
                # ここでは実際のURL検索の代わりに、キーワード情報をYouTubeCollectorに渡す形に変更
            
            print(f"  ChatGPT YouTube検索: キーワード {len(video_keywords)}個を特定")
            return []  # 実際のURLは取得困難だが、キーワード情報は有用
            
        except Exception as e:
            print(f"  ChatGPT YouTube検索エラー: {e}")
            return []
    
    def _get_youtube_keywords_from_chatgpt(self, character_name: str, api_key: str) -> List[str]:
        """
        ChatGPTからYouTube動画の検索キーワードを取得
        
        Args:
            character_name: キャラクター名
            api_key: OpenAI API Key
            
        Returns:
            YouTube検索に使えるキーワードのリスト
        """
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            user_prompt = f""""{character_name}"に関するYouTube動画について教えてください。

具体的には以下の情報を知りたいです：
1. {character_name}が登場する有名な動画の種類やジャンル
2. {character_name}の声や話し方が聞ける可能性が高い動画の特徴
3. YouTube検索で見つけやすいキーワードの組み合わせ

実際のURLは不要です。YouTube検索に使えるキーワードを3-5個程度、以下の形式で回答してください：

キーワード1: [説明]
キーワード2: [説明]
...

YouTube動画が存在しない、または不明な場合は「不明」と回答してください。"""
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL_GPT4O,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=CHATGPT_KEYWORD_MAX_TOKENS,
                temperature=SPEECH_PATTERN_EXTRACTION_TEMPERATURE
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # キーワードを抽出
            keywords = []
            for line in result_text.split('\n'):
                if 'キーワード' in line and ':' in line:
                    keyword = line.split(':')[1].strip()
                    if keyword and keyword != '[説明]':
                        keywords.append(keyword)
            
            return keywords[:CHATGPT_MAX_KEYWORDS]  # 最大5個まで
            
        except Exception as e:
            print(f"    YouTube キーワード取得エラー: {e}")
            return []