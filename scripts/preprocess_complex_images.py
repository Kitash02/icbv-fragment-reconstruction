#!/usr/bin/env python3
"""
Complex Image Preprocessing for Archaeological Fragment Images

This script handles multi-fragment images that cannot be directly processed by the main
reconstruction pipeline. It provides three modes:

1. AUTO MODE: Automatically detects and splits multi-fragment images into individual files
2. BACKGROUND REMOVAL MODE: Removes complex backgrounds using GrabCut algorithm
3. MANUAL MODE: Interactive cropping interface for user-guided fragment extraction

The script builds on the early vision techniques from Lectures 21-23:
  - Gaussian smoothing for noise suppression (Lecture 22)
  - Morphological operations for connected component isolation
  - Contour detection and analysis (Lecture 23)
  - GrabCut algorithm for foreground/background segmentation (OpenCV implementation)

Usage:
    # Automatically split multi-fragment images
    python preprocess_complex_images.py \\
        --input data/raw/real_fragments/wikimedia \\
        --output data/raw/real_fragments_validated/wikimedia_processed \\
        --mode auto

    # Interactive manual cropping
    python preprocess_complex_images.py \\
        --input data/raw/real_fragments/wikimedia \\
        --output data/raw/real_fragments_validated/wikimedia_processed \\
        --mode manual

    # Background removal only (no splitting)
    python preprocess_complex_images.py \\
        --input data/raw/real_fragments/wikimedia \\
        --output data/raw/real_fragments_validated/wikimedia_processed \\
        --mode background

Output:
    - Individual fragment images with white backgrounds
    - Processing log (preprocess_TIMESTAMP.log)
    - Transformation manifest (manifest.json)
"""

import cv2
import numpy as np
import argparse
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

# Processing parameters
GAUSSIAN_KERNEL = (5, 5)
GAUSSIAN_SIGMA = 1.5
MIN_FRAGMENT_AREA = 1000  # Minimum pixels for a valid fragment
MIN_FRAGMENT_SIZE = 30    # Minimum width/height in pixels
MORPH_KERNEL_SIZE = 7
GRABCUT_ITERATIONS = 5
BORDER_MARGIN = 10        # Pixels of white border around extracted fragments

logger = logging.getLogger(__name__)


