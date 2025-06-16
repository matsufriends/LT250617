"""
時間計測用のユーティリティ
"""

import time
from typing import Any, Callable, TypeVar, Optional
from contextlib import contextmanager

T = TypeVar('T')


@contextmanager
def timer():
    """
    コンテキストマネージャーとして使用する時間計測器
    
    Usage:
        with timer() as t:
            # 処理
        print(f"所要時間: {t.duration}秒")
    """
    class TimerResult:
        def __init__(self):
            self.start_time = time.time()
            self.duration = 0
            
        def stop(self):
            self.duration = time.time() - self.start_time
            return self.duration
    
    timer_result = TimerResult()
    try:
        yield timer_result
    finally:
        timer_result.stop()


def measure_time(func: Callable[..., T]) -> Callable[..., tuple[T, float]]:
    """
    関数の実行時間を計測するデコレータ
    
    Args:
        func: 計測対象の関数
        
    Returns:
        (関数の戻り値, 実行時間) のタプルを返す関数
    """
    def wrapper(*args, **kwargs) -> tuple[T, float]:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            return result, duration
        except Exception as e:
            duration = time.time() - start_time
            raise e
    
    return wrapper


def time_function(func: Callable[..., T], *args, **kwargs) -> tuple[T, float]:
    """
    関数を実行して結果と実行時間を返す
    
    Args:
        func: 実行する関数
        *args: 関数に渡す引数
        **kwargs: 関数に渡すキーワード引数
        
    Returns:
        (関数の戻り値, 実行時間) のタプル
    """
    start_time = time.time()
    try:
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        return result, duration
    except Exception as e:
        duration = time.time() - start_time
        raise e