#!/usr/bin/env python3
"""
Google Custom Search APIの動作確認スクリプト
"""

import os
import requests
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def test_google_custom_search():
    """Google Custom Search APIをテスト"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")
    
    print("=== Google Custom Search API テスト ===")
    print(f"API Key: {api_key[:10]}... (length: {len(api_key) if api_key else 0})")
    print(f"CX: {cx[:10] if cx else 'None'}... (length: {len(cx) if cx else 0})")
    
    if not api_key:
        print("\n❌ エラー: GOOGLE_API_KEY が設定されていません")
        return
    
    if not cx:
        print("\n❌ エラー: GOOGLE_CX が設定されていません")
        print("→ https://programmablesearchengine.google.com/ で検索エンジンを作成してください")
        return
    
    # テスト検索を実行
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cx,
        'q': 'ワンピース ルフィ',
        'num': 1,
        'lr': 'lang_ja'
    }
    
    print(f"\nテスト検索: '{params['q']}'")
    print(f"リクエストURL: {url}")
    
    try:
        response = requests.get(url, params=params)
        print(f"\nHTTPステータス: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功！")
            
            if 'items' in data and data['items']:
                print(f"\n検索結果数: {len(data['items'])}")
                print(f"最初の結果:")
                print(f"  タイトル: {data['items'][0].get('title', 'N/A')}")
                print(f"  URL: {data['items'][0].get('link', 'N/A')}")
            else:
                print("\n⚠️ 検索結果が0件でした")
                
        elif response.status_code == 404:
            print("\n❌ 404エラー: 検索エンジンIDが無効です")
            print("対処法:")
            print("1. https://programmablesearchengine.google.com/ にアクセス")
            print("2. 検索エンジンが存在するか確認")
            print("3. 検索エンジンIDをコピーして GOOGLE_CX に設定")
            
        elif response.status_code == 403:
            print("\n❌ 403エラー: APIキーが無効またはAPIが有効化されていません")
            print("対処法:")
            print("1. Google Cloud Consoleで Custom Search API を有効化")
            print("2. APIキーが正しいか確認")
            
        elif response.status_code == 429:
            print("\n❌ 429エラー: 日次クォータを超過しました")
            print("対処法: 課金設定を確認するか、翌日まで待つ")
            
        else:
            print(f"\n❌ エラー: {response.text}")
            
    except Exception as e:
        print(f"\n❌ リクエストエラー: {e}")

if __name__ == "__main__":
    test_google_custom_search()