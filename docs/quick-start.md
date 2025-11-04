# Quick Start Guide

Get up and running with the Multi-Backend Video Generator in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- An API key for at least one backend (see [Authentication](reference/authentication.md))

## Installation

### 1. Set Up Python Environment

```bash
# Create a virtual environment (recommended)
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 3. Configure API Keys

Choose one or more backends and set the corresponding API key:

```bash
# For OpenAI Sora
export OPENAI_API_KEY="your-openai-key"

# For RunwayML
export RUNWAY_API_KEY="your-runway-key"

# For Azure Sora
export AZURE_OPENAI_API_KEY="your-azure-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

# For Google Veo (use browser login - easiest)
./image2video.py --backend veo3 --google-login
```

**Tip:** Create a `.env` file to persist your API keys:
```bash
echo "OPENAI_API_KEY=your-key-here" >> .env
echo "RUNWAY_API_KEY=your-key-here" >> .env
```

## Your First Video

### Text-to-Video (Simplest)

Generate a video from just a text prompt:

```bash
./image2video.py "A peaceful sunset over mountains"
```

### Image-to-Video

Generate a video from an image:

```bash
./image2video.py -i "photo.jpg" "Animate this scene with gentle motion"
```

### Multiple Images

Use multiple reference images:

```bash
./image2video.py -i "img1.jpg,img2.jpg,img3.jpg" "Create a tour of these locations"
```

### Wildcard Patterns

Process all images in a directory:

```bash
./image2video.py -i "photos/*.jpg" "Create a walkthrough video"
```

## Choosing a Backend

By default, the script uses OpenAI Sora-2. To use a different backend:

```bash
# Use RunwayML Gen-4
./image2video.py --backend runway "Your prompt"

# Use Google Veo-3
./image2video.py --backend veo3 "Your prompt"

# Use Azure Sora
./image2video.py --backend azure-sora "Your prompt"
```

## Model Selection

List available models for a backend:

```bash
./image2video.py --list-models
./image2video.py --list-models runway
./image2video.py --list-models veo3
```

Choose a specific model:

```bash
# Fast generation with Veo
./image2video.py --backend veo3 --model veo-3.0-fast-generate-001 "Your prompt"

# High quality with RunwayML
./image2video.py --backend runway --model gen4 -i "photo.jpg" "Your prompt"
```

## Common Use Cases

### 1. Quick Test

```bash
./image2video.py "A serene lake at dawn"
```

### 2. Product Demo

```bash
./image2video.py -i "product.jpg" "Smooth 360-degree rotation of the product"
```

### 3. Real Estate Walkthrough

```bash
./image2video.py -i "interior/*.jpg" "Smooth camera walkthrough of the home"
```

### 4. Time-lapse Effect

```bash
./image2video.py -i "landscape.jpg" "Time-lapse from day to night"
```

## Troubleshooting Quick Fixes

### "No images provided" error
```bash
# Make sure to use -i flag before image paths
./image2video.py -i "image.jpg" "Your prompt"
```

### "API key not found" error
```bash
# Check that you've exported the correct API key
echo $OPENAI_API_KEY
echo $RUNWAY_API_KEY
```

### API capacity errors
The script automatically retries with exponential backoff. Just wait - it will eventually succeed.

### Google Veo authentication issues
```bash
# Use the browser login method (easiest)
./image2video.py --backend veo3 --google-login
```

## Next Steps

Now that you have the basics working:

- 📖 Read the **[User Guide](user-guide.md)** for complete documentation
- 🎯 Learn **[Prompt Engineering](advanced/prompts.md)** techniques
- 🔗 Try **[Multi-clip Stitching](advanced/stitching.md)** (Veo 3.1)
- 🔧 Explore backend-specific guides in **[backends/](backends/)**
- 🛠️ Check **[Troubleshooting](advanced/troubleshooting.md)** for detailed solutions

## Getting Help

- Check the logs: `tail -f logs/video_gen.log`
- Review **[Troubleshooting Guide](advanced/troubleshooting.md)**
- See **[Common Issues](advanced/troubleshooting.md#common-issues)**

---

**Ready for more?** Continue to the **[User Guide](user-guide.md)** for comprehensive documentation.
