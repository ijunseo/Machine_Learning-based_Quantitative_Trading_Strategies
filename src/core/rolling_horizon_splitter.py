import json
from pathlib import Path
from typing import Any, Dict


def load_config(config_path: str) -> Dict[str, Any]:
    """実験設定ファイル(JSON or YAML)を読み込む.

    Args:
        config_path: 実験設定ファイルのパス.

    Returns:
        設定内容の辞書.
    """
    path = Path(config_path)

    if path.suffix == ".json":
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # YAMLの場合
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
