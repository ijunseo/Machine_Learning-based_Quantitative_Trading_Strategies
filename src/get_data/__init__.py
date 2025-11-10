"""データ取得モジュール.

yfinanceを使用した株価データの取得機能を提供します。
"""

from .fetcher import fetch_and_save_all, load_config

__all__ = ['fetch_and_save_all', 'load_config']
