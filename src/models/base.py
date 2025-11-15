"""モデル基底クラス"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np


class BaseModel(ABC):
    """全モデルの基底クラス

    このクラスを継承することで、統一されたインターフェースでモデルを管理できます。

    Attributes:
        config (Dict[str, Any]): モデル設定
        model_name (str): モデル名
        is_trained (bool): モデルが訓練済みかどうか

    Examples:
        >>> from src.models.neural_net.simple_nn import SimpleNN
        >>> config = {"hidden_dims": [64, 32], "dropout": 0.2}
        >>> model = SimpleNN(config)
        >>> model.fit(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """
        モデルを初期化する。

        Args:
            config: モデル設定（config.yamlから読込）
        """
        self.config = config
        self.model_name = self.__class__.__name__
        self.is_trained = False

    @abstractmethod
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> None:
        """
        モデルを訓練する。

        Args:
            X_train: 訓練データの特徴量 (shape: [n_samples, n_features])
            y_train: 訓練データのラベル (shape: [n_samples])
            X_val: 検証データの特徴量 (optional)
            y_val: 検証データのラベル (optional)

        Notes:
            - 各サブクラスで具体的な訓練ロジックを実装すること
            - 訓練完了後は `self.is_trained = True` を設定すること
        """
        pass

    @abstractmethod
    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """
        予測を実行する。

        Args:
            X_test: テストデータの特徴量 (shape: [n_samples, n_features])

        Returns:
            予測結果 (shape: [n_samples])
            - 分類: クラスラベル（-1, 0, 1）
            - 回帰: 連続値

        Raises:
            RuntimeError: モデルが未訓練の場合

        Notes:
            各サブクラスで具体的な予測ロジックを実装すること。
        """
        pass

    @abstractmethod
    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        """
        クラス確率を予測する（分類モデル用）。

        Args:
            X_test: テストデータの特徴量 (shape: [n_samples, n_features])

        Returns:
            クラス確率 (shape: [n_samples, n_classes])

        Raises:
            RuntimeError: モデルが未訓練の場合
            NotImplementedError: 回帰モデルの場合
        """
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        """
        モデルを保存する。

        Args:
            path: 保存先パス

        Notes:
            - モデルの重みと設定を保存すること
            - PyTorchモデル: `torch.save()`
            - Scikit-learnモデル: `joblib.dump()`
        """
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        """
        モデルを読み込む。

        Args:
            path: 読み込み元パス

        Notes:
            - 保存されたモデルの重みと設定を読み込むこと
            - 読み込み後は `self.is_trained = True` を設定すること
        """
        pass

    def __repr__(self) -> str:
        """モデルの文字列表現"""
        status = "trained" if self.is_trained else "untrained"
        return f"{self.model_name}(status={status})"
