# Image Grouping Guide for Stitching Mode

When using `--stitch` mode, you can control which reference images are used for each clip using three different methods:

## Method 1: Simple Keyword Matching (Automatic)

**How it works:** The script automatically groups images by keywords in their filenames and matches them with keywords in prompts.

**Example:**
```bash
# Images: foyer1.png, foyer2.png, living1.png, living2.png, kitchen1.png
# Prompts contain keywords: "foyer", "living", "kitchen"

./image2video.py --provider runway --stitch \
  -i ~/images/foyer*.png ~/images/living*.png ~/images/kitchen*.png \
  -p "Camera pans across the foyer entrance" \
     "Dolly through the living room space" \
     "Pan around the modern kitchen"

# Result:
#   Clip 1 (foyer prompt) -> foyer1.png, foyer2.png
#   Clip 2 (living prompt) -> living1.png, living2.png
#   Clip 3 (kitchen prompt) -> kitchen1.png
```

**Limitation:** Requires keywords in your prompt text.

---

## Method 2: Filename Pattern Matching (Current Implementation)

**How it works:** Groups images by removing numbers from filenames, creating natural groups.

**Example:**
```bash
# Images organized by prefix:
#   foyer1.png, foyer2.png, foyer3.png
#   living1.png, living2.png, living3.png, living4.png
#   kitchen1.png, kitchen2.png

./image2video.py --provider runway --stitch \
  -i ~/Downloads/FisherRoad/* \
  -p "$(cat prompts/fr_foyer1.txt)" \
     "$(cat prompts/fr_foyer2.txt)" \
     "$(cat prompts/fr_living1.txt)" \
     "$(cat prompts/fr_living2.txt)" \
     "$(cat prompts/fr_kitchen1.txt)"

# Auto-detects groups: foyer*, living*, kitchen*
# Matches based on prompt filename if available (fr_foyer1.txt -> foyer*)
```

**Current behavior with your files:**
- Prompt `fr_foyer1.txt` → uses `foyer*.png` images
- Prompt `fr_living1.txt` → uses `living*.png` images
- Prompt `fr_kitchen1.txt` → uses `kitchen*.png` images

---

## Method 3: Manual Specification (Most Control)

**How it works:** Create a simple mapping file or use a wrapper script to specify exactly which images go with each prompt.

**Option A: Create a wrapper script**

Create `generate_fisher_road.sh`:
```bash
#!/bin/bash
# Custom image groups for Fisher Road walkthrough

source venv/bin/activate

python image2video.py --provider runway --stitch \
  -i ~/Downloads/FisherRoad/foyer1.png \
     ~/Downloads/FisherRoad/foyer2.png \
  -p "$(cat prompts/fr_foyer1.txt)" \
  && \
python image2video.py --provider runway --stitch \
  -i ~/Downloads/FisherRoad/living1.png \
     ~/Downloads/FisherRoad/living2.png \
     ~/Downloads/FisherRoad/living3.png \
  -p "$(cat prompts/fr_living1.txt)" \
  --output living_clip.mp4
```

**Option B: Use separate directories**
```bash
# Organize images into directories
mkdir -p clips/foyer clips/living clips/kitchen
cp foyer*.png clips/foyer/
cp living*.png clips/living/
cp kitchen*.png clips/kitchen/

# Generate each clip with specific images
./image2video.py --provider runway --stitch \
  -i clips/foyer/* -p "$(cat prompts/fr_foyer1.txt)" -o foyer_clip.mp4

./image2video.py --provider runway --stitch \
  -i clips/living/* -p "$(cat prompts/fr_living1.txt)" -o living_clip.mp4
```

---

## Current Auto-Detection Logic

The script uses this logic to match images to clips:

1. **Extract keywords from image filenames:**
   - `foyer1.png` → keyword: `foyer`
   - `living2.png` → keyword: `living`
   - `kitchen1.png` → keyword: `kitchen`

2. **Try to extract keywords from prompt filenames:**
   - `fr_foyer1.txt` → looks for `foyer` in pattern
   - `fr_living1.txt` → looks for `living` in pattern
   - Pattern: `_(foyer|living|kitchen|garage|bedroom|bathroom|dining)`

3. **Match keyword from prompt file to image groups:**
   - If `fr_foyer1.txt` → uses all `foyer*.png` images
   - If `fr_living1.txt` → uses all `living*.png` images

4. **Fallback:** If no match found, uses ALL images for that clip

---

## Checking Image Distribution

When you run the command, you'll see the distribution:

```
📸 Image distribution per clip:
   Clip 1: 4 images (foyer1, foyer2, foyer3, foyer4)
           Prompt: You are rendering a single continuous walkthr...
   Clip 2: 5 images (living1, living2, living3, ... (5 total))
           Prompt: You are rendering a single continuous walkthr...
   Clip 3: 2 images (kitchen1, kitchen2)
           Prompt: You are rendering a single continuous walkthr...
```

This shows exactly which images will be used for each clip BEFORE generation starts.

---

## Recommendations for Your Fisher Road Project

Given your file structure:
```
Images: foyer1-4.png, living1-5.png, kitchen1-2.png
Prompts: fr_foyer1.txt, fr_foyer2.txt, fr_living1.txt, fr_living2.txt, fr_living3.txt, fr_kitchen1.txt
```

**Best approach:** Rename your prompt files to match the image groups:

```bash
# Current names -> Suggested names
fr_foyer1.txt    -> foyer_clip1.txt   # Uses foyer*.png
fr_foyer2.txt    -> foyer_clip2.txt   # Uses foyer*.png
fr_living1.txt   -> living_clip1.txt  # Uses living*.png
fr_living2.txt   -> living_clip2.txt  # Uses living*.png
fr_living3.txt   -> living_clip3.txt  # Uses living*.png
fr_kitchen1.txt  -> kitchen_clip1.txt # Uses kitchen*.png
```

Or keep current names and the script will auto-detect based on the `fr_foyer`, `fr_living`, `fr_kitchen` patterns.

---

## Testing Without Credits

You can see the image distribution without generating videos:

```bash
# Add --help or check the distribution output
./image2video.py --provider runway --stitch \
  -i ~/Downloads/FisherRoad/* \
  -p "$(cat prompts/fr_foyer1.txt)" \
     "$(cat prompts/fr_living1.txt)" \
  2>&1 | grep -A 20 "Image distribution"
```

This shows which images will be used for each clip before the API call.
