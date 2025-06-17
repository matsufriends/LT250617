"""
YouTube字幕収集モジュール
"""

import re
import random
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
from core.interfaces import CharacterQuote
from config import (
    YOUTUBE_MAX_VIDEOS, YOUTUBE_MAX_TRANSCRIPTS, YOUTUBE_TRANSCRIPT_LIMIT,
    SAMPLE_PHRASES_MAX, SAMPLE_PHRASE_MIN_LENGTH, SAMPLE_PHRASE_MAX_LENGTH,
    SAMPLE_QUALITY_MIN_LENGTH, SAMPLE_QUALITY_MAX_LENGTH,
    CHATGPT_FILTER_TEXT_LIMIT, OPENAI_MODEL, OPENAI_FILTER_MAX_TOKENS,
    OPENAI_FILTER_TEMPERATURE, get_search_patterns,
    YOUTUBE_VIDEO_ID_DISPLAY_LENGTH, YOUTUBE_PREVIEW_TEXT_LENGTH,
    YOUTUBE_SAMPLE_DISPLAY_LIMIT, YOUTUBE_MIN_SENTENCE_LENGTH,
    YOUTUBE_MAX_SINGLE_CHAR_LENGTH, YOUTUBE_MAX_PERIOD_COUNT,
    YOUTUBE_FILTER_PHRASE_LIMIT, YOUTUBE_ANALYSIS_TEXT_LIMIT,
    YOUTUBE_ANALYSIS_MAX_TOKENS, REGEX_JAPANESE_CHAR_MIN, REGEX_JAPANESE_CHAR_MAX
)


