# Download Real Fragments - Usage Examples

## Quick Start

### Install Dependencies
```bash
pip install requests pillow tqdm
```

### Download from All Sources
Download 30 images from both Wikimedia Commons and MET Museum:
```bash
python scripts/download_real_fragments.py --source all --limit 30
```

## Common Usage Patterns

### 1. Test Run (Small Dataset)
Start with a small number of images to test:
```bash
python scripts/download_real_fragments.py --source all --limit 5
```

### 2. Wikimedia Commons Only
Download only from Wikimedia Commons:
```bash
python scripts/download_real_fragments.py --source wikimedia --limit 20
```

### 3. MET Museum Only
Download only from MET Museum:
```bash
python scripts/download_real_fragments.py --source met --limit 20
```

### 4. High-Quality Images Only
Increase minimum resolution requirements:
```bash
python scripts/download_real_fragments.py --source all --limit 30 --min-width 1024 --min-height 768
```

### 5. Large Dataset
Download a larger dataset:
```bash
python scripts/download_real_fragments.py --source all --limit 100
```

### 6. Custom Output Directory
Save to a different location:
```bash
python scripts/download_real_fragments.py --source all --limit 30 --output-dir /path/to/my/fragments
```

## Expected Output

### Console Output
```
======================================================================
Archaeological Fragment Image Downloader
======================================================================
Source: all
Limit per source: 30
Output directory: data/raw/real_fragments
Minimum resolution: 800x600
======================================================================

======================================================================
WIKIMEDIA COMMONS
======================================================================
Fetching files from category: Sherds
Found 150 files in category
Wikimedia: 100%|████████████████████| 150/150 [05:23<00:00,  2.15s/it]
Downloaded: Ceramic_shard_Greece_500BC.jpg
Downloaded: Pottery_fragment_Roman.jpg
...
Metadata saved to data/raw/real_fragments/wikimedia/metadata.json

======================================================================
MET MUSEUM
======================================================================
Searching MET Museum for: ceramic fragment
Found 234 objects
MET Museum: 100%|█████████████████████| 234/234 [03:42<00:00,  1.05it/s]
Downloaded: met_12345_Terracotta_amphora_fragment.jpg
Downloaded: met_67890_Ceramic_bowl_shard.jpg
...
Metadata saved to data/raw/real_fragments/met/metadata.json

======================================================================
DOWNLOAD COMPLETE
======================================================================
Download Summary:
  Total Attempted: 60
  Successful: 55
  Failed: 5
  Skipped: 23

Images saved to: data/raw/real_fragments
Wikimedia images: 28
MET Museum images: 27
Total images: 55
======================================================================
```

### Directory Structure After Download
```
data/raw/real_fragments/
├── README.md                           # Attribution and source information
├── wikimedia/
│   ├── metadata.json                   # Detailed metadata for each image
│   ├── Ceramic_shard_Greece_500BC.jpg
│   ├── Pottery_fragment_Roman.jpg
│   └── ... (more images)
└── met/
    ├── metadata.json                   # Detailed metadata for each image
    ├── met_12345_Terracotta_amphora_fragment.jpg
    ├── met_67890_Ceramic_bowl_shard.jpg
    └── ... (more images)
```

### Metadata JSON Example (wikimedia/metadata.json)
```json
[
  {
    "filename": "Ceramic_shard_Greece_500BC.jpg",
    "original_title": "File:Ceramic shard from ancient Greece.jpg",
    "source": "Wikimedia Commons",
    "category": "Sherds",
    "url": "https://commons.wikimedia.org/wiki/File:...",
    "image_url": "https://upload.wikimedia.org/...",
    "width": 1920,
    "height": 1080,
    "mime": "image/jpeg",
    "artist": "John Doe",
    "license": "CC-BY-SA-4.0",
    "attribution_required": "yes",
    "download_date": "2026-04-08T10:15:30"
  }
]
```

### Log File (download_real_fragments.log)
A detailed log file is created in the current directory with:
- All download attempts
- Success/failure reasons
- API calls and responses
- Error messages and stack traces

## Troubleshooting

### Network Errors
If you encounter network timeouts:
```bash
# The script will automatically retry and continue with remaining images
# Check the log file for details: download_real_fragments.log
```

### Rate Limiting
The script includes built-in rate limiting:
- Wikimedia Commons: 0.5 requests/second
- MET Museum: 2 requests/second

These are conservative values that respect API terms of service.

### Image Quality Issues
If images don't meet quality requirements:
```bash
# Adjust minimum resolution
python scripts/download_real_fragments.py --source all --limit 30 --min-width 600 --min-height 400
```

### Missing Dependencies
```bash
pip install requests pillow tqdm
```

## Integration with Project

After downloading images, use them for testing:

```python
from pathlib import Path
from PIL import Image

# Load downloaded fragments
fragment_dir = Path("data/raw/real_fragments/wikimedia")
for img_path in fragment_dir.glob("*.jpg"):
    img = Image.open(img_path)
    print(f"Loaded {img_path.name}: {img.size}")
    # Process with your fragment reconstruction pipeline
```

## Attribution

Always check the README.md and metadata.json files created by the script for proper attribution requirements. Wikimedia Commons images may have different license requirements.

## API Limits

### Wikimedia Commons
- No hard limit, but be respectful
- Script uses 0.5 requests/second
- User-Agent header included

### MET Museum
- No published rate limit
- Script uses 2 requests/second
- Public API with CC0 images

## Performance

Typical download times (depends on network speed):
- 10 images: ~2-3 minutes
- 30 images: ~5-8 minutes
- 100 images: ~15-25 minutes

The script includes progress bars (with tqdm) to show real-time progress.
