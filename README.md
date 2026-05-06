# Gistory

Gistory reads a local Git repository's commit history and diffs, summarizes the
evolution of the project, and writes a narrative Markdown file named
`GISTORY.md`.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

Create the default configuration:

```bash
gistory init
```

Generate a history file:

```bash
gistory generate
gistory generate --since "30 days ago"
gistory generate --range "HEAD~20..HEAD"
gistory generate --out GISTORY.md
gistory generate --provider ollama --model qwen3:8b
```

Explain a range without writing a file:

```bash
gistory explain --range "HEAD~10..HEAD"
```

## Configuration

`gistory init` creates `.gistory.yml`:

```yaml
output: GISTORY.md
provider: ollama
model: qwen3:8b
group_by: month
ignore:
  - package-lock.json
  - yarn.lock
  - pnpm-lock.yaml
  - dist/**
  - build/**
  - node_modules/**
  - .next/**
```

## Providers

The default provider is `ollama`, which sends commit summaries to the local
Ollama API at `http://localhost:11434/api/generate`.

For tests and offline runs, use the deterministic mock provider:

```bash
gistory generate --provider mock
```

## Development

```bash
pytest
```
