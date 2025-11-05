# Multi-Backend Video Generator

A Python application that converts images to videos using multiple AI backends: OpenAI's Sora-2, Azure AI Foundry Sora, Google's Veo-3, and RunwayML's Gen-4 models.

## Features

- 🎨 **Multiple AI Backends** - Choose between OpenAI Sora-2, Azure Sora, Google Veo-3, or RunwayML
- 🖼️ **Flexible Image Input** - Single files, multiple images, wildcard patterns, or text-only
- 🔗 **Seamless Stitching** - Multi-clip video generation with automatic frame transitions (Veo 3.1, RunwayML Veo)
- 🔄 **Automatic Retries** - Exponential backoff when APIs are at capacity
- 📝 **Comprehensive Logging** - DEBUG-level logging to `logs/video_gen.log`
- 🏗️ **Modular Architecture** - Clean, maintainable, and extensible codebase

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export OPENAI_API_KEY="your-key"      # For OpenAI Sora
export RUNWAY_API_KEY="your-key"      # For RunwayML
# For Google Veo - see authentication guide

# Generate a video
./image2video.py "A peaceful sunset over mountains"

# With images
./image2video.py -i "photo.jpg" "Animate this scene"

# Choose a backend
./image2video.py --backend runway "Your prompt"
```

## Documentation

📚 **[Complete Documentation](docs/README.md)** - Full documentation index

### Quick Links

- **[Quick Start Guide](docs/quick-start.md)** - Get started in 5 minutes
- **[User Guide](docs/user-guide.md)** - Complete usage documentation
- **[Installation](docs/installation.md)** - Detailed setup instructions

### Backend Guides

- **[OpenAI Sora](docs/backends/openai-sora.md)** - OpenAI Sora-2 setup
- **[Azure Sora](docs/backends/azure-sora.md)** - Azure AI Foundry setup
- **[Google Veo](docs/backends/google-veo.md)** - Google Veo-3 with OAuth
- **[RunwayML](docs/backends/runwayml.md)** - RunwayML Gen-4 & Veo

### Advanced Topics

- **[Stitching Guide](docs/advanced/stitching.md)** - Multi-clip video generation
- **[Image Grouping](docs/advanced/image-grouping.md)** - Control which images are used per clip
- **[Prompt Engineering](docs/advanced/prompts.md)** - Writing effective prompts
- **[Troubleshooting](docs/advanced/troubleshooting.md)** - Common issues

## Supported Backends

| Backend | Models | Pricing | Multi-Image | Stitching |
|---------|--------|---------|-------------|-----------|
| **OpenAI Sora** | sora-2, sora-2-pro | Variable | ✅ | ❌ |
| **Azure Sora** | sora-2, sora-2-pro | \$0.10/sec | ✅ | ❌ |
| **Google Veo** | veo-3.0, veo-3.1 | \$0.15-0.40 | ✅ | ✅ |
| **RunwayML** | gen4, gen4_turbo, veo3.x | Variable | Single only | ✅ (Veo) |

See **[Backend Comparison](docs/reference/backend-comparison.md)** for detailed feature matrix.

## Usage Examples

### Basic Text-to-Video
```bash
./image2video.py "A serene lake at dawn with mist rising"
```

### Image-to-Video
```bash
./image2video.py -i "landscape.jpg" "Time-lapse of this scene at sunset"
```

### Multiple Images
```bash
./image2video.py -i "img1.jpg,img2.jpg,img3.jpg" "Tour of these locations"
```

### Wildcard Patterns
```bash
./image2video.py -i "photos/*.jpg" "Create a walkthrough video"
```

### Backend Selection
```bash
# Use Google Veo
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview "Your prompt"

# Use RunwayML
./image2video.py --backend runway --model gen4 "Your prompt"

