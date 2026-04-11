"""
Analyze Track 3 (Ensemble Voting) Integration Results

Compares:
- Track 2 only (Hard Discriminators)
- Track 2 + Track 3 (Hard Discriminators + Ensemble Voting)

Outputs detailed analysis to TRACK3_INTEGRATION_RESULTS.md
"""

import re
from pathlib import Path


def parse_test_results(file_path):
    """Parse test results file and extract pass/fail status for each test."""
    results = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all test results
    pattern = r'Test case: (.+?)\s+\[RESULT\]\s+(\w+)'
    matches = re.findall(pattern, content, re.MULTILINE)

    for test_name, result in matches:
        test_name = test_name.strip()
        results[test_name] = result.strip()

    return results


def categorize_tests(results):
    """Categorize tests into positive and negative."""
    positive = {}
    negative = {}

    for test_name, result in results.items():
        if test_name.startswith('mixed_'):
            negative[test_name] = result
        else:
            positive[test_name] = result

    return positive, negative


def compute_stats(results):
    """Compute accuracy statistics."""
    total = len(results)
    passed = sum(1 for r in results.values() if r == 'PASS')
    failed = sum(1 for r in results.values() if r == 'FAIL')

    accuracy = (passed / total * 100) if total > 0 else 0

    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'accuracy': accuracy
    }


def compare_results(track2_results, track3_results):
    """Compare two result sets and identify changes."""
    improved = []
    degraded = []
    unchanged_pass = []
    unchanged_fail = []

    all_tests = set(track2_results.keys()) | set(track3_results.keys())

    for test in sorted(all_tests):
        track2_status = track2_results.get(test, 'MISSING')
        track3_status = track3_results.get(test, 'MISSING')

        if track2_status == 'FAIL' and track3_status == 'PASS':
            improved.append(test)
        elif track2_status == 'PASS' and track3_status == 'FAIL':
            degraded.append(test)
        elif track2_status == 'PASS' and track3_status == 'PASS':
            unchanged_pass.append(test)
        elif track2_status == 'FAIL' and track3_status == 'FAIL':
            unchanged_fail.append(test)

    return {
        'improved': improved,
        'degraded': degraded,
        'unchanged_pass': unchanged_pass,
        'unchanged_fail': unchanged_fail
    }


