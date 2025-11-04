# OpenAI Sora Backend Guide

Complete guide to using OpenAI's Sora-2 video generation models directly via OpenAI API.

## Overview

OpenAI's Sora-2 is a cutting-edge video generation model that creates high-quality videos from text prompts and images. Key features:

- **High-quality output** with excellent motion understanding
- **Flexible parameters** for duration, resolution, and aspect ratio
- **Multiple reference images** support
- **Simple authentication** with API key
- **Direct OpenAI API access** (official source)

## Prerequisites

- **OpenAI Account**: Create account at [platform.openai.com](https://platform.openai.com/)
- **API Key**: Generate from API Keys section
- **Credits**: Sora requires paid credits (not available on free tier)

## Authentication Setup

### Getting Your API Key

1. **Sign up/Login**: Visit [platform.openai.com](https://platform.openai.com/)
2. **Navigate to API Keys**: Click your profile → "View API keys"
3. **Create new key**: Click "Create new secret key"
4. **Save securely**: Copy the key (it won't be shown again)

### Configuration

**Method 1: Environment Variable**

```bash
# Set for current session
export OPENAI_API_KEY="sk-proj-xxxxx"

# Add to shell profile for persistence
echo 'export OPENAI_API_KEY="sk-proj-xxxxx"' >> ~/.zshrc
source ~/.zshrc
```

**Method 2: .env File (Recommended)**

```bash
# Create or edit .env file in project root
echo "OPENAI_API_KEY=sk-proj-xxxxx" >> .env
```

**Method 3: Direct in Command**

```bash
OPENAI_API_KEY="sk-proj-xxxxx" ./image2video.py "Your prompt"
```

### Verify Setup

```bash
# Test configuration
./image2video.py --backend sora2 --list-models

# Expected output:
# Available models for backend 'sora2':
#   - sora-2 (default)
#   - sora-2-pro
```

## Available Models

OpenAI offers two Sora-2 models with different quality/cost tradeoffs:

### sora-2 (Standard)

```bash
./image2video.py --backend sora2 --model sora-2 \
  -i "image.jpg" "Your prompt"
```

**Characteristics:**
- **Quality**: High quality video generation
- **Speed**: Standard generation time (~2-5 minutes)
- **Pricing**: Standard rate
- **Best for**: Most use cases, balanced quality/cost

### sora-2-pro (Advanced)

```bash
./image2video.py --backend sora2 --model sora-2-pro \
  -i "image.jpg" "Your prompt"
```

**Characteristics:**
- **Quality**: Superior quality with enhanced detail
- **Speed**: Standard generation time (~2-5 minutes)
- **Pricing**: Premium rate
- **Best for**: High-end production, client work

### Model Selection

```bash
# Use default model (sora-2)
./image2video.py --backend sora2 "Prompt"

# Explicitly select standard
./image2video.py --backend sora2 --model sora-2 "Prompt"

# Use pro model
./image2video.py --backend sora2 --model sora-2-pro "Prompt"
```

**When to use sora-2-pro:**
- Final production deliverables
- Client-facing content
- High-resolution output requirements
- Complex scenes with fine details

**When to use sora-2:**
- Development and testing
- Internal content
- Quick iterations
- Budget-conscious projects

## Basic Usage

### Text-to-Video

Generate video from text prompt only:

```bash
./image2video.py --backend sora2 \
  "A serene lake at sunset with gentle waves lapping at the shore"
```

### Image-to-Video

Generate video using reference images:

```bash
# Single image
./image2video.py --backend sora2 \
  -i "landscape.jpg" \
  "Slow pan across the mountains at golden hour"

# Multiple images (recommended for better results)
./image2video.py --backend sora2 \
  -i "angle1.jpg,angle2.jpg,angle3.jpg" \
  "Smooth camera movement revealing the scene"
```

### With Model Selection

```bash
# Standard model
./image2video.py --backend sora2 --model sora-2 \
  -i "photo.jpg" "Quick test prompt"

# Pro model for production
./image2video.py --backend sora2 --model sora-2-pro \
  -i "hero_image.jpg" "Cinematic reveal with dramatic lighting"
```

## Video Parameters

### Duration

Sora-2 supports flexible video durations:

```bash
# Short clip (5 seconds)
./image2video.py --backend sora2 --duration 5 "Quick action sequence"

# Medium clip (10 seconds)
./image2video.py --backend sora2 --duration 10 "Standard scene"

# Longer clip (20 seconds)
./image2video.py --backend sora2 --duration 20 "Extended cinematic shot"
```

**Recommendations:**
- **5-10s**: Best quality, most consistent
- **10-15s**: Good balance
- **15-20s**: Maximum length, may have more variance
- **20s+**: Check current model limits (may require splitting)

### Resolution

Control output resolution and aspect ratio:

```bash
# 1080p landscape (default, 16:9)
./image2video.py --backend sora2 \
  --width 1920 --height 1080 "Prompt"

# 4K landscape (16:9)
./image2video.py --backend sora2 \
  --width 3840 --height 2160 "Prompt"

# 1080p portrait (9:16, mobile)
./image2video.py --backend sora2 \
  --width 1080 --height 1920 "Prompt"

# Square (1:1, social media)
./image2video.py --backend sora2 \
  --width 1080 --height 1080 "Prompt"

# Cinema (2.39:1)
./image2video.py --backend sora2 \
  --width 2048 --height 858 "Prompt"
```

**Common resolutions:**

| Format | Resolution | Aspect Ratio | Best For |
|--------|-----------|--------------|----------|
| 1080p Landscape | 1920x1080 | 16:9 | General use, YouTube |
| 4K Landscape | 3840x2160 | 16:9 | High quality, TV |
| 1080p Portrait | 1080x1920 | 9:16 | Instagram, TikTok |
| Square | 1080x1080 | 1:1 | Instagram feed |
| Cinema | 2048x858 | 2.39:1 | Cinematic look |

### Seed (Reproducibility)

Use seed for consistent results:

```bash
# Generate with seed
./image2video.py --backend sora2 --seed 42 \
  -i "reference.jpg" "Specific camera movement"

# Same seed + same prompt = same result
./image2video.py --backend sora2 --seed 42 \
  -i "reference.jpg" "Specific camera movement"
```

**Use cases:**
- A/B testing different prompts
- Iterating on a specific generation
- Creating variations with controlled randomness
- Reproducible results for clients

## Image Input

### Single Image

```bash
./image2video.py --backend sora2 \
  -i "hero_shot.jpg" \
  "Dramatic zoom in on the subject with cinematic lighting"
```

### Multiple Images (Recommended)

Using multiple images helps Sora understand:
- **Spatial layout** from different angles
- **Style consistency** across views
- **Key elements** to maintain
- **Camera paths** that work well

```bash
./image2video.py --backend sora2 \
  -i "front.jpg,side.jpg,detail.jpg" \
  "360 degree rotation revealing all angles"
```

**Best practices:**
- Use 2-5 images for best results
- Include different angles of the same subject
- Maintain consistent lighting across images
- Order matters: arrange in sequence you want camera to follow

### Wildcards and Patterns

```bash
# All images in directory
./image2video.py --backend sora2 \
  -i "reference_images/*.jpg" \
  "Smooth walkthrough of the space"

# Multiple directories
./image2video.py --backend sora2 \
  -i "living_room/*.jpg,kitchen/*.png" \
  "Tour from living room to kitchen"

# Mixed: specific files and wildcards
./image2video.py --backend sora2 \
  -i "hero.jpg,supporting/*.jpg" \
  "Start with hero image, then reveal supporting elements"
```

## Prompt Engineering

### Camera Movements

Explicitly describe camera behavior:

```bash
# Pan
./image2video.py --backend sora2 \
  "Slow pan from left to right across the landscape"

# Dolly
./image2video.py --backend sora2 \
  "Smooth dolly forward through the forest path"

# Crane
./image2video.py --backend sora2 \
  "Crane up from ground level to reveal the city skyline"

# Static
./image2video.py --backend sora2 \
  "Static shot with subtle natural movement"

# Complex movement
./image2video.py --backend sora2 \
  "Start with slow pan right, then dolly forward while panning left"
```

### Timing and Holds

Control pacing within your prompt:

```bash
./image2video.py --backend sora2 --duration 15 \
  "Open on the entrance hall. Hold for 3 seconds. \
   Slow pan right revealing the staircase. Hold for 2 seconds. \
   Dolly forward into the living area over 5 seconds. \
   Final pan left to the windows. Hold for remaining duration."
```

### Lighting and Atmosphere

Describe mood and lighting:

```bash
# Time of day
./image2video.py --backend sora2 \
  "Golden hour lighting with warm sun rays through trees"

# Lighting style
./image2video.py --backend sora2 \
  "Soft diffused lighting, professional studio setup, no harsh shadows"

# Atmosphere
./image2video.py --backend sora2 \
  "Moody atmospheric lighting with dramatic shadows and fog"

# Technical specs
./image2video.py --backend sora2 \
  "Cinematic lighting, 24mm lens, f/2.8, natural color grading"
```

### Style and Quality

Describe the visual style you want:

```bash
# Cinematic
./image2video.py --backend sora2 \
  "Cinematic film look, professional color grading, \
   shallow depth of field, bokeh in background"

# Documentary
./image2video.py --backend sora2 \
  "Documentary style handheld camera, natural lighting, \
   subtle movements, authentic feel"

# Commercial
./image2video.py --backend sora2 \
  "High-end commercial look, perfect exposure, \
   smooth gimbal movement, pristine quality"
```

## Advanced Features

### Loop Parameter

Create seamlessly looping videos:

```bash
./image2video.py --backend sora2 --loop true \
  "Gentle ocean waves that loop seamlessly"
```

**Best for:**
- Background videos
- Ambient content
- Social media loops
- Video wallpapers

### High-Resolution Output

Generate in 4K for maximum quality:

```bash
./image2video.py --backend sora2 --model sora-2-pro \
  --width 3840 --height 2160 \
  --duration 10 \
  -i "high_res_reference.jpg" \
  "Ultra high definition cinematic shot with perfect clarity"
```

**Note:** Higher resolution = longer generation time and higher cost

### Batch Generation

Generate multiple videos with variations:

```bash
#!/bin/bash
# Generate variations with different seeds

PROMPT="Cinematic dolly shot through forest"
IMAGE="forest_ref.jpg"

for seed in {1..5}; do
  ./image2video.py --backend sora2 \
    --seed $seed \
    -i "$IMAGE" \
    "$PROMPT"
done
```

## Pricing

Sora-2 pricing is based on video generation:

- **Pricing model**: Per-second of generated video
- **Model tiers**: sora-2 (standard) vs sora-2-pro (premium)
- **Resolution impact**: Higher resolution may cost more
- **Duration impact**: Longer videos cost proportionally more

**Check current pricing:**
- Visit [OpenAI Pricing](https://openai.com/pricing)
- Check your [usage dashboard](https://platform.openai.com/usage)

**Cost optimization tips:**
- Use sora-2 (standard) for testing
- Generate shorter clips (5-10s) during iteration
- Use lower resolution (1080p) for testing
- Switch to sora-2-pro + 4K only for final output

## Troubleshooting

### Authentication Issues

**Error: "Invalid API key"**
```bash
# Check your API key is set
echo $OPENAI_API_KEY

# Should output: sk-proj-xxxxx
# If empty, set it:
export OPENAI_API_KEY="sk-proj-xxxxx"
```

**Error: "API key not found"**
```bash
# Ensure .env file exists and is properly formatted
cat .env

# Should contain:
# OPENAI_API_KEY=sk-proj-xxxxx

# If missing, create it:
echo "OPENAI_API_KEY=sk-proj-xxxxx" > .env
```

### Generation Issues

**Error: "Insufficient credits"**
- Add payment method: [OpenAI Billing](https://platform.openai.com/account/billing)
- Check usage: [Usage Dashboard](https://platform.openai.com/usage)
- Sora requires paid credits (not available on free tier)

**Error: "Model not found: sora-2"**
- Sora access may be limited or require waitlist
- Check [OpenAI Status](https://status.openai.com/)
- Verify your account has Sora access

**Slow generation**
- Sora-2 typically takes 2-5 minutes
- Longer videos take more time
- Higher resolution increases generation time
- This is normal - just wait for completion

**Generation stalls at capacity**
```bash
# The script has automatic retry logic
# Just wait - it will retry with exponential backoff
# Press Ctrl+C to cancel if needed
```

### Quality Issues

**Video doesn't match prompt**
- Be more specific in your prompt
- Add camera movement details
- Specify lighting and mood
- Include timing information

**Inconsistent motion**
- Use multiple reference images from different angles
- Describe camera path explicitly
- Reduce duration (shorter clips are more consistent)
- Try different seed values

**Reference images ignored**
- Ensure images are high resolution
- Use 2-5 images instead of just 1
- Order images to match desired camera path
- Describe connection between images in prompt

## Best Practices

### Image Preparation

**Resolution:**
- Minimum 1080p (1920x1080)
- Preferably 4K source images
- All images should be similar resolution

**Quality:**
- Well-lit, clear images
- Avoid compression artifacts
- No watermarks or overlays
- Sharp focus on key elements

**Composition:**
- Show scene from multiple angles
- Include key elements you want in video
- Consistent lighting across images
- Professional photography quality when possible

### Prompt Strategy

**Structure your prompt:**
1. **Setup**: Describe the scene
2. **Camera**: Specify movement
3. **Timing**: Include holds and pacing
4. **Style**: Lighting, mood, quality

**Example:**
```bash
./image2video.py --backend sora2 \
  "Modern living room with floor-to-ceiling windows. \
   Start on the entrance, hold 2 seconds. \
   Smooth dolly forward while panning left, revealing the sofas and TV. \
   Hold on the main seating area for 3 seconds. \
   Golden hour lighting, cinematic look, professional color grading."
```

### Development Workflow

**1. Testing phase:**
```bash
# Use standard model, lower resolution, shorter duration
./image2video.py --backend sora2 --model sora-2 \
  --width 1280 --height 720 \
  --duration 5 \
  -i "test.jpg" "Test prompt"
```

**2. Refinement:**
```bash
# Iterate on prompts with same seed
./image2video.py --backend sora2 --seed 42 \
  -i "refs/*.jpg" "Refined prompt v1"

./image2video.py --backend sora2 --seed 42 \
  -i "refs/*.jpg" "Refined prompt v2"
```

**3. Production:**
```bash
# Final generation with pro model, full resolution
./image2video.py --backend sora2 --model sora-2-pro \
  --width 3840 --height 2160 \
  --duration 15 \
  -i "final_refs/*.jpg" "Final production prompt"
```

## Examples

### Example 1: Product Showcase

```bash
./image2video.py --backend sora2 --model sora-2-pro \
  --width 1920 --height 1080 \
  --duration 10 \
  -i "product_white_bg.jpg,product_angle2.jpg" \
  "Smooth 360 degree rotation of product on white background. \
   Professional studio lighting with soft shadows. \
   Product stays centered throughout. \
   Slow, elegant movement. Clean and minimal."
```

### Example 2: Real Estate

```bash
./image2video.py --backend sora2 \
  --width 3840 --height 2160 \
  --duration 20 \
  -i "entrance.jpg,living.jpg,kitchen.jpg,bedroom.jpg" \
  "Luxury home walkthrough. Start in grand entrance foyer with chandelier. \
   Slow dolly forward into open concept living room with floor-to-ceiling windows. \
   Pan left revealing gourmet kitchen with marble island. \
   Continue to master suite with king bed and city views. \
   Natural lighting throughout. Smooth, professional camera work. \
   High-end real estate style."
```

### Example 3: Nature Scene

```bash
./image2video.py --backend sora2 --model sora-2-pro \
  --width 1920 --height 1080 \
  --duration 15 \
  -i "forest_path.jpg" \
  "Slow dolly forward through misty forest path at dawn. \
   Dappled sunlight filtering through tall trees. \
   Gentle breeze moving leaves and fog. \
   Birds flying in distance. \
   Peaceful, serene atmosphere. \
   Cinematic nature documentary style. \
   Shallow depth of field with soft bokeh."
```

### Example 4: Social Media Content

```bash
./image2video.py --backend sora2 \
  --width 1080 --height 1920 \
  --duration 5 \
  --loop true \
  -i "product_lifestyle.jpg" \
  "Quick zoom in on product in lifestyle setting. \
   Vibrant colors, energetic feel. \
   Perfect for Instagram stories. \
   Seamless loop."
```

## Additional Resources

- 🎨 **[Prompt Engineering Guide](../advanced/prompts.md)**
- 📖 **[User Guide](../user-guide.md)**
- 🔧 **[Troubleshooting Guide](../advanced/troubleshooting.md)**
- 📚 **[OpenAI Documentation](https://platform.openai.com/docs)**

## External Links

- [OpenAI Platform](https://platform.openai.com/)
- [Sora Documentation](https://openai.com/sora)
- [API Reference](https://platform.openai.com/docs/api-reference)
- [Pricing Information](https://openai.com/pricing)
- [Usage Dashboard](https://platform.openai.com/usage)

---

**Need help?** Check the **[Troubleshooting Guide](../advanced/troubleshooting.md)** or visit the **[OpenAI Help Center](https://help.openai.com/)**.
