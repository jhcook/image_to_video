# Advanced Stitching Guide

Create seamless multi-clip videos using Veo 3.1 models (Google or Runway Veo).

- For a quick intro, see the User Guide section: user-guide.md#multi-clip-stitching
- This guide dives deeper into techniques and patterns.

## What Is Stitching?

Stitching generates a sequence of short clips where each clip’s last frame becomes the next clip’s first frame. This ensures visual continuity without jumps.

- Works with: Veo 3.1 models only
  - Google: `veo-3.1-fast-generate-preview`, `veo-3.1-generate-preview`
  - Runway: `veo3.1_fast`, `veo3.1`
- Not supported by: Sora-2, Runway Gen-4

## Command-Line Workflow

Minimal example:

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -i "refs/*.jpg" \
  -p "Clip 1: Opening movement" \
     "Clip 2: Continue movement" \
     "Clip 3: Final reveal"
```

  **💡 Tip:** By default, all images are shared across all clips. For more control over which images are used for each clip, see the **[Image Grouping Guide](image-grouping-quick.md)**.

Outputs:
- `veo3_clip_2.mp4` → Used to derive the first frame of clip 3
- `veo3_clip_3.mp4`

Concatenate:

```bash
# Direct concat (fast)
ffmpeg -i "concat:veo3_clip_1.mp4|veo3_clip_2.mp4|veo3_clip_3.mp4" -c copy final.mp4

# Or concat demuxer (robust)
printf "file 'veo3_clip_1.mp4'\nfile 'veo3_clip_2.mp4'\nfile 'veo3_clip_3.mp4'\n" > concat.txt
ffmpeg -f concat -safe 0 -i concat.txt -c copy final.mp4
```

## Python API Workflow

Generate programmatically for more control:

```python
from video_gen.video_generator import generate_video_sequence_with_veo3_stitching

prompts = [
  "Entrance: slow pan right revealing staircase",
  "Dolly forward into living room, pan left to sofas and TV",
  "Pan right to sideboard with ornate mirror",
  "Dolly forward and pan left to hallway",
  "Dolly forward, slowly pan right reintroducing stairs",
  "Pan left to window with bar and stools"
]

# Same reference images for all clips
file_paths_list = [["ref1.jpg", "ref2.jpg"]] * len(prompts)

outputs = generate_video_sequence_with_veo3_stitching(
  prompts=prompts,
  file_paths_list=file_paths_list,
  width=1280,
  height=720,
  duration_seconds=7,
  model="veo-3.1-fast-generate-preview"
)

print(outputs)
```

## Design Patterns

### 1) One Scene, Multiple Camera Moves

- Use consistent reference images across clips
- Each prompt describes a different camera move
- Keep lighting and time-of-day consistent

Prompt template:

```
Scene: {brief description}
Movement: {pan/dolly/crane, direction, speed}
Timing: {holds, transitions}
Continuity: {recurring objects stay consistent}
Look: {lighting, grading, lens}
```

### 2) Different Sub-Areas of the Same Space

- Use targeted images per clip for local detail
- Keep 1–2 global references across clips for style

Example file_paths_list:

```python
file_paths_list = [
  ["foyer1.jpg", "foyer2.jpg"],
  ["living1.jpg", "living2.jpg"],
  ["sideboard.jpg"],
  ["hallway.jpg"],
  ["stairs.jpg"],
  ["window_bar.jpg"],
]
```

### 3) Text-Only Storyboard

- No image references; rely on vivid, specific prompts
- Works well for animated or abstract sequences

```bash
./image2video.py --backend veo3 --model veo-3.1-fast-generate-preview --stitch \
  -p "An empty stage; lights slowly rise" \
     "Curtains pull back; pan to the right" \
     "Spotlight reveals the lead; push in" \
     "The ensemble enters; crane up"
```

## Prompt Crafting for Continuity

- Mention recurring anchors: stairs, island, mirror, windows, etc.
- Keep movement pace similar between adjacent clips
- Use consistent camera height unless intentionally changing
- Repeat style terms ("cinematic lighting", "golden hour", "handheld feel")

Example prompt (per clip):

```
Keep lighting and color consistent with previous clip. Maintain the same staircase on the right frame edge.
Slow pan left over 7 seconds revealing the living area, holding on the sofas for the final 2 seconds.
```

## Tuning Parameters

- Duration per clip: 5–7 seconds for best quality
- Resolution: start 1280x720; move to 1920x1080 when locked
- Model: use fast model for iteration; switch to standard for finals

## Runway Veo vs Google Veo

- Both support stitching behavior
- Runway Veo: easy API key auth, credit-based pricing
- Google Veo: OAuth with Vertex AI, explicit per-video pricing

Choose based on your authentication preference and cost model.

## Using walk-through scripts

A helper script may exist (if provided) to illustrate end-to-end stitching flows:
- `walkthrough_and_stitch.sh` (optional): Example pipeline using ffmpeg

Review and adapt it to your needs if present in the repo.

## Troubleshooting Stitching

- Jumps between clips
  - Ensure previous last frame was applied (tool handles this automatically)
  - Align movement speed/direction across prompts
- Color/lighting drift
  - Reinforce consistent lighting in prompts; keep references consistent
- ffmpeg concat issues
  - Use the concat demuxer method; ensure correct file order and paths

## Next Steps

- See backends/google-veo.md and backends/runwayml.md for stitching-ready models
- Practice with 3–4 clips, then scale to 6–10 for long sequences
- Combine with the Prompt Guide for cinematic results
