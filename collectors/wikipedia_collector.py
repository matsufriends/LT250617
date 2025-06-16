"""
Wikipedia情報収集モジュール
"""

import wikipedia
import time
from typing import Optional, Dict, Any, List

from core.interfaces import BaseCollector, CollectionResult, SearchResult
from core.exceptions import WikipediaError
from config import config
from utils.text_processor import TextProcessor
from utils.execution_logger import ExecutionLogger


class WikipediaCollector(BaseCollector):
    """Wikipedia情報を収集するクラス"""
    
    def __init__(self, language: str = 'ja', **kwargs):
        """
        初期化
        
        Args:
            language: Wikipedia言語設定 (デフォルト: 'ja')
        """
        super().__init__(**kwargs)
        self.language = language
        wikipedia.set_lang(language)
    
    def collect_info(self, name: str, logger: Optional[ExecutionLogger] = None, **kwargs) -> CollectionResult:
        """
        指定された名前の人物情報をWikipediaから収集
        
        Args:
            name: 検索対象の人物名
            logger: 実行ログ記録用
            
        Returns:
            収集した情報
        """
        start_time = time.time()
        
        try:
            # まず検索してページを特定
            search_results = wikipedia.search(name, results=5)
            
            if not search_results:
                return self._create_error_result(
                    f"'{name}'に関するWikipediaページが見つかりませんでした",
                    query=name
                )
            
            # 最適なページを選択
            page_title = self._select_best_character_option(name, search_results)
            page = wikipedia.page(page_title)
            
            result_data = {
                "title": page.title,
                "summary": page.summary[:500],  # 最初の500文字
                "content": page.content[:2000],  # 最初の2000文字
                "url": page.url,
                "categories": page.categories[:10] if hasattr(page, 'categories') else []
            }
            
            return CollectionResult(
                found=True,
                error=None,
                results=[result_data],
                total_results=1
            )
            
        except wikipedia.exceptions.DisambiguationError as e:
            # 曖昧さ回避ページの場合
            try:
                # キャラクター名らしい候補を選択
                best_option = self._select_best_character_option(name, e.options)
                page = wikipedia.page(best_option)
                
                result_data = {
                    "title": page.title,
                    "summary": page.summary[:500],
                    "content": page.content[:2000],
                    "url": page.url,
                    "categories": page.categories[:10] if hasattr(page, 'categories') else [],
                    "other_options": e.options[:5]  # 候補も記録
                }
                
                return CollectionResult(
                    found=True,
                    error=f"曖昧さ回避: {best_option} を選択しました",
                    results=[result_data],
                    total_results=1
                )
            except Exception as inner_e:
                return self._create_error_result(
                    f"曖昧さ回避エラー: {str(inner_e)}",
                    query=name,
                    details={"disambiguation_options": e.options[:5]}
                )
                
        except wikipedia.exceptions.PageError:
            return self._create_error_result(
                f"'{name}'のWikipediaページが存在しません",
                query=name
            )
            
        except Exception as e:
            return self._create_error_result(
                f"Wikipedia取得エラー: {str(e)}",
                query=name
            )
    
    def search_suggestions(self, name: str, limit: int = 10) -> List[str]:
        """
        検索候補を取得
        
        Args:
            name: 検索対象の名前
            limit: 取得する候補数
            
        Returns:
            検索候補のリスト
        """
        try:
            return wikipedia.search(name, results=limit)
        except Exception as e:
            print(f"検索候補取得エラー: {e}")
            return []
    
    def _select_best_character_option(self, original_name: str, options: List[str]) -> str:
        """
        曖昧さ回避の候補からキャラクターらしいものを選択
        
        Args:
            original_name: 元の検索名
            options: 曖昧さ回避の候補リスト
            
        Returns:
            選択された候補
        """
        if not options:
            return original_name
        
        # キャラクター名によく含まれる要素（一般的なもののみ）
        character_indicators = [
            original_name,  # 元の名前が含まれるもの
            'キャラクター', 'character', 'アニメ', 'anime', 'マンガ', 'manga', '漫画',
            'ゲーム', 'game', 'フィクション', 'fiction', '作品', '登場人物'
        ]
        
        # 除外すべき要素
        exclude_indicators = [
            '聖書', '宗教', 'religion', '事件', '犯罪', 'crime', '政治', 'politics',
            '企業', 'company', '会社', '組織', '団体', '学校', 'school', '大学'
        ]
        
        best_score = -1
        best_option = options[0]  # デフォルトは最初の候補
        
        for option in options[:10]:  # 上位10件のみチェック
            score = 0
            option_lower = option.lower()
            
            # キャラクター指標の加点
            for indicator in character_indicators:
                if indicator.lower() in option_lower:
                    score += 2
            
            # 除外指標の減点
            for exclude in exclude_indicators:
                if exclude.lower() in option_lower:
                    score -= 3
            
            # 元の名前との類似度
            if original_name.lower() in option_lower:
                score += 5
            
            if score > best_score:
                best_score = score
                best_option = option
        
        return best_option