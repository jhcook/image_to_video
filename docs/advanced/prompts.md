# Prompt Engineering Guide

Practical patterns for crafting prompts that produce stable, cinematic videos.

- New? Start with examples in user-guide.md and quick-start.md
- This guide shows reusable templates and tips

## Core Principles

1. Be specific about camera movement
2. Control timing with holds and pacing
3. Anchor continuity with recurring elements
4. Define lighting, lens, and mood
5. Keep language concise and concrete

## Prompt Structure Template

```
Scene setup:
- Subject/location: {brief description}
- Time of day / lighting: {golden hour, soft studio, etc.}
- Lens / style: {24mm wide, handheld, cinematic}

Camera movement (for the duration):
- Movement: {pan/dolly/crane/static}
- Direction: {left/right/forward/back/up}
- Speed: {slow/smooth/steady}
- Holds: {where and for how long}

Continuity constraints:
- Keep recurring elements consistent: {stairs, sideboard mirror, windows}
- Maintain straight lines; no bending walls; no hallucinated objects
- Stable exposure and white balance; no flicker

Output intent:
- Mood / grade: {cinematic, natural, high-end commercial}
- Framing: {center subject, thirds composition}
```

## Movement Patterns

- Slow pan right with 2s holds
- Dolly forward while panning left
- Static shot with subtle parallax
- Crane up from low angle to reveal the scene
- Push in over 5s, then hold final frame for 2s

Examples:

```bash
# Pan
"Slow pan from left to right across a modern living room; hold for 2 seconds when revealing the panoramic windows."

# Dolly + pan
"Dolly forward over 5 seconds while panning left to keep the kitchen island centered; hold for the final 2 seconds."

# Static
"Static tripod shot with subtle natural motion; breeze moving curtains; gentle exposure changes are acceptable."
```

## Lighting & Lens

- Lighting: golden hour, soft diffused, dramatic shadows, clean studio
- Lens: 24–28mm wide (walkthroughs), 50mm (portraits), macro for detail
- Color: cinematic grade, natural tones, high-key commercial

Examples:

```bash
"Golden hour lighting with warm side light; 24mm lens; cinematic color grade; natural contrast."
"Soft studio lighting on white sweep; product remains perfectly exposed; 50mm lens look."
```

## Continuity Anchors

Repeat across prompts (especially for stitching):
- Named objects: "the same staircase", "the ornate mirror", "the marble island"
- Geometry: "keep edges straight, no bending walls"
- Camera height: "eye-level camera height maintained"
- Style: "consistent golden hour lighting and cinematic color grade"

## Duration Guidance

- 5–7 seconds usually yields the best consistency
- Longer durations increase risk of drift; use stitching for long stories
- Runway Gen-4 is limited to 5 or 10 seconds

## Multi-Image Strategy

- Provide 2–3 images showing different angles of the same subject
- Order images to match the camera path when possible
- Use consistent lighting across references
- For Runway Gen-4, only the first image is used

## Example Prompts

### Real Estate Walkthrough (single clip)

```
Scene setup:
- Modern lower ground floor with staircase, living area, and window bar with stools.
- Golden hour lighting, 24mm lens, cinematic color grade.

Camera movement (10 seconds):
- Start on the foyer; hold 2s. Slow pan right revealing the staircase with white balusters and a window with shutters. 
- Dolly forward 5 seconds into the living area; pan left to sofas and wall-mounted TV. Hold 3s on the seating area.

Continuity constraints:
- Keep floorboards, sideboard with ornate mirror, cat tree, dining set, and curtains consistent across the scene.
- Keep edges straight; no warped geometry; no added text or people.
```

### Product 360 (studio)

```
Scene setup:
- Single product on a white sweep, soft studio lighting, 50mm lens look.

Camera movement (5 seconds):
- 360-degree rotation around the product at steady speed; keep product centered.

Continuity constraints:
- Background stays clean and white; no color shifts.
- Product edges remain sharp; no warping.

Output intent:
- High-end commercial look with natural shadows and subtle reflections.
```

### Nature Scene (cinematic)

```
Scene setup:
- Forest path at dawn with mist; gentle breeze; birds chirping in the distance.
- 24mm lens, cinematic grade, soft low-contrast look.

Camera movement (7 seconds):
- Slow dolly forward along the path; slight parallax in trees; hold final 1.5 seconds.

Continuity constraints:
- Keep fog density stable; no sudden lighting changes.
- Trees remain upright; edges straight; no bending.
```

## Prompt Iteration Tips

- Keep a fixed seed while iterating (`--seed 42`) to compare changes
- Change one variable at a time (movement, duration, lighting)
- Save prompts alongside outputs for traceability
- For drift, shorten duration or increase references

## Troubleshooting Prompts

- Output looks generic
  - Add more specifics: camera movement, objects, light direction, timing
- Warped geometry
  - Emphasize straight lines; reduce duration; add multi-angle references
- Style instability
  - Reinforce lighting and color grading terms across prompts
- Not following camera instructions
  - Use imperative, concise phrases; avoid ambiguous language

## Next Steps

- Try the Stitching Guide for long sequences
- Explore provider guides for model-specific nuances
- Build a library of reusable templates for your domain