import json
from pathlib import Path

import pandas as pd


class FeatureStore:
    """Persist named feature tables and descriptions beneath a project directory."""

    def __init__(self, base_dir: str | Path = "feature_store") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.base_dir / "metadata.json"

    def save_features(self, name: str, data: pd.DataFrame, description: str = "") -> Path:
        if not name or Path(name).name != name:
            raise ValueError("Feature name must be a non-empty filename-safe value")
        path = self.base_dir / f"{name}.csv"
        data.to_csv(path, index=True)
        metadata = self._read_metadata()
        metadata[name] = {"description": description, "path": path.name}
        self._metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return path

    def load_features(self, name: str, **read_csv_options: object) -> pd.DataFrame:
        metadata = self._read_metadata()
        if name not in metadata:
            raise KeyError(f"Feature table not found: {name}")
        path = self.base_dir / metadata[name]["path"]
        return pd.read_csv(path, index_col=0, **read_csv_options)

    def list_features(self) -> list[dict[str, str]]:
        return [
            {"name": name, **details}
            for name, details in sorted(self._read_metadata().items())
        ]

    def _read_metadata(self) -> dict[str, dict[str, str]]:
        if not self._metadata_path.is_file():
            return {}
        return json.loads(self._metadata_path.read_text(encoding="utf-8"))