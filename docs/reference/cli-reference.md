# CLI Reference

Command-line options for `image2video.py`.

## Usage

```
./image2video.py [OPTIONS] "PROMPT"
```

- PROMPT: Required positional argument, quoted if it contains spaces

## Options

### Image Input

- `-i, --images PATHS`
  - One or more images to use as references
  - Supports comma-separated lists and wildcards
  - Examples:
    - `-i "image.jpg"`
    - `-i "img1.jpg,img2.jpg,dir/*.png"`

### Provider Selection

- `--provider {openai|azure|google|runway}`
  - Select AI video provider (default: openai)

- `--model MODEL_NAME`
  - Choose a specific model for the selected provider

- `--list-models [PROVIDER]`
  - List available models (all providers if omitted)

### Artifact Management

- `--list-artifacts`
  - List all generated video artifacts with metadata and download status
  - Shows: Task ID, Provider, Model, Status, Created date, Prompt preview
  - Optional filters: `--provider PROVIDER` and `--status STATUS`

- `--download TASK_ID`
  - Download a specific video artifact by its unique task ID
  - Optional: `--output PATH` to specify custom output location
  - Optional: `--force` to overwrite existing files
  - Automatically updates artifact status to 'downloaded'

### Video Parameters

- `--duration SECONDS`
  - Target video length (provider-dependent)
  - Runway Gen-4: only 5 or 10; others: flexible (2–10 typical)

- `--width PIXELS`, `--height PIXELS`
  - Output resolution
  - Common presets: 1920x1080, 1080x1920, 1080x1080

- `--seed NUMBER`
  - Random seed for reproducibility (not all providers support)

- `--loop true|false`
  - Attempt seamless loop (Sora only)

### Stitching (Veo 3.1)

- `--stitch`
  - Enable multi-clip generation with automatic frame transitions

- `-p, --prompts "P1" "P2" ...`
  - Provide one prompt per clip

### Authentication Helpers

- `--google-login`
  - Launch browser for Google OAuth (Veo)

### Help/Meta

- `-h, --help`       Show help
- `--version`        Show version

## Examples

### Basic Video Generation

- Basic:
```
./image2video.py "A serene lake at sunset"
```

- With images:
```
./image2video.py -i "photo.jpg" "Slow pan across the scene"
```

- Runway Gen-4 Turbo:
```
./image2video.py --provider runway --model gen4_turbo -i hero.jpg "Prompt"
```

### Artifact Management

- List all generated videos:
```
./image2video.py --list-artifacts
```

- Filter by provider:
```
./image2video.py --list-artifacts --provider runway
./image2video.py --list-artifacts --provider openai
```

- Filter by status:
```
./image2video.py --list-artifacts --status completed
./image2video.py --list-artifacts --status downloaded
```

- Download a specific video:
```
./image2video.py --download ce88ed9c-89c9-483f-ae46-8259c64dd180
```

- Download with custom output path:
```
./image2video.py --download <task_id> --output ~/Videos/my_video.mp4
```

- Force overwrite existing file:
```
./image2video.py --download <task_id> --force
```

### Multi-Clip Stitching

- Veo 3.1 Stitching:
```
./image2video.py --provider google --model veo-3.1-fast-generate-preview --stitch \
  -i "refs/*.jpg" \
  -p "Opening" "Middle" "Final"
```

## Notes

- Environment variables are read from the shell and `.env` (see [Environment Variables](environment-variables.md))
- Logs are written to `logs/video_gen.log`
- On capacity errors, the tool retries with exponential backoff
- All generated videos are automatically tracked as artifacts for later download
- Use `--list-artifacts` to see all your generated videos and their status
- Videos can be downloaded later even if generation was interrupted or failed initially
- Artifact management also available via module: `python -m video_gen.artifact_manager`
