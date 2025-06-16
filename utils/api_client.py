"""
API呼び出し用の共通クライアント
"""

import time
from typing import Dict, Any, Optional, List
from openai import OpenAI

from config import (OPENAI_MODEL, OPENAI_MAX_TOKENS, OPENAI_TEMPERATURE,
                    API_PROMPT_SLICE_LENGTH, CHATGPT_FILTER_TEXT_LIMIT,
                    OPENAI_FILTER_MAX_TOKENS, OPENAI_FILTER_TEMPERATURE,
                    OPENAI_SEARCH_MAX_TOKENS, OPENAI_SEARCH_TEMPERATURE)
from core.exceptions import OpenAIError
from utils.execution_logger import ExecutionLogger


class OpenAIClient:
    """OpenAI API用の共通クライアント"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.api_key = api_key
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        logger: Optional[ExecutionLogger] = None,
        api_type: str = "openai_chat_completion"
    ) -> Dict[str, Any]:
        """
        ChatGPT APIを呼び出す
        
        Args:
            messages: メッセージリスト
            model: 使用するモデル
            max_tokens: 最大トークン数
            temperature: Temperature値
            logger: ログ記録用
            api_type: APIタイプ（ログ用）
            
        Returns:
            API応答と呼び出し情報
        """
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model or OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens or OPENAI_MAX_TOKENS,
                temperature=temperature or OPENAI_TEMPERATURE
            )
            
            duration = time.time() - start_time
            result_text = response.choices[0].message.content.strip()
            
            api_info = {
                "model": model or OPENAI_MODEL,
                "messages": messages,
                "max_tokens": max_tokens or OPENAI_MAX_TOKENS,
                "temperature": temperature or OPENAI_TEMPERATURE,
                "duration": duration
            }
            
            # ログ記録
            if logger:
                request_data = {
                    "model": api_info["model"],
                    "messages_count": len(messages),
                    "system_prompt": messages[0]["content"][:API_PROMPT_SLICE_LENGTH] + "..." if messages and len(messages[0]["content"]) > API_PROMPT_SLICE_LENGTH else messages[0]["content"] if messages else "",
                    "user_prompt": messages[-1]["content"][:API_PROMPT_SLICE_LENGTH] + "..." if len(messages) > 1 and len(messages[-1]["content"]) > API_PROMPT_SLICE_LENGTH else messages[-1]["content"] if len(messages) > 1 else ""
                }
                
                response_data = {
                    "result": result_text,
                    "result_length": len(result_text)
                }
                
                logger.log_api_call(api_type, request_data, response_data, duration)
            
            return {
                "result": result_text,
                "api_info": api_info,
                "duration": duration
            }
            
        except Exception as e:
            duration = time.time() - start_time
            
            if logger:
                logger.log_error(f"{api_type}_error", str(e), {
                    "model": model or OPENAI_MODEL,
                    "messages_count": len(messages),
                    "duration": duration
                })
            
            raise OpenAIError(
                f"OpenAI API呼び出し失敗: {str(e)}",
                details={"api_type": api_type, "duration": duration},
                original_error=e
            )
    
    def extract_speech_patterns(
        self, 
        text: str, 
        character_name: str = "", 
        logger: Optional[ExecutionLogger] = None
    ) -> List[str]:
        """
        テキストから口調・セリフパターンをChatGPT APIで抽出
        
        Args:
            text: 対象テキスト
            character_name: キャラクター名
            logger: ログ記録用
            
        Returns:
            抽出されたセリフパターンのリスト
        """
        try:
            if not text:
                return []
            
            # テキストが長すぎる場合は切り詰め
            if len(text) > CHATGPT_FILTER_TEXT_LIMIT:
                text = text[:CHATGPT_FILTER_TEXT_LIMIT]
            
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
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.chat_completion(
                messages=messages,
                max_tokens=OPENAI_FILTER_MAX_TOKENS,
                temperature=OPENAI_FILTER_TEMPERATURE,
                logger=logger,
                api_type="openai_speech_pattern_extraction"
            )
            
            result_text = response["result"]
            speech_patterns = []
            
            # 結果を解析
            for line in result_text.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    speech_patterns.append(line)
            
            return speech_patterns[:10]  # 最大10個まで
            
        except Exception as e:
            if logger:
                logger.log_error("speech_pattern_extraction_error", str(e), {
                    "character_name": character_name,
                    "text_length": len(text) if text else 0,
                    "error_type": type(e).__name__
                })
            return []
    
    def search_character_info(
        self, 
        search_query: str, 
        character_name: str, 
        logger: Optional[ExecutionLogger] = None
    ) -> Optional[str]:
        """
        ChatGPTの知識ベースからキャラクター情報を検索
        
        Args:
            search_query: 検索クエリ
            character_name: キャラクター名
            logger: ログ記録用
            
        Returns:
            検索結果テキスト
        """
        try:
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
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.chat_completion(
                messages=messages,
                max_tokens=OPENAI_SEARCH_MAX_TOKENS,
                temperature=OPENAI_SEARCH_TEMPERATURE,
                logger=logger,
                api_type="openai_chatgpt_search"
            )
            
            return response["result"]
            
        except Exception as e:
            if logger:
                logger.log_error("chatgpt_search_error", str(e), {
                    "search_query": search_query,
                    "character_name": character_name,
                    "error_type": type(e).__name__
                })
            return None