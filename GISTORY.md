# Gistory

<!-- gistory:segment start=9f78fcf end=c879fae -->

## 2026-05

The initial commit introduces Gistory, a tool that generates a narrative Markdown history from a local Git repository’s commit data. It implements core functionality to read commit metadata and diffs, filter files based on ignore patterns, and summarize changes using pluggable providers, including a default integration with the Ollama API and a mock provider for testing. The project includes a CLI with commands to initialize configuration, generate history files with flexible revision ranges or date filters, and explain commit ranges interactively. Configuration is managed via a YAML file supporting output paths, provider selection, and file ignore patterns. Comprehensive tests cover filters, Git reading, Markdown generation, and the processing pipeline, establishing a solid foundation for extensible, automated project history summarization.

Configurable connection settings for the Ollama provider were added to Gistory, allowing users to specify the Ollama API base URL and request timeout via command-line options or the config file. The default Ollama URL remains `http://localhost:11434` with a 300-second timeout, but these can now be overridden to support scenarios like running Ollama on a different host or adjusting for slow model loading. The CLI commands `generate` and `explain` accept `--ollama-url` and `--ollama-timeout` flags, which are passed through the configuration and used when constructing the OllamaProvider instance. Documentation was updated to explain these options and troubleshooting tips for WSL users, and tests were added to verify that the provider correctly receives the configured URL and timeout values.

The project added a new OpenAI-compatible provider to support remote LLM services that implement the OpenAI chat completions API shape. This provider enables users to specify an API base URL, API key environment variable, and request timeout, allowing flexible integration with any OpenAI-compatible endpoint. The CLI, configuration model, and pipeline were extended to accept these new parameters, and documentation was updated with usage examples. Internally, a shared prompt builder was introduced for consistent commit summary prompts across providers. The OpenAI-compatible provider sends chat completion requests with a system message instructing concise, factual project history summaries, improving developer experience by broadening supported LLM backends while maintaining existing workflows. Tests were added to cover the new provider’s integration.

AWS Bedrock support was added as a new provider option, enabling Gistory to generate commit summaries using Bedrock's chat-based model runtime. The integration introduces a dedicated BedrockProvider class that handles authentication via AWS credentials or profiles, configures request parameters like region, timeout, max tokens, and temperature, and formats prompts to Bedrock’s converse API. CLI commands and configuration schemas were extended to accept Bedrock-specific options, allowing users to specify region, profile, and generation settings seamlessly. Comprehensive tests were added to validate the provider’s behavior, and documentation was updated with usage examples demonstrating AWS SSO login and Bedrock invocation. This enhancement broadens Gistory’s model support to include AWS Bedrock, improving flexibility for users leveraging AWS-managed LLM services.

Support for Azure AI Foundry and Google Cloud Vertex AI was added as new provider options, enabling users to generate commit histories and explanations using these cloud-native LLM services. The CLI and configuration schema were extended with provider-specific parameters such as Azure endpoints, API key environment variables, and Vertex project/location settings. New provider modules encapsulate the integration logic, while tests were added to validate pipeline behavior with these providers. The README was updated with usage examples and authentication instructions for both Azure and Vertex, improving developer experience and expanding the tool’s cloud compatibility.

Incremental append mode was introduced to gistory, enabling users to preserve an existing GISTORY.md file and append new commit summaries as hidden, marker-delimited segments. This feature adds a new CLI option `--append` and a corresponding `append_only` config flag, disallowing use with `--range` or `--since` to avoid conflicting commit selections. Architecturally, the implementation detects the last appended commit hash from segment markers in the existing Markdown, then generates summaries only for subsequent commits, rendering them as a new segment enclosed by start/end markers referencing commit hashes. The new segments are appended to the existing file content, improving developer experience by supporting incremental history generation without overwriting prior output. Comprehensive tests verify segment rendering, marker parsing, and append behavior, while documentation and CLI help were updated to describe usage and constraints.

The CLI now reports the elapsed time for generating Git history output, enhancing user feedback on command duration. A new --repo option was added to specify the target Git repository path, improving flexibility for multi-repo workflows. Internally, timing is measured using monotonic clocks around the history generation and write steps, and the output path resolution was adjusted to handle relative paths within the specified repo. Corresponding tests verify that output files are created correctly and that the elapsed time formatting behaves as expected. Additionally, the default config serialization was refined to use JSON mode for consistent YAML output.

The gistory reporting output was refined to improve readability and accuracy in the generated project history. Commit summaries within each monthly group are now sorted chronologically by commit date, ensuring narratives reflect the actual sequence of changes. The narrative builder was enhanced to format summaries as distinct paragraphs with normalized whitespace and proper sentence-ending punctuation, replacing the previous single-sentence concatenation. Additionally, the markdown segment renderer was corrected to identify the oldest and newest commits by date rather than list position, improving segment metadata accuracy. The commit prompt template was also updated to guide the AI toward clearer, more concrete, and engineer-focused summaries that emphasize user-visible, architectural, testing, or developer-experience impacts. These changes collectively enhance the clarity and precision of gistory’s generated project histories, supported by expanded tests verifying paragraph normalization and ordering.

### Key commits
- 9f78fcf initial commit
- 5cffba2 add configurable Ollama connection settings
- 4d79ee6 add compatibility for remote llm providers, openAI compatible
- 190fccd support AWS Bedrock
- 535056d Added support for Azure and GCP Vertex
- b04ff68 added incremental gistory.md append mode
- 1b0be80 added time elapsed to output
- 23d5c8b refined gistory reporting output

## 2026-06

A reusable GitHub Action was introduced to automate generating or incrementally updating the GISTORY.md file from a repository’s Git history. The action, defined in a new action.yml manifest, sets up Python, installs Gistory, and runs it with configurable inputs for provider, model, config path, output file, and append mode. An example workflow demonstrates usage with full Git history checkout, environment-based API key injection, and conditional commits when changes occur. Tests validate the action metadata and ensure the example workflow enforces full git history fetch and proper secret usage. This addition streamlines integration of Gistory into CI pipelines, improving developer experience by automating documentation updates.

The update refines the narrative flow by introducing logic to mark month-based history sections as "(continued)" when they appear in existing markdown, improving clarity in incremental changelog generation. It adjusts the grouping of commits by month to sort chronologically rather than reverse, ensuring a natural timeline progression. The segment rendering function now accepts explicit start and end commit hashes to accurately annotate the commit range, overriding date-based ordering. These changes enhance the readability of generated history segments and support incremental updates without duplicating month headings. Corresponding tests verify correct labeling of continued months and proper segment boundary markers, reinforcing robustness in markdown output and developer experience.

### Key commits
- fb09597 add reusable github action
- c879fae update narrative flow

<!-- gistory:segment-end -->

<!-- gistory:segment start=d1c5f09 end=d1c5f09 -->

## 2026-06 (continued)

The commit refactors Gistory’s commit history generation by replacing the previous append-only mode with a clearer, marker-based incremental update system. It removes the deprecated append flag and introduces a new --fresh option to rebuild the entire marked history file from a specified range or since-date, ensuring consistent segment markers are always present. The CLI, GitHub Action, and configuration schema were updated to reflect this change, simplifying command flags and improving user experience by preventing silent duplication or marker-less outputs. Internally, the pipeline now distinguishes between generating a full marked document and updating an existing one by appending new segments after the last commit marker. Tests were added and adjusted to verify correct marker handling and incremental updates, enhancing reliability and maintainability of the commit summarization workflow.

### Key commits
- d1c5f09 fixed commit marking and changed command flags

<!-- gistory:segment-end -->
