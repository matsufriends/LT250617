"""
プロンプト生成モジュール
"""

import openai
from typing import Dict, Any
from config import config


class PromptGenerator:
    """収集した情報からChatGPT用プロンプトを生成するクラス"""
    
    def __init__(self, api_key: str, model: str = None):
        """
        初期化
        
        Args:
            api_key: OpenAI API Key
            model: 使用するモデル名
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model or config.api.openai_model
    
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
                max_tokens=config.api.openai_max_tokens,
                temperature=config.api.openai_temperature
            )
            
            generated_prompt = response.choices[0].message.content.strip()
            print("✅ ChatGPT APIからレスポンスを受信しました")
            
            # 生成されたプロンプトを使用してキャラクターの自己紹介を生成
            character_introduction = self._generate_character_introduction(generated_prompt, character_info.get("name", "unknown"))
            
            # コンテンツポリシー対応版プロンプトを生成
            policy_safe_prompt = self._generate_policy_safe_prompt(generated_prompt, character_info.get("name", "unknown"))
            
            # APIやり取りを結果に含める
            return {
                "generated_prompt": generated_prompt,
                "policy_safe_prompt": policy_safe_prompt,
                "character_introduction": character_introduction,
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
            if logger:
                logger.log_error("openai_prompt_generation_error", str(e), {
                    "character_name": character_info.get("name", "unknown"),
                    "error_type": type(e).__name__,
                    "model": self.model
                })
            print("📝 フォールバックプロンプトを生成しています...")
            # エラー時は基本的なプロンプトを返す
            fallback_prompt = self._generate_fallback_prompt(character_info)
            
            # フォールバック時も自己紹介を生成
            fallback_introduction = self._generate_character_introduction(fallback_prompt, character_info.get("name", "unknown"))
            
            # フォールバック時もポリシー対応版を生成
            fallback_policy_safe = self._generate_policy_safe_prompt(fallback_prompt, character_info.get("name", "unknown"))
            
            return {
                "generated_prompt": fallback_prompt,
                "policy_safe_prompt": fallback_policy_safe,
                "character_introduction": fallback_introduction,
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
                categories = ", ".join(wiki_info["categories"][:config.processing.max_key_information])
                organized["key_information"].append(f"カテゴリ: {categories}")
        
        # Google検索結果の整理
        google_info = character_info.get("google_search_results", {})
        if google_info.get("found") and google_info.get("results"):
            organized["google_results_count"] = len(google_info["results"])
            
            # 各検索結果から重要な情報を抽出
            web_speech_patterns = []
            for result in google_info["results"][:config.processing.max_key_information]:  # 上位件数のみ
                if result.get("title"):
                    organized["key_information"].append(f"関連情報: {result['title'][:100]}")
                
                # Webページから抽出されたスピーチパターンを収集
                if result.get("speech_patterns"):
                    web_speech_patterns.extend(result["speech_patterns"])
            
            # Web検索から得られたスピーチパターンを保存
            organized["web_speech_patterns"] = web_speech_patterns[:10]  # 最大10個
            
            # 生のテキストデータも保存（絵文字保持のため）
            raw_content = []
            for result in google_info["results"][:3]:  # 上位3件の生テキスト
                if result.get("content"):
                    # 1000文字以内の抜粋
                    content_excerpt = result["content"][:1000]
                    if content_excerpt.strip():
                        raw_content.append(content_excerpt)
            organized["raw_web_content"] = raw_content
        
        # YouTube情報の整理
        youtube_info = character_info.get("youtube_transcripts", {})
        if youtube_info.get("found"):
            organized["youtube_found"] = True
            organized["sample_phrases"] = youtube_info.get("sample_phrases", [])
            organized["youtube_speech_analysis"] = youtube_info.get("speech_pattern_analysis", {})
        
        return organized
    
    def _build_system_prompt(self) -> str:
        """システムプロンプトを構築"""
        return """あなたは、収集された情報に基づいて架空のキャラクターの話し方を分析し、教育的で創作支援目的のロールプレイプロンプトを作成する専門家です。

以下のような詳細で構造化されたプロンプトを生成してください：

【理想的なプロンプト構造】
1. **キャラクターの役割**: 具体的な設定（基本的な性格、立場）
2. **言語的特徴**: 一人称、語尾、特徴的表現を正確に指定
3. **話し方の詳細**: 口調、敬語の使用有無、特徴的なパターン
4. **対人関係**: 相手との関係性、呼び方、接し方
5. **性格・行動原理**: 根底にある価値観、思考パターン
6. **具体的な表現例**: 実際のデータに基づく表現例を提示
7. **キャラクターガイドライン**: 一貫性を保つための詳細な指示
8. **知識と回答スタイル**: キャラクター性を最優先にした回答方法

