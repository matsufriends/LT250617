"""
出力抑制ユーティリティ
リアルタイム表示時にprint文による出力干渉を防ぐ
"""

import sys
import io
import threading
from contextlib import contextmanager
from typing import Optional


class OutputSuppressor:
    """標準出力を抑制するクラス"""
    
    def __init__(self):
        self._suppress_stdout = False
        self._original_stdout = sys.stdout
        self._captured_output = io.StringIO()
        self._lock = threading.Lock()
    
    def enable_suppression(self):
        """出力抑制を有効にする"""
        with self._lock:
            self._suppress_stdout = True
            self._captured_output = io.StringIO()
            sys.stdout = self._captured_output
    
    def disable_suppression(self):
        """出力抑制を無効にする"""
        with self._lock:
            self._suppress_stdout = False
            sys.stdout = self._original_stdout
            # 抑制されていた出力を取得（必要に応じて使用）
            captured = self._captured_output.getvalue()
            self._captured_output = io.StringIO()
            return captured
    
    def is_suppressed(self) -> bool:
        """現在抑制中かどうかを返す"""
        return self._suppress_stdout
    
    def get_captured_output(self) -> str:
        """抑制されていた出力を取得"""
        with self._lock:
            return self._captured_output.getvalue()
    
    @contextmanager
    def suppress(self):
        """コンテキストマネージャとして使用"""
        self.enable_suppression()
        try:
            yield self
        finally:
            self.disable_suppression()


# グローバルインスタンス
_global_suppressor: Optional[OutputSuppressor] = None
_lock = threading.Lock()


def get_suppressor() -> OutputSuppressor:
    """グローバル出力抑制器を取得"""
    global _global_suppressor
    with _lock:
        if _global_suppressor is None:
            _global_suppressor = OutputSuppressor()
        return _global_suppressor


def safe_print(*args, **kwargs):
    """
    抑制されていない場合のみ出力するprint関数
    リアルタイム表示が有効な場合は出力を抑制
    """
    suppressor = get_suppressor()
    if not suppressor.is_suppressed():
        print(*args, **kwargs)


def force_print(*args, **kwargs):
    """
    抑制状態に関わらず強制的に出力するprint関数
    重要なメッセージやエラーに使用
    """
    suppressor = get_suppressor()
    original_stdout = suppressor._original_stdout
    print(*args, file=original_stdout, **kwargs)


# モンキーパッチ用の関数
def _patched_print(*args, **kwargs):
    """
    print関数のモンキーパッチ版
    抑制状態を考慮して出力を制御
    """
    suppressor = get_suppressor()
    if suppressor.is_suppressed():
        # 抑制中は何も出力しない
        return
    else:
        # 元のprint関数を呼び出し
        suppressor._original_stdout.write(' '.join(str(arg) for arg in args))
        if kwargs.get('end', '\n'):
            suppressor._original_stdout.write(kwargs.get('end', '\n'))
        suppressor._original_stdout.flush()


def enable_print_suppression():
    """
    グローバルなprint抑制を有効にする
    リアルタイム表示開始時に呼び出す
    """
    get_suppressor().enable_suppression()


def disable_print_suppression():
    """
    グローバルなprint抑制を無効にする
    リアルタイム表示終了時に呼び出す
    """
    return get_suppressor().disable_suppression()