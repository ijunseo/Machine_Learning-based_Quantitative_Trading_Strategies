"""Rolling Horizon データ分割モジュール.

固定ウィンドウサイズでデータを分割し、時系列順序を維持します。

Rolling Horizonの特徴:
    - 訓練データのサイズが一定（batch_unit）
    - テストデータのサイズが一定（horizon）
    - 最新データから遡って分割可能（latest_first=true）
    
例（batch_unit=200, horizon=5）:
    Fold 1: Train [0:200]    Test [200:205]
    Fold 2: Train [5:205]    Test [205:210]
    Fold 3: Train [10:210]   Test [210:215]

典型的な使用例:
    $ python src/core/data_splitter.py \\
        --config data/experiments/TSLA_experiment.yaml
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Generator, Tuple

import numpy as np
import pandas as pd
import yaml


def load_config(config_path: str) -> Dict[str, Any]:
    """実験設定YAMLを読み込む.
    
    Args:
        config_path: 実験設定YAMLファイルのパス.
        
    Returns:
        設定内容の辞書.
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class RollingHorizonSplitter:
    """Rolling Horizon方式のデータ分割クラス.
    
    固定サイズの訓練ウィンドウをスライドさせながらデータを分割します。
    
    Attributes:
        batch_unit: 訓練データのサンプル数.
        horizon: テストデータのサンプル数.
        latest_first: Trueの場合、最新データから遡って分割.
    """
    
    def __init__(
        self,
        batch_unit: int,
        horizon: int,
        latest_first: bool = True
    ):
        """初期化.
        
        Args:
            batch_unit: 各訓練バッチのサンプル数.
            horizon: 各テストバッチのサンプル数.
            latest_first: 最新データから遡るか.
        """
        self.batch_unit = batch_unit
        self.horizon = horizon
        self.latest_first = latest_first
    
    def split(
        self,
        df: pd.DataFrame
    ) -> Generator[Tuple[int, pd.DataFrame, pd.DataFrame], None, None]:
        """データを分割してyield.
        
        Args:
            df: 分割対象のDataFrame.
            
        Yields:
            (fold_idx, train_df, test_df)のタプル.
        """
        total_size = len(df)
        window_size = self.batch_unit + self.horizon
        
        if total_size < window_size:
            raise ValueError(
                f"データサイズ({total_size})が不足しています。"
                f"最小サイズ: {window_size} (batch_unit + horizon)"
            )
        
        # スタート位置のリストを生成
        if self.latest_first:
            # 最新から遡る
            start_positions = list(range(
                total_size - window_size,
                -1,
                -self.horizon
            ))
        else:
            # 古いデータから進む
            start_positions = list(range(
                0,
                total_size - window_size + 1,
                self.horizon
            ))
        
        # 各ウィンドウで分割
        for fold_idx, start in enumerate(start_positions, start=1):
            train_start = start
            train_end = start + self.batch_unit
            test_start = train_end
            test_end = train_end + self.horizon
            
            train_df = df.iloc[train_start:train_end].copy()
            test_df = df.iloc[test_start:test_end].copy()
            
            yield fold_idx, train_df, test_df


def compute_stats(df: pd.DataFrame, stats_columns: list) -> Dict[str, Any]:
    """データの統計情報を計算.
    
    Args:
        df: 統計を計算するDataFrame.
        stats_columns: 統計を計算する列名のリスト.
        
    Returns:
        統計情報の辞書.
    """
    stats = {
        "n_samples": len(df)
    }
    
    # 日付情報
    if 'Date' in df.columns:
        stats["start_date"] = df['Date'].min().strftime("%Y-%m-%d")
        stats["end_date"] = df['Date'].max().strftime("%Y-%m-%d")
    
    # 数値列の統計
    for col in stats_columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            stats[f"{col}_mean"] = float(df[col].mean())
            stats[f"{col}_std"] = float(df[col].std())
            stats[f"{col}_min"] = float(df[col].min())
            stats[f"{col}_max"] = float(df[col].max())
            
            # Sharpe-like指標（Returnsがある場合）
            if col == "Returns" and df[col].std() != 0:
                stats["sharpe_like"] = float(
                    df[col].mean() / df[col].std() * np.sqrt(252)
                )
    
    return stats


