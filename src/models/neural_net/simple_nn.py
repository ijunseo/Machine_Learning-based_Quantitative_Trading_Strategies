"""
Simple Neural Network モデル

PyTorchベースの多層パーセプトロン（MLP）による分類モデル。
Triple Barrier Labelingの3クラス分類（-1: Short, 0: Neutral, 1: Long）に対応。
"""

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from src.models.base import BaseModel


class SimpleNNArchitecture(nn.Module):
    """
    Simple Neural Networkのアーキテクチャ
    
    多層パーセプトロン（MLP）による分類器。
    
    Args:
        input_dim: 入力特徴量の次元数
        hidden_dims: 隠れ層の各層のユニット数 (例: [128, 64, 32])
        output_dim: 出力クラス数（Triple Barrierの場合は3）
        dropout: ドロップアウト率
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dims: list[int],
        output_dim: int,
        dropout: float = 0.3
    ) -> None:
        super().__init__()
        
        layers = []
        prev_dim = input_dim
        
        # 隠れ層の構築
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        
        # 出力層
        layers.append(nn.Linear(prev_dim, output_dim))
        
        self.network = nn.Sequential(*layers)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """順伝播"""
        return self.network(x)


class SimpleNN(BaseModel):
    """
    Simple Neural Network モデル
    
    PyTorchベースのMLPによる分類モデル。
    
    Attributes:
        model: PyTorchモデル
        criterion: 損失関数
        optimizer: 最適化アルゴリズム
        device: 計算デバイス（CPU/GPU）
    
    Examples:
        >>> import yaml
        >>> with open("src/models/neural_net/config.yaml") as f:
        ...     config = yaml.safe_load(f)
        >>> model = SimpleNN(config)
        >>> model.fit(X_train, y_train, X_val, y_val)
        >>> predictions = model.predict(X_test)
    """
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        モデルを初期化する。
        
        Args:
            config: モデル設定（config.yamlから読込）
        """
        super().__init__(config)
        
        self.device = torch.device(config.get("device", "cpu"))
        self.model: Optional[SimpleNNArchitecture] = None
        self.criterion: Optional[nn.Module] = None
        self.optimizer: Optional[optim.Optimizer] = None
        
        # シード固定
        torch.manual_seed(config.get("experiment", {}).get("seed", 42))
    
    def _build_model(self, input_dim: int) -> None:
        """
        モデルアーキテクチャを構築する。
        
        Args:
            input_dim: 入力特徴量の次元数
        """
        arch_config = self.config["architecture"]
        
        self.model = SimpleNNArchitecture(
            input_dim=input_dim,
            hidden_dims=arch_config["hidden_dims"],
            output_dim=arch_config["output_dim"],
            dropout=arch_config["dropout"]
        ).to(self.device)
        
        # 損失関数
        self.criterion = nn.CrossEntropyLoss()
        
        # 最適化アルゴリズム
        train_config = self.config["training"]
        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=train_config["learning_rate"],
            weight_decay=train_config["weight_decay"]
        )
    
    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> None:
        """
        モデルを訓練する。
        
        Args:
            X_train: 訓練データの特徴量
            y_train: 訓練データのラベル（-1, 0, 1 → 0, 1, 2に変換）
            X_val: 検証データの特徴量
            y_val: 検証データのラベル
        """
        # ラベルを0始まりに変換（-1, 0, 1 → 0, 1, 2）
        y_train_shifted = y_train + 1
        
        # モデル構築
        if self.model is None:
            self._build_model(input_dim=X_train.shape[1])
        
        # データローダー作成
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.LongTensor(y_train_shifted)
        )
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config["training"]["batch_size"],
            shuffle=True
        )
        
        # 訓練ループ
        epochs = self.config["training"]["epochs"]
        log_interval = self.config["experiment"]["log_interval"]
        
        for epoch in range(epochs):
            self.model.train()
            total_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # 順伝播
                self.optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                # 逆伝播
                loss.backward()
                self.optimizer.step()
                
                total_loss += loss.item()
            
            avg_loss = total_loss / len(train_loader)
            
            if (epoch + 1) % log_interval == 0:
                print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")
        
        self.is_trained = True
    
    def predict(self, X_test: np.ndarray) -> np.ndarray:
        """
        予測を実行する。
        
        Args:
            X_test: テストデータの特徴量
        
        Returns:
            予測されたクラスラベル（-1, 0, 1）
        """
        if not self.is_trained:
            raise RuntimeError("モデルが未訓練です。先にfit()を実行してください。")
        
        self.model.eval()
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_test).to(self.device)
            outputs = self.model(X_tensor)
            predictions = torch.argmax(outputs, dim=1).cpu().numpy()
        
        # 0, 1, 2 → -1, 0, 1 に変換
        return predictions - 1
    
    def predict_proba(self, X_test: np.ndarray) -> np.ndarray:
        """
        クラス確率を予測する。
        
        Args:
            X_test: テストデータの特徴量
        
        Returns:
            各クラスの確率 (shape: [n_samples, 3])
        """
        if not self.is_trained:
            raise RuntimeError("モデルが未訓練です。先にfit()を実行してください。")
        
        self.model.eval()
        
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X_test).to(self.device)
            outputs = self.model(X_tensor)
            probabilities = torch.softmax(outputs, dim=1).cpu().numpy()
        
        return probabilities
    
    def save(self, path: Path) -> None:
        """
        モデルを保存する。
        
        Args:
            path: 保存先パス（例: models/simple_nn_model.pth）
        """
        if not self.is_trained:
            raise RuntimeError("モデルが未訓練です。保存できません。")
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "config": self.config
        }, path)
        
        print(f"✅ モデルを保存しました: {path}")
    
    def load(self, path: Path) -> None:
        """
        モデルを読み込む。
        
        Args:
            path: 読み込み元パス
        """
        checkpoint = torch.load(path, map_location=self.device)
        
        self.config = checkpoint["config"]
        
        # モデル再構築
        input_dim = checkpoint["model_state_dict"]["network.0.weight"].shape[1]
        self._build_model(input_dim)
        
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.is_trained = True
        
        print(f"✅ モデルを読み込みました: {path}")
