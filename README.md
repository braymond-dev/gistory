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
gistory generate --repo ../wikiwatch
gistory generate --out GISTORY.md
gistory generate --fresh
gistory generate --provider ollama --model qwen3:8b
gistory generate --ollama-url http://localhost:11434
gistory generate --ollama-timeout 300
gistory generate --provider openai-compatible --model gpt-4.1-mini
gistory generate --provider bedrock --model us.anthropic.claude-3-5-haiku-20241022-v1:0 --bedrock-region us-east-1
gistory generate --provider azure --model my-deployment --azure-endpoint https://my-resource.services.ai.azure.com/models
gistory generate --provider vertex --model gemini-2.5-flash --vertex-project my-gcp-project --vertex-location us-central1
```

Explain a range without writing a file:

```bash
gistory explain --range "HEAD~10..HEAD"
```

## Configuration

`gistory init` creates a minimal Ollama config. Select another provider to emit
only its relevant settings:

```bash
gistory init --provider openai-compatible --model gpt-4.1-mini
```

```yaml
output: GISTORY.md
provider: openai-compatible
model: gpt-4.1-mini
openai_api_base: https://api.openai.com/v1
openai_api_key_env: OPENAI_API_KEY
openai_timeout: 120
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

Only the selected provider's fields are required. Other provider settings are
optional defaults inside Gistory and do not need to appear in the YAML.

## Providers

Every generated `GISTORY.md` contains hidden commit-hash markers. On the first
run Gistory creates a complete marked history; later runs automatically add a
new segment for commits after the last marker:

```bash
gistory generate
```

The markers use commit hashes:

```markdown
<!-- gistory:segment start=9f78fcf end=5cffba2 -->
...
<!-- gistory:segment-end -->
```

Markers are always enabled and cannot be toggled. An existing output without
markers causes generation to stop instead of duplicating history. Use
`gistory generate --fresh` to rebuild a clean marked file. Supplying `--range`
or `--since` also performs a marked rebuild of that selected history.

The configured output path is always excluded from commit summaries. Commits
that only update `GISTORY.md` are skipped, and mixed commits retain only their
non-generated files and diffs in the model prompt.

The default provider is `ollama`, which sends commit summaries to the local
Ollama API at `http://localhost:11434/api/generate`.

If you run Gistory in WSL and Ollama on Windows, test the connection from WSL:

```bash
curl http://localhost:11434/api/tags
```

If `localhost` does not reach the Windows Ollama service, set `ollama_url` in
`.gistory.yml` or pass `--ollama-url` with the Windows host IP.

Local models can be slow on first use while Ollama loads the model. Increase
`ollama_timeout` or pass `--ollama-timeout` if generation times out.

For tests and offline runs, use the deterministic mock provider:

```bash
gistory generate --provider mock
```

For remote hosted models, use the OpenAI-compatible provider. Set your API key
in the environment variable named by `openai_api_key_env`:

```bash
export OPENAI_API_KEY="..."
gistory generate --provider openai-compatible --model gpt-4.1-mini
```

Any service that supports the OpenAI chat completions shape can be used by
changing `openai_api_base`, `openai_api_key_env`, and `model`.

For AWS Bedrock, authenticate with normal AWS credentials or SSO, then use the
Bedrock provider:

```bash
aws sso login --profile work
gistory generate \
  --provider bedrock \
  --model us.anthropic.claude-3-5-haiku-20241022-v1:0 \
  --bedrock-region us-east-1 \
  --bedrock-profile work
```

If your environment uses default AWS credentials, omit `--bedrock-profile`.

For Azure AI Foundry, use Microsoft Entra ID by default:

```bash
az login
gistory generate \
  --provider azure \
  --model my-deployment \
  --azure-endpoint https://my-resource.services.ai.azure.com/models
```

If your Azure deployment uses an API key, name the environment variable:

```bash
export AZURE_INFERENCE_CREDENTIAL="..."
gistory generate \
  --provider azure \
  --model my-deployment \
  --azure-endpoint https://my-resource.services.ai.azure.com/models \
  --azure-api-key-env AZURE_INFERENCE_CREDENTIAL
```

For Google Cloud Vertex AI, authenticate with application default credentials:

```bash
gcloud auth application-default login
gistory generate \
  --provider vertex \
  --model gemini-2.5-flash \
  --vertex-project my-gcp-project \
  --vertex-location us-central1
```

## Development

```bash
pytest
```

## GitHub Actions

Gistory can run as a reusable action in another repository. The checkout must
include full history, and provider credentials stay in the consuming
repository's secrets or cloud authentication steps.

`GISTORY.md` is intended to be committed when using this workflow. Do not add
it to the consuming repository's `.gitignore`; the committed file provides the
durable narrative and segment markers used by later runs.

```yaml
name: Update Gistory

on:
  push:
    branches: [main]
    paths-ignore: [GISTORY.md]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  gistory:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - id: gistory
        uses: braymond-dev/gistory@v1
        with:
          provider: openai-compatible
          model: gpt-4.1-mini
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Commit updated history
        if: steps.gistory.outputs.changed == 'true'
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add GISTORY.md
          git commit -m "docs: update Gistory"
          git push
```

Copy [`examples/github-actions/gistory.yml`](examples/github-actions/gistory.yml)
to `.github/workflows/gistory.yml` in the consuming project. Add an
`OPENAI_API_KEY` repository secret, then publish a `v1` tag for this repository
so `uses: braymond-dev/gistory@v1` resolves.

For Bedrock, Azure, or Vertex, authenticate with the relevant official login
action before the Gistory step and select the corresponding provider/model.

Every run writes a job summary and uploads a `gistory-log-<run>-<attempt>`
artifact retained for 14 days. Successful summaries report whether the output
changed; failed summaries point to the same artifact for diagnosis. The log
includes safe run metadata, Python and Git context, dependency install output,
and Gistory stdout/stderr. Provider credentials and environment values are not
written to the log.

Screenshots referenced by `GISTORY.md` must also have durable locations. CI
workspace files and ordinary build artifacts disappear or expire after the
run, so images must either be committed alongside the history or uploaded to
stable storage whose URLs can be written into the Markdown. Gistory does not
currently ingest screenshot manifests.