def generate_report():
    """Generate comprehensive comparison report."""

    # Load results
    track2_path = Path('outputs/track2_integrated.txt')
    track3_path = Path('outputs/track3_integrated.txt')

    if not track2_path.exists():
        print(f"ERROR: {track2_path} not found")
        return

    if not track3_path.exists():
        print(f"ERROR: {track3_path} not found")
        return

    print("Parsing Track 2 results...")
    track2_all = parse_test_results(track2_path)
    track2_pos, track2_neg = categorize_tests(track2_all)

    print("Parsing Track 3 results...")
    track3_all = parse_test_results(track3_path)
    track3_pos, track3_neg = categorize_tests(track3_all)

    # Compute statistics
    track2_stats = {
        'overall': compute_stats(track2_all),
        'positive': compute_stats(track2_pos),
        'negative': compute_stats(track2_neg)
    }

    track3_stats = {
        'overall': compute_stats(track3_all),
        'positive': compute_stats(track3_pos),
        'negative': compute_stats(track3_neg)
    }

    # Compare results
    overall_comparison = compare_results(track2_all, track3_all)
    pos_comparison = compare_results(track2_pos, track3_pos)
    neg_comparison = compare_results(track2_neg, track3_neg)

    # Generate markdown report
    report = []
    report.append("# TRACK 3 (ENSEMBLE VOTING) INTEGRATION RESULTS\n")
    report.append("## Executive Summary\n")

    # Determine verdict
    overall_delta = track3_stats['overall']['accuracy'] - track2_stats['overall']['accuracy']
    pos_delta = track3_stats['positive']['accuracy'] - track2_stats['positive']['accuracy']
    neg_delta = track3_stats['negative']['accuracy'] - track2_stats['negative']['accuracy']

    if overall_delta > 2.0:
        verdict = "**SUCCESSFUL**"
        status = "✅ SUCCESS"
    elif overall_delta > 0:
        verdict = "**MARGINAL IMPROVEMENT**"
        status = "⚠️ MARGINAL"
    elif overall_delta > -2.0:
        verdict = "**NEUTRAL**"
        status = "⚠️ NEUTRAL"
    else:
        verdict = "**DEGRADED**"
        status = "❌ DEGRADED"

    report.append(f"Track 3 integration is {verdict}. ")

    if overall_delta > 0:
        report.append(f"Ensemble voting improved accuracy by {overall_delta:.1f} percentage points ")
        report.append(f"({track2_stats['overall']['accuracy']:.1f}% → {track3_stats['overall']['accuracy']:.1f}%).\n\n")
    elif overall_delta < 0:
        report.append(f"Ensemble voting decreased accuracy by {abs(overall_delta):.1f} percentage points ")
        report.append(f"({track2_stats['overall']['accuracy']:.1f}% → {track3_stats['overall']['accuracy']:.1f}%).\n\n")
    else:
        report.append(f"Ensemble voting did not change overall accuracy ({track3_stats['overall']['accuracy']:.1f}%).\n\n")

    report.append("---\n\n")
    report.append("## Performance Comparison\n\n")
    report.append("### Track 2 Only (Hard Discriminators)\n")
    report.append("```\n")
    report.append(f"Overall Accuracy: {track2_stats['overall']['passed']}/{track2_stats['overall']['total']} ({track2_stats['overall']['accuracy']:.0f}%)\n")
    report.append(f"├─ Positive Tests: {track2_stats['positive']['passed']}/{track2_stats['positive']['total']} ({track2_stats['positive']['accuracy']:.0f}%)\n")
    report.append(f"└─ Negative Tests: {track2_stats['negative']['passed']}/{track2_stats['negative']['total']} ({track2_stats['negative']['accuracy']:.0f}%)\n")
    report.append("```\n\n")

    report.append("### Track 2+3 (Hard Discriminators + Ensemble Voting)\n")
    report.append("```\n")
    report.append(f"Overall Accuracy: {track3_stats['overall']['passed']}/{track3_stats['overall']['total']} ({track3_stats['overall']['accuracy']:.0f}%)\n")
    report.append(f"├─ Positive Tests: {track3_stats['positive']['passed']}/{track3_stats['positive']['total']} ({track3_stats['positive']['accuracy']:.0f}%)\n")
    report.append(f"└─ Negative Tests: {track3_stats['negative']['passed']}/{track3_stats['negative']['total']} ({track3_stats['negative']['accuracy']:.0f}%)\n")
    report.append("```\n\n")

    report.append("---\n\n")
    report.append("## Changes Summary\n\n")
    report.append("| Metric | Track 2 | Track 2+3 | Change |\n")
    report.append("|--------|---------|-----------|--------|\n")
    report.append(f"| **Overall Accuracy** | {track2_stats['overall']['accuracy']:.0f}% | {track3_stats['overall']['accuracy']:.0f}% | {overall_delta:+.1f} points |\n")
    report.append(f"| **Positive Accuracy** | {track2_stats['positive']['accuracy']:.0f}% | {track3_stats['positive']['accuracy']:.0f}% | {pos_delta:+.1f} points |\n")
    report.append(f"| **Negative Accuracy** | {track2_stats['negative']['accuracy']:.0f}% | {track3_stats['negative']['accuracy']:.0f}% | {neg_delta:+.1f} points |\n")
    report.append(f"| **Tests Passing** | {track2_stats['overall']['passed']} | {track3_stats['overall']['passed']} | {track3_stats['overall']['passed'] - track2_stats['overall']['passed']:+d} |\n")
    report.append("\n---\n\n")

    # Test changes detail
    if overall_comparison['improved']:
        report.append(f"## Improved Tests ({len(overall_comparison['improved'])} tests)\n\n")
        report.append("Track 3 fixed these tests that Track 2 failed:\n\n")
        for test in overall_comparison['improved']:
            report.append(f"- `{test}`\n")
        report.append("\n")

    if overall_comparison['degraded']:
        report.append(f"## Degraded Tests ({len(overall_comparison['degraded'])} tests)\n\n")
        report.append("Track 3 broke these tests that Track 2 passed:\n\n")
        for test in overall_comparison['degraded']:
            report.append(f"- `{test}`\n")
        report.append("\n")

    report.append("---\n\n")
    report.append("## Detailed Analysis\n\n")

    # Positive test analysis
    report.append("### Positive Tests (Same-Source Fragments)\n\n")
    report.append(f"- **Track 2**: {track2_stats['positive']['passed']}/{track2_stats['positive']['total']} pass ({track2_stats['positive']['accuracy']:.0f}%)\n")
    report.append(f"- **Track 2+3**: {track3_stats['positive']['passed']}/{track3_stats['positive']['total']} pass ({track3_stats['positive']['accuracy']:.0f}%)\n")
    report.append(f"- **Change**: {pos_delta:+.1f} percentage points\n\n")

    if pos_comparison['improved']:
        report.append(f"**Recovered by Track 3** ({len(pos_comparison['improved'])} tests):\n")
        for test in pos_comparison['improved']:
            report.append(f"- `{test}`\n")
        report.append("\n")

    if pos_comparison['degraded']:
        report.append(f"**Broken by Track 3** ({len(pos_comparison['degraded'])} tests):\n")
        for test in pos_comparison['degraded']:
            report.append(f"- `{test}`\n")
        report.append("\n")

    # Negative test analysis
    report.append("### Negative Tests (Cross-Source Fragments)\n\n")
    report.append(f"- **Track 2**: {track2_stats['negative']['passed']}/{track2_stats['negative']['total']} pass ({track2_stats['negative']['accuracy']:.0f}%)\n")
    report.append(f"- **Track 2+3**: {track3_stats['negative']['passed']}/{track3_stats['negative']['total']} pass ({track3_stats['negative']['accuracy']:.0f}%)\n")
    report.append(f"- **Change**: {neg_delta:+.1f} percentage points\n\n")

    if neg_comparison['improved']:
        report.append(f"**Fixed by Track 3** ({len(neg_comparison['improved'])} tests):\n")
        for test in neg_comparison['improved']:
            report.append(f"- `{test}`\n")
        report.append("\n")

    if neg_comparison['degraded']:
        report.append(f"**Broken by Track 3** ({len(neg_comparison['degraded'])} tests):\n")
        for test in neg_comparison['degraded']:
            report.append(f"- `{test}`\n")
        report.append("\n")

    report.append("---\n\n")
    report.append("## Recommendation\n\n")

    if overall_delta > 2.0:
        report.append("**DEPLOY TRACK 3**: Ensemble voting provides significant improvement. ")
        report.append("The additional computational cost is justified by the accuracy gain.\n\n")
    elif overall_delta > 0:
        report.append("**CONSIDER TRACK 3**: Ensemble voting provides marginal improvement. ")
        report.append("Deploy if computational cost is acceptable, otherwise Track 2 alone is sufficient.\n\n")
    elif overall_delta == 0:
        report.append("**SKIP TRACK 3**: Ensemble voting provides no benefit over Track 2 alone. ")
        report.append("Stick with Track 2 to avoid unnecessary complexity.\n\n")
    else:
        report.append("**REJECT TRACK 3**: Ensemble voting degrades performance. ")
        report.append("Stick with Track 2 only.\n\n")

    report.append("---\n\n")
    report.append("## Implementation Details\n\n")
    report.append("### Track 3 Integration\n\n")
    report.append("**File**: `src/ensemble_postprocess.py` (new)\n\n")
    report.append("**Function**: `reclassify_borderline_cases(assemblies, compat_matrix, appearance_mats, images)`\n\n")
    report.append("**Strategy**: Post-processing filter (Option B - low risk)\n\n")
    report.append("**What it does**:\n")
    report.append("1. Run AFTER relaxation labeling produces assemblies\n")
    report.append("2. Re-classify WEAK_MATCH pairs using 5-way voting ensemble\n")
    report.append("3. Leave MATCH and NO_MATCH verdicts unchanged (high confidence)\n")
    report.append("4. Only modify borderline cases where voting can help\n\n")
    report.append("**Ensemble Voters**:\n")
    report.append("1. Raw Compatibility (geometric features)\n")
    report.append("2. Color Discriminator (Lab histogram BC)\n")
    report.append("3. Texture Discriminator (LBP histogram BC)\n")
    report.append("4. Gabor Discriminator (frequency-domain texture)\n")
    report.append("5. Morphological Discriminator (edge density + entropy)\n\n")
    report.append("**Voting Rule**:\n")
    report.append("- MATCH: Requires 3+ MATCH votes (60% confidence)\n")
    report.append("- NO_MATCH: Requires 2+ NO_MATCH votes (40% rejection)\n")
    report.append("- WEAK_MATCH: Otherwise\n\n")
    report.append("---\n\n")
    report.append("## Files Modified\n\n")
    report.append("- `src/ensemble_postprocess.py` - New file with post-processing logic\n")
    report.append("- `src/main.py` - Added ensemble post-processing call\n")
    report.append("- `src/compatibility.py` - Modified to return appearance matrices\n")
    report.append("- `outputs/track3_integrated.txt` - Test results with Track 2+3\n")
    report.append("- `TRACK3_INTEGRATION_RESULTS.md` - This report\n\n")
    report.append("---\n\n")
    report.append(f"**Report Generated**: 2026-04-08\n")
    report.append(f"**Integration Status**: {status}\n")

    # Write report
    output_path = Path('TRACK3_INTEGRATION_RESULTS.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(report))

    print(f"\nReport written to: {output_path}")
    print(f"\nSummary:")
    print(f"  Track 2 Only:  {track2_stats['overall']['accuracy']:.1f}% overall ({track2_stats['positive']['accuracy']:.0f}% pos, {track2_stats['negative']['accuracy']:.0f}% neg)")
    print(f"  Track 2+3:     {track3_stats['overall']['accuracy']:.1f}% overall ({track3_stats['positive']['accuracy']:.0f}% pos, {track3_stats['negative']['accuracy']:.0f}% neg)")
    print(f"  Change:        {overall_delta:+.1f} points")
    print(f"  Status:        {status}")


if __name__ == '__main__':
    generate_report()
