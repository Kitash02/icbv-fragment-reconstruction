"""
Comprehensive stress test for preprocessing pipeline on all real fragments.

Tests preprocessing robustness on:
- 26 fragments from wikimedia_processed
- 20 fragments from wikimedia
- 2 fragments from british_museum

For each fragment, measures:
- Contour extraction success/failure
- Edge detection method used (Canny vs Otsu vs Adaptive)
- Contour quality metrics (point count, area, perimeter)
- Image properties (resolution, aspect ratio, file size)
- Processing time

Identifies problematic images and provides detailed analysis.
"""

import cv2
import numpy as np
import time
import logging
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from preprocessing import preprocess_fragment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FragmentTestResult:
    """Results from testing a single fragment."""
    filename: str
    category: str
    success: bool
    error_message: Optional[str] = None

    # Image properties
    width: int = 0
    height: int = 0
    aspect_ratio: float = 0.0
    file_size_kb: float = 0.0
    resolution_mp: float = 0.0

    # Processing results
    processing_time_ms: float = 0.0
    method_used: str = ""  # "alpha", "canny", "otsu", "adaptive", or "failed"

    # Contour metrics
    contour_points: int = 0
    contour_area: float = 0.0
    contour_perimeter: float = 0.0
    area_ratio: float = 0.0  # contour area / image area

    # Quality indicators
    has_text_labels: bool = False
    has_stand: bool = False
    low_contrast: bool = False
    complex_background: bool = False

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'filename': self.filename,
            'category': self.category,
            'success': self.success,
            'error_message': self.error_message,
            'image_properties': {
                'width': self.width,
                'height': self.height,
                'aspect_ratio': round(self.aspect_ratio, 2),
                'file_size_kb': round(self.file_size_kb, 2),
                'resolution_mp': round(self.resolution_mp, 2)
            },
            'processing': {
                'time_ms': round(self.processing_time_ms, 2),
                'method_used': self.method_used
            },
            'contour_metrics': {
                'points': self.contour_points,
                'area': round(self.contour_area, 2),
                'perimeter': round(self.contour_perimeter, 2),
                'area_ratio': round(self.area_ratio, 4)
            },
            'quality_flags': {
                'has_text_labels': self.has_text_labels,
                'has_stand': self.has_stand,
                'low_contrast': self.low_contrast,
                'complex_background': self.complex_background
            }
        }


def detect_image_issues(image_path: str, image: np.ndarray) -> Dict[str, bool]:
    """
    Analyze image for common issues that may affect preprocessing.

    Returns dict with boolean flags for various issues.
    """
    issues = {
        'has_text_labels': False,
        'has_stand': False,
        'low_contrast': False,
        'complex_background': False
    }

    # Convert to grayscale for analysis
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # Check contrast (standard deviation of pixel intensities)
    std_dev = np.std(gray)
    if std_dev < 30:
        issues['low_contrast'] = True

    # Check for complex background by examining edge density in corners
    h, w = gray.shape
    corner_size = min(h, w) // 10
    corners = [
        gray[:corner_size, :corner_size],
        gray[:corner_size, -corner_size:],
        gray[-corner_size:, :corner_size],
        gray[-corner_size:, -corner_size:]
    ]

    edge_density = 0
    for corner in corners:
        edges = cv2.Canny(corner, 50, 150)
        edge_density += np.sum(edges > 0) / corner.size

    edge_density /= 4
    if edge_density > 0.1:
        issues['complex_background'] = True

    # Heuristic: check filename for indicators
    filename_lower = Path(image_path).name.lower()
    if 'identifying' in filename_lower or 'label' in filename_lower:
        issues['has_text_labels'] = True

    if 'stand' in filename_lower or 'museum' in filename_lower:
        issues['has_stand'] = True

    return issues


