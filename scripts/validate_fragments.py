#!/usr/bin/env python3
"""
Comprehensive validation script for archaeological fragment images.

This script performs thorough validation of downloaded fragment images to ensure they meet
quality requirements for fragment reconstruction:
1. Single fragment per image (not multiple fragments)
2. Simple background
3. Good resolution (min 800x600)
4. Clear edges
5. Not complete vessels

The validation results are saved in a detailed JSON report.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation_fragments.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FragmentValidator:
    """Comprehensive validator for archaeological fragment images."""

    def __init__(self, min_width: int = 800, min_height: int = 600):
        self.min_width = min_width
        self.min_height = min_height
        self.validation_report = {
            "validation_date": datetime.now().isoformat(),
            "criteria": {
                "min_resolution": f"{min_width}x{min_height}",
                "single_fragment": "Must have exactly one connected component",
                "simple_background": "Background should be mostly uniform",
                "clear_edges": "Edges should be well-defined",
                "not_complete_vessel": "Should be a fragment, not a complete object"
            },
            "validated_images": [],
            "rejected_images": [],
            "summary": {
                "total_checked": 0,
                "passed": 0,
                "rejected": 0
            }
        }

    def check_resolution(self, img: np.ndarray) -> Tuple[bool, str]:
        """Check if image meets minimum resolution requirements."""
        height, width = img.shape[:2]
        if width >= self.min_width and height >= self.min_height:
            return True, f"Resolution OK: {width}x{height}"
        else:
            return False, f"Resolution too low: {width}x{height} (min: {self.min_width}x{self.min_height})"

    def check_single_fragment(self, img: np.ndarray) -> Tuple[bool, str, int]:
        """Check if image contains a single fragment (one connected component)."""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Threshold to binary
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert if background is dark
        if np.mean(binary) < 127:
            binary = cv2.bitwise_not(binary)

        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

        # Filter out very small components (noise)
        min_component_size = (img.shape[0] * img.shape[1]) * 0.01  # 1% of image
        significant_components = []

        for i in range(1, num_labels):  # Skip background (label 0)
            area = stats[i, cv2.CC_STAT_AREA]
            if area > min_component_size:
                significant_components.append({
                    'label': i,
                    'area': area,
                    'bbox': stats[i]
                })

        num_significant = len(significant_components)

        if num_significant == 1:
            return True, "Single fragment detected", num_significant
        elif num_significant == 0:
            return False, "No significant fragment detected", num_significant
        else:
            return False, f"Multiple fragments detected ({num_significant} components)", num_significant

    def check_simple_background(self, img: np.ndarray) -> Tuple[bool, str, float]:
        """Check if background is simple (uniform)."""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Threshold to separate object from background
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert if background is dark
        if np.mean(binary) < 127:
            binary = cv2.bitwise_not(binary)

        # Assume white is background
        background_mask = binary == 255

        if not np.any(background_mask):
            return False, "No background detected", 0.0

        # Calculate background uniformity (inverse of standard deviation)
        background_pixels = gray[background_mask]
        if len(background_pixels) > 0:
            bg_std = np.std(background_pixels)
            uniformity = 1.0 - min(bg_std / 127.5, 1.0)  # Normalize to [0, 1]

            if uniformity > 0.7:  # Threshold for "simple" background
                return True, f"Background is simple (uniformity: {uniformity:.2f})", uniformity
            else:
                return False, f"Background is complex (uniformity: {uniformity:.2f})", uniformity
        else:
            return False, "Cannot assess background", 0.0

    def check_clear_edges(self, img: np.ndarray) -> Tuple[bool, str, float]:
        """Check if fragment has clear, well-defined edges."""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150)

        # Calculate edge density
        edge_pixels = np.count_nonzero(edges)
        total_pixels = edges.shape[0] * edges.shape[1]
        edge_density = edge_pixels / total_pixels

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            return False, "No edges detected", 0.0

        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        contour_perimeter = cv2.arcLength(largest_contour, True)

        # Calculate compactness (measure of how well-defined the boundary is)
        if contour_perimeter > 0:
            compactness = 4 * np.pi * contour_area / (contour_perimeter ** 2)
        else:
            compactness = 0.0

        # Good edges: moderate edge density and reasonable compactness
        if 0.01 < edge_density < 0.3 and compactness > 0.1:
            return True, f"Clear edges (density: {edge_density:.3f}, compactness: {compactness:.3f})", edge_density
        else:
            return False, f"Unclear edges (density: {edge_density:.3f}, compactness: {compactness:.3f})", edge_density

    def check_not_complete_vessel(self, img: np.ndarray) -> Tuple[bool, str, float]:
        """Check if object is a fragment, not a complete vessel."""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img.copy()

        # Threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Invert if needed
        if np.mean(binary) < 127:
            binary = cv2.bitwise_not(binary)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            return False, "No object detected", 0.0

        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Calculate solidity (ratio of contour area to convex hull area)
        contour_area = cv2.contourArea(largest_contour)
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)

        if hull_area == 0:
            return False, "Invalid object shape", 0.0

        solidity = contour_area / hull_area

        # Calculate extent (ratio of contour area to bounding box area)
        x, y, w, h = cv2.boundingRect(largest_contour)
        bbox_area = w * h
        extent = contour_area / bbox_area if bbox_area > 0 else 0.0

        # Fragments typically have lower solidity (due to broken edges)
        # and irregular extent
        # Complete vessels tend to be very regular (high solidity and extent)
        if solidity < 0.85 and extent < 0.8:
            return True, f"Appears to be fragment (solidity: {solidity:.2f}, extent: {extent:.2f})", solidity
        else:
            return False, f"May be complete vessel (solidity: {solidity:.2f}, extent: {extent:.2f})", solidity

    def validate_image(self, image_path: Path) -> Dict:
        """Perform comprehensive validation on a single image."""
        logger.info(f"Validating: {image_path.name}")

        validation_result = {
            "filename": image_path.name,
            "path": str(image_path),
            "checks": {},
            "passed": False,
            "reason": []
        }

        try:
            # Load image
            img = cv2.imread(str(image_path))
            if img is None:
                validation_result["checks"]["load"] = {
                    "passed": False,
                    "message": "Failed to load image"
                }
                validation_result["reason"].append("Failed to load image")
                return validation_result

            # Check 1: Resolution
            res_ok, res_msg = self.check_resolution(img)
            validation_result["checks"]["resolution"] = {
                "passed": res_ok,
                "message": res_msg
            }
            if not res_ok:
                validation_result["reason"].append(res_msg)

            # Check 2: Single fragment
            single_ok, single_msg, num_components = self.check_single_fragment(img)
            validation_result["checks"]["single_fragment"] = {
                "passed": single_ok,
                "message": single_msg,
                "num_components": num_components
            }
            if not single_ok:
                validation_result["reason"].append(single_msg)

            # Check 3: Simple background
            bg_ok, bg_msg, uniformity = self.check_simple_background(img)
            validation_result["checks"]["simple_background"] = {
                "passed": bg_ok,
                "message": bg_msg,
                "uniformity_score": float(uniformity)
            }
            if not bg_ok:
                validation_result["reason"].append(bg_msg)

            # Check 4: Clear edges
            edge_ok, edge_msg, edge_score = self.check_clear_edges(img)
            validation_result["checks"]["clear_edges"] = {
                "passed": edge_ok,
                "message": edge_msg,
                "edge_score": float(edge_score)
            }
            if not edge_ok:
                validation_result["reason"].append(edge_msg)

            # Check 5: Not complete vessel
            frag_ok, frag_msg, solidity = self.check_not_complete_vessel(img)
            validation_result["checks"]["fragment_not_vessel"] = {
                "passed": frag_ok,
                "message": frag_msg,
                "solidity": float(solidity)
            }
            if not frag_ok:
                validation_result["reason"].append(frag_msg)

            # Overall pass: all checks must pass
            all_checks_passed = all(
                check.get("passed", False)
                for key, check in validation_result["checks"].items()
            )

            validation_result["passed"] = all_checks_passed

            if all_checks_passed:
                logger.info(f"  [x] PASSED: {image_path.name}")
            else:
                logger.warning(f"  [ ] REJECTED: {image_path.name}")
                for reason in validation_result["reason"]:
                    logger.warning(f"    - {reason}")

        except Exception as e:
            logger.error(f"  Error validating {image_path.name}: {e}")
            validation_result["checks"]["error"] = {
                "passed": False,
                "message": str(e)
            }
            validation_result["reason"].append(f"Validation error: {str(e)}")

        return validation_result

    def validate_directory(self, input_dir: Path, delete_rejected: bool = False) -> Dict:
        """Validate all images in a directory."""
        logger.info("=" * 70)
        logger.info("FRAGMENT IMAGE VALIDATION")
        logger.info("=" * 70)
        logger.info(f"Input directory: {input_dir}")
        logger.info(f"Min resolution: {self.min_width}x{self.min_height}")
        logger.info(f"Delete rejected: {delete_rejected}")
        logger.info("=" * 70)

        # Find all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))

        logger.info(f"\nFound {len(image_files)} images to validate\n")

        # Validate each image
        for image_path in sorted(image_files):
            result = self.validate_image(image_path)
            self.validation_report["summary"]["total_checked"] += 1

            if result["passed"]:
                self.validation_report["validated_images"].append(result)
                self.validation_report["summary"]["passed"] += 1
            else:
                self.validation_report["rejected_images"].append(result)
                self.validation_report["summary"]["rejected"] += 1

                # Delete rejected image if requested
                if delete_rejected:
                    try:
                        image_path.unlink()
                        logger.info(f"    Deleted rejected image: {image_path.name}")
                    except Exception as e:
                        logger.error(f"    Failed to delete {image_path.name}: {e}")

        return self.validation_report

    def save_report(self, output_path: Path):
        """Save validation report to JSON file."""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.validation_report, f, indent=2, ensure_ascii=False)
            logger.info(f"\nValidation report saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving validation report: {e}")

    def print_summary(self):
        """Print validation summary."""
        logger.info("\n" + "=" * 70)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total images checked: {self.validation_report['summary']['total_checked']}")
        logger.info(f"Passed validation: {self.validation_report['summary']['passed']}")
        logger.info(f"Rejected: {self.validation_report['summary']['rejected']}")

        if self.validation_report['summary']['rejected'] > 0:
            logger.info("\nRejection Reasons:")
            rejection_reasons = {}
            for rejected in self.validation_report['rejected_images']:
                for reason in rejected.get('reason', []):
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

            for reason, count in sorted(rejection_reasons.items(), key=lambda x: -x[1]):
                logger.info(f"  - {reason}: {count} images")

        logger.info("=" * 70)


def main():
    """Main function to run validation."""
    parser = argparse.ArgumentParser(
        description='Validate archaeological fragment images for reconstruction suitability.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'input_dir',
        type=str,
        help='Directory containing images to validate'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for validation report (default: validation_report.json in input directory)'
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
        '--delete-rejected',
        action='store_true',
        help='Delete images that fail validation'
    )

    args = parser.parse_args()

    # Setup paths
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_dir / 'validation_report.json'

    # Run validation
    validator = FragmentValidator(min_width=args.min_width, min_height=args.min_height)
    validator.validate_directory(input_dir, delete_rejected=args.delete_rejected)
    validator.save_report(output_path)
    validator.print_summary()

    return 0 if validator.validation_report['summary']['passed'] > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
