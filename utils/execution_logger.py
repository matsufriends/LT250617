"""
実行ログ記録モジュール - 分析用のキャッシュ機能
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from config import JSON_INDENT_LEVEL


class ExecutionLogger:
    """実行ログを記録・管理するクラス"""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリのパス
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # 実行セッションの開始
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")
        
        # ログデータの初期化
        self.execution_log = {
            "session_id": self.session_id,
            "session_start": self.session_start.isoformat(),
            "character_name": None,
            "steps": [],
            "api_calls": [],
            "errors": [],
            "performance": {},
            "final_result": None
        }
    
    def set_character_name(self, name: str):
        """処理対象のキャラクター名を設定"""
        self.execution_log["character_name"] = name
    
    def log_step(self, step_name: str, status: str, details: Dict[str, Any] = None, duration: float = None):
        """
        実行ステップをログに記録
        
        Args:
            step_name: ステップ名
            status: 実行状態 (start, success, error, info)
            details: 詳細情報
            duration: 実行時間（秒）
        """
        step_data = {
            "timestamp": datetime.now().isoformat(),
            "step_name": step_name,
            "status": status,
            "details": details or {},
            "duration": duration
        }
        
        self.execution_log["steps"].append(step_data)
        
        # リアルタイムで保存
        self._save_log()
    
    def log_api_call(self, api_type: str, request_data: Dict[str, Any], response_data: Dict[str, Any], 
                     duration: float = None, error: str = None):
        """
        API呼び出しをログに記録
        
        Args:
            api_type: API種別 (openai, wikipedia, google, youtube)
            request_data: リクエストデータ
            response_data: レスポンスデータ
            duration: 実行時間（秒）
            error: エラーメッセージ（エラー時）
        """
        api_call_data = {
            "timestamp": datetime.now().isoformat(),
            "api_type": api_type,
            "request": request_data,
            "response": response_data,
            "duration": duration,
            "error": error,
            "status": "error" if error else "success"
        }
        
        self.execution_log["api_calls"].append(api_call_data)
        
        # リアルタイムで保存
        self._save_log()
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """
        エラー情報をログに記録
        
        Args:
            error_type: エラー種別
            error_message: エラーメッセージ
            context: エラー発生時のコンテキスト
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        self.execution_log["errors"].append(error_data)
        
        # リアルタイムで保存
        self._save_log()
    
    def log_performance_metric(self, metric_name: str, value: Any, unit: str = None):
        """
        パフォーマンス指標をログに記録
        
        Args:
            metric_name: 指標名
            value: 値
            unit: 単位
        """
        self.execution_log["performance"][metric_name] = {
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        }
        
        # リアルタイムで保存
        self._save_log()
    
    def set_final_result(self, result: Dict[str, Any]):
        """
        最終結果をログに記録
        
        Args:
            result: 最終結果データ
        """
        self.execution_log["final_result"] = result
        self.execution_log["session_end"] = datetime.now().isoformat()
        
        # 最終保存
        self._save_log()
    
    def _save_log(self):
        """ログをファイルに保存"""
        try:
            # セッション別のログファイル
            log_file = self.cache_dir / f"execution_log_{self.session_id}.json"
            
            # ログ保存時の進捗を表示
            print(f"  💾 ログ更新中: {log_file.name}")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.execution_log, f, ensure_ascii=False, indent=JSON_INDENT_LEVEL)
                f.flush()  # 強制的にバッファをフラッシュ
                os.fsync(f.fileno())  # OSレベルでの書き込み強制
            
            # 最新ログのシンボリックリンク的な役割
            latest_log_file = self.cache_dir / "latest_execution_log.json"
            with open(latest_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.execution_log, f, ensure_ascii=False, indent=JSON_INDENT_LEVEL)
                f.flush()  # 強制的にバッファをフラッシュ
                os.fsync(f.fileno())  # OSレベルでの書き込み強制
                
        except Exception as e:
            print(f"⚠️ ログ保存エラー: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """実行サマリーを取得"""
        total_steps = len(self.execution_log["steps"])
        successful_steps = len([s for s in self.execution_log["steps"] if s["status"] == "success"])
        total_api_calls = len(self.execution_log["api_calls"])
        successful_api_calls = len([a for a in self.execution_log["api_calls"] if a["status"] == "success"])
        total_errors = len(self.execution_log["errors"])
        
        session_duration = None
        if "session_end" in self.execution_log:
            start_time = datetime.fromisoformat(self.execution_log["session_start"])
            end_time = datetime.fromisoformat(self.execution_log["session_end"])
            session_duration = (end_time - start_time).total_seconds()
        
        return {
            "session_id": self.session_id,
            "character_name": self.execution_log["character_name"],
            "total_steps": total_steps,
            "successful_steps": successful_steps,
            "total_api_calls": total_api_calls,
            "successful_api_calls": successful_api_calls,
            "total_errors": total_errors,
            "session_duration": session_duration,
            "performance_metrics": self.execution_log["performance"]
        }


class ExecutionLogAnalyzer:
    """実行ログの分析を行うクラス"""
    
    def __init__(self, cache_dir: str = "cache"):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリのパス
        """
        self.cache_dir = Path(cache_dir)
    
    def load_log(self, session_id: str = None) -> Dict[str, Any]:
        """
        指定されたセッションのログを読み込み
        
        Args:
            session_id: セッションID（Noneの場合は最新ログ）
            
        Returns:
            ログデータ
        """
        try:
            if session_id:
                log_file = self.cache_dir / f"execution_log_{session_id}.json"
            else:
                log_file = self.cache_dir / "latest_execution_log.json"
            
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
                
        except Exception as e:
            print(f"⚠️ ログ読み込みエラー: {e}")
            return {}
    
    def list_all_sessions(self) -> List[str]:
        """全てのセッションIDを取得"""
        try:
            session_ids = []
            for log_file in self.cache_dir.glob("execution_log_*.json"):
                session_id = log_file.stem.replace("execution_log_", "")
                session_ids.append(session_id)
            
            return sorted(session_ids, reverse=True)  # 新しい順
            
        except Exception as e:
            print(f"⚠️ セッション一覧取得エラー: {e}")
            return []
    
    def analyze_api_performance(self, session_id: str = None) -> Dict[str, Any]:
        """
        API呼び出しパフォーマンスを分析
        
        Args:
            session_id: セッションID（Noneの場合は最新ログ）
            
        Returns:
            分析結果
        """
        log_data = self.load_log(session_id)
        if not log_data or "api_calls" not in log_data:
            return {}
        
        api_calls = log_data["api_calls"]
        
        analysis = {
            "total_calls": len(api_calls),
            "successful_calls": len([c for c in api_calls if c["status"] == "success"]),
            "failed_calls": len([c for c in api_calls if c["status"] == "error"]),
            "by_api_type": {},
            "average_duration": {}
        }
        
        # API種別ごとの統計
        for call in api_calls:
            api_type = call["api_type"]
            if api_type not in analysis["by_api_type"]:
                analysis["by_api_type"][api_type] = {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "durations": []
                }
            
            analysis["by_api_type"][api_type]["total"] += 1
            if call["status"] == "success":
                analysis["by_api_type"][api_type]["successful"] += 1
            else:
                analysis["by_api_type"][api_type]["failed"] += 1
            
            if call["duration"]:
                analysis["by_api_type"][api_type]["durations"].append(call["duration"])
        
        # 平均実行時間計算
        for api_type, data in analysis["by_api_type"].items():
            if data["durations"]:
                analysis["average_duration"][api_type] = sum(data["durations"]) / len(data["durations"])
        
        return analysis
    
    def analyze_character_extraction_quality(self, session_id: str = None) -> Dict[str, Any]:
        """
        キャラクター抽出品質を分析
        
        Args:
            session_id: セッションID（Noneの場合は最新ログ）
            
        Returns:
            品質分析結果
        """
        log_data = self.load_log(session_id)
        if not log_data:
            return {}
        
        # 最終結果から品質指標を抽出
        final_result = log_data.get("final_result")
        if not final_result:
            return {}
        
        quality_metrics = {}
        
        # Wikipedia情報の品質
        if "wikipedia_info" in final_result:
            wiki_info = final_result["wikipedia_info"]
            quality_metrics["wikipedia"] = {
                "found": wiki_info.get("found", False),
                "summary_length": len(wiki_info.get("summary", "")),
                "has_categories": bool(wiki_info.get("categories"))
            }
        
        # Google検索結果の品質
        if "google_search_results" in final_result:
            google_info = final_result["google_search_results"]
            quality_metrics["google"] = {
                "total_results": google_info.get("total_results", 0),
                "speech_patterns_found": sum(len(result.get("speech_patterns", [])) 
                                           for result in google_info.get("results", []))
            }
        
        # YouTube情報の品質
        if "youtube_transcripts" in final_result:
            youtube_info = final_result["youtube_transcripts"]
            quality_metrics["youtube"] = {
                "videos_processed": youtube_info.get("total_videos", 0),
                "sample_phrases_count": len(youtube_info.get("sample_phrases", [])),
                "successful_extractions": youtube_info.get("successful_extractions", 0)
            }
        
        return quality_metrics
    
    def generate_analysis_report(self, session_id: str = None) -> str:
        """
        詳細な分析レポートを生成
        
        Args:
            session_id: セッションID（Noneの場合は最新ログ）
            
        Returns:
            分析レポート（テキスト形式）
        """
        log_data = self.load_log(session_id)
        if not log_data:
            return "ログデータが見つかりません。"
        
        # 基本情報
        character_name = log_data.get("character_name", "不明")
        session_start = log_data.get("session_start", "不明")
        session_end = log_data.get("session_end", "実行中")
        
        # パフォーマンス分析
        api_analysis = self.analyze_api_performance(session_id)
        quality_analysis = self.analyze_character_extraction_quality(session_id)
        
        report_lines = [
            f"=== 実行ログ分析レポート ===",
            f"キャラクター名: {character_name}",
            f"セッションID: {log_data.get('session_id', '不明')}",
            f"開始時刻: {session_start}",
            f"終了時刻: {session_end}",
            "",
            "=== API呼び出し統計 ===",
            f"総API呼び出し数: {api_analysis.get('total_calls', 0)}",
            f"成功: {api_analysis.get('successful_calls', 0)}",
            f"失敗: {api_analysis.get('failed_calls', 0)}",
            ""
        ]
        
        # API種別ごとの詳細
        if "by_api_type" in api_analysis:
            report_lines.append("=== API種別ごとの統計 ===")
            for api_type, stats in api_analysis["by_api_type"].items():
                avg_duration = api_analysis.get("average_duration", {}).get(api_type, 0)
                report_lines.extend([
                    f"{api_type}:",
                    f"  - 呼び出し数: {stats['total']}",
                    f"  - 成功率: {stats['successful']}/{stats['total']}",
                    f"  - 平均実行時間: {avg_duration:.2f}秒",
                    ""
                ])
        
        # 品質分析
        if quality_analysis:
            report_lines.append("=== データ品質分析 ===")
            for source, metrics in quality_analysis.items():
                report_lines.append(f"{source}:")
                for metric, value in metrics.items():
                    report_lines.append(f"  - {metric}: {value}")
                report_lines.append("")
        
        # エラー統計
        errors = log_data.get("errors", [])
        if errors:
            report_lines.extend([
                "=== エラー統計 ===",
                f"総エラー数: {len(errors)}",
                ""
            ])
            
            error_types = {}
            for error in errors:
                error_type = error.get("error_type", "unknown")
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            for error_type, count in error_types.items():
                report_lines.append(f"{error_type}: {count}件")
        
        return "\n".join(report_lines)