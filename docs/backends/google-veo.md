# Google Veo-3 Backend Guide

Complete guide to using Google's Veo-3 video generation models through Vertex AI.

## Overview

Google Veo-3 is a state-of-the-art video generation model available through Google Cloud's Vertex AI. It offers:

- **High-quality video generation** with excellent motion understanding
- **Seamless multi-clip stitching** (Veo 3.1 models)
- **Flexible duration** (2-10 seconds per clip)
- **Multiple reference images** (up to 3 images for style/content guidance)
- **Predictable pricing** ($0.15-$0.40 per video)

## Prerequisites

- **Google Cloud Project**: Must have a Google Cloud project with Vertex AI enabled
- **Authentication**: OAuth2 credentials (not API keys)
- **Billing**: Google Cloud billing account with payment method

## Authentication Setup

Veo-3 requires OAuth2 authentication through Vertex AI. **AI Studio API keys will NOT work**.

### Method 1: Browser OAuth (Recommended)

The simplest method - authenticate directly from the CLI:

```bash
# One-time login (opens browser)
./image2video.py --backend veo3 --google-login
```

**What happens:**
1. Browser opens with Google login page
2. You authenticate and grant permissions
3. Token is saved locally for future use
4. Token expires after 1 hour

**Re-authentication:**
```bash
# When token expires (after 1 hour)
./image2video.py --backend veo3 --google-login
```

### Method 2: gcloud CLI

For users who prefer command-line tools:

**Install gcloud CLI:**

```bash
# macOS
brew install google-cloud-sdk

# Ubuntu/Debian
sudo snap install google-cloud-sdk --classic

# Windows
# Download from: https://cloud.google.com/sdk/docs/install
```

**Authenticate:**

```bash
# One-time authentication
gcloud auth application-default login

# Get access token (expires after 1 hour)
export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"

# Set your project ID (REQUIRED)
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

**Add to .env file:**

```bash
# Add these to your .env file
echo "GOOGLE_CLOUD_PROJECT=your-project-id" >> .env

# Note: Don't add GOOGLE_API_KEY to .env (it expires hourly)
# Instead, get it fresh each time:
export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
```

### Method 3: Service Account (Advanced)

For production environments and automation:

**Create service account:**

```bash
# Set variables
PROJECT_ID="your-project-id"
SA_NAME="video-generator-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account
gcloud iam service-accounts create $SA_NAME \
  --display-name="Video Generator Service Account" \
  --project=$PROJECT_ID

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create ~/video-gen-key.json \
  --iam-account=$SA_EMAIL \
  --project=$PROJECT_ID
```

**Use service account:**

```bash
# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/video-gen-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Get access token
export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
```

### Token Management

**Important:** OAuth2 tokens expire after 1 hour. You'll see this error when expired:

```
Error 401: Request had invalid authentication credentials
```

**Refresh token:**

```bash
# Browser method
./image2video.py --backend veo3 --google-login

# gcloud method
export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
```

**Check token expiry:**

```bash
# View token details (gcloud users)
gcloud auth application-default print-access-token | \
  python -c "import sys, json, base64; \
  token=sys.stdin.read().strip(); \
  payload=token.split('.')[1]; \
  padding='='*(4-len(payload)%4); \
  print(json.loads(base64.urlsafe_b64decode(payload+padding)))"
```

## Available Models

List models:
```bash
./image2video.py --list-models veo3
```

### Veo 3.0 Models

**veo-3.0-generate-001** (Standard)
- **Quality**: High
- **Speed**: Standard (~2-4 minutes)
- **Pricing**: $0.40 per video
- **Duration**: 2-10 seconds
- **Best for**: Production-quality videos

```bash
./image2video.py --backend veo3 --model veo-3.0-generate-001 \
  -i "reference.jpg" "Your prompt"
```

**veo-3.0-fast-generate-001** (Fast)
- **Quality**: Good
- **Speed**: Fast (~1-2 minutes)
- **Pricing**: $0.15 per video
- **Duration**: 2-10 seconds
- **Best for**: Quick iterations, testing

```bash
./image2video.py --backend veo3 --model veo-3.0-fast-generate-001 \
  -i "reference.jpg" "Your prompt"
