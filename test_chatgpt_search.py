#!/usr/bin/env python3
"""
ChatGPT知識ベース検索のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from collectors.chatgpt_collector import ChatGPTCollector

def test_chatgpt_search():
    """ChatGPT知識ベース検索をテスト"""
    print("=== ChatGPT知識ベース検索テスト ===")
    
    # 環境変数から設定を取得
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    
    print(f"OpenAI API Key: {'設定済み' if openai_api_key else '未設定'}")
    
    if not openai_api_key:
        print("\n⚠️  OpenAI API Keyが設定されていません。")
        print("以下の環境変数を設定してからテストを実行してください:")
        print("export OPENAI_API_KEY=\"your-api-key\"")
        return
    
    # テスト実行
    collector = ChatGPTCollector(delay=1.0)
    
    test_name = "ずんだもん"
    print(f"\nテスト対象: {test_name}")
    print()
    
    try:
        result = collector.collect_info(test_name, logger=None, api_key=openai_api_key)
        
        print("\n=== 結果サマリー ===")
        print(f"検索成功: {result['found']}")
        print(f"エラー: {result['error']}")
        print(f"結果数: {result['total_results']}")
        print(f"クエリ: {result['query']}")
        
        if result['results']:
            print("\n=== 検索結果詳細 ===")
            for i, item in enumerate(result['results'], 1):
                print(f"\n{i}. {item['title']}")
                print(f"   URL: {item['url']}")
                print(f"   ドメイン: {item['domain']}")
                print(f"   検索クエリ: {item['search_query']}")
                print(f"   コンテンツ長: {item['content_length']}文字")
                print(f"   話し方パターン: {len(item['speech_patterns'])}件")
                print(f"   内容: {item['content'][:200]}...")
                
                if item['speech_patterns']:
                    print("   抽出された話し方パターン:")
                    for pattern in item['speech_patterns'][:3]:
                        print(f"     - {pattern}")
        else:
            print("\n検索結果なし")
            
    except Exception as e:
        print(f"テストエラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chatgpt_search()