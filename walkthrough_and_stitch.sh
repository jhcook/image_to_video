#!/usr/bin/env bash
#
# walkthrough_and_stitch.sh — Generate seamless multi-clip videos with Veo 3.1
#
# Description:
#   Generates multiple video clips with automatic frame stitching using Google Veo 3.1.
#   Each clip's last frame becomes the first frame of the next clip for seamless transitions.
#
# Features:
#   - Automated Google authentication (optional)
#   - Multiple clips from individual prompts (--stitch mode)
#   - Reference image support (wildcards and paths)
#   - Rate limit avoidance with configurable delays
#   - Automatic concatenation into final video
#
# Prerequisites:
#   - ffmpeg (for video concatenation)
#   - .env file with GOOGLE_CLOUD_PROJECT configured
#   - Google authentication (via --google-login or GOOGLE_API_KEY)
#
# Usage:
#   # First time (with inline authentication)
#   GOOGLE_LOGIN=1 ./walkthrough_and_stitch.sh
#
#   # Subsequent runs (token valid ~1 hour)
#   ./walkthrough_and_stitch.sh
#
#   # Custom settings
#   WIDTH=1920 HEIGHT=1080 DURATION=10 ./walkthrough_and_stitch.sh

set -euo pipefail

#==============================================================================
# Configuration
#==============================================================================

# Reference images (supports wildcards and multiple paths)
# Up to 3 images recommended for optimal Veo performance
IMAGES=(
  "foyer/*.png"
  "living/*.png"
  "kitchen/*.png"
)

# Video output settings (per clip)
WIDTH=${WIDTH:-1280}
HEIGHT=${HEIGHT:-720}
DURATION=${DURATION:-7}  # seconds per clip
FPS=${FPS:-24}
SEED=${SEED:-}           # optional seed for reproducibility

# Veo 3.1 model selection
# Options: veo-3.1-fast-generate-preview (fast), veo-3.1-generate-preview (quality)
MODEL=${MODEL:-veo-3.1-fast-generate-preview}

# Authentication options
GOOGLE_LOGIN=${GOOGLE_LOGIN:-0}         # Set to 1 to authenticate via gcloud/browser
GOOGLE_LOGIN_BROWSER=${GOOGLE_LOGIN_BROWSER:-0}  # Set to 1 to force browser OAuth

# Rate limiting
DELAY=${DELAY:-20}  # seconds between clips (10-30 recommended to avoid 429 errors)

# Output file
FINAL_OUTPUT=${FINAL_OUTPUT:-lower_ground_walkthrough.mp4}

#==============================================================================
# Prompts (one per clip)
#==============================================================================

# Common scene setup applied to all clips
COMMON_PREFIX="You are rendering a smooth, cinematic walkthrough of the lower ground floor. \
Scene setup: Focal length ~24–28mm, indoor LED lighting, stable exposure and white balance, \
handheld but stabilized. Keep floorboards, stair rail, cat tree, dining set, and curtains consistent. \
No added text, logos, or people."

# Individual camera movements for each clip
PROMPTS=(
  "Start on foyer pictures. SLOW pan to show the balcony/void. HOLD 2s. Then TILT DOWN and PAN LEFT to the stairs and a window with shutters. HOLD 2s."
  "DOLLY FORWARD five steps into the living area. PAN LEFT to show the sofas and wall-mounted television. HOLD 3s."
  "SLOW PAN RIGHT to the sideboard with the ornate mirror above. HOLD 3s."
  "DOLLY FORWARD five steps. PAN LEFT to show the entry toward other rooms. HOLD 3s."
  "DOLLY FORWARD five steps while SLOWLY PANNING RIGHT to re-introduce the stairs. HOLD 3s."
  "PAN LEFT to the window with the narrow bar and two stools. HOLD 3s."
)

#==============================================================================
# Helper Functions
#==============================================================================

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "❌ Missing dependency: $1"
    echo "   Please install $1 and ensure it's on your PATH"
    exit 1
  }
}

#==============================================================================
# Preflight Checks
#==============================================================================

# Verify required dependencies
need_cmd ffmpeg
need_cmd ./image2video.py

