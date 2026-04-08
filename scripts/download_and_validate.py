#!/usr/bin/env python3
"""
Combined download and validation script for archaeological fragments.

This script:
1. Downloads pottery fragments from Wikimedia Commons and MET Museum
2. Immediately validates each downloaded image
3. Rejects unsuitable images
4. Creates a comprehensive validation report

Usage:
    python download_and_validate.py --limit 15 --output data/raw/real_fragments_validated/british_museum
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_and_validate.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ImageValidator:
    """Quick validator to check if an image meets requirements."""

    def __init__(self, min_width=800, min_height=600):
        self.min_width = min_width
        self.min_height = min_height

    def validate(self, img_array: np.ndarray) -> Dict:
        """Quick validation of image quality."""
        result = {
            "resolution_ok": False,
            "single_fragment": False,
            "simple_background": False,
            "clear_edges": False,
            "is_fragment": False,
            "passed": False,
            "details": {}
        }

        try:
            height, width = img_array.shape[:2]
            result["details"]["resolution"] = f"{width}x{height}"

            # Check 1: Resolution
            if width >= self.min_width and height >= self.min_height:
                result["resolution_ok"] = True

            # Convert to grayscale for analysis
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            else:
                gray = img_array.copy()

            # Check 2: Single fragment
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            if np.mean(binary) < 127:
                binary = cv2.bitwise_not(binary)

            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
            min_size = (width * height) * 0.01
            significant = sum(1 for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] > min_size)

            result["details"]["num_components"] = significant
            if significant == 1:
                result["single_fragment"] = True

            # Check 3: Simple background
            background_mask = binary == 255
            if np.any(background_mask):
                bg_pixels = gray[background_mask]
                if len(bg_pixels) > 0:
                    bg_std = np.std(bg_pixels)
                    uniformity = 1.0 - min(bg_std / 127.5, 1.0)
                    result["details"]["bg_uniformity"] = float(uniformity)
                    if uniformity > 0.7:
                        result["simple_background"] = True

            # Check 4: Clear edges - be more lenient
            edges = cv2.Canny(gray, 50, 150)
            edge_pixels = np.count_nonzero(edges)
            edge_density = edge_pixels / (width * height)
            result["details"]["edge_density"] = float(edge_density)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 0:
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                perimeter = cv2.arcLength(largest, True)
                if perimeter > 0:
                    compactness = 4 * np.pi * area / (perimeter ** 2)
                    result["details"]["compactness"] = float(compactness)
                    # More lenient: just check if there are some edges
                    if edge_density > 0.005:  # Very low threshold
                        result["clear_edges"] = True
            elif edge_density > 0.005:
                result["clear_edges"] = True

            # Check 5: Fragment not complete vessel
            if len(contours) > 0:
                largest = max(contours, key=cv2.contourArea)
                contour_area = cv2.contourArea(largest)
                hull = cv2.convexHull(largest)
                hull_area = cv2.contourArea(hull)

                if hull_area > 0:
                    solidity = contour_area / hull_area
                    result["details"]["solidity"] = float(solidity)
                    if solidity < 0.85:
                        result["is_fragment"] = True

            # Overall validation - require most but not necessarily all checks
            # At minimum: resolution, single fragment, and some form of validation
            critical_checks = [
                result["resolution_ok"],
                result["single_fragment"] or result["simple_background"]  # One of these must pass
            ]

            # Bonus checks - at least 2 of these should pass
            bonus_checks = [
                result["simple_background"],
                result["clear_edges"],
                result["is_fragment"]
            ]

            passed_bonus = sum(1 for check in bonus_checks if check)

            result["passed"] = all(critical_checks) and passed_bonus >= 2

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Validation error: {e}")

        return result


class DownloadAndValidate:
    """Download and validate archaeological fragments."""

    def __init__(self, output_dir: Path, min_width=800, min_height=600):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validator = ImageValidator(min_width, min_height)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArchaeologicalFragmentDownloader/1.0 (Educational Research)'
        })
        self.report = {
            "download_date": datetime.now().isoformat(),
            "validated_fragments": [],
            "rejected_fragments": [],
            "summary": {
                "attempted": 0,
                "validated": 0,
                "rejected": 0
            }
        }

    def download_from_wikimedia(self, search_terms: List[str], limit: int):
        """Download and validate fragments from Wikimedia Commons."""
        logger.info("=" * 70)
        logger.info("DOWNLOADING FROM WIKIMEDIA COMMONS")
        logger.info("=" * 70)

        api_url = "https://commons.wikimedia.org/w/api.php"
        fragments_found = 0

        for search_term in search_terms:
            if fragments_found >= limit:
                break

            logger.info(f"\nSearching for: '{search_term}'")

            params = {
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": search_term,
                "gsrnamespace": "6",
                "gsrlimit": "20",
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata"
            }

            try:
                response = self.session.get(api_url, params=params, timeout=30)
                if response.status_code != 200:
                    continue

                data = response.json()
                pages = data.get('query', {}).get('pages', {})

                for page_id, page in pages.items():
                    if fragments_found >= limit:
                        break

                    imageinfo = page.get('imageinfo', [])
                    if not imageinfo:
                        continue

                    img_info = imageinfo[0]
                    url = img_info.get('url')
                    title = page.get('title', 'Unknown')

                    if not url or not (url.endswith(('.jpg', '.jpeg', '.png'))):
                        continue

                    # Download and validate
                    self.report["summary"]["attempted"] += 1
                    success = self.download_and_validate_image(url, title, "Wikimedia Commons")

                    if success:
                        fragments_found += 1
                        logger.info(f"  OK Downloaded and validated ({fragments_found}/{limit}): {title}")

                    if fragments_found >= limit:
                        break

            except Exception as e:
                logger.error(f"Error searching Wikimedia: {e}")

    def download_from_met(self, queries: List[str], limit: int):
        """Download and validate fragments from MET Museum."""
        logger.info("=" * 70)
        logger.info("DOWNLOADING FROM MET MUSEUM")
        logger.info("=" * 70)

        base_url = "https://collectionapi.metmuseum.org/public/collection/v1"
        fragments_found = 0

        for query in queries:
            if fragments_found >= limit:
                break

            logger.info(f"\nSearching for: '{query}'")

            search_url = f"{base_url}/search"
            params = {
                'q': query,
                'hasImages': 'true',
                'isPublicDomain': 'true'
            }

            try:
                response = self.session.get(search_url, params=params, timeout=30)
                if response.status_code != 200:
                    continue

                data = response.json()
                object_ids = data.get('objectIDs', [])[:50]  # Limit search results

                for object_id in object_ids:
                    if fragments_found >= limit:
                        break

                    # Get object details
                    object_url = f"{base_url}/objects/{object_id}"
                    obj_response = self.session.get(object_url, timeout=30)

                    if obj_response.status_code != 200:
                        continue

                    obj_data = obj_response.json()
                    if not obj_data.get('isPublicDomain', False):
                        continue

                    image_url = obj_data.get('primaryImage')
                    title = obj_data.get('title', 'Untitled')

                    if not image_url:
                        continue

                    # Download and validate
                    self.report["summary"]["attempted"] += 1
                    success = self.download_and_validate_image(
                        image_url,
                        f"MET_{object_id}_{title[:30]}",
                        "MET Museum"
                    )

                    if success:
                        fragments_found += 1
                        logger.info(f"  OK Downloaded and validated ({fragments_found}/{limit}): {title}")

            except Exception as e:
                logger.error(f"Error searching MET: {e}")

    def download_and_validate_image(self, url: str, title: str, source: str) -> bool:
        """Download image, validate it, and save if it passes validation."""
        try:
            # Download image
            response = self.session.get(url, timeout=60)
            if response.status_code != 200:
                return False

            # Load image with PIL first
            pil_img = Image.open(BytesIO(response.content))

            # Convert to OpenCV format
            img_array = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

            # Validate
            validation = self.validator.validate(img_array)

            if validation["passed"]:
                # Save image
                safe_filename = "".join(c for c in title if c.isalnum() or c in ('_', '-'))[:50]
                filename = f"fragment_{self.report['summary']['validated'] + 1:03d}_{safe_filename}.jpg"
                filepath = self.output_dir / filename

                # Convert to RGB if needed and save
                if len(img_array.shape) == 2:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)

                cv2.imwrite(str(filepath), img_array, [cv2.IMWRITE_JPEG_QUALITY, 95])

                # Record in report
                self.report["validated_fragments"].append({
                    "filename": filename,
                    "original_title": title,
                    "source": source,
                    "url": url,
                    "validation": validation
                })
                self.report["summary"]["validated"] += 1

                return True
            else:
                # Record rejection
                self.report["rejected_fragments"].append({
                    "title": title,
                    "source": source,
                    "url": url,
                    "validation": validation,
                    "reason": [k for k, v in validation.items() if k.endswith('_ok') or k in ['single_fragment', 'simple_background', 'clear_edges', 'is_fragment'] if not v]
                })
                self.report["summary"]["rejected"] += 1

                failed_checks = [k for k, v in validation.items() if k.endswith('_ok') or k in ['single_fragment', 'simple_background', 'clear_edges', 'is_fragment'] if not v]
                logger.warning(f"  X Rejected '{title[:40]}': {', '.join(failed_checks)}")

                return False

        except Exception as e:
            logger.error(f"Error processing '{title}': {e}")
            self.report["summary"]["rejected"] += 1
            return False

    def save_report(self):
        """Save validation report to JSON."""
        report_path = self.output_dir / "validation_report.json"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False)
            logger.info(f"\nValidation report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")

    def print_summary(self):
        """Print download and validation summary."""
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOAD AND VALIDATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total attempted: {self.report['summary']['attempted']}")
        logger.info(f"Validated and saved: {self.report['summary']['validated']}")
        logger.info(f"Rejected: {self.report['summary']['rejected']}")
        logger.info(f"Success rate: {self.report['summary']['validated'] / max(self.report['summary']['attempted'], 1) * 100:.1f}%")

        if self.report["summary"]["rejected"] > 0:
            logger.info("\nCommon rejection reasons:")
            reasons = {}
            for rejected in self.report["rejected_fragments"]:
                for reason in rejected.get("reason", []):
                    reasons[reason] = reasons.get(reason, 0) + 1

            for reason, count in sorted(reasons.items(), key=lambda x: -x[1])[:5]:
                logger.info(f"  - {reason}: {count} images")

        logger.info("=" * 70)


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Download and validate archaeological fragment images.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=15,
        help='Target number of validated fragments to download (default: 15)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='data/raw/real_fragments_validated/british_museum',
        help='Output directory for validated fragments'
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
        '--source',
        choices=['wikimedia', 'met', 'all'],
        default='all',
        help='Source to download from (default: all)'
    )

    args = parser.parse_args()

    output_dir = Path(args.output)
    downloader = DownloadAndValidate(output_dir, args.min_width, args.min_height)

    logger.info("=" * 70)
    logger.info("ARCHAEOLOGICAL FRAGMENT DOWNLOADER WITH VALIDATION")
    logger.info("=" * 70)
    logger.info(f"Target: {args.limit} validated fragments")
    logger.info(f"Output: {output_dir}")
    logger.info(f"Min resolution: {args.min_width}x{args.min_height}")
    logger.info(f"Source: {args.source}")
    logger.info("=" * 70)

    # Download from sources
    if args.source in ['wikimedia', 'all']:
        search_terms = [
            "pottery sherd",
            "potsherd",
            "ceramic sherd",
            "pottery fragment"
        ]
        downloader.download_from_wikimedia(search_terms, args.limit)

    if args.source in ['met', 'all']:
        queries = [
            "ceramic fragment",
            "potsherd",
            "pottery shard",
            "terracotta fragment"
        ]
        downloader.download_from_met(queries, args.limit)

    # Save report and print summary
    downloader.save_report()
    downloader.print_summary()

    return 0 if downloader.report['summary']['validated'] > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
