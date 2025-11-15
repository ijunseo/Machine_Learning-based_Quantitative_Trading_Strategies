# src/get_data/visualizer.py

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# --- プロジェクトのパス設定 ---
# このファイルの場所を基準にプロジェクトのルートディレクトリを探します。
BASE_PATH = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_PATH / "data"
CHARTS_PATH = BASE_PATH / "charts"


def visualize_stock_data(ticker: str):
    """
    指定されたティッカーのParquetデータを読み込み、ローソク足チャートを生成してHTMLファイルとして保存します。
    """
    parquet_file = DATA_PATH / f"{ticker}.parquet"

    # --- データファイルの存在確認 ---
    if not parquet_file.exists():
        print(f"❌エラー： '{parquet_file}' が見つかりません。")
        print("まず 'make fetch' を実行して、データをダウンロードしてください。")
        return

    print(f"'{parquet_file}' からデータを読み込んでいます...")
    df = pd.read_parquet(parquet_file)

    # --- 20日移動平均線の計算 ---
    df["MA20"] = df["Close"].rolling(window=20).mean()

    print(f"'{ticker}' の株価チャートを生成しています...")

    # --- Plotlyローソク足チャートの生成 ---
    fig = go.Figure()

    # 1. ローソク足チャートの追加
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="価格",
        )
    )

    # 2. 20日移動平均線(SMA)の追加
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MA20"],
            mode="lines",
            name="20日移動平均",
            line={"color": "orange", "width": 1},
        )
    )

    # --- チャートレイアウトの設定 ---
    fig.update_layout(
        title=f"{ticker} 株価チャート",
        yaxis_title="株価 (USD)",
        xaxis_title="日付",
        xaxis_rangeslider_visible=False,  # レンジスライダーを非表示にする
    )

    # --- チャートの保存 ---
    CHARTS_PATH.mkdir(exist_ok=True)
    output_path = CHARTS_PATH / f"{ticker}_chart.html"

    fig.write_html(output_path)
    print(f"✅ チャートを '{output_path}' に保存しました。")
    print("ファイルを開いてインタラクティブなチャートを確認してください。")


def main():
    # --- CLI引数パーサーの設定 ---
    parser = argparse.ArgumentParser(description="指定されたティッカーの株価データを可視化します。")
    parser.add_argument(
        "--ticker", type=str, required=True, help="可視化する株式のティッカーシンボル (例: TSLA)"
    )
    args = parser.parse_args()

    visualize_stock_data(args.ticker)


if __name__ == "__main__":
    main()
