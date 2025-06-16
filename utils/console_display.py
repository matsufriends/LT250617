"""
リアルタイム更新コンソール表示ユーティリティ
"""

import sys
import os
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime

# Windows環境でANSIカラーを有効化
if sys.platform == "win32":
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass


class ConsoleDisplay:
    """リアルタイムで更新されるコンソール表示を管理するクラス"""
    
    def __init__(self):
        self.status = {
            "character_name": "",
            "wikipedia": {"status": "待機中", "progress": "", "time": ""},
            "web_search": {"status": "待機中", "progress": "", "time": ""},
            "youtube": {"status": "待機中", "progress": "", "time": ""},
            "overall": {"status": "初期化中", "elapsed": 0}
        }
        self.start_time = time.time()
        self.is_running = True
        self.lock = threading.Lock()
        self.display_thread = None
        self.first_render = True
        
    def start(self, character_name: str):
        """表示を開始"""
        self.status["character_name"] = character_name
        self.status["overall"]["status"] = "情報収集中"
        self.start_time = time.time()
        self.is_running = True
        
        # print出力を抑制
        from utils.output_suppressor import enable_print_suppression
        enable_print_suppression()
        
        # 表示スレッドを開始
        self.display_thread = threading.Thread(target=self._display_loop)
        self.display_thread.daemon = True
        self.display_thread.start()
        
    def stop(self):
        """表示を停止"""
        self.is_running = False
        if self.display_thread:
            self.display_thread.join(timeout=1)
        
        # print出力抑制を解除
        from utils.output_suppressor import disable_print_suppression
        captured_output = disable_print_suppression()
        
        # 最終状態を表示
        self._clear_console()
        self._render()
        print("\n")  # 最後に改行を追加
        
        # 抑制されていた重要な出力があれば表示（エラーメッセージなど）
        if captured_output.strip():
            # エラーや重要なメッセージのみを抽出して表示
            important_lines = []
            for line in captured_output.split('\n'):
                if any(keyword in line for keyword in ['❌', '⚠️', 'エラー', 'Error', '失敗', 'Failed']):
                    important_lines.append(line)
            
            if important_lines:
                print("📋 処理中に発生した重要な通知:")
                for line in important_lines:
                    print(f"  {line}")
        
    def update_status(self, component: str, status: str, progress: str = "", time_info: str = ""):
        """ステータスを更新"""
        with self.lock:
            if component in self.status:
                self.status[component]["status"] = status
                if progress:
                    self.status[component]["progress"] = progress
                if time_info:
                    self.status[component]["time"] = time_info
                    
    def _display_loop(self):
        """表示を更新するループ"""
        while self.is_running:
            if not self.first_render:
                self._clear_console()
            else:
                self.first_render = False
            self._render()
            time.sleep(0.1)  # 100msごとに更新
            
    def _clear_console(self):
        """コンソール表示をクリア（カーソルを上に移動）"""
        # カーソルを7行上に移動して、表示をリフレッシュ
        sys.stdout.write('\033[7A\033[J')  # 7行上に移動して下をクリア
        sys.stdout.flush()
        
    def _render(self):
        """現在の状態をレンダリング"""
        with self.lock:
            elapsed = int(time.time() - self.start_time)
            self.status["overall"]["elapsed"] = elapsed
            
            # ヘッダー
            print(f"╔══════════════════════════════════════════════════════════════════╗")
            print(f"║ キャラクター情報収集: {self.status['character_name']:<30} ║")
            print(f"║ 経過時間: {self._format_time(elapsed):<46} ║")
            print(f"╠══════════════════════════════════════════════════════════════════╣")
            
            # 各コンポーネントの状態
            self._render_component("Wikipedia", self.status["wikipedia"])
            self._render_component("Web検索", self.status["web_search"])
            self._render_component("YouTube", self.status["youtube"])
            
            print(f"╚══════════════════════════════════════════════════════════════════╝")
            
    def _render_component(self, name: str, info: Dict[str, Any]):
        """コンポーネントの状態を表示"""
        status_icon = self._get_status_icon(info["status"])
        status_text = f"{status_icon} {info['status']}"
        
        # プログレスバーを作成
        if info["progress"]:
            progress_bar = self._create_progress_bar(info["progress"])
            status_line = f"{name:12} {status_text:20} {progress_bar}"
        else:
            status_line = f"{name:12} {status_text:20}"
            
        # 時間情報があれば追加
        if info.get("time"):
            status_line += f" ({info['time']})"
            
        print(f"║ {status_line:<64} ║")
        
    def _get_status_icon(self, status: str) -> str:
        """ステータスに応じたアイコンを返す"""
        icons = {
            "待機中": "⏸️",
            "実行中": "🔄",
            "処理中": "⚙️",
            "完了": "✅",
            "エラー": "❌",
            "タイムアウト": "⏱️",
            "スキップ": "⏭️"
        }
        return icons.get(status, "❓")
        
    def _create_progress_bar(self, progress: str) -> str:
        """プログレスバーを作成"""
        # progress は "10/20" のような形式を想定
        try:
            if "/" in progress:
                current, total = map(int, progress.split("/"))
                percentage = (current / total) * 100 if total > 0 else 0
            else:
                percentage = float(progress.strip("%"))
                
            bar_length = 20
            filled = int((percentage / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            return f"[{bar}] {percentage:5.1f}%"
        except:
            return progress
            
    def _format_time(self, seconds: int) -> str:
        """秒数を MM:SS 形式にフォーマット"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class ProgressReporter:
    """進捗を報告するためのヘルパークラス"""
    
    def __init__(self, console_display: ConsoleDisplay):
        self.console = console_display
        self.component_start_times = {}
        
    def start_component(self, component: str):
        """コンポーネントの処理開始を報告"""
        self.component_start_times[component] = time.time()
        self.console.update_status(component, "実行中")
        
    def update_progress(self, component: str, current: int, total: int, detail: str = ""):
        """進捗を更新"""
        progress = f"{current}/{total}"
        status = "処理中" if detail else "実行中"
        self.console.update_status(component, status, progress, detail)
        
    def complete_component(self, component: str, success: bool = True, message: str = ""):
        """コンポーネントの処理完了を報告"""
        elapsed = time.time() - self.component_start_times.get(component, time.time())
        time_str = f"{elapsed:.1f}秒"
        
        if success:
            status = "完了"
        else:
            status = "エラー" if message else "スキップ"
            
        self.console.update_status(component, status, "", time_str)
        
    def error_component(self, component: str, error_msg: str):
        """エラーを報告"""
        elapsed = time.time() - self.component_start_times.get(component, time.time())
        time_str = f"{elapsed:.1f}秒"
        self.console.update_status(component, "エラー", "", time_str)