#!/usr/bin/env bash
# walkthrough_and_stitch.sh — Veo 3.1 multi-clip walkthrough using our CLI
#
# What this does
# - Authenticates to Google (optional inline)
# - Generates 6 seamless clips with Veo 3.1 stitching using --stitch and -p
# - Uses your reference images for every clip (-i supports wildcards and lists)
# - Concatenates the resulting clips into a final MP4 without re-encoding
#
# Prereqs
# - ffmpeg installed and on PATH
# - .env configured with GOOGLE_CLOUD_PROJECT (and optionally others)
# - Google auth: either run with --google-login once per hour, or export GOOGLE_API_KEY

set -euo pipefail

# -------- Configuration --------

# Reference images (use wildcards or list multiple). Up to 3 images recommended for Veo.
IMAGES=(
  "foyer/*.png"
  "living/*.png"
  "kitchen/*.png"
)

# Output settings per clip
WIDTH=${WIDTH:-1280}
HEIGHT=${HEIGHT:-720}
DURATION=${DURATION:-7}   # seconds per clip
FPS=${FPS:-24}
SEED=${SEED:-}            # optional; leave empty for random

# Veo 3.1 model
MODEL=${MODEL:-veo-3.1-fast-generate-preview}

# Optional: authenticate inline. Set to 1 to force browser/gcloud auth as part of this run.
GOOGLE_LOGIN=${GOOGLE_LOGIN:-0}         # 1 to enable, 0 to skip
GOOGLE_LOGIN_BROWSER=${GOOGLE_LOGIN_BROWSER:-0} # 1 to force browser OAuth

# Delay between clips to avoid rate limits (seconds). 10–30 recommended for longer runs.
DELAY=${DELAY:-20}

# Final output
FINAL_OUTPUT=${FINAL_OUTPUT:-lower_ground_walkthrough.mp4}

# -------- Prompts (one per clip) --------
COMMON_PREFIX="You are rendering a smooth, cinematic walkthrough of the lower ground floor. \
Scene setup: Focal length ~24–28mm, indoor LED lighting, stable exposure and white balance, \
handheld but stabilized. Keep floorboards, stair rail, cat tree, dining set, and curtains consistent. \
No added text, logos, or people."

PROMPTS=(
  "Start on foyer pictures. SLOW pan to show the balcony/void. HOLD 2s. Then TILT DOWN and PAN LEFT to the stairs and a window with shutters. HOLD 2s."
  "DOLLY FORWARD five steps into the living area. PAN LEFT to show the sofas and wall-mounted television. HOLD 3s."
  "SLOW PAN RIGHT to the sideboard with the ornate mirror above. HOLD 3s."
  "DOLLY FORWARD five steps. PAN LEFT to show the entry toward other rooms. HOLD 3s."
  "DOLLY FORWARD five steps while SLOWLY PANNING RIGHT to re-introduce the stairs. HOLD 3s."
  "PAN LEFT to the window with the narrow bar and two stools. HOLD 3s."
)

# -------- Helpers --------
need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "❌ Missing dependency: $1"; exit 1; }; }
join_by() { local IFS="$1"; shift; echo "$*"; }

# -------- Checks --------
need_cmd ffmpeg
need_cmd ./image2video.py

# Expand image globs safely into a list of image paths
EXPANDED_IMAGES=()
for pat in "${IMAGES[@]}"; do
  # Allow empty expansions to be skipped
  shopt -s nullglob
  for f in $pat; do EXPANDED_IMAGES+=("$f"); done
  shopt -u nullglob
done

if [[ ${#EXPANDED_IMAGES[@]} -eq 0 ]]; then
  echo "⚠️  No reference images found for patterns: ${IMAGES[*]}"
  echo "    Proceeding with text-only stitching."
fi

# Build -i list only if we have images (each file is a separate arg)
IMAGE_ARGS=()
if [[ ${#EXPANDED_IMAGES[@]} -gt 0 ]]; then
  IMAGE_ARGS=( -i )
  for f in "${EXPANDED_IMAGES[@]}"; do
    IMAGE_ARGS+=("$f")
  done
fi

# Build -p list from PROMPTS (prepend common prefix to each)
PROMPT_ARGS=( -p )
for p in "${PROMPTS[@]}"; do
  PROMPT_ARGS+=("${COMMON_PREFIX} Camera sequence: ${p}")
done

# Optional Google login
GOOGLE_LOGIN_FLAGS=()
if [[ "$GOOGLE_LOGIN" == "1" ]]; then
  if [[ "$GOOGLE_LOGIN_BROWSER" == "1" ]]; then
    GOOGLE_LOGIN_FLAGS+=( --google-login-browser )
  else
    GOOGLE_LOGIN_FLAGS+=( --google-login )
  fi
fi

echo "🎬 Generating ${#PROMPTS[@]} stitched clips with Veo 3.1"
echo "   Model: ${MODEL}"
echo "   Size:  ${WIDTH}x${HEIGHT} @ ${FPS}fps, ${DURATION}s per clip"
if [[ ${#EXPANDED_IMAGES[@]} -gt 0 ]]; then
  echo "   Using ${#EXPANDED_IMAGES[@]} reference image(s) for each clip"
else
  echo "   No reference images"
fi
echo

# Run stitching in one command; CLI will output veo3_clip_1.mp4, veo3_clip_2.mp4, ...
./image2video.py \
  --backend veo3 \
  --model "${MODEL}" \
  --stitch \
  "${GOOGLE_LOGIN_FLAGS[@]}" \
  "${IMAGE_ARGS[@]}" \
  "${PROMPT_ARGS[@]}" \
  --width "${WIDTH}" --height "${HEIGHT}" \
  --fps "${FPS}" --duration "${DURATION}" \
  ${SEED:+--seed "$SEED"} \
  --delay "${DELAY}"

echo
echo "📼 Concatenating clips..."

# Build the concat list from the expected default filenames
CLIP_FILES=()
for i in $(seq 1 ${#PROMPTS[@]}); do
  CLIP_FILES+=("veo3_clip_${i}.mp4")
done

# Write concat file for ffmpeg
CONCAT_FILE=concat.txt
: > "$CONCAT_FILE"
for f in "${CLIP_FILES[@]}"; do
  if [[ -f "$f" ]]; then
    printf "file '%s'\n" "$f" >> "$CONCAT_FILE"
  else
    echo "❌ Missing expected clip: $f" >&2
    exit 1
  fi
done

ffmpeg -y -f concat -safe 0 -i "$CONCAT_FILE" -c copy "$FINAL_OUTPUT"
echo "✅ Render complete: $FINAL_OUTPUT"
