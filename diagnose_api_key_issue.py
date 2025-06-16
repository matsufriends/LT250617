#!/usr/bin/env python3
"""
OpenAI APIキー問題の詳細診断スクリプト
"""

import os
import sys
import subprocess
from pathlib import Path


def check_environment_variables():
    """環境変数の状況を詳しく調査"""
    print("=== 環境変数調査 ===")
    
    # OpenAI関連の環境変数をチェック
    openai_vars = {
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
        'OPENAI_ORG': os.environ.get('OPENAI_ORG'),
        'OPENAI_API_BASE': os.environ.get('OPENAI_API_BASE'),
    }
    
    for var_name, var_value in openai_vars.items():
        if var_value:
            print(f"✅ {var_name}: 設定済み (末尾4文字: ...{var_value[-4:]})")
        else:
            print(f"❌ {var_name}: 未設定")
    
    # シェル設定ファイルを確認
    print("\n=== シェル設定ファイル調査 ===")
    shell_files = [
        Path.home() / '.bashrc',
        Path.home() / '.zshrc',
        Path.home() / '.profile',
        Path.home() / '.bash_profile'
    ]
    
    for shell_file in shell_files:
        if shell_file.exists():
            try:
                with open(shell_file, 'r') as f:
                    content = f.read()
                    if 'OPENAI_API_KEY' in content:
                        print(f"✅ {shell_file}: OPENAI_API_KEY の設定が見つかりました")
                        # 該当行を抽出
                        lines = content.split('\n')
                        for line in lines:
                            if 'OPENAI_API_KEY' in line and not line.strip().startswith('#'):
                                # APIキーの値を隠して表示
                                if '=' in line:
                                    key_part = line.split('=')[0]
                                    value_part = line.split('=', 1)[1]
                                    if len(value_part) > 8:
                                        hidden_value = value_part[:4] + '*' * (len(value_part) - 8) + value_part[-4:]
                                    else:
                                        hidden_value = '*' * len(value_part)
                                    print(f"    {key_part}={hidden_value}")
                    else:
                        print(f"⚪ {shell_file}: OPENAI_API_KEY の設定なし")
            except Exception as e:
                print(f"❌ {shell_file}: 読み取りエラー - {e}")
        else:
            print(f"⚪ {shell_file}: ファイルが存在しません")


def check_project_files():
    """プロジェクト内のファイルでAPIキーがハードコーディングされていないかチェック"""
    print("\n=== プロジェクトファイル調査 ===")
    
    # チェック対象のファイルパターン
    patterns = ['*.py', '*.env', '*.conf', '*.json', '*.txt']
    
    api_key_found = False
    
    for pattern in patterns:
        for file_path in Path('.').rglob(pattern):
            # 除外するディレクトリ
            if any(exclude in str(file_path) for exclude in ['.git', '__pycache__', 'venv', 'node_modules']):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'sk-' in content and ('proj' in content or 'OPENAI' in content):
                        print(f"⚠️ {file_path}: API キーらしき文字列が見つかりました")
                        # 該当行を抽出（セキュリティのため一部隠す）
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if 'sk-' in line:
                                # APIキーを隠して表示
                                masked_line = line
                                import re
                                api_keys = re.findall(r'sk-[A-Za-z0-9\-_]+', line)
                                for key in api_keys:
                                    if len(key) > 8:
                                        masked_key = key[:7] + '*' * (len(key) - 11) + key[-4:]
                                    else:
                                        masked_key = '*' * len(key)
                                    masked_line = masked_line.replace(key, masked_key)
                                print(f"    行{i}: {masked_line.strip()}")
                        api_key_found = True
            except Exception as e:
                # バイナリファイルなどは無視
                pass
    
    if not api_key_found:
        print("✅ プロジェクトファイル内にAPIキーのハードコーディングは見つかりませんでした")


