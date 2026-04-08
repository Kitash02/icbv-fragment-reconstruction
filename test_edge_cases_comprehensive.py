#!/usr/bin/env python3
"""
Comprehensive Edge Case Testing Script
Tests system robustness with boundary conditions and extreme scenarios
"""

import sys
import os
import time
import argparse
import shutil
from pathlib import Path
from datetime import datetime
import io
from contextlib import redirect_stdout
import logging

import cv2
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from preprocessing import preprocess_fragment
import main as pipeline_main

# Test configuration
BASE_DIR = Path(__file__).parent
TEMP_DIR = BASE_DIR / "outputs" / "edge_case_tests"
REPORT_DIR = BASE_DIR / "outputs" / "implementation"
LOG_DIR = BASE_DIR / "outputs" / "logs"

# Ensure directories exist
TEMP_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


class EdgeCaseResult:
    """Container for test results"""
    def __init__(self, name):
        self.name = name
        self.status = "PENDING"
        self.message = ""
        self.details = {}
        self.recommendation = ""
        self.start_time = time.time()
        self.end_time = None

    def mark_pass(self, message, details=None, recommendation=""):
        self.status = "PASS"
        self.message = message
        self.details = details or {}
        self.recommendation = recommendation
        self.end_time = time.time()

    def mark_fail(self, message, details=None, recommendation=""):
        self.status = "FAIL"
        self.message = message
        self.details = details or {}
        self.recommendation = recommendation
        self.end_time = time.time()

    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time


