from pathlib import Path

from gistory.config import load_config, write_default_config


def test_write_default_config_only_includes_selected_provider(tmp_path: Path) -> None:
    config_path = tmp_path / ".gistory.yml"

    write_default_config(config_path, provider="openai-compatible")

    text = config_path.read_text(encoding="utf-8")
    assert "openai_api_base: https://api.openai.com/v1" in text
    assert "provider: openai-compatible" in text
    assert "model: gpt-4.1-mini" in text
    assert "ollama_url" not in text
    assert "bedrock_region" not in text
    assert "azure_endpoint" not in text
    assert "vertex_project" not in text


def test_write_default_config_defaults_to_minimal_ollama_config(tmp_path: Path) -> None:
    config_path = tmp_path / ".gistory.yml"

    write_default_config(config_path)

    text = config_path.read_text(encoding="utf-8")
    assert "provider: ollama" in text
    assert "ollama_url: http://localhost:11434" in text
    assert "openai_api_base" not in text


def test_load_config_accepts_legacy_openai_field_names(tmp_path: Path) -> None:
    config_path = tmp_path / ".gistory.yml"
    config_path.write_text(
        "provider: openai-compatible\n"
        "api_base: https://legacy.example/v1\n"
        "api_key_env: LEGACY_KEY\n"
        "api_timeout: 45\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert str(config.openai_api_base) == "https://legacy.example/v1"
    assert config.openai_api_key_env == "LEGACY_KEY"
    assert config.openai_timeout == 45
