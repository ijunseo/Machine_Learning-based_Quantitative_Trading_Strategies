"""ティッカー別実験設定JSON自動生成モジュール.

このモジュールは、config_universe.yamlに定義されたティッカーリストを元に、
各ティッカー専用の実験設定JSONファイルを自動生成します。

典型的な使用例:
    $ python src/core/generate_ticker_yaml.py \\
        --config src/config_universe.yaml \\
        --template src/data_split_labeling.yaml \\
        --output-dir data/experiments/
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import yaml

# インポートパスの更新
from src.core.labeling.triple_barrier_labeler import TripleBarrierLabeler  # 変更箇所


def load_yaml(filepath: str) -> Dict[str, Any]:
    """YAMLファイルを読み込む.

    Args:
        filepath: YAMLファイルのパス.

    Returns:
        YAMLファイルの内容を辞書として返す.

    Raises:
        FileNotFoundError: ファイルが存在しない場合.
        yaml.YAMLError: YAML構文エラーの場合.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_json(data: Dict[str, Any], filepath: str) -> None:
    """辞書をJSONファイルとして保存.

    Args:
        data: 保存するデータ（辞書形式）.
        filepath: 出力先ファイルパス.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_ticker_config(
    ticker: str, template: Dict[str, Any], base_data_dir: str = "data"
) -> Dict[str, Any]:
    """ティッカー専用の実験設定を生成.

    テンプレート設定を元に、ティッカー固有のパス情報を埋め込んだ
    実験設定辞書を作成します。

    Args:
        ticker: ティッカーシンボル（例: "TSLA"）.
        template: data_split_labeling.yamlから読み込んだテンプレート.
        base_data_dir: データディレクトリのベースパス.

    Returns:
        ティッカー専用の実験設定辞書.
    """
    # テンプレートのパスを取得して {ticker} を置換
    labeling_input = template["labeling"].get("input_data", "data/raw/{ticker}.parquet")
    labeling_output = template["labeling"].get(
        "output_data", "data/processed/{ticker}_features_labeled.csv"
    )
    split_input = template["split"].get(
        "input_data", "data/processed/{ticker}_features_labeled.csv"
    )

    config = {
        "ticker": ticker,
        "split": {
            **template["split"],
            "save_dir": f"{base_data_dir}/splits/{ticker}",
            "input_data": split_input.format(ticker=ticker),
            "date_column": "Date",
            "stats_columns": ["Returns", "Close"],
        },
        "labeling": {
            **template["labeling"],
            "input_data": labeling_input.format(ticker=ticker),
            "output_data": labeling_output.format(ticker=ticker),
        },
    }
    return config


def generate_all_ticker_configs(config_path: str, template_path: str, output_dir: str) -> List[str]:
    """全ティッカーの実験設定JSONを一括生成.

    Args:
        config_path: config_universe.yamlのパス.
        template_path: data_split_labeling.yamlのパス.
        output_dir: 出力先ディレクトリ.

    Returns:
        生成されたファイルパスのリスト.
    """
    # 設定読み込み
    universe = load_yaml(config_path)
    template = load_yaml(template_path)

    # 出力ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # 各ティッカーに対して処理
    for ticker in universe["tickers"]:
        # ティッカー専用設定を生成
        config = generate_ticker_config(
            ticker=ticker, template=template, base_data_dir=universe.get("data_dir", "data")
        )

        # JSONファイルとして保存
        output_file = output_path / f"{ticker}_experiment.json"
        save_json(config, str(output_file))
        generated_files.append(str(output_file))

        print(f"✅ Generated: {output_file}")

    return generated_files


def main() -> None:
    """CLIエントリーポイント."""
    parser = argparse.ArgumentParser(
        description="ティッカー別実験設定JSONを自動生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", type=str, default="src/config_universe.yaml", help="config_universe.yamlのパス"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="src/data_split_labeling.yaml",
        help="data_split_labeling.yamlのパス",
    )
    parser.add_argument(
        "--output-dir", type=str, default="data/experiments", help="出力先ディレクトリ"
    )

    args = parser.parse_args()

    print("📝 Generating experiment configs...")
    print(f"   Config: {args.config}")
    print(f"   Template: {args.template}")
    print(f"   Output: {args.output_dir}")
    print()

    generated_files = generate_all_ticker_configs(
        config_path=args.config, template_path=args.template, output_dir=args.output_dir
    )

    print()
    print(f"🎉 Successfully generated {len(generated_files)} experiment configs!")


if __name__ == "__main__":
    main()
