"""
Rolling Horizon Splitter

時系列データに対するRolling Horizon分割を実装します。
将来的にCPCV (Combinatorial Purged Cross-Validation) も追加予定。
"""

from typing import Iterator, Tuple
import numpy as np
import pandas as pd


class RollingHorizonSplitter:
    """
    Rolling Horizon方式でデータを分割するクラス
    
    最新データから遡って固定ウィンドウで訓練/テストセットを生成します。
    
    Attributes:
        batch_unit (int): 訓練データのサイズ
        horizon (int): テストデータのサイズ
        latest_first (bool): 最新データから遡るかどうか
    """
    
    def __init__(
        self,
        batch_unit: int = 200,
        horizon: int = 5,
        latest_first: bool = True
    ) -> None:
        """
        Rolling Horizon Splitterを初期化する。
        
        Args:
            batch_unit: 訓練データのサイズ
            horizon: テストデータのサイズ
            latest_first: 最新データから遡るかどうか
        """
        self.batch_unit = batch_unit
        self.horizon = horizon
        self.latest_first = latest_first
    
    def split(
        self,
        X: pd.DataFrame
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        データをRolling Horizon方式で分割する。
        
        Args:
            X: 分割対象のDataFrame
        
        Yields:
            Tuple[np.ndarray, np.ndarray]: (訓練インデックス, テストインデックス)
        
        Examples:
            >>> splitter = RollingHorizonSplitter(batch_unit=200, horizon=5)
            >>> for train_idx, test_idx in splitter.split(df):
            ...     X_train, X_test = df.iloc[train_idx], df.iloc[test_idx]
        """
        n_samples = len(X)
        
        if self.latest_first:
            # 最新データから遡る
            current_end = n_samples
            
            while current_end - self.horizon - self.batch_unit >= 0:
                test_start = current_end - self.horizon
                test_end = current_end
                train_start = test_start - self.batch_unit
                train_end = test_start
                
                train_idx = np.arange(train_start, train_end)
                test_idx = np.arange(test_start, test_end)
                
                yield train_idx, test_idx
                
                current_end = train_start
        else:
            # 古いデータから順に
            current_start = 0
            
            while current_start + self.batch_unit + self.horizon <= n_samples:
                train_start = current_start
                train_end = current_start + self.batch_unit
                test_start = train_end
                test_end = test_start + self.horizon
                
                train_idx = np.arange(train_start, train_end)
                test_idx = np.arange(test_start, test_end)
                
                yield train_idx, test_idx
                
                current_start = test_end


class CPCVSplitter:
    """
    CPCV (Combinatorial Purged Cross-Validation) Splitter
    
    時系列データに対する情報リークを防ぐためのPurging/Embargoを実装します。
    ※ 将来実装予定
    
    Attributes:
        n_blocks (int): 全ブロック数
        n_test_blocks (int): テストに使用するブロック数
        purge_window (int): Purging期間（日数）
        embargo_window (int): Embargo期間（日数）
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
        self.n_blocks = n_blocks
        self.n_test_blocks = n_test_blocks
        self.purge_window = purge_window
        self.embargo_window = embargo_window
    
    def split(
        self,
        X: pd.DataFrame
    ) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        データをCPCV方式で分割する。
        
        Args:
            X: 分割対象のDataFrame
        
        Yields:
            Tuple[np.ndarray, np.ndarray]: (訓練インデックス, テストインデックス)
        
        Raises:
            NotImplementedError: 現在未実装
        """
        raise NotImplementedError(
            "CPCV Splitterは将来実装予定です。"
            "現在はRollingHorizonSplitterを使用してください。"
        )
