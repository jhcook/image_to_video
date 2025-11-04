# Installation Guide

Detailed instructions for installing and configuring the Multi-Backend Video Generator.

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **pip**: Python package installer (usually comes with Python)
- **Disk Space**: 500 MB for dependencies
- **RAM**: 2 GB minimum, 4 GB recommended
- **Internet**: Required for API calls

### Optional Requirements
- **ffmpeg**: Required only for multi-clip stitching feature
- **Git**: For cloning the repository

## Installation Methods

### Method 1: Using Git (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd image_to_video

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Method 2: Direct Download

```bash
# Download and extract the archive
# Then:
cd image_to_video

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Dependencies

The `requirements.txt` includes:

```
openai>=1.0.0          # OpenAI Sora-2 API client
requests>=2.31.0       # HTTP library for Veo-3 and RunwayML
python-dotenv>=1.0.0   # Environment variable management
```

### Installing ffmpeg (Optional)

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

**Note:** ffmpeg is only required for the multi-clip stitching feature (Veo 3.1, RunwayML Veo).

## Backend-Specific Setup

### OpenAI Sora

1. **Get API Key:**
   - Visit [OpenAI Platform](https://platform.openai.com/)
   - Navigate to API Keys section
   - Create a new key

2. **Configure:**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. **Verify:**
   ```bash
   ./image2video.py --backend sora2 --list-models
   ```

### Azure AI Foundry Sora

1. **Get Credentials:**
   - Access [Azure AI Foundry](https://ai.azure.com/)
   - Deploy Sora-2 model
   - Note your endpoint and API key

2. **Configure:**
   ```bash
   export AZURE_OPENAI_API_KEY="your-api-key"
   export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
   export AZURE_OPENAI_API_VERSION="2024-10-01-preview"  # Optional
   ```

3. **Verify:**
   ```bash
   ./image2video.py --backend azure-sora --list-models
   ```

See **[Azure Sora Guide](backends/azure-sora.md)** for detailed setup.

### Google Veo

**Option 1: Browser OAuth (Recommended)**

```bash
# One-time login
./image2video.py --backend veo3 --google-login
```

This opens a browser for Google authentication and saves your token for future use.

**Option 2: Manual gcloud Setup**

1. **Install gcloud CLI:**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Ubuntu/Debian
   sudo snap install google-cloud-sdk --classic
   ```

2. **Authenticate:**
   ```bash
   gcloud auth application-default login
   ```

3. **Configure:**
   ```bash
   export GOOGLE_API_KEY="$(gcloud auth application-default print-access-token)"
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

4. **Verify:**
   ```bash
   ./image2video.py --backend veo3 --list-models
   ```

**Important:** OAuth tokens expire after 1 hour. Re-run the login command when needed.

See **[Google Veo Guide](backends/google-veo.md)** for detailed authentication.

### RunwayML

1. **Get API Key:**
   - Visit [RunwayML](https://runwayml.com/)
   - Navigate to API settings
   - Generate an API key

2. **Configure:**
   ```bash
   export RUNWAY_API_KEY="your-api-key"
   ```

3. **Verify:**
   ```bash
   ./image2video.py --backend runway --list-models
   ```

See **[RunwayML Guide](backends/runwayml.md)** for detailed setup.

## Environment Variables

For the complete list across all backends, see Reference: [Environment Variables](reference/environment-variables.md).

### Using .env File (Recommended)

Create a `.env` file in the project root:

```bash
# OpenAI Sora
OPENAI_API_KEY=your-openai-key

# Azure Sora
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-10-01-preview

# Google Veo
GOOGLE_CLOUD_PROJECT=your-project-id
# Note: GOOGLE_API_KEY should be obtained via gcloud command

# RunwayML
RUNWAY_API_KEY=your-runway-key
RUNWAY_MODEL=gen4_turbo  # Optional: set default model
```

The script automatically loads the `.env` file on startup.

### Using Shell Environment

Alternatively, export variables in your shell:

```bash
# Add to ~/.bashrc, ~/.zshrc, or equivalent
export OPENAI_API_KEY="your-key"
export RUNWAY_API_KEY="your-key"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

## Verification

### Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Test imports
python -c "from video_gen import *; print('✓ Imports successful')"

# Test CLI
./image2video.py --help
```

### Test Backend Connection

```bash
# Test with actual generation (uses API credits)
./image2video.py --backend sora2 "Test prompt"
./image2video.py --backend runway "Test prompt"
./image2video.py --backend veo3 "Test prompt"
```

### Check Logs

```bash
# View log output
tail -f logs/video_gen.log
```

## Common Installation Issues

### Python Version Mismatch

**Error:** `Python 3.8 or higher required`

**Solution:**
```bash
# Check Python version
python3 --version

# If too old, install newer Python
# macOS
brew install python@3.11

# Ubuntu
sudo apt-get install python3.11
```

### pip Not Found

**Error:** `pip: command not found`

**Solution:**
```bash
# Install pip
python3 -m ensurepip --upgrade

# Or use package manager
# macOS
brew install python3

# Ubuntu
sudo apt-get install python3-pip
```

### Permission Errors

**Error:** `Permission denied` during pip install

**Solution:**
```bash
# Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Or use --user flag (not recommended)
pip install --user -r requirements.txt
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'openai'`

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### API Key Not Loading

**Error:** `API key not found`

**Solution:**
```bash
# Check .env file exists and has correct format
cat .env

# Or export directly
export OPENAI_API_KEY="your-key"

# Verify it's set
echo $OPENAI_API_KEY
```

## Directory Structure After Installation

```
image_to_video/
├── venv/                  # Virtual environment (created)
├── logs/                  # Log files (created on first run)
│   └── video_gen.log     # Debug logs
├── image2video.py         # Main script
├── requirements.txt       # Dependencies
├── .env                   # API keys (you create this)
└── video_gen/            # Core package
```

## Updating

To update to the latest version:

```bash
# Activate virtual environment
source venv/bin/activate

# Pull latest changes (if using git)
git pull

# Update dependencies
pip install --upgrade -r requirements.txt
```

## Uninstallation

To completely remove the application:

```bash
# Deactivate virtual environment
deactivate

# Remove directory
cd ..
rm -rf image_to_video
```

## Next Steps

- 🚀 **[Quick Start Guide](quick-start.md)** - Generate your first video
- 📖 **[User Guide](user-guide.md)** - Complete usage documentation
- 🔐 **[Authentication Guide](reference/authentication.md)** - Detailed auth setup
- 🔧 **[Backend Guides](backends/)** - Backend-specific configuration

## Getting Help

If you encounter issues during installation:

1. Check the **[Troubleshooting Guide](advanced/troubleshooting.md)**
2. For SSL certificate errors, see **[SSL Troubleshooting](technical/ssl-troubleshooting.md)**
3. Verify all prerequisites are met
4. Review the logs: `cat logs/video_gen.log`
5. Ensure API keys are correctly configured

---

**Installation complete?** Continue to the **[Quick Start Guide](quick-start.md)**.
