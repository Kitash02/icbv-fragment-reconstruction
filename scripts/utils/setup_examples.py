#!/usr/bin/env python3
"""
setup_examples.py
-----------------
One-time script to build the data/examples/ directory tree from raw images.

Creates two kinds of test cases:

  data/examples/positive/<stem>/
      Fragments from a *single* image — the reconstruction pipeline should
      detect a MATCH.  Each folder contains 6–8 fragments, with 1 randomly
      dropped (to simulate a missing piece) and ~30 % of fragments having
      surface erosion damage.

  data/examples/negative/mixed_<A>_<B>/
      Fragments mixed from two *different* images (half from A, half from B).
      The pipeline should return NO_MATCH for these — they test that the system
      correctly rejects unrelated sherds.

Usage
-----
    python setup_examples.py
    python setup_examples.py --raw data/raw --examples data/examples --frags 7 --seed 42

The script is idempotent: re-running it regenerates all examples from scratch
(existing folders are deleted and recreated).

Dependencies: same as generate_benchmark_data.py (opencv-python, numpy)
"""

import argparse
import random
import shutil
import sys
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from generate_benchmark_data import (
    IMAGE_EXTENSIONS,
    process_image,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def collect_raw_images(raw_dir: Path) -> List[Path]:
    """Return sorted list of images in raw_dir, skipping hidden / non-image files."""
    return sorted(
        p for p in raw_dir.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS and not p.name.startswith(".")
    )


def make_clean_dir(path: Path) -> Path:
    """Delete and recreate path so the folder is always fresh."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


# ---------------------------------------------------------------------------
# Positive example generation
# ---------------------------------------------------------------------------

def generate_positive(
    image_path: Path,
    examples_positive_dir: Path,
    n_frags: int,
    displacement: float,
    drop_frags: int,
    damage_prob: float,
    max_size: int,
    seed: int,
) -> Path:
    """
    Fragment one source image and save the result in data/examples/positive/<stem>/.

    Returns the created output directory.
    """
    out_dir = make_clean_dir(examples_positive_dir / image_path.stem)

    random.seed(seed)
    np.random.seed(seed)

    meta = process_image(
        image_path=image_path,
        output_dir=out_dir,
        min_frags=n_frags,
        max_frags=n_frags,
        displacement_scale=displacement,
        fixed_n=n_frags,
        drop_frags=drop_frags,
        damage_prob=damage_prob,
        max_size=max_size,
        rng_seed=seed,
    )

    n_saved   = meta["n_fragments_saved"]
    n_dropped = meta["n_fragments_dropped"]
    n_damaged = sum(1 for f in meta["fragments"] if f.get("surface_damaged"))
    print(
        f"    [positive] {image_path.stem:<40}  "
        f"{n_saved} frags saved, {n_dropped} dropped, {n_damaged} damaged"
    )
    return out_dir


# ---------------------------------------------------------------------------
# Negative example generation
# ---------------------------------------------------------------------------

def generate_negative(
    img_a: Path,
    img_b: Path,
    examples_negative_dir: Path,
    n_frags: int,
    displacement: float,
    max_size: int,
    seed: int,
) -> Path:
    """
    Create a mixed folder from two unrelated images.

    Generates n_frags fragments from each image, then copies approximately
    half from img_a and half from img_b into a single folder.  Because the
    fragments come from different sources they should not match.

    Returns the created output directory.
    """
    label = f"mixed_{img_a.stem[:20]}_{img_b.stem[:20]}"
    out_dir = make_clean_dir(examples_negative_dir / label)

    # Temporary directories for intermediate fragments
    tmp_a = out_dir / "_tmp_a"
    tmp_b = out_dir / "_tmp_b"
    tmp_a.mkdir()
    tmp_b.mkdir()

    random.seed(seed)
    np.random.seed(seed)

    meta_a = process_image(
        image_path=img_a,
        output_dir=tmp_a,
        min_frags=n_frags,
        max_frags=n_frags,
        displacement_scale=displacement,
        fixed_n=n_frags,
        drop_frags=0,
        damage_prob=0.0,
        max_size=max_size,
        rng_seed=seed,
    )

    random.seed(seed + 1)
    np.random.seed(seed + 1)

    meta_b = process_image(
        image_path=img_b,
        output_dir=tmp_b,
        min_frags=n_frags,
        max_frags=n_frags,
        displacement_scale=displacement,
        fixed_n=n_frags,
        drop_frags=0,
        damage_prob=0.0,
        max_size=max_size,
        rng_seed=seed + 1,
    )

    frags_a = [f["filename"] for f in meta_a["fragments"]]
    frags_b = [f["filename"] for f in meta_b["fragments"]]

    # Take roughly half from each source (at least 1 from each)
    half = max(1, n_frags // 2)
    chosen_a = frags_a[:half]
    chosen_b = frags_b[:half]

    # Copy and rename into the mixed output folder
    counter = 0
    for fname in chosen_a:
        src = tmp_a / fname
        dst = out_dir / f"A_{counter:02d}_{fname}"
        shutil.copy2(src, dst)
        counter += 1

    for fname in chosen_b:
        src = tmp_b / fname
        dst = out_dir / f"B_{counter:02d}_{fname}"
        shutil.copy2(src, dst)
        counter += 1

    # Clean up temp dirs
    shutil.rmtree(tmp_a)
    shutil.rmtree(tmp_b)

    print(
        f"    [negative] {label:<50}  "
        f"{len(chosen_a)} from '{img_a.stem}' + {len(chosen_b)} from '{img_b.stem}'"
    )
    return out_dir


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate data/examples/ tree from raw images",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--raw",      default="data/raw",      help="Folder with raw source images")
    p.add_argument("--examples", default="data/examples", help="Root output folder for examples")
    p.add_argument("--frags",    type=int, default=7,     help="Fragments per image")
    p.add_argument("--drop",     type=int, default=1,     help="Fragments to drop per positive case")
    p.add_argument("--damage",   type=float, default=0.3, help="Erosion damage probability per fragment")
    p.add_argument("--max-size", type=int, default=1024,  help="Max pixels on longest side")
    p.add_argument("--displacement", type=float, default=12.0, help="Fracture jaggedness scale")
    p.add_argument("--seed",     type=int, default=42,    help="Base random seed")
    return p


def main() -> None:
    args = build_parser().parse_args()

    raw_dir         = Path(args.raw)
    examples_dir    = Path(args.examples)
    positive_dir    = examples_dir / "positive"
    negative_dir    = examples_dir / "negative"

    positive_dir.mkdir(parents=True, exist_ok=True)
    negative_dir.mkdir(parents=True, exist_ok=True)

    images = collect_raw_images(raw_dir)
    if not images:
        print(f"[ERROR] No images found in '{raw_dir}'. Aborting.")
        sys.exit(1)

    print(f"\n{'='*68}")
    print(f"  SETUP EXAMPLES")
    print(f"{'='*68}")
    print(f"  Raw images    : {len(images)} found in '{raw_dir}'")
    print(f"  Fragments     : {args.frags} per image  (drop {args.drop}, damage {args.damage:.0%})")
    print(f"  Max size      : {args.max_size} px")
    print(f"  Displacement  : {args.displacement}")
    print(f"  Output root   : {examples_dir}")
    print(f"{'='*68}\n")

    t_total = time.time()

    # ── Positive examples ─────────────────────────────────────────────────
    print("Generating POSITIVE examples (same-image fragments):")
    for idx, img_path in enumerate(images):
        t0 = time.time()
        generate_positive(
            image_path=img_path,
            examples_positive_dir=positive_dir,
            n_frags=args.frags,
            displacement=args.displacement,
            drop_frags=args.drop,
            damage_prob=args.damage,
            max_size=args.max_size,
            seed=args.seed + idx * 1000,
        )
        print(f"      → {time.time() - t0:.1f}s")

    # ── Negative examples ─────────────────────────────────────────────────
    print("\nGenerating NEGATIVE examples (mixed fragments from different images):")
    n_neg = 0
    for i in range(len(images)):
        for j in range(i + 1, len(images)):
            t0 = time.time()
            generate_negative(
                img_a=images[i],
                img_b=images[j],
                examples_negative_dir=negative_dir,
                n_frags=args.frags,
                displacement=args.displacement,
                max_size=args.max_size,
                seed=args.seed + 9000 + n_neg * 100,
            )
            print(f"      → {time.time() - t0:.1f}s")
            n_neg += 1

    print(f"\n{'='*68}")
    print(f"  Done in {time.time() - t_total:.1f}s")
    print(f"  Positive cases : {len(images)}  →  {positive_dir}")
    print(f"  Negative cases : {n_neg}  →  {negative_dir}")
    print(f"{'='*68}\n")


if __name__ == "__main__":
    main()