#==============================================================================
# Image Processing
#==============================================================================

# Expand image glob patterns safely
EXPANDED_IMAGES=()
for pat in "${IMAGES[@]}"; do
  shopt -s nullglob  # Allow empty expansions
  for f in $pat; do
    EXPANDED_IMAGES+=("$f")
  done
  shopt -u nullglob
done

# Warn if no images found
if [[ ${#EXPANDED_IMAGES[@]} -eq 0 ]]; then
  echo "⚠️  No reference images found for patterns: ${IMAGES[*]}"
  echo "    Proceeding with text-only stitching."
fi

#==============================================================================
# Build CLI Arguments
#==============================================================================

# Image arguments (-i file1 file2 ...)
IMAGE_ARGS=()
if [[ ${#EXPANDED_IMAGES[@]} -gt 0 ]]; then
  IMAGE_ARGS=(-i)
  for f in "${EXPANDED_IMAGES[@]}"; do
    IMAGE_ARGS+=("$f")
  done
fi

# Prompt arguments (-p "prompt1" "prompt2" ...)
PROMPT_ARGS=(-p)
for p in "${PROMPTS[@]}"; do
  PROMPT_ARGS+=("${COMMON_PREFIX} Camera sequence: ${p}")
done

# Authentication flags
GOOGLE_LOGIN_FLAGS=()
if [[ "$GOOGLE_LOGIN" == "1" ]]; then
  if [[ "$GOOGLE_LOGIN_BROWSER" == "1" ]]; then
    GOOGLE_LOGIN_FLAGS+=(--google-login-browser)
  else
    GOOGLE_LOGIN_FLAGS+=(--google-login)
  fi
fi

#==============================================================================
# Generate Video Clips
#==============================================================================

echo "🎬 Generating ${#PROMPTS[@]} stitched clips with Veo 3.1"
echo "   Model:     ${MODEL}"
echo "   Size:      ${WIDTH}x${HEIGHT} @ ${FPS}fps"
echo "   Duration:  ${DURATION}s per clip"
echo "   Delay:     ${DELAY}s between clips"

if [[ ${#EXPANDED_IMAGES[@]} -gt 0 ]]; then
  echo "   Images:    ${#EXPANDED_IMAGES[@]} reference image(s) per clip"
else
  echo "   Images:    Text-only (no reference images)"
fi
echo

# Generate all clips with automatic frame stitching
# Output files: veo3_clip_1.mp4, veo3_clip_2.mp4, ...
./image2video.py \
  --provider veo3 \
  --model "${MODEL}" \
  --stitch \
  "${GOOGLE_LOGIN_FLAGS[@]}" \
  "${IMAGE_ARGS[@]}" \
  "${PROMPT_ARGS[@]}" \
  --width "${WIDTH}" \
  --height "${HEIGHT}" \
  --fps "${FPS}" \
  --duration "${DURATION}" \
  ${SEED:+--seed "$SEED"} \
  --delay "${DELAY}"

#==============================================================================
# Concatenate Clips
#==============================================================================

echo
echo "📼 Concatenating ${#PROMPTS[@]} clips into final video..."

# Build list of expected clip files
CLIP_FILES=()
for i in $(seq 1 ${#PROMPTS[@]}); do
  CLIP_FILES+=("veo3_clip_${i}.mp4")
done

# Create ffmpeg concat file
CONCAT_FILE="concat.txt"
: > "$CONCAT_FILE"

for f in "${CLIP_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "❌ Error: Missing expected clip file: $f" >&2
    echo "   Clip generation may have failed. Check logs for errors." >&2
    exit 1
  fi
  printf "file '%s'\n" "$f" >> "$CONCAT_FILE"
done

# Concatenate without re-encoding (fast)
echo "   Using concat demuxer (no re-encoding)..."
ffmpeg -y -f concat -safe 0 -i "$CONCAT_FILE" -c copy "$FINAL_OUTPUT" 2>&1 | grep -v "^frame="

echo
echo "✅ Success! Final video: $FINAL_OUTPUT"
echo "   Individual clips: ${CLIP_FILES[*]}"