class YouTubeCollector:
    """YouTube動画の字幕を収集するクラス"""
    
    def __init__(self):
        """初期化"""
        self.formatter = TextFormatter()
    
    def collect_info(self, youtube_urls: List[str], max_videos: int = None, logger=None, character_info: Dict = None, api_key: str = None) -> Dict[str, Any]:
        """
        YouTube URLから字幕情報を収集
        
        Args:
            youtube_urls: YouTube URLのリスト
            max_videos: 処理する最大動画数
            
        Returns:
            収集した字幕情報の辞書
        """
        try:
            if max_videos is None:
                max_videos = YOUTUBE_MAX_VIDEOS
                
            if not youtube_urls:
                return {
                    "found": False,
                    "error": "YouTube URLが提供されませんでした",
                    "transcripts": [],
                    "total_videos": 0,
                    "sample_phrases": []
                }
            
            print(f"  {len(youtube_urls)}個の動画から字幕を収集中（最大{max_videos}動画）...")
            
            transcripts = []
            all_text = []
            total_videos = min(len(youtube_urls), max_videos)
            
            for i, url in enumerate(youtube_urls[:max_videos]):
                video_id = self._extract_video_id(url)
                if not video_id:
                    print(f"  動画{i+1}: 無効なURL - {url}")
                    continue
                
                print(f"  動画{i+1}/{total_videos} (ID: {video_id[:YOUTUBE_VIDEO_ID_DISPLAY_LENGTH]}): 字幕取得中...")
                transcript_info = self._get_video_transcript(video_id)
                
                if transcript_info["found"]:
                    transcripts.append(transcript_info)
                    all_text.append(transcript_info["text"])
                    # 取得したテキストの一部を表示（デバッグ用）
                    preview = transcript_info["text"][:YOUTUBE_PREVIEW_TEXT_LENGTH].replace('\n', ' ')
                    print(f"    ✅ 字幕取得成功 ({transcript_info['word_count']}語, {transcript_info['language']})")
                    print(f"    プレビュー: {preview}...")
                else:
                    print(f"    ❌ 字幕取得失敗: {transcript_info['error']}")
                
                # 字幕が十分取得できたら早期終了
                if len(transcripts) >= YOUTUBE_MAX_TRANSCRIPTS:
                    print(f"  十分な字幕データを取得しました ({len(transcripts)}動画)")
                    break
            
            # サンプルフレーズを抽出
            print(f"\n  📝 サンプルフレーズ抽出中...")
            sample_phrases = self._extract_sample_phrases(all_text)
            
            # サンプル品質チェック
            quality_checked_phrases = self._check_sample_quality(sample_phrases)
            
            # 検索パターン相当の言語特徴抽出（API keyがある場合）
            pattern_analysis = {}
            if api_key and all_text:
                print(f"  🤔 言語パターン分析中 (ChatGPT API)...")
                pattern_analysis = self._analyze_speech_patterns(all_text, character_info.get("name", ""), api_key)
            
            print(f"  📝 サンプルフレーズ抽出: {len(sample_phrases)}個 → 品質チェック後: {len(quality_checked_phrases)}個")
            
            # デバッグ用：抽出されたフレーズの一部を表示
            if quality_checked_phrases:
                print(f"  📋 抽出されたサンプル（最初の{YOUTUBE_SAMPLE_DISPLAY_LIMIT}個）:")
                for i, phrase in enumerate(quality_checked_phrases[:YOUTUBE_SAMPLE_DISPLAY_LIMIT]):
                    print(f"    {i+1}. {phrase}")
            else:
                print("  ⚠️ サンプルフレーズが抽出されませんでした")
            
            # CharacterQuoteオブジェクトとしてセリフを整理
            character_quotes = []
            for phrase in quality_checked_phrases:
                # YouTubeソースは基本的に信頼性は中程度
                # キャラクター名がセリフに含まれるか、APIでフィルタリングされている場合は信頼性を上げる
                confidence = 0.5  # デフォルト信頼性
                character_name = character_info.get("name", "") if character_info else ""
                
                # キャラクター名がセリフに含まれる場合は信頼性アップ
                if character_name and character_name in phrase:
                    confidence = 0.8
                
                quote = CharacterQuote(
                    text=phrase,
                    source="youtube",
                    source_url=None,  # 複数の動画から集約されているため
                    confidence_score=confidence,
                    context="YouTube動画字幕からChatGPT APIで抽出"
                )
                # 辞書形式に変換してから追加（JSON保存のため）
                character_quotes.append(quote.to_dict())
            
            return {
                "found": len(transcripts) > 0,
                "error": None if len(transcripts) > 0 else "字幕付き動画が見つかりませんでした",
                "transcripts": transcripts,
                "total_videos": len(transcripts),
                "sample_phrases": quality_checked_phrases,
                "character_quotes": character_quotes,  # CharacterQuoteオブジェクトのリストを追加
                "processed_urls": len(youtube_urls),
                "successful_extractions": len(transcripts),
                "speech_pattern_analysis": pattern_analysis  # 検索パターン相当の分析結果
            }
            
        except Exception as e:
            import traceback
            error_msg = f"YouTube字幕収集エラー: {str(e)}"
            error_traceback = traceback.format_exc()
            
            print(f"❌ YouTube字幕収集エラーの詳細:")
            print(f"エラー: {error_msg}")
            print(f"トレースバック:\n{error_traceback}")
            
            return {
                "found": False,
                "error": error_msg,
                "transcripts": [],
                "total_videos": 0,
                "sample_phrases": []
            }
    
    def _extract_video_id(self, url: str) -> str:
        """
        YouTubeのURLから動画IDを抽出
        
        Args:
            url: YouTube URL
            
        Returns:
            動画ID（見つからない場合はNone）
        """
        try:
            # 様々なYouTube URLパターンに対応
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
                r'youtube\.com/watch\?.*v=([^&\n?#]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            return None
        except Exception:
            return None
    
    def _get_video_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        指定された動画IDの字幕を取得
        
        Args:
            video_id: YouTube動画ID
            
        Returns:
            字幕情報の辞書
        """
        try:
            # 利用可能な字幕言語を取得
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 日本語字幕を優先的に取得
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['ja', 'jp'])
            except:
                # 日本語がない場合は英語を試す
                try:
                    transcript = transcript_list.find_transcript(['en'])
                except:
                    # 自動生成字幕を試す
                    try:
                        transcript = transcript_list.find_generated_transcript(['ja', 'jp', 'en'])
                    except:
                        pass
            
            if not transcript:
                return {
                    "found": False,
                    "error": "利用可能な字幕が見つかりませんでした",
                    "video_id": video_id,
                    "text": "",
                    "language": None
                }
            
            # 字幕データを取得
            transcript_data = transcript.fetch()
            
            # テキストを結合（正しい属性アクセス）
            text_parts = []
            for entry in transcript_data:
                if hasattr(entry, 'text'):
                    text_parts.append(entry.text)
                elif isinstance(entry, dict) and 'text' in entry:
                    text_parts.append(entry['text'])
                else:
                    # FetchedTranscriptSnippetオブジェクトの場合
                    text_parts.append(str(entry))
            
            full_text = ' '.join(text_parts)
            
            # テキストを制限
            limited_text = full_text[:YOUTUBE_TRANSCRIPT_LIMIT] if full_text else ""
            
            return {
                "found": True,
                "error": None,
                "video_id": video_id,
                "text": limited_text,
                "language": transcript.language_code,
                "is_generated": transcript.is_generated,
                "word_count": len(limited_text.split())
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": f"字幕取得エラー: {str(e)}",
                "video_id": video_id,
                "text": "",
                "language": None
            }
    
    def _extract_sample_phrases(self, text_list: List[str], max_phrases: int = None) -> List[str]:
        """
        テキストからサンプルフレーズを抽出（完全に中立的な抽出）
        
        Args:
            text_list: テキストのリスト
            max_phrases: 抽出する最大フレーズ数
            
        Returns:
            サンプルフレーズのリスト
        """
        try:
            if max_phrases is None:
                max_phrases = SAMPLE_PHRASES_MAX
                
            all_text = ' '.join(text_list)
            
            if not all_text:
                return []
            
            # ノイズを除去（[音楽]、[拍手]などの記号）
            cleaned_text = re.sub(r'\[.*?\]', '', all_text)
            
            # 文章を分割
            sentences = re.split(r'[。！？\.\!\?]', cleaned_text)
            
            filtered_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                
                # 基本的なフィルタリングのみ（特徴的パターンによる優先順位付けは廃止）
                if (SAMPLE_PHRASE_MIN_LENGTH <= len(sentence) <= SAMPLE_PHRASE_MAX_LENGTH and 
                    not re.match(r'^[音楽拍手効果音]+', sentence) and
                    not re.match(rf'^[あ-ん]{{{REGEX_JAPANESE_CHAR_MIN},{REGEX_JAPANESE_CHAR_MAX}}}$', sentence) and
                    sentence not in ['', ' ', 'うん', 'そう', 'はい', 'えー', 'あー']):
                    
                    filtered_sentences.append(sentence)
            
            # 重複を除去
            unique_sentences = []
            seen = set()
            for sentence in filtered_sentences:
                # 正規化して重複チェック
                normalized = re.sub(r'\s+', '', sentence.lower())  # 空白除去＋小文字化
                if normalized not in seen and len(normalized) > SAMPLE_PHRASE_MIN_LENGTH:
                    unique_sentences.append(sentence)
                    seen.add(normalized)
            
            # ランダムに選択（優先順位なし）
            if len(unique_sentences) > max_phrases:
                return random.sample(unique_sentences, max_phrases)
            else:
                return unique_sentences
            
        except Exception as e:
            print(f"サンプルフレーズ抽出エラー: {e}")
            return []
    
    def _check_sample_quality(self, sample_phrases: List[str]) -> List[str]:
        """
        サンプルフレーズの品質をチェック
        
        Args:
            sample_phrases: 抽出されたサンプルフレーズのリスト
            
        Returns:
            品質チェック済みのサンプルフレーズ
        """
        try:
            quality_phrases = []
            
            # 品質基準
            for phrase in sample_phrases:
                phrase = phrase.strip()
                
                # 基本的な品質チェック
                if (len(phrase) < SAMPLE_QUALITY_MIN_LENGTH or len(phrase) > SAMPLE_QUALITY_MAX_LENGTH or
                    phrase.count('詰んだろうが') > 0 or  # 明らかに間違った文を除外
                    phrase.count('教会の常識') > 0 or
                    re.match(r'^[同じ文章の繰り返し]', phrase) or
                    phrase.count('。') > YOUTUBE_MAX_PERIOD_COUNT):  # 複数文が混在している場合
                    continue
                
                # 意味のある文かどうかチェック
                if (not re.match(r'^[あいうえおかきくけこ]+$', phrase) and  # 意味のない文字列
                    not re.match(r'^[音楽効果音]+', phrase) and
                    phrase not in ['', ' ', 'はい', 'そう', 'うん']):
                    quality_phrases.append(phrase)
            
            return quality_phrases
            
        except Exception as e:
            print(f"サンプル品質チェックエラー: {e}")
            return sample_phrases  # エラー時は元のリストを返す
    
    def filter_character_speech(self, text_list: List[str], character_name: str, api_key: str = None) -> List[str]:
        """
        字幕テキストから特定キャラクターの発言を抽出
        
        Args:
            text_list: 字幕テキストのリスト
            character_name: 対象キャラクター名
            api_key: OpenAI API Key（オプション）
            
        Returns:
            フィルタリングされた発言リスト
        """
        if not api_key:
            # API Keyがない場合は基本的なフィルタリングのみ
            return self._extract_sample_phrases(text_list)
        
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            all_text = ' '.join(text_list)
            if len(all_text) > CHATGPT_FILTER_TEXT_LIMIT:  # テキストが長すぎる場合は切り詰め
                all_text = all_text[:CHATGPT_FILTER_TEXT_LIMIT]
            
            print(f"  ChatGPT APIで{character_name}の発言を特定中...")
            
            # プロンプトを構築（キャラクター特有の特徴を含める）
            system_prompt = "あなたは字幕から特定キャラクターの発言を抽出する専門家です。キャラクターの特徴的な口調や語尾を正確に識別し、他のキャラクターや関係ない発言は確実に除外してください。"
            
            # キャラクター固有の特徴を追加
            character_features = self._get_character_features(character_name)
            
            user_prompt = f"""
