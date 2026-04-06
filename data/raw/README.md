# Real Fragment Images

Place your real archaeological fragment images here.

## Requirements for best results

- One fragment per image (pre-segmented)
- Format: PNG or JPG
- Background: plain white or dark — the preprocessing detects it automatically
- Resolution: at least 300×300 pixels recommended

## Sources for test images

Free archaeological imagery suitable for this pipeline:

- **Wikimedia Commons — Sherds category**
  https://commons.wikimedia.org/wiki/Category:Sherds
  Many museum-quality photographs of pottery fragments.

- **The British Museum Collection Online**
  https://www.britishmuseum.org/collection
  Search "sherd" or "potsherd" — most images are open-access (CC BY-NC-SA 4.0).

- **MET Open Access Collection**
  https://www.metmuseum.org/art/collection
  Filter by "Open Access" — includes ceramic fragments from excavations.

## Running on real images

```bash
python src/main.py \
  --input  data/real \
  --output outputs/results \
  --log    outputs/logs
```

## Notes on preprocessing

The pipeline will automatically:
- Detect whether the background is light or dark
- Try both Otsu and adaptive thresholding and pick the better result
- Apply morphological cleanup to fill gaps caused by shadows
- Select the largest connected region as the fragment

If a fragment image is not processed correctly, check:
1. That the fragment occupies most of the image frame
2. That the background is relatively uniform (avoid heavily patterned surfaces)
3. That the image is in focus
