#!/usr/bin/env python3
"""
ChatGPT Collector 専用テストスクリプト
"""

import sys
import os
from dotenv import load_dotenv
from collectors.chatgpt_collector import ChatGPTCollector
from utils.execution_logger import ExecutionLogger

# .envファイルから環境変数を読み込み
load_dotenv()


def test_chatgpt_collector_with_real_api(api_key: str):
    """実際のAPIキーを使ってChatGPT Collectorをテスト"""
    print("=== ChatGPT Collector 実際のAPIテスト ===")
    
    try:
        # ログを記録
        logger = ExecutionLogger()
        logger.set_character_name("テストキャラクター")
        
        # ChatGPT Collectorのインスタンスを作成
        collector = ChatGPTCollector()
        
        print(f"APIキー（末尾4文字）: ...{api_key[-4:]}")
        print("ChatGPT Collectorのテスト実行中...")
        
        # 実際に情報収集を実行
        result = collector.collect_info(
            name="初音ミク",
            logger=logger,
            api_key=api_key
        )
        
        print("✅ ChatGPT Collector テスト成功")
        print(f"結果の詳細:")
        print(f"  - 成功: {result.found}")
        print(f"  - エラー: {result.error}")
        print(f"  - 結果数: {result.total_results}")
        
        if result.results:
            print(f"  - 最初の結果のタイトル: {result.results[0].title}")
            print(f"  - 最初の結果の内容長: {len(result.results[0].content)} 文字")
            print(f"  - 最初の結果の一部: {result.results[0].content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ChatGPT Collector テスト失敗: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        
        # 詳細なエラー情報を表示
        import traceback
        traceback.print_exc()
        
        return False


def test_search_with_chatgpt_method(api_key: str):
    """_search_with_chatgptメソッドを直接テスト"""
    print("\n=== _search_with_chatgpt メソッド直接テスト ===")
    
    try:
        collector = ChatGPTCollector()
        
        result = collector._search_with_chatgpt(
            search_query="初音ミク 話し方 特徴",
            character_name="初音ミク",
            api_key=api_key,
            logger=None
        )
        
        if result:
            print("✅ _search_with_chatgpt メソッド成功")
            print(f"結果の詳細:")
            print(f"  - URL: {result.get('url', 'N/A')}")
            print(f"  - タイトル: {result.get('title', 'N/A')}")
            print(f"  - 内容長: {len(result.get('content', ''))} 文字")
            print(f"  - スピーチパターン数: {len(result.get('speech_patterns', []))}")
            print(f"  - 内容の一部: {result.get('content', '')[:300]}...")
        else:
            print("❌ _search_with_chatgpt メソッドがNoneを返しました")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ _search_with_chatgpt メソッド失敗: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        
        # 詳細なエラー情報を表示
        import traceback
        traceback.print_exc()
        
        return False


def test_openai_client_directly(api_key: str):
    """OpenAIクライアントを直接テスト（ChatGPT Collectorと同じ方法で）"""
    print("\n=== OpenAI クライアント直接テスト（ChatGPT Collector方式）===")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # ChatGPT Collectorと同じプロンプトを使用
        system_prompt = """あなたは日本のキャラクター、人物、作品に関する詳細な知識を持つ専門家です。
質問されたキャラクターについて、あなたの知識ベースから正確で詳細な情報を提供してください。
推測や曖昧な情報は避け、確実に知っている情報のみを回答してください。"""

        user_prompt = """「初音ミク」について、以下の観点から詳しく教えてください：

検索クエリ: 初音ミク 話し方 特徴

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

        print("OpenAI API呼び出し実行中...")
        
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
        
        print("✅ OpenAI クライアント直接テスト成功")
        print(f"応答長: {len(result_text)} 文字")
        print(f"応答の一部: {result_text[:400]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI クライアント直接テスト失敗: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        
        # APIキーエラーの詳細分析
        if "401" in str(e) or "Unauthorized" in str(e):
            print(f"🔍 APIキー認証エラーの詳細分析:")
            print(f"   - 提供されたAPIキー（末尾4文字）: ...{api_key[-4:]}")
            print(f"   - APIキー長: {len(api_key)} 文字")
            print(f"   - APIキー開始: {api_key[:10]}...")
            
            # エラーメッセージからAPIキー情報を抽出
            error_str = str(e)
            if "sk-" in error_str:
                import re
                api_key_pattern = r'sk-[A-Za-z0-9\-_]+'
                found_keys = re.findall(api_key_pattern, error_str)
                if found_keys:
                    error_key = found_keys[0]
                    print(f"   - エラーメッセージ内のAPIキー: {error_key[:10]}...{error_key[-4:]}")
                    print(f"   - エラーメッセージ内のAPIキー長: {len(error_key)} 文字")
                    
                    # キーの比較
                    if error_key == api_key:
                        print("   ✅ APIキーはエラーメッセージと一致しています")
                    else:
                        print("   ❌ APIキーがエラーメッセージと一致しません!")
                        print(f"       提供: {api_key}")
                        print(f"       エラー: {error_key}")
        
        # 詳細なエラー情報を表示
        import traceback
        traceback.print_exc()
        
        return False


def main():
    """メイン関数"""
    print("ChatGPT Collector 専用テスト開始")
    print("=" * 60)
    
    # APIキーを取得
    api_key = None
    
    # 環境変数から取得
    env_api_key = os.environ.get("OPENAI_API_KEY")
    if env_api_key:
        api_key = env_api_key
        print(f"✅ 環境変数からAPIキーを取得: ...{api_key[-4:]}")
    
    # コマンドライン引数から取得
    elif len(sys.argv) > 1:
        api_key = sys.argv[1]
        print(f"✅ コマンドライン引数からAPIキーを取得: ...{api_key[-4:]}")
    
    if not api_key:
        print("❌ APIキーが提供されていません")
        print("使用方法:")
        print("  python3 test_chatgpt_collector.py <your-api-key>")
        print("または:")
        print("  export OPENAI_API_KEY=\"your-api-key\"")
        print("  python3 test_chatgpt_collector.py")
        sys.exit(1)
    
    print(f"APIキー確認: 長さ={len(api_key)}文字, 開始={api_key[:10]}..., 末尾=...{api_key[-4:]}")
    print("")
    
    # テスト実行
    tests_passed = 0
    total_tests = 3
    
    # 1. OpenAI クライアント直接テスト
    if test_openai_client_directly(api_key):
        tests_passed += 1
    
    # 2. _search_with_chatgpt メソッド直接テスト
    if test_search_with_chatgpt_method(api_key):
        tests_passed += 1
    
    # 3. ChatGPT Collector フルテスト
    if test_chatgpt_collector_with_real_api(api_key):
        tests_passed += 1
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print(f"テスト結果: {tests_passed}/{total_tests} テスト成功")
    
    if tests_passed == total_tests:
        print("✅ 全てのテストが成功しました！")
        print("ChatGPT Collectorは正常に動作しています。")
    else:
        print("❌ 一部またはすべてのテストが失敗しました。")
        print("APIキーや設定を確認してください。")


if __name__ == "__main__":
    main()