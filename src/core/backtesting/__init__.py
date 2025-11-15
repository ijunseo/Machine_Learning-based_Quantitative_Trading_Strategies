"""
バックテスト機能パッケージ

CPCV、Purging、Embargoなどの時系列分割機能を提供します。
"""

from .cpcv_splitter import CPCVSplitter, apply_embargo, apply_purging

__all__ = [
    "CPCVSplitter",
    "apply_purging",
    "apply_embargo",
]
