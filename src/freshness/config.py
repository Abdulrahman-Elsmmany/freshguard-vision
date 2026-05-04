"""Configuration loading helpers."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIGS_DIR = ROOT_DIR / "configs"


def resolve_path(value: str | Path, base_dir: Path | None = None) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if base_dir is None:
        base_dir = ROOT_DIR
    return (base_dir / path).resolve()


def load_toml(path: str | Path) -> dict[str, Any]:
    resolved = resolve_path(path)
    with resolved.open("rb") as handle:
        return tomllib.load(handle)
