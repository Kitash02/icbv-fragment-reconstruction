# Scripts Directory

This directory contains utility scripts for the ICBV Fragment Reconstruction project.

## Available Scripts

### download_real_fragments.py

Automates downloading of real archaeological fragment images from open-access sources.

**Features:**
- Downloads from Wikimedia Commons (Category:Sherds)
- Downloads from MET Museum Open Access API
- Filters for quality images (minimum 800x600 resolution)
- Respects API rate limits
- Creates metadata files with attribution information
- Generates README with source information

**Dependencies:**
```bash
pip install requests pillow tqdm
```

**Usage:**

Download from all sources (default 30 images per source):
```bash
python scripts/download_real_fragments.py --source all --limit 30
```

Download only from Wikimedia Commons:
```bash
python scripts/download_real_fragments.py --source wikimedia --limit 20
```

Download only from MET Museum:
```bash
python scripts/download_real_fragments.py --source met --limit 10
```

Custom output directory:
```bash
python scripts/download_real_fragments.py --source all --limit 50 --output-dir /path/to/output
```

Custom minimum resolution:
```bash
python scripts/download_real_fragments.py --source all --limit 30 --min-width 1024 --min-height 768
```

**Output Structure:**
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

**Logging:**
All download activity is logged to `download_real_fragments.log` in the current directory.

**Error Handling:**
- Network failures are logged and download continues
- Invalid images are skipped
- Rate limiting prevents API overload
- Duplicate downloads are automatically skipped

**Attribution:**
The script automatically generates:
- Individual metadata.json files per source
- A comprehensive README.md with attribution information
- License information for each downloaded image

---

### preprocess_complex_images.py

Handles multi-fragment images and complex backgrounds to make them usable for the main reconstruction pipeline.

**Features:**
- Auto-split: Automatically detects and separates multiple fragments in one image
- Background removal: Uses GrabCut algorithm for complex backgrounds
- Manual mode: Interactive cropping for problematic images
- Batch processing with progress tracking
- Generates processing manifest and detailed logs

**Dependencies:**
Already included in main requirements.txt (opencv-python, numpy)

**Usage:**

Automatically split multi-fragment images:
```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/real_fragments/wikimedia \
    --output data/raw/real_fragments_validated/wikimedia_processed \
    --mode auto
```

Background removal with GrabCut:
```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/real_fragments/wikimedia \
    --output data/raw/real_fragments_validated/wikimedia_processed \
    --mode background
```

Interactive manual cropping:
```bash
python scripts/preprocess_complex_images.py \
    --input data/raw/real_fragments/wikimedia \
    --output data/raw/real_fragments_validated/wikimedia_processed \
    --mode manual
```

Process specific images:
```bash
python scripts/preprocess_complex_images.py \
    --input data/raw \
    --output data/processed \
    --mode auto \
    --pattern "*14_scherven*"
```

Resume interrupted processing:
```bash
python scripts/preprocess_complex_images.py \
    --input data/raw \
    --output data/processed \
    --mode auto \
    --skip-existing
```

**Output Structure:**
```
output_directory/
├── manifest.json                    # Processing metadata & transformation log
├── preprocess_YYYYMMDD_HHMMSS.log  # Detailed processing log
├── original_name_fragment_001.jpg   # Extracted fragments
├── original_name_fragment_002.jpg
└── ...
```

**Manual Mode Controls:**
- Click and drag: Draw bounding box around fragment
- Press 's': Save current selection
- Press 'r': Reset selection
- Press 'q': Quit

**Performance:**
- Auto mode: ~50 fragments/minute
- Background mode: ~10 fragments/minute (GrabCut is slower but higher quality)
- Manual mode: User-dependent, typically 2-5 minutes per image

**Algorithm Details:**
- Gaussian smoothing (Lecture 22)
- Otsu thresholding for automatic binarization
- Morphological operations (closing/opening)
- Connected component analysis (Lecture 23)
- GrabCut segmentation for complex backgrounds

See `README_PREPROCESSING.md` for comprehensive documentation, algorithm details, and troubleshooting.

---

### analyze_benchmark_results.py

Analyzes benchmark results from fragment reconstruction tests.

**Usage:**
```bash
python scripts/analyze_benchmark_results.py outputs/benchmark_results.json
```

See `README_analyze.md` for detailed documentation.

---

### profile_performance.py

Profiles the reconstruction pipeline to identify performance bottlenecks.

**Usage:**
```bash
python scripts/profile_performance.py --input data/sample --output profile_results
```

See `README_PROFILING.md` for detailed documentation.

---

## Notes

- The script uses conservative rate limiting to respect API terms of service
- Images are validated for format (JPG/PNG) and minimum resolution
- Progress bars are shown if tqdm is installed
- All metadata includes download date and source information
