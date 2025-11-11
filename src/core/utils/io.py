"""
I/Oユーティリティモジュール

設定ファイルの読み込み、データの保存/読み込みなどの共通処理を提供します。
"""

from pathlib import Path
from typing import Any, Dict

import json
import pandas as pd
import yaml


def load_config(config_path: str | Path) -> Dict[str, Any]:
    """設定ファイル（YAML/JSON）を読み込む。

    Args:
        config_path: 設定ファイルのパス。

    Returns:
        設定内容の辞書。

    Raises:
        ValueError: サポートされていないファイル形式の場合。
        FileNotFoundError: ファイルが存在しない場合。

    Examples:
        >>> config = load_config("src/config_universe.yaml")
        >>> print(config["tickers"])
        ['AAPL', 'TSLA', ...]
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")

    if config_path.suffix in [".yaml", ".yml"]:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif config_path.suffix == ".json":
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError(f"サポートされていないファイル形式: {config_path.suffix}")


def save_json(data: Dict[str, Any], output_path: str | Path) -> None:
    """データをJSON形式で保存する。

    Args:
        data: 保存するデータ。
        output_path: 出力先パス。

    Examples:
        >>> save_json({"ticker": "TSLA", "params": {...}}, "data/config.json")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_parquet(file_path: str | Path) -> pd.DataFrame:
    """Parquetファイルを読み込む。

    Args:
        file_path: Parquetファイルのパス。

    Returns:
        読み込んだDataFrame。

    Raises:
        FileNotFoundError: ファイルが存在しない場合。

    Examples:
        >>> df = load_parquet("data/raw/TSLA.parquet")
        >>> print(df.head())
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    return pd.read_parquet(file_path)


def save_csv(df: pd.DataFrame, output_path: str | Path) -> None:
    """DataFrameをCSV形式で保存する。

    Args:
        df: 保存するDataFrame。
        output_path: 出力先パス。

    Examples:
        >>> save_csv(labeled_df, "data/processed/TSLA_labeled.csv")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
