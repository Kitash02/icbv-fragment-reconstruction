#!/usr/bin/env python3
"""
Download pottery fragments from Wikimedia Commons categories.
This script uses the Category API to get better results.
"""

import json
import logging
import sys
import time
from datetime import datetime
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
import requests
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wikimedia_download.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def download_from_category(category: str, output_dir: Path, limit: int = 20):
    """Download images from a Wikimedia Commons category."""
    api_url = "https://commons.wikimedia.org/w/api.php"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'ArchaeologicalFragmentDownloader/1.0 (Educational Research)'
    })

    logger.info(f"Downloading from category: {category}")

    params = {
        'action': 'query',
        'list': 'categorymembers',
        'cmtitle': f'Category:{category}',
        'cmtype': 'file',
        'cmlimit': min(limit * 2, 500),
        'format': 'json'
    }

    try:
        response = session.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        members = data.get('query', {}).get('categorymembers', [])
        logger.info(f"Found {len(members)} files in category")

        downloaded = 0
        for member in members[:limit * 2]:
            if downloaded >= limit:
                break

            filename = member.get('title', '')
            if not filename:
                continue

            # Get image info
            img_params = {
                'action': 'query',
                'titles': filename,
                'prop': 'imageinfo',
                'iiprop': 'url|size|mime',
                'format': 'json'
            }

            time.sleep(0.5)  # Rate limiting
            img_response = session.get(api_url, params=img_params, timeout=30)
            img_data = img_response.json()

            pages = img_data.get('query', {}).get('pages', {})
            for page_id, page in pages.items():
                if 'imageinfo' not in page:
                    continue

                img_info = page['imageinfo'][0]
                url = img_info.get('url')
                width = img_info.get('width', 0)
                height = img_info.get('height', 0)
                mime = img_info.get('mime', '')

                # Check resolution
                if width < 600 or height < 600:
                    logger.debug(f"Skipping {filename}: too small ({width}x{height})")
                    continue

                # Check format
                if mime not in ['image/jpeg', 'image/png', 'image/jpg']:
                    logger.debug(f"Skipping {filename}: unsupported format ({mime})")
                    continue

                # Download image
                try:
                    time.sleep(0.5)
                    img_response = session.get(url, timeout=60)
                    img_response.raise_for_status()

                    # Save to file
                    safe_filename = "".join(c for c in filename.replace('File:', '') if c.isalnum() or c in ('_', '.', '-'))[:80]
                    output_path = output_dir / safe_filename

                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)

                    # Verify it's a valid image
                    img = Image.open(output_path)
                    img.verify()

                    downloaded += 1
                    logger.info(f"  [{downloaded}/{limit}] Downloaded: {safe_filename}")

                except Exception as e:
                    logger.error(f"  Error downloading {filename}: {e}")
                    if output_path.exists():
                        output_path.unlink()

    except Exception as e:
        logger.error(f"Error accessing category {category}: {e}")

    return downloaded


def main():
    """Main execution."""
    output_dir = Path("data/raw/real_fragments_validated/british_museum")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 70)
    logger.info("WIKIMEDIA COMMONS POTTERY FRAGMENT DOWNLOADER")
    logger.info("=" * 70)

    # Good categories for pottery fragments
    categories = [
        "Sherds",
        "Pottery_fragments",
        "Archaeological_ceramics",
        "Ceramic_fragments"
    ]

    total_downloaded = 0
    for category in categories:
        if total_downloaded >= 15:
            break

        count = download_from_category(category, output_dir, limit=max(1, 15 - total_downloaded))
        total_downloaded += count

        if total_downloaded >= 15:
            break

    logger.info("=" * 70)
    logger.info(f"DOWNLOAD COMPLETE: {total_downloaded} fragments downloaded")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 70)


if __name__ == '__main__':
    main()
