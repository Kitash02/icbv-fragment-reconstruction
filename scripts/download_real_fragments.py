#!/usr/bin/env python3
"""
Script to download real archaeological fragment images from open-access sources.

This script downloads images from:
1. Wikimedia Commons (Category:Sherds)
2. MET Museum Open Access API

Usage:
    python scripts/download_real_fragments.py --source all --limit 30
    python scripts/download_real_fragments.py --source wikimedia --limit 20
    python scripts/download_real_fragments.py --source met --limit 10
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, unquote, urlparse

import requests
from PIL import Image

# Try to import tqdm for progress bars
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Note: Install tqdm for progress bars: pip install tqdm")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_real_fragments.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DownloadStats:
    """Track download statistics."""

    def __init__(self):
        self.total_attempted = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []

    def record_success(self):
        self.total_attempted += 1
        self.successful += 1

    def record_failure(self, reason: str):
        self.total_attempted += 1
        self.failed += 1
        self.errors.append(reason)

    def record_skip(self):
        self.skipped += 1

    def summary(self) -> str:
        return (f"Download Summary:\n"
                f"  Total Attempted: {self.total_attempted}\n"
                f"  Successful: {self.successful}\n"
                f"  Failed: {self.failed}\n"
                f"  Skipped: {self.skipped}")


class RateLimiter:
    """Simple rate limiter to respect API limits."""

    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time = 0.0

    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_call_time

        if time_since_last_call < self.min_interval:
            sleep_time = self.min_interval - time_since_last_call
            time.sleep(sleep_time)

        self.last_call_time = time.time()


class WikimediaDownloader:
    """Download archaeological fragment images from Wikimedia Commons."""

    def __init__(self, output_dir: Path, min_width: int = 800, min_height: int = 600):
        self.output_dir = output_dir
        self.min_width = min_width
        self.min_height = min_height
        self.api_url = "https://commons.wikimedia.org/w/api.php"
        self.rate_limiter = RateLimiter(calls_per_second=0.5)  # Conservative rate
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchaeologicalFragmentDownloader/1.0 (Educational Research)'
        })
        self.metadata = []

    def get_category_members(self, category: str, limit: int) -> List[Dict]:
        """Get list of files from a Wikimedia Commons category."""
        logger.info(f"Fetching files from category: {category}")

        members = []
        params = {
            'action': 'query',
            'list': 'categorymembers',
            'cmtitle': f'Category:{category}',
            'cmtype': 'file',
            'cmlimit': min(limit, 500),  # API max is 500
            'format': 'json'
        }

        try:
            self.rate_limiter.wait()
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'query' in data and 'categorymembers' in data['query']:
                members = data['query']['categorymembers']
                logger.info(f"Found {len(members)} files in category")
            else:
                logger.warning("No files found in category")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching category members: {e}")

        return members[:limit]

    def get_image_info(self, filename: str) -> Optional[Dict]:
        """Get detailed information about an image file."""
        params = {
            'action': 'query',
            'titles': filename,
            'prop': 'imageinfo',
            'iiprop': 'url|size|mime|extmetadata',
            'format': 'json'
        }

        try:
            self.rate_limiter.wait()
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if 'imageinfo' in page_data and len(page_data['imageinfo']) > 0:
                    return page_data['imageinfo'][0]

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching image info for {filename}: {e}")

        return None

    def validate_image(self, image_info: Dict) -> Tuple[bool, str]:
        """Validate if image meets quality requirements."""
        # Check dimensions
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)

        if width < self.min_width or height < self.min_height:
            return False, f"Image too small: {width}x{height}"

        # Check MIME type
        mime = image_info.get('mime', '')
        if mime not in ['image/jpeg', 'image/png', 'image/jpg']:
            return False, f"Unsupported format: {mime}"

        return True, "OK"

    def download_image(self, url: str, output_path: Path) -> bool:
        """Download an image from URL to output path."""
        try:
            self.rate_limiter.wait()
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Download in chunks
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify the downloaded image
            try:
                with Image.open(output_path) as img:
                    img.verify()
                return True
            except Exception as e:
                logger.error(f"Downloaded file is not a valid image: {e}")
                output_path.unlink(missing_ok=True)
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return False

    def download_from_category(self, category: str, limit: int, stats: DownloadStats) -> int:
        """Download images from a specific category."""
        logger.info(f"Starting download from Wikimedia Commons category: {category}")

        members = self.get_category_members(category, limit * 3)  # Get more to account for filtering
        downloaded_count = 0

        iterator = tqdm(members, desc="Wikimedia") if HAS_TQDM else members

        for member in iterator:
            if downloaded_count >= limit:
                break

            filename = member.get('title', '')
            if not filename:
                continue

            # Get image info
            image_info = self.get_image_info(filename)
            if not image_info:
                stats.record_failure(f"Could not get info for {filename}")
                continue

            # Validate image
            is_valid, reason = self.validate_image(image_info)
            if not is_valid:
                logger.debug(f"Skipping {filename}: {reason}")
                stats.record_skip()
                continue

            # Prepare output filename
            safe_filename = filename.replace('File:', '').replace(' ', '_')
            safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in ('_', '.', '-'))
            output_path = self.output_dir / safe_filename

            # Skip if already exists
            if output_path.exists():
                logger.debug(f"Skipping existing file: {safe_filename}")
                stats.record_skip()
                downloaded_count += 1
                continue

            # Download image
            image_url = image_info.get('url')
            if not image_url:
                stats.record_failure(f"No URL for {filename}")
                continue

            if self.download_image(image_url, output_path):
                logger.info(f"Downloaded: {safe_filename}")

                # Save metadata
                metadata_entry = {
                    'filename': safe_filename,
                    'original_title': filename,
                    'source': 'Wikimedia Commons',
                    'category': category,
                    'url': image_info.get('descriptionurl', ''),
                    'image_url': image_url,
                    'width': image_info.get('width'),
                    'height': image_info.get('height'),
                    'mime': image_info.get('mime'),
                    'download_date': datetime.now().isoformat()
                }

                # Try to extract attribution info
                ext_metadata = image_info.get('extmetadata', {})
                if 'Artist' in ext_metadata:
                    metadata_entry['artist'] = ext_metadata['Artist'].get('value', '')
                if 'LicenseShortName' in ext_metadata:
                    metadata_entry['license'] = ext_metadata['LicenseShortName'].get('value', '')
                if 'AttributionRequired' in ext_metadata:
                    metadata_entry['attribution_required'] = ext_metadata['AttributionRequired'].get('value', '')

                self.metadata.append(metadata_entry)
                stats.record_success()
                downloaded_count += 1
            else:
                stats.record_failure(f"Download failed for {filename}")

        return downloaded_count

    def save_metadata(self):
        """Save metadata to JSON file."""
        metadata_path = self.output_dir / 'metadata.json'
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata saved to {metadata_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")


class METDownloader:
    """Download archaeological fragment images from MET Museum Open Access API."""

    def __init__(self, output_dir: Path, min_width: int = 800, min_height: int = 600):
        self.output_dir = output_dir
        self.min_width = min_width
        self.min_height = min_height
        self.base_url = "https://collectionapi.metmuseum.org/public/collection/v1"
        self.rate_limiter = RateLimiter(calls_per_second=2.0)  # MET allows more requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchaeologicalFragmentDownloader/1.0 (Educational Research)'
        })
        self.metadata = []

    def search_objects(self, query: str) -> List[int]:
        """Search for objects matching the query."""
        logger.info(f"Searching MET Museum for: {query}")

        search_url = f"{self.base_url}/search"
        params = {
            'q': query,
            'hasImages': 'true',
            'isPublicDomain': 'true'  # Only CC0/Public Domain
        }

        try:
            self.rate_limiter.wait()
            response = self.session.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            object_ids = data.get('objectIDs', [])
            if object_ids:
                logger.info(f"Found {len(object_ids)} objects")
                return object_ids
            else:
                logger.warning("No objects found")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching MET API: {e}")
            return []

    def get_object_info(self, object_id: int) -> Optional[Dict]:
        """Get detailed information about an object."""
        object_url = f"{self.base_url}/objects/{object_id}"

        try:
            self.rate_limiter.wait()
            response = self.session.get(object_url, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching object {object_id}: {e}")
            return None

    def validate_object(self, obj_info: Dict) -> Tuple[bool, str]:
        """Validate if object meets requirements."""
        # Check if it's public domain / CC0
        if not obj_info.get('isPublicDomain', False):
            return False, "Not public domain"

        # Check if it has primary image
        primary_image = obj_info.get('primaryImage', '')
        if not primary_image:
            return False, "No primary image"

        return True, "OK"

    def download_image(self, url: str, output_path: Path) -> bool:
        """Download an image from URL to output path."""
        try:
            self.rate_limiter.wait()
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Download in chunks
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Verify the downloaded image and check dimensions
            try:
                with Image.open(output_path) as img:
                    width, height = img.size

                    # Check dimensions
                    if width < self.min_width or height < self.min_height:
                        logger.debug(f"Image too small: {width}x{height}")
                        output_path.unlink(missing_ok=True)
                        return False

                    # Verify format
                    if img.format not in ['JPEG', 'PNG', 'JPG']:
                        logger.debug(f"Unsupported format: {img.format}")
                        output_path.unlink(missing_ok=True)
                        return False

                return True
            except Exception as e:
                logger.error(f"Downloaded file is not a valid image: {e}")
                output_path.unlink(missing_ok=True)
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return False

    def download_from_search(self, queries: List[str], limit: int, stats: DownloadStats) -> int:
        """Download images from search queries."""
        logger.info(f"Starting download from MET Museum")

        # Collect object IDs from all queries
        all_object_ids = []
        for query in queries:
            object_ids = self.search_objects(query)
            all_object_ids.extend(object_ids)

        # Remove duplicates
        all_object_ids = list(set(all_object_ids))
        logger.info(f"Total unique objects found: {len(all_object_ids)}")

        downloaded_count = 0
        iterator = tqdm(all_object_ids, desc="MET Museum") if HAS_TQDM else all_object_ids

        for object_id in iterator:
            if downloaded_count >= limit:
                break

            # Get object info
            obj_info = self.get_object_info(object_id)
            if not obj_info:
                stats.record_failure(f"Could not get info for object {object_id}")
                continue

            # Validate object
            is_valid, reason = self.validate_object(obj_info)
            if not is_valid:
                logger.debug(f"Skipping object {object_id}: {reason}")
                stats.record_skip()
                continue

            # Prepare output filename
            object_number = obj_info.get('objectID', object_id)
            title = obj_info.get('title', 'untitled')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-'))[:50]
            safe_filename = f"met_{object_number}_{safe_title.replace(' ', '_')}.jpg"
            output_path = self.output_dir / safe_filename

            # Skip if already exists
            if output_path.exists():
                logger.debug(f"Skipping existing file: {safe_filename}")
                stats.record_skip()
                downloaded_count += 1
                continue

            # Download image
            image_url = obj_info.get('primaryImage')
            if not image_url:
                stats.record_failure(f"No image URL for object {object_id}")
                continue

            if self.download_image(image_url, output_path):
                logger.info(f"Downloaded: {safe_filename}")

                # Save metadata
                metadata_entry = {
                    'filename': safe_filename,
                    'object_id': object_number,
                    'source': 'MET Museum',
                    'title': obj_info.get('title', ''),
                    'culture': obj_info.get('culture', ''),
                    'period': obj_info.get('period', ''),
                    'date': obj_info.get('objectDate', ''),
                    'medium': obj_info.get('medium', ''),
                    'department': obj_info.get('department', ''),
                    'url': obj_info.get('objectURL', ''),
                    'image_url': image_url,
                    'is_public_domain': obj_info.get('isPublicDomain', False),
                    'license': 'CC0' if obj_info.get('isPublicDomain') else 'Unknown',
                    'download_date': datetime.now().isoformat()
                }

                self.metadata.append(metadata_entry)
                stats.record_success()
                downloaded_count += 1
            else:
                stats.record_failure(f"Download failed for object {object_id}")

        return downloaded_count

    def save_metadata(self):
        """Save metadata to JSON file."""
        metadata_path = self.output_dir / 'metadata.json'
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata saved to {metadata_path}")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")


def create_readme(output_dir: Path, wikimedia_metadata: List[Dict], met_metadata: List[Dict]):
    """Create README.md with sources and attribution information."""
    readme_path = output_dir / 'README.md'

    readme_content = f"""# Real Archaeological Fragment Images