def save_split(
    fold_idx: int,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    save_dir: Path,
    stats_columns: list
) -> None:
    """分割データを保存.
    
    Args:
        fold_idx: Foldのインデックス.
        train_df: 訓練データ.
        test_df: テストデータ.
        save_dir: 保存先ディレクトリ.
        stats_columns: 統計を計算する列名のリスト.
    """
    fold_dir = save_dir / f"fold_{fold_idx}"
    fold_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV保存
    train_df.to_csv(fold_dir / "train.csv", index=False)
    test_df.to_csv(fold_dir / "test.csv", index=False)
    
    # 統計情報
    train_stats = compute_stats(train_df, stats_columns)
    test_stats = compute_stats(test_df, stats_columns)
    
    stats = {
        "fold": fold_idx,
        "train": train_stats,
        "test": test_stats
    }
    
    with open(fold_dir / "stats.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def print_fold_info(
    fold_idx: int,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> None:
    """Fold情報をコンソールに出力.
    
    Args:
        fold_idx: Foldのインデックス.
        train_df: 訓練データ.
        test_df: テストデータ.
    """
    if 'Date' in train_df.columns:
        train_start = train_df['Date'].min().strftime("%Y-%m-%d")
        train_end = train_df['Date'].max().strftime("%Y-%m-%d")
        test_start = test_df['Date'].min().strftime("%Y-%m-%d")
        test_end = test_df['Date'].max().strftime("%Y-%m-%d")
        
        print(f"[Fold {fold_idx}] Train: {train_start} ~ {train_end} (N={len(train_df)})")
        print(f"[Fold {fold_idx}] Test:  {test_start} ~ {test_end} (N={len(test_df)})")
    else:
        print(f"[Fold {fold_idx}] Train: N={len(train_df)}")
        print(f"[Fold {fold_idx}] Test:  N={len(test_df)}")


def run_split(config: Dict[str, Any]) -> None:
    """データ分割を実行.
    
    Args:
        config: 実験設定の辞書.
    """
    ticker = config.get('ticker', 'UNKNOWN')
    split_config = config['split']
    
    # データ読み込み
    input_path = split_config['input_data']
    df = pd.read_csv(input_path)
    
    # 日付列の処理
    date_column = split_config.get('date_column', 'Date')
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(date_column).reset_index(drop=True)
    
    # Splitter初期化
    splitter = RollingHorizonSplitter(
        batch_unit=split_config['batch_unit'],
        horizon=split_config['horizon'],
        latest_first=split_config.get('latest_first', True)
    )
    
    # 保存先
    save_dir = Path(split_config['save_dir'])
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用設定のスナップショットを保存
    with open(save_dir / "experiment_config.yaml", 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    # 分割実行
    print(f"\n{'='*60}")
    print(f"Rolling Horizon Split: {ticker}")
    print(f"  Batch Unit: {split_config['batch_unit']}")
    print(f"  Horizon: {split_config['horizon']}")
    print(f"  Latest First: {split_config.get('latest_first', True)}")
    print(f"{'='*60}\n")
    
    stats_columns = split_config.get('stats_columns', ['Returns', 'Close'])
    
    for fold_idx, train_df, test_df in splitter.split(df):
        save_split(fold_idx, train_df, test_df, save_dir, stats_columns)
        print_fold_info(fold_idx, train_df, test_df)
        print()
    
    print(f"✅ All splits saved to: {save_dir}")


def main() -> None:
    """CLIエントリーポイント."""
    parser = argparse.ArgumentParser(
        description="Rolling Horizon データ分割を実行",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--config',
        type=str,
        required=True,
        help='実験設定YAMLファイルのパス（例: data/experiments/TSLA_experiment.yaml）'
    )
    
    args = parser.parse_args()
    
    # 設定読み込み
    config = load_config(args.config)
    
    # 分割実行
    run_split(config)


if __name__ == "__main__":
    main()
