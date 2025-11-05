# Environment Variables

Central reference for all environment variables used by the tool.

The application loads variables from the OS environment and a `.env` file in the project root (if present).

## Global

- No global variables are strictly required; each provider has its own.

## OpenAI Sora-2

- `OPENAI_API_KEY`
  - Description: OpenAI API key for Sora-2 access
  - Required: Yes (for OpenAI provider)
  - Example: `sk-proj-xxxxx`

## Azure AI Foundry Sora

- `AZURE_OPENAI_API_KEY`
  - Description: Azure OpenAI key for AI Foundry resource
  - Required: Yes (unless using CLI/managed identity)

- `AZURE_OPENAI_ENDPOINT`
  - Description: Azure OpenAI endpoint URL
  - Required: Yes
  - Example: `https://your-resource.openai.azure.com/`

- `AZURE_OPENAI_API_VERSION`
  - Description: API version to use
  - Required: No (default: `2024-10-01-preview`)

## Google Veo-3 (Vertex AI)

- `GOOGLE_CLOUD_PROJECT`
  - Description: Google Cloud project ID that enables Vertex AI
  - Required: Yes

- `GOOGLE_API_KEY`
  - Description: OAuth2 access token from gcloud or browser login
  - Required: Yes (at runtime), short-lived (do not place in .env)

## RunwayML

- `RUNWAY_API_KEY`
  - Description: RunwayML API key
  - Required: Yes

- `RUNWAY_MODEL`
  - Description: Default model selection for RunwayML
  - Required: No
  - Allowed: `gen4_turbo`, `gen4`, `google`, `google.1`, `google.1_fast`

## Tips

- Use a `.env` file for long-lived API keys (OpenAI, Azure, RunwayML)
- Avoid storing short-lived tokens (Google OAuth) in `.env`
- Source your shell profile to load changes: `source ~/.zshrc`

## Example .env

```
# OpenAI Sora
OPENAI_API_KEY=sk-proj-xxxxx

# Azure Sora
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-01-preview

# Google Veo (do not store GOOGLE_API_KEY here)
GOOGLE_CLOUD_PROJECT=your-project-id

# RunwayML
RUNWAY_API_KEY=your-runway-key
RUNWAY_MODEL=gen4_turbo
```

## Where They’re Used

- `video_gen/config.py` loads and validates variables per provider
- `video_gen/video_generator.py` chooses provider configs via `create_config_for_provider`

## Troubleshooting

- Empty variable: `echo $VAR_NAME` should print a value
- Wrong file: ensure `.env` is in project root
- Process not seeing changes: restart terminal or `source` your profile
