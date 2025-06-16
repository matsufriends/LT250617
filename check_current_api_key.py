#!/usr/bin/env python3
"""
現在使用されているAPIキーを確認するスクリプト
"""

import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込み
load_dotenv()

def main():
    print("=== 現在のAPIキー確認 ===")
    
    # 環境変数からAPIキーを取得
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if api_key:
        print(f"✅ OPENAI_API_KEY が設定されています")
        print(f"   開始: {api_key[:10]}...")
        print(f"   末尾: ...{api_key[-4:]}")
        print(f"   長さ: {len(api_key)} 文字")
        
        # .envファイルの内容と比較
        try:
            with open('.env', 'r') as f:
                env_content = f.read()
                if 'iFoA' in env_content:
                    print("✅ .envファイルに'iFoA'で終わるAPIキーが含まれています")
                    if api_key.endswith('iFoA'):
                        print("✅ 環境変数のAPIキーは.envファイルと一致しています")
                    else:
                        print("❌ 環境変数のAPIキーは.envファイルと異なります")
                else:
                    print("⚠️ .envファイルに'iFoA'で終わるAPIキーが見つかりません")
        except Exception as e:
            print(f"⚠️ .envファイルの読み取りエラー: {e}")
    else:
        print("❌ OPENAI_API_KEY が設定されていません")

if __name__ == "__main__":
    main()