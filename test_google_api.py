#!/usr/bin/env python3
"""
Google Custom Search APIのテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.google_collector import GoogleCollector

def test_google_custom_search():
    """Google Custom Search APIをテスト"""
    print("=== Google Custom Search APIテスト ===")
    
    # 環境変数から設定を取得
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_cx = os.environ.get("GOOGLE_CX")
    
    print(f"Google API Key: {'設定済み' if google_api_key else '未設定'}")
    print(f"Google CX: {'設定済み' if google_cx else '未設定'}")
    
    if not google_api_key or not google_cx:
        print("\n⚠️  Google Custom Search APIが設定されていません。")
        print("以下の環境変数を設定してからテストを実行してください:")
        print("export GOOGLE_API_KEY=\"your-api-key\"")
        print("export GOOGLE_CX=\"your-search-engine-id\"")
        return
    
    # テスト実行
    collector = GoogleCollector(
        delay=1.0,
        google_api_key=google_api_key,
        google_cx=google_cx
    )
    
    test_name = "ずんだもん"
    print(f"\nテスト対象: {test_name}")
    print()
    
    try:
        result = collector.collect_info(test_name, logger=None, api_key="test-key")
        
        print("\n=== 結果サマリー ===")
        print(f"検索成功: {result['found']}")
        print(f"エラー: {result['error']}")
        print(f"結果数: {result['total_results']}")
        print(f"クエリ: {result['query']}")
        
        if result['results']:
            print("\n=== 検索結果詳細 ===")
            for i, item in enumerate(result['results'][:3], 1):
                print(f"\n{i}. {item['title']}")
                print(f"   URL: {item['url']}")
                print(f"   ドメイン: {item['domain']}")
                print(f"   説明: {item['description'][:100]}...")
                if 'api_snippet' in item:
                    print(f"   API Snippet: {item['api_snippet'][:100]}...")
        else:
            print("\n検索結果なし")
            
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_google_custom_search()