def setup_logging(output_dir: Path) -> None:
    """
    Configure logging to both file and console.

    Creates timestamped log file in the output directory and mirrors
    INFO-level messages to stdout for user feedback.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = output_dir / f"preprocess_{timestamp}.log"

    # File handler - detailed logging
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - user-friendly messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.info(f"Logging to {log_file}")


def load_image(path: Path) -> np.ndarray:
    """Load image as BGR array, raising error if file not found."""
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    logger.info(f"Loaded {path.name} -- shape {image.shape}")
    return image


def detect_background_color(image: np.ndarray, sample_size: int = 50) -> np.ndarray:
    """
    Estimate background color by sampling image corners.

    Assumes corners contain background pixels. Returns mean BGR color
    vector for use in background removal.
    """
    h, w = image.shape[:2]
    s = min(sample_size, h // 4, w // 4)

    corners = [
        image[:s, :s],
        image[:s, -s:],
        image[-s:, :s],
        image[-s:, -s:],
    ]

    mean_color = np.mean([patch.mean(axis=(0, 1)) for patch in corners], axis=0)
    logger.debug(f"Detected background color: BGR={mean_color}")
    return mean_color.astype(np.uint8)


def preprocess_for_segmentation(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Gaussian blur and create binary mask for fragment detection.

    Implements early vision pipeline from Lectures 21-22:
      1. Gaussian smoothing to suppress noise
      2. Otsu thresholding for automatic binarization
      3. Morphological closing to connect fragment regions

    Returns:
        gray: Blurred grayscale image
        binary: Clean binary mask (255 = fragment, 0 = background)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, GAUSSIAN_KERNEL, GAUSSIAN_SIGMA)

    # Determine if background is light or dark
    bg_brightness = detect_background_color(image).mean()
    is_light_bg = bg_brightness > 128

    # Apply Otsu thresholding
    if is_light_bg:
        _, binary = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
    else:
        _, binary = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

    # Morphological cleanup: close small gaps between fragment parts
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE)
    )
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    logger.debug(f"Preprocessing: background={'light' if is_light_bg else 'dark'}")
    return blurred, binary


def detect_fragments(binary_mask: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Detect individual fragment bounding boxes using connected component analysis.

    Uses cv2.findContours (Lecture 23) to identify separate connected regions
    in the binary mask. Each region above MIN_FRAGMENT_AREA is considered a
    potential fragment.

    Returns:
        List of bounding boxes as (x, y, width, height) tuples, sorted by area
        (largest first)
    """
    contours, _ = cv2.findContours(
        binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    fragments = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < MIN_FRAGMENT_AREA:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        if w < MIN_FRAGMENT_SIZE or h < MIN_FRAGMENT_SIZE:
            continue

        fragments.append((x, y, w, h))

    # Sort by area (largest first)
    fragments.sort(key=lambda box: box[2] * box[3], reverse=True)

    logger.info(f"Detected {len(fragments)} fragments above size threshold")
    return fragments


def apply_grabcut_background_removal(
    image: np.ndarray,
    bbox: Optional[Tuple[int, int, int, int]] = None
) -> np.ndarray:
    """
    Remove background using GrabCut algorithm.

    GrabCut is an iterative graph-cut based segmentation technique that
    separates foreground from background. If bbox is provided, it initializes
    the algorithm with that region as likely foreground. Otherwise, uses
    automatic initialization based on image borders.

    Args:
        image: Input BGR image
        bbox: Optional (x, y, w, h) rectangle hint for foreground region

    Returns:
        RGBA image with transparent background and white fill
    """
    h, w = image.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    if bbox is None:
        # Use center region as probable foreground
        margin = min(h, w) // 6
        bbox = (margin, margin, w - 2 * margin, h - 2 * margin)

    x, y, bw, bh = bbox
    # Ensure bbox is within image bounds
    x = max(0, x)
    y = max(0, y)
    bw = min(bw, w - x)
    bh = min(bh, h - y)
    rect = (x, y, bw, bh)

    try:
        cv2.grabCut(
            image, mask, rect, bgd_model, fgd_model,
            GRABCUT_ITERATIONS, cv2.GC_INIT_WITH_RECT
        )
    except cv2.error as e:
        logger.warning(f"GrabCut failed: {e}. Using bounding box crop instead.")
        # Fallback: simple mask from bbox
        mask[:, :] = cv2.GC_BGD
        mask[y:y+bh, x:x+bw] = cv2.GC_FGD

    # Create binary mask (foreground = 255, background = 0)
    fg_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # Create white background result
    result = np.full_like(image, 255, dtype=np.uint8)
    result = cv2.bitwise_and(image, image, dst=result, mask=fg_mask)
    result[fg_mask == 0] = 255  # White background

    logger.debug(f"GrabCut: extracted {fg_mask.sum() / 255} foreground pixels")
    return result


def extract_fragment(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    apply_grabcut: bool = True
) -> np.ndarray:
    """
    Extract a single fragment from the source image.

    Crops the bounding box region, optionally applies GrabCut for refined
    background removal, and adds a white border margin around the result.

    Args:
        image: Source BGR image
        bbox: (x, y, width, height) bounding box
        apply_grabcut: Whether to apply GrabCut segmentation

    Returns:
        Extracted fragment on white background
    """
    x, y, w, h = bbox
    cropped = image[y:y+h, x:x+w].copy()

    if apply_grabcut:
        # Apply GrabCut within the cropped region
        cropped = apply_grabcut_background_removal(cropped)

    # Add white border margin
    bordered = cv2.copyMakeBorder(
        cropped,
        BORDER_MARGIN, BORDER_MARGIN, BORDER_MARGIN, BORDER_MARGIN,
        cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )

    return bordered


def auto_split_fragments(
    image: np.ndarray,
    output_dir: Path,
    base_name: str,
    apply_grabcut: bool = False
) -> List[str]:
    """
    Automatically detect and split multi-fragment images.

    Pipeline:
      1. Preprocess image to get binary mask
      2. Detect connected components as individual fragments
      3. Extract each fragment to separate file
      4. Optionally apply GrabCut for background refinement

    Args:
        image: Input BGR image
        output_dir: Directory to save extracted fragments
        base_name: Base filename (without extension) for output files
        apply_grabcut: Whether to use GrabCut for background removal

    Returns:
        List of output filenames
    """
    _, binary = preprocess_for_segmentation(image)
    fragments = detect_fragments(binary)

    if len(fragments) == 0:
        logger.warning("No fragments detected in image")
        return []

    if len(fragments) == 1:
        logger.info("Only one fragment detected - image may not need splitting")

    output_files = []
    for idx, bbox in enumerate(fragments, start=1):
        fragment_img = extract_fragment(image, bbox, apply_grabcut=apply_grabcut)

        # Save with zero-padded index
        output_name = f"{base_name}_fragment_{idx:03d}.jpg"
        output_path = output_dir / output_name
        cv2.imwrite(str(output_path), fragment_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

        x, y, w, h = bbox
        logger.info(f"  Extracted fragment {idx}: {w}x{h} pixels -> {output_name}")
        output_files.append(output_name)

    return output_files


def manual_crop_mode(image: np.ndarray, output_dir: Path, base_name: str) -> List[str]:
    """
    Interactive manual cropping interface.

    Displays the image and allows user to draw bounding boxes around fragments.
    Press 'r' to reset, 's' to save current box, 'q' to quit.

    Returns:
        List of output filenames
    """
    output_files = []
    fragment_count = 0

    # State for ROI selection
    roi_state = {
        'selecting': False,
        'start_point': None,
        'current_rect': None
    }

    def mouse_callback(event, x, y, flags, param):
        """Handle mouse events for bounding box drawing."""
        display_img = param['display']

        if event == cv2.EVENT_LBUTTONDOWN:
            roi_state['selecting'] = True
            roi_state['start_point'] = (x, y)
            roi_state['current_rect'] = None

        elif event == cv2.EVENT_MOUSEMOVE and roi_state['selecting']:
            temp_img = display_img.copy()
            cv2.rectangle(temp_img, roi_state['start_point'], (x, y), (0, 255, 0), 2)
            cv2.imshow('Manual Crop', temp_img)

        elif event == cv2.EVENT_LBUTTONUP:
            roi_state['selecting'] = False
            x1, y1 = roi_state['start_point']
            x2, y2 = x, y

            # Normalize coordinates
            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)

            roi_state['current_rect'] = (x_min, y_min, x_max - x_min, y_max - y_min)

            # Draw final rectangle
            temp_img = display_img.copy()
            cv2.rectangle(temp_img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            cv2.imshow('Manual Crop', temp_img)

    # Create window and setup
    window_name = 'Manual Crop'
    cv2.namedWindow(window_name)

    # Scale image if too large for display
    display_img = image.copy()
    scale_factor = 1.0
    max_display_size = 1200
    h, w = image.shape[:2]
    if max(h, w) > max_display_size:
        scale_factor = max_display_size / max(h, w)
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)
        display_img = cv2.resize(display_img, (new_w, new_h))
        logger.info(f"Display scaled to {new_w}x{new_h} for visibility")

    cv2.setMouseCallback(window_name, mouse_callback, {'display': display_img})

    print("\n" + "="*60)
    print("MANUAL CROP MODE")
    print("="*60)
    print("Instructions:")
    print("  - Click and drag to draw bounding box around fragment")
    print("  - Press 's' to save current selection")
    print("  - Press 'r' to reset current selection")
    print("  - Press 'q' to quit")
    print("="*60 + "\n")

    cv2.imshow(window_name, display_img)

    while True:
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('r'):
            # Reset selection
            roi_state['current_rect'] = None
            roi_state['selecting'] = False
            cv2.imshow(window_name, display_img)
            logger.info("Selection reset")

        elif key == ord('s'):
            # Save current selection
            if roi_state['current_rect'] is not None:
                x, y, w, h = roi_state['current_rect']

                # Scale back to original image coordinates
                if scale_factor != 1.0:
                    x = int(x / scale_factor)
                    y = int(y / scale_factor)
                    w = int(w / scale_factor)
                    h = int(h / scale_factor)

                if w > MIN_FRAGMENT_SIZE and h > MIN_FRAGMENT_SIZE:
                    fragment_count += 1
                    fragment_img = extract_fragment(image, (x, y, w, h), apply_grabcut=True)

                    output_name = f"{base_name}_manual_{fragment_count:03d}.jpg"
                    output_path = output_dir / output_name
                    cv2.imwrite(str(output_path), fragment_img, [cv2.IMWRITE_JPEG_QUALITY, 95])

                    logger.info(f"Saved fragment {fragment_count}: {w}x{h} -> {output_name}")
                    output_files.append(output_name)

                    # Reset for next selection
                    roi_state['current_rect'] = None
                    cv2.imshow(window_name, display_img)
                else:
                    logger.warning("Selection too small, must be at least 30x30 pixels")
            else:
                logger.warning("No selection to save - draw a box first")

    cv2.destroyAllWindows()
    return output_files


def process_image(
    input_path: Path,
    output_dir: Path,
    mode: str,
    manifest: Dict
) -> None:
    """
    Process a single image according to the selected mode.

    Args:
        input_path: Path to input image
        output_dir: Directory for output files
        mode: Processing mode ('auto', 'manual', 'background')
        manifest: Dictionary to record transformations
    """
    logger.info(f"\nProcessing: {input_path.name}")
    logger.info("="*60)

    try:
        image = load_image(input_path)
    except Exception as e:
        logger.error(f"Failed to load {input_path}: {e}")
        return

    base_name = input_path.stem
    output_files = []

    try:
        if mode == 'auto':
            output_files = auto_split_fragments(image, output_dir, base_name, apply_grabcut=False)

        elif mode == 'background':
            output_files = auto_split_fragments(image, output_dir, base_name, apply_grabcut=True)

        elif mode == 'manual':
            output_files = manual_crop_mode(image, output_dir, base_name)

        # Record transformation in manifest
        manifest[input_path.name] = {
            'mode': mode,
            'output_files': output_files,
            'fragment_count': len(output_files),
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Successfully processed: {len(output_files)} fragments extracted")

    except Exception as e:
        logger.error(f"Error processing {input_path.name}: {e}", exc_info=True)
        manifest[input_path.name] = {
            'mode': mode,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Main entry point for the preprocessing script."""
    parser = argparse.ArgumentParser(
        description="Preprocess complex archaeological fragment images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-split multi-fragment image
  python preprocess_complex_images.py -i data/raw -o data/processed -m auto

  # Manual cropping with interactive GUI
  python preprocess_complex_images.py -i data/raw -o data/processed -m manual

  # Background removal with GrabCut
  python preprocess_complex_images.py -i data/raw -o data/processed -m background
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Input directory containing fragment images'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Output directory for processed fragments'
    )

    parser.add_argument(
        '--mode', '-m',
        choices=['auto', 'manual', 'background'],
        default='auto',
        help='Processing mode: auto (split), manual (interactive), background (GrabCut)'
    )

    parser.add_argument(
        '--pattern',
        default='*.jpg',
        help='File pattern to match (default: *.jpg)'
    )

    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip images already in manifest'
    )

    args = parser.parse_args()

    # Validate paths
    if not args.input.exists():
        print(f"Error: Input directory does not exist: {args.input}", file=sys.stderr)
        return 1

    # Setup output directory and logging
    args.output.mkdir(parents=True, exist_ok=True)
    setup_logging(args.output)

    # Load or create manifest
    manifest_path = args.output / 'manifest.json'
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logger.info(f"Loaded existing manifest with {len(manifest)} entries")

    # Find input images
    image_files = sorted(args.input.glob(args.pattern))
    if not image_files:
        logger.error(f"No images found matching pattern '{args.pattern}' in {args.input}")
        return 1

    logger.info(f"Found {len(image_files)} images to process")
    logger.info(f"Mode: {args.mode.upper()}")
    logger.info(f"Output directory: {args.output}")

    # Process each image
    processed_count = 0
    skipped_count = 0

    for img_path in image_files:
        # Skip if already processed and flag is set
        if args.skip_existing and img_path.name in manifest:
            logger.info(f"Skipping (already processed): {img_path.name}")
            skipped_count += 1
            continue

        process_image(img_path, args.output, args.mode, manifest)
        processed_count += 1

        # Save manifest after each image (for safety)
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*60)
    logger.info(f"Processed: {processed_count} images")
    logger.info(f"Skipped: {skipped_count} images")
    logger.info(f"Total fragments extracted: {sum(m.get('fragment_count', 0) for m in manifest.values())}")
    logger.info(f"Manifest saved to: {manifest_path}")
    logger.info("="*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
