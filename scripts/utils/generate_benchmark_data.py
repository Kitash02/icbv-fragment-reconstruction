#!/usr/bin/env python3
"""
generate_benchmark_data.py
--------------------------
Synthetic fragment dataset generator for archaeological reconstruction benchmarking.

Splits each source image into N irregular fragments using Voronoi partitioning
combined with multi-octave Gaussian noise displacement. The resulting fracture
lines are highly jagged to simulate physical breaks in fired clay or parchment.

New in this version
-------------------
* --drop-frags K  : randomly omit K fragments from the saved set (simulate lost pieces).
* --damage-prob P : apply erosion-based surface damage to each fragment with probability P
                    (simulates weathering, worn edges, missing surface material).
* --max-size PX   : resize source images to at most PX pixels on the longest side before
                    processing, so large images run in a reasonable time.
* --min-frags / --max-frags defaults raised to 6–8.

Algorithm
---------
1. Optionally resize source image to max-size.
2. Choose N random seed points inside the image.
3. Build a displacement field by summing Gaussian-smoothed random noise at several
   spatial scales (coarse structure + fine grain = Perlin-like appearance).
4. For every pixel (x, y), query the *displaced* coordinate against the seed KD-tree.
   The nearest seed determines the pixel's fragment label.
5. Optionally apply erosion damage to individual fragment masks.
6. Optionally drop K fragments (randomly) to simulate missing pieces.
7. Extract each labeled region as an RGBA PNG cropped to its minimal bounding box.
8. Write a JSON ground-truth file recording each fragment's origin and drop list.

Output layout
-------------
  <output_dir>/<stem>_frag_00.png   RGBA fragment, bounding-box-cropped
  <output_dir>/<stem>_frag_01.png   …
  <output_dir>/<stem>_meta.json     ground truth per fragment (includes dropped IDs)

Usage
-----
  python generate_benchmark_data.py
  python generate_benchmark_data.py --input data/raw --output data/examples/positive/myset
  python generate_benchmark_data.py --min-frags 6 --max-frags 8 --drop-frags 1 --damage-prob 0.4

Dependencies: opencv-python  numpy  (no scipy required)
"""

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".jfif", ".webp"}

# Noise parameters — tuned for fracture-like appearance
NOISE_OCTAVES = 7          # more octaves = richer detail at all scales
NOISE_BASE_SCALE = 0.10    # coarsest scale as a fraction of min(H, W)
NOISE_PERSISTENCE = 0.72   # high persistence: fine octaves keep >70% amplitude

# Fraction of min(H, W) used as displacement amplitude (before user scaling)
BASE_DISPLACEMENT_FRACTION = 0.06

# Micro-crack layer: very-short-range noise added on top of the smooth field.
MICRO_CRACK_SIGMA = 1.8    # pixels — nearly unsmoothed, very high frequency
MICRO_CRACK_WEIGHT = 0.30  # fraction of total displacement dedicated to micro-cracks

# Damage simulation — erosion blobs
DAMAGE_MIN_BLOBS = 3       # minimum erosion spots per damaged fragment
DAMAGE_MAX_BLOBS = 12      # maximum erosion spots per damaged fragment
DAMAGE_RADIUS_FRAC = 0.06  # blob radius as fraction of min(H, W) of the fragment


# ---------------------------------------------------------------------------
# Multi-scale noise generation  (Perlin-like via Gaussian octaves)
# ---------------------------------------------------------------------------

def _single_octave_noise(h: int, w: int, sigma: float) -> np.ndarray:
    """
    One octave of spatially-coherent noise: iid Gaussian → Gaussian filter.

    Uses cv2.GaussianBlur (available without scipy). Kernel size is derived
    from sigma following the OpenCV convention (odd, ≥ 3). Produces values
    with zero mean and unit standard deviation.
    """
    raw = np.random.randn(h, w).astype(np.float32)
    sigma = max(sigma, 0.5)
    k = int(np.ceil(sigma * 6)) | 1   # bitwise OR with 1 ensures odd
    k = max(k, 3)
    smoothed = cv2.GaussianBlur(raw, (k, k), sigmaX=sigma, sigmaY=sigma)
    std = float(smoothed.std())
    return smoothed / std if std > 1e-8 else smoothed