以下の字幕テキストから「{character_name}」が話している部分だけを正確に抽出してください。

【{character_name}の分析対象特徴】
{character_features}

【抽出基準】
1. {character_name}特有の語尾や口調を含む発言を抽出
2. {character_name}特有の一人称を使った発言を抽出
3. {character_name}らしい性格や特徴を示す発言を抽出
4. 明らかに他のキャラクターの特徴を持つ発言は除外

【除外すべき発言】
- 関係のないナレーションや説明文
- [音楽]や[拍手]などの効果音
- 明らかに{character_name}と無関係な会話
- 技術的な説明や実況コメント

【出力要求】
- {character_name}らしい発言のみ{YOUTUBE_FILTER_PHRASE_LIMIT}個以内
- 各発言を改行で区切る
- 重複は避ける
- 不確実な場合は除外

字幕テキスト:
{all_text}
"""
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=OPENAI_FILTER_MAX_TOKENS,
                temperature=OPENAI_FILTER_TEMPERATURE
            )
            
            filtered_text = response.choices[0].message.content.strip()
            filtered_phrases = [phrase.strip() for phrase in filtered_text.split('\n') if phrase.strip()]
            
            print(f"  ✅ {len(filtered_phrases)}個の{character_name}らしい発言を特定")
            
            # APIのやり取りも返す
            return {
                "filtered_phrases": filtered_phrases[:YOUTUBE_FILTER_PHRASE_LIMIT],
                "api_interaction": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response": filtered_text,
                    "model": OPENAI_MODEL,
                    "character_name": character_name
                }
            }
            
        except Exception as e:
            print(f"  ❌ ChatGPT APIによるフィルタリング失敗: {e}")
            # フォールバック: 基本的なフィルタリング
            return {
                "filtered_phrases": self._extract_sample_phrases(text_list),
                "api_interaction": {
                    "error": str(e),
                    "fallback_used": True
                }
            }
    
    def _get_character_features(self, character_name: str) -> str:
        """
        キャラクター固有の特徴を取得（中立的な分析指示のみ）
        
        Args:
            character_name: キャラクター名
            
        Returns:
            キャラクターの特徴文字列
        """
        # 事前定義されたキャラクター特徴は廃止（ユーザー要求により）
        # 完全に中立的な分析指示のみを提供
        return f"""