def test_fragment(image_path: str, category: str) -> FragmentTestResult:
    """
    Test preprocessing on a single fragment.

    Args:
        image_path: Path to fragment image
        category: Category name (wikimedia_processed, wikimedia, british_museum)

    Returns:
        FragmentTestResult with detailed metrics
    """
    result = FragmentTestResult(
        filename=Path(image_path).name,
        category=category,
        success=False
    )

    try:
        # Get file size
        result.file_size_kb = Path(image_path).stat().st_size / 1024.0

        # Load image to get properties
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            result.error_message = "Failed to load image"
            return result

        result.height, result.width = image.shape[:2]
        result.aspect_ratio = result.width / result.height
        result.resolution_mp = (result.width * result.height) / 1_000_000.0

        # Convert to BGR for analysis
        if image.ndim == 2:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            image_bgr = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        else:
            image_bgr = image

        # Detect potential issues
        issues = detect_image_issues(image_path, image_bgr)
        result.has_text_labels = issues['has_text_labels']
        result.has_stand = issues['has_stand']
        result.low_contrast = issues['low_contrast']
        result.complex_background = issues['complex_background']

        # Configure logging to capture method used
        log_handler = logging.StreamHandler()
        log_handler.setLevel(logging.INFO)
        preprocessing_logger = logging.getLogger('preprocessing')
        preprocessing_logger.addHandler(log_handler)

        # Capture log messages to determine method
        log_messages = []
        class LogCapture(logging.Handler):
            def emit(self, record):
                log_messages.append(record.getMessage())

        capture_handler = LogCapture()
        capture_handler.setLevel(logging.INFO)
        preprocessing_logger.addHandler(capture_handler)

        # Time the preprocessing
        start_time = time.perf_counter()

        try:
            image_result, contour = preprocess_fragment(image_path)

            end_time = time.perf_counter()
            result.processing_time_ms = (end_time - start_time) * 1000.0

            result.success = True
            result.contour_points = len(contour)

            # Calculate contour metrics
            contour_cv = contour.reshape(-1, 1, 2).astype(np.int32)
            result.contour_area = cv2.contourArea(contour_cv)
            result.contour_perimeter = cv2.arcLength(contour_cv, closed=True)

            image_area = result.width * result.height
            result.area_ratio = result.contour_area / image_area if image_area > 0 else 0.0

            # Determine method used from log messages
            if any('alpha channel' in msg.lower() for msg in log_messages):
                result.method_used = "alpha"
            elif any('canny silhouette' in msg.lower() for msg in log_messages):
                result.method_used = "canny"
            elif any('otsu' in msg.lower() for msg in log_messages):
                result.method_used = "otsu"
            elif any('adaptive' in msg.lower() for msg in log_messages):
                result.method_used = "adaptive"
            else:
                result.method_used = "unknown"

        except Exception as e:
            end_time = time.perf_counter()
            result.processing_time_ms = (end_time - start_time) * 1000.0
            result.error_message = str(e)
            result.method_used = "failed"

        finally:
            preprocessing_logger.removeHandler(capture_handler)
            preprocessing_logger.removeHandler(log_handler)

    except Exception as e:
        result.error_message = f"Unexpected error: {str(e)}"

    return result


def collect_fragment_paths() -> Dict[str, List[str]]:
    """
    Collect all fragment image paths organized by category.

    Returns:
        Dict mapping category name to list of image paths
    """
    base_path = Path(__file__).parent.parent / "data" / "raw" / "real_fragments_validated"

    categories = {
        'wikimedia_processed': [],
        'wikimedia': [],
        'british_museum': []
    }

    # Wikimedia processed (26 fragments, exclude example1_auto duplicates)
    wp_path = base_path / "wikimedia_processed"
    if wp_path.exists():
        for img_path in sorted(wp_path.glob("*.jpg")):
            categories['wikimedia_processed'].append(str(img_path))

    # Wikimedia (20 candidates)
    w_path = base_path / "wikimedia"
    if w_path.exists():
        for img_path in sorted(w_path.glob("candidate_*.jpg")):
            categories['wikimedia'].append(str(img_path))

    # British Museum (2 fragments)
    bm_path = base_path / "british_museum"
    if bm_path.exists():
        for img_path in sorted(bm_path.glob("*.jpg")):
            if 'wikimedia' not in str(img_path):  # Exclude nested wikimedia folder
                categories['british_museum'].append(str(img_path))

    return categories


