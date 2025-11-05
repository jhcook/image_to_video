# RunwayML Backend Guide

Complete guide to using RunwayML's Gen-4 and Google Veo models through RunwayML's API.

## Overview

RunwayML provides access to both their own Gen-4 models and Google's Veo models through a unified API. Key features:

- **Simple authentication** with API key only
- **Gen-4 models**: Fast turnaround with turbo option
- **Veo models**: Access Google Veo without Google Cloud setup
- **Stitching support**: Seamless multi-clip videos with Veo models
- **Flexible pricing**: Pay-as-you-go credit system

## Prerequisites

- **RunwayML Account**: Sign up at [runwayml.com](https://runwayml.com/)
- **API Key**: Generate from account settings
- **Credits**: Purchase RunwayML credits for generation

## Authentication Setup

### Getting Your API Key

1. **Sign up/Login**: Visit [runwayml.com](https://runwayml.com/)
2. **Navigate to Settings**: Click profile → Settings
3. **API Section**: Go to API settings
4. **Generate Key**: Click "Generate API Key"
5. **Copy Key**: Save your key securely

### Configuration

**Method 1: .env File (Recommended)**

```bash
# Create or edit .env file
echo "RUNWAY_API_KEY=your-runway-api-key" >> .env

# Optional: Set default model
echo "RUNWAY_MODEL=gen4_turbo" >> .env
```

**Method 2: Environment Variable**

```bash
# Set for current session
export RUNWAY_API_KEY="your-runway-api-key"

# Add to shell profile for persistence
echo 'export RUNWAY_API_KEY="your-runway-api-key"' >> ~/.zshrc
source ~/.zshrc
```

**Method 3: Direct in Command**

```bash
RUNWAY_API_KEY="your-key" ./image2video.py --backend runway "Prompt"
```

### Verify Setup

```bash
# Test configuration
./image2video.py --backend runway --list-models

# Expected output:
# Available models for backend 'runway':
#   - gen4_turbo (default)
#   - gen4
#   - veo3
#   - veo3.1
#   - veo3.1_fast
```

## Available Models

RunwayML offers two model families: Gen-4 (RunwayML's own) and Veo (Google's via Runway).

### Gen-4 Models (RunwayML Native)

**gen4_turbo** (Default, Recommended)
- **Quality**: Good quality, optimized for speed
- **Speed**: Fast (~1-2 minutes)
- **Duration**: 5 or 10 seconds only
- **Pricing**: ~20-30 credits/sec (1 credit = $0.01)
- **Best for**: Quick iterations, testing, social media

```bash
./image2video.py --backend runway --model gen4_turbo \
  -i "photo.jpg" "Quick generation prompt"
```

**gen4**
- **Quality**: High quality, maximum detail
- **Speed**: Standard (~2-4 minutes)
- **Duration**: 5 or 10 seconds only
- **Pricing**: ~40-50 credits/sec
- **Best for**: Production quality, client work

```bash
./image2video.py --backend runway --model gen4 \
  -i "photo.jpg" "High quality production prompt"
```

### Veo Models (Google via RunwayML)

RunwayML now provides Google's Veo models with simpler authentication!

**veo3**
- **Quality**: High quality (Google Veo 3.0)
- **Speed**: Standard (~2-4 minutes)
- **Duration**: 2-10 seconds
- **Stitching**: ✅ Supported
- **Pricing**: ~40 credits/sec ($0.40/sec)
- **Best for**: High-quality videos without Google Cloud setup

```bash
./image2video.py --backend runway --model veo3 \
  -i "ref1.jpg,ref2.jpg,ref3.jpg" "Veo 3.0 prompt"
```

**veo3.1** (Latest)
- **Quality**: Excellent (Google Veo 3.1)
- **Speed**: Standard (~2-4 minutes)
- **Duration**: 2-10 seconds
- **Stitching**: ✅ Supported
- **Pricing**: ~40 credits/sec ($0.40/sec)
- **Best for**: Maximum quality with stitching

```bash
./image2video.py --backend runway --model veo3.1 \
  -i "refs/*.jpg" "Veo 3.1 prompt"
```

**veo3.1_fast** (Recommended for Veo)
- **Quality**: Excellent (Google Veo 3.1 Fast)
- **Speed**: Fast (~1-2 minutes)
- **Duration**: 2-10 seconds
- **Stitching**: ✅ Supported
- **Pricing**: ~20 credits/sec ($0.20/sec)
- **Best for**: Best balance of quality, speed, and cost

```bash
./image2video.py --backend runway --model veo3.1_fast \
  -i "refs/*.jpg" "Fast Veo 3.1 prompt"
```

## Basic Usage

### Text-to-Video

```bash
# Gen-4 Turbo (default)
./image2video.py --backend runway \
  "A peaceful mountain landscape at sunrise"

# Veo model
./image2video.py --backend runway --model veo3.1_fast \
  "Cinematic shot of ocean waves"
```

### Image-to-Video

```bash
# Gen-4: Single image only
./image2video.py --backend runway --model gen4_turbo \
  -i "photo.jpg" "Slow zoom on the subject"

# Veo: Multiple reference images (up to 3)
./image2video.py --backend runway --model veo3.1_fast \
  -i "img1.jpg,img2.jpg,img3.jpg" "Smooth camera movement"
```

**Important:** Gen-4 models only support **one image**. If you provide multiple, only the first is used. Veo models support up to **3 reference images**.

## Model-Specific Features

### Gen-4 Models

**Duration restrictions:**
- **Only 5 or 10 seconds** supported
- Script auto-adjusts to 5s if you specify other values

```bash
# Automatically adjusted to 5s
./image2video.py --backend runway --duration 7 "Prompt"

# Explicitly set 10s
./image2video.py --backend runway --duration 10 "Prompt"
```

**promptImage parameter:**
- Gen-4 uses single reference image for style
- Image influences the generation but isn't the first frame

```bash
# Image as style reference
./image2video.py --backend runway --model gen4 \
  -i "style_ref.jpg" "Generate in this style"
```

**Seed parameter:**
- Control reproducibility with seed

```bash
./image2video.py --backend runway --model gen4_turbo \
  --seed 12345 "Reproducible generation"
```

### Veo Models

**Multiple reference images:**
- Up to 3 images for style and content guidance
- Images passed via `referenceImages` parameter

```bash
./image2video.py --backend runway --model veo3.1_fast \
  -i "angle1.jpg,angle2.jpg,angle3.jpg" "Multi-angle prompt"
```

**firstKeyframe and lastKeyframe:**
- Control start and end frames explicitly
- Useful for seamless stitching

```bash
# Python API example
from video_gen.providers.runway_provider import RunwayVeoClient

client = RunwayVeoClient(config)
result = client.generate_video(
    prompt="Your prompt",
    firstKeyframe="path/to/start.jpg",  # First frame
    lastKeyframe="path/to/end.jpg",     # Last frame
    referenceImages=["ref1.jpg", "ref2.jpg"]
)
```

**Flexible duration:**
- Veo supports 2-10 seconds

```bash
./image2video.py --backend runway --model veo3.1_fast \
  --duration 7 "Seven second clip"
```

## Multi-Clip Stitching (Veo Models Only)

Veo models through RunwayML support seamless multi-clip stitching.

### Basic Stitching

```bash
./image2video.py --backend runway --model veo3.1_fast --stitch \
  -i "ref1.jpg,ref2.jpg" \
  -p "First clip movement" \
     "Second clip movement" \
     "Third clip movement"
```

**How it works:**
1. Generates clip 1 with reference images
2. Extracts last frame from clip 1
3. Uses last frame as `firstKeyframe` for clip 2
4. Reference images provided to all clips
5. Repeats for remaining clips

**Output:**
- `runway_clip_1.mp4`
- `runway_clip_2.mp4`
- `runway_clip_3.mp4`

### Concatenating Clips

```bash
# Combine into final video
ffmpeg -i "concat:runway_clip_1.mp4|runway_clip_2.mp4|runway_clip_3.mp4" \
  -c copy final_video.mp4
```

### Real Estate Example

```bash
./image2video.py --backend runway --model veo3.1_fast --stitch \
  --duration 7 \
  -i "foyer.jpg,living.jpg,kitchen.jpg" \
  -p "Start in foyer, slow pan right revealing stairs" \
     "Dolly into living room, pan left to sofas and TV" \
     "Continue to kitchen, pan across island and appliances" \
     "Final shot through window with view"

# Cost: 4 clips × 7s × $0.20/sec = $5.60 total

# Concatenate
ffmpeg -i "concat:runway_clip_1.mp4|runway_clip_2.mp4|runway_clip_3.mp4|runway_clip_4.mp4" \
  -c copy house_tour.mp4
```

### Python API for Stitching

```python
from video_gen.video_generator import generate_video_sequence_with_runway_stitching

prompts = [
    "Entrance hall with grand staircase",
    "Pan left into spacious living room",
    "Continue to gourmet kitchen",
    "Final view out window"
]

# Same reference images for all clips
file_paths = [["ref1.jpg", "ref2.jpg", "ref3.jpg"]] * len(prompts)

outputs = generate_video_sequence_with_runway_stitching(
    prompts=prompts,
    file_paths_list=file_paths,
    width=1280,
    height=720,
    duration_seconds=7,
    model="veo3.1_fast"
)

print(f"Generated {len(outputs)} clips")
# Returns: ["runway_clip_1.mp4", "runway_clip_2.mp4", ...]
```

## Video Parameters

### Duration

**Gen-4 models:**
```bash
# Only 5 or 10 seconds
./image2video.py --backend runway --model gen4_turbo --duration 5 "Prompt"
./image2video.py --backend runway --model gen4_turbo --duration 10 "Prompt"

# Other values auto-adjust to 5s
./image2video.py --backend runway --model gen4 --duration 7 "Prompt"  # → 5s
```

**Veo models:**
```bash
# Flexible 2-10 seconds
./image2video.py --backend runway --model veo3.1_fast --duration 3 "Prompt"
./image2video.py --backend runway --model veo3.1_fast --duration 7 "Prompt"
./image2video.py --backend runway --model veo3.1_fast --duration 10 "Prompt"
```

### Resolution

Standard resolutions supported:

```bash
# 1080p landscape (default)
./image2video.py --backend runway --width 1920 --height 1080 "Prompt"

# 1080p portrait
./image2video.py --backend runway --width 1080 --height 1920 "Prompt"

# 720p
./image2video.py --backend runway --width 1280 --height 720 "Prompt"

# Square
./image2video.py --backend runway --width 1080 --height 1080 "Prompt"
```

### Default Model

Set default model via environment:

```bash
# In .env file
RUNWAY_MODEL=veo3.1_fast

# Or export
export RUNWAY_MODEL=veo3.1_fast

# Then just:
./image2video.py --backend runway "Prompt"  # Uses veo3.1_fast
```

## Pricing

RunwayML uses a credit-based system:
- **1 credit = $0.01 USD**
- Charged per second of generated video
- Different models have different rates

### Pricing Table

| Model | Credits/Second | USD/Second | 5s Video | 10s Video |
|-------|---------------|------------|----------|-----------|
| **gen4_turbo** | 20-30 | $0.20-$0.30 | $1.00-$1.50 | $2.00-$3.00 |
| **gen4** | 40-50 | $0.40-$0.50 | $2.00-$2.50 | $4.00-$5.00 |
| **veo3** | ~40 | ~$0.40 | $2.00 | $4.00 |
| **veo3.1** | ~40 | ~$0.40 | $2.00 | $4.00 |
| **veo3.1_fast** | ~20 | ~$0.20 | $1.00 | $2.00 |

**Multi-clip stitching costs:**
- 4 clips × 7s × $0.20/sec = $5.60
- 6 clips × 7s × $0.20/sec = $8.40
- Plan your sequence to optimize costs

### Cost Optimization

**Testing phase:**
```bash
# Use fastest, cheapest model
./image2video.py --backend runway --model gen4_turbo \
  --duration 5 "Test prompt"
# Cost: ~$1.00-$1.50
```

**Veo testing:**
```bash
# Use veo3.1_fast for balance
./image2video.py --backend runway --model veo3.1_fast \
  --duration 5 "Veo test"
# Cost: ~$1.00
```

**Production:**
```bash
# Gen-4 high quality
./image2video.py --backend runway --model gen4 \
  --duration 10 "Final prompt"
# Cost: ~$4.00-$5.00

# Or Veo 3.1 Fast (better quality for same price as gen4_turbo)
./image2video.py --backend runway --model veo3.1_fast \
  --duration 10 "Final prompt"
# Cost: ~$2.00
```

## Choosing Between Gen-4 and Veo

| Feature | Gen-4 | Veo (via Runway) |
|---------|-------|------------------|
| **Setup** | RunwayML API key only | RunwayML API key only |
| **Duration** | 5 or 10s only | 2-10s flexible |
| **Images** | Single image only | Up to 3 images |
| **Stitching** | ❌ No | ✅ Yes |
| **Speed** | Fast (turbo) | Fast (3.1_fast) |
| **Quality** | Good to high | Excellent |
| **Price** | $0.20-$0.50/sec | $0.20-$0.40/sec |

**Choose Gen-4 when:**
- Need fastest turnaround (gen4_turbo)
- Only have one reference image
- Don't need stitching
- Want RunwayML's native models

**Choose Veo when:**
- Need seamless multi-clip stitching
- Have multiple reference images
- Want flexible duration (2-10s)
- Want Google Veo without Google Cloud setup
- Best quality/price ratio (veo3.1_fast)

## Troubleshooting

### Authentication Issues

**Error: "Invalid API key"**
```bash
# Check key is set
echo $RUNWAY_API_KEY

# Reset key
export RUNWAY_API_KEY="your-runway-api-key"
```

**Error: "API key not found"**
```bash
# Create .env file
echo "RUNWAY_API_KEY=your-key" > .env

# Verify
cat .env
```

### Generation Issues

**Error: "Insufficient credits"**
- Purchase more credits at [runwayml.com](https://runwayml.com/)
- Check your credit balance in account settings
- Each generation shows estimated cost

**Error: "Duration must be 5 or 10 seconds" (Gen-4)**
- Gen-4 models only support 5s or 10s
- Solution: Use `--duration 5` or `--duration 10`
- Or switch to Veo models for flexible duration

**Error: "Only one image supported" (Gen-4)**
- Gen-4 uses single image only
- Solution: Use first image or switch to Veo models
- Veo supports up to 3 reference images

**Slow generation**
- gen4_turbo: ~1-2 minutes (normal)
- gen4: ~2-4 minutes (normal)
- veo3.1_fast: ~1-2 minutes (normal)
- veo3/veo3.1: ~2-4 minutes (normal)

### Stitching Issues

**Error: "Stitching requires Veo model"**
- Gen-4 doesn't support stitching
- Solution: Use `--model veo3.1_fast` or other Veo model

**Clips don't align**
- Ensure using `--stitch` flag
- Check prompts describe continuous action
- Verify reference images are consistent

## Best Practices

### Prompt Engineering

**Camera movements:**
```bash
./image2video.py --backend runway --model veo3.1_fast \
  "Slow dolly forward through the scene, smooth gimbal movement"
```

**Timing:**
```bash
./image2video.py --backend runway --model veo3.1_fast \
  --duration 7 \
  "Hold on subject for 2 seconds, then slow pan right over 5 seconds"
```

**Style:**
```bash
./image2video.py --backend runway --model gen4 \
  "Cinematic lighting, professional color grading, shallow depth of field"
```

### Image Selection

**For Gen-4:**
- Use your best hero image
- High resolution (1080p+)
- Clear, well-lit
- Represents desired style

**For Veo:**
- 2-3 images from different angles
- Consistent lighting
- Shows spatial relationships
- High resolution

### Model Selection Strategy

**Development workflow:**
1. **Testing**: Use gen4_turbo ($1-$1.50 per 5s clip)
2. **Refinement**: Switch to veo3.1_fast ($1 per 5s clip)
3. **Production**: Use gen4 or veo3.1 for maximum quality

**Long-form content:**
1. Plan sequence (6+ clips)
2. Use veo3.1_fast with stitching
3. Test with 2-3 clips first
4. Generate full sequence
5. Concatenate with ffmpeg

## Examples

### Example 1: Product Video (Gen-4 Turbo)

```bash
./image2video.py --backend runway --model gen4_turbo \
  --duration 5 \
  -i "product_white_bg.jpg" \
  "360 degree rotation of product on white background, \
   smooth continuous motion, professional studio lighting"

# Cost: ~$1.00-$1.50
```

### Example 2: Social Media Content (Gen-4)

```bash
./image2video.py --backend runway --model gen4 \
  --width 1080 --height 1920 \
  --duration 10 \
  -i "lifestyle_shot.jpg" \
  "Quick zoom with energy, vibrant colors, perfect for Instagram stories"

# Cost: ~$4.00-$5.00
```

### Example 3: Cinematic Scene (Veo 3.1 Fast)

```bash
./image2video.py --backend runway --model veo3.1_fast \
  --duration 10 \
  -i "landscape.jpg,detail.jpg" \
  "Slow crane up revealing majestic mountain vista, \
   golden hour lighting, cinematic film look"

# Cost: ~$2.00
```

### Example 4: Multi-Clip Walkthrough (Veo Stitching)

```bash
./image2video.py --backend runway --model veo3.1_fast --stitch \
  --duration 7 \
  -i "entrance.jpg,living.jpg,kitchen.jpg" \
  -p "Start in entrance foyer, pan right to stairs" \
     "Dolly into living room, pan left to sofas and TV" \
     "Continue to kitchen, show island and appliances" \
     "Final pan to window with city view"

# Cost: 4 clips × 7s × $0.20/sec = $5.60

# Concatenate
ffmpeg -i "concat:runway_clip_1.mp4|runway_clip_2.mp4|runway_clip_3.mp4|runway_clip_4.mp4" \
  -c copy walkthrough_final.mp4
```

## Additional Resources

- 🎨 **[Prompt Engineering Guide](../advanced/prompts.md)**
- 🔗 **[Advanced Stitching Guide](../advanced/stitching.md)**
- 📖 **[User Guide](../user-guide.md)**
- 🔧 **[Troubleshooting](../advanced/troubleshooting.md)**

## External Links

- [RunwayML Website](https://runwayml.com/)
- [RunwayML Documentation](https://docs.runwayml.com/)
- [API Documentation](https://docs.runwayml.com/api/)
- [Pricing](https://runwayml.com/pricing/)
- [Support](https://support.runwayml.com/)

---

**Need help?** Check the **[Troubleshooting Guide](../advanced/troubleshooting.md)** or visit **[RunwayML Support](https://support.runwayml.com/)**.