【分析重点項目】
- 語尾パターン: 実際のデータから抽出された語尾を完全な形で分析
- 一人称と呼び方: 実際のデータで使用されている一人称を特定
- 特徴的な決まり文句: データから抽出された実際の表現を保持
- 口調の特徴: 実際の発言から読み取れる口調パターンを分析
- 性格的特徴: データに基づいた客観的な性格分析
- 対人関係: 実際の発言から推測される関係性の特徴

【重要：エンタメ重視の指針】
このプロンプトはエンターテインメント目的であり、キャラクター性を最優先とします：
- **正確性よりもキャラクター性を優先**
- 技術的な質問や専門的な内容でも、キャラクターらしい反応を重視
- 「わからない」「興味ない」「適当な回答」もキャラクターの個性として歓迎
- 嘘や間違いもキャラクター性の一部として許容
- 面白さ・個性・エンタメ価値を正確性より上位に置く

【出力要件】
- 会話形式で即座に使用できる完成されたプロンプト
- 具体的な表現例を含める
- 一貫性を保つための詳細な指示を含める
- 相手役の設定も明確に定義する
- キャラクター性を最優先にした回答スタイルを明記
- エンタメ重視の注意事項を含める

収集した情報を詳細に分析し、エンターテインメント性とキャラクター性を最優先にしたプロンプトを作成してください。"""
    
    def _build_user_prompt(self, organized_info: Dict[str, Any]) -> str:
        """ユーザープロンプトを構築"""
        character_name = organized_info['name']
        
        # センシティブな可能性のあるキャラクター名を一般化
        safe_character_reference = "対象キャラクター" if self._is_potentially_sensitive(character_name) else character_name
        
        prompt_parts = [
            f"収集された情報に基づいて、特定のキャラクターの口調・話し方を完全に再現するChatGPT用プロンプトを作成してください。",
            f"対象キャラクター名: {character_name}",
            "",
            "【分析対象情報】"
        ]
        
        # Wikipedia情報
        if organized_info["wikipedia_found"]:
            prompt_parts.extend([
                f"■ 基本情報（Wikipedia）",
                organized_info["wikipedia_summary"][:config.collector.wikipedia_summary_limit] + "...",
                ""
            ])
        
        # 重要な情報
        if organized_info["key_information"]:
            prompt_parts.append("■ 追加の基本情報")
            for info in organized_info["key_information"][:config.processing.max_key_information]:  # 重要な件数のみ
                prompt_parts.append(f"- {info}")
            prompt_parts.append("")
        
        # Web検索から抽出されたスピーチパターン
        if organized_info.get("web_speech_patterns"):
            prompt_parts.extend([
                f"■ 口調・語尾情報（Web検索より）",
                "以下はWebページから抽出された話し方の特徴です："
            ])
            for pattern in organized_info["web_speech_patterns"]:
                if pattern.strip():
                    prompt_parts.append(f"- {pattern}")
            prompt_parts.append("")
        
        # 生のWebコンテンツ（絵文字保持のため）
        if organized_info.get("raw_web_content"):
            prompt_parts.extend([
                f"■ 関連Webページ内容（抜粋）",
                "以下は実際のWebページから取得した生のテキストです："
            ])
            for i, content in enumerate(organized_info["raw_web_content"][:2], 1):
                if content.strip():
                    prompt_parts.append(f"【資料{i}】")
                    prompt_parts.append(content)
                    prompt_parts.append("")
        
        # YouTube言語特徴分析結果
        if organized_info.get("youtube_speech_analysis"):
            prompt_parts.extend([
                f"■ 言語特徴分析（YouTube字幕より）",
                "以下は動画字幕から分析された言語的特徴です："
            ])
            analysis = organized_info["youtube_speech_analysis"]
            for key, value in analysis.items():
                if value.strip():
                    pattern_num = key.replace("pattern_", "")
                    prompt_parts.append(f"- 項目{pattern_num}: {value}")
            prompt_parts.append("")
        
        # YouTube発言サンプル
        if organized_info["youtube_found"] and organized_info["sample_phrases"]:
            prompt_parts.extend([
                f"■ 実際の発言サンプル（YouTube動画より）",
                "以下は動画から抽出された実際の話し方です："
            ])
            for phrase in organized_info["sample_phrases"][:config.processing.max_sample_phrases_display]:  # サンプル数は設定から
                if phrase.strip():
                    prompt_parts.append(f"「{phrase}」")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "【詳細分析要求】",
            f"上記の全ての情報を総合的に分析し、対象キャラクターの完全なロールプレイ用プロンプトを作成してください。",
            "",
            "【必須要素】",
            "1. **【あなたの役割】**: キャラクターの詳細な設定",
            "2. **言語的特徴**: 一人称、語尾の適切な使用指示",
            "3. **話し方のパターン**: 特徴的な表現の適切な使用",
            "4. **対人関係**: 相手との関係性の明確化",
            "5. **性格・価値観**: 思考パターンの正確な表現",
            "6. **具体的表現例**: 特徴的な決まり文句を10個程度",
            "7. **【回答スタイル】**: エンタメ重視・キャラクター性優先の回答方法",
            "8. **【キャラクターガイドライン】**: 一貫性を保つ詳細指示",
            "9. **【私の役割】**: 相手役の設定も明確に定義",
            "10. **注意事項**: エンタメ重視・キャラクター性優先の指示",
            "",
            "【分析観点（エンタメ重視）】",
            f"- 収集データから対象キャラクターの最も特徴的な語尾や表現パターンは何か？",
            f"- 実際のデータの一人称と呼び方を適切に使用するには？",
            f"- データから読み取れる性格特徴をエンタメ性を重視して表現するには？",
            f"- キャラクターらしさを面白く魅力的に表現するための指示は？",
            f"- 技術的質問や専門知識にどのようなキャラクター的反応をするか？",
            "",
            "【重要な原則（エンタメ優先）】",
            "- 収集されたデータを最優先に分析し、エンタメ性を重視して表現する",
            "- 実際に抽出された語尾・一人称・表現を魅力的に使用するよう指示する",
            "- 特定の一人称や表現様式を排除せず、面白く使用する", 
            "- 収集データに含まれる全ての特徴をエンタメ性を重視して活用する",
            "- キャラクター性を正確性より優先し、面白さと個性を最重視する",
            "- 技術的質問でも「わからない」「興味ない」「嘘回答」もキャラ次第で歓迎",
            "",
            f"Web検索とYouTube動画から得られた実際のデータを最大限活用し、対象キャラクターの本質を",
            "エンターテインメント性とキャラクター性を最重視して表現した、面白く魅力的なロールプレイプロンプトを生成してください。",
            "",
            "【最重要】生成されるプロンプトには以下を明確に含めること：",
            "- 技術的・専門的質問への個性的な反応指示",
            "- 正確性よりキャラクター性を優先する指示",
            "- 「わからない」「興味ない」などもキャラクター表現として推奨",
            "- エンタメ目的でありキャラ演技を最優先する旨",
            "",
            "出力は「以下の情報をもとに、エンターテインメント重視のロールプレイを行います」で始めてください。"
        ])
        
        return "\n".join(prompt_parts)
    
    def _is_potentially_sensitive(self, character_name: str) -> bool:
        """
        キャラクター名がセンシティブな可能性があるかチェック
        
        Args:
            character_name: キャラクター名
            
        Returns:
            センシティブな可能性がある場合True
        """
        sensitive_patterns = [
            'メスガキ', 'メス', 'ガキ', 'クソ', '殺', '死', 'エロ', 'セクシー',
            '爆乳', 'ロリ', 'ショタ', '変態', '淫', '姦', '卑猥'
        ]
        
        name_lower = character_name.lower()
        for pattern in sensitive_patterns:
            if pattern.lower() in name_lower:
                return True
        return False
    
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
                organized_info["wikipedia_summary"][:config.collector.wikipedia_fallback_limit] + "...",
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
    
    def _generate_character_introduction(self, role_prompt: str, character_name: str) -> Dict[str, Any]:
        """
        生成されたプロンプトを使用してキャラクターの自己紹介を生成
        
        Args:
            role_prompt: 生成されたロールプレイプロンプト
            character_name: キャラクター名
            
        Returns:
            自己紹介生成の結果
        """
        try:
            print("🎭 キャラクターの自己紹介を生成中...")
            
            # ロールプレイプロンプトをそのまま使用
            introduction_prompt = f"""あなたは以下のプロンプトに従って、自己紹介を行ってください。

