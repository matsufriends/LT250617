"""
プロンプト生成モジュール
"""

import openai
from typing import Dict, Any
from config import (
    CHATGPT_MODEL, CHATGPT_MAX_TOKENS, CHATGPT_TEMPERATURE,
    WIKIPEDIA_SUMMARY_LIMIT, WIKIPEDIA_FALLBACK_LIMIT,
    MAX_KEY_INFORMATION, MAX_SAMPLE_PHRASES_DISPLAY
)


class PromptGenerator:
    """収集した情報からChatGPT用プロンプトを生成するクラス"""
    
    def __init__(self, api_key: str, model: str = CHATGPT_MODEL):
        """
        初期化
        
        Args:
            api_key: OpenAI API Key
            model: 使用するモデル名
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def generate_voice_prompt(self, character_info: Dict[str, Any], logger=None) -> str:
        """
        キャラクター情報から口調設定プロンプトを生成
        
        Args:
            character_info: 収集したキャラクター情報
            
        Returns:
            生成されたプロンプト
        """
        try:
            # 情報を整理
            organized_info = self._organize_information(character_info)
            
            # ChatGPTに送信するプロンプトを構築
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(organized_info)
            
            print("ChatGPT APIにリクエスト送信中...")
            
            # ChatGPT APIを呼び出し
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=CHATGPT_MAX_TOKENS,
                temperature=CHATGPT_TEMPERATURE
            )
            
            generated_prompt = response.choices[0].message.content.strip()
            print("✅ ChatGPT APIからレスポンスを受信しました")
            
            # APIやり取りを結果に含める
            return {
                "generated_prompt": generated_prompt,
                "api_interaction": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response": generated_prompt,
                    "model": self.model,
                    "character_name": character_info.get("name", "unknown")
                }
            }
            
        except Exception as e:
            print(f"⚠️ ChatGPT API呼び出しエラー: {e}")
            print("📝 フォールバックプロンプトを生成しています...")
            # エラー時は基本的なプロンプトを返す
            fallback_prompt = self._generate_fallback_prompt(character_info)
            return {
                "generated_prompt": fallback_prompt,
                "api_interaction": {
                    "error": str(e),
                    "fallback_used": True,
                    "character_name": character_info.get("name", "unknown")
                }
            }
    
    def _organize_information(self, character_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        収集した情報を整理
        
        Args:
            character_info: 生の情報
            
        Returns:
            整理された情報
        """
        organized = {
            "name": character_info.get("name", "不明"),
            "wikipedia_found": False,
            "wikipedia_summary": "",
            "google_results_count": 0,
            "key_information": [],
            "youtube_found": False,
            "sample_phrases": []
        }
        
        # Wikipedia情報の整理
        wiki_info = character_info.get("wikipedia_info", {})
        if wiki_info.get("found"):
            organized["wikipedia_found"] = True
            organized["wikipedia_summary"] = wiki_info.get("summary", "")
            
            # 重要な情報を抽出
            if wiki_info.get("title"):
                organized["key_information"].append(f"正式名称: {wiki_info['title']}")
            if wiki_info.get("categories"):
                categories = ", ".join(wiki_info["categories"][:MAX_KEY_INFORMATION])
                organized["key_information"].append(f"カテゴリ: {categories}")
        
        # Google検索結果の整理
        google_info = character_info.get("google_search_results", {})
        if google_info.get("found") and google_info.get("results"):
            organized["google_results_count"] = len(google_info["results"])
            
            # 各検索結果から重要な情報を抽出
            web_speech_patterns = []
            for result in google_info["results"][:MAX_KEY_INFORMATION]:  # 上位件数のみ
                if result.get("title"):
                    organized["key_information"].append(f"関連情報: {result['title'][:100]}")
                
                # Webページから抽出されたスピーチパターンを収集
                if result.get("speech_patterns"):
                    web_speech_patterns.extend(result["speech_patterns"])
            
            # Web検索から得られたスピーチパターンを保存
            organized["web_speech_patterns"] = web_speech_patterns[:10]  # 最大10個
        
        # YouTube情報の整理
        youtube_info = character_info.get("youtube_transcripts", {})
        if youtube_info.get("found"):
            organized["youtube_found"] = True
            organized["sample_phrases"] = youtube_info.get("sample_phrases", [])
        
        return organized
    
    def _build_system_prompt(self) -> str:
        """システムプロンプトを構築"""
        return """あなたは、キャラクターの口調や話し方を分析し、高品質で実用的なロールプレイ用プロンプトを作成する専門家です。

以下の例のような詳細で構造化されたプロンプトを生成してください：

【理想的なプロンプト構造】
1. **キャラクターの役割**: 明確で具体的な設定（年齢、立場、基本性格）
2. **言語的特徴**: 一人称、語尾、特徴的表現を具体的に指定
3. **話し方の詳細**: 口調、敬語の使用有無、特徴的なパターン
4. **対人関係**: 相手との関係性、呼び方、接し方
5. **性格・行動原理**: 根底にある価値観、思考パターン
6. **具体的な表現例**: 「○○❤」のような実際の使用例を豊富に提示
7. **キャラクターガイドライン**: 一貫性を保つための詳細な指示
8. **禁止事項**: そのキャラクターらしくない表現の明確な指示

【分析重点項目】
- 語尾パターン（絵文字含む）: 実際のデータから抽出された語尾を分析
- 一人称と呼び方: 実際のデータで使用されている一人称を正確に特定
- 特徴的な決まり文句: データから抽出された実際の表現を重視
- 口調の特徴: 実際の発言から読み取れる口調パターンを分析  
- 性格的特徴: データに基づいた客観的な性格分析
- 対人関係: 実際の発言から推測される関係性の特徴

【出力要件】
- 会話形式で即座に使用できる完成されたプロンプト
- 具体的な表現例を10個以上含める
- 一貫性を保つための詳細な指示を含める
- 相手役の設定も明確に定義する
- ロールプレイが崩れないための注意事項を明記

収集した情報を詳細に分析し、そのキャラクターの本質を完全に捉えた高品質なプロンプトを作成してください。"""
    
    def _build_user_prompt(self, organized_info: Dict[str, Any]) -> str:
        """ユーザープロンプトを構築"""
        character_name = organized_info['name']
        
        prompt_parts = [
            f"「{character_name}」の口調・話し方を完全に再現するChatGPT用プロンプトを作成してください。",
            "",
            "【分析対象情報】"
        ]
        
        # Wikipedia情報
        if organized_info["wikipedia_found"]:
            prompt_parts.extend([
                f"■ {character_name}の基本情報（Wikipedia）",
                organized_info["wikipedia_summary"][:WIKIPEDIA_SUMMARY_LIMIT] + "...",
                ""
            ])
        
        # 重要な情報
        if organized_info["key_information"]:
            prompt_parts.append("■ 追加の基本情報")
            for info in organized_info["key_information"][:MAX_KEY_INFORMATION]:  # 重要な件数のみ
                prompt_parts.append(f"- {info}")
            prompt_parts.append("")
        
        # Web検索から抽出されたスピーチパターン
        if organized_info.get("web_speech_patterns"):
            prompt_parts.extend([
                f"■ {character_name}の口調・語尾情報（Web検索より）",
                "以下はWebページから抽出された話し方の特徴です："
            ])
            for pattern in organized_info["web_speech_patterns"]:
                if pattern.strip():
                    prompt_parts.append(f"- {pattern}")
            prompt_parts.append("")
        
        # YouTube発言サンプル
        if organized_info["youtube_found"] and organized_info["sample_phrases"]:
            prompt_parts.extend([
                f"■ {character_name}の実際の発言サンプル（YouTube動画より）",
                "以下は動画から抽出された実際の話し方です："
            ])
            for phrase in organized_info["sample_phrases"][:MAX_SAMPLE_PHRASES_DISPLAY]:  # サンプル数は設定から
                if phrase.strip():
                    prompt_parts.append(f"「{phrase}」")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "【詳細分析要求】",
            f"上記の全ての情報を総合的に分析し、{character_name}の完全なロールプレイ用プロンプトを作成してください。",
            "",
            "【必須要素】",
            "1. **【あなたの役割】**: キャラクターの詳細な設定（年齢、立場、基本性格）",
            "2. **言語的特徴**: 一人称、語尾（絵文字含む）、口調の詳細",
            "3. **話し方のパターン**: 敬語の使用、方言、特徴的な表現",
            "4. **対人関係**: 相手の呼び方、接し方、距離感",
            "5. **性格・価値観**: 思考パターン、行動原理、根底にある特徴",
            "6. **具体的表現例**: 特徴的な決まり文句を10個以上",
            "7. **【キャラクターガイドライン】**: 一貫性を保つための詳細指示",
            "8. **【私の役割】**: 相手役の設定も明確に定義",
            "9. **注意事項**: キャラクター崩れを防ぐための指示",
            "",
            "【分析観点】",
            f"- 収集データから{character_name}の最も特徴的な語尾や表現パターンは何か？",
            f"- 実際のデータで{character_name}が使用している一人称と相手の呼び方は？",
            f"- データから読み取れる{character_name}の基本的な性格や対人関係は？",
            f"- 収集したデータに基づき、{character_name}らしくない表現は何か？",
            "",
            "【重要な原則】",
            "- 収集されたデータを最優先に分析し、推測や一般論は避ける",
            "- 実際に抽出された語尾・一人称・表現を正確に反映させる", 
            "- 特定の一人称や表現様式を排除せず、データに忠実に従う",
            "",
            f"Web検索とYouTube動画から得られた実際のデータを最大限活用し、{character_name}の本質を完全に捉えた",
            "実用的で詳細なロールプレイプロンプトを生成してください。",
            "",
            "出力は「以下の情報をもとに、ロールプレイを行います」で始めてください。"
        ])
        
        return "\n".join(prompt_parts)
    
    def _generate_fallback_prompt(self, character_info: Dict[str, Any]) -> str:
        """
        API呼び出しが失敗した場合のフォールバックプロンプトを生成
        
        Args:
            character_info: キャラクター情報
            
        Returns:
            基本的なプロンプト
        """
        name = character_info.get("name", "不明なキャラクター")
        
        # 収集した情報を活用してより良いフォールバックを作成
        organized_info = self._organize_information(character_info)
        
        fallback_parts = [
            "以下の情報をもとに、ロールプレイを行います。",
            "会話形式のやりとりで進行し、キャラクター性を保ちながら自由に発言してください。",
            "",
            "【あなたの役割】",
            f"・{name}として一貫したキャラクターを演じる",
            "・収集された情報に基づいて適切な口調・語尾・性格を再現する",
            ""
        ]
        
        # Wikipedia情報があれば追加
        if organized_info["wikipedia_found"]:
            fallback_parts.extend([
                "## 基本情報",
                organized_info["wikipedia_summary"][:WIKIPEDIA_FALLBACK_LIMIT] + "...",
                ""
            ])
        
        # Web検索パターンがあれば追加
        if organized_info.get("web_speech_patterns"):
            fallback_parts.extend([
                "## 口調・語尾特徴（Web検索より）",
                "以下の特徴を参考にしてください："
            ])
            for pattern in organized_info["web_speech_patterns"][:5]:
                if pattern.strip():
                    fallback_parts.append(f"- {pattern}")
            fallback_parts.append("")
        
        # YouTube発言サンプルがあれば追加
        if organized_info["youtube_found"] and organized_info["sample_phrases"]:
            fallback_parts.extend([
                "## 実際の発言例（YouTube動画より）",
                "以下の話し方を参考にしてください："
            ])
            for phrase in organized_info["sample_phrases"][:5]:
                if phrase.strip():
                    fallback_parts.append(f"- 「{phrase}」")
            fallback_parts.append("")
        
        # より詳細な指示（収集データに基づく）
        fallback_parts.extend([
            "【キャラクターガイドライン】",
            f"・{name}の特徴的な一人称・語尾・口調を一貫して使用する",
            f"・{name}らしい性格や価値観を常に保つ",
            "・どんな話題でもキャラクター性を崩さない",
            "・相手との関係性に応じた適切な距離感を保つ",
            "",
            "【話し方の詳細指示】",
            f"1. **一人称**: 収集データから{name}の一人称を特定し一貫使用",
            f"2. **語尾・口調**: {name}特有の語尾や表現パターンを活用", 
            f"3. **敬語使用**: {name}の敬語使用パターンに従う",
            f"4. **特徴的表現**: {name}らしい決まり文句や表現を適切に使用",
            f"5. **性格反映**: {name}の基本的な性格や価値観を発言に反映",
            "",
            "【注意事項】",
            f"・{name}らしくない表現や態度は避ける",
            "・話題が変わってもキャラクター性を維持する",
            "・収集された情報と矛盾する設定は使用しない",
            ""
        ])
        
        # 追加情報があれば言及
        info_sources = []
        if organized_info["wikipedia_found"]:
            info_sources.append("Wikipedia")
        if organized_info["google_results_count"] > 0:
            info_sources.append(f"Google検索({organized_info['google_results_count']}件)")
        if organized_info["youtube_found"]:
            info_sources.append("YouTube動画")
        
        if info_sources:
            fallback_parts.append(f"※ {', '.join(info_sources)}から収集した情報を基に作成されています。")
        
        # API呼び出し失敗の注意書き
        fallback_parts.append("※ ChatGPT APIが利用できないため、基本的なプロンプト形式で提供しています。")
        
        return "\n".join(fallback_parts)