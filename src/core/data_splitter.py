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
from typing import Any, Dict, List, Optional

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
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def rolling_horizon_split(
    df: pd.DataFrame,
    batch_unit: int = 200,
    horizon: int = 5,
    latest_first: bool = True,
    save_dir: Optional[str] = None,
    date_column: str = "Date",
    stats_columns: Optional[List[str]] = None,
) -> List[Dict[str, pd.DataFrame]]:
    """Rolling Horizon方式でデータを分割.

    Args:
        df: 分割対象のDataFrame.
        batch_unit: 各訓練バッチのサンプル数.
        horizon: 各テストバッチのサンプル数.
        latest_first: 最新データから遡るか.
        save_dir: 保存先ディレクトリ.
        date_column: 日付列の名前.
        stats_columns: 統計を計算する列名のリスト.

    Returns:
        分割結果の辞書のリスト.
    """
    total_samples = len(df)
    folds = []
    fold_num = 1

    if latest_first:
        # 最新から遡る
        end_idx = total_samples
        while end_idx >= batch_unit + horizon:
            start_idx = end_idx - batch_unit

            train_data = df.iloc[start_idx:end_idx]
            test_data = df.iloc[end_idx : end_idx + horizon]

            folds.append({"train": train_data, "test": test_data, "fold": fold_num})

            # Fold詳細ログを削除
            fold_num += 1
            end_idx -= horizon
    else:
        # 古いデータから進む
        start_idx = 0
        while start_idx + batch_unit + horizon <= total_samples:
            end_idx = start_idx + batch_unit

            train_data = df.iloc[start_idx:end_idx]
            test_data = df.iloc[end_idx : end_idx + horizon]

            folds.append({"train": train_data, "test": test_data, "fold": fold_num})

            # Fold詳細ログを削除
            fold_num += 1
            start_idx += horizon

    # 成功した総Fold数を表示
    print(f"\n✅ Successfully created {len(folds)} folds")
    print(f"   Train size per fold: {batch_unit}")
    print(f"   Test size per fold: {horizon}")

    # 保存処理
    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        for fold in folds:
            fold_dir = save_dir / f"fold_{fold['fold']}"
            fold_dir.mkdir(parents=True, exist_ok=True)

            # CSV保存
            fold["train"].to_csv(fold_dir / "train.csv", index=False)
            fold["test"].to_csv(fold_dir / "test.csv", index=False)

            # 統計情報
            train_stats = compute_stats(fold["train"], stats_columns)
            test_stats = compute_stats(fold["test"], stats_columns)

            stats = {"fold": fold["fold"], "train": train_stats, "test": test_stats}

            with open(fold_dir / "stats.json", "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

    return folds


def compute_stats(df: pd.DataFrame, stats_columns: list) -> Dict[str, Any]:
    """データの統計情報を計算.

    Args:
        df: 統計を計算するDataFrame.
        stats_columns: 統計を計算する列名のリスト.

    Returns:
        統計情報の辞書.
    """
    stats = {"n_samples": len(df)}

    # 日付情報
    if "Date" in df.columns:
        stats["start_date"] = df["Date"].min().strftime("%Y-%m-%d")
        stats["end_date"] = df["Date"].max().strftime("%Y-%m-%d")

    # 数値列の統計
    for col in stats_columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            stats[f"{col}_mean"] = float(df[col].mean())
            stats[f"{col}_std"] = float(df[col].std())
            stats[f"{col}_min"] = float(df[col].min())
            stats[f"{col}_max"] = float(df[col].max())

            # Sharpe-like指標（Returnsがある場合）
            if col == "Returns" and df[col].std() != 0:
                stats["sharpe_like"] = float(df[col].mean() / df[col].std() * np.sqrt(252))

    return stats


def print_fold_info(fold_idx: int, train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """Fold情報をコンソールに出力.

    Args:
        fold_idx: Foldのインデックス.
        train_df: 訓練データ.
        test_df: テストデータ.
    """
    if "Date" in train_df.columns:
        train_start = train_df["Date"].min().strftime("%Y-%m-%d")
        train_end = train_df["Date"].max().strftime("%Y-%m-%d")
        test_start = test_df["Date"].min().strftime("%Y-%m-%d")
        test_end = test_df["Date"].max().strftime("%Y-%m-%d")

        print(f"[Fold {fold_idx}] Train: {train_start} ~ {train_end} (N={len(train_df)})")
        print(f"[Fold {fold_idx}] Test:  {test_start} ~ {test_end} (N={len(test_df)})")
    else:
        print(f"[Fold {fold_idx}] Train: N={len(train_df)}")
        print(f"[Fold {fold_idx}] Test:  N={len(test_df)}")


def run_split(config: Dict[str, Any]) -> None:
    """分割処理を実行."""
    ticker = config["ticker"]
    split_config = config["split"]

    # データ読み込み
    input_path = split_config["input_data"]
    print(f"📂 Loading data: {input_path}")
    df = pd.read_csv(input_path)

    # 日付列の処理
    date_column = split_config.get("date_column", "Date")
    if date_column in df.columns:
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.sort_values(date_column).reset_index(drop=True)

    print(f"\n{'=' * 60}")
    print(f"Rolling Horizon Split: {ticker}")
    print(f"  Batch Unit: {split_config['batch_unit']}")
    print(f"  Horizon: {split_config['horizon']}")
    print(f"  Latest First: {split_config.get('latest_first', True)}")
    print(f"{'=' * 60}\n")

    # 分割実行 (dfを渡す)
    _ = rolling_horizon_split(
        df=df,  # ← これが必要
        batch_unit=split_config["batch_unit"],
        horizon=split_config["horizon"],
        latest_first=split_config.get("latest_first", True),
        save_dir=split_config["save_dir"],
        date_column=date_column,
        stats_columns=split_config.get("stats_columns", ["Returns", "Close"]),
    )

    print(f"\n✅ All splits saved to: {split_config['save_dir']}")


def main() -> None:
    """CLIエントリーポイント."""
    parser = argparse.ArgumentParser(
        description="Rolling Horizon データ分割を実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="実験設定YAMLファイルのパス（例: data/experiments/TSLA_experiment.yaml）",
    )

    args = parser.parse_args()

    # 設定読み込み
    config = load_config(args.config)

    # 分割実行
    run_split(config)


if __name__ == "__main__":
    main()