{role_prompt}

【自己紹介の指示（エンタメ重視）】
上記のキャラクター設定に完全に従って、そのキャラクターとして自己紹介をしてください。
- 200文字程度の自己紹介
- そのキャラクターらしい口調・語尾・表現を魅力的に使用
- 一人称や特徴的な表現を面白く含める
- キャラクター性をエンタメ重視で表現
- 性格特徴を魅力的で個性的に表現
- そのキャラクターらしい印象的で面白い自己紹介にする
- 正確性より個性とエンタメ性を優先

それでは、{character_name}としてエンタメ重視の自己紹介をどうぞ："""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": introduction_prompt}
                ],
                max_tokens=300,
                temperature=0.8  # 少し創造性を持たせる
            )
            
            introduction_text = response.choices[0].message.content.strip()
            print("✅ キャラクター自己紹介を生成しました")
            
            return {
                "introduction_text": introduction_text,
                "api_interaction": {
                    "prompt": introduction_prompt,
                    "response": introduction_text,
                    "model": self.model,
                    "character_name": character_name
                }
            }
            
        except Exception as e:
            print(f"⚠️ 自己紹介生成エラー: {e}")
            # エラーをログに記録（logger は _generate_character_introduction の引数ではないため、グローバルに記録できません）
            # エラー時は簡単な自己紹介を返す
            fallback_introduction = f"はじめまして、{character_name}です。よろしくお願いします。"
            return {
                "introduction_text": fallback_introduction,
                "api_interaction": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "fallback_used": True,
                    "character_name": character_name
                }
            }
    
    def _generate_policy_safe_prompt(self, original_prompt: str, character_name: str) -> Dict[str, Any]:
        """
        ChatGPTのコンテンツポリシーに配慮したプロンプトを生成
        
        Args:
            original_prompt: 元のプロンプト
            character_name: キャラクター名
            
        Returns:
            ポリシー対応版プロンプトの結果
        """
        try:
            print("🛡️ コンテンツポリシー対応版プロンプトを生成中...")
            
            # キャラクター名をより安全な形に変換
            safe_char_ref = "対象キャラクター" if self._is_potentially_sensitive(character_name) else character_name
            
            safety_prompt = f"""以下は創作・教育目的のキャラクター分析から生成されたロールプレイプロンプトです。このプロンプトをより幅広い利用者に適切な形で修正してください。

