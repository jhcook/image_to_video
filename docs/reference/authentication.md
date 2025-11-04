# Authentication Reference

Backend-specific authentication methods and environment variables.

## OpenAI Sora-2

- Method: API key
- Variable: `OPENAI_API_KEY`
- Configure:
```bash
# .env
OPENAI_API_KEY=sk-proj-xxxxx

# or shell
export OPENAI_API_KEY=sk-proj-xxxxx
```

## Azure AI Foundry Sora

- Method: API key or Azure CLI credentials
- Variables:
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_ENDPOINT` (e.g., https://your-resource.openai.azure.com/)
  - `AZURE_OPENAI_API_VERSION` (optional, default: 2024-10-01-preview)
- Configure:
```bash
# .env
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-01-preview
```

- Azure CLI (managed identity):
```bash
az login
# Tool can use CLI credentials; API key optional depending on setup
```

## Google Veo-3 (Vertex AI)

- Method: OAuth2 access token + project ID
- Variables:
  - `GOOGLE_CLOUD_PROJECT` (required)
  - `GOOGLE_API_KEY` (OAuth token via gcloud; short-lived; DO NOT store in .env)
- Browser OAuth (recommended):
```bash
./image2video.py --backend veo3 --google-login
```

- gcloud CLI alternative:
```bash
gcloud auth application-default login
export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

- Enable API:
```bash
gcloud services enable aiplatform.googleapis.com --project=your-project-id
```

## RunwayML

- Method: API key
- Variables:
  - `RUNWAY_API_KEY` (required)
  - `RUNWAY_MODEL` (optional default model)
- Configure:
```bash
# .env
RUNWAY_API_KEY=your-runway-key
RUNWAY_MODEL=gen4_turbo
```

## Security Tips

- Prefer `.env` for long-lived keys; avoid committing it to version control
- For Google OAuth tokens, refresh on demand; do not store in files
- Rotate keys regularly; consider Azure Key Vault or other secret managers
- Scope Azure RBAC and network (private endpoints) as needed

## Troubleshooting

- 401 Unauthorized:
  - Check environment variables are set
  - Verify token/key is valid and not expired
- Project not found (Veo): ensure `GOOGLE_CLOUD_PROJECT` is set
- Endpoint errors (Azure): verify correct endpoint URL

## See Also

- Installation: [../installation.md](../installation.md)
- Backends: [../backends/](../backends/)
- Environment Variables: [environment-variables.md](environment-variables.md)
