"""株価データ取得モジュール.

yfinanceを使用してティッカーの株価データを取得し、Parquet形式で保存します。

典型的な使用例:
    $ python src/get_data/fetcher.py
"""

from pathlib import Path
from typing import Any, Dict, List

import yaml
import yfinance as yf

# プロジェクトのルートディレクトリを基準にパスを設定
# CONFIG_PATH が src/config_universe.yaml に変更
CONFIG_PATH = Path(__file__).resolve().parents[2] / "src" / "config_universe.yaml"
DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "raw"


def load_config() -> Dict[str, Any]:
    """config_universe.yaml ファイルを読み込んで設定を返す.

    Returns:
        設定内容の辞書.

    Raises:
        FileNotFoundError: 設定ファイルが存在しない場合.
    """
    print(f"設定ファイルを読み込んでいます: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    print("設定ファイルの読み込みが完了しました。")
    return config


def fetch_and_save_all() -> None:
    """設定ファイルに基づいて全ティッカーの株価データを取得し、Parquet形式で保存する.

    config_universe.yamlからティッカーリスト、開始日、インターバルを読み込み、
    各ティッカーのデータをyfinanceで取得してdata/raw/に保存します。
    """
    config = load_config()
    tickers: List[str] = config.get("tickers", [])
    start_date: str = config.get("start", "2020-01-01")
    interval: str = config.get("interval", "1d")
    auto_adjust: bool = config.get("auto_adjust", False)

    if not tickers:
        print("エラー：config_universe.yamlにティッカーが指定されていません。")
        return

    # データ保存ディレクトリを作成
    DATA_PATH.mkdir(parents=True, exist_ok=True)
    print(f"データ保存先：'{DATA_PATH}'")

    for ticker in tickers:
        try:
            print(f"\n--- {ticker}のデータを取得中... (期間: {start_date}〜, 間隔: {interval}) ---")

            # yfinanceを使ってデータをダウンロード
            data = yf.download(
                ticker,
                start=start_date,
                interval=interval,
                auto_adjust=auto_adjust,
                progress=False
            )

            if data.empty:
                print(
                    f"警告：{ticker}のデータが見つかりませんでした。"
                    f"ティッカーが正しいか確認してください。"
                )
                continue

            # ファイルパスを定義
            output_path = DATA_PATH / f"{ticker}.parquet"

            # Parquet形式で保存
            data.to_parquet(output_path)
            print(f"✅ {ticker}のデータを'{output_path}'に保存しました。")
            print(f"   サンプル数: {len(data)}, 期間: {data.index[0]} ~ {data.index[-1]}")

        except Exception as e:
            print(f"エラー：{ticker}のデータ取得中に問題が発生しました：{e}")

    print("\n" + "="*60)
    print("すべてのデータ取得処理が完了しました。")
    print("="*60)


if __name__ == "__main__":
    fetch_and_save_all()