```

### Veo 3.1 Models (Stitching Support)

**veo-3.1-fast-generate-preview** (Latest, Recommended)
- **Quality**: Excellent
- **Speed**: Fast (~1-2 minutes)
- **Pricing**: $0.15 per video
- **Duration**: 2-10 seconds
- **Stitching**: ✅ Seamless multi-clip support
- **Best for**: High-quality videos with stitching

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview \
  -i "reference.jpg" "Your prompt"
```

**veo-3.1-generate-preview**
- **Quality**: Maximum
- **Speed**: Standard (~2-4 minutes)
- **Pricing**: $0.40 per video
- **Duration**: 2-10 seconds
- **Stitching**: ✅ Seamless multi-clip support
- **Best for**: Highest quality production work

```bash
./image2video.py --backend veo3 --model veo-3.1-generate-preview \
  -i "reference.jpg" "Your prompt"
```

## Basic Usage

### Text-to-Video

```bash
# No images required
./image2video.py --backend veo3 "A serene lake at sunset with gentle waves"
```

### Image-to-Video

```bash
# Single image
./image2video.py --backend veo3 -i "photo.jpg" "Slow pan across the landscape"

# Multiple reference images (up to 3)
./image2video.py --backend veo3 \
  -i "img1.jpg,img2.jpg,img3.jpg" \
  "Smooth transition between views"
```

### With Model Selection

```bash
# Fast model for testing
./image2video.py --backend veo3 --model veo-3.0-fast-generate-001 \
  -i "test.jpg" "Quick test prompt"

# High quality for production
./image2video.py --backend veo3 --model veo-3.0-generate-001 \
  -i "hero.jpg" "Final production prompt"
```

## Multi-Clip Stitching

Veo 3.1 models support seamless multi-clip generation with automatic frame transitions.

### Basic Stitching

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "ref1.jpg,ref2.jpg" \
  -p "First clip prompt" \
     "Second clip prompt" \
     "Third clip prompt"
```

**Output:**
- `veo3_clip_1.mp4` - Generated from first prompt + reference images
- `veo3_clip_2.mp4` - Generated from second prompt + last frame of clip 1 + reference images
- `veo3_clip_3.mp4` - Generated from third prompt + last frame of clip 2 + reference images

### How Stitching Works

1. **Clip 1**: Uses your reference images as style guide
2. **Automatic extraction**: Last frame of clip 1 is saved as PNG
3. **Clip 2**: Uses last frame of clip 1 as **first frame** (source) + reference images for style
4. **Repeat**: Each subsequent clip uses previous clip's last frame

**Key concept:** 
- **Source frame** (first frame): From previous clip's last frame
- **Reference images** (style guide): Your uploaded images, consistent across all clips

### Real Estate Walkthrough Example

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "foyer.jpg,living.jpg,kitchen.jpg" \
  -p "Entrance foyer, slow pan right revealing staircase" \
     "Dolly forward into living room, pan left to show sofas and TV" \
     "Continue into kitchen, pan right across island and appliances" \
     "Final shot through kitchen window with garden view"
```

### Concatenating Clips

After generation, combine into final video:

```bash
# Method 1: Direct concat (fast)
ffmpeg -i "concat:veo3_clip_1.mp4|veo3_clip_2.mp4|veo3_clip_3.mp4|veo3_clip_4.mp4" \
  -c copy final_walkthrough.mp4

# Method 2: Using concat file (more reliable)
printf "file 'veo3_clip_1.mp4'\n" > concat.txt
printf "file 'veo3_clip_2.mp4'\n" >> concat.txt
printf "file 'veo3_clip_3.mp4'\n" >> concat.txt
printf "file 'veo3_clip_4.mp4'\n" >> concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy final_walkthrough.mp4
```

### Text-Only Stitching

No reference images required:

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -p "Dawn breaks over calm lake with mist rising" \
     "Sun rays pierce through trees on shoreline" \
     "Birds take flight across the water" \
     "Morning mist clears revealing distant mountains"
```

### Python API for Advanced Control

```python
from video_gen.video_generator import generate_video_sequence_with_veo3_stitching

# Define prompts (one per clip)
prompts = [
    "Opening: entrance hall with modern staircase",
    "Pan left into spacious living room with floor-to-ceiling windows",
    "Smooth transition to gourmet kitchen with marble island",
    "Final view out window overlooking city skyline"
]

