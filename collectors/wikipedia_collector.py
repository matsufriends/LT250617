"""
Wikipedia情報収集モジュール
"""

import wikipedia
from typing import Optional, Dict, Any


class WikipediaCollector:
    """Wikipedia情報を収集するクラス"""
    
    def __init__(self, language: str = 'ja'):
        """
        初期化
        
        Args:
            language: Wikipedia言語設定 (デフォルト: 'ja')
        """
        self.language = language
        wikipedia.set_lang(language)
    
    def collect_info(self, name: str, logger=None) -> Dict[str, Any]:
        """
        指定された名前の人物情報をWikipediaから収集
        
        Args:
            name: 検索対象の人物名
            
        Returns:
            収集した情報の辞書
        """
        try:
            # まず検索してページを特定
            search_results = wikipedia.search(name, results=5)
            
            if not search_results:
                return {
                    "found": False,
                    "error": f"'{name}'に関するWikipediaページが見つかりませんでした",
                    "title": None,
                    "summary": None,
                    "content": None,
                    "url": None,
                    "categories": []
                }
            
            # 最初の検索結果を取得
            page_title = search_results[0]
            page = wikipedia.page(page_title)
            
            return {
                "found": True,
                "error": None,
                "title": page.title,
                "summary": page.summary[:500],  # 最初の500文字
                "content": page.content[:2000],  # 最初の2000文字
                "url": page.url,
                "categories": page.categories[:10] if hasattr(page, 'categories') else []
            }
            
        except wikipedia.exceptions.DisambiguationError as e:
            # 曖昧さ回避ページの場合
            try:
                # 最初の候補を試す
                page = wikipedia.page(e.options[0])
                return {
                    "found": True,
                    "error": f"曖昧さ回避: {e.options[0]} を選択しました",
                    "title": page.title,
                    "summary": page.summary[:500],
                    "content": page.content[:2000],
                    "url": page.url,
                    "categories": page.categories[:10] if hasattr(page, 'categories') else [],
                    "other_options": e.options[1:5]  # 他の候補も記録
                }
            except Exception as inner_e:
                return {
                    "found": False,
                    "error": f"曖昧さ回避エラー: {str(inner_e)}",
                    "title": None,
                    "summary": None,
                    "content": None,
                    "url": None,
                    "categories": [],
                    "disambiguation_options": e.options[:5]
                }
                
        except wikipedia.exceptions.PageError:
            return {
                "found": False,
                "error": f"'{name}'のWikipediaページが存在しません",
                "title": None,
                "summary": None,
                "content": None,
                "url": None,
                "categories": []
            }
            
        except Exception as e:
            return {
                "found": False,
                "error": f"Wikipedia取得エラー: {str(e)}",
                "title": None,
                "summary": None,
                "content": None,
                "url": None,
                "categories": []
            }
    
    def search_suggestions(self, name: str, limit: int = 10) -> list:
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