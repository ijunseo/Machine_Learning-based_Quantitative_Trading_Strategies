"""株価データ可視化モジュール.

CPCV分割結果を可視化し、各foldのtrain/test期間とTriple-Barrierラベルを
色分けしたローソク足チャートを生成します。

典型的な使用例:
    $ python src/get_data/visualizer.py --ticker AAPL
"""

import argparse
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import plotly.graph_objects as go

# --- プロジェクトのパス設定 ---
BASE_PATH = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_PATH / "data" / "processed"
SPLITS_PATH = BASE_PATH / "data" / "splits"
CHARTS_PATH = BASE_PATH / "data" / "charts"


def load_split_data(ticker: str) -> List[Tuple[pd.DataFrame, pd.DataFrame, int]]:
    """CPCV分割データを読み込む.

    Args:
        ticker: ティッカーシンボル

    Returns:
        List of (train_df, test_df, fold_idx) tuples
    """
    splits_dir = SPLITS_PATH / ticker
    if not splits_dir.exists():
        return []

    fold_data = []
    fold_files = sorted(splits_dir.glob("fold_*_train.csv"))

    for train_file in fold_files:
        fold_idx = int(train_file.stem.split("_")[1])
        test_file = splits_dir / f"fold_{fold_idx}_test.csv"

        if test_file.exists():
            train_df = pd.read_csv(train_file, parse_dates=["Date"], index_col="Date")
            test_df = pd.read_csv(test_file, parse_dates=["Date"], index_col="Date")
            fold_data.append((train_df, test_df, fold_idx))

    return fold_data


