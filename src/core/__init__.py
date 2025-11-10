"""コアモジュール.

データ分割、ラベル付け、実験設定生成などのコア機能を提供します。
"""

from .data_splitter import RollingHorizonSplitter, run_split
from .generate_ticker_yaml import generate_all_ticker_configs
from .triple_barrier_labeler import apply_labeling, triple_barrier_label

__all__ = [
    'RollingHorizonSplitter',
    'run_split',
    'generate_all_ticker_configs',
    'apply_labeling',
    'triple_barrier_label',
]
