#!/usr/bin/env python3
"""
DuckDuckGo検索のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.duckduckgo_collector import DuckDuckGoCollector

def test_duckduckgo_search():
    """DuckDuckGo検索をテスト"""
    print("=== DuckDuckGo検索テスト ===")
    
    collector = DuckDuckGoCollector(delay=1.0)
    
    # テスト用キャラクター名
    test_name = "ずんだもん"
    
    print(f"テスト対象: {test_name}")
    print()
    
    try:
        result = collector.collect_info(test_name, logger=None, api_key="test-key")
        
        print("\n=== 結果サマリー ===")
        print(f"検索成功: {result['found']}")
        print(f"エラー: {result['error']}")
        print(f"結果数: {result['total_results']}")
        
        if result['results']:
            print("\n=== 検索結果詳細 ===")
            for i, item in enumerate(result['results'][:3], 1):
                print(f"\n{i}. {item['title']}")
                print(f"   URL: {item['url']}")
                print(f"   ドメイン: {item['domain']}")
                print(f"   説明: {item['description'][:100]}...")
                print(f"   話し方パターン: {len(item['speech_patterns'])}件")
        else:
            print("\n検索結果なし")
            
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_duckduckgo_search()