# Option 1: Same reference images for all clips
file_paths = [["house_ref1.jpg", "house_ref2.jpg"]] * len(prompts)

# Option 2: Different images per clip (for specific style control)
file_paths = [
    ["entrance1.jpg", "entrance2.jpg"],
    ["living1.jpg", "living2.jpg"],
    ["kitchen.jpg"],
    ["window_view.jpg"]
]

# Generate sequence
outputs = generate_video_sequence_with_veo3_stitching(
    prompts=prompts,
    file_paths_list=file_paths,
    width=1280,
    height=720,
    duration_seconds=7,
    model="veo-3.1-fast-generate-preview"
)

# Returns: ["veo3_clip_1.mp4", "veo3_clip_2.mp4", ...]
print(f"Generated {len(outputs)} seamless clips")
```

See **[Advanced Stitching Guide](../advanced/stitching.md)** for more techniques.

## Video Parameters

### Duration

Veo supports 2-10 seconds per clip:

```bash
# Short clip
./image2video.py --backend veo3 --duration 3 "Quick action"

# Standard clip
./image2video.py --backend veo3 --duration 7 "Medium length"

# Maximum length
./image2video.py --backend veo3 --duration 10 "Longer sequence"
```

**Recommendations:**
- 5-7 seconds: Best balance of quality and cost
- 2-4 seconds: Quick cuts, action sequences
- 8-10 seconds: Slow, cinematic movements

### Resolution

Standard resolutions supported:

```bash
# 1080p landscape (default)
./image2video.py --backend veo3 --width 1920 --height 1080 "Prompt"

# 1080p portrait (mobile)
./image2video.py --backend veo3 --width 1080 --height 1920 "Prompt"

# 720p landscape
./image2video.py --backend veo3 --width 1280 --height 720 "Prompt"

# Square (social media)
./image2video.py --backend veo3 --width 1080 --height 1080 "Prompt"
```

### Reference Images

Up to 3 reference images for style and content guidance:

```bash
# Single reference
./image2video.py --backend veo3 -i "style_ref.jpg" "Prompt"

# Multiple references (up to 3)
./image2video.py --backend veo3 \
  -i "angle1.jpg,angle2.jpg,angle3.jpg" \
  "Smooth camera movement through the scene"
