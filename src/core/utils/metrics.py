"""
評価指標モジュール

分類指標と金融指標を計算する関数群。
"""

from typing import Optional, List

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)


def calculate_classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, labels: Optional[List[int]] = None
) -> dict:
    """分類モデルの評価指標を計算する。

    Args:
        y_true: 真のラベル (shape: [n_samples])。
        y_pred: 予測ラベル (shape: [n_samples])。
        labels: ラベルのリスト（デフォルト: [-1, 0, 1]）。

    Returns:
        評価指標の辞書:
            - accuracy: 正解率
            - precision_macro: マクロ平均プレシジョン
            - recall_macro: マクロ平均リコール
            - f1_macro: マクロ平均F1スコア
            - confusion_matrix: 混同行列

    Examples:
        >>> y_true = np.array([-1, 0, 1, -1, 1])
        >>> y_pred = np.array([-1, 0, 1, 0, 1])
        >>> metrics = calculate_classification_metrics(y_true, y_pred)
        >>> print(f"Accuracy: {metrics['accuracy']:.2%}")
    """
    if labels is None:
        labels = [-1, 0, 1]  # Triple Barrier デフォルト

    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_macro": precision_score(
            y_true, y_pred, labels=labels, average="macro", zero_division=0
        ),
        "recall_macro": recall_score(
            y_true, y_pred, labels=labels, average="macro", zero_division=0
        ),
        "f1_macro": f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
    }

    return metrics


def calculate_sharpe_ratio(
    returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252
) -> float:
    """シャープレシオを計算する。

    Args:
        returns: リターン系列（例: 日次リターン）。
        risk_free_rate: 無リスク金利（年率）。デフォルトは0.0。
        periods_per_year: 年間期間数。デフォルトは252（取引日数）。

    Returns:
        シャープレシオ（年率換算）。

    Notes:
        シャープレシオ = (平均リターン - 無リスク金利) / リターンの標準偏差 * √periods

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        >>> sharpe = calculate_sharpe_ratio(returns)
        >>> print(f"Sharpe Ratio: {sharpe:.2f}")
    """
    if len(returns) < 2:
        return np.nan

    excess_returns = returns - risk_free_rate / periods_per_year
    mean_excess = excess_returns.mean()
    std_excess = excess_returns.std()

    if std_excess == 0:
        return np.nan

    sharpe_ratio = np.sqrt(periods_per_year) * mean_excess / std_excess
    return sharpe_ratio


def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
    """最大ドローダウンを計算する。

    Args:
        cumulative_returns: 累積リターン系列（例: (1 + r1) * (1 + r2) * ...）。

    Returns:
        最大ドローダウン（負の値、パーセンテージ）。

    Notes:
        最大ドローダウン = (谷の値 - 直近ピーク) / 直近ピーク

    Examples:
        >>> cumulative_returns = pd.Series([1.0, 1.1, 1.05, 1.15, 1.0])
        >>> mdd = calculate_max_drawdown(cumulative_returns)
        >>> print(f"Max Drawdown: {mdd:.2%}")
    """
    if len(cumulative_returns) < 2:
        return np.nan

    running_max = cumulative_returns.expanding().max()
    drawdown = (cumulative_returns - running_max) / running_max
    max_dd = drawdown.min()

    return max_dd


def calculate_calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """カルマーレシオを計算する。

    Args:
        returns: リターン系列。
        periods_per_year: 年間期間数。デフォルトは252。

    Returns:
        カルマーレシオ（年率リターン / 最大ドローダウン）。

    Notes:
        カルマーレシオ = 年率リターン / abs(最大ドローダウン)

    Examples:
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        >>> calmar = calculate_calmar_ratio(returns)
        >>> print(f"Calmar Ratio: {calmar:.2f}")
    """
    if len(returns) < 2:
        return np.nan

    # 年率リターン
    annual_return = returns.mean() * periods_per_year

    # 累積リターン
    cumulative_returns = (1 + returns).cumprod()

    # 最大ドローダウン
    max_dd = calculate_max_drawdown(cumulative_returns)

    if max_dd == 0 or np.isnan(max_dd):
        return np.nan

    calmar_ratio = annual_return / abs(max_dd)
    return calmar_ratio


def calculate_all_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, returns: Optional[pd.Series] = None
) -> dict:
    """全ての評価指標を一括計算する。

    Args:
        y_true: 真のラベル。
        y_pred: 予測ラベル。
        returns: リターン系列（金融指標を計算する場合）。

    Returns:
        全評価指標の辞書。

    Examples:
        >>> y_true = np.array([-1, 0, 1, -1, 1])
        >>> y_pred = np.array([-1, 0, 1, 0, 1])
        >>> returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        >>> metrics = calculate_all_metrics(y_true, y_pred, returns)
        >>> print(metrics)
    """
    # 分類指標
    classification_metrics = calculate_classification_metrics(y_true, y_pred)

    # 金融指標
    financial_metrics = {}
    if returns is not None and len(returns) > 0:
        financial_metrics = {
            "sharpe_ratio": calculate_sharpe_ratio(returns),
            "max_drawdown": calculate_max_drawdown((1 + returns).cumprod()),
            "calmar_ratio": calculate_calmar_ratio(returns),
        }

    # 統合
    all_metrics = {**classification_metrics, **financial_metrics}

    return all_metrics
