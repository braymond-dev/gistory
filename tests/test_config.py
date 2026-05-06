from pathlib import Path

from gistory.config import write_default_config


def test_write_default_config_serializes_pydantic_url(tmp_path: Path) -> None:
    config_path = tmp_path / ".gistory.yml"

    write_default_config(config_path)

    text = config_path.read_text(encoding="utf-8")
    assert "api_base: https://api.openai.com/v1" in text
    assert "provider: ollama" in text