def build_displacement_field(
    h: int,
    w: int,
    displacement_pixels: float,
    seed: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build a 2-D displacement field (dx, dy) for fracture-boundary perturbation.

    The field is a weighted sum of Gaussian-smoothed noise at geometrically
    decreasing spatial scales (coarsest to finest). Each finer octave adds
    high-frequency irregularity that gives the fracture its jagged appearance.

    Returns
    -------
    dx, dy : float32 arrays of shape (h, w), values in [-displacement, +displacement]
    """
    if seed is not None:
        rng_state = np.random.get_state()
        np.random.seed(seed)

    min_dim = min(h, w)
    coarse_sigma = NOISE_BASE_SCALE * min_dim

    dx = np.zeros((h, w), dtype=np.float32)
    dy = np.zeros((h, w), dtype=np.float32)
    total_weight = 0.0
    amplitude = 1.0

    for octave in range(NOISE_OCTAVES):
        sigma = coarse_sigma / (2.0 ** octave)
        if sigma < 0.4:
            break
        dx += amplitude * _single_octave_noise(h, w, sigma)
        dy += amplitude * _single_octave_noise(h, w, sigma)
        total_weight += amplitude
        amplitude *= NOISE_PERSISTENCE

    smooth_scale = displacement_pixels * (1.0 - MICRO_CRACK_WEIGHT)
    dx = (dx / total_weight) * smooth_scale
    dy = (dy / total_weight) * smooth_scale

    micro_amp = displacement_pixels * MICRO_CRACK_WEIGHT
    dx += _single_octave_noise(h, w, MICRO_CRACK_SIGMA) * micro_amp
    dy += _single_octave_noise(h, w, MICRO_CRACK_SIGMA) * micro_amp

    if seed is not None:
        np.random.set_state(rng_state)

    return dx, dy


# ---------------------------------------------------------------------------
# Voronoi fragment labeling with noise displacement
# ---------------------------------------------------------------------------

def label_fragments(
    h: int,
    w: int,
    seeds: np.ndarray,
    displacement_pixels: float,
    noise_seed: Optional[int] = None,
) -> np.ndarray:
    """
    Assign each pixel a fragment label (0 … n_seeds−1) using displaced Voronoi.

    Each pixel's coordinates are perturbed by the displacement field before the
    nearest-seed query, warping Voronoi boundaries into irregular fracture-like curves.

    Parameters
    ----------
    seeds : (N, 2) array of (x, y) seed coordinates inside the image.

    Returns
    -------
    labels : int32 array of shape (h, w)
    """
    dx, dy = build_displacement_field(h, w, displacement_pixels, seed=noise_seed)

    yy, xx = np.mgrid[0:h, 0:w]
    xx_d = np.clip(xx + dx, 0, w - 1).ravel()
    yy_d = np.clip(yy + dy, 0, h - 1).ravel()

    n_px = h * w
    xx_d_f = xx_d.reshape(n_px, 1)
    yy_d_f = yy_d.reshape(n_px, 1)

    sx = seeds[:, 0].reshape(1, -1)
    sy = seeds[:, 1].reshape(1, -1)

    dist2 = (xx_d_f - sx) ** 2 + (yy_d_f - sy) ** 2
    labels_flat = dist2.argmin(axis=1)

    return labels_flat.reshape(h, w).astype(np.int32)


def choose_seeds(
    h: int,
    w: int,
    n_fragments: int,
    margin_frac: float = 0.08,
) -> np.ndarray:
    """
    Sample N seed points inside the image, respecting a small border margin.

    Uses Poisson-disk-like rejection: new seeds must be at least ``min_dist``
    pixels from every existing seed to avoid slivers.
    """
    margin = int(min(h, w) * margin_frac)
    x_lo, x_hi = margin, w - margin
    y_lo, y_hi = margin, h - margin

    min_dist = max(
        int(min(h, w) * 0.15 / max(n_fragments - 1, 1)),
        10,
    )

    seeds: List[Tuple[int, int]] = []
    attempts = 0
    max_attempts = 2000

    while len(seeds) < n_fragments and attempts < max_attempts:
        attempts += 1
        cx = random.randint(x_lo, x_hi)
        cy = random.randint(y_lo, y_hi)
        if all(
            (cx - sx) ** 2 + (cy - sy) ** 2 >= min_dist ** 2
            for sx, sy in seeds
        ):
            seeds.append((cx, cy))

    if len(seeds) < n_fragments:
        # Fallback: uniform grid jitter — guaranteed to fill
        cols = int(np.ceil(np.sqrt(n_fragments)))
        rows = int(np.ceil(n_fragments / cols))
        seeds = []
        for r in range(rows):
            for c in range(cols):
                if len(seeds) >= n_fragments:
                    break
                cx = int(x_lo + (x_hi - x_lo) * (c + 0.5) / cols + random.randint(-10, 10))
                cy = int(y_lo + (y_hi - y_lo) * (r + 0.5) / rows + random.randint(-10, 10))
                seeds.append((np.clip(cx, x_lo, x_hi), np.clip(cy, y_lo, y_hi)))

    return np.array(seeds, dtype=np.float64)


# ---------------------------------------------------------------------------
# Fragment damage simulation (Lecture 22 — erosion as morphological filtering)
# ---------------------------------------------------------------------------

def apply_fragment_damage(mask: np.ndarray, rng: random.Random) -> np.ndarray:
    """
    Simulate surface weathering / erosion damage on a fragment mask.

    Randomly removes elliptical blobs from the fragment's interior and erodes
    the boundary, simulating the worn material seen on archaeological artifacts.
    This directly models how physical degradation removes surface material while
    leaving the overall fragment shape recognizable.

    Parameters
    ----------
    mask : binary uint8 mask (0 or 255) of shape (h, w).
    rng  : seeded random.Random instance for reproducibility.

    Returns
    -------
    damaged_mask : uint8 mask with erosion damage applied.
    """
    h, w = mask.shape
    damaged = mask.copy()
    min_dim = min(h, w)
    n_blobs = rng.randint(DAMAGE_MIN_BLOBS, DAMAGE_MAX_BLOBS)

    # Find the bounding box of the fragment to place blobs inside it
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return damaged

    x_lo, x_hi = int(xs.min()), int(xs.max())
    y_lo, y_hi = int(ys.min()), int(ys.max())

    for _ in range(n_blobs):
        # Place blob centre randomly within the fragment bounding box
        cx = rng.randint(x_lo, x_hi)
        cy = rng.randint(y_lo, y_hi)

        # Only damage if the centre pixel is inside the fragment
        if mask[cy, cx] == 0:
            continue

        # Irregular radius: varies between blobs to break uniformity
        base_r = max(int(min_dim * DAMAGE_RADIUS_FRAC), 4)
        rx = rng.randint(base_r // 2, base_r * 2)
        ry = rng.randint(base_r // 2, base_r * 2)

        # Draw filled ellipse of zeros (eroded area)
        cv2.ellipse(
            damaged,
            (cx, cy),
            (rx, ry),
            angle=rng.uniform(0, 180),
            startAngle=0,
            endAngle=360,
            color=0,
            thickness=-1,
        )

    # Light morphological erosion along fragment boundary for realism
    erode_r = max(2, int(min_dim * 0.01))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erode_r * 2 + 1,) * 2)
    damaged = cv2.erode(damaged, kernel, iterations=1)

    return damaged


# ---------------------------------------------------------------------------
# Fragment extraction and measurement
# ---------------------------------------------------------------------------

def compute_jaggedness(mask: np.ndarray) -> Dict[str, float]:
    """
    Compute edge-roughness metrics for a binary fragment mask.

    jaggedness_ratio : contour perimeter / convex hull perimeter.
        Near 1.0 → smooth convex shape.  > 2.0 → highly irregular.
    isoperimetric   : perimeter / (2 * sqrt(pi * area)).
        A perfect circle has value 1.0; higher = more irregular.
    """
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
    )
    if not contours:
        return {"jaggedness_ratio": 0.0, "isoperimetric": 0.0, "perimeter": 0.0}

    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    perimeter = float(cv2.arcLength(contour, closed=True))

    hull = cv2.convexHull(contour)
    hull_perimeter = float(cv2.arcLength(hull, closed=True))

    jaggedness_ratio = perimeter / hull_perimeter if hull_perimeter > 0 else 1.0
    isoperimetric = perimeter / (2 * np.sqrt(np.pi * area)) if area > 0 else 1.0

    return {
        "jaggedness_ratio": round(jaggedness_ratio, 4),
        "isoperimetric": round(isoperimetric, 4),
        "perimeter": round(perimeter, 1),
        "area_px": int(area),
    }


def extract_fragment(
    img_bgr: np.ndarray,
    mask: np.ndarray,
) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """
    Build an RGBA image for one fragment and return its bounding box.

    Returns
    -------
    rgba_crop : (H', W', 4) uint8 RGBA image, tightly cropped.
    bbox      : (x_min, y_min, x_max, y_max) in original image coordinates.
    """
    bgra = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = mask

    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return bgra, (0, 0, 0, 0)

    x_min, x_max = int(xs.min()), int(xs.max())
    y_min, y_max = int(ys.min()), int(ys.max())
    crop = bgra[y_min:y_max + 1, x_min:x_max + 1].copy()

    return crop, (x_min, y_min, x_max, y_max)


def resize_if_needed(img: np.ndarray, max_size: int) -> np.ndarray:
    """
    Downscale img so its longest side is at most max_size pixels.
    Returns the image unchanged if it already fits.
    """
    h, w = img.shape[:2]
    longest = max(h, w)
    if longest <= max_size:
        return img
    scale = max_size / longest
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


# ---------------------------------------------------------------------------
# Per-image pipeline
# ---------------------------------------------------------------------------

def process_image(
    image_path: Path,
    output_dir: Path,
    min_frags: int,
    max_frags: int,
    displacement_scale: float,
    fixed_n: Optional[int] = None,
    drop_frags: int = 0,
    damage_prob: float = 0.0,
    max_size: int = 1024,
    rng_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fragment one image and write output files.

    Parameters
    ----------
    drop_frags   : how many fragments to randomly omit from the saved set
                   (simulates pieces lost after breakage).
    damage_prob  : probability in [0, 1] that each fragment receives erosion
                   damage (simulates surface weathering).
    max_size     : longest-side cap in pixels before fragmentation.
    rng_seed     : optional seed for the damage/drop RNG (for reproducibility).

    Returns the complete metadata dict that will be saved as JSON.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    img = resize_if_needed(img, max_size)
    h, w = img.shape[:2]

    n_frags = fixed_n if fixed_n is not None else random.randint(min_frags, max_frags)
    noise_seed = random.randint(0, 2 ** 31 - 1)
    damage_rng = random.Random(rng_seed if rng_seed is not None else noise_seed)

    displacement_pixels = BASE_DISPLACEMENT_FRACTION * min(h, w) * (displacement_scale / 10.0)
    seeds = choose_seeds(h, w, n_frags)
    labels = label_fragments(h, w, seeds, displacement_pixels, noise_seed=noise_seed)

    stem = image_path.stem
    all_fragment_records: List[Dict[str, Any]] = []
    skipped = 0

    for frag_idx in range(n_frags):
        mask = ((labels == frag_idx).astype(np.uint8)) * 255
        n_pixels = int((mask > 0).sum())
        total_pixels = h * w

        # Drop slivers: fragment must cover at least 3 % of the image
        if n_pixels < total_pixels * 0.03:
            skipped += 1
            continue

        # Optionally apply surface damage
        damaged = False
        if damage_prob > 0 and damage_rng.random() < damage_prob:
            mask = apply_fragment_damage(mask, damage_rng)
            damaged = True

        rgba_crop, (x_min, y_min, x_max, y_max) = extract_fragment(img, mask)
        jagged = compute_jaggedness(mask)

        all_fragment_records.append({
            "fragment_id": frag_idx,
            "origin": {"x": x_min, "y": y_min},
            "size": {
                "width": x_max - x_min + 1,
                "height": y_max - y_min + 1,
            },
            "pixel_count": n_pixels,
            "coverage_pct": round(100 * n_pixels / total_pixels, 2),
            "edge_metrics": jagged,
            "surface_damaged": damaged,
            "_rgba_crop": rgba_crop,  # temp — removed before JSON serialization
        })

    # ── Randomly drop fragments (simulate missing pieces) ──────────────────
    n_to_drop = min(drop_frags, max(0, len(all_fragment_records) - 2))
    dropped_ids: List[int] = []
    saved_records: List[Dict[str, Any]] = []

    if n_to_drop > 0:
        drop_indices = damage_rng.sample(range(len(all_fragment_records)), n_to_drop)
        dropped_ids = [all_fragment_records[i]["fragment_id"] for i in drop_indices]
    else:
        drop_indices = []

    for idx, rec in enumerate(all_fragment_records):
        rgba_crop = rec.pop("_rgba_crop")   # remove from record before saving
        if idx in drop_indices:
            continue   # omit this fragment from the saved set

        out_name = f"{stem}_frag_{rec['fragment_id']:02d}.png"
        cv2.imwrite(str(output_dir / out_name), rgba_crop)
        rec["filename"] = out_name
        saved_records.append(rec)

    metadata = {
        "source_image": image_path.name,
        "source_size": {"width": w, "height": h},
        "n_fragments_requested": n_frags,
        "n_fragments_saved": len(saved_records),
        "n_fragments_dropped": len(dropped_ids),
        "dropped_fragment_ids": dropped_ids,
        "n_fragments_skipped_sliver": skipped,
        "displacement_pixels": round(displacement_pixels, 1),
        "noise_seed": noise_seed,
        "seeds": seeds.tolist(),
        "fragments": saved_records,
    }

    json_path = output_dir / f"{stem}_meta.json"
    json_path.write_text(json.dumps(metadata, indent=2))

    return metadata


# ---------------------------------------------------------------------------
# Jaggedness verification report
# ---------------------------------------------------------------------------

def print_verification(metadata: Dict[str, Any]) -> None:
    """Print a human-readable summary of fragment edge quality."""
    print()
    print("=" * 70)
    print(f"  Verification report — {metadata['source_image']}")
    print("=" * 70)
    print(f"  Source size      : {metadata['source_size']['width']} × "
          f"{metadata['source_size']['height']} px")
    print(f"  Displacement     : {metadata['displacement_pixels']:.1f} px")
    n_saved   = metadata['n_fragments_saved']
    n_dropped = metadata['n_fragments_dropped']
    n_req     = metadata['n_fragments_requested']
    print(f"  Fragments saved  : {n_saved}  (requested {n_req}, "
          f"dropped {n_dropped}, skipped slivers {metadata['n_fragments_skipped_sliver']})")
    if n_dropped:
        print(f"  Dropped IDs      : {metadata['dropped_fragment_ids']}")
    print()
    header = f"  {'Fragment':<18}  {'Coverage':>8}  {'Perimeter':>10}  {'Jagged':>7}  {'Damaged':>7}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    for frag in metadata["fragments"]:
        em = frag["edge_metrics"]
        jagg = em["jaggedness_ratio"]
        verdict = "✓✓" if jagg >= 1.4 else "✓" if jagg >= 1.1 else "✗"
        dmg = "yes" if frag.get("surface_damaged") else "—"
        name = frag.get("filename", f"frag_{frag['fragment_id']:02d}")
        print(
            f"  {name:<18}  "
            f"{frag['coverage_pct']:>7.1f}%  "
            f"{em['perimeter']:>10.0f}  "
            f"{jagg:>7.3f}  "
            f"{dmg:>7}  {verdict}"
        )

    all_jagged = all(f["edge_metrics"]["jaggedness_ratio"] >= 1.1 for f in metadata["fragments"])
    any_highly = any(f["edge_metrics"]["jaggedness_ratio"] >= 1.4 for f in metadata["fragments"])
    print()
    if all_jagged and any_highly:
        print("  PASS — all fragments jagged; at least one is highly irregular")
    elif all_jagged:
        print("  PASS — all fragments have jaggedness_ratio ≥ 1.1")
    else:
        print("  WARN — some fragments may be too smooth; try --displacement > 10")
    print("=" * 70)
    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synthetic archaeological fragment dataset generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", default="data/raw",
        help="Folder containing source images (PNG / JPG / BMP / TIF / WEBP)",
    )
    parser.add_argument(
        "--output", default="dataset/fragments",
        help="Output folder for RGBA fragment PNGs and JSON metadata",
    )
    parser.add_argument(
        "--min-frags", type=int, default=6,
        help="Minimum number of fragments per image",
    )
    parser.add_argument(
        "--max-frags", type=int, default=8,
        help="Maximum number of fragments per image",
    )
    parser.add_argument(
        "--displacement", type=float, default=10.0,
        help=(
            "Fracture jaggedness scale (1=subtle, 10=moderate, 20=very jagged). "
            "Internally scales to 6%% of min(H,W) × this factor / 10."
        ),
    )
    parser.add_argument(
        "--drop-frags", type=int, default=0,
        help="Number of fragments to randomly omit from the saved set per image "
             "(simulates lost / unrecovered pieces). Minimum 2 fragments always kept.",
    )
    parser.add_argument(
        "--damage-prob", type=float, default=0.0,
        help="Probability in [0,1] that each fragment gets surface erosion damage "
             "applied (simulates weathering). 0 = no damage, 0.4 = 40%% chance per fragment.",
    )
    parser.add_argument(
        "--max-size", type=int, default=1024,
        help="Resize source images so the longest side is at most this many pixels. "
             "Keeps processing time reasonable for large inputs.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Global random seed for reproducibility",
    )
    parser.add_argument(
        "--verify", action="store_true", default=True,
        help="Print edge-quality verification report after each image",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not image_paths:
        print(f"[WARN] No images found in '{input_dir}'.")
        print("       Run with a populated data/raw/ folder or see README.")
        sys.exit(0)

    print(f"Found {len(image_paths)} image(s) in '{input_dir}'.")
    print(f"Output → '{output_dir}'")
    if args.drop_frags:
        print(f"Drop frags: {args.drop_frags} per image (missing pieces simulation)")
    if args.damage_prob > 0:
        print(f"Damage prob: {args.damage_prob:.0%} per fragment (erosion simulation)")
    print()

    total_t = time.time()
    for image_path in image_paths:
        t0 = time.time()
        print(f"  Processing {image_path.name} …", end="", flush=True)
        try:
            metadata = process_image(
                image_path=image_path,
                output_dir=output_dir,
                min_frags=args.min_frags,
                max_frags=args.max_frags,
                displacement_scale=args.displacement,
                drop_frags=args.drop_frags,
                damage_prob=args.damage_prob,
                max_size=args.max_size,
            )
            elapsed = time.time() - t0
            n_saved   = metadata['n_fragments_saved']
            n_dropped = metadata['n_fragments_dropped']
            drop_note = f", {n_dropped} dropped" if n_dropped else ""
            print(f"  {n_saved} fragments saved{drop_note}  ({elapsed:.2f}s)")
            if args.verify:
                print_verification(metadata)
        except Exception as exc:
            print(f"\n  ERROR: {exc}")

    print(f"Done — total time: {time.time() - total_t:.2f}s")
    print(f"Fragments saved to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
