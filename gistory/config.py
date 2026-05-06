from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import AnyHttpUrl, BaseModel, Field


DEFAULT_IGNORE = [
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "dist/**",
    "build/**",
    "node_modules/**",
    ".next/**",
]


class GistoryConfig(BaseModel):
    output: str = "GISTORY.md"
    provider: Literal["ollama", "openai-compatible", "bedrock", "mock"] = "ollama"
    model: str = "qwen3:8b"
    ollama_url: str = "http://localhost:11434"
    ollama_timeout: float = 300.0
    api_base: AnyHttpUrl = AnyHttpUrl("https://api.openai.com/v1")
    api_key_env: str = "OPENAI_API_KEY"
    api_timeout: float = 120.0
    bedrock_region: str = "us-east-1"
    bedrock_profile: str | None = None
    bedrock_timeout: float = 120.0
    bedrock_max_tokens: int = 500
    bedrock_temperature: float = 0.2
    group_by: Literal["month"] = "month"
    ignore: list[str] = Field(default_factory=lambda: DEFAULT_IGNORE.copy())


def default_config() -> GistoryConfig:
    return GistoryConfig()


def load_config(path: Path = Path(".gistory.yml")) -> GistoryConfig:
    if not path.exists():
        return default_config()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise RuntimeError(f"Unable to read config file {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(f"Invalid YAML in config file {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"Config file {path} must contain a YAML mapping")
    return GistoryConfig.model_validate(raw)


def write_default_config(path: Path = Path(".gistory.yml"), overwrite: bool = False) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists")
    config = default_config()
    data = config.model_dump()
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
