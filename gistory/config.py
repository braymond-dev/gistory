from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import AliasChoices, AnyHttpUrl, BaseModel, Field


DEFAULT_IGNORE = [
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "dist/**",
    "build/**",
    "node_modules/**",
    ".next/**",
]

PROVIDERS = ("ollama", "openai-compatible", "bedrock", "azure", "vertex", "mock")
PROVIDER_DEFAULT_MODELS = {
    "ollama": "qwen3:8b",
    "openai-compatible": "gpt-4.1-mini",
    "bedrock": "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "azure": "your-deployment-name",
    "vertex": "gemini-2.5-flash",
    "mock": "mock",
}
COMMON_CONFIG_FIELDS = {"output", "provider", "model", "group_by", "ignore"}
PROVIDER_CONFIG_FIELDS = {
    "ollama": {"ollama_url", "ollama_timeout"},
    "openai-compatible": {"openai_api_base", "openai_api_key_env", "openai_timeout"},
    "bedrock": {
        "bedrock_region",
        "bedrock_profile",
        "bedrock_timeout",
        "bedrock_max_tokens",
        "bedrock_temperature",
    },
    "azure": {
        "azure_endpoint",
        "azure_api_key_env",
        "azure_timeout",
        "azure_max_tokens",
        "azure_temperature",
    },
    "vertex": {
        "vertex_project",
        "vertex_location",
        "vertex_timeout",
        "vertex_max_tokens",
        "vertex_temperature",
    },
    "mock": set(),
}


class GistoryConfig(BaseModel):
    output: str = "GISTORY.md"
    provider: Literal["ollama", "openai-compatible", "bedrock", "azure", "vertex", "mock"] = "ollama"
    model: str = "qwen3:8b"
    ollama_url: str = "http://localhost:11434"
    ollama_timeout: float = 300.0
    openai_api_base: AnyHttpUrl = Field(
        default=AnyHttpUrl("https://api.openai.com/v1"),
        validation_alias=AliasChoices("openai_api_base", "api_base"),
    )
    openai_api_key_env: str = Field(
        default="OPENAI_API_KEY",
        validation_alias=AliasChoices("openai_api_key_env", "api_key_env"),
    )
    openai_timeout: float = Field(
        default=120.0,
        validation_alias=AliasChoices("openai_timeout", "api_timeout"),
    )
    bedrock_region: str = "us-east-1"
    bedrock_profile: str | None = None
    bedrock_timeout: float = 120.0
    bedrock_max_tokens: int = 500
    bedrock_temperature: float = 0.2
    azure_endpoint: str = "https://your-resource.services.ai.azure.com/models"
    azure_api_key_env: str | None = None
    azure_timeout: float = 120.0
    azure_max_tokens: int = 500
    azure_temperature: float = 0.2
    vertex_project: str | None = None
    vertex_location: str = "global"
    vertex_timeout: float = 120.0
    vertex_max_tokens: int = 500
    vertex_temperature: float = 0.2
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


def write_default_config(
    path: Path = Path(".gistory.yml"),
    overwrite: bool = False,
    provider: str = "ollama",
    model: str | None = None,
) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists")
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    config = GistoryConfig(provider=provider, model=model or PROVIDER_DEFAULT_MODELS[provider])
    fields = COMMON_CONFIG_FIELDS | PROVIDER_CONFIG_FIELDS[provider]
    data = config.model_dump(mode="json", include=fields)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
