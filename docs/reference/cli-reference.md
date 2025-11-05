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