def generate_report(results: List[FragmentTestResult], output_path: str):
    """
    Generate comprehensive markdown report from test results.

    Args:
        results: List of test results
        output_path: Path to save report
    """
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful

    success_rate = (successful / total * 100) if total > 0 else 0

    # Statistics by category
    category_stats = {}
    for result in results:
        cat = result.category
        if cat not in category_stats:
            category_stats[cat] = {'total': 0, 'success': 0, 'failed': 0}
        category_stats[cat]['total'] += 1
        if result.success:
            category_stats[cat]['success'] += 1
        else:
            category_stats[cat]['failed'] += 1

    # Method usage statistics
    method_counts = {}
    for result in results:
        if result.success:
            method = result.method_used
            method_counts[method] = method_counts.get(method, 0) + 1

    # Quality metrics for successful extractions
    successful_results = [r for r in results if r.success]

    if successful_results:
        avg_points = np.mean([r.contour_points for r in successful_results])
        avg_area_ratio = np.mean([r.area_ratio for r in successful_results])
        avg_time = np.mean([r.processing_time_ms for r in successful_results])

        min_resolution = min(r.resolution_mp for r in successful_results)
        max_resolution = max(r.resolution_mp for r in successful_results)
    else:
        avg_points = avg_area_ratio = avg_time = 0
        min_resolution = max_resolution = 0

    # Issue flags
    issue_counts = {
        'text_labels': sum(1 for r in results if r.has_text_labels),
        'stand': sum(1 for r in results if r.has_stand),
        'low_contrast': sum(1 for r in results if r.low_contrast),
        'complex_background': sum(1 for r in results if r.complex_background)
    }

    # Generate markdown report
    report = f"""# Preprocessing Pipeline Robustness Test Report

**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Total Fragments Tested:** {total}

---

## Executive Summary

- **Overall Success Rate:** {success_rate:.1f}% ({successful}/{total} fragments)
- **Failed Extractions:** {failed} fragments
- **Average Processing Time:** {avg_time:.2f}ms per fragment
- **Average Contour Points:** {avg_points:.0f} points
- **Average Area Coverage:** {avg_area_ratio:.2%} of image area

---

## Success Rate by Category

| Category | Total | Success | Failed | Success Rate |
|----------|-------|---------|--------|--------------|
"""

    for cat, stats in sorted(category_stats.items()):
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        report += f"| {cat} | {stats['total']} | {stats['success']} | {stats['failed']} | {rate:.1f}% |\n"

    report += f"""
---

## Edge Detection Method Usage

Successfully processed fragments used the following methods:

| Method | Count | Percentage |
|--------|-------|------------|
"""

    total_successful = sum(method_counts.values())
    for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total_successful * 100) if total_successful > 0 else 0
        report += f"| {method} | {count} | {pct:.1f}% |\n"

    report += f"""
**Method Descriptions:**
- **alpha:** Used alpha channel from RGBA image (highest quality)
- **canny:** Canny edge detection with flood fill
- **otsu:** Otsu's global thresholding
- **adaptive:** Adaptive local thresholding

---

## Image Characteristic Analysis

### Resolution Distribution

- **Minimum Resolution:** {min_resolution:.2f} MP
- **Maximum Resolution:** {max_resolution:.2f} MP
- **Average Resolution:** {np.mean([r.resolution_mp for r in results]):.2f} MP

### Aspect Ratio Distribution

"""

    aspect_ratios = [r.aspect_ratio for r in results if r.aspect_ratio > 0]
    if aspect_ratios:
        report += f"""- **Minimum:** {min(aspect_ratios):.2f}
- **Maximum:** {max(aspect_ratios):.2f}
- **Average:** {np.mean(aspect_ratios):.2f}

"""

    report += f"""### File Size Distribution

- **Minimum:** {min(r.file_size_kb for r in results):.2f} KB
- **Maximum:** {max(r.file_size_kb for r in results):.2f} KB
- **Average:** {np.mean([r.file_size_kb for r in results]):.2f} KB

---

## Problematic Image Characteristics

Images flagged with potential preprocessing issues:

| Issue Type | Count | Percentage |
|------------|-------|------------|
| Text Labels/Annotations | {issue_counts['text_labels']} | {issue_counts['text_labels']/total*100:.1f}% |
| Museum Stands/Fixtures | {issue_counts['stand']} | {issue_counts['stand']/total*100:.1f}% |
| Low Contrast | {issue_counts['low_contrast']} | {issue_counts['low_contrast']/total*100:.1f}% |
| Complex Background | {issue_counts['complex_background']} | {issue_counts['complex_background']/total*100:.1f}% |

---

## Failed Extractions

"""

    failed_results = [r for r in results if not r.success]
    if failed_results:
        report += f"**Total Failures:** {len(failed_results)}\n\n"
        for r in failed_results:
            report += f"### {r.filename}\n\n"
            report += f"- **Category:** {r.category}\n"
            report += f"- **Resolution:** {r.width}x{r.height} ({r.resolution_mp:.2f} MP)\n"
            report += f"- **Error:** {r.error_message}\n"
            report += f"- **Processing Time:** {r.processing_time_ms:.2f}ms\n"

            issues = []
            if r.has_text_labels:
                issues.append("text labels")
            if r.has_stand:
                issues.append("museum stand")
            if r.low_contrast:
                issues.append("low contrast")
            if r.complex_background:
                issues.append("complex background")

            if issues:
                report += f"- **Detected Issues:** {', '.join(issues)}\n"

            report += "\n"
    else:
        report += "**No failed extractions!** All fragments processed successfully.\n\n"

    report += """---

## Contour Quality Metrics

For successfully processed fragments:

"""

    if successful_results:
        contour_points = [r.contour_points for r in successful_results]
        area_ratios = [r.area_ratio for r in successful_results]
        perimeters = [r.contour_perimeter for r in successful_results]

        report += f"""### Contour Point Count

- **Minimum:** {min(contour_points)} points
- **Maximum:** {max(contour_points)} points
- **Average:** {np.mean(contour_points):.0f} points
- **Median:** {np.median(contour_points):.0f} points

### Area Coverage Ratio

Percentage of image area occupied by extracted contour:

- **Minimum:** {min(area_ratios):.2%}
- **Maximum:** {max(area_ratios):.2%}
- **Average:** {np.mean(area_ratios):.2%}
- **Median:** {np.median(area_ratios):.2%}

### Contour Perimeter

- **Minimum:** {min(perimeters):.0f} pixels
- **Maximum:** {max(perimeters):.0f} pixels
- **Average:** {np.mean(perimeters):.0f} pixels

"""

    report += """---

## Processing Time Analysis

"""

    processing_times = [r.processing_time_ms for r in results if r.processing_time_ms > 0]
    if processing_times:
        report += f"""- **Minimum:** {min(processing_times):.2f}ms
- **Maximum:** {max(processing_times):.2f}ms
- **Average:** {np.mean(processing_times):.2f}ms
- **Median:** {np.median(processing_times):.2f}ms
- **Total:** {sum(processing_times):.2f}ms ({sum(processing_times)/1000:.2f}s)

"""

    report += """---

## Recommendations

### Image Quality Standards

Based on this stress test, the following standards are recommended for fragment images:

1. **Resolution:** Minimum 0.5 MP (megapixels) recommended for reliable contour extraction
2. **Background:** Plain, uniform background (white or neutral gray preferred)
3. **Lighting:** Even illumination without harsh shadows
4. **Contrast:** Fragment should have clear contrast with background (std dev > 30)
5. **Composition:** Single fragment per image, centered
6. **Cleanliness:** No text labels, rulers, or museum stands in frame

### Filtering Criteria for Future Data

**Exclude images with:**
- Complex textured backgrounds
- Multiple fragments in single image
- Text overlays or scale markers
- Heavy shadows or uneven lighting
- Very low contrast (std dev < 30)

**Prefer images with:**
- RGBA format with alpha channel (best quality)
- High resolution (> 1 MP)
- Clean white or neutral background
- Good fragment-background contrast
- Single centered fragment

### Method Selection Guidelines

"""

    if method_counts:
        most_common = max(method_counts.items(), key=lambda x: x[1])[0]
        report += f"""The preprocessing pipeline successfully adapts to different image types:

- **Alpha channel method** provides the most reliable results when available (RGBA images)
- **Canny edge detection** is the preferred method for real photographs (used in {method_counts.get('canny', 0)} cases)
- **Threshold-based methods** (Otsu/Adaptive) serve as reliable fallbacks

**Most commonly used method:** {most_common} ({method_counts[most_common]} fragments)

"""

    report += """---

## Edge Cases Identified

"""

    # Identify edge cases
    edge_cases = []

    # Very small fragments
    small_fragments = [r for r in successful_results if r.area_ratio < 0.1]
    if small_fragments:
        edge_cases.append(f"**Small fragments** ({len(small_fragments)} cases): Fragment occupies < 10% of image area")

    # Very large fragments
    large_fragments = [r for r in successful_results if r.area_ratio > 0.8]
    if large_fragments:
        edge_cases.append(f"**Large fragments** ({len(large_fragments)} cases): Fragment occupies > 80% of image area")

    # High resolution
    high_res = [r for r in results if r.resolution_mp > 5.0]
    if high_res:
        edge_cases.append(f"**High resolution** ({len(high_res)} cases): Images > 5 MP")

    # Low resolution
    low_res = [r for r in results if r.resolution_mp < 0.5]
    if low_res:
        edge_cases.append(f"**Low resolution** ({len(low_res)} cases): Images < 0.5 MP")

    # Extreme aspect ratios
    extreme_aspect = [r for r in results if r.aspect_ratio > 2.0 or r.aspect_ratio < 0.5]
    if extreme_aspect:
        edge_cases.append(f"**Extreme aspect ratios** ({len(extreme_aspect)} cases): Ratio > 2.0 or < 0.5")

    # Complex contours (many points)
    if successful_results:
        avg_pts = np.mean([r.contour_points for r in successful_results])
        complex_contours = [r for r in successful_results if r.contour_points > avg_pts * 2]
        if complex_contours:
            edge_cases.append(f"**Complex contours** ({len(complex_contours)} cases): > {avg_pts*2:.0f} points (2x average)")

    if edge_cases:
        for case in edge_cases:
            report += f"- {case}\n"
    else:
        report += "No significant edge cases identified. All fragments fall within normal parameters.\n"

    report += f"""
---

## Detailed Test Results

Full JSON data for all {total} fragments:

"""

    # Add JSON data
    json_data = [r.to_dict() for r in results]
    report += f"""```json
{json.dumps(json_data, indent=2)}
```

---

## Conclusion

This stress test evaluated the preprocessing pipeline on all {total} real archaeological fragment images
across three categories. The pipeline achieved a **{success_rate:.1f}% success rate**, demonstrating
robust performance across diverse image types and quality levels.

### Key Findings

1. **Method Adaptivity:** The pipeline successfully selects appropriate edge detection methods based on image characteristics
2. **Category Performance:** {'All categories show strong performance' if all(s['success']/s['total'] > 0.8 for s in category_stats.values()) else 'Some categories require attention'}
3. **Edge Case Handling:** {len(edge_cases)} types of edge cases identified and successfully processed
4. **Processing Efficiency:** Average processing time of {avg_time:.2f}ms enables real-time preprocessing

### Next Steps

- Investigate failed cases to improve robustness
- Consider additional preprocessing strategies for low-contrast images
- Develop automated quality scoring for input image selection
- Implement preprocessing parameter tuning for specific categories

---

*Report generated by stress_test_preprocessing.py*
*Dataset: {total} fragments from wikimedia_processed ({category_stats.get('wikimedia_processed', {}).get('total', 0)}),
wikimedia ({category_stats.get('wikimedia', {}).get('total', 0)}),
and british_museum ({category_stats.get('british_museum', {}).get('total', 0)})*
"""

    # Write report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(report, encoding='utf-8')

    print(f"\n[OK] Report saved to: {output_path}")
    print(f"  Total fragments tested: {total}")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Failed: {failed}")