- {character_name}特有の一人称や呼び方
- {character_name}特有の語尾や口調パターン
- {character_name}特有の性格を表す話し方
- {character_name}特有の表現方法や決まり文句
- 他のキャラクターと区別される言語的特徴
"""
    
    def _analyze_speech_patterns(self, text: str, character_name: str, api_key: str) -> Dict[str, Any]:
        """
        YouTube字幕から検索パターン相当の言語特徴を分析
        
        Args:
            text: 字幕テキスト
            character_name: キャラクター名
            api_key: OpenAI API Key
            
        Returns:
            分析結果の辞書
        """
        try:
            if not text or not api_key:
                return {}
            
            # テキストが長すぎる場合は切り詰め
            if len(text) > YOUTUBE_ANALYSIS_TEXT_LIMIT:
                text = text[:YOUTUBE_ANALYSIS_TEXT_LIMIT]
            
            import openai
            client = openai.OpenAI(api_key=api_key)
            
            # 検索パターンを取得
            search_patterns = get_search_patterns(character_name)
            pattern_descriptions = [
                "人物プロフィール・基本情報",
                "名台詞・決まり文句",
                "セリフ・発言例",
                "口癖・語尾",
                "話し方・特徴",
                "キャラクター・性格",
                "一人称・呼び方",
                "決まり文句・常套句",
                "特徴・特性",
                "解説・まとめ"
            ]
            
            system_prompt = """あなたは動画字幕から話者の言語的特徴を中立的に分析する専門家です。
