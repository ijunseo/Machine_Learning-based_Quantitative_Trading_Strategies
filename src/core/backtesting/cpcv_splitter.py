"""
CPCV (Combinatorial Purged Cross-Validation) Splitter

時系列データに対する情報リークを防ぐためのPurging/Embargoを実装。

References:
    - Advances in Financial Machine Learning (Marcos López de Prado)
"""

from itertools import combinations
from typing import Iterator, Tuple, Optional

import numpy as np
import pandas as pd


class CPCVSplitter:
    """
    CPCV (Combinatorial Purged Cross-Validation) Splitter
    
    時系列データをN個のブロックに分割し、K個のテストブロックを選択。
    Purging/Embargoを適用して情報リークを防止します。
    
    Attributes:
        n_blocks (int): 全ブロック数
        n_test_blocks (int): テストに使用するブロック数
        purge_window (int): Purging期間（日数）
        embargo_window (int): Embargo期間（日数）
    
    Examples:
        >>> splitter = CPCVSplitter(n_blocks=10, n_test_blocks=2, purge_window=5, embargo_window=3)
        >>> for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(df)):
        ...     print(f"Fold {fold_idx}: Train={len(train_idx)}, Test={len(test_idx)}")
    """
    
    def __init__(
        self,
        n_blocks: int = 10,
        n_test_blocks: int = 2,
        purge_window: int = 5,
        embargo_window: int = 3
    ) -> None:
        """
        CPCV Splitterを初期化する。
        
        Args:
            n_blocks: 全ブロック数
            n_test_blocks: テストに使用するブロック数
            purge_window: Purging期間（日数）
            embargo_window: Embargo期間（日数）
        """
        if n_test_blocks >= n_blocks:
            raise ValueError(f"n_test_blocks ({n_test_blocks}) must be < n_blocks ({n_blocks})")
        
        self.n_blocks = n_blocks
        self.n_test_blocks = n_test_blocks
        self.purge_window = purge_window
        self.embargo_window = embargo_window
    
    def split(
        self,
        X: pd.DataFrame,
        barrier_times: Optional[pd.DataFrame] = None
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        データをCPCV方式で分割する。
        
        Args:
            X: 分割対象のDataFrame
            barrier_times: Triple Barrierのメタ情報（t0, t1を含むDataFrame）
                - t0: エントリー時刻
                - t1: エグジット時刻
        
        Yields:
            Tuple[np.ndarray, np.ndarray]: (訓練インデックス, テストインデックス)
        
        Notes:
            - barrier_timesが提供されない場合、時間ベースのPurgingのみ適用
            - barrier_timesがある場合、オーバーラップ検出による高度なPurgingを実施
        """
        n_samples = len(X)
        block_size = n_samples // self.n_blocks
        
        # ブロックインデックスの作成
        block_indices = []
        for i in range(self.n_blocks):
            start = i * block_size
            end = (i + 1) * block_size if i < self.n_blocks - 1 else n_samples
            block_indices.append(np.arange(start, end))
        
        # K個のテストブロックの組み合わせを生成
        for test_blocks in combinations(range(self.n_blocks), self.n_test_blocks):
            # テストインデックス
            test_idx = np.concatenate([block_indices[i] for i in test_blocks])
            
            # 訓練インデックス（テスト以外）
            train_blocks = [i for i in range(self.n_blocks) if i not in test_blocks]
            train_idx = np.concatenate([block_indices[i] for i in train_blocks])
            
            # Purging適用
            if barrier_times is not None:
                train_idx = apply_purging(
                    train_idx=train_idx,
                    test_idx=test_idx,
                    barrier_times=barrier_times
                )
            else:
                # 時間ベースのPurging
                train_idx = apply_time_based_purging(
                    train_idx=train_idx,
                    test_idx=test_idx,
                    purge_window=self.purge_window
                )
            
            # Embargo適用
            train_idx = apply_embargo(
                train_idx=train_idx,
                test_idx=test_idx,
                embargo_window=self.embargo_window
            )
            
            yield train_idx, test_idx


def apply_purging(
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    barrier_times: pd.DataFrame
) -> np.ndarray:
    """
    Triple Barrierのメタ情報を用いたPurgingを適用する。
    
    Args:
        train_idx: 訓練データのインデックス
        test_idx: テストデータのインデックス
        barrier_times: Triple Barrierのメタ情報（t0, t1を含む）
    
    Returns:
        Purging適用後の訓練インデックス
    
    Notes:
        以下の条件を満たす訓練サンプルを除外:
        - t1_train > t0_test（訓練のエグジットがテストのエントリーより後）
    
    Examples:
        >>> barrier_times = pd.DataFrame({
        ...     "t0": pd.date_range("2020-01-01", periods=100),
        ...     "t1": pd.date_range("2020-01-06", periods=100)
        ... })
        >>> train_idx = np.arange(50)
        >>> test_idx = np.arange(50, 70)
        >>> clean_train = apply_purging(train_idx, test_idx, barrier_times)
    """
    # テスト期間の最小エントリー時刻
    test_start = barrier_times.iloc[test_idx]["t0"].min()
    
    # 訓練データのエグジット時刻
    train_exit = barrier_times.iloc[train_idx]["t1"]
    
    # t1_train <= test_start のサンプルのみ保持
    valid_train_mask = train_exit <= test_start
    clean_train_idx = train_idx[valid_train_mask.values]
    
    return clean_train_idx


def apply_time_based_purging(
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    purge_window: int
) -> np.ndarray:
    """
    時間ベースのPurgingを適用する（barrier_timesがない場合）。
    
    Args:
        train_idx: 訓練データのインデックス
        test_idx: テストデータのインデックス
        purge_window: Purging期間（サンプル数）
    
    Returns:
        Purging適用後の訓練インデックス
    
    Notes:
        テスト期間の直前purge_window期間のデータを訓練から除外。
    """
    test_start = test_idx.min()
    purge_threshold = test_start - purge_window
    
    # train_idx < purge_threshold のサンプルのみ保持
    clean_train_idx = train_idx[train_idx < purge_threshold]
    
    return clean_train_idx


def apply_embargo(
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    embargo_window: int
) -> np.ndarray:
    """
    Embargoを適用する。
    
    Args:
        train_idx: 訓練データのインデックス
        test_idx: テストデータのインデックス
        embargo_window: Embargo期間（サンプル数）
    
    Returns:
        Embargo適用後の訓練インデックス
    
    Notes:
        テスト期間の直後embargo_window期間のデータを訓練から除外。
    
    Examples:
        >>> train_idx = np.arange(100)
        >>> test_idx = np.arange(50, 70)
        >>> embargo_window = 5
        >>> clean_train = apply_embargo(train_idx, test_idx, embargo_window)
        >>> # test_idx の直後5サンプル（70-75）が除外される
    """
    test_end = test_idx.max()
    embargo_threshold = test_end + embargo_window
    
    # train_idx > embargo_threshold または train_idx < test_idx.min() のサンプルを保持
    test_start = test_idx.min()
    valid_mask = (train_idx < test_start) | (train_idx > embargo_threshold)
    clean_train_idx = train_idx[valid_mask]
    
    return clean_train_idx
