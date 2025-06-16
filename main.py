#!/usr/bin/env python3
"""
キャラクター口調設定プロンプト自動生成プログラム
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Union, Optional
from dotenv import load_dotenv
from utils.execution_logger import ExecutionLogger
from config import (DISPLAY_SEPARATOR_LENGTH, DISPLAY_EMOJI_REPEAT_COUNT, 
                    ERROR_WAIT_TIME_HOURS_MIN, ERROR_WAIT_TIME_HOURS_MAX,
                    DISPLAY_SEPARATOR_CHAR, DISPLAY_EMOJI_SHIELD, DISPLAY_EMOJI_MASK)

# .envファイルから環境変数を読み込み
load_dotenv()

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="キャラクター口調設定プロンプト自動生成プログラム"
    )
    parser.add_argument(
        "name", 
        help="対象となる人物・キャラクターの名前"
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API Key (環境変数 OPENAI_API_KEY からも読み取り可能)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="結果を指定したファイルに保存"
    )
    parser.add_argument(
        "--no-youtube",
        action="store_true",
        help="YouTube字幕からの情報収集を無効にする"
    )
    parser.add_argument(
        "--no-google",
        action="store_true",
        help="Google検索からの情報収集を無効にする（レート制限回避）"
    )
    parser.add_argument(
        "--use-duckduckgo",
        action="store_true",
        help="Google検索の代わりにDuckDuckGo検索を使用"
    )
    parser.add_argument(
        "--use-bing",
        action="store_true",
        help="Google検索の代わりにBing検索を使用"
    )
    parser.add_argument(
        "--use-chatgpt-search",
        action="store_true",
        help="Web検索の代わりにChatGPTの知識ベースから情報を取得"
    )
    
    args = parser.parse_args()
    
    # 検索エンジンフラグの競合チェック
    search_flags = [args.use_duckduckgo, args.use_bing, args.use_chatgpt_search]
    if sum(search_flags) > 1:
        print("エラー: 検索エンジンオプション（--use-duckduckgo, --use-bing, --use-chatgpt-search）は同時に指定できません。")
        sys.exit(1)
    
    # 実行ログ開始
    logger = ExecutionLogger()
    logger.set_character_name(args.name)
    logger.log_step("main_start", "start", {"character_name": args.name})
    
    # API キーの設定確認
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        error_msg = "OpenAI API Keyが設定されていません"
        logger.log_error("configuration_error", error_msg, {"missing": "api_key"})
        print("エラー: OpenAI API Keyが設定されていません。")
        print("--api-key オプションまたは環境変数 OPENAI_API_KEY を設定してください。")
        sys.exit(1)
    
    logger.log_step("api_key_verification", "success", {"api_key_source": "args" if args.api_key else "env"})
    
    print(f"=== キャラクター口調プロンプト生成: {args.name} ===")
    
    # 検索エンジン選択の表示
    if args.use_chatgpt_search:
        print("🤖 検索エンジン: ChatGPT知識ベース（完全AI検索）")
        print("    ✨ Web検索不要でレート制限なし、2023年4月までの知識を使用")
    elif args.use_bing:
        print("🔍 検索エンジン: Bing（Google制限回避）")
    elif args.use_duckduckgo:
        print("🦆 検索エンジン: DuckDuckGo（実験的）")
        print("    💡 202エラーが出る場合は --use-bing への切り替えを推奨")
    elif not args.no_google:
        print("🔍 検索エンジン: Google")
        # Google Custom Search API の設定状況を表示
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        google_cx = os.environ.get("GOOGLE_CX")
        if google_api_key and google_cx:
            print("    ✅ Google Custom Search API: 設定済み（安定動作）")
        else:
            print("    ⚠️  Google Custom Search API: 未設定（429エラーの可能性）")
            print("    💡 安定動作のため以下環境変数の設定を推奨:")
            print("       export GOOGLE_API_KEY=\"your-api-key\"")
            print("       export GOOGLE_CX=\"your-search-engine-id\"")
    else:
        print("🚫 Web検索: 無効")
    
    if args.no_youtube:
        print("🎥 YouTube字幕: 無効")
    else:
        print("🎥 YouTube字幕: 有効")
        if args.use_chatgpt_search:
            print("    📹 ChatGPT検索でもYouTube字幕収集は利用可能です")
    
    print()
    
    try:
        # 情報収集
        print("📚 情報収集中...")
        start_time = time.time()
        
        from core.character_info_service import CharacterInfoService
        info_service = CharacterInfoService(api_key=api_key)
        character_info = info_service.collect_character_info(
            args.name, 
            logger=logger, 
            use_youtube=not args.no_youtube, 
            use_google=not args.no_google, 
            use_duckduckgo=args.use_duckduckgo, 
            use_bing=args.use_bing, 
            use_chatgpt_search=args.use_chatgpt_search
        )
        
        collection_duration = time.time() - start_time
        logger.log_step("character_info_collection", "success", character_info, collection_duration)
        logger.log_performance_metric("info_collection_duration", collection_duration, "seconds")
        
        # プロンプト生成
        print("🤖 プロンプト生成中...")
        start_time = time.time()
        prompt_result = generate_voice_prompt(character_info, api_key, logger=logger)
        generation_duration = time.time() - start_time
        logger.log_step("prompt_generation", "success", {"prompt_length": len(str(prompt_result))}, generation_duration)
        logger.log_performance_metric("prompt_generation_duration", generation_duration, "seconds")
        
        # 結果を統一形式で処理
        if isinstance(prompt_result, dict):
            final_prompt = prompt_result["generated_prompt"]
            policy_safe_prompt = prompt_result.get("policy_safe_prompt", {})
            character_introduction = prompt_result.get("character_introduction", {})
            character_info["prompt_generation_api"] = prompt_result["api_interaction"]
        else:
            # 後方互換性のため
            final_prompt = prompt_result
            policy_safe_prompt = {}
            character_introduction = {}
        
        # 最終結果をログに記録
        final_result = {
            "character_name": args.name,
            "generated_prompt": final_prompt,
            "policy_safe_prompt": policy_safe_prompt,
            "prompt_length": len(final_prompt),
            "character_introduction": character_introduction,
            "character_info": character_info
        }
        logger.set_final_result(final_result)
        
        # 結果出力
        print("\n" + DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH)
        print("生成されたプロンプト:")
        print(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH)
        print(final_prompt)
        print(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH)
        
        # コンテンツポリシー対応版プロンプトの表示
        if policy_safe_prompt and policy_safe_prompt.get("safe_prompt"):
            print("\n" + f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT)
            print("コンテンツポリシー対応版プロンプト:")
            print(f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT)
            print(policy_safe_prompt["safe_prompt"])
            print(f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT)
        
        # キャラクター自己紹介の表示
        if character_introduction and character_introduction.get("introduction_text"):
            print("\n" + f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT)
            print(f"{args.name}による自己紹介:")
            print(f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT)
            print(character_introduction["introduction_text"])
            print(f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT)
        
        # 自動的に最終プロンプトを.txtファイルに出力（日時付き）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = args.name.replace(' ', '_').replace('/', '_')
        prompt_filename = f"prompt_{timestamp}_{safe_name}.txt"
        
        # 実行したコマンドを構築
        command_parts = ["python main.py", f'"{args.name}"']
        if args.api_key:
            command_parts.append('--api-key "YOUR_API_KEY"')
        if args.output:
            command_parts.append(f'--output "{args.output}"')
        if args.no_youtube:
            command_parts.append("--no-youtube")
        if args.no_google:
            command_parts.append("--no-google")
        if args.use_duckduckgo:
            command_parts.append("--use-duckduckgo")
        if args.use_bing:
            command_parts.append("--use-bing")
        if args.use_chatgpt_search:
            command_parts.append("--use-chatgpt-search")
        executed_command = " ".join(command_parts)
        
        with open(prompt_filename, 'w', encoding='utf-8') as f:
            f.write(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH + "\n")
            f.write(f"キャラクター口調プロンプト: {args.name}\n")
            f.write(f"生成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
            f.write(f"実行コマンド: {executed_command}\n")
            f.write(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH + "\n\n")
            f.write(final_prompt)
            f.write("\n\n")
            
            # コンテンツポリシー対応版プロンプトも含める
            if policy_safe_prompt and policy_safe_prompt.get("safe_prompt"):
                f.write(f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
                f.write("コンテンツポリシー対応版プロンプト:\n")
                f.write(f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n\n")
                f.write(policy_safe_prompt["safe_prompt"])
                f.write("\n\n")
            
            # 自己紹介も含める
            if character_introduction and character_introduction.get("introduction_text"):
                f.write(f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
                f.write(f"{args.name}による自己紹介:\n")
                f.write(f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n\n")
                f.write(character_introduction["introduction_text"])
                f.write("\n\n")
            
            # 実行情報のサマリーを追加
            f.write(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH + "\n")
            f.write("実行情報サマリー:\n")
            f.write(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH + "\n")
            f.write(f"検索エンジン: ")
            if args.use_chatgpt_search:
                f.write("ChatGPT知識ベース\n")
            elif args.use_bing:
                f.write("Bing\n")
            elif args.use_duckduckgo:
                f.write("DuckDuckGo\n")
            elif not args.no_google:
                f.write("Google\n")
            else:
                f.write("なし（Web検索無効）\n")
            
            f.write(f"YouTube字幕収集: {'無効' if args.no_youtube else '有効'}\n")
            f.write(f"出力ファイル: {prompt_filename}\n")
            if args.output:
                f.write(f"追加出力: {args.output}\n")
            f.write(f"セッションID: {logger.session_id}\n")
        
        print(f"\n✅ プロンプトを {prompt_filename} に保存しました。")
        
        # 追加のファイル出力（ユーザー指定）
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH + "\n")
                f.write("生成されたプロンプト:\n")
                f.write(DISPLAY_SEPARATOR_CHAR*DISPLAY_SEPARATOR_LENGTH + "\n")
                f.write(final_prompt)
                f.write("\n" + "="*DISPLAY_SEPARATOR_LENGTH + "\n\n")
                
                # コンテンツポリシー対応版も含める
                if policy_safe_prompt and policy_safe_prompt.get("safe_prompt"):
                    f.write(f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
                    f.write("コンテンツポリシー対応版プロンプト:\n")
                    f.write(f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
                    f.write(policy_safe_prompt["safe_prompt"])
                    f.write("\n" + f"{DISPLAY_EMOJI_SHIELD} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n\n")
                
                # 自己紹介も含める
                if character_introduction and character_introduction.get("introduction_text"):
                    f.write(f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
                    f.write(f"{args.name}による自己紹介:\n")
                    f.write(f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
                    f.write(character_introduction["introduction_text"])
                    f.write("\n" + f"{DISPLAY_EMOJI_MASK} "*DISPLAY_EMOJI_REPEAT_COUNT + "\n")
            print(f"\n✅ 通常版・ポリシー対応版プロンプトと自己紹介を {args.output} に保存しました。")
            logger.log_step("file_output", "success", {"output_file": args.output})
        
        # 実行サマリーを表示
        summary = logger.get_summary()
        print(f"\n📊 実行ログ: セッションID {summary['session_id']}")
        print(f"   - 実行ステップ: {summary['successful_steps']}/{summary['total_steps']}")
        print(f"   - API呼び出し: {summary['successful_api_calls']}/{summary['total_api_calls']}")
        if summary['total_errors'] > 0:
            print(f"   - エラー数: {summary['total_errors']}")
        print(f"   - ログファイル: cache/execution_log_{summary['session_id']}.json")
        
        logger.log_step("main_complete", "success", summary)
        
    except Exception as e:
        error_msg = str(e)
        logger.log_error("execution_error", error_msg, {"traceback": str(e)})
        logger.log_step("main_error", "error", {"error": error_msg})
        print(f"❌ エラーが発生しました: {e}")
        
        # エラー種別に応じた対処法を表示
        if "429" in error_msg or "Too Many Requests" in error_msg:
            print("\n💡 Google検索でレート制限エラーが発生しました。以下をお試しください:")
            print("   1. Bing検索に切り替え: --use-bing フラグを追加")
            print("   2. Web検索を無効化: --no-google フラグを追加") 
            print(f"   3. 時間を置いて再実行（{ERROR_WAIT_TIME_HOURS_MIN}-{ERROR_WAIT_TIME_HOURS_MAX}時間後）")
            print(f"   例: python main.py \"{args.name}\" --use-bing --api-key \"your-key\"")
        elif "No module named" in error_msg:
            print(f"\n💡 依存関係が不足しています:")
            print(f"   pip install -r requirements.txt")
        elif "OpenAI" in error_msg or "API" in error_msg:
            print(f"\n💡 OpenAI API関連のエラーです:")
            print(f"   - API Keyが正しいか確認してください")
            print(f"   - API利用制限を確認してください")
        
        print(f"\n📋 詳細ログ: cache/latest_execution_log.json")
        sys.exit(1)


def generate_voice_prompt(character_info: Dict[str, Any], api_key: str, logger: Optional[ExecutionLogger] = None) -> Union[str, Dict[str, Any]]:
    """音声プロンプトを生成"""
    from generators.prompt_generator import PromptGenerator
    
    if logger:
        logger.log_step("prompt_generation_init", "start", {"character_name": character_info.get("name")})
    
    generator = PromptGenerator(api_key)
    result = generator.generate_voice_prompt(character_info, logger=logger)
    
    if logger:
        # API呼び出し情報をログに記録
        if isinstance(result, dict) and "api_interaction" in result:
            api_info = result["api_interaction"]
            logger.log_api_call(
                "openai_prompt_generation",
                {
                    "system_prompt": api_info.get("system_prompt", ""),
                    "user_prompt": api_info.get("user_prompt", ""),
                    "model": api_info.get("model", "")
                },
                {
                    "generated_prompt": result.get("generated_prompt", ""),
                    "prompt_length": len(result.get("generated_prompt", ""))
                },
                error=api_info.get("error")
            )
        
        # 自己紹介生成のAPI呼び出しもログに記録
        if isinstance(result, dict) and "character_introduction" in result:
            intro_info = result["character_introduction"]
            if "api_interaction" in intro_info:
                intro_api = intro_info["api_interaction"]
                logger.log_api_call(
                    "openai_character_introduction",
                    {
                        "prompt": intro_api.get("prompt", ""),
                        "model": intro_api.get("model", "")
                    },
                    {
                        "introduction_text": intro_info.get("introduction_text", ""),
                        "introduction_length": len(intro_info.get("introduction_text", ""))
                    },
                    error=intro_api.get("error")
                )
        
        # ポリシー対応版生成のAPI呼び出しもログに記録
        if isinstance(result, dict) and "policy_safe_prompt" in result:
            policy_info = result["policy_safe_prompt"]
            if "api_interaction" in policy_info:
                policy_api = policy_info["api_interaction"]
                logger.log_api_call(
                    "openai_policy_safe_prompt",
                    {
                        "prompt": policy_api.get("prompt", ""),
                        "model": policy_api.get("model", "")
                    },
                    {
                        "safe_prompt": policy_info.get("safe_prompt", ""),
                        "safe_prompt_length": len(policy_info.get("safe_prompt", ""))
                    },
                    error=policy_api.get("error")
                )
    
    return result

if __name__ == "__main__":
    main()