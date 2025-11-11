"""Triple-Barrier Labeling モジュール.

金融時系列データに対してTriple-Barrier方式でラベル付けを行います。

Triple-Barrierの仕組み:
    - Upper Barrier: 利益確定ライン（例: +3%）
    - Lower Barrier: 損切りライン（例: -2%）
    - Time Barrier: 最大保有期間（例: 5日）
    
    最初にいずれかのバリアに到達した時点でラベル確定:
        - Upper到達 → Label = 1 (Long推奨)
        - Lower到達 → Label = -1 (Short推奨)
        - Time到達  → Label = 0 (Neutral) または現在のリターンの符号

典型的な使用例:
    $ python src/core/triple_barrier_labeler.py \\
        --config data/experiments/TSLA_experiment.yaml
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


def load_config(config_path: str) -> Dict[str, Any]:
    """実験設定ファイル(JSON or YAML)を読み込む.

    Args:
        config_path: 実験設定ファイルのパス.

    Returns:
        設定内容の辞書.
    """
    path = Path(config_path)

    if path.suffix == ".json":
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # YAMLの場合
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


def triple_barrier_label(
    df: pd.DataFrame,
    upper_return: float = 0.03,
    lower_return: float = -0.02,
    max_holding_days: int = 5,
    reference_column: str = "Close",
    include_neutral: bool = True,
) -> pd.Series:
    """Triple-Barrier方式でラベルを生成.

    各時点でエントリーした場合、最初にバリアに到達した方向でラベル確定。

    Args:
        df: 価格データを含むDataFrame.
        upper_return: 上限バリア（利益確定）の閾値（例: 0.03 = +3%）.
        lower_return: 下限バリア（損切り）の閾値（例: -0.02 = -2%）.
        max_holding_days: 最大保有日数（時間バリア）.
        reference_column: 価格参照列名（通常は"Close"）.
        include_neutral: Trueの場合、時間切れ時にLabel=0を返す.

    Returns:
        ラベルのSeries（1: Long, -1: Short, 0: Neutral）.
    """
    labels = []
    prices = df[reference_column].values

    # 未来データが不足する最後の期間は除外
    for i in range(len(df) - max_holding_days):
        entry_price = prices[i]
        upper_barrier = entry_price * (1 + upper_return)
        lower_barrier = entry_price * (1 + lower_return)

        # 未来の価格を確認
        future_prices = prices[i + 1 : i + 1 + max_holding_days]

        # バリア到達判定
        upper_hit_idx = np.where(future_prices >= upper_barrier)[0]
        lower_hit_idx = np.where(future_prices <= lower_barrier)[0]

        if len(upper_hit_idx) > 0 and len(lower_hit_idx) > 0:
            # 両方に到達した場合、早い方を採用
            if upper_hit_idx[0] < lower_hit_idx[0]:
                labels.append(1)
            else:
                labels.append(-1)
        elif len(upper_hit_idx) > 0:
            # 上限バリアのみ到達
            labels.append(1)
        elif len(lower_hit_idx) > 0:
            # 下限バリアのみ到達
            labels.append(-1)
        else:
            # どちらにも到達せず（時間切れ）
            if include_neutral:
                labels.append(0)
            else:
                # ニュートラルなしの場合、最終リターンの符号
                final_return = (future_prices[-1] / entry_price) - 1
                labels.append(int(np.sign(final_return)))

    # 残りの期間はNaNで埋める
    labels.extend([np.nan] * max_holding_days)

    return pd.Series(labels, index=df.index, name="Label")


def apply_labeling(input_path: str, output_path: str, config: Dict[str, Any]) -> None:
    """
    指定されたCSVファイルにTriple-Barrierラベリングを適用し、結果を保存する。
    """
    print(f"   📂 Parquetを読み込み中: {input_path}")
    df = pd.read_parquet(input_path)

    # 日付列の処理
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date").reset_index(drop=True)

    # ラベル生成
    labels = triple_barrier_label(
        df=df,
        upper_return=config["upper_return"],
        lower_return=config["lower_return"],
        max_holding_days=config["max_holding_days"],
        reference_column=config["reference_column"],
        include_neutral=config["include_neutral"],
    )

    # ラベル列を追加
    label_column = config.get("label_column", "Label")
    df[label_column] = labels

    # 保存
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    # 統計情報を表示
    label_counts = df[label_column].value_counts().sort_index()
    print("\n📊 ラベル分布:")
    print(f"   Long (1):    {label_counts.get(1.0, 0):>6} サンプル")
    print(f"   Short (-1):  {label_counts.get(-1.0, 0):>6} サンプル")
    print(f"   Neutral (0): {label_counts.get(0.0, 0):>6} サンプル")
    print(f"   NaN:         {df[label_column].isna().sum():>6} サンプル")


def main() -> None:
    """CLIエントリーポイント."""
    parser = argparse.ArgumentParser(
        description="Triple-Barrier Labelingを実行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="実験設定ファイルのパス（例: data/experiments/TSLA_experiment.json）",
    )

    args = parser.parse_args()

    # 設定読み込み
    config = load_config(args.config)
    ticker = config.get("ticker", "UNKNOWN")
    labeling_config = config["labeling"]

    if not labeling_config.get("enabled", True):
        print(f"⚠️  {ticker} のラベリングは無効です")
        return

    print(f"🏷️  Triple-Barrier Labeling: {ticker}")
    print(f"   上限: +{labeling_config['upper_return'] * 100:.1f}%")
    print(f"   下限: {labeling_config['lower_return'] * 100:.1f}%")
    print(f"   最大保有日数: {labeling_config['max_holding_days']}")

    # 入力パスの生成 (raw parquet)
    input_path = labeling_config.get("input_data", "data/raw/{ticker}.parquet").format(
        ticker=ticker
    )

    # 出力パスの生成
    output_path = labeling_config["output_data"].format(ticker=ticker)

    # ラベル付け実行
    apply_labeling(input_path, output_path, labeling_config)
    print(f"\n✅ ラベル保存完了: {output_path}")


if __name__ == "__main__":
    main()