def check_cache_files():
    """キャッシュファイルを調査"""
    print("\n=== キャッシュファイル調査 ===")
    
    cache_dir = Path('cache')
    if not cache_dir.exists():
        print("⚪ キャッシュディレクトリが存在しません")
        return
    
    # 最新のログファイルを確認
    latest_log = cache_dir / 'latest_execution_log.json'
    if latest_log.exists():
        try:
            import json
            with open(latest_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
            
            # APIキー関連のエラーを探す
            api_errors = []
            for error in log_data.get('errors', []):
                if 'api_key' in error.get('error_message', '').lower():
                    api_errors.append(error)
            
            for api_call in log_data.get('api_calls', []):
                if api_call.get('error') and 'api_key' in api_call.get('error', '').lower():
                    api_errors.append(api_call)
            
            if api_errors:
                print(f"⚠️ APIキー関連エラーが {len(api_errors)} 件見つかりました")
                for i, error in enumerate(api_errors[:3], 1):  # 最大3件表示
                    error_msg = error.get('error_message') or error.get('error', '')
                    # APIキーを隠す
                    import re
                    masked_msg = re.sub(r'sk-[A-Za-z0-9\-_]+', 
                                      lambda m: m.group()[:7] + '*' * (len(m.group()) - 11) + m.group()[-4:],
                                      error_msg)
                    print(f"  エラー{i}: {masked_msg[:200]}...")
            else:
                print("✅ 最新ログにAPIキー関連エラーは見つかりませんでした")
                
        except Exception as e:
            print(f"❌ ログファイルの読み取りエラー: {e}")
    else:
        print("⚪ 最新ログファイルが存在しません")


def check_system_environment():
    """システム環境の調査"""
    print("\n=== システム環境調査 ===")
    
    # Pythonバージョン
    print(f"Python版: {sys.version}")
    
    # 作業ディレクトリ
    print(f"作業ディレクトリ: {os.getcwd()}")
    
    # シェル環境
    shell = os.environ.get('SHELL', 'unknown')
    print(f"シェル: {shell}")
    
    # OpenAIパッケージの確認
    try:
        import openai
        print(f"✅ OpenAIパッケージ: v{openai.__version__}")
    except ImportError:
        print("❌ OpenAIパッケージがインストールされていません")
    except Exception as e:
        print(f"⚠️ OpenAIパッケージエラー: {e}")


def suggest_solutions():
    """解決方法の提案"""
    print("\n" + "=" * 60)
    print("🔧 解決方法の提案")
    print("=" * 60)
    
    solutions = [
        "1. **環境変数の再設定**",
        "   export OPENAI_API_KEY=\"your-actual-api-key-ending-with-iFoA\"",
        "   source ~/.bashrc  # または ~/.zshrc",
        "",
        "2. **新しいターミナルセッションで実行**",
        "   現在のセッションを閉じて、新しいターミナルを開く",
        "",
        "3. **APIキーの直接指定**",
        "   python main.py \"キャラクター名\" --api-key \"your-api-key\"",
        "",
        "4. **APIキーの形式確認**",
        "   - OpenAI Platformで最新のAPIキーを確認",
        "   - 新形式: sk-proj-... で始まる",
        "   - 旧形式: sk-... で始まる",
        "",
        "5. **キャッシュのクリア**",
        "   rm -rf cache/",
        "   # 古いキャッシュデータを削除",
        "",
        "6. **設定ファイルの確認**",
        "   grep -r \"OPENAI_API_KEY\" ~/.bashrc ~/.zshrc ~/.profile",
        "",
        "7. **OpenAI APIキーの再生成**",
        "   https://platform.openai.com/account/api-keys",
        "   古いキーを削除して新しいキーを生成"
    ]
    
    for solution in solutions:
        print(solution)


def main():
    """メイン診断関数"""
    print("OpenAI APIキー問題 詳細診断")
    print("=" * 60)
    
    # 各種調査を実行
    check_environment_variables()
    check_project_files()
    check_cache_files()
    check_system_environment()
    
    # 解決方法を提案
    suggest_solutions()
    
    print("\n" + "=" * 60)
    print("🏁 診断完了")
    print("上記の情報を参考に、APIキーの設定を確認してください。")


if __name__ == "__main__":
    main()