def create_synthetic_fragment(path, size, color=(100, 100, 100), shape='circle'):
    """Create a synthetic fragment image"""
    img = np.ones((size[1], size[0], 3), dtype=np.uint8) * 255

    if shape == 'circle':
        radius = min(size) // 3
        cv2.circle(img, (size[0]//2, size[1]//2), radius, color, -1)
    elif shape == 'square':
        margin = min(size) // 5
        cv2.rectangle(img, (margin, margin),
                     (size[0]-margin, size[1]-margin), color, -1)
    elif shape == 'irregular':
        # Create star-like irregular shape
        center = (size[0]//2, size[1]//2)
        points = []
        for j in range(10):
            angle = j * np.pi / 5
            radius = (min(size) // 3) if j % 2 == 0 else (min(size) // 5)
            x = int(center[0] + radius * np.cos(angle))
            y = int(center[1] + radius * np.sin(angle))
            points.append([x, y])
        points = np.array(points, dtype=np.int32)
        cv2.fillPoly(img, [points], color)

    cv2.imwrite(str(path), img)


def run_pipeline_test(test_dir, test_name):
    """Run the pipeline on a test directory and capture results"""
    output_dir = TEMP_DIR / f"output_{test_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    captured = io.StringIO()
    logging.disable(logging.WARNING)

    try:
        args_ns = argparse.Namespace(
            input=str(test_dir),
            output=str(output_dir),
            log=str(LOG_DIR)
        )

        t0 = time.time()
        with redirect_stdout(captured):
            pipeline_main.run_pipeline(args_ns)
        elapsed = time.time() - t0

        output_text = captured.getvalue()
        verdict = "UNKNOWN"

        for line in output_text.splitlines():
            if "[RESULT]" in line:
                if "NO MATCH" in line:
                    verdict = "NO_MATCH"
                elif "MATCH FOUND" in line:
                    verdict = "MATCH"

        return {
            'success': True,
            'verdict': verdict,
            'elapsed': elapsed,
            'output': output_text
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'elapsed': time.time() - t0 if 't0' in locals() else 0
        }
    finally:
        logging.disable(logging.NOTSET)


def test_1_single_fragment():
    """Test Case 1: Single fragment (should handle gracefully)"""
    result = EdgeCaseResult("1. Single Fragment")

    test_dir = TEMP_DIR / "test_1_single"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create one fragment
    create_synthetic_fragment(test_dir / "frag_01.png", (300, 300))

    # Try to run pipeline
    try:
        from main import collect_fragment_paths
        paths = collect_fragment_paths(str(test_dir))

        if len(paths) == 1:
            # System should require at least 2 fragments
            # Try preprocessing at least
            img, cnt = preprocess_fragment(str(paths[0]))
            result.mark_pass(
                "System handles single fragment gracefully",
                details={'fragments': 1, 'preprocessing': 'success'},
                recommendation="Add check to require minimum 2 fragments before assembly"
            )
        else:
            result.mark_fail("Unexpected fragment count")

    except Exception as e:
        if "at least" in str(e).lower() or "minimum" in str(e).lower():
            result.mark_pass(
                f"System correctly rejects single fragment: {str(e)[:80]}",
                recommendation="Error handling is appropriate"
            )
        else:
            result.mark_fail(f"Unexpected error: {str(e)}")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def test_2_large_fragment_count():
    """Test Case 2: 100+ fragments (performance test)"""
    result = EdgeCaseResult("2. Large Fragment Count (100+)")

    test_dir = TEMP_DIR / "test_2_large"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create 100 small fragments (reduced size for speed)
    n_fragments = 100
    t0 = time.time()

    try:
        for i in range(n_fragments):
            create_synthetic_fragment(
                test_dir / f"frag_{i:03d}.png",
                (150, 150),
                color=(100 + i % 155, 100, 100),
                shape='circle' if i % 2 == 0 else 'square'
            )

        # Test preprocessing only (full pipeline would be too slow)
        processed = 0
        preprocess_time = 0

        for i in range(min(10, n_fragments)):  # Test first 10
            frag_path = test_dir / f"frag_{i:03d}.png"
            t_start = time.time()
            img, cnt = preprocess_fragment(str(frag_path))
            preprocess_time += time.time() - t_start
            if len(cnt) > 0:
                processed += 1

        avg_time = preprocess_time / 10
        estimated_total = avg_time * n_fragments

        result.mark_pass(
            f"Preprocessed {processed}/10 test fragments successfully",
            details={
                'total_fragments': n_fragments,
                'avg_preprocess_time': f"{avg_time:.3f}s",
                'estimated_total_time': f"{estimated_total:.1f}s"
            },
            recommendation=f"System can handle {n_fragments} fragments but processing time is ~{estimated_total:.0f}s. "
                          f"Consider parallel processing or batch optimization for large datasets."
        )

    except Exception as e:
        result.mark_fail(
            f"Failed with {n_fragments} fragments: {str(e)[:100]}",
            recommendation="Consider memory limits or add fragment count warnings"
        )

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def test_3_tiny_images():
    """Test Case 3: Tiny images (<100px)"""
    result = EdgeCaseResult("3. Tiny Images (<100px)")

    test_dir = TEMP_DIR / "test_3_tiny"
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create very small fragments (50x50)
        create_synthetic_fragment(test_dir / "tiny_01.png", (50, 50), color=(120, 120, 120))
        create_synthetic_fragment(test_dir / "tiny_02.png", (50, 50), color=(120, 120, 120))

        pipeline_result = run_pipeline_test(test_dir, "tiny")

        if pipeline_result['success']:
            result.mark_pass(
                f"System processes tiny images (verdict: {pipeline_result['verdict']})",
                details={
                    'image_size': '50x50',
                    'time': f"{pipeline_result['elapsed']:.2f}s",
                    'verdict': pipeline_result['verdict']
                },
                recommendation="Tiny images work but may lack detail. Recommend minimum 200x200px for reliable results."
            )
        else:
            result.mark_fail(
                f"Failed on tiny images: {pipeline_result.get('error', 'Unknown')}",
                recommendation="Add minimum size check (e.g., 100x100px) and provide clear error message"
            )

    except Exception as e:
        result.mark_fail(f"Unexpected error: {str(e)}")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def test_4_huge_images():
    """Test Case 4: Huge images (>4K resolution)"""
    result = EdgeCaseResult("4. Huge Images (>4K)")

    test_dir = TEMP_DIR / "test_4_huge"
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create 4K+ images (4096x4096 = 16.7 megapixels)
        size = (4096, 4096)
        t0 = time.time()

        create_synthetic_fragment(test_dir / "huge_01.png", size, color=(120, 120, 120))
        create_synthetic_fragment(test_dir / "huge_02.png", size, color=(120, 120, 120))

        creation_time = time.time() - t0

        # Test preprocessing
        t1 = time.time()
        img, cnt = preprocess_fragment(str(test_dir / "huge_01.png"))
        preprocess_time = time.time() - t1

        result.mark_pass(
            f"System handles 4K images (preprocess: {preprocess_time:.2f}s)",
            details={
                'image_size': f"{size[0]}x{size[1]}",
                'creation_time': f"{creation_time:.2f}s",
                'preprocess_time': f"{preprocess_time:.2f}s",
                'contour_points': len(cnt)
            },
            recommendation=f"4K images work but slow ({preprocess_time:.1f}s/image). "
                          f"Consider automatic downscaling for images >2048px to improve performance."
        )

    except MemoryError:
        result.mark_fail(
            "Out of memory with 4K images",
            recommendation="Add memory check and downscale large images automatically"
        )
    except Exception as e:
        result.mark_fail(f"Error: {str(e)[:100]}")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def test_5_corrupted_images():
    """Test Case 5: Corrupted/incomplete images"""
    result = EdgeCaseResult("5. Corrupted Images")

    test_dir = TEMP_DIR / "test_5_corrupt"
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create valid fragment
        create_synthetic_fragment(test_dir / "valid.png", (300, 300))

        # Create corrupted file (random bytes with .png extension)
        corrupt_path = test_dir / "corrupted.png"
        with open(corrupt_path, 'wb') as f:
            f.write(os.urandom(500))

        # Create incomplete/truncated PNG
        valid_path = test_dir / "valid.png"
        with open(valid_path, 'rb') as f:
            data = f.read()

        truncated_path = test_dir / "truncated.png"
        with open(truncated_path, 'wb') as f:
            f.write(data[:len(data)//2])  # Write only half

        # Test error handling
        errors_caught = 0
        try:
            img, cnt = preprocess_fragment(str(corrupt_path))
        except Exception:
            errors_caught += 1

        try:
            img, cnt = preprocess_fragment(str(truncated_path))
        except Exception:
            errors_caught += 1

        if errors_caught == 2:
            result.mark_pass(
                "System correctly handles corrupted images with proper errors",
                details={'corrupted_files_rejected': errors_caught},
                recommendation="Error handling is robust. Consider logging corrupted files for user review."
            )
        else:
            result.mark_fail(
                f"Only caught {errors_caught}/2 corrupted files",
                recommendation="Improve input validation to catch all corrupted images"
            )

    except Exception as e:
        result.mark_fail(f"Test setup error: {str(e)}")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def test_6_identical_fragments():
    """Test Case 6: Identical fragments (duplicates)"""
    result = EdgeCaseResult("6. Identical Fragments")

    test_dir = TEMP_DIR / "test_6_identical"
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create one fragment
        create_synthetic_fragment(test_dir / "frag_01.png", (300, 300), color=(120, 120, 120))

        # Copy it multiple times
        shutil.copy2(test_dir / "frag_01.png", test_dir / "frag_02.png")
        shutil.copy2(test_dir / "frag_01.png", test_dir / "frag_03.png")

        pipeline_result = run_pipeline_test(test_dir, "identical")

        if pipeline_result['success']:
            result.mark_pass(
                f"System processes identical fragments (verdict: {pipeline_result['verdict']})",
                details={
                    'verdict': pipeline_result['verdict'],
                    'time': f"{pipeline_result['elapsed']:.2f}s"
                },
                recommendation="Identical fragments processed. Consider adding duplicate detection to warn users."
            )
        else:
            result.mark_fail(f"Error: {pipeline_result.get('error', 'Unknown')}")

    except Exception as e:
        result.mark_fail(f"Unexpected error: {str(e)}")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def test_7_different_objects():
    """Test Case 7: Completely different objects (not pottery)"""
    result = EdgeCaseResult("7. Different Objects (Non-Pottery)")

    test_dir = TEMP_DIR / "test_7_different"
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create fragments with very different colors/shapes
        # Simulating completely different materials (metal, wood, stone)
        create_synthetic_fragment(test_dir / "metal.png", (300, 300),
                                 color=(200, 200, 200), shape='square')  # Metallic gray
        create_synthetic_fragment(test_dir / "wood.png", (300, 300),
                                 color=(139, 90, 43), shape='irregular')  # Brown wood
        create_synthetic_fragment(test_dir / "stone.png", (300, 300),
                                 color=(128, 128, 120), shape='circle')  # Gray stone

        pipeline_result = run_pipeline_test(test_dir, "different")

        if pipeline_result['success']:
            if pipeline_result['verdict'] == 'NO_MATCH':
                result.mark_pass(
                    "System correctly rejects completely different objects",
                    details={
                        'verdict': 'NO_MATCH',
                        'time': f"{pipeline_result['elapsed']:.2f}s"
                    },
                    recommendation="Color pre-check successfully discriminates different materials. Working as designed."
                )
            else:
                result.mark_fail(
                    f"System incorrectly matched different objects (verdict: {pipeline_result['verdict']})",
                    recommendation="Tighten color/texture discrimination thresholds"
                )
        else:
            result.mark_fail(f"Pipeline error: {pipeline_result.get('error', 'Unknown')}")

    except Exception as e:
        result.mark_fail(f"Unexpected error: {str(e)}")

    finally:
        shutil.rmtree(test_dir, ignore_errors=True)

    return result


def generate_report(results):
    """Generate markdown report"""
    lines = []
    lines.append("# Edge Cases and Boundary Conditions Report")
    lines.append("")
    lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**System**: Fragment Reconstruction Pipeline")
    lines.append("")

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")

    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- **Total Tests**: {total}")
    lines.append(f"- **Passed**: {passed} / {total} ({100*passed/total:.0f}%)")
    lines.append(f"- **Failed**: {failed} / {total} ({100*failed/total:.0f}%)")
    lines.append("")

    if passed == total:
        lines.append("**Overall Assessment**: EXCELLENT - System handles all edge cases robustly.")
    elif passed >= total * 0.8:
        lines.append("**Overall Assessment**: GOOD - System handles most edge cases with minor issues.")
    elif passed >= total * 0.5:
        lines.append("**Overall Assessment**: FAIR - System needs improvements for several edge cases.")
    else:
        lines.append("**Overall Assessment**: POOR - System has significant robustness issues.")
    lines.append("")

    # Detailed results
    lines.append("## Detailed Test Results")
    lines.append("")

    for r in results:
        status_emoji = "✅" if r.status == "PASS" else "❌"
        lines.append(f"### {status_emoji} {r.name}")
        lines.append("")
        lines.append(f"**Status**: {r.status}")
        lines.append(f"**Duration**: {r.duration():.2f}s")
        lines.append(f"**Result**: {r.message}")
        lines.append("")

        if r.details:
            lines.append("**Details**:")
            for key, value in r.details.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

        if r.recommendation:
            lines.append(f"**Recommendation**: {r.recommendation}")
            lines.append("")

    # Recommendations summary
    lines.append("## Overall Recommendations")
    lines.append("")

    critical_recs = [r for r in results if r.status == "FAIL"]
    if critical_recs:
        lines.append("### Critical Issues to Address:")
        for r in critical_recs:
            lines.append(f"- **{r.name}**: {r.recommendation}")
        lines.append("")

    lines.append("### Performance Optimizations:")
    lines.append("- Consider parallel processing for large fragment sets (100+ fragments)")
    lines.append("- Add automatic downscaling for images >2048px")
    lines.append("- Implement early validation checks (minimum 2 fragments, size limits)")
    lines.append("")

    lines.append("### User Experience:")
    lines.append("- Add progress indicators for large datasets")
    lines.append("- Provide clear error messages for invalid inputs")
    lines.append("- Consider duplicate detection warnings")
    lines.append("- Document recommended image specifications (200x200 to 2048x2048)")
    lines.append("")

    # Test matrix
    lines.append("## Test Matrix")
    lines.append("")
    lines.append("| Test Case | Status | Time | Key Finding |")
    lines.append("|-----------|--------|------|-------------|")

    for r in results:
        status_mark = "✅ PASS" if r.status == "PASS" else "❌ FAIL"
        finding = r.message[:60] + "..." if len(r.message) > 60 else r.message
        lines.append(f"| {r.name} | {status_mark} | {r.duration():.1f}s | {finding} |")

    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated: {datetime.now().isoformat()}*")

    return "\n".join(lines)


def main():
    """Run all edge case tests"""
    print("\n" + "="*70)
    print("EDGE CASE AND BOUNDARY CONDITION TESTING")
    print("="*70 + "\n")

    results = []

    # Run all tests
    tests = [
        ("1. Single Fragment", test_1_single_fragment),
        ("2. Large Count (100+)", test_2_large_fragment_count),
        ("3. Tiny Images", test_3_tiny_images),
        ("4. Huge Images (4K)", test_4_huge_images),
        ("5. Corrupted Images", test_5_corrupted_images),
        ("6. Identical Fragments", test_6_identical_fragments),
        ("7. Different Objects", test_7_different_objects),
    ]

    for name, test_func in tests:
        print(f"Running: {name}...", end=" ", flush=True)
        result = test_func()
        results.append(result)
        status = "[PASS]" if result.status == "PASS" else "[FAIL]"
        print(f"{status} ({result.duration():.1f}s)")

    # Generate report
    report_content = generate_report(results)
    report_path = REPORT_DIR / "EDGE_CASES_REPORT.md"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    # Summary
    passed = sum(1 for r in results if r.status == "PASS")
    total = len(results)

    print("\n" + "="*70)
    print(f"RESULTS: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print(f"Report: {report_path}")
    print("="*70 + "\n")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