```

**Tips:**
- Use images from different angles of the same subject
- Maintain consistent lighting across reference images
- Higher resolution references = better results

## Pricing

Veo-3 has straightforward per-video pricing:

| Model | Price per Video | Speed | Best For |
|-------|----------------|-------|----------|
| veo-3.0-fast-generate-001 | $0.15 | Fast | Testing, iterations |
| veo-3.1-fast-generate-preview | $0.15 | Fast | Production + stitching |
| veo-3.0-generate-001 | $0.40 | Standard | High quality |
| veo-3.1-generate-preview | $0.40 | Standard | Maximum quality + stitching |

**Multi-clip stitching costs:**
- 4 clips × $0.15 = $0.60 total
- 6 clips × $0.15 = $0.90 total
- 10 clips × $0.15 = $1.50 total

**Cost optimization tips:**
- Use fast models ($0.15) for all but final production
- Test with 5s clips before generating 10s
- Plan your clip sequence carefully (each generation costs money)

## Troubleshooting

### Authentication Errors

**Error: "401 Unauthorized"**
- Token has expired (1 hour limit)
- Solution: Re-run `--google-login` or refresh gcloud token

**Error: "Project not found"**
- `GOOGLE_CLOUD_PROJECT` not set
- Solution: `export GOOGLE_CLOUD_PROJECT="your-project-id"`

**Error: "AI Studio API key not supported"**
- Veo requires Vertex AI, not AI Studio
- Solution: Use OAuth2 via `--google-login` or gcloud

### Project Issues

**Error: "Vertex AI API not enabled"**
```bash
# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com --project=your-project-id
```

**Error: "Billing not enabled"**
- Go to Google Cloud Console
- Enable billing for your project
- Add payment method

### Generation Issues

**Error: "Model not found"**
- Check model name spelling
- List available models: `./image2video.py --list-models veo3`
- Ensure you're using a valid Veo 3.x model

**Error: "Too many reference images"**
- Veo supports maximum 3 reference images
- Solution: Reduce to 3 or fewer images

**Slow generation**
- Standard models take 2-4 minutes
- Use fast models for quicker turnaround
- Generation time doesn't affect quality

### Stitching Issues

**Error: "Stitching requires Veo 3.1 model"**
- Must use `veo-3.1-fast-generate-preview` or `veo-3.1-generate-preview`
- Solution: Specify correct model with `--model`

**Clips don't transition smoothly**
- Ensure using `--stitch` flag
- Check that prompts describe continuous action
- Verify reference images are consistent

**ffmpeg concat fails**
- Check all clip files exist
- Verify file paths in concat.txt
- Use absolute paths if needed

## Best Practices

### Prompt Engineering

**Camera movements:**
- "Slow dolly forward"
- "Smooth pan left to right"
- "Static shot with subtle movement"
- "Crane up revealing the scene"

**Timing:**
- "Hold for 2 seconds, then pan left"
- "Quick zoom over 3 seconds"
- "Slow reveal over the full duration"

**Style:**
- "Cinematic lighting"
- "Natural handheld movement"
- "Perfectly stable gimbal shot"
- "Dreamy slow motion feel"

### Multi-Clip Strategy

**Plan your sequence:**
1. Sketch out camera movements
2. Write prompts for each clip (5-7s each)
3. Identify consistent reference images
4. Generate and review each clip
5. Concatenate final sequence

**Continuity tips:**
- Describe similar lighting across clips
- Mention recurring elements ("the same staircase", "the marble island")
- Use consistent camera heights
- Maintain similar movement speeds

### Cost Management

**During testing:**
- Use `veo-3.1-fast-generate-preview` ($0.15)
- Generate 5s clips instead of 10s
- Test with 2-3 clips before full sequence

**For production:**
- Finalize prompts before generation
- Use fast model for most clips
- Reserve standard model ($0.40) for hero shots
- Budget: $0.15 × number of clips

## Examples

### Example 1: Product Reveal

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview \
  -i "product_white_bg.jpg" \
  --duration 7 \
  "360 degree rotation of the product on white background, \
   soft studio lighting, smooth continuous motion, \
   product remains centered throughout"
```

### Example 2: Nature Scene

```bash
./image2video.py --backend veo3 --model veo-3.0-fast-generate-001 \
  -i "landscape.jpg" \
  --duration 10 \
  "Slow dolly forward through forest path, \
   dappled sunlight filtering through trees, \
   gentle breeze moving leaves, peaceful atmosphere"
```

### Example 3: Real Estate Tour (6 Clips)

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "house_ref1.jpg,house_ref2.jpg,house_ref3.jpg" \
  --duration 7 \
  -p "Entrance foyer with modern staircase, slow pan right" \
     "Dolly into living room, pan left to sofas and wall-mounted TV" \
     "Pan right to sideboard with ornate mirror above" \
     "Dolly forward, pan left showing entry to other rooms" \
     "Dolly forward while panning right to re-show stairs" \
     "Final pan left to window with bar area and stools"

# Cost: 6 clips × $0.15 = $0.90
# Total duration: 6 × 7s = 42 seconds

# Concatenate
ffmpeg -i "concat:veo3_clip_1.mp4|veo3_clip_2.mp4|veo3_clip_3.mp4|veo3_clip_4.mp4|veo3_clip_5.mp4|veo3_clip_6.mp4" \
  -c copy house_tour_final.mp4
```

## Additional Resources

- 🎨 **[Prompt Engineering Guide](../advanced/prompts.md)**
- 🔗 **[Advanced Stitching Techniques](../advanced/stitching.md)**
- 🔧 **[General Troubleshooting](../advanced/troubleshooting.md)**
- 📖 **[User Guide](../user-guide.md)**

## External Links

- [Google Cloud Vertex AI Docs](https://cloud.google.com/vertex-ai/docs)
- [Veo Model Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/video/generate-video)
- [Google Cloud Console](https://console.cloud.google.com/)
- [gcloud CLI Installation](https://cloud.google.com/sdk/docs/install)

---

**Having issues?** Check the **[Troubleshooting Guide](../advanced/troubleshooting.md)** or review **[Authentication Setup](#authentication-setup)** above.
