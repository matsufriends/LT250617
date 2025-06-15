"""
YouTube字幕収集モジュール
"""

import re
import random
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
from config import (
    YOUTUBE_MAX_VIDEOS, YOUTUBE_MAX_TRANSCRIPTS, YOUTUBE_TRANSCRIPT_CHAR_LIMIT,
    SAMPLE_PHRASES_MAX, SAMPLE_PHRASE_MIN_LENGTH, SAMPLE_PHRASE_MAX_LENGTH,
    SAMPLE_QUALITY_MIN_LENGTH, SAMPLE_QUALITY_MAX_LENGTH,
    CHATGPT_MODEL, CHATGPT_FILTER_MAX_TOKENS, CHATGPT_FILTER_TEMPERATURE,
    CHATGPT_FILTER_TEXT_LIMIT
)


class YouTubeCollector:
    """YouTube動画の字幕を収集するクラス"""
    
    def __init__(self):
        """初期化"""
        self.formatter = TextFormatter()
    
    def collect_info(self, youtube_urls: List[str], max_videos: int = YOUTUBE_MAX_VIDEOS, logger=None) -> Dict[str, Any]:
        """
        YouTube URLから字幕情報を収集
        
        Args:
            youtube_urls: YouTube URLのリスト
            max_videos: 処理する最大動画数
            
        Returns:
            収集した字幕情報の辞書
        """
        try:
            if not youtube_urls:
                return {
                    "found": False,
                    "error": "YouTube URLが提供されませんでした",
                    "transcripts": [],
                    "total_videos": 0,
                    "sample_phrases": []
                }
            
            print(f"  {len(youtube_urls)}個の動画から字幕を収集中...")
            
            transcripts = []
            all_text = []
            
            for i, url in enumerate(youtube_urls[:max_videos]):
                video_id = self._extract_video_id(url)
                if not video_id:
                    print(f"  動画{i+1}: 無効なURL - {url}")
                    continue
                
                print(f"  動画{i+1} (ID: {video_id[:11]}): 字幕取得中...")
                transcript_info = self._get_video_transcript(video_id)
                
                if transcript_info["found"]:
                    transcripts.append(transcript_info)
                    all_text.append(transcript_info["text"])
                    # 取得したテキストの一部を表示（デバッグ用）
                    preview = transcript_info["text"][:100].replace('\n', ' ')
                    print(f"  ✅ 字幕取得成功 ({transcript_info['word_count']}語) - プレビュー: {preview}...")
                else:
                    print(f"  ❌ 字幕取得失敗: {transcript_info['error']}")
                
                # 字幕が十分取得できたら早期終了
                if len(transcripts) >= YOUTUBE_MAX_TRANSCRIPTS:
                    print(f"  十分な字幕データを取得しました ({len(transcripts)}動画)")
                    break
            
            # サンプルフレーズを抽出
            sample_phrases = self._extract_sample_phrases(all_text)
            
            # サンプル品質チェック
            quality_checked_phrases = self._check_sample_quality(sample_phrases)
            
            print(f"  📝 サンプルフレーズ抽出: {len(sample_phrases)}個 → 品質チェック後: {len(quality_checked_phrases)}個")
            
            # デバッグ用：抽出されたフレーズの一部を表示
            if quality_checked_phrases:
                print("  📋 抽出されたサンプル（最初の5個）:")
                for i, phrase in enumerate(quality_checked_phrases[:5]):
                    print(f"    {i+1}. {phrase}")
            else:
                print("  ⚠️ サンプルフレーズが抽出されませんでした")
            
            return {
                "found": len(transcripts) > 0,
                "error": None if len(transcripts) > 0 else "字幕付き動画が見つかりませんでした",
                "transcripts": transcripts,
                "total_videos": len(transcripts),
                "sample_phrases": quality_checked_phrases,
                "processed_urls": len(youtube_urls),
                "successful_extractions": len(transcripts)
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": f"YouTube字幕収集エラー: {str(e)}",
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
            limited_text = full_text[:YOUTUBE_TRANSCRIPT_CHAR_LIMIT] if full_text else ""
            
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
    
    def _extract_sample_phrases(self, text_list: List[str], max_phrases: int = SAMPLE_PHRASES_MAX) -> List[str]:
        """
        テキストからサンプルフレーズを抽出（完全に中立的な抽出）
        
        Args:
            text_list: テキストのリスト
            max_phrases: 抽出する最大フレーズ数
            
        Returns:
            サンプルフレーズのリスト
        """
        try:
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
                    not re.match(r'^[あ-ん]{1,3}$', sentence) and
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
                    phrase.count('。') > 3):  # 複数文が混在している場合
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
- {character_name}らしい発言のみ10個以内
- 各発言を改行で区切る
- 重複は避ける
- 不確実な場合は除外

字幕テキスト:
{all_text}
"""
            
            response = client.chat.completions.create(
                model=CHATGPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=CHATGPT_FILTER_MAX_TOKENS,
                temperature=CHATGPT_FILTER_TEMPERATURE
            )
            
            filtered_text = response.choices[0].message.content.strip()
            filtered_phrases = [phrase.strip() for phrase in filtered_text.split('\n') if phrase.strip()]
            
            print(f"  ✅ {len(filtered_phrases)}個の{character_name}らしい発言を特定")
            
            # APIのやり取りも返す
            return {
                "filtered_phrases": filtered_phrases[:10],
                "api_interaction": {
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response": filtered_text,
                    "model": CHATGPT_MODEL,
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