def visualize_stock_data(ticker: str) -> None:
    """指定されたティッカーのCPCV分割結果を可視化する.

    Args:
        ticker: ティッカーシンボル（例: "AAPL"）.
    """
    csv_file = DATA_PATH / f"{ticker}_features_labeled.csv"

    # --- データファイルの存在確認 ---
    if not csv_file.exists():
        print(f"❌エラー： '{csv_file}' が見つかりません。")
        print("まず 'make full-pipeline' を実行して、ラベル付きデータを生成してください。")
        return

    print(f"📂 '{csv_file}' からデータを読み込んでいます...")
    df = pd.read_csv(csv_file, parse_dates=["Date"], index_col="Date")

    # --- CPCV分割データを読み込む ---
    fold_data = load_split_data(ticker)

    if not fold_data:
        print(f"⚠️  警告: CPCV分割データが見つかりません (data/splits/{ticker}/)")
        print("通常のラベル付きチャートのみを生成します...")
        fold_data = []
    else:
        # CPCV分割データの範囲でフィルタリング
        all_train_test_dates = []
        for train_df, test_df, _ in fold_data:
            all_train_test_dates.extend(train_df.index.tolist())
            all_train_test_dates.extend(test_df.index.tolist())

        if all_train_test_dates:
            min_date = min(all_train_test_dates)
            max_date = max(all_train_test_dates)
            df = df.loc[min_date:max_date]
            print(f"📅 CPCV期間でフィルタリング: {min_date.date()} ~ {max_date.date()}")

    # --- 20日移動平均線の計算 ---
    df["MA20"] = df["Close"].rolling(window=20).mean()

    print(f"📊 '{ticker}' のCPCV分割可視化チャートを生成しています...")

    # --- Plotlyローソク足チャートの生成 ---
    fig = go.Figure()

    # 1. ローソク足チャート（全体）
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="価格",
            showlegend=True,
        )
    )

    # 2. CPCV分割の可視化
    colors = [
        "rgba(0, 123, 255, 0.15)",
        "rgba(40, 167, 69, 0.15)",
        "rgba(255, 193, 7, 0.15)",
        "rgba(220, 53, 69, 0.15)",
        "rgba(108, 117, 125, 0.15)",
        "rgba(23, 162, 184, 0.15)",
        "rgba(111, 66, 193, 0.15)",
    ]

    for idx, (train_df, test_df, fold_idx) in enumerate(fold_data):
        color = colors[fold_idx % len(colors)]

        # Train期間を塗りつぶし
        fig.add_vrect(
            x0=train_df.index.min(),
            x1=train_df.index.max(),
            fillcolor=color.replace("0.15", "0.08"),
            layer="below",
            line_width=0,
            annotation_text=f"Fold {fold_idx} Train",
            annotation_position="top left",
            annotation_font_size=10,
        )

        # Test期間を強調
        fig.add_vrect(
            x0=test_df.index.min(),
            x1=test_df.index.max(),
            fillcolor=color.replace("0.15", "0.25"),
            layer="below",
            line_width=2,
            line_color=color.replace("0.15", "0.8"),
            annotation_text=f"Fold {fold_idx} Test",
            annotation_position="top left",
            annotation_font_size=10,
            annotation_font_color="red",
        )

    # 3. ラベル別のマーカーを追加（NaN以外のみ）
    if "Label" in df.columns:
        df_labeled = df[df["Label"].notna()].copy()

        # Long (Label = 1)
        long_data = df_labeled[df_labeled["Label"] == 1.0]
        if not long_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=long_data.index,
                    y=long_data["Close"],
                    mode="markers",
                    name="Long (1)",
                    marker=dict(
                        symbol="triangle-up",
                        size=8,
                        color="green",
                        line=dict(width=1, color="darkgreen"),
                    ),
                    hovertemplate="<b>Long</b><br>日付: %{x}<br>価格: $%{y:.2f}<extra></extra>",
                )
            )

        # Short (Label = -1)
        short_data = df_labeled[df_labeled["Label"] == -1.0]
        if not short_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=short_data.index,
                    y=short_data["Close"],
                    mode="markers",
                    name="Short (-1)",
                    marker=dict(
                        symbol="triangle-down",
                        size=8,
                        color="red",
                        line=dict(width=1, color="darkred"),
                    ),
                    hovertemplate="<b>Short</b><br>日付: %{x}<br>価格: $%{y:.2f}<extra></extra>",
                )
            )

        # Neutral (Label = 0)
        neutral_data = df_labeled[df_labeled["Label"] == 0.0]
        if not neutral_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=neutral_data.index,
                    y=neutral_data["Close"],
                    mode="markers",
                    name="Neutral (0)",
                    marker=dict(
                        symbol="circle",
                        size=6,
                        color="gray",
                        line=dict(width=1, color="darkgray"),
                    ),
                    hovertemplate="<b>Neutral</b><br>日付: %{x}<br>価格: $%{y:.2f}<extra></extra>",
                )
            )

    # 4. 20日移動平均線(SMA)の追加
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MA20"],
            mode="lines",
            name="MA20",
            line={"color": "orange", "width": 1.5, "dash": "dash"},
            opacity=0.7,
        )
    )

    # --- 統計情報を追加 ---
    label_counts = df["Label"].value_counts()
    stats_text = f"総サンプル: {len(df)} | "
    stats_text += f"Long: {label_counts.get(1.0, 0)} | "
    stats_text += f"Short: {label_counts.get(-1.0, 0)} | "
    stats_text += f"Neutral: {label_counts.get(0.0, 0)} | "
    stats_text += f"保有中: {df['Label'].isna().sum()}"

    if fold_data:
        stats_text += f" | Folds: {len(fold_data)}"

    # --- チャートレイアウトの設定 ---
    fig.update_layout(
        title=f"{ticker} CPCV分割 & Triple-Barrier ラベリング結果<br>"
        f"<sub>{stats_text}</sub><br>"
        f"<sub>🟢 Long | 🔴 Short | ⚪ Neutral | 色付き背景: Train/Test期間</sub>",
        yaxis_title="株価 (USD)",
        xaxis_title="日付",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        height=700,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    # --- チャートの保存 ---
    CHARTS_PATH.mkdir(exist_ok=True, parents=True)
    output_path = CHARTS_PATH / f"{ticker}_cpcv_chart.html"

    fig.write_html(output_path)
    print(f"✅ CPCV可視化チャートを '{output_path}' に保存しました。")
    print("📈 ファイルを開いてインタラクティブなチャートを確認してください。")


def main() -> None:
    """CLIエントリーポイント."""
    parser = argparse.ArgumentParser(
        description="指定されたティッカーのラベル付き株価データを可視化します。"
    )
    parser.add_argument(
        "--ticker", type=str, required=True, help="可視化する株式のティッカーシンボル (例: TSLA)"
    )
    args = parser.parse_args()

    visualize_stock_data(args.ticker)


if __name__ == "__main__":
    main()
