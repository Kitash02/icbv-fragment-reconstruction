"""
Diagnostic script to understand why Lab color space is failing.
Compares HSV vs Lab Bhattacharyya coefficients for same vs different images.
"""

import cv2
import numpy as np
import sys
import os

sys.path.insert(0, 'src')

# Read sample images
data_dir = "data/test_images"
image_files = [
    "gettyimages-1311604917-1024x1024.png",
    "gettyimages-170096524-1024x1024.png",
    "scroll.png"
]

images = []
for fname in image_files:
    path = os.path.join(data_dir, fname)
    if os.path.exists(path):
        img = cv2.imread(path)
        images.append((fname, img))
        print(f"Loaded: {fname} - shape {img.shape}")

if len(images) < 3:
    print("WARNING: Need at least 3 different source images")
    sys.exit(1)

# HSV histogram function
def compute_hsv_signature(image_bgr):
    if image_bgr is None or image_bgr.size == 0:
        return np.zeros(64, dtype=np.float32)

    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 4], [0, 180, 0, 256])
    hist = hist.flatten().astype(np.float32)
    total = hist.sum()
    return hist / total if total > 1e-8 else hist

# Lab histogram function
def compute_lab_signature(image_bgr):
    if image_bgr is None or image_bgr.size == 0:
        return np.zeros(32, dtype=np.float32)

    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2Lab)
    hist_L = cv2.calcHist([lab], [0], None, [16], [0, 256])
    hist_a = cv2.calcHist([lab], [1], None, [8], [0, 256])
    hist_b = cv2.calcHist([lab], [2], None, [8], [0, 256])
    hist = np.concatenate([hist_L.flatten(), hist_a.flatten(), hist_b.flatten()]).astype(np.float32)
    total = hist.sum()
    return hist / total if total > 1e-8 else hist

# Bhattacharyya coefficient
def bhattacharyya(sig_a, sig_b):
    bc = float(np.sum(np.sqrt(np.clip(sig_a, 0, None) * np.clip(sig_b, 0, None))))
    return float(np.clip(bc, 0.0, 1.0))

print("\n" + "="*80)
print("ANALYSIS: HSV vs Lab Bhattacharyya Coefficients")
print("="*80)

# Compute signatures
hsv_sigs = [(name, compute_hsv_signature(img)) for name, img in images]
lab_sigs = [(name, compute_lab_signature(img)) for name, img in images]

print(f"\nHSV signature length: {len(hsv_sigs[0][1])}")
print(f"Lab signature length: {len(lab_sigs[0][1])}")

# Compare all pairs
print("\n" + "-"*80)
print("Cross-image comparisons (should be LOW for good discrimination):")
print("-"*80)

for i in range(len(images)):
    for j in range(i+1, len(images)):
        name_i = hsv_sigs[i][0]
        name_j = hsv_sigs[j][0]

        hsv_bc = bhattacharyya(hsv_sigs[i][1], hsv_sigs[j][1])
        lab_bc = bhattacharyya(lab_sigs[i][1], lab_sigs[j][1])

        print(f"\n{name_i[:30]}")
        print(f"  vs {name_j[:30]}")
        print(f"  HSV BC: {hsv_bc:.4f}")
        print(f"  Lab BC: {lab_bc:.4f}")
        print(f"  Difference: {lab_bc - hsv_bc:+.4f}")

        if lab_bc > hsv_bc:
            print(f"  ⚠ Lab is WORSE (higher similarity)")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("If Lab BC values are consistently HIGHER than HSV BC values,")
print("then Lab is producing LESS discrimination between different images.")
print("This explains why the color penalty isn't working effectively.")
print("="*80)
