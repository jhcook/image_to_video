# Quick Reference: Image Grouping for Stitching

## TL;DR - Three Ways to Control Images Per Clip

### 1. **Automatic (Current)** - Works with your filenames
```bash
# Your files: foyer1.png, living1.png, kitchen1.png
# Your prompts: fr_foyer1.txt, fr_living1.txt, fr_kitchen1.txt
# Auto-detects: fr_foyer → foyer*.png, fr_living → living*.png

./image2video.py --backend runway --stitch \
  -i ~/Downloads/FisherRoad/* \
  -p "$(cat prompts/fr_foyer1.txt)" \
     "$(cat prompts/fr_living1.txt)" \
     "$(cat prompts/fr_kitchen1.txt)"
```
**Result:** Automatically groups by keyword matching.

---

### 2. **Custom Script** - Full control
```bash
# Use the provided helper script
./generate_fisher_road.sh --dry-run  # See distribution first
./generate_fisher_road.sh            # Generate videos
```

Edit `generate_fisher_road.sh` to customize which images go with each clip.

---

### 3. **Manual Per-Clip** - Most precise
```bash
# Generate each clip separately with exact images

# Foyer clip: uses only foyer1 and foyer2
python image2video.py --backend runway \
  -i foyer1.png foyer2.png \
  -p "$(cat prompts/fr_foyer1.txt)" \
  -o foyer_clip.mp4

# Living room clip: uses living1, living2, living3
python image2video.py --backend runway \
  -i living1.png living2.png living3.png \
  -p "$(cat prompts/fr_living1.txt)" \
  -o living_clip.mp4

# Kitchen clip: uses both kitchen images
python image2video.py --backend runway \
  -i kitchen1.png kitchen2.png \
  -p "$(cat prompts/fr_kitchen1.txt)" \
  -o kitchen_clip.mp4
```

---

## How Auto-Detection Works

```
Image filenames: foyer1.png, foyer2.png, living1.png, living2.png, kitchen1.png
                 ↓            ↓            ↓             ↓             ↓
Keywords:        foyer        foyer        living        living        kitchen

Prompt files:    fr_foyer1.txt    fr_living1.txt    fr_kitchen1.txt
                    ↓                 ↓                  ↓
Pattern match:   "foyer" in name   "living" in name   "kitchen" in name
                    ↓                 ↓                  ↓
Uses images:     foyer1, foyer2    living1, living2   kitchen1
```

Supported keywords: `foyer`, `living`, `kitchen`, `garage`, `bedroom`, `bathroom`, `dining`, `hallway`, `entry`, `stairs`

---

## Checking Distribution Before Running

```bash
# See what will be used without generating (saves API credits!)
source venv/bin/activate
python image2video.py --backend runway --stitch \
  -i ~/Downloads/FisherRoad/* \
  -p "test1" "test2" "test3" \
  2>&1 | head -50
```

Look for this output:
```
📸 Image distribution per clip:
   Clip 1: 4 images (foyer1, foyer2, foyer3, foyer4)
   Clip 2: 5 images (living1, living2, living3, ... (5 total))
   Clip 3: 2 images (kitchen1, kitchen2)
```

---

## Your Specific Files

Based on your Fisher Road project:

| Prompt File      | Auto-Detected Images | Reason |
|------------------|---------------------|--------|
| fr_foyer1.txt    | foyer1-4.png       | "foyer" keyword in filename |
| fr_foyer2.txt    | foyer1-4.png       | "foyer" keyword in filename |
| fr_living1.txt   | living1-5.png      | "living" keyword in filename |
| fr_living2.txt   | living1-5.png      | "living" keyword in filename |
| fr_living3.txt   | living1-5.png      | "living" keyword in filename |
| fr_kitchen1.txt  | kitchen1-2.png     | "kitchen" keyword in filename |

**Note:** The API will only use the first 3 images per clip due to Veo's limit.

---

## Troubleshooting

**Q: All clips are getting all images**  
A: Your filenames don't contain recognizable keywords. Use Method 2 or 3 (custom script or manual per-clip).

**Q: Wrong images are being grouped**  
A: Check the "Image distribution" output before generation. Adjust filenames or use manual method.

**Q: Want different images for similar prompts (e.g., two foyer clips with different foyer images)**  
A: Use Method 3 (manual per-clip) to specify exact images for each.

---

## Next Steps

1. **Test distribution:** Run with `--dry-run` to see grouping
2. **Use automatic:** If grouping looks good, proceed with full command
3. **Use custom script:** Edit `generate_fisher_road.sh` for full control
4. **Generate individually:** Use manual method for precise control

For more details, see `IMAGE_GROUPING_GUIDE.md`.