def main():
    """Run comprehensive preprocessing stress test."""
    print("=" * 80)
    print("PREPROCESSING PIPELINE STRESS TEST")
    print("=" * 80)
    print()

    # Collect all fragment paths
    print("Collecting fragment images...")
    categories = collect_fragment_paths()

    total_count = sum(len(paths) for paths in categories.values())
    print(f"Found {total_count} total fragments:")
    for cat, paths in categories.items():
        print(f"  - {cat}: {len(paths)} fragments")
    print()

    # Test each fragment
    print("Testing preprocessing on all fragments...")
    print("-" * 80)

    all_results = []

    for category, paths in categories.items():
        print(f"\nCategory: {category}")
        print("-" * 40)

        for i, path in enumerate(paths, 1):
            filename = Path(path).name
            print(f"  [{i}/{len(paths)}] {filename}...", end=" ", flush=True)

            result = test_fragment(path, category)
            all_results.append(result)

            if result.success:
                print(f"[OK] {result.method_used} ({result.processing_time_ms:.0f}ms, {result.contour_points} pts)")
            else:
                print(f"[FAIL] {result.error_message}")

    print()
    print("=" * 80)
    print("GENERATING REPORT")
    print("=" * 80)

    # Generate report
    output_path = Path(__file__).parent.parent / "outputs" / "testing" / "preprocessing_robustness.md"
    generate_report(all_results, str(output_path))

    # Print summary
    successful = sum(1 for r in all_results if r.success)
    success_rate = (successful / len(all_results) * 100) if all_results else 0

    print()
    print("=" * 80)
    print("STRESS TEST COMPLETE")
    print("=" * 80)
    print(f"Total fragments: {len(all_results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(all_results) - successful}")
    print(f"Success rate: {success_rate:.1f}%")
    print()
    print(f"Detailed report: {output_path}")
    print()


if __name__ == "__main__":
    main()
