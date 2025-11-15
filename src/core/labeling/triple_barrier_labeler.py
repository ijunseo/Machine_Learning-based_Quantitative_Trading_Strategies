"""
Triple-Barrier Labeling

株価データに対するTriple-Barrier法によるラベリング。
ポジションの重複を避けるため、max_holding_days間隔でラベルを生成。
"""

import sys
import numpy as np
import pandas as pd

# UTF-8出力を強制
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')


class TripleBarrierLabeler:
    """
    Triple-Barrier法によるラベリングクラス
    
    重複しないラベル生成のため、以下のロジックを実装:
    1. N日目にポジション進入 → Label生成
    2. N+1 ~ N+max_holding_days: Label = NaN (保有中)
    3. N+max_holding_days+1日目: 次のポジション進入可能
    """

    def __init__(
        self,
        upper_return: float = 0.03,
        lower_return: float = -0.02,
        max_holding_days: int = 5,
        reference_column: str = "Close",
        label_column: str = "Label",
        include_neutral: bool = True,
    ):
        """
        Triple-Barrier Labelerを初期化する。

        Args:
            upper_return: 利益確定閾値 (例: 0.03 = +3%)
            lower_return: 損切り閾値 (例: -0.02 = -2%)
            max_holding_days: 最大保有日数
            reference_column: 基準となる価格列名
            label_column: 生成するラベル列名
            include_neutral: Neutral (0) ラベルを含むか
        """
        self.upper_return = upper_return
        self.lower_return = lower_return
        self.max_holding_days = max_holding_days
        self.reference_column = reference_column
        self.label_column = label_column
        self.include_neutral = include_neutral

    def _calculate_label_from_future(self, entry_price: float, future_prices: pd.Series) -> float:
        """
        エントリー時点の価格と未来の価格系列からラベルを計算する。
        
        Args:
            entry_price: t日目の終値 (エントリー価格)
            future_prices: t+1 ~ t+max_holding_days の価格系列

        Returns:
            1.0 (Long), -1.0 (Short), 0.0 (Neutral), or np.nan
        """
        if len(future_prices) < 1:
            return np.nan

        # NumPy配列に変換
        future_array = future_prices.values
        
        # 未来の各時点でリターンを計算
        for future_price in future_array:
            return_rate = (future_price - entry_price) / entry_price
            
            # Upper Barrier: 利益確定 → Long推奨
            if return_rate >= self.upper_return:
                return 1.0
            
            # Lower Barrier: 損切り → Short推奨
            if return_rate <= self.lower_return:
                return -1.0
        
        # Time Barrier: max_holding_days経過してもバリア未到達 → Neutral
        if self.include_neutral:
            return 0.0
        else:
            return np.nan

    def _calculate_single_label(self, prices: pd.Series) -> float:
        """
        単一ポジションのラベルを計算する（後方互換性のため残す）。

        Args:
            prices: max_holding_days+1 日分の価格シリーズ

        Returns:
            1.0 (Long), -1.0 (Short), 0.0 (Neutral), or np.nan
        """
        if len(prices) < 2:
            return np.nan

        # NumPy配列に変換してスカラー値として扱う
        prices_array = prices.values
        entry_price = prices_array[0]
        
        # entry_price を基準に future (prices[1:]) を評価
        future_prices = pd.Series(prices_array[1:])
        return self._calculate_label_from_future(entry_price, future_prices)

    def label_data(self, input_path: str, output_path: str) -> None:
        """
        株価データにTriple-Barrierラベリングを適用する。
        
        ★ 重要: t日目の特徴量で t+1 ~ t+max_holding_days の未来を予測
        
        ラベリングロジック:
        1. t日目の終値(Close)を基準として記録
        2. t+1 ~ t+max_holding_days の期間を評価
        3. 評価期間中に上限/下限バリアに到達 → ラベル確定
        4. 評価期間終了までバリア未到達 → Neutral (0)
        
        ポジション重複を避けるため、max_holding_days間隔でラベル生成

        Args:
            input_path: 入力Parquetファイルパス
            output_path: 出力CSVファイルパス
        """
        print(f"📂 Parquetを読み込み中: {input_path}")
        
        # Parquet読み込み (Dateがインデックス)
        df = pd.read_parquet(input_path)
        
        # MultiIndex列を平坦化 (もし存在する場合)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # インデックスをリセットしてDate列を作成
        df = df.reset_index()
        if 'index' in df.columns:
            df.rename(columns={'index': 'Date'}, inplace=True)
        
        # ラベル列を初期化 (全てNaN)
        df[self.label_column] = np.nan
        
        # ★ 修正: t日目の特徴で t+1 ~ t+max_holding_days の未来を予測
        labeled_count = 0
        i = 0
        while i < len(df) - self.max_holding_days:
            # t日目 (i) に進入 → t+1 ~ t+max_holding_days (i+1 ~ i+max_holding_days) を評価
            entry_price = df[self.reference_column].iloc[i]
            future_window = df[self.reference_column].iloc[i+1:i + self.max_holding_days + 1]
            
            # 未来の価格変動を評価してラベル生成
            label = self._calculate_label_from_future(entry_price, future_window)
            df.iloc[i, df.columns.get_loc(self.label_column)] = label
            
            # ★ 重要: 次のラベルは max_holding_days 後
            i += self.max_holding_days
            labeled_count += 1
            
            # 進捗表示 (50サンプルごと)
            if labeled_count % 50 == 0:
                print(f"  処理中... {labeled_count} サンプル完了")
            df.iloc[i, df.columns.get_loc(self.label_column)] = label
        
        # ラベル分布を表示
        label_counts = df[self.label_column].value_counts()
        nan_count = df[self.label_column].isna().sum()

        print()
        print("=" * 60)
        print("Label Distribution:")
        print("=" * 60)
        if 1.0 in label_counts.index:
            print(f"  Long (1):       {int(label_counts[1.0]):>5} samples")
        if -1.0 in label_counts.index:
            print(f"  Short (-1):     {int(label_counts[-1.0]):>5} samples")
        if 0.0 in label_counts.index:
            print(f"  Neutral (0):    {int(label_counts[0.0]):>5} samples")
        print(f"  Holding (NaN):  {nan_count:>5} samples")
        print("=" * 60)
        print()

        # ★ 修正: Date列を含めてCSV保存 (インデックスなし)
        df.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"✅ Label saved: {output_path}")
        print(f"   Total samples: {len(df)}")
        print(f"   Labeled samples: {len(df) - nan_count}")
        print()