# Use Azure Sora
./image2video.py --backend azure-sora "Your prompt"
```

### Seamless Multi-Clip Stitching (Veo 3.1)
```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \\
  -i reference_images/*.jpg \\
  -p "Camera pans across the foyer" \\
     "Dolly forward into the living room" \\
     "Pan right to show the kitchen"
```

**💡 Tip:** Control which images are used for each clip - see **[Image Grouping Guide](docs/advanced/image-grouping-quick.md)**

## Installation

### Requirements
- Python 3.8 or higher
- ffmpeg (for video processing)

### Setup
```bash
# Clone or download the repository
git clone <repository-url>
cd image_to_video

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys
```

See **[Installation Guide](docs/installation.md)** for detailed instructions.

## Authentication

Each backend requires different authentication:

Tip: A fully commented template of all required and optional variables is provided in .env.sample. Copy it to .env and edit values as needed.

### OpenAI Sora
```bash
export OPENAI_API_KEY="your-api-key"
```

### Azure Sora
```bash
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
```

### Google Veo
```bash
# Browser OAuth (easiest)
./image2video.py --backend veo3 --google-login

# Or manual with gcloud
gcloud auth application-default login
export GOOGLE_API_KEY="\$(gcloud auth application-default print-access-token)"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### RunwayML
```bash
export RUNWAY_API_KEY="your-api-key"
```

See **[Authentication Guide](docs/reference/authentication.md)** for complete details.

## Project Structure

```
image_to_video/
├── image2video.py              # Main CLI entry point
├── image2video_mono.py         # Legacy monolithic script (Sora-2 only)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── docs/                       # Documentation
│   ├── README.md              # Documentation index
│   ├── quick-start.md         # Quick start guide
│   ├── user-guide.md          # Complete user guide
│   ├── backends/              # Backend-specific docs
│   ├── advanced/              # Advanced topics
│   ├── technical/             # Technical documentation
│   └── reference/             # Reference materials
│
└── video_gen/                  # Core package
    ├── config.py              # Configuration management
    ├── file_handler.py        # File operations
    ├── arg_parser.py          # Argument parsing
    ├── video_generator.py     # Main orchestration
    ├── logger.py              # Logging infrastructure
    └── providers/             # Provider implementations
        ├── openai_provider/   # OpenAI Sora
        ├── azure_provider/    # Azure Sora
        ├── google_provider/   # Google Veo
        └── runway_provider/   # RunwayML Gen-4 & Veo
```

## Development

### Running Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run the full unittest suite
python -m unittest discover -s tests -p "test_*.py" -v

# Test specific backend
./image2video.py --backend sora2 "Test prompt"
```

### Contributing
We welcome contributions! See the **[Development Guide](docs/technical/development.md)** for:
- Setting up a development environment
- Code style and conventions
- Testing guidelines
- Submitting pull requests

## Troubleshooting

Common issues and solutions:

**"No images provided" error**
```bash
# Use -i flag before image paths
./image2video.py -i "images/*.jpg" "Your prompt"
```

**API key not found**
```bash
# Verify environment variables are set
echo \$OPENAI_API_KEY
echo \$RUNWAY_API_KEY
```

**Google Veo authentication issues**
```bash
# Use browser OAuth (easiest method)
./image2video.py --backend veo3 --google-login
```

See **[Troubleshooting Guide](docs/advanced/troubleshooting.md)** for complete solutions.

## Architecture

The application uses a modular, provider-based architecture:

- **Providers** - Backend-specific implementations (OpenAI, Azure, Google, RunwayML)
- **Clients** - Separate client classes per model family within each provider
- **Configuration** - Per-provider config classes with validation
- **Orchestration** - Central dispatcher routes requests to appropriate providers
- **Logging** - Centralized logging infrastructure with DEBUG-level detail

See **[Architecture Guide](docs/technical/architecture.md)** for detailed design documentation.

## License

This project is provided as-is for educational and research purposes.

## Links

- 📖 **[Full Documentation](docs/README.md)**
- 🚀 **[Quick Start](docs/quick-start.md)**
- 📚 **[User Guide](docs/user-guide.md)**
- 🔧 **[API Reference](docs/technical/api-reference.md)**
- 🐛 **[Troubleshooting](docs/advanced/troubleshooting.md)**
