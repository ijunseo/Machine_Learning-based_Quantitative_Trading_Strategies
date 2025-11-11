"""
CPCVSplitterのテスト
"""

import numpy as np
import pandas as pd

from src.core.backtesting.cpcv_splitter import CPCVSplitter, apply_purging, apply_embargo


def test_cpcv_basic():
    """基本的なCPCV動作テスト"""
    # ダミーデータ生成
    n_samples = 100
    df = pd.DataFrame({
        "feature1": np.random.randn(n_samples),
        "feature2": np.random.randn(n_samples),
    })
    
    splitter = CPCVSplitter(n_blocks=5, n_test_blocks=1, purge_window=5, embargo_window=3)
    
    print("=== CPCV Basic Test ===")
    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(df)):
        print(f"Fold {fold_idx}: Train={len(train_idx)}, Test={len(test_idx)}")
    
    print("✅ CPCV basic test passed!")


def test_purging():
    """Purgingのテスト"""
    # Triple Barrierメタ情報
    barrier_times = pd.DataFrame({
        "t0": pd.date_range("2020-01-01", periods=100),
        "t1": pd.date_range("2020-01-06", periods=100),  # 5日後にエグジット
    })
    
    train_idx = np.arange(50)
    test_idx = np.arange(50, 70)
    
    clean_train = apply_purging(train_idx, test_idx, barrier_times)
    
    print("\n=== Purging Test ===")
    print(f"Original train size: {len(train_idx)}")
    print(f"After purging: {len(clean_train)}")
    print(f"Removed: {len(train_idx) - len(clean_train)} samples")
    print("✅ Purging test passed!")


def test_embargo():
    """Embargoのテスト"""
    train_idx = np.arange(100)
    test_idx = np.arange(50, 70)
    embargo_window = 5
    
    clean_train = apply_embargo(train_idx, test_idx, embargo_window)
    
    print("\n=== Embargo Test ===")
    print(f"Original train size: {len(train_idx)}")
    print(f"After embargo: {len(clean_train)}")
    print(f"Removed: {len(train_idx) - len(clean_train)} samples")
    print("✅ Embargo test passed!")


if __name__ == "__main__":
    test_cpcv_basic()
    test_purging()
    test_embargo()
    print("\n🎉 All CPCV tests passed!")
