# User Guide

Complete guide to using the Multi-Backend Video Generator.

## Table of Contents

- [Overview](#overview)
- [Basic Usage](#basic-usage)
- [Backend Selection](#backend-selection)
- [Model Selection](#model-selection)
- [Image Input](#image-input)
- [Video Parameters](#video-parameters)
- [Multi-Clip Stitching](#multi-clip-stitching)
- [Command-Line Options](#command-line-options)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Examples](#examples)

## Overview

The Multi-Backend Video Generator supports four powerful AI video generation services:

- **OpenAI Sora-2**: High-quality text-to-video and image-to-video generation
- **Azure AI Foundry Sora**: Enterprise deployment of Sora-2 with Azure security
- **Google Veo-3**: Advanced video generation with seamless stitching capabilities
- **RunwayML**: Fast Gen-4 models plus access to Google Veo via simpler API

Each backend has unique features, pricing, and authentication requirements. This guide covers everything you need to know.

## Basic Usage

### Prerequisites

Before generating videos, ensure you have:

1. **Python environment activated**:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **API credentials configured** (see [Installation Guide](installation.md))

3. **Images prepared** (optional for text-to-video)

### Your First Video

**Text-to-video (no images):**
```bash
./image2video.py "A serene lake at sunset with gentle waves"
```

**Image-to-video:**
```bash
./image2video.py -i "photo.jpg" "A timelapse showing clouds moving across the sky"
```

**Output:**
```
Loading configuration from environment and .env file...
Using backend: sora2
Using model: sora-2
Video generation parameters:
  Prompt: A serene lake at sunset with gentle waves
  Images: photo.jpg
  Duration: 5 seconds
  Resolution: 1920x1080

Generating video...
Video generated successfully: sora2_video_20250127_143022.mp4
```

## Backend Selection

Use the `--backend` flag to choose your AI provider:

```bash
# OpenAI Sora (default)
./image2video.py "Prompt"

# Or explicitly:
./image2video.py --backend sora2 "Prompt"

# Azure AI Foundry Sora
./image2video.py --backend azure-sora "Prompt"

# Google Veo
./image2video.py --backend veo3 "Prompt"

# RunwayML Gen-4
./image2video.py --backend runway "Prompt"
```

### Backend Comparison

| Feature | Sora-2 | Azure Sora | Veo-3 | RunwayML |
|---------|--------|------------|-------|----------|
| **Authentication** | API key | Azure credentials | OAuth2 | API key |
| **Setup Complexity** | Easy | Medium | Complex | Easy |
| **Multiple Images** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Single only |
| **Duration Control** | ✅ Flexible | ✅ Flexible | ✅ Flexible | ⚠️ 5s or 10s only |
| **Multi-Clip Stitching** | ❌ No | ❌ No | ✅ Yes | ✅ Yes (Veo models) |
| **Enterprise Features** | ❌ No | ✅ Yes | ❌ No | ❌ No |
| **Pricing** | Variable | Variable | $0.15-$0.40/video | Variable |

### Choosing the Right Backend

**Use Sora-2 (OpenAI) when:**
- You want the simplest setup (just an API key)
- You need flexible video durations
- You're working with multiple reference images
- You want official OpenAI API access

**Use Azure Sora when:**
- You need enterprise security and compliance
- You're already using Azure services
- You want Azure's billing and governance
- You need RBAC and private endpoints

**Use Veo-3 (Google) when:**
- You need seamless multi-clip stitching
- You want to generate long videos (6+ clips)
- You're comfortable with OAuth2 authentication
- Budget predictability is important ($0.15-$0.40 fixed)

**Use RunwayML when:**
- You want fast turnaround (gen4_turbo)
- You're doing quick iterations or prototypes
- You need access to Veo without Google Cloud setup
- You prefer simple API key authentication

## Model Selection

Each backend offers multiple models optimized for different use cases.

### Listing Available Models

```bash
# Show all models for all backends
./image2video.py --list-models

# Show models for specific backend
./image2video.py --list-models sora2
./image2video.py --list-models veo3
./image2video.py --list-models runway
./image2video.py --list-models azure-sora
```

### Model Characteristics

**Sora-2 (OpenAI/Azure):**
```bash
# Standard quality
./image2video.py --backend sora2 --model sora-2 "Prompt"

# Advanced quality (higher cost)
./image2video.py --backend sora2 --model sora-2-pro "Prompt"
```

**Veo-3 (Google):**
```bash
# Standard quality - $0.40 per video
./image2video.py --backend veo3 --model veo-3.0-generate-001 "Prompt"

# Fast generation - $0.15 per video
./image2video.py --backend veo3 --model veo-3.0-fast-generate-001 "Prompt"

# Veo 3.1 (stitching support) - $0.15 per video
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview "Prompt"
```

**RunwayML Gen-4:**
```bash
# Fast generation (default)
./image2video.py --backend runway --model gen4_turbo "Prompt"

# High quality
./image2video.py --backend runway --model gen4 "Prompt"
```

**RunwayML Veo (Google via Runway):**
```bash
# Veo 3.0 - Standard quality
./image2video.py --backend runway --model veo3 "Prompt"

# Veo 3.1 - Latest quality
./image2video.py --backend runway --model veo3.1 "Prompt"

# Veo 3.1 Fast - Best balance
./image2video.py --backend runway --model veo3.1_fast "Prompt"
```

### Model Selection Tips

**For quick iteration:**
- Use `gen4_turbo` (RunwayML) or `veo-3.0-fast-generate-001` (Veo)
- Lower cost, faster results
- Good for testing prompts and compositions

**For production quality:**
- Use `sora-2-pro` (Sora), `gen4` (RunwayML), or `veo-3.0-generate-001` (Veo)
- Higher quality output
- Better for final deliverables

**For long-form content:**
- Use Veo 3.1 models with `--stitch` flag
- Seamless multi-clip generation
- Automatic frame transitions

## Image Input

The tool supports flexible image input methods.

### Single Image

```bash
./image2video.py -i "photo.jpg" "Prompt"
```

### Multiple Images (Comma-Separated)

```bash
./image2video.py -i "img1.jpg,img2.jpg,img3.jpg" "Prompt"
```

### Wildcard Patterns

```bash
# All JPG files in a directory
./image2video.py -i "photos/*.jpg" "Prompt"

# Multiple patterns
./image2video.py -i "photos/*.jpg,screenshots/*.png" "Prompt"

# Mixed: specific files and patterns
./image2video.py -i "hero.jpg,background/*.png" "Prompt"
```

### Image Order Matters

The AI uses images as spatial and style references. Order them logically:

```bash
# Good: Follows camera path
./image2video.py -i "entrance.jpg,hallway.jpg,living_room.jpg" \
  "A smooth walkthrough from entrance to living room"

# Bad: Random order confuses the model
./image2video.py -i "living_room.jpg,entrance.jpg,hallway.jpg" \
  "A smooth walkthrough from entrance to living room"
```

### Image Best Practices

**Resolution:**
- Minimum: 512x512 pixels
- Recommended: 1080p (1920x1080) or higher
- All images should have similar resolutions

**Format:**
- Supported: JPG, PNG, WebP, and other common formats
- PNG recommended for graphics or screenshots
- JPG recommended for photos

**Content:**
- Clear, well-lit images work best
- Avoid blurry or heavily compressed images
- Images should be relevant to your prompt

**Quantity:**
- Sora/Veo: Use 2-10 images for best results
- RunwayML: Only uses 1 image (first one if multiple provided)

## Video Parameters

### Duration

**Flexible backends** (Sora, Veo):
```bash
./image2video.py --duration 5 "Prompt"   # 5 seconds
./image2video.py --duration 10 "Prompt"  # 10 seconds
./image2video.py --duration 15 "Prompt"  # 15 seconds (if supported)
```

**RunwayML** (fixed durations):
```bash
./image2video.py --backend runway --duration 5 "Prompt"   # 5 seconds
./image2video.py --backend runway --duration 10 "Prompt"  # 10 seconds
# Note: Other values auto-adjust to 5s
```

### Resolution

**Using preset aspect ratios:**
```bash
./image2video.py --width 1920 --height 1080 "Prompt"  # 16:9 landscape
./image2video.py --width 1080 --height 1920 "Prompt"  # 9:16 portrait
./image2video.py --width 1080 --height 1080 "Prompt"  # 1:1 square
```

**Common resolutions:**
- 1920x1080 (1080p landscape)
- 3840x2160 (4K landscape)
- 1080x1920 (1080p portrait, mobile)
- 1080x1080 (square, social media)

**Tips:**
- Higher resolution = longer generation time
- Start with 1080p for testing
- Match your output platform's requirements

### Other Parameters

**Seed (reproducibility):**
```bash
# Same seed + prompt = same output
./image2video.py --seed 12345 "Prompt"
```

**Loop (seamless looping):**
```bash
# Create videos that loop seamlessly
./image2video.py --loop true "Prompt"
```

**Note:** Parameter support varies by backend. Check documentation for specific capabilities.

## Multi-Clip Stitching

Veo 3.1 models support seamless multi-clip generation where each clip's last frame becomes the next clip's first frame.

### Basic Stitching

**Single command for multiple clips:**
```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "reference/*.jpg" \
  -p "Clip 1 prompt" "Clip 2 prompt" "Clip 3 prompt"
```

**How it works:**
1. Generates clip 1 using reference images
2. Extracts last frame from clip 1
3. Generates clip 2 using last frame + reference images
4. Repeats for all clips
5. Outputs: `veo3_clip_1.mp4`, `veo3_clip_2.mp4`, etc.

### Concatenating Clips

**Combine clips into final video:**
```bash
# Method 1: Direct concatenation (fast, no re-encoding)
ffmpeg -i "concat:veo3_clip_1.mp4|veo3_clip_2.mp4|veo3_clip_3.mp4" \
  -c copy final_video.mp4

# Method 2: Using concat demuxer (more reliable)
printf "file 'veo3_clip_1.mp4'\nfile 'veo3_clip_2.mp4'\nfile 'veo3_clip_3.mp4'\n" > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy final_video.mp4
```

### Text-Only Stitching

No reference images required:
```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -p "A serene lake at dawn" \
     "The sun rises over the mountains" \
     "Birds fly across the water" \
     "The morning mist clears"
```

### Python API for Stitching

For programmatic control:
```python
from video_gen.video_generator import generate_video_sequence_with_veo3_stitching

prompts = [
    "Entrance hall with staircase",
    "Pan left to living room with sofas",
    "Show kitchen area with island",
    "Final view through window"
]

# Option 1: Same reference images for all clips
file_paths_list = [["ref1.jpg", "ref2.jpg"]] * len(prompts)

# Option 2: Different images per clip
file_paths_list = [
    ["entrance1.jpg", "entrance2.jpg"],
    ["living1.jpg", "living2.jpg"],
    ["kitchen.jpg"],
    ["window.jpg"]
]

outputs = generate_video_sequence_with_veo3_stitching(
    prompts=prompts,
    file_paths_list=file_paths_list,
    width=1280,
    height=720,
    duration_seconds=7,
    model="veo-3.1-fast-generate-preview"
)

print(f"Generated {len(outputs)} seamless clips")
```

See **[Advanced Stitching Guide](advanced/stitching.md)** for detailed techniques.

## Command-Line Options

### Complete Options Reference

```bash
./image2video.py [OPTIONS] "PROMPT"
```

**Required:**
- `PROMPT` - Text description of the video to generate

**Image Input:**
- `-i, --images PATH` - Image files (comma-separated, wildcards, or mixed)

**Backend Selection:**
- `--backend {sora2|azure-sora|veo3|runway}` - Choose AI provider (default: sora2)
- `--model MODEL_NAME` - Specific model within backend
- `--list-models [BACKEND]` - List available models

**Video Parameters:**
- `--duration SECONDS` - Video length (5-15s, backend dependent)
- `--width PIXELS` - Output width (default: 1920)
- `--height PIXELS` - Output height (default: 1080)
- `--seed NUMBER` - Random seed for reproducibility
- `--loop true|false` - Create seamless looping video

**Multi-Clip (Veo 3.1):**
- `--stitch` - Enable multi-clip stitching mode
- `-p, --prompts "P1" "P2" ...` - Multiple prompts (one per clip)

**Authentication:**
- `--google-login` - Launch browser for Veo OAuth2 authentication

**Utility:**
- `-h, --help` - Show help message
- `--version` - Show version information

### Example Commands

**Basic generation:**
```bash
./image2video.py "A cat playing with a ball of yarn"
```

**With images:**
```bash
./image2video.py -i "cat.jpg" "The cat chasing the yarn ball"
```

**Specific backend and model:**
```bash
./image2video.py --backend runway --model gen4_turbo \
  -i "scene.jpg" "Cinematic pan across the landscape"
```

**Custom resolution:**
```bash
./image2video.py --width 3840 --height 2160 \
  "Ultra HD view of the mountains"
```

**Multi-clip stitching:**
```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "refs/*.jpg" \
  -p "Opening shot" "Middle transition" "Final reveal"
```

## Configuration

### Environment Variables

For a full configuration matrix per backend, see Reference: [Environment Variables](reference/environment-variables.md).

The tool reads configuration from environment variables and `.env` files.

**Create `.env` file:**
```bash
# OpenAI Sora
OPENAI_API_KEY=sk-proj-xxxxx

# Azure Sora
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-01-preview

# Google Veo (project ID required)
GOOGLE_CLOUD_PROJECT=your-project-id
# Note: GOOGLE_API_KEY obtained via gcloud or --google-login

# RunwayML
RUNWAY_API_KEY=your-runway-key
RUNWAY_MODEL=gen4_turbo  # Optional default model
```

**Or export directly:**
```bash
export OPENAI_API_KEY="sk-proj-xxxxx"
export RUNWAY_API_KEY="your-key"
```

### Per-Backend Configuration

**Sora-2:**
- Only requires `OPENAI_API_KEY`
- Works with standard OpenAI API

**Azure Sora:**
- Requires `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT`
- Optionally set `AZURE_OPENAI_API_VERSION` (defaults to 2024-10-01-preview)

**Veo-3:**
- **Must set** `GOOGLE_CLOUD_PROJECT` (project ID)
- Token via `--google-login` (recommended) or `gcloud auth`
- Tokens expire after 1 hour

**RunwayML:**
- Only requires `RUNWAY_API_KEY`
- Optionally set `RUNWAY_MODEL` for default model

### Configuration Priority

1. Command-line arguments (highest priority)
2. Environment variables
3. `.env` file
4. Default values (lowest priority)

**Example:**
```bash
# .env file has: RUNWAY_MODEL=gen4
# Environment has: export RUNWAY_MODEL=gen4_turbo
# Command-line: --model gen4

# Result: Uses gen4 (command-line wins)
```

## Best Practices

### Prompt Engineering

**Be specific:**
```bash
# Bad: Vague
./image2video.py "A video of a house"

# Good: Detailed
./image2video.py "Smooth dolly shot through a modern living room, \
  panning left to reveal floor-to-ceiling windows with city views"
```

**Include camera movements:**
- "Slow pan right"
- "Dolly forward"
- "Static shot"
- "Smooth tracking shot"
- "Crane up"

**Specify timing:**
- "Hold for 3 seconds"
- "Slow pan over 5 seconds"
- "Quick dolly in 2 seconds"

**Mention lighting and mood:**
- "Warm afternoon lighting"
- "Dramatic shadows"
- "Soft diffused light"
- "Golden hour glow"

### Multi-Image Strategy

**Spatial references:**
- Order images to match camera path
- Use images from different angles
- Include key landmarks in multiple images

**Style consistency:**
- Use images with similar lighting
- Match color grading across images
- Consistent time of day

### Cost Optimization

**Testing phase:**
- Use fast models (gen4_turbo, veo-3.0-fast)
- Generate at lower resolution (720p)
- Test with single images first

**Production phase:**
- Switch to quality models for final output
- Generate at target resolution
- Use multiple reference images

**Veo stitching:**
- Plan clips carefully before generation
- Each clip costs $0.15-$0.40
- 6 clips = $0.90-$2.40 total

### Quality Tips

**Image preparation:**
- Use high-resolution source images (1080p+)
- Ensure good lighting in reference photos
- Avoid blurry or compressed images

**Duration:**
- Shorter clips (5-7s) often have better consistency
- Longer clips risk drift or artifacts
- Use stitching for extended sequences

**Resolution:**
- Start at 1080p (1920x1080)
- Increase to 4K only when needed
- Higher resolution = longer generation time

## Examples

### Example 1: Simple Product Showcase

```bash
./image2video.py --backend runway --model gen4_turbo \
  -i "product_hero.jpg" \
  "360 degree rotation of the product on a white background, \
   soft studio lighting, smooth continuous motion"
```

### Example 2: Real Estate Walkthrough (Multi-Clip)

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "entrance.jpg,living.jpg,kitchen.jpg,bedroom.jpg" \
  -p "Slow dolly through the entrance hall toward the living room" \
     "Pan left across the living room showing modern furniture and windows" \
     "Smooth transition into the kitchen with island and appliances" \
     "Final pan right revealing the master bedroom with king bed"

# Combine clips
ffmpeg -i "concat:veo3_clip_1.mp4|veo3_clip_2.mp4|veo3_clip_3.mp4|veo3_clip_4.mp4" \
  -c copy house_tour.mp4
```

### Example 3: Social Media Content

```bash
./image2video.py --backend sora2 --model sora-2 \
  --width 1080 --height 1920 \
  -i "before.jpg,after.jpg" \
  "Smooth transition from before to after, revealing the transformation, \
   upbeat and energetic feel"
```

### Example 4: Artistic Vision

```bash
./image2video.py --backend veo3 --model veo-3.0-generate-001 \
  -i "artwork/*.jpg" \
  "A dream-like journey through surreal landscapes, \
   floating camera movement, ethereal lighting, \
   transitions between scenes like watercolor paintings blending"
```

### Example 5: Batch Processing

```bash
#!/bin/bash
# Generate videos for all images in a directory

for img in photos/*.jpg; do
  prompt="Cinematic reveal of the landscape, slow pan right, golden hour lighting"
  ./image2video.py --backend runway --model gen4_turbo -i "$img" "$prompt"
done
```

### Example 6: High-Quality Production

```bash
./image2video.py --backend sora2 --model sora-2-pro \
  --width 3840 --height 2160 \
  --duration 10 \
  -i "hero_shot_1.jpg,hero_shot_2.jpg,hero_shot_3.jpg" \
  "Epic establishing shot of the mountain range at sunrise, \
   slow crane up revealing the peaks, \
   cinematic color grading, atmospheric haze, \
   hold on the summit for 3 seconds"
```

## Next Steps

- 📖 **[Backend Guides](backends/)** - Detailed setup for each provider
- 🎨 **[Prompt Engineering](advanced/prompts.md)** - Master prompt writing
- 🔗 **[Stitching Guide](advanced/stitching.md)** - Advanced multi-clip techniques
- 🔧 **[Troubleshooting](advanced/troubleshooting.md)** - Solve common issues
- 💻 **[API Reference](technical/api-reference.md)** - Programmatic usage

---

**Have questions?** Check the **[Troubleshooting Guide](advanced/troubleshooting.md)** or review **[Installation](installation.md)** if you're having setup issues.
