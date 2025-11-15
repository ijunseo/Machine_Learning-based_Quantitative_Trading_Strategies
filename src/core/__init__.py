"""Core modules for machine learning-based quantitative trading strategies.

Provides data splitting and rolling horizon splitting functionalities.
"""

from .data_splitter import DataSplitter, rolling_horizon_split
from .rolling_horizon_splitter import RollingHorizonSplitter

__all__ = [
    "DataSplitter",
    "RollingHorizonSplitter",
    "rolling_horizon_split",
]