【修正方針】
1. キャラクターの言語的特徴（一人称、語尾、口調）は保持
2. 創作・教育目的として適切な表現に調整
3. 幅広い年齢層に適用可能な内容に修正
4. キャラクターの本質的な性格特徴は維持
5. 建設的で健全な会話を促進する方向に調整

【重要な原則】
- 収集データに基づく言語的特徴は維持
- 性格の核となる特徴は保持
- 表現の仕方のみを調整し、本質は変更しない
- ChatGPTのカスタム指示として問題なく保存できる内容にする

【元のプロンプト内容】
{original_prompt}

【出力要求】
上記を参考に、以下の要件を満たす修正版を作成してください：
- カスタム指示として安全に保存可能
- {safe_char_ref}の核となる言語的特徴を維持
- 建設的で教育的な利用を前提とした内容
- 様々な年齢層に適用可能

修正版プロンプト："""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": safety_prompt}
                ],
                max_tokens=config.api.openai_max_tokens,
                temperature=0.3  # 安全側に振る
            )
            
            safe_prompt = response.choices[0].message.content.strip()
            print("✅ コンテンツポリシー対応版プロンプトを生成しました")
            
            return {
                "safe_prompt": safe_prompt,
                "api_interaction": {
                    "prompt": safety_prompt,
                    "response": safe_prompt,
                    "model": self.model,
                    "character_name": character_name
                }
            }
            
        except Exception as e:
            print(f"⚠️ ポリシー対応版生成エラー: {e}")
            # エラーをログに記録（logger は _generate_policy_safe_prompt の引数ではないため、グローバルに記録できません）
            # エラー時は基本的な安全版を返す
            safe_fallback = f"""以下の情報をもとに、ロールプレイを行います。

【あなたの役割】
・{character_name}として適切な範囲でキャラクターを演じる
・収集された情報に基づいて口調・語尾・性格を再現する
・常識的で建設的な会話を心がける

【話し方の特徴】
・{character_name}特有の一人称や語尾を使用
・{character_name}らしい性格を適切に表現
・相手に対して敬意を持った接し方をする

【注意事項】
・不適切な内容は避け、健全な会話を維持する
・{character_name}らしさを保ちつつ、適切な表現を使用する"""
            
            return {
                "safe_prompt": safe_fallback,
                "api_interaction": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "fallback_used": True,
                    "character_name": character_name
                }
            }