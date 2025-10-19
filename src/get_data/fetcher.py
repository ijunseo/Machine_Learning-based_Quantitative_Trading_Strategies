# src/get_data/fetcher.py

import yfinance as yf
import yaml
from pathlib import Path
import pandas as pd

# プロジェクトのルートディレクトリを基準にパスを設定
# --- Set path based on the project root directory ---
CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"
DATA_PATH = Path(__file__).resolve().parents[2] / "data"

def load_config():
    """
    config.yaml ファイルを読み込んで設定を返す
    ---
    Loads and returns settings from config.yaml.
    """
    print("設定ファイルを読み込んでいます...")
    # --- Loading configuration file... ---
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    print("設定ファイルの読み込みが完了しました。")
    # --- Configuration file loaded successfully. ---
    return config

def fetch_and_save_all():
    """
    設定ファイルに基づいて全ティッカーの株価データを取得し、Parquet形式で保存する
    ---
    Fetches stock data for all tickers based on the config file and saves it in Parquet format.
    """
    config = load_config()
    tickers = config.get("tickers", [])
    start_date = config.get("start", "2020-01-01")
    interval = config.get("interval", "1d")

    if not tickers:
        print("エラー：config.yamlにティッカーが指定されていません。")
        # --- Error: No tickers specified in config.yaml. ---
        return

    # データ保存ディレクトリを作成
    # --- Create data storage directory ---
    DATA_PATH.mkdir(exist_ok=True)
    print(f"データ保存先：'{DATA_PATH}'")
    # --- Data will be saved to: '{DATA_PATH}' ---

    for ticker in tickers:
        try:
            print(f"--- {ticker}のデータを取得中... (期間: {start_date}〜, 間隔: {interval}) ---")
            # --- Fetching data for {ticker}... (Period: {start_date} to present, Interval: {interval}) ---
            
            # yfinanceを使ってデータをダウンロード
            # --- Download data using yfinance ---
            data = yf.download(ticker, start=start_date, interval=interval, progress=False)

            if data.empty:
                print(f"警告：{ticker}のデータが見つかりませんでした。ティッカーが正しいか確認してください。")
                # --- Warning: No data found for {ticker}. Please check if the ticker is correct. ---
                continue
            
            # ファイルパスを定義
            # --- Define file path ---
            output_path = DATA_PATH / f"{ticker}.parquet"
            
            # Parquet形式で保存
            # --- Save in Parquet format ---
            data.to_parquet(output_path)
            print(f"✅ {ticker}のデータを'{output_path}'に保存しました。")
            # --- ✅ Saved data for {ticker} to '{output_path}'. ---

        except Exception as e:
            print(f"エラー：{ticker}のデータ取得中に問題が発生しました：{e}")
            # --- Error: An issue occurred while fetching data for {ticker}: {e} ---

    print("\nすべてのデータ取得処理が完了しました。")
    # --- All data fetching processes are complete. ---

if __name__ == "__main__":
    fetch_and_save_all()