def main():
    """
    CLI エントリーポイント
    
    Usage:
        python -m src.core.labeling.triple_barrier_labeler \
            --ticker AAPL \
            --input data/raw/AAPL.parquet \
            --output data/processed/AAPL_features_labeled.csv
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply Triple-Barrier Labeling")
    parser.add_argument("--ticker", type=str, required=True, help="Ticker symbol")
    parser.add_argument("--input", type=str, required=True, help="Input Parquet file")
    parser.add_argument("--output", type=str, required=True, help="Output CSV file")
    parser.add_argument("--upper", type=float, default=0.03, help="Upper return threshold")
    parser.add_argument("--lower", type=float, default=-0.02, help="Lower return threshold")
    parser.add_argument("--days", type=int, default=5, help="Max holding days")
    
    args = parser.parse_args()
    
    labeler = TripleBarrierLabeler(
        upper_return=args.upper,
        lower_return=args.lower,
        max_holding_days=args.days,
    )
    
    print("=" * 60)
    print(f"Triple-Barrier Labeling: {args.ticker}")
    print("=" * 60)
    print(f"  Upper Barrier: +{args.upper*100:.1f}%")
    print(f"  Lower Barrier: {args.lower*100:.1f}%")
    print(f"  Max Holding Days: {args.days}")
    print("=" * 60)
    print()
    
    labeler.label_data(args.input, args.output)


if __name__ == "__main__":
    main()
