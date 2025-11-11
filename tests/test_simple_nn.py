"""
Simple Neural Network の動作確認テスト
"""

import yaml
import numpy as np
from pathlib import Path

from src.models.neural_net.simple_nn import SimpleNN


def test_simple_nn():
    """SimpleNNの基本動作をテスト"""
    
    # 設定ファイル読み込み
    config_path = Path("src/models/neural_net/config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # ダミーデータ生成
    np.random.seed(42)
    X_train = np.random.randn(100, 10)  # 100サンプル、10特徴量
    y_train = np.random.choice([-1, 0, 1], size=100)  # Triple Barrierラベル
    X_test = np.random.randn(20, 10)
    
    # モデル初期化
    model = SimpleNN(config)
    print(f"Model: {model}")
    
    # 訓練
    print("\n訓練開始...")
    model.fit(X_train, y_train)
    
    # 予測
    print("\n予測実行...")
    predictions = model.predict(X_test)
    probabilities = model.predict_proba(X_test)
    
    print(f"Predictions: {predictions}")
    print(f"Probabilities shape: {probabilities.shape}")
    
    # 保存・読み込みテスト
    save_path = Path("models/test_simple_nn.pth")
    model.save(save_path)
    
    model_loaded = SimpleNN(config)
    model_loaded.load(save_path)
    
    predictions_loaded = model_loaded.predict(X_test)
    assert np.array_equal(predictions, predictions_loaded), "保存・読み込み後の予測が一致しません"
    
    print("\n✅ 全てのテストが成功しました！")


if __name__ == "__main__":
    test_simple_nn()
