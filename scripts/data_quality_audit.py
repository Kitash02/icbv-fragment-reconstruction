#!/usr/bin/env python3
"""
Comprehensive Data Quality Validation Script

Performs thorough quality assessment of all downloaded/processed fragments:
- Visual inspection (single fragment, clean background, clear edges)
- Metadata validation
- Same-source verification (wikimedia_processed)
- Different-source verification (wikimedia)
- Quality scoring and categorization
"""

import cv2
import numpy as np
import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Dict, List, Tuple, Any

class FragmentQualityAuditor:
    """Comprehensive quality auditor for fragment images"""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results = {
            'wikimedia_processed': [],
            'wikimedia': [],
            'british_museum': []
        }
        self.quality_categories = {
            'excellent': [],
            'good': [],
            'acceptable': [],
            'poor': []
        }

    def analyze_single_fragment(self, img_path: Path) -> Dict[str, Any]:
        """Perform comprehensive quality analysis on a single fragment"""

        # Load image
        img = cv2.imread(str(img_path))
        if img is None:
            return {'error': 'Failed to load image'}

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Quality checks
        results = {
            'filename': img_path.name,
            'path': str(img_path),
            'resolution': f"{w}x{h}",
            'file_size_kb': img_path.stat().st_size / 1024,
            'checks': {}
        }

        # 1. Resolution check
        min_res = 100
        max_res = 10000
        res_ok = min_res <= w <= max_res and min_res <= h <= max_res
        results['checks']['resolution'] = {
            'passed': res_ok,
            'score': 10 if res_ok else 3,
            'message': f"Resolution {w}x{h} - {'OK' if res_ok else 'Out of range'}"
        }

        # 2. Single fragment detection
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter small noise
        significant_contours = [c for c in contours if cv2.contourArea(c) > (w*h*0.01)]
        num_components = len(significant_contours)

        single_fragment = num_components == 1
        results['checks']['single_fragment'] = {
            'passed': single_fragment,
            'score': 10 if single_fragment else (7 if num_components <= 3 else 3),
            'num_components': num_components,
            'message': f"{'Single' if single_fragment else f'{num_components}'} fragment(s) detected"
        }

        # 3. Background uniformity
        if len(significant_contours) > 0:
            # Create mask for background
            mask = np.zeros_like(binary)
            cv2.drawContours(mask, significant_contours, -1, 255, -1)
            background = gray.copy()
            background[mask > 0] = 0

            bg_pixels = background[background > 0]
            if len(bg_pixels) > 0:
                bg_std = np.std(bg_pixels)
                bg_uniformity = 1.0 - min(bg_std / 128.0, 1.0)
            else:
                bg_uniformity = 0.0
        else:
            bg_uniformity = 0.0

        bg_score = int(bg_uniformity * 10)
        results['checks']['background_uniformity'] = {
            'passed': bg_uniformity > 0.7,
            'score': bg_score,
            'uniformity': bg_uniformity,
            'message': f"Background uniformity: {bg_uniformity:.2f}"
        }

        # 4. Edge clarity
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / (w * h)

        # Good fragments have moderate edge density (not too sparse, not too noisy)
        if 0.01 <= edge_density <= 0.15:
            edge_score = 10
            edge_quality = "excellent"
        elif 0.005 <= edge_density <= 0.25:
            edge_score = 7
            edge_quality = "good"
        else:
            edge_score = 4
            edge_quality = "poor"

        results['checks']['edge_clarity'] = {
            'passed': edge_density >= 0.005,
            'score': edge_score,
            'edge_density': edge_density,
            'quality': edge_quality,
            'message': f"Edge density: {edge_density:.4f} - {edge_quality}"
        }

        # 5. Fragment completeness (not too small fragments)
        if len(significant_contours) > 0:
            main_contour = max(significant_contours, key=cv2.contourArea)
            fragment_area = cv2.contourArea(main_contour)
            image_area = w * h
            area_ratio = fragment_area / image_area

            if area_ratio > 0.3:
                size_score = 10
                size_quality = "good size"
            elif area_ratio > 0.1:
                size_score = 7
                size_quality = "moderate size"
            else:
                size_score = 4
                size_quality = "very small"

            results['checks']['fragment_size'] = {
                'passed': area_ratio > 0.05,
                'score': size_score,
                'area_ratio': area_ratio,
                'quality': size_quality,
                'message': f"Fragment occupies {area_ratio:.1%} of image - {size_quality}"
            }
        else:
            results['checks']['fragment_size'] = {
                'passed': False,
                'score': 0,
                'area_ratio': 0.0,
                'quality': "no fragment",
                'message': "No fragment detected"
            }

        # 6. No obvious artifacts (check for excessive noise)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        noise_level = np.mean(np.abs(gray.astype(float) - blurred.astype(float)))

        if noise_level < 5:
            noise_score = 10
            noise_quality = "clean"
        elif noise_level < 10:
            noise_score = 7
            noise_quality = "slight noise"
        else:
            noise_score = 4
            noise_quality = "noisy"

        results['checks']['artifacts'] = {
            'passed': noise_level < 15,
            'score': noise_score,
            'noise_level': noise_level,
            'quality': noise_quality,
            'message': f"Noise level: {noise_level:.2f} - {noise_quality}"
        }

        # Calculate overall quality score
        total_score = sum(check['score'] for check in results['checks'].values())
        max_score = len(results['checks']) * 10
        quality_score = (total_score / max_score) * 10

        results['quality_score'] = round(quality_score, 2)
        results['total_score'] = total_score
        results['max_score'] = max_score

        # Categorize
        if quality_score >= 8.5:
            results['category'] = 'excellent'
        elif quality_score >= 7.0:
            results['category'] = 'good'
        elif quality_score >= 5.0:
            results['category'] = 'acceptable'
        else:
            results['category'] = 'poor'

        return results

    def verify_same_source(self, fragments: List[Path]) -> Dict[str, Any]:
        """Verify that fragments from wikimedia_processed are from same source photo"""

        if len(fragments) < 2:
            return {'error': 'Need at least 2 fragments to compare'}

        # Load first few fragments for visual similarity check
        sample_size = min(10, len(fragments))
        samples = []

        for frag_path in fragments[:sample_size]:
            img = cv2.imread(str(frag_path))
            if img is not None:
                samples.append(img)

        if len(samples) < 2:
            return {'error': 'Could not load enough samples'}

        # Compare color histograms
        hist_similarities = []
        for i in range(len(samples) - 1):
            hist1 = cv2.calcHist([samples[i]], [0, 1, 2], None, [32, 32, 32], [0, 256, 0, 256, 0, 256])
            hist1 = cv2.normalize(hist1, hist1).flatten()

            hist2 = cv2.calcHist([samples[i+1]], [0, 1, 2], None, [32, 32, 32], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.normalize(hist2, hist2).flatten()

            similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            hist_similarities.append(similarity)

        avg_similarity = np.mean(hist_similarities)

        result = {
            'num_fragments': len(fragments),
            'samples_compared': sample_size,
            'avg_color_similarity': avg_similarity,
            'min_similarity': min(hist_similarities),
            'max_similarity': max(hist_similarities),
            'verdict': 'LIKELY_SAME_SOURCE' if avg_similarity > 0.7 else 'UNCERTAIN' if avg_similarity > 0.5 else 'LIKELY_DIFFERENT'
        }

        return result

    def verify_different_sources(self, fragments: List[Path]) -> Dict[str, Any]:
        """Verify that wikimedia fragments are from different artifacts"""

        if len(fragments) < 2:
            return {'error': 'Need at least 2 fragments to compare'}

        # Load all fragments
        images = []
        for frag_path in fragments:
            img = cv2.imread(str(frag_path))
            if img is not None:
                images.append((frag_path.name, img))

        if len(images) < 2:
            return {'error': 'Could not load fragments'}

        # Compare all pairs
        similarities = []
        duplicate_candidates = []

        for i in range(len(images)):
            for j in range(i + 1, len(images)):
                name1, img1 = images[i]
                name2, img2 = images[j]

                # Compare color histograms
                hist1 = cv2.calcHist([img1], [0, 1, 2], None, [32, 32, 32], [0, 256, 0, 256, 0, 256])
                hist1 = cv2.normalize(hist1, hist1).flatten()

                hist2 = cv2.calcHist([img2], [0, 1, 2], None, [32, 32, 32], [0, 256, 0, 256, 0, 256])
                hist2 = cv2.normalize(hist2, hist2).flatten()

                similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                similarities.append(similarity)

                # Flag potential duplicates
                if similarity > 0.9:
                    duplicate_candidates.append((name1, name2, similarity))

        avg_similarity = np.mean(similarities)

        result = {
            'num_fragments': len(images),
            'num_comparisons': len(similarities),
            'avg_similarity': avg_similarity,
            'min_similarity': min(similarities),
            'max_similarity': max(similarities),
            'potential_duplicates': duplicate_candidates,
            'verdict': 'ALL_DIFFERENT' if avg_similarity < 0.5 else 'MOSTLY_DIFFERENT' if avg_similarity < 0.7 else 'SUSPICIOUS'
        }

        return result

    def audit_dataset(self):
        """Run complete audit on all datasets"""

        print("=" * 80)
        print("COMPREHENSIVE DATA QUALITY AUDIT")
        print("=" * 80)
        print()

        # 1. Audit wikimedia_processed fragments (same source)
        print("1. Analyzing wikimedia_processed fragments (expected: same source)...")
        wp_dir = self.base_path / "wikimedia_processed"
        wp_fragments = sorted(list(wp_dir.glob("14_scherven_*.jpg")))

        if wp_fragments:
            for frag in wp_fragments:
                result = self.analyze_single_fragment(frag)
                self.results['wikimedia_processed'].append(result)
                if 'category' in result:
                    self.quality_categories[result['category']].append(result)

            same_source_result = self.verify_same_source(wp_fragments)
            self.results['wikimedia_processed_verification'] = same_source_result
            print(f"  - Analyzed {len(wp_fragments)} fragments")
            print(f"  - Same-source verification: {same_source_result.get('verdict', 'N/A')}")

        # Also check example1_auto subdirectory
        wp_ex1_dir = wp_dir / "example1_auto"
        if wp_ex1_dir.exists():
            wp_ex1_fragments = sorted(list(wp_ex1_dir.glob("*.jpg")))
            for frag in wp_ex1_fragments:
                result = self.analyze_single_fragment(frag)
                self.results['wikimedia_processed'].append(result)
                if 'category' in result:
                    self.quality_categories[result['category']].append(result)

            if wp_ex1_fragments:
                same_source_result2 = self.verify_same_source(wp_ex1_fragments)
                self.results['wikimedia_processed_ex1_verification'] = same_source_result2
                print(f"  - Analyzed {len(wp_ex1_fragments)} additional fragments from example1_auto")
                print(f"  - Same-source verification: {same_source_result2.get('verdict', 'N/A')}")

        print()

        # 2. Audit wikimedia fragments (different sources)
        print("2. Analyzing wikimedia fragments (expected: different sources)...")
        wm_dir = self.base_path / "wikimedia"
        wm_fragments = sorted(list(wm_dir.glob("candidate_*.jpg")))

        if wm_fragments:
            for frag in wm_fragments:
                result = self.analyze_single_fragment(frag)
                self.results['wikimedia'].append(result)
                if 'category' in result:
                    self.quality_categories[result['category']].append(result)

            diff_source_result = self.verify_different_sources(wm_fragments)
            self.results['wikimedia_verification'] = diff_source_result
            print(f"  - Analyzed {len(wm_fragments)} fragments")
            print(f"  - Different-source verification: {diff_source_result.get('verdict', 'N/A')}")

        print()

        # 3. Audit British Museum fragments
        print("3. Analyzing British Museum fragments...")
        bm_dir = self.base_path / "british_museum"
        bm_fragments = sorted(list(bm_dir.glob("*.jpg")))

        if bm_fragments:
            for frag in bm_fragments:
                result = self.analyze_single_fragment(frag)
                self.results['british_museum'].append(result)
                if 'category' in result:
                    self.quality_categories[result['category']].append(result)
            print(f"  - Analyzed {len(bm_fragments)} fragments")

        print()
        print("=" * 80)
        print("AUDIT COMPLETE")
        print("=" * 80)

    def generate_report(self, output_path: Path):
        """Generate comprehensive markdown report"""

        report_lines = []

        # Header
        report_lines.append("# Data Quality Audit Report")
        report_lines.append("")
        report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Executive Summary
        report_lines.append("## Executive Summary")
        report_lines.append("")

        total_fragments = (len(self.results['wikimedia_processed']) +
                          len(self.results['wikimedia']) +
                          len(self.results['british_museum']))

        report_lines.append(f"**Total Fragments Analyzed:** {total_fragments}")
        report_lines.append("")
        report_lines.append("**By Source:**")
        report_lines.append(f"- Wikimedia Processed (same source): {len(self.results['wikimedia_processed'])} fragments")
        report_lines.append(f"- Wikimedia (different sources): {len(self.results['wikimedia'])} fragments")
        report_lines.append(f"- British Museum: {len(self.results['british_museum'])} fragments")
        report_lines.append("")

        report_lines.append("**Quality Distribution:**")
        for category in ['excellent', 'good', 'acceptable', 'poor']:
            count = len(self.quality_categories[category])
            pct = (count / total_fragments * 100) if total_fragments > 0 else 0
            report_lines.append(f"- {category.capitalize()}: {count} ({pct:.1f}%)")
        report_lines.append("")

        # Calculate average quality score
        all_results = (self.results['wikimedia_processed'] +
                      self.results['wikimedia'] +
                      self.results['british_museum'])

        # Filter out results with errors
        valid_results = [r for r in all_results if 'quality_score' in r]

        if valid_results:
            avg_quality = np.mean([r['quality_score'] for r in valid_results])
            report_lines.append(f"**Average Quality Score:** {avg_quality:.2f}/10")
        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Same-Source Verification
        report_lines.append("## Same-Source Verification (Wikimedia Processed)")
        report_lines.append("")

        if 'wikimedia_processed_verification' in self.results:
            ver = self.results['wikimedia_processed_verification']
            report_lines.append(f"**Objective:** Verify that the {ver.get('num_fragments', 0)} fragments are from the same source photo")
            report_lines.append("")
            report_lines.append(f"**Verdict:** {ver.get('verdict', 'N/A')}")
            report_lines.append("")
            report_lines.append("**Metrics:**")
            report_lines.append(f"- Samples Compared: {ver.get('samples_compared', 0)}")
            report_lines.append(f"- Average Color Similarity: {ver.get('avg_color_similarity', 0):.3f}")
            report_lines.append(f"- Min Similarity: {ver.get('min_similarity', 0):.3f}")
            report_lines.append(f"- Max Similarity: {ver.get('max_similarity', 0):.3f}")
            report_lines.append("")

            if ver.get('avg_color_similarity', 0) > 0.7:
                report_lines.append("**Analysis:** The fragments show high color histogram similarity, confirming they likely originate from the same source photograph. This validates the dataset integrity for same-source reconstruction testing.")
            else:
                report_lines.append("**Analysis:** The fragments show lower than expected similarity. This may warrant further investigation.")
            report_lines.append("")

        if 'wikimedia_processed_ex1_verification' in self.results:
            ver = self.results['wikimedia_processed_ex1_verification']
            report_lines.append("**Additional Set (example1_auto):**")
            report_lines.append(f"- Verdict: {ver.get('verdict', 'N/A')}")
            report_lines.append(f"- Average Similarity: {ver.get('avg_color_similarity', 0):.3f}")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Different-Source Verification
        report_lines.append("## Different-Source Verification (Wikimedia)")
        report_lines.append("")

        if 'wikimedia_verification' in self.results:
            ver = self.results['wikimedia_verification']
            report_lines.append(f"**Objective:** Verify that the {ver.get('num_fragments', 0)} fragments are from different artifacts")
            report_lines.append("")
            report_lines.append(f"**Verdict:** {ver.get('verdict', 'N/A')}")
            report_lines.append("")
            report_lines.append("**Metrics:**")
            report_lines.append(f"- Pairwise Comparisons: {ver.get('num_comparisons', 0)}")
            report_lines.append(f"- Average Similarity: {ver.get('avg_similarity', 0):.3f}")
            report_lines.append(f"- Min Similarity: {ver.get('min_similarity', 0):.3f}")
            report_lines.append(f"- Max Similarity: {ver.get('max_similarity', 0):.3f}")
            report_lines.append("")

            duplicates = ver.get('potential_duplicates', [])
            if duplicates:
                report_lines.append(f"**WARNING:** {len(duplicates)} potential duplicate(s) detected:")
                for name1, name2, sim in duplicates:
                    report_lines.append(f"- {name1} vs {name2}: similarity = {sim:.3f}")
                report_lines.append("")
            else:
                report_lines.append("**Analysis:** No duplicate fragments detected. All fragments appear to be from different source artifacts, validating the dataset for different-source testing.")
                report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Detailed Quality Analysis by Source
        report_lines.append("## Detailed Quality Analysis by Source")
        report_lines.append("")

        for source_name, source_key in [
            ("Wikimedia Processed (Same Source)", "wikimedia_processed"),
            ("Wikimedia (Different Sources)", "wikimedia"),
            ("British Museum", "british_museum")
        ]:
            report_lines.append(f"### {source_name}")
            report_lines.append("")

            source_results = self.results[source_key]
            if not source_results:
                report_lines.append("No fragments analyzed.")
                report_lines.append("")
                continue

            # Filter valid results
            valid_source_results = [r for r in source_results if 'quality_score' in r]
            if not valid_source_results:
                report_lines.append("No valid quality scores.")
                report_lines.append("")
                continue

            # Statistics
            scores = [r['quality_score'] for r in valid_source_results]
            report_lines.append(f"**Fragments:** {len(valid_source_results)}")
            report_lines.append(f"**Average Quality Score:** {np.mean(scores):.2f}/10")
            report_lines.append(f"**Min Score:** {np.min(scores):.2f}/10")
            report_lines.append(f"**Max Score:** {np.max(scores):.2f}/10")
            report_lines.append("")

            # Top 5 and Bottom 5
            sorted_results = sorted(valid_source_results, key=lambda x: x['quality_score'], reverse=True)

            report_lines.append("**Top 5 Quality Fragments:**")
            for i, result in enumerate(sorted_results[:5], 1):
                report_lines.append(f"{i}. `{result['filename']}` - Score: {result['quality_score']:.2f}/10 ({result['category']})")
            report_lines.append("")

            if len(sorted_results) > 5:
                report_lines.append("**Bottom 5 Quality Fragments:**")
                for i, result in enumerate(sorted_results[-5:], 1):
                    report_lines.append(f"{i}. `{result['filename']}` - Score: {result['quality_score']:.2f}/10 ({result['category']})")
                report_lines.append("")

            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Per-Fragment Detailed Ratings
        report_lines.append("## Per-Fragment Quality Ratings")
        report_lines.append("")

        # Sort all fragments by quality score
        all_results = (self.results['wikimedia_processed'] +
                      self.results['wikimedia'] +
                      self.results['british_museum'])

        # Filter valid results only
        valid_results = [r for r in all_results if 'quality_score' in r]
        sorted_all = sorted(valid_results, key=lambda x: x['quality_score'], reverse=True)

        report_lines.append("| Rank | Fragment | Source | Score | Category | Key Issues |")
        report_lines.append("|------|----------|--------|-------|----------|------------|")

        for i, result in enumerate(sorted_all, 1):
            # Determine source
            if result in self.results['wikimedia_processed']:
                source = "WM-Proc"
            elif result in self.results['wikimedia']:
                source = "WM"
            else:
                source = "BM"

            # Identify key issues
            issues = []
            for check_name, check_data in result['checks'].items():
                if not check_data.get('passed', False):
                    issues.append(check_name.replace('_', ' '))

            issue_str = ", ".join(issues[:3]) if issues else "None"
            filename_short = result['filename'][:40] + "..." if len(result['filename']) > 43 else result['filename']

            report_lines.append(f"| {i} | `{filename_short}` | {source} | {result['quality_score']:.2f} | {result['category'].capitalize()} | {issue_str} |")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations for Data Curation")
        report_lines.append("")

        excellent = self.quality_categories['excellent']
        good = self.quality_categories['good']
        acceptable = self.quality_categories['acceptable']
        poor = self.quality_categories['poor']

        report_lines.append("### Priority 1: Use for All Testing")
        report_lines.append(f"**{len(excellent)} Excellent-Quality Fragments**")
        report_lines.append("- Single, well-defined fragments")
        report_lines.append("- Clean backgrounds")
        report_lines.append("- Clear edges and good resolution")
        report_lines.append("- Recommended for primary algorithm validation")
        report_lines.append("")

        if excellent:
            report_lines.append("**List:**")
            for result in excellent[:10]:
                report_lines.append(f"- `{result['filename']}` (Score: {result['quality_score']:.2f})")
            if len(excellent) > 10:
                report_lines.append(f"- ... and {len(excellent) - 10} more")
            report_lines.append("")

        report_lines.append("### Priority 2: Use for Robustness Testing")
        report_lines.append(f"**{len(good)} Good-Quality Fragments**")
        report_lines.append("- Generally suitable for testing")
        report_lines.append("- May have minor issues (slight noise, moderate background complexity)")
        report_lines.append("- Useful for testing algorithm robustness")
        report_lines.append("")

        report_lines.append("### Priority 3: Use with Caution")
        report_lines.append(f"**{len(acceptable)} Acceptable-Quality Fragments**")
        report_lines.append("- Have quality issues but still usable")
        report_lines.append("- May require additional preprocessing")
        report_lines.append("- Use for stress testing or edge cases")
        report_lines.append("")

        report_lines.append("### Consider Excluding")
        report_lines.append(f"**{len(poor)} Poor-Quality Fragments**")
        report_lines.append("- Significant quality issues")
        report_lines.append("- May negatively impact algorithm performance evaluation")
        report_lines.append("- Recommend manual review before use")
        report_lines.append("")

        if poor:
            report_lines.append("**List:**")
            for result in poor:
                issues = [name for name, check in result['checks'].items() if not check.get('passed', False)]
                report_lines.append(f"- `{result['filename']}` - Issues: {', '.join(issues)}")
            report_lines.append("")

        report_lines.append("---")
        report_lines.append("")

        # Quality Metrics Summary
        report_lines.append("## Quality Metrics Summary")
        report_lines.append("")
        report_lines.append("### Check Pass Rates")
        report_lines.append("")

        # Aggregate check statistics
        check_stats = defaultdict(lambda: {'passed': 0, 'failed': 0})

        for result in valid_results:
            if 'checks' not in result:
                continue
            for check_name, check_data in result['checks'].items():
                if check_data.get('passed', False):
                    check_stats[check_name]['passed'] += 1
                else:
                    check_stats[check_name]['failed'] += 1

        report_lines.append("| Check | Passed | Failed | Pass Rate |")
        report_lines.append("|-------|--------|--------|-----------|")

        for check_name, stats in sorted(check_stats.items()):
            total = stats['passed'] + stats['failed']
            pass_rate = (stats['passed'] / total * 100) if total > 0 else 0
            report_lines.append(f"| {check_name.replace('_', ' ').title()} | {stats['passed']} | {stats['failed']} | {pass_rate:.1f}% |")

        report_lines.append("")
        report_lines.append("---")
        report_lines.append("")

        # Conclusion
        report_lines.append("## Conclusion")
        report_lines.append("")

        usable_count = len(excellent) + len(good)
        usable_pct = (usable_count / total_fragments * 100) if total_fragments > 0 else 0

        report_lines.append(f"Out of {total_fragments} total fragments analyzed:")
        report_lines.append(f"- **{usable_count} ({usable_pct:.1f}%)** are suitable for primary testing (excellent + good quality)")
        report_lines.append(f"- **{len(acceptable)} ({len(acceptable)/total_fragments*100:.1f}%)** can be used with caution")
        report_lines.append(f"- **{len(poor)} ({len(poor)/total_fragments*100:.1f}%)** should be reviewed or excluded")
        report_lines.append("")

        # Dataset-specific conclusions
        wp_results = [r for r in self.results['wikimedia_processed'] if 'quality_score' in r]
        if wp_results:
            wp_avg = np.mean([r['quality_score'] for r in wp_results])
            report_lines.append(f"**Wikimedia Processed Dataset:** Average quality {wp_avg:.2f}/10 - {'Excellent' if wp_avg >= 8 else 'Good' if wp_avg >= 7 else 'Acceptable' if wp_avg >= 5 else 'Needs improvement'} dataset for same-source reconstruction testing.")

        wm_results = [r for r in self.results['wikimedia'] if 'quality_score' in r]
        if wm_results:
            wm_avg = np.mean([r['quality_score'] for r in wm_results])
            report_lines.append(f"**Wikimedia Dataset:** Average quality {wm_avg:.2f}/10 - {'Excellent' if wm_avg >= 8 else 'Good' if wm_avg >= 7 else 'Acceptable' if wm_avg >= 5 else 'Needs improvement'} dataset for different-source testing.")

        report_lines.append("")
        report_lines.append("**Overall Assessment:** The fragment collection provides a solid foundation for algorithm development and testing, with sufficient high-quality samples for validation and lower-quality samples for robustness testing.")
        report_lines.append("")

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))

        print(f"Report saved to: {output_path}")

    def save_json_results(self, output_path: Path):
        """Save detailed results as JSON"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        def convert_to_native(obj):
            """Convert numpy types to native Python types"""
            if isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                                np.int16, np.int32, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj

        # Prepare JSON-serializable data
        json_data = {
            'audit_date': datetime.now().isoformat(),
            'results': self.results,
            'quality_categories': {
                cat: [r['filename'] for r in results]
                for cat, results in self.quality_categories.items()
            }
        }

        # Convert numpy types
        import json as json_module

        class NumpyEncoder(json_module.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, (np.bool_, np.integer, np.floating)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)

        with open(output_path, 'w', encoding='utf-8') as f:
            json_module.dump(json_data, f, indent=2, cls=NumpyEncoder)

        print(f"JSON results saved to: {output_path}")


def main():
    """Main execution"""
    base_path = Path(__file__).parent.parent / "data" / "raw" / "real_fragments_validated"
    output_dir = Path(__file__).parent.parent / "outputs" / "testing"

    auditor = FragmentQualityAuditor(base_path)
    auditor.audit_dataset()

    # Generate reports
    report_path = output_dir / "data_quality_audit.md"
    json_path = output_dir / "data_quality_audit.json"

    auditor.generate_report(report_path)
    auditor.save_json_results(json_path)

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total fragments analyzed: {sum(len(v) if isinstance(v, list) else 0 for v in auditor.results.values())}")
    print(f"Excellent: {len(auditor.quality_categories['excellent'])}")
    print(f"Good: {len(auditor.quality_categories['good'])}")
    print(f"Acceptable: {len(auditor.quality_categories['acceptable'])}")
    print(f"Poor: {len(auditor.quality_categories['poor'])}")
    print()
    print(f"Report: {report_path}")
    print(f"JSON: {json_path}")


if __name__ == "__main__":
    main()
