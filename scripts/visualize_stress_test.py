#!/usr/bin/env python3
"""
Quick visualization of preprocessing stress test results.
Generates summary charts for the preprocessing robustness report.
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load the report data
report_path = Path(__file__).parent.parent / "outputs" / "testing" / "preprocessing_robustness.md"

# Parse the JSON data from the report
with open(report_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract JSON section
json_start = content.find('```json\n[')
json_end = content.find('\n```', json_start)
json_str = content[json_start+8:json_end]

data = json.loads(json_str)

# Separate successful and failed
successful = [d for d in data if d['success']]
failed = [d for d in data if not d['success']]

print(f"Loaded {len(data)} test results: {len(successful)} successful, {len(failed)} failed")

# Create visualization
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Preprocessing Pipeline Stress Test Results', fontsize=16, fontweight='bold')

# 1. Success rate by category
ax = axes[0, 0]
categories = {}
for d in data:
    cat = d['category']
    if cat not in categories:
        categories[cat] = {'total': 0, 'success': 0}
    categories[cat]['total'] += 1
    if d['success']:
        categories[cat]['success'] += 1

cat_names = list(categories.keys())
success_counts = [categories[c]['success'] for c in cat_names]
fail_counts = [categories[c]['total'] - categories[c]['success'] for c in cat_names]

x = np.arange(len(cat_names))
width = 0.35

ax.bar(x, success_counts, width, label='Success', color='#2ecc71')
ax.bar(x, fail_counts, width, bottom=success_counts, label='Failed', color='#e74c3c')
ax.set_ylabel('Fragment Count')
ax.set_title('Success Rate by Category')
ax.set_xticks(x)
ax.set_xticklabels([c.replace('_', '\n') for c in cat_names], fontsize=9)
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Add percentage labels
for i, cat in enumerate(cat_names):
    total = categories[cat]['total']
    success = categories[cat]['success']
    pct = (success / total * 100) if total > 0 else 0
    ax.text(i, total + 0.5, f'{pct:.0f}%', ha='center', fontsize=10, fontweight='bold')

# 2. Method distribution
ax = axes[0, 1]
methods = {}
for d in successful:
    method = d['processing']['method_used']
    methods[method] = methods.get(method, 0) + 1

if methods:
    colors = {'otsu': '#3498db', 'canny': '#e67e22', 'alpha': '#9b59b6', 'adaptive': '#1abc9c'}
    method_colors = [colors.get(m, '#95a5a6') for m in methods.keys()]

    wedges, texts, autotexts = ax.pie(
        methods.values(),
        labels=[f'{m}\n({c})' for m, c in methods.items()],
        autopct='%1.1f%%',
        colors=method_colors,
        startangle=90
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    ax.set_title('Edge Detection Method Usage')

# 3. Processing time distribution
ax = axes[0, 2]
times = [d['processing']['time_ms'] for d in successful]
ax.hist(times, bins=20, color='#3498db', edgecolor='black', alpha=0.7)
ax.axvline(np.mean(times), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(times):.1f}ms')
ax.axvline(np.median(times), color='green', linestyle='--', linewidth=2, label=f'Median: {np.median(times):.1f}ms')
ax.set_xlabel('Processing Time (ms)')
ax.set_ylabel('Frequency')
ax.set_title('Processing Time Distribution')
ax.legend()
ax.grid(axis='y', alpha=0.3)

# 4. Contour points distribution
ax = axes[1, 0]
points = [d['contour_metrics']['points'] for d in successful]
ax.hist(points, bins=20, color='#2ecc71', edgecolor='black', alpha=0.7)
ax.axvline(np.mean(points), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(points):.0f}')
ax.set_xlabel('Contour Points')
ax.set_ylabel('Frequency')
ax.set_title('Contour Complexity Distribution')
ax.legend()
ax.grid(axis='y', alpha=0.3)

# 5. Area coverage distribution
ax = axes[1, 1]
area_ratios = [d['contour_metrics']['area_ratio'] * 100 for d in successful]
ax.hist(area_ratios, bins=20, color='#e67e22', edgecolor='black', alpha=0.7)
ax.axvline(np.mean(area_ratios), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(area_ratios):.1f}%')
ax.set_xlabel('Area Coverage (%)')
ax.set_ylabel('Frequency')
ax.set_title('Fragment Area Coverage')
ax.legend()
ax.grid(axis='y', alpha=0.3)

# 6. Resolution vs processing time
ax = axes[1, 2]
resolutions = [d['image_properties']['resolution_mp'] for d in successful]
times = [d['processing']['time_ms'] for d in successful]
scatter = ax.scatter(resolutions, times, c=times, cmap='viridis', s=100, alpha=0.6, edgecolors='black')
ax.set_xlabel('Resolution (MP)')
ax.set_ylabel('Processing Time (ms)')
ax.set_title('Performance Scalability')
ax.grid(alpha=0.3)
plt.colorbar(scatter, ax=ax, label='Time (ms)')

# Add trendline
if len(resolutions) > 1:
    z = np.polyfit(resolutions, times, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(resolutions), max(resolutions), 100)
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f'Trend: {z[0]:.1f}ms/MP')
    ax.legend()

plt.tight_layout()
plt.savefig(Path(__file__).parent.parent / "outputs" / "testing" / "preprocessing_stress_test_summary.png", dpi=300, bbox_inches='tight')
print("\nVisualization saved to: outputs/testing/preprocessing_stress_test_summary.png")

# Print summary statistics
print("\n" + "="*80)
print("PREPROCESSING STRESS TEST - SUMMARY STATISTICS")
print("="*80)
print(f"\nTotal Fragments:     {len(data)}")
print(f"Successful:          {len(successful)} ({len(successful)/len(data)*100:.1f}%)")
print(f"Failed:              {len(failed)} ({len(failed)/len(data)*100:.1f}%)")
print(f"\nProcessing Time:")
print(f"  Mean:              {np.mean(times):.2f}ms")
print(f"  Median:            {np.median(times):.2f}ms")
print(f"  Min:               {min(times):.2f}ms")
print(f"  Max:               {max(times):.2f}ms")
print(f"\nContour Quality:")
print(f"  Avg Points:        {np.mean(points):.0f}")
print(f"  Avg Coverage:      {np.mean(area_ratios):.1f}%")
print(f"\nMethod Distribution:")
for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
    pct = count / len(successful) * 100
    print(f"  {method:12s}     {count:2d} fragments ({pct:.1f}%)")
print("\n" + "="*80)
