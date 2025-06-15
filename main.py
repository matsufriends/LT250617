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
from utils.execution_logger import ExecutionLogger

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
    
    args = parser.parse_args()
    
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
    print()
    
    try:
        # 情報収集
        print("📚 情報収集中...")
        start_time = time.time()
        character_info = collect_character_info(args.name, api_key=api_key, logger=logger, use_youtube=not args.no_youtube)
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
            character_info["prompt_generation_api"] = prompt_result["api_interaction"]
        else:
            # 後方互換性のため
            final_prompt = prompt_result
        
        # 最終結果をログに記録
        final_result = {
            "character_name": args.name,
            "generated_prompt": final_prompt,
            "prompt_length": len(final_prompt),
            "character_info": character_info
        }
        logger.set_final_result(final_result)
        
        # 結果出力
        print("\n" + "="*60)
        print("生成されたプロンプト:")
        print("="*60)
        print(final_prompt)
        print("="*60)
        
        # ファイル出力
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(final_prompt)
            print(f"\n✅ 結果を {args.output} に保存しました。")
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
        sys.exit(1)

def collect_character_info(name: str, api_key: str = None, logger: ExecutionLogger = None, use_youtube: bool = True) -> dict:
    """キャラクター情報を収集"""
    from collectors.wikipedia_collector import WikipediaCollector
    from collectors.google_collector import GoogleCollector
    from collectors.youtube_collector import YouTubeCollector
    
    # キャッシュ機能は廃止（ユーザー要求）
    # 常にランタイムで新規取得
    
    # 情報収集開始
    character_info = {"name": name}
    
    # Wikipedia情報収集
    print("📖 Wikipedia情報を収集中...")
    if logger:
        logger.log_step("wikipedia_collection", "start", {"character_name": name})
    
    start_time = time.time()
    wiki_collector = WikipediaCollector()
    character_info["wikipedia_info"] = wiki_collector.collect_info(name, logger=logger)
    wiki_duration = time.time() - start_time
    
    if logger:
        logger.log_step("wikipedia_collection", "success", character_info["wikipedia_info"], wiki_duration)
        logger.log_performance_metric("wikipedia_duration", wiki_duration, "seconds")
    
    # Google検索情報収集
    print("🔍 Google検索情報を収集中...")
    if logger:
        logger.log_step("google_collection", "start", {"character_name": name})
    
    start_time = time.time()
    google_collector = GoogleCollector(delay=1.5)  # 少し長めの待機時間
    character_info["google_search_results"] = google_collector.collect_info(name, logger=logger, api_key=api_key)
    google_duration = time.time() - start_time
    
    if logger:
        logger.log_step("google_collection", "success", character_info["google_search_results"], google_duration)
        logger.log_performance_metric("google_duration", google_duration, "seconds")
    
    # YouTube情報収集（オプション）
    if use_youtube:
        print("🎥 YouTube情報を収集中...")
        if logger:
            logger.log_step("youtube_collection", "start", {"character_name": name})
        
        start_time = time.time()
        youtube_urls = google_collector.search_youtube_videos(name)
        youtube_collector = YouTubeCollector()
        youtube_info = youtube_collector.collect_info(youtube_urls, logger=logger)
        youtube_duration = time.time() - start_time
        
        if logger:
            logger.log_step("youtube_collection", "success", youtube_info, youtube_duration)
            logger.log_performance_metric("youtube_duration", youtube_duration, "seconds")
        
        # キャラクター特定フィルタリング（API Keyがある場合）
        if youtube_info["found"] and api_key and api_key != "test-key":
            print("🎯 キャラクター発言の特定中...")
            if logger:
                logger.log_step("character_filtering", "start", {"character_name": name})
            
            start_time = time.time()
            all_transcript_text = []
            for transcript in youtube_info["transcripts"]:
                all_transcript_text.append(transcript["text"])
            
            # ChatGPT APIでキャラクターの発言を特定
            filter_result = youtube_collector.filter_character_speech(
                all_transcript_text, name, api_key
            )
            filtering_duration = time.time() - start_time
            
            if isinstance(filter_result, dict):
                youtube_info["sample_phrases"] = filter_result["filtered_phrases"]
                youtube_info["character_filtering_api"] = filter_result["api_interaction"]
                
                if logger:
                    logger.log_api_call(
                        "openai_filtering",
                        filter_result["api_interaction"].get("user_prompt", {}),
                        {"filtered_phrases": filter_result["filtered_phrases"]},
                        filtering_duration
                    )
            else:
                # 後方互換性のため
                youtube_info["sample_phrases"] = filter_result
            
            if logger:
                logger.log_step("character_filtering", "success", 
                              {"filtered_phrases_count": len(youtube_info.get("sample_phrases", []))}, 
                              filtering_duration)
                logger.log_performance_metric("filtering_duration", filtering_duration, "seconds")
        
        character_info["youtube_transcripts"] = youtube_info
    else:
        print("🎥 YouTube情報収集をスキップしました (--no-youtube)")
        character_info["youtube_transcripts"] = {
            "found": False,
            "error": "YouTube情報収集が無効化されています",
            "transcripts": [],
            "total_videos": 0,
            "sample_phrases": [],
            "skipped": True
        }
        if logger:
            logger.log_step("youtube_collection", "skipped", {"reason": "no-youtube flag"}, 0)
    
    return character_info

def generate_voice_prompt(character_info: dict, api_key: str, logger: ExecutionLogger = None):
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
    
    return result

if __name__ == "__main__":
    main()