話者の特定に注意を払い、指定されたキャラクターの発言のみを分析してください。"""
            
            user_prompt = f"""以下の動画字幕から「{character_name}」の言語的特徴を分析してください。

【重要】話者の特定について：
- 複数の話者が混在している可能性があります
- {character_name}の発言と判断できるもののみを分析対象とする
- 不明確な場合は「不明」として扱う

【分析項目】
以下の各項目について、字幕から読み取れる情報を抽出してください：
1. 人物プロフィール・基本情報
2. 名台詞・決まり文句
3. セリフ・発言例
4. 口癖・語尾（あらゆる形の語尾を見逃さずに抽出）
5. 話し方・特徴
6. キャラクター・性格
7. 一人称・呼び方
8. 決まり文句・常套句
9. 特徴・特性
10. 解説・まとめ

【語尾について】
- あらゆる形の語尾を見逃さずに抽出
- 短い語尾、長い語尾、珍しい語尾も含む
- 変化形も含む
- 句読点との組み合わせも正確に記録

【原則】
- 字幕に実際に含まれている内容のみを抽出
- {character_name}以外の話者の発言は除外
- 推測や一般的な知識は使用しない
- 特殊語尾や珍しい語尾も見逃さずに抽出
- 語尾の全ての変化形を含めて抽出
- 見つからない項目は「なし」と記載

【出力形式】
各項目を以下の形式で出力：
項目1: [抽出された内容またはなし]
項目2: [抽出された内容またはなし]
...

字幕テキスト:
{text}"""
            
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=YOUTUBE_ANALYSIS_MAX_TOKENS,
                temperature=OPENAI_FILTER_TEMPERATURE
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # 結果を解析して構造化
            analysis_result = {}
            lines = result_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line and line.startswith('項目'):
                    try:
                        # "項目1: 内容" の形式から抽出
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            item_num = parts[0].replace('項目', '').strip()
                            content = parts[1].strip()
                            if content and content != 'なし':
                                analysis_result[f"pattern_{item_num}"] = content
                    except:
                        continue
            
            print(f"  🎯 YouTube言語特徴分析: {len(analysis_result)}項目抽出")
            
            return analysis_result
            
        except Exception as e:
            print(f"YouTube言語特徴分析エラー: {e}")
            return {}