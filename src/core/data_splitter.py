"""Data Splitter

時系列データの分割を管理するモジュール。
Rolling Horizon分割をサポート。
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

# UTF-8出力を強制
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.rolling_horizon_splitter import RollingHorizonSplitter
from src.core.backtesting.cpcv_splitter import CPCVSplitter


def cpcv_split(
    ticker: str,
    config: Dict[str, Any],
    data_dir: str = "data",
) -> None:
    """
    CPCV法によるデータ分割（Combinatorial Purged Cross-Validation）

    Args:
        ticker: ティッカーシンボル
        config: 実験設定（n_blocks, n_test_blocks, purge_window, embargo_window）
        data_dir: データディレクトリ
    """
    print("=" * 60)
    print(f"CPCV Split: {ticker}")
    print("=" * 60)
    print(f"  N Blocks: {config['n_blocks']}")
    print(f"  N Test Blocks: {config['n_test_blocks']}")
    print(f"  Purge Window: {config['purge_window']} days")
    print(f"  Embargo Window: {config['embargo_window']} days")
    print("=" * 60)
    print()

    processed_path = os.path.join(data_dir, "processed", f"{ticker}_features_labeled.csv")
    
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Labeled data not found: {processed_path}")
    
    print(f"Loading data: {processed_path}")
    
    # Date列を読み込んでインデックスに設定
    df = pd.read_csv(processed_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    
    # ラベルがNaNの行を除外 (保有中のサンプル)
    df = df[df['Label'].notna()]
    
    print(f"CPCV: {ticker} | Blocks={config['n_blocks']}, Test={config['n_test_blocks']} | Samples={len(df)}")
    
    splitter = CPCVSplitter(
        n_blocks=config["n_blocks"],
        n_test_blocks=config["n_test_blocks"],
        purge_window=config["purge_window"],
        embargo_window=config["embargo_window"],
    )
    
    splits_dir = Path(data_dir) / "splits" / ticker
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate expected folds: C(n_blocks, n_test_blocks)
    from math import comb
    expected_folds = comb(config["n_blocks"], config["n_test_blocks"])
    
    fold_idx = 0
    for train_idx, test_idx in splitter.split(df):
        train_data = df.iloc[train_idx].copy()
        test_data = df.iloc[test_idx].copy()
        
        # インデックスをソート
        train_data = train_data.sort_index()
        test_data = test_data.sort_index()
        
        train_path = splits_dir / f"fold_{fold_idx}_train.csv"
        train_data.to_csv(train_path, index=True, index_label='Date')
        
        test_path = splits_dir / f"fold_{fold_idx}_test.csv"
        test_data.to_csv(test_path, index=True, index_label='Date')
        
        # Progress every 10 folds
        if fold_idx % 10 == 0:
            print(f"  Fold {fold_idx}/{expected_folds} completed")
        
        fold_idx += 1
    
    print(f"✅ {fold_idx} folds created for {ticker}")


def rolling_horizon_split(
    ticker: str,
    config: Dict[str, Any],
    data_dir: str = "data",
) -> None:
    """
    Rolling Horizon法によるデータ分割（時系列）

    Args:
        ticker: ティッカーシンボル
        config: 実験設定（batch_unit, horizon等）
        data_dir: データディレクトリ
    """
    print("=" * 60)
    print(f"Rolling Horizon Split: {ticker}")
    print("=" * 60)
    print(f"  Batch Unit: {config['batch_unit']}")
    print(f"  Horizon: {config['horizon']}")
    print(f"  Latest First: {config.get('latest_first', True)}")
    print("=" * 60)
    print()

    processed_path = os.path.join(data_dir, "processed", f"{ticker}_features_labeled.csv")
    
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Labeled data not found: {processed_path}")
    
    print(f"Loading data: {processed_path}")
    
    # ★ 修正: Date列を読み込んでインデックスに設定
    df = pd.read_csv(processed_path)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
    
    # ★ 追加: ラベルがNaNの行を除外 (保有中のサンプル)
    df = df[df['Label'].notna()]
    
    print(f"  Labeled samples: {len(df)} (after removing NaN)")
    print()
    
    splitter = RollingHorizonSplitter(
        batch_unit=config["batch_unit"],
        horizon=config["horizon"],
        latest_first=config.get("latest_first", True),
    )
    
    splits_dir = Path(data_dir) / "splits" / ticker
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    fold_idx = 0
    for train_idx, test_idx in splitter.split(df):
        train_data = df.iloc[train_idx]
        train_path = splits_dir / f"fold_{fold_idx}_train.csv"
        train_data.to_csv(train_path, index=True, index_label='Date')
        
        test_data = df.iloc[test_idx]
        test_path = splits_dir / f"fold_{fold_idx}_test.csv"
        test_data.to_csv(test_path, index=True, index_label='Date')
        
        print(f"Fold {fold_idx}:")
        print(f"  Train: {train_data.index[0]} ~ {train_data.index[-1]} ({len(train_data)} samples)")
        print(f"  Test:  {test_data.index[0]} ~ {test_data.index[-1]} ({len(test_data)} samples)")
        print()
        
        fold_idx += 1
    
    print("=" * 60)
    print(f"✅ {fold_idx} folds created for {ticker}")
    print(f"   Output: {splits_dir}")
    print("=" * 60)


class DataSplitter:
    """
    データ分割を管理するクラス
    
    実験設定に基づいてティッカーごとのデータ分割を実行します。
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        DataSplitterを初期化する。
        
        Args:
            data_dir: データディレクトリ
        """
        self.data_dir = data_dir
        self.experiments_dir = Path(data_dir) / "experiments"
    
    def split_all(self) -> None:
        """
        全ティッカーのデータ分割を実行する。
        """
        if not self.experiments_dir.exists():
            raise FileNotFoundError(
                f"Experiments directory not found: {self.experiments_dir}\n"
                "Run 'make generate-experiments' first."
            )
        
        experiment_files = list(self.experiments_dir.glob("*_experiment.json"))
        
        if not experiment_files:
            raise FileNotFoundError(
                f"No experiment files found in {self.experiments_dir}\n"
                "Run 'make generate-experiments' first."
            )
        
        print(f"📂 Found {len(experiment_files)} experiment configurations")
        print()
        
        for exp_file in experiment_files:
            ticker = exp_file.stem.replace("_experiment", "")
            
            with open(exp_file, "r") as f:
                config = json.load(f)
            
            try:
                print("━" * 60)
                print(f"Processing: {ticker}")
                print("━" * 60)
                
                method = config["split"].get("method", "cpcv")
                
                if method == "cpcv":
                    cpcv_split(
                        ticker=ticker,
                        config=config["split"],
                        data_dir=self.data_dir,
                    )
                elif method == "rolling_horizon":
                    rolling_horizon_split(
                        ticker=ticker,
                        config=config["split"],
                        data_dir=self.data_dir,
                    )
                else:
                    raise ValueError(f"Unknown split method: {method}")
                
            except Exception as e:
                print(f"❌ Error processing {ticker}: {e}")
                continue
    
    def split_single(self, ticker: str) -> None:
        """
        特定ティッカーのデータ分割を実行する。
        
        Args:
            ticker: ティッカーシンボル
        """
        exp_file = self.experiments_dir / f"{ticker}_experiment.json"
        
        if not exp_file.exists():
            raise FileNotFoundError(
                f"Experiment file not found: {exp_file}\n"
                f"Run 'make generate-experiments' first."
            )
        
        with open(exp_file, "r") as f:
            config = json.load(f)
        
        method = config["split"].get("method", "cpcv")
        
        if method == "cpcv":
            cpcv_split(
                ticker=ticker,
                config=config["split"],
                data_dir=self.data_dir,
            )
        elif method == "rolling_horizon":
            rolling_horizon_split(
                ticker=ticker,
                config=config["split"],
                data_dir=self.data_dir,
            )
        else:
            raise ValueError(f"Unknown split method: {method}")
    
    def split_from_config(self, config_path: str) -> None:
        """
        実験設定ファイルから直接データ分割を実行する。
        
        Args:
            config_path: 実験設定ファイルのパス
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        ticker = config.get("ticker")
        if not ticker:
            raise ValueError(f"'ticker' field not found in config: {config_path}")
        
        method = config["split"].get("method", "cpcv")
        
        if method == "cpcv":
            cpcv_split(
                ticker=ticker,
                config=config["split"],
                data_dir=self.data_dir,
            )
        elif method == "rolling_horizon":
            rolling_horizon_split(
                ticker=ticker,
                config=config["split"],
                data_dir=self.data_dir,
            )
        else:
            raise ValueError(f"Unknown split method: {method}")


def main():
    """
    CLI エントリーポイント
    
    Usage:
        python -m src.core.data_splitter --ticker AAPL
        python -m src.core.data_splitter --all
        python -m src.core.data_splitter --config data/experiments/AAPL_experiment.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Split stock data using Rolling Horizon")
    parser.add_argument("--ticker", type=str, help="Ticker symbol (e.g., AAPL)")
    parser.add_argument("--all", action="store_true", help="Split all tickers")
    parser.add_argument("--config", type=str, help="Path to experiment config file")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    
    args = parser.parse_args()
    
    splitter = DataSplitter(data_dir=args.data_dir)
    
    if args.config:
        # ★ 追加: --config 引数のサポート
        splitter.split_from_config(args.config)
    elif args.all:
        splitter.split_all()
    elif args.ticker:
        splitter.split_single(args.ticker)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
