# Archaeological Fragment Image Dataset Sources

This document provides comprehensive guidance on sourcing high-quality archaeological fragment images for testing and expanding the ICBV Fragment Reconstruction project dataset.

## Table of Contents
1. [Primary Image Sources](#primary-image-sources)
2. [Academic and Research Sources](#academic-and-research-sources)
3. [Usage Guidelines and Licensing](#usage-guidelines-and-licensing)
4. [Quality Criteria for Fragment Images](#quality-criteria-for-fragment-images)
5. [Download Instructions](#download-instructions)
6. [Image Preprocessing Tips](#image-preprocessing-tips)

---

## Primary Image Sources

### 1. Wikimedia Commons

**Category: Sherds**
- **Direct Link**: [Category:Sherds](https://commons.wikimedia.org/wiki/Category:Sherds)
- **Subcategories**:
  - [Pottery sherds](https://commons.wikimedia.org/wiki/Category:Pottery_sherds)
  - [Ceramic fragments](https://commons.wikimedia.org/wiki/Category:Ceramic_fragments)
  - [Archaeological pottery](https://commons.wikimedia.org/wiki/Category:Archaeological_pottery)

**Advantages**:
- All images are openly licensed (CC BY, CC BY-SA, or Public Domain)
- High-resolution images available
- Well-documented with metadata
- Easy bulk download via API

**Search Tips**:
- Use search terms: "sherd", "potsherd", "ceramic fragment", "pottery fragment"
- Filter by license type in Advanced Search
- Look for archaeological museum collections

### 2. British Museum Collection

**Search Parameters**:
- **Base URL**: https://www.britishmuseum.org/collection
- **Search Terms**:
  - "potsherd"
  - "sherd"
  - "ceramic fragment"
  - "pottery fragment"

**License Filter**:
- Select: **CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike)
- This license allows use for research and educational purposes

**Access Method**:
1. Navigate to the British Museum Collection website
2. Enter search term in the collection search
3. Apply filters:
   - Type: "Object"
   - Material: "ceramic", "pottery", "terracotta"
   - License: "CC BY-NC-SA 4.0"
4. Select high-resolution image downloads where available

**Notable Collections**:
- Ancient Greek pottery fragments
- Roman ceramic sherds
- Near Eastern archaeological materials
- Egyptian pottery fragments

### 3. Metropolitan Museum of Art (MET)

**Open Access Collection**:
- **Base URL**: https://www.metmuseum.org/art/collection
- **Open Access Filter**: https://www.metmuseum.org/art/collection/search#!?showOnly=openAccess

**Search Strategy**:
1. Enable "Open Access" filter (Public Domain images)
2. Search terms:
   - "ceramic fragment"
   - "pottery fragment"
   - "sherd"
   - "ostracon" (inscribed pottery fragments)
3. Filter by:
   - Classification: "Ceramics" or "Vases"
   - Culture/Period: Greek, Roman, Egyptian, etc.

**API Access**:
- The MET provides a public API for bulk access
- API Documentation: https://metmuseum.github.io/
- All Open Access images can be downloaded programmatically

**Advantages**:
- All Open Access images are Public Domain (CC0)
- Very high-resolution images (often 4000+ pixels)
- Excellent documentation and provenance

### 4. Smithsonian Institution

**Collections**:
- **URL**: https://collections.si.edu/search/
- **License**: Many images under CC0 (Public Domain)

**Search Tips**:
- Use "Usage Conditions: CC0" filter
- Search: "pottery fragment", "ceramic sherd", "archaeological ceramic"
- Particularly strong in:
  - American archaeology
  - Mesoamerican pottery
  - Asian ceramics

---

## Academic and Research Sources

### 5. Perseus Digital Library

**URL**: http://www.perseus.tufts.edu/
**Focus**: Classical archaeology, particularly Greek and Roman materials

**Resources**:
- Digital images of archaeological artifacts
- Searchable database of ancient ceramics
- High-quality scholarly documentation
- Many images available for educational use

**Access**:
- Free for academic and educational purposes
- Attribution required
- Check individual image licenses

### 6. Archaeological Data Service (ADS)

**URL**: https://archaeologydataservice.ac.uk/
**Focus**: UK-based archaeological research data

**Features**:
- Digital archives from UK excavations
- Includes pottery databases with images
- Often CC BY licensed
- Detailed stratigraphic and contextual information

**Key Collections**:
- Roman pottery databases
- Medieval ceramic studies
- Post-medieval pottery assemblages

### 7. Open Context

**URL**: https://opencontext.org/
**Focus**: Open access archaeological data

**Features**:
- CC BY licensed data and images
- Linked open data format
- Pottery and ceramic assemblages from worldwide excavations
- API access available

### 8. Digital Archaeological Record (tDAR)

**URL**: https://core.tdar.org/
**Focus**: North American and global archaeology

**Features**:
- Many open access datasets
- Pottery and ceramic images
- Requires free registration
- Various license types (check individual items)

### 9. University Museum Collections

**Notable Collections**:
- **Penn Museum**: https://www.penn.museum/collections/
- **Harvard Art Museums**: https://harvardartmuseums.org/collections
- **Yale Peabody Museum**: https://peabody.yale.edu/collections
- **Ashmolean Museum**: https://collections.ashmolean.org/

**General Approach**:
- Many have digitized collections online
- Often CC BY or similar licenses
- High-quality images with scholarly documentation

---

## Usage Guidelines and Licensing

### License Types and Permissions

#### CC0 (Public Domain)
- **Use**: Unrestricted, including commercial use
- **Attribution**: Not required but recommended
- **Best for**: Research, testing, publication
- **Sources**: MET Museum, many Smithsonian items

#### CC BY (Attribution)
- **Use**: Free use including commercial
- **Attribution**: Required (photographer/institution)
- **Modifications**: Allowed
- **Sources**: Wikimedia Commons, some museums

#### CC BY-SA (Attribution-ShareAlike)
- **Use**: Free use including commercial
- **Attribution**: Required
- **Modifications**: Must share under same license
- **Sources**: Wikimedia Commons, some museums

#### CC BY-NC-SA (Attribution-NonCommercial-ShareAlike)
- **Use**: Non-commercial only
- **Attribution**: Required
- **Modifications**: Must share under same license
- **Best for**: Academic research and education
- **Sources**: British Museum, many academic institutions

### Attribution Best Practices

**Minimum Attribution Template**:
```
[Image Title/Object ID]
[Institution Name]
[Photographer Name, if available]
[License Type]
[URL or Accession Number]
```

**Example**:
```
Red-Figure Pottery Fragment, Object 1998.123
Metropolitan Museum of Art
CC0 1.0 Public Domain
https://www.metmuseum.org/art/collection/search/123456
```

### Usage for Research Projects

**Academic Research**:
- Most CC licenses are suitable
- Always maintain attribution records
- Include license information in publications

**Algorithm Testing and Development**:
- Prefer CC0, CC BY, or CC BY-SA
- Avoid NC (NonCommercial) if planning future commercial applications
- Document all sources in project README

**Dataset Publication**:
- Verify you can redistribute under chosen licenses
- Maintain metadata files with attribution
- Consider creating license matrix if using mixed sources

---

## Quality Criteria for Fragment Images

### Essential Requirements

#### 1. **Clean Background**
- **Ideal**: Neutral white, gray, or black background
- **Avoid**: Cluttered backgrounds, measurement scales obscuring edges
- **Why**: Simplifies segmentation and edge detection

#### 2. **Good Lighting**
- **Ideal**: Even, diffused lighting from multiple angles
- **Avoid**: Harsh shadows, glare, hot spots
- **Look for**: Consistent brightness across the fragment
- **Why**: Critical for texture analysis and edge detection

#### 3. **Proper Focus and Resolution**
- **Minimum**: 1000 pixels on longest dimension
- **Ideal**: 2000+ pixels for detailed analysis
- **Check**: Sharp edges, visible surface details
- **Why**: Algorithm performance depends on edge clarity

#### 4. **Fragment Orientation**
- **Ideal**: Fragment laid flat, photographed from directly above
- **Acceptable**: Slight angles if edges are clearly visible
- **Avoid**: Extreme perspective distortion
- **Why**: Simplifies geometric analysis

#### 5. **Edge Visibility**
- **Critical**: All edges must be clearly distinguishable
- **Ideal**: High contrast between fragment and background
- **Check**: No edge obscured by shadows or artifacts
- **Why**: Edge matching is core to reconstruction

### Desirable Features

#### 6. **Multiple Views**
- Front and back views of the same fragment
- Different lighting conditions
- Useful for 3D reconstruction experiments

#### 7. **Scale Reference**
- Measurement scale in image (can be cropped later)
- Size information in metadata
- Useful for real-world dimension analysis

#### 8. **Surface Texture**
- Visible surface decoration or texture
- Color variation patterns
- Useful for advanced matching algorithms

#### 9. **Fragment Type Diversity**
- Rim fragments (curved edges)
- Body sherds (straight edges)
- Decorated vs. plain surfaces
- Various ceramic types (fine ware, coarse ware)

### Image Quality Checklist

Before downloading an image, verify:
- [ ] Clear, unobstructed view of all fragment edges
- [ ] Neutral background (or easily removable)
- [ ] Good contrast and lighting
- [ ] Sufficient resolution (1000+ pixels)
- [ ] In-focus throughout
- [ ] Appropriate license for your use case
- [ ] Metadata/documentation available

### Images to Avoid

**Poor Quality Indicators**:
- Blurry or out-of-focus images
- Extreme perspective distortion
- Multiple fragments in one image (unless you plan to segment)
- Heavy shadow or glare
- Low resolution (<500 pixels)
- Watermarks over critical areas
- Complex backgrounds that are difficult to remove

---

## Download Instructions

### Method 1: Manual Download from Wikimedia Commons

**Single Image**:
1. Navigate to image page
2. Click on image to view full resolution
3. Right-click → "Save Image As"
4. Save with descriptive filename

**Batch Download**:
1. Install [Wikimedia Commons Mass Downloader](https://github.com/Commonists/Commons-mass-downloader)
2. Create category list (e.g., "Category:Sherds")
3. Run downloader with category parameter
4. Images saved to specified directory

### Method 2: Using wget/curl (Command Line)

**Example for single image**:
```bash
wget -O fragment_001.jpg "https://upload.wikimedia.org/wikipedia/commons/full-url-here"
```

**Example for batch (with URL list)**:
```bash
# Create urls.txt with one URL per line
while read url; do
    wget "$url"
done < urls.txt
```

### Method 3: Wikimedia Commons API

**Python Example**:
```python
import requests
import json

def download_commons_category(category, limit=50):
    """Download images from a Wikimedia Commons category"""
    url = "https://commons.wikimedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "generator": "categorymembers",
        "gcmtitle": f"Category:{category}",
        "gcmtype": "file",
        "gcmlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size|mime"
    }

    response = requests.get(url, params=params)
    data = response.json()

    images = []
    if "query" in data and "pages" in data["query"]:
        for page in data["query"]["pages"].values():
            if "imageinfo" in page:
                info = page["imageinfo"][0]
                images.append({
                    "title": page["title"],
                    "url": info["url"],
                    "width": info["width"],
                    "height": info["height"]
                })

    return images

# Usage
sherds = download_commons_category("Sherds", limit=100)
for img in sherds:
    print(f"{img['title']}: {img['url']}")
```

### Method 4: MET Museum API

**Python Example**:
```python
import requests
import json

def search_met_collection(query, department_id=None):
    """Search MET Museum collection"""
    base_url = "https://collectionapi.metmuseum.org/public/collection/v1"

    # Search for objects
    search_params = {"q": query}
    if department_id:
        search_params["departmentId"] = department_id

    search_url = f"{base_url}/search"
    response = requests.get(search_url, params=search_params)
    object_ids = response.json().get("objectIDs", [])

    # Get details for each object
    objects = []
    for obj_id in object_ids[:50]:  # Limit to first 50
        obj_url = f"{base_url}/objects/{obj_id}"
        obj_response = requests.get(obj_url)
        obj_data = obj_response.json()

        # Filter for Open Access images
        if obj_data.get("isPublicDomain") and obj_data.get("primaryImage"):
            objects.append({
                "id": obj_id,
                "title": obj_data.get("title"),
                "image_url": obj_data.get("primaryImage"),
                "culture": obj_data.get("culture"),
                "period": obj_data.get("period")
            })

    return objects

# Usage
ceramic_fragments = search_met_collection("ceramic fragment")
for obj in ceramic_fragments:
    print(f"{obj['title']}: {obj['image_url']}")
```

### Method 5: British Museum Collection

**Manual Download**:
1. Navigate to collection search results
2. Click on individual objects
3. Select "Download image" option
4. Choose resolution (select highest available)
5. Image downloads with object ID in filename

**Bulk Download Note**:
- British Museum does not provide a public API
- Use manual download or browser automation tools
- Respect rate limits and terms of service

### Organizing Downloaded Images

**Recommended Directory Structure**:
```
dataset/
├── raw/
│   ├── wikimedia_commons/
│   │   ├── sherds_001.jpg
│   │   ├── sherds_002.jpg
│   │   └── metadata.json
│   ├── met_museum/
│   │   ├── met_123456.jpg
│   │   └── metadata.json
│   └── british_museum/
│       ├── bm_2024_001.jpg
│       └── metadata.json
├── processed/
│   ├── background_removed/
│   ├── normalized/
│   └── segmented/
└── metadata/
    ├── licenses.csv
    └── attribution.txt
```

**Metadata File Template (JSON)**:
```json
{
  "images": [
    {
      "filename": "sherds_001.jpg",
      "source": "Wikimedia Commons",
      "url": "https://commons.wikimedia.org/wiki/File:Example.jpg",
      "license": "CC BY-SA 4.0",
      "author": "Photographer Name",
      "institution": "Museum Name",
      "object_id": "2024.123",
      "description": "Roman pottery sherd",
      "date_downloaded": "2026-04-08",
      "dimensions": {
        "width": 2048,
        "height": 1536
      }
    }
  ]
}
```

---

## Image Preprocessing Tips

### Background Removal

**Using Python/OpenCV**:
```python
import cv2
import numpy as np

def remove_background(image_path, output_path):
    """Simple background removal for fragments on neutral backgrounds"""
    img = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold to separate fragment from background
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Create mask
    mask = cv2.bitwise_not(thresh)

    # Apply mask to original image
    result = cv2.bitwise_and(img, img, mask=mask)

    # Make background white
    background = np.full(img.shape, 255, dtype=np.uint8)
    background = cv2.bitwise_and(background, background, mask=thresh)
    result = cv2.add(result, background)

    cv2.imwrite(output_path, result)
    return result
```

### Standardization

**Consistent Sizing**:
```python
def standardize_image(image_path, target_size=(1024, 1024)):
    """Resize image while maintaining aspect ratio"""
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    # Calculate scaling factor
    scale = min(target_size[0]/w, target_size[1]/h)
    new_w, new_h = int(w*scale), int(h*scale)

    # Resize
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

    # Create canvas and center image
    canvas = np.full((target_size[1], target_size[0], 3), 255, dtype=np.uint8)
    y_offset = (target_size[1] - new_h) // 2
    x_offset = (target_size[0] - new_w) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas
```

### Quality Checks

**Automated Quality Assessment**:
```python
def assess_image_quality(image_path):
    """Check if image meets quality criteria"""
    img = cv2.imread(image_path)

    if img is None:
        return {"valid": False, "reason": "Unable to read image"}

    h, w = img.shape[:2]

    # Check resolution
    if min(h, w) < 1000:
        return {"valid": False, "reason": f"Resolution too low: {w}x{h}"}

    # Check if image is too blurry (Laplacian variance)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()

    if blur_score < 100:
        return {"valid": False, "reason": f"Image too blurry: {blur_score:.2f}"}

    return {
        "valid": True,
        "resolution": f"{w}x{h}",
        "blur_score": blur_score
    }
```

---

## Additional Resources

### Online Tools
- **Background Removal**: remove.bg (for quick single-image processing)
- **Batch Rename**: Bulk Rename Utility (Windows) or rename command (Linux/Mac)
- **Image Conversion**: ImageMagick for batch format conversion

### Communities and Forums
- **r/archaeology**: Reddit community for archaeological discussions
- **Archaeological Institute of America**: Professional organization
- **Computer Applications in Archaeology (CAA)**: Conference and community

### Further Reading
- "Digital Archaeology: Bridging Method and Theory" by Huggett & Ross
- "Computational Approaches to Archaeological Spaces" edited by Bevan & Lake
- MET Museum's Digital Underground blog on collection digitization

---

## Quick Start Checklist

To quickly build a test dataset:

1. **Start with Wikimedia Commons**
   - [ ] Search "Category:Sherds"
   - [ ] Download 20-30 high-quality images
   - [ ] Save license information

2. **Add MET Museum Images**
   - [ ] Use Open Access filter
   - [ ] Search "ceramic fragment"
   - [ ] Download 10-15 high-res images

3. **Organize and Document**
   - [ ] Create directory structure
   - [ ] Generate metadata.json file
   - [ ] Record all attributions

4. **Preprocess**
   - [ ] Remove backgrounds
   - [ ] Standardize sizes
   - [ ] Run quality checks

5. **Test with Algorithms**
   - [ ] Run edge detection
   - [ ] Verify segmentation works
   - [ ] Iterate on quality criteria

---

## Contact and Contributions

For questions or to suggest additional sources:
- Create an issue in the project repository
- Update this document with new sources as you discover them
- Share quality assessment results to help others

---

**Last Updated**: 2026-04-08
**Version**: 1.0
**Maintainer**: ICBV Fragment Reconstruction Project
