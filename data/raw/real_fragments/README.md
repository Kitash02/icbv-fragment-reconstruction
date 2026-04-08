# Real Archaeological Fragment Images

This directory contains real archaeological fragment images downloaded from open-access sources.

**Download Date:** 2026-04-08 10:20:24

## Sources

### Wikimedia Commons
- **Category:** Sherds
- **Images Downloaded:** 8
- **License:** Various open licenses (see individual metadata)
- **URL:** https://commons.wikimedia.org/wiki/Category:Sherds

### MET Museum Open Access
- **Search Terms:** ceramic fragment, potsherd, pottery shard
- **Images Downloaded:** 20
- **License:** CC0 (Public Domain)
- **URL:** https://www.metmuseum.org/art/collection

## Directory Structure

```
data/raw/real_fragments/
├── wikimedia/
│   ├── metadata.json
│   └── [image files]
├── met/
│   ├── metadata.json
│   └── [image files]
└── README.md
```

## Metadata Files

Each source directory contains a `metadata.json` file with detailed information about each image:

- **Wikimedia Commons metadata includes:**
  - Original filename and title
  - Image URL and description URL
  - Dimensions (width, height)
  - License information
  - Artist/attribution (when available)

- **MET Museum metadata includes:**
  - Object ID and title
  - Culture, period, and date
  - Medium and department
  - Object URL and image URL
  - License (CC0)

## Attribution

### Wikimedia Commons Images
Images from Wikimedia Commons are used under their respective open licenses. Please refer to the `metadata.json` file in the `wikimedia/` directory for specific license information and attribution requirements for each image.

### MET Museum Images
Images from the MET Museum are in the public domain (CC0). The Metropolitan Museum of Art provides these images under the Creative Commons Zero license, meaning you can use them without restriction.

**Citation:**
```
The Metropolitan Museum of Art, Open Access Initiative
https://www.metmuseum.org/about-the-met/policies-and-documents/open-access
```

## Usage Guidelines

1. **Research and Educational Use:** These images are intended for research and educational purposes in the field of archaeological fragment reconstruction.

2. **Attribution:** While MET images don't require attribution, it's good practice to cite the source. For Wikimedia Commons images, please check individual license requirements.

3. **Quality:** Images have been filtered to meet minimum quality requirements:
   - Minimum resolution: 800x600 pixels
   - Format: JPG or PNG
   - Clear, good quality images

## Scripts

Images were downloaded using the automated script:
```bash
python scripts/download_real_fragments.py --source all --limit 30
```

## Contact & Issues

If you have questions about the images or their usage, please refer to:
- Wikimedia Commons: https://commons.wikimedia.org/
- MET Museum: https://www.metmuseum.org/about-the-met/policies-and-documents/open-access

---

*Last updated: 2026-04-08*
