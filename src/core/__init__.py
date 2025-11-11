"""コア機能パッケージ

データ分割、ラベリング、実験設定生成などの機能を提供します。
"""

from .data_splitter import DataSplitter

__all__ = [
    "DataSplitter",
]