This directory contains real archaeological fragment images downloaded from open-access sources.

**Download Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Sources

### Wikimedia Commons
- **Category:** Sherds
- **Images Downloaded:** {len(wikimedia_metadata)}
- **License:** Various open licenses (see individual metadata)
- **URL:** https://commons.wikimedia.org/wiki/Category:Sherds

### MET Museum Open Access
- **Search Terms:** ceramic fragment, potsherd, pottery shard
- **Images Downloaded:** {len(met_metadata)}
- **License:** CC0 (Public Domain)
- **URL:** https://www.metmuseum.org/art/collection

## Directory Structure

```
data/raw/real_fragments/
+-- wikimedia/
|   +-- metadata.json
|   +-- [image files]
+-- met/
|   +-- metadata.json
|   +-- [image files]
+-- README.md
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

*Last updated: {datetime.now().strftime('%Y-%m-%d')}*
"""

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        logger.info(f"README created at {readme_path}")
    except Exception as e:
        logger.error(f"Error creating README: {e}")


def main():
    """Main function to orchestrate the download process."""
    parser = argparse.ArgumentParser(
        description='Download real archaeological fragment images from open-access sources.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --source all --limit 30
  %(prog)s --source wikimedia --limit 20
  %(prog)s --source met --limit 10
  %(prog)s --source all --limit 50 --output-dir /custom/path
  %(prog)s --validate-only --output-dir data/raw/real_fragments_validated/british_museum
        """
    )

    parser.add_argument(
        '--source',
        choices=['wikimedia', 'met', 'all'],
        default='all',
        help='Source to download from (default: all)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=30,
        help='Maximum number of images to download per source (default: 30)'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw/real_fragments',
        help='Output directory for downloads (default: data/raw/real_fragments)'
    )

    parser.add_argument(
        '--min-width',
        type=int,
        default=800,
        help='Minimum image width in pixels (default: 800)'
    )

    parser.add_argument(
        '--min-height',
        type=int,
        default=600,
        help='Minimum image height in pixels (default: 600)'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate and create validation report for already downloaded images'
    )

    args = parser.parse_args()

    # Setup output directories
    output_base = Path(args.output_dir)
    wikimedia_dir = output_base / 'wikimedia'
    met_dir = output_base / 'met'

    wikimedia_dir.mkdir(parents=True, exist_ok=True)
    met_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("Archaeological Fragment Image Downloader")
    logger.info("=" * 70)
    logger.info(f"Source: {args.source}")
    logger.info(f"Limit per source: {args.limit}")
    logger.info(f"Output directory: {output_base}")
    logger.info(f"Minimum resolution: {args.min_width}x{args.min_height}")
    logger.info("=" * 70)

    stats = DownloadStats()
    wikimedia_metadata = []
    met_metadata = []

    # Download from Wikimedia Commons
    if args.source in ['wikimedia', 'all']:
        try:
            logger.info("\n" + "=" * 70)
            logger.info("WIKIMEDIA COMMONS")
            logger.info("=" * 70)

            downloader = WikimediaDownloader(
                wikimedia_dir,
                min_width=args.min_width,
                min_height=args.min_height
            )

            # Download from multiple related categories
            categories = ['Sherds', 'Archaeological_ceramics', 'Pottery_fragments']
            downloaded = 0

            for category in categories:
                if downloaded >= args.limit:
                    break
                remaining = args.limit - downloaded
                count = downloader.download_from_category(category, remaining, stats)
                downloaded += count

            downloader.save_metadata()
            wikimedia_metadata = downloader.metadata

        except Exception as e:
            logger.error(f"Error downloading from Wikimedia Commons: {e}", exc_info=True)

    # Download from MET Museum
    if args.source in ['met', 'all']:
        try:
            logger.info("\n" + "=" * 70)
            logger.info("MET MUSEUM")
            logger.info("=" * 70)

            downloader = METDownloader(
                met_dir,
                min_width=args.min_width,
                min_height=args.min_height
            )

            # Search for various terms related to ceramic fragments
            queries = [
                'ceramic fragment',
                'potsherd',
                'pottery shard',
                'ceramic shard',
                'terracotta fragment'
            ]

            downloader.download_from_search(queries, args.limit, stats)
            downloader.save_metadata()
            met_metadata = downloader.metadata

        except Exception as e:
            logger.error(f"Error downloading from MET Museum: {e}", exc_info=True)

    # Create README with attribution
    try:
        create_readme(output_base, wikimedia_metadata, met_metadata)
    except Exception as e:
        logger.error(f"Error creating README: {e}")

    # Print final statistics
    logger.info("\n" + "=" * 70)
    logger.info("DOWNLOAD COMPLETE")
    logger.info("=" * 70)
    logger.info(stats.summary())
    logger.info(f"\nImages saved to: {output_base}")
    logger.info(f"Wikimedia images: {len(wikimedia_metadata)}")
    logger.info(f"MET Museum images: {len(met_metadata)}")
    logger.info(f"Total images: {len(wikimedia_metadata) + len(met_metadata)}")

    if stats.failed > 0:
        logger.warning(f"\n{stats.failed} downloads failed. Check the log for details.")

    logger.info("=" * 70)

    return 0 if stats.successful > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
