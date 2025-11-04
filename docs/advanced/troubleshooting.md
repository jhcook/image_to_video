# Troubleshooting Guide

Common issues and fixes for the Multi-Backend Video Generator.

- If you're new, first try the 5-minute guide: quick-start.md
- For setup problems, see installation.md
- For auth errors, see reference/authentication.md
- **For SSL certificate errors, see [SSL Troubleshooting](../technical/ssl-troubleshooting.md)**

## Quick Checklist

1. Python venv is activated: `source venv/bin/activate`
2. Dependencies installed: `pip install -r requirements.txt`
3. Correct backend selected: `--backend sora2|azure-sora|veo3|runway`
4. Required environment variables set (per backend)
5. Images exist and paths are correct (use absolute paths if unsure)
6. Logs reviewed for details: `tail -50 logs/video_gen.log`

## Authentication & Credentials

### OpenAI Sora
- Error: "API key not found" or 401 Unauthorized
  - Ensure `OPENAI_API_KEY` is set (env or .env)
  - Verify the key is valid: `echo $OPENAI_API_KEY`
  - Confirm your account has access to Sora

### Azure Sora
- Error: "Endpoint not found"
  - Check `AZURE_OPENAI_ENDPOINT` format: `https://<name>.openai.azure.com/`
  - Make sure the resource exists in the Azure subscription
- Error: 401 Unauthorized
  - Ensure `AZURE_OPENAI_API_KEY` is set, or login via `az login`
  - Confirm the user/service principal has Cognitive Services User role

### Google Veo
- Error: 401 Unauthorized
  - Token expired (valid ~1h); re-run `--google-login` or `gcloud auth application-default login`
  - Ensure `GOOGLE_CLOUD_PROJECT` is set to a valid project ID
- Error: Using AI Studio key
  - Veo requires OAuth token, not AI Studio API key; follow docs/backends/google-veo.md
- Error: Vertex AI API not enabled
  - Enable: `gcloud services enable aiplatform.googleapis.com`

### RunwayML
- Error: 401 Unauthorized / Invalid API key
  - Ensure `RUNWAY_API_KEY` is set; confirm in account settings
- Error: Insufficient credits
  - Purchase or add credits in RunwayML

## Image Input Issues

- Error: "No images provided"
  - Use `-i` flag; supports comma-separated list and wildcards
  - Example: `-i "img1.jpg,img2.jpg,dir/*.png"`
- Error: "File not found"
  - Check path spelling; try absolute paths
  - Quote wildcard patterns to avoid shell expansion issues in some shells
- RunwayML ignoring extra images
  - Gen-4 models accept only one image; the first is used

## Duration & Resolution

- RunwayML duration must be 5 or 10 seconds
  - The script auto-adjusts to 5s if unsupported value is used
  - Use Veo models for 2-10s flexible duration
- Output resolution too large/slow
  - Start with 1280x720 for tests; move to 1920x1080 or 4K for final

## Veo 3.1 Stitching Problems

- Error: "Stitching requires Veo 3.1 model"
  - Use `--model veo-3.1-fast-generate-preview` or `veo-3.1-generate-preview`
- Clips not transitioning smoothly
  - Ensure `--stitch` is set
  - Prompts should describe continuous action
  - Keep reference images consistent across clips
- ffmpeg concat fails
  - Verify clip files exist and are in order
  - Use concat demuxer with a list file if needed

## Performance & Reliability

- Slow generation times
  - Fast models: gen4_turbo (Runway), veo-3.0-fast (Google), veo3.1_fast (Runway)
  - Lower resolution and shorter duration during testing
- API capacity errors / 429
  - Script retries with exponential backoff automatically; wait or try off-peak
- Network timeouts
  - Check firewall/proxy settings; retry

## Prompt & Quality Issues

- Output doesn’t match prompt
  - Be specific; include camera movements, timing, lighting
  - Use multiple reference images (except Runway Gen-4)
- Geometry warping or drift
  - Reduce duration (5–7s often best)
  - Increase number of reference images
  - Reinforce constraints in prompt (e.g., "keep edges straight, no bending walls")
- Style inconsistencies
  - Use images with similar lighting/time of day
  - Mention consistent style and color grading in the prompt

## Logging and Diagnostics

- Log file: `logs/video_gen.log` (DEBUG level)
- Useful commands:
  - View last lines: `tail -50 logs/video_gen.log`
  - Follow live: `tail -f logs/video_gen.log`
  - Search errors: `grep -i "error" logs/video_gen.log`

## Common Command Examples

- List models: `./image2video.py --list-models` or `--list-models runway`
- Quick test: `./image2video.py --backend runway --model gen4_turbo "A quick test"`
- Stitching: `./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch -p "A" "B"`

## When to Switch Backends

- Need multi-clip stitching → Use Veo 3.1 (Google or Runway Veo)
- Need multiple reference images (3) → Veo models
- Fast, simple tests → Runway gen4_turbo
- Enterprise features (RBAC, private endpoints) → Azure Sora

## Still Stuck?

- Revisit installation: installation.md
- Recheck authentication: reference/authentication.md
- Open an issue with: logs excerpt, command used (omit secrets), backend, model, and error message.
