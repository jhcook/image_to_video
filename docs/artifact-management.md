# Video Artifact Management

The video generation system now includes comprehensive artifact management that allows you to track, list, and download generated videos even after interruptions or failures.

## Features

### 🎯 **Automatic Tracking**
Every video generation is automatically tracked with:
- **Task ID**: Unique identifier for each video
- **Provider**: Which service generated it (OpenAI, RunwayML, Google)
- **Model**: Specific model used (sora-2, gen4_turbo, veo-3.1, etc.)
- **Status**: Current state (generated, downloaded, failed)
- **Metadata**: Prompt, dimensions, duration, and other parameters

### 📋 **List Available Videos**

**Main CLI Interface (Recommended):**
```bash
# List all artifacts
./image2video.py --list-artifacts

# Filter by provider
./image2video.py --list-artifacts --provider runway
./image2video.py --list-artifacts --provider openai

# Filter by status
./image2video.py --list-artifacts --status completed
./image2video.py --list-artifacts --status downloaded
```

**Alternative Module Interface:**
```bash
# List all artifacts
python -m video_gen.artifact_manager list

# Filter by provider
python -m video_gen.artifact_manager list --provider runway
python -m video_gen.artifact_manager list --provider openai

# Filter by status
python -m video_gen.artifact_manager list --status generated
python -m video_gen.artifact_manager list --status downloaded
```

### ⬇️ **Download Videos**

**Main CLI Interface (Recommended):**
```bash
# Download a specific video by task ID
./image2video.py --download <task_id>

# Download to custom location
./image2video.py --download <task_id> --output ~/Videos/my_video.mp4

# Force re-download even if file exists
./image2video.py --download <task_id> --force
```

**Alternative Module Interface:**
```bash
# Download a specific video by task ID
python -m video_gen.artifact_manager download <task_id>

# Download to custom location
python -m video_gen.artifact_manager download <task_id> --output ~/Videos/my_video.mp4

# Force re-download even if file exists
python -m video_gen.artifact_manager download <task_id> --force
```

### 🗂️ **File Organization**
Downloaded videos are organized in the `artifacts/` directory:
```
artifacts/
├── artifacts.json          # Metadata database
└── downloads/
    ├── runway_<task_id>_gen4_turbo.mp4
    ├── openai_<task_id>_sora-2.mp4
    └── google_<task_id>_veo-3.1.mp4
```

## Use Cases

### 🔄 **Resume Interrupted Downloads**
If video generation succeeds but download fails (network issues, etc.):
```bash
# List videos ready for download
./image2video.py --list-artifacts --status completed

# Download the failed video
./image2video.py --download <task_id>
```

### 📊 **Track Generation History**
Keep track of all your video generations:
```bash
# See everything you've generated
./image2video.py --list-artifacts

# See only RunwayML videos
./image2video.py --list-artifacts --provider runway
```

### 🎬 **Batch Management**
Download multiple videos from different sessions:
```bash
# List available videos
./image2video.py --list-artifacts --status completed

# Download specific ones
./image2video.py --download task-id-1
./image2video.py --download task-id-2
```

## Integration with Video Generation

The artifact system is automatically integrated with all providers:

### **OpenAI Sora**
```bash
./image2video.py --provider openai --model sora-2 "A peaceful lake"
# If verification fails, the video is still tracked for later download
```

### **RunwayML**
```bash
./image2video.py --provider runway --model gen4_turbo -i image.jpg "Motion prompt"
# Task is tracked even if polling or download fails
```

### **Google VEO**
```bash
./image2video.py --provider google --model veo-3.1-generate-preview "Video prompt"
# Tracked automatically with VEO-specific metadata
```

## Example Workflow

1. **Generate a video** (may fail at download step):
   ```bash
   ./image2video.py --provider runway -i photo.jpg "Add gentle movement"
   ```

2. **Check what's available**:
   ```bash
   ./image2video.py --list-artifacts
   ```

3. **Download later**:
   ```bash
   ./image2video.py --download ce88ed9c-89c9-483f-ae46-8259c64dd180
   ```

4. **Verify download**:
   ```bash
   ./image2video.py --list-artifacts --status downloaded
   ls artifacts/downloads/
   ```

## Error Recovery

### **Network Interruptions**
If generation succeeds but download fails due to network issues, the artifact system allows you to retry the download without regenerating the video.

### **Provider API Issues**
When providers have temporary issues, you can download successful generations once the provider is back online.

### **Storage Management**
Track which videos have been downloaded to avoid unnecessary API calls and manage local storage efficiently.

## Technical Details

- **Storage**: Artifacts stored in `artifacts/artifacts.json`
- **Downloads**: Videos saved to `artifacts/downloads/`
- **Metadata**: Includes full generation parameters for reproducibility
- **Provider Support**: Works with all supported providers (OpenAI, RunwayML, Google)
- **Format**: Standardized video file naming and organization

The artifact management system ensures you never lose generated videos due to technical issues and provides a complete history of your video generation activities.