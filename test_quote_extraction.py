#!/usr/bin/env python3
"""
キャラクターセリフ抽出機能のテストスクリプト
"""

import os
from dotenv import load_dotenv
from utils.api_client import OpenAIClient
from core.interfaces import CharacterQuote

# 環境変数を読み込み
load_dotenv()

def test_quote_extraction():
    """セリフ抽出機能をテスト"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ エラー: OPENAI_API_KEY が設定されていません")
        return
    
    client = OpenAIClient(api_key)
    
    # テスト用のテキスト（ドラえもんの例）
    test_text = """
    ドラえもんは、のび太に向かって「君はじつにばかだな」と言いました。
    「どこでもドア～！」と叫びながら、ポケットから道具を取り出します。
    のび太が困っていると、ドラえもんは「しょうがないなあ、のび太くんは」と言いながら助けてくれます。
    「未来の道具を使えば、なんでもできるんだよ」とドラえもんは説明しました。
    「僕はネコ型ロボットなんだ」と自己紹介することもあります。
    """
    
    print("=== キャラクターセリフ抽出テスト ===")
    print(f"テスト対象: ドラえもん")
    print(f"テキスト長: {len(test_text)}文字")
    print()
    
    # セリフを抽出
    quotes = client.extract_character_quotes(
        text=test_text,
        character_name="ドラえもん",
        source="test",
        source_url=None
    )
    
    print(f"抽出されたセリフ数: {len(quotes)}")
    print()
    
    for i, quote in enumerate(quotes, 1):
        print(f"{i}. 「{quote.text}」")
        print(f"   信頼性スコア: {quote.confidence_score}")
        print(f"   ソース: {quote.source}")
        print()

if __name__ == "__main__":
    test_quote_extraction()