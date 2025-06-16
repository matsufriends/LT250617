#!/usr/bin/env python3
"""
OpenAI API接続テストスクリプト
"""

import os
import sys
import traceback
from typing import Optional
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()


def test_api_key_detection():
    """APIキーの検出をテスト"""
    print("=== APIキー検出テスト ===")
    
    # 環境変数からAPIキーを取得
    env_api_key = os.environ.get("OPENAI_API_KEY")
    
    if env_api_key:
        print(f"✅ 環境変数 OPENAI_API_KEY が設定されています")
        print(f"   キー（末尾4文字）: ...{env_api_key[-4:]}")
    else:
        print("❌ 環境変数 OPENAI_API_KEY が設定されていません")
        return None
    
    return env_api_key


def test_openai_import():
    """OpenAIライブラリのインポートをテスト"""
    print("\n=== OpenAIライブラリ インポートテスト ===")
    
    try:
        import openai
        print(f"✅ openai ライブラリのインポート成功")
        print(f"   バージョン: {openai.__version__}")
        return True
    except ImportError as e:
        print(f"❌ openai ライブラリのインポート失敗: {e}")
        print("   解決方法: pip install openai")
        return False
    except Exception as e:
        print(f"❌ openai ライブラリのインポートでエラー: {e}")
        return False


def test_openai_client_creation(api_key: str):
    """OpenAI クライアントの作成をテスト"""
    print("\n=== OpenAI クライアント作成テスト ===")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI クライアントの作成成功")
        return client
    except Exception as e:
        print(f"❌ OpenAI クライアントの作成失敗: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        return None


def test_simple_api_call(client, api_key: str):
    """シンプルなAPI呼び出しをテスト"""
    print("\n=== 簡単なAPI呼び出しテスト ===")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": "Hello! Please respond with 'API test successful'"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API呼び出し成功")
        print(f"   応答: {result}")
        print(f"   モデル: gpt-4o")
        return True
        
    except Exception as e:
        print(f"❌ API呼び出し失敗: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        
        # 詳細なエラー情報を表示
        if hasattr(e, 'response'):
            print(f"   HTTPステータス: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        
        # APIキーの詳細情報を表示
        print(f"   使用したAPIキー（末尾4文字）: ...{api_key[-4:]}")
        
        return False


def test_chatgpt_collector_simulation(api_key: str, character_name: str = "テストキャラクター"):
    """ChatGPT Collectorのシミュレーションテスト"""
    print(f"\n=== ChatGPT Collector シミュレーションテスト（{character_name}）===")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # ChatGPT Collectorと同じプロンプトを使用
        system_prompt = """あなたは日本のキャラクター、人物、作品に関する詳細な知識を持つ専門家です。
質問されたキャラクターについて、あなたの知識ベースから正確で詳細な情報を提供してください。
推測や曖昧な情報は避け、確実に知っている情報のみを回答してください。"""

        user_prompt = f""""{character_name}"について、以下の観点から詳しく教えてください：

検索クエリ: {character_name} 話し方 特徴

以下の項目について、知っている情報があれば詳しく説明してください：

1. 基本情報
   - 作品名・出典
   - キャラクターの設定・背景
   - 性格や特徴

2. 話し方・言語的特徴
   - 一人称（「僕」「俺」「私」「ウチ」「ワタクシ」など）
   - 語尾の特徴（「だよ」「なのだ」「ですの」「だっぺ」など）
   - 口癖や決まり文句
   - 敬語の使用パターン
   - 特徴的な表現や話し方

知らない情報については「不明」と明記し、推測は行わないでください。
確実に知っている情報のみを、具体例を交えて詳しく説明してください。"""

        print(f"   システムプロンプト長: {len(system_prompt)} 文字")
        print(f"   ユーザープロンプト長: {len(user_prompt)} 文字")
        print("   API呼び出し実行中...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        result_text = response.choices[0].message.content.strip()
        print(f"✅ ChatGPT Collector シミュレーション成功")
        print(f"   応答長: {len(result_text)} 文字")
        print(f"   使用モデル: gpt-4o")
        print(f"   応答の一部: {result_text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ChatGPT Collector シミュレーション失敗: {e}")
        print(f"   エラータイプ: {type(e).__name__}")
        
        # 詳細なトレースバックを表示
        traceback.print_exc()
        
        return False


def test_api_key_format(api_key: str):
    """APIキーの形式をチェック"""
    print("\n=== APIキー形式チェック ===")
    
    print(f"APIキー長: {len(api_key)} 文字")
    print(f"APIキー開始: {api_key[:7]}...")
    print(f"APIキー末尾: ...{api_key[-4:]}")
    
    # OpenAI APIキーの一般的な形式をチェック
    if api_key.startswith("sk-"):
        print("✅ APIキーは 'sk-' で始まっています")
    else:
        print("❌ APIキーが 'sk-' で始まっていません")
    
    # 長さをチェック（OpenAI APIキーは通常51文字）
    if 45 <= len(api_key) <= 60:
        print("✅ APIキーの長さは妥当です")
    else:
        print(f"⚠️ APIキーの長さが標準的でない可能性があります（通常: 51文字）")


def main():
    """メイン関数"""
    print("OpenAI API 接続テスト開始")
    print("=" * 50)
    
    # 1. APIキー検出テスト
    api_key = test_api_key_detection()
    if not api_key:
        print("\n❌ 環境変数にAPIキーが設定されていません")
        print("コマンドライン引数でAPIキーを指定して再度実行してください：")
        print("python3 test_openai_api.py <your-api-key>")
        print("\nまたは、環境変数を設定してください：")
        print("export OPENAI_API_KEY=\"your-api-key\"")
        
        # コマンドライン引数からAPIキーを取得
        if len(sys.argv) > 1:
            api_key = sys.argv[1]
            print(f"\n✅ コマンドライン引数からAPIキーを取得しました")
            print(f"   キー（末尾4文字）: ...{api_key[-4:]}")
        else:
            sys.exit(1)
    
    # 2. APIキー形式チェック
    test_api_key_format(api_key)
    
    # 3. OpenAIライブラリインポートテスト
    if not test_openai_import():
        print("\n❌ OpenAIライブラリが利用できないため、テストを中止します")
        sys.exit(1)
    
    # 4. クライアント作成テスト
    client = test_openai_client_creation(api_key)
    if not client:
        print("\n❌ OpenAIクライアントが作成できないため、テストを中止します")
        sys.exit(1)
    
    # 5. 簡単なAPI呼び出しテスト
    if not test_simple_api_call(client, api_key):
        print("\n❌ 基本的なAPI呼び出しが失敗しました")
        return
    
    # 6. ChatGPT Collectorシミュレーションテスト
    if not test_chatgpt_collector_simulation(api_key, "初音ミク"):
        print("\n❌ ChatGPT Collectorシミュレーションが失敗しました")
        return
    
    print("\n" + "=" * 50)
    print("✅ 全てのテストが成功しました！")
    print("OpenAI API接続は正常に動作しています。")


if __name__ == "__main__":
    main()