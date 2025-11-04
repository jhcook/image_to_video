# Testing

How to validate functionality and avoid regressions.

## Quick Checks

- Imports: `python -c "from video_gen import *; print('ok')"`
- CLI help: `./image2video.py --help`
- List models: `./image2video.py --list-models`

## Unit Tests

A lightweight test script is included for parsing and basic flows:

```bash
# Activate venv first
source venv/bin/activate

# Argument parsing and wildcard expansion
python test_final.py "Test prompt" -i "*.jpg,*.png"
```

Add more tests as needed using `unittest` or `pytest`.

## Manual Integration Tests

These tests exercise real backends (costs may apply):

```bash
# Sora-2 (OpenAI)
./image2video.py --backend sora2 "Simple prompt"

# Azure Sora
./image2video.py --backend azure-sora "Simple prompt"

# Veo-3 (Google)
./image2video.py --backend veo3 --google-login
./image2video.py --backend veo3 --model veo-3.0-fast-generate-001 "Simple prompt"

# RunwayML (Gen-4)
./image2video.py --backend runway --model gen4_turbo "Simple prompt"
```

### Image-to-Video

```bash
mkdir -p test_images
# Add 2–3 JPG/PNG files
./image2video.py -i "test_images/*.jpg" "Test with images"
```

### Stitching (Veo 3.1)

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "refs/*.jpg" \
  -p "Clip 1" "Clip 2" "Clip 3"

ffmpeg -f concat -safe 0 -i <(printf "file 'veo3_clip_1.mp4'\nfile 'veo3_clip_2.mp4'\nfile 'veo3_clip_3.mp4'\n") -c copy final.mp4
```

## Developer Workflows

### Local Dev Loop

1. Create/activate venv
2. Install deps: `pip install -r requirements.txt`
3. Run quick commands:
   - `./image2video.py --list-models`
   - `./image2video.py --backend runway "Hello"`
4. Review `logs/video_gen.log` (DEBUG)

### Code Quality

- Type hints are used throughout
- Keep functions small and testable
- Add unit tests for new parsing/validation logic

## Troubleshooting Tests

- Missing modules → activate venv and reinstall requirements
- Auth errors → verify environment variables and backend guides
- ffmpeg not found → install via Homebrew or your package manager

## CI Suggestions (optional)

- Lint/typecheck: `ruff`, `mypy`
- Unit tests: `pytest -q`
- Pre-commit hooks to enforce formatting

## Next Steps

- See technical/api-reference.md for function contracts
- Review advanced/stitching.md for multi-clip test plans
