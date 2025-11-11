"""
評価指標のテスト
"""

import numpy as np
import pandas as pd

from src.core.utils.metrics import (
    calculate_classification_metrics,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_calmar_ratio,
    calculate_all_metrics,
)


def test_classification_metrics():
    """分類指標のテスト"""
    y_true = np.array([-1, 0, 1, -1, 1, 0, 1])
    y_pred = np.array([-1, 0, 1, 0, 1, 0, -1])
    
    metrics = calculate_classification_metrics(y_true, y_pred)
    
    print("=== Classification Metrics ===")
    print(f"Accuracy: {metrics['accuracy']:.2%}")
    print(f"Precision (Macro): {metrics['precision_macro']:.2%}")
    print(f"Recall (Macro): {metrics['recall_macro']:.2%}")
    print(f"F1 (Macro): {metrics['f1_macro']:.2%}")
    print(f"Confusion Matrix:\n{np.array(metrics['confusion_matrix'])}")


def test_financial_metrics():
    """金融指標のテスト"""
    returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02, 0.01, -0.015])
    
    sharpe = calculate_sharpe_ratio(returns)
    cumulative = (1 + returns).cumprod()
    mdd = calculate_max_drawdown(cumulative)
    calmar = calculate_calmar_ratio(returns)
    
    print("\n=== Financial Metrics ===")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {mdd:.2%}")
    print(f"Calmar Ratio: {calmar:.2f}")


def test_all_metrics():
    """全指標の一括計算テスト"""
    y_true = np.array([-1, 0, 1, -1, 1])
    y_pred = np.array([-1, 0, 1, 0, 1])
    returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
    
    all_metrics = calculate_all_metrics(y_true, y_pred, returns)
    
    print("\n=== All Metrics ===")
    for key, value in all_metrics.items():
        if isinstance(value, (int, float)):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")


if __name__ == "__main__":
    test_classification_metrics()
    test_financial_metrics()
    test_all_metrics()
    print("\n✅ All tests passed!")
