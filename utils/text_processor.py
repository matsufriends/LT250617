"""
テキスト処理用のユーティリティ
"""

import re
from typing import List, Optional
from urllib.parse import urlparse


class TextProcessor:
    """テキスト処理のためのユーティリティクラス"""
    
    @staticmethod
    def extract_domain(url: str) -> str:
        """URLからドメインを抽出"""
        try:
            return urlparse(url).netloc
        except Exception:
            return "unknown"
    
    @staticmethod
    def clean_text(text: str, max_length: Optional[int] = None) -> str:
        """テキストをクリーニング"""
        if not text:
            return ""
        
        # 余分な空白を除去
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned = ' '.join(chunk for chunk in chunks if chunk)
        
        # 長さ制限
        if max_length and len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        return cleaned
    
    @staticmethod
    def extract_basic_patterns(text: str, character_name: str) -> List[str]:
        """基本的な話し方パターンを抽出"""
        patterns = []
        
        try:
            if not text:
                return patterns
            
            text_lower = text.lower()
            
            # キャラクター名の言及があるかチェック
            if character_name and character_name.lower() in text_lower:
                patterns.append(f"呼び方: {character_name}")
            
            # 簡単な特徴抽出
            if "口調" in text or "語尾" in text:
                patterns.append("表現: 口調・語尾に関する情報")
            
            if "一人称" in text or "話し方" in text:
                patterns.append("表現: 話し方に関する情報")
                
        except Exception as e:
            print(f"パターン抽出エラー: {e}")
        
        return patterns
    
    @staticmethod
    def extract_speech_patterns_from_chatgpt_result(text: str, character_name: str) -> List[str]:
        """ChatGPTの回答から話し方パターンを抽出"""
        patterns = []
        
        try:
            if not text:
                return patterns
            
            # 一人称の抽出
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
            for i, quote in enumerate(quote_matches[:5]):  # 最大5個まで
                if len(quote) > 3 and character_name.lower() not in quote.lower():
                    patterns.append(f"セリフ例: {quote}")
            
            # 特徴的表現
            if "特徴" in text or "表現" in text:
                patterns.append("表現: 特徴的な話し方に関する情報")
                
        except Exception as e:
            print(f"パターン抽出エラー: {e}")
        
        return patterns[:10]  # 最大10個まで


class URLProcessor:
    """URL処理のためのユーティリティクラス"""
    
    @staticmethod
    def extract_duckduckgo_url(url: str) -> str:
        """DuckDuckGoのリダイレクトURLから実際のURLを抽出"""
        try:
            if url.startswith('//duckduckgo.com/l/?uddg='):
                import urllib.parse
                # URLデコードして実際のURLを取得
                encoded_url = url.split('uddg=')[1].split('&')[0]
                return urllib.parse.unquote(encoded_url)
            return url
        except Exception:
            return url
    
    @staticmethod
    def validate_url(url: str) -> str:
        """URLの検証と修正"""
        if not url:
            return ""
        
        if not url.startswith(('http://', 'https://')):
            if url.startswith('//'):
                return 'https:' + url
            elif url.startswith('/'):
                return ""  # 相対URLは無効として除外
            else:
                return 'https://' + url
        
        return url
    
    @staticmethod
    def is_youtube_url(url: str) -> bool:
        """YouTube動画URLかどうかを判定"""
        return 'youtube.com/watch?v=' in url
    
    @staticmethod
    def filter_valid_urls(urls: List[str], exclude_domains: Optional[List[str]] = None) -> List[str]:
        """有効なURLのみをフィルタリング"""
        exclude_domains = exclude_domains or []
        valid_urls = []
        
        for url in urls:
            validated_url = URLProcessor.validate_url(url)
            if validated_url and not any(domain in validated_url for domain in exclude_domains):
                valid_urls.append(validated_url)
        
        return valid_urls