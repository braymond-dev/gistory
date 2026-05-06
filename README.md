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
gistory generate --append
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

`gistory init` creates `.gistory.yml`:

```yaml
output: GISTORY.md
append_only: false
provider: ollama
model: qwen3:8b
ollama_url: http://localhost:11434
ollama_timeout: 300
api_base: https://api.openai.com/v1
api_key_env: OPENAI_API_KEY
api_timeout: 120
bedrock_region: us-east-1
bedrock_profile: null
bedrock_timeout: 120
bedrock_max_tokens: 500
bedrock_temperature: 0.2
azure_endpoint: https://your-resource.services.ai.azure.com/models
azure_api_key_env: null
azure_timeout: 120
azure_max_tokens: 500
azure_temperature: 0.2
vertex_project: null
vertex_location: global
vertex_timeout: 120
vertex_max_tokens: 500
vertex_temperature: 0.2
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

Append-only mode preserves the existing `GISTORY.md` and adds a new hidden
marker-delimited segment for commits after the last generated segment:

```bash
gistory generate --append
```

The markers use commit hashes:

```markdown
<!-- gistory:segment start=9f78fcf end=5cffba2 -->
...
<!-- gistory:segment-end -->
```

Append-only mode cannot be combined with `--range` or `--since`.

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
in the environment variable named by `api_key_env`:

```bash
export OPENAI_API_KEY="..."
gistory generate --provider openai-compatible --model gpt-4.1-mini
```

Any service that supports the OpenAI chat completions shape can be used by
changing `api_base`, `api_key_env`, and `model`.

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
