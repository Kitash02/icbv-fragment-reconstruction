#!/usr/bin/env python3
"""
run_test.py
-----------
End-to-end benchmark on the data/examples/ test suite.

For each example folder the pipeline is run and the result is compared against
the expected outcome:

  data/examples/positive/*   →  expect MATCH or WEAK_MATCH  (PASS if so)
  data/examples/negative/*   →  expect NO_MATCH             (PASS if so)

At the end a single summary table is printed showing every test case with its
verdict, confidence, timing, and PASS / FAIL status.

Usage
-----
    python run_test.py
    python run_test.py --examples data/examples --n-frags 3 --seed 42
    python run_test.py --no-rotate        # skip rotation (faster, easier)
    python run_test.py --positive-only    # run only the positive (matching) cases
"""

import argparse
import io
import logging
import math
import random
import shutil
import sys
import time
from contextlib import redirect_stdout
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

import main as pipeline_main

# ---------------------------------------------------------------------------
# Fragment rotation utility
# ---------------------------------------------------------------------------

def rotate_rgba_fragment(rgba: np.ndarray, angle_deg: float) -> np.ndarray:
    """
    Rotate an RGBA fragment image by angle_deg (counter-clockwise).

    The canvas is expanded so no content is clipped; transparent borders are
    added where needed.  This tests rotation invariance of the pipeline.
    """
    h, w = rgba.shape[:2]
    cx, cy = w / 2.0, h / 2.0
    theta = math.radians(angle_deg)
    cos_a, sin_a = abs(math.cos(theta)), abs(math.sin(theta))
    new_w = int(w * cos_a + h * sin_a) + 2
    new_h = int(w * sin_a + h * cos_a) + 2

    rot_mat = cv2.getRotationMatrix2D((cx, cy), angle_deg, 1.0)
    rot_mat[0, 2] += (new_w - w) / 2
    rot_mat[1, 2] += (new_h - h) / 2

    return cv2.warpAffine(
        rgba, rot_mat, (new_w, new_h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )


# ---------------------------------------------------------------------------
# Per-folder pipeline runner
# ---------------------------------------------------------------------------

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".jfif", ".webp"}


def run_one_folder(
    folder: Path,
    results_dir: Path,
    log_dir: Path,
    rotate: bool,
    rng: random.Random,
) -> dict:
    """
    Run the reconstruction pipeline on all fragment images in *folder*.

    Returns a result dict suitable for the summary table.
    """
    frag_files = sorted(
        p for p in folder.iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS and not p.name.startswith(".")
    )

    if len(frag_files) < 2:
        return {
            "folder": folder.name,
            "n_fragments": len(frag_files),
            "verdict": "ERROR",
            "reason": f"Only {len(frag_files)} fragment(s) in folder",
            "t_total": 0.0,
        }

    # ── Optionally rotate fragments into a temp working copy ──────────────
    work_dir = results_dir / ("_work_" + folder.name)
    work_dir.mkdir(parents=True, exist_ok=True)
    angles = []

    for src_path in frag_files:
        if rotate:
            angle = rng.uniform(0, 360)
            angles.append(round(angle, 1))
            rgba = cv2.imread(str(src_path), cv2.IMREAD_UNCHANGED)
            if rgba is not None and rgba.shape[2] == 4:
                rotated = rotate_rgba_fragment(rgba, angle)
                cv2.imwrite(str(work_dir / src_path.name), rotated)
            else:
                shutil.copy2(src_path, work_dir / src_path.name)
        else:
            shutil.copy2(src_path, work_dir / src_path.name)

    out_dir = results_dir / folder.name
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Run pipeline ──────────────────────────────────────────────────────
    t0 = time.time()
    captured = io.StringIO()
    logging.disable(logging.WARNING)

    try:
        args_ns = argparse.Namespace(
            input=str(work_dir),
            output=str(out_dir),
            log=str(log_dir),
        )
        with redirect_stdout(captured):
            pipeline_main.run_pipeline(args_ns)
    except Exception as exc:
        logging.disable(logging.NOTSET)
        shutil.rmtree(work_dir, ignore_errors=True)
        return {
            "folder": folder.name,
            "n_fragments": len(frag_files),
            "verdict": "ERROR",
            "reason": str(exc),
            "t_total": round(time.time() - t0, 2),
        }
    finally:
        logging.disable(logging.NOTSET)

    t_pipeline = round(time.time() - t0, 2)

    # ── Parse verdict from captured stdout ────────────────────────────────
    output_text = captured.getvalue()
    verdict = "UNKNOWN"
    best_confidence = 0.0
    n_match_pairs = 0

    for line in output_text.splitlines():
        if "[RESULT]" in line and verdict == "UNKNOWN":
            if "NO MATCH" in line:
                # Covers both NO_MATCH (geometric) and NO_MATCH_COLOR (pre-check)
                verdict = "NO_MATCH"
            elif "MATCH FOUND" in line:
                v_part = [p for p in line.split() if p.startswith("verdict=")]
                verdict = v_part[0].split("=")[1] if v_part else "MATCH"
                tokens = line.split()
                if "pairs:" in tokens:
                    pidx = tokens.index("pairs:") + 1
                    if pidx < len(tokens):
                        try:
                            n_match_pairs = int(tokens[pidx])
                        except ValueError:
                            pass
        if "Assembly #1" in line and "confidence=" in line and best_confidence == 0.0:
            conf_part = [p for p in line.split() if p.startswith("confidence=")]
            if conf_part:
                try:
                    best_confidence = float(conf_part[0].split("=")[1])
                except ValueError:
                    pass

    # ── Clean up working copy ─────────────────────────────────────────────
    shutil.rmtree(work_dir, ignore_errors=True)

    return {
        "folder": folder.name,
        "n_fragments": len(frag_files),
        "angles": angles,
        "verdict": verdict,
        "best_confidence": best_confidence,
        "n_match_pairs": n_match_pairs,
        "t_pipeline": t_pipeline,
        "t_total": t_pipeline,
    }


# ---------------------------------------------------------------------------
# Summary table printer
# ---------------------------------------------------------------------------

def _verdict_icon(verdict: str) -> str:
    return {"MATCH": "+", "WEAK_MATCH": "~", "NO_MATCH": "-", "ERROR": "!", "UNKNOWN": "?"}.get(verdict, "?")


def _pass_fail(verdict: str, expected: str) -> str:
    """Return PASS / FAIL based on verdict vs. expected outcome."""
    if expected == "MATCH":
        return "PASS" if verdict in ("MATCH", "WEAK_MATCH") else "FAIL"
    if expected == "NO_MATCH":
        return "PASS" if verdict == "NO_MATCH" else "FAIL"
    return "????"


def print_summary_table(results: list, rotate_label: str) -> None:
    """Print a formatted results table with PASS/FAIL for every test case."""
    col_folder = 42
    col_type   =  8
    col_frags  =  5
    col_verdict= 11
    col_conf   =  6
    col_time   =  7
    col_pass   =  5

    sep = "-"
    hdr_fmt = (
        f"  {{:<{col_folder}}}  {{:^{col_type}}}  {{:^{col_frags}}}  "
        f"{{:^{col_verdict}}}  {{:>{col_conf}}}  {{:>{col_time}}}  {{:^{col_pass}}}"
    )
    row_fmt = hdr_fmt  # same widths

    total_width = col_folder + col_type + col_frags + col_verdict + col_conf + col_time + col_pass + 16

    print()
    print("=" * total_width)
    print(f"  RECONSTRUCTION TEST RESULTS  ({rotate_label})")
    print("=" * total_width)
    print(hdr_fmt.format("Test Case", "Type", "Frags", "Verdict", "Conf", "Time(s)", "Pass?"))
    print("  " + sep * (total_width - 2))

    n_pass = n_fail = n_err = 0
    last_type = None

    for r in results:
        case_type    = r["case_type"]
        expected     = r["expected"]
        verdict      = r["verdict"]
        icon         = _verdict_icon(verdict)
        pass_label   = _pass_fail(verdict, expected)
        conf_str     = f"{r.get('best_confidence', 0):.2f}" if verdict not in ("ERROR", "UNKNOWN") else "—"
        time_str     = f"{r['t_total']:.1f}"
        display_name = r["folder"][:col_folder]

        # Blank separator row between positive and negative sections
        if last_type is not None and case_type != last_type:
            print("  " + sep * (total_width - 2))
        last_type = case_type

        pf_marker = "PASS" if pass_label == "PASS" else "FAIL"
        if verdict == "ERROR":
            pf_marker = "ERR"
            n_err += 1
        elif pass_label == "PASS":
            n_pass += 1
        else:
            n_fail += 1

        print(row_fmt.format(
            display_name,
            case_type,
            r["n_fragments"],
            f"{icon} {verdict}",
            conf_str,
            time_str,
            pf_marker,
        ))

        if verdict == "ERROR" and r.get("reason"):
            print(f"    {'':>{col_folder}}  ERROR: {r['reason'][:60]}")

    total = len(results)
    print("  " + sep * (total_width - 2))
    print(row_fmt.format(
        f"TOTAL  {n_pass}/{total} pass  {n_fail} fail  {n_err} error",
        "", "", "", "", "", "",
    ))
    print("=" * total_width)
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run reconstruction pipeline on all data/examples/ test cases",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--examples",      default="data/examples",
                   help="Root folder containing positive/ and negative/ subdirs")
    p.add_argument("--results",       default="outputs/test_results",
                   help="Output folder for reconstruction images")
    p.add_argument("--logs",          default="outputs/test_logs",
                   help="Log folder")
    p.add_argument("--rotate",        action="store_true", default=True,
                   help="Apply random rotation to each fragment before reconstruction")
    p.add_argument("--no-rotate",     dest="rotate", action="store_false",
                   help="Skip rotation (faster; tests without rotation invariance)")
    p.add_argument("--positive-only", action="store_true", default=False,
                   help="Run only the positive (same-image) test cases")
    p.add_argument("--negative-only", action="store_true", default=False,
                   help="Run only the negative (mixed-image) test cases")
    p.add_argument("--seed",          type=int, default=42)
    return p


def main() -> None:
    args = build_parser().parse_args()
    rng = random.Random(args.seed)
    np.random.seed(args.seed)

    examples_dir = Path(args.examples)
    positive_dir = examples_dir / "positive"
    negative_dir = examples_dir / "negative"
    results_dir  = Path(args.results)
    log_dir      = Path(args.logs)

    for d in (results_dir, log_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Collect test folders
    all_cases = []

    if not args.negative_only and positive_dir.exists():
        for folder in sorted(positive_dir.iterdir()):
            if folder.is_dir():
                all_cases.append({"folder": folder, "case_type": "positive", "expected": "MATCH"})

    if not args.positive_only and negative_dir.exists():
        for folder in sorted(negative_dir.iterdir()):
            if folder.is_dir():
                all_cases.append({"folder": folder, "case_type": "negative", "expected": "NO_MATCH"})

    if not all_cases:
        print(f"[ERROR] No test folders found in '{examples_dir}'.")
        print("        Run  python setup_examples.py  first to generate the test suite.")
        sys.exit(1)

    rot_label = "WITH rotation" if args.rotate else "NO rotation"
    print(f"\n{'='*68}")
    print(f"  RUNNING {len(all_cases)} TEST CASES  ({rot_label})")
    print(f"{'='*68}")
    n_pos = sum(1 for c in all_cases if c["case_type"] == "positive")
    n_neg = sum(1 for c in all_cases if c["case_type"] == "negative")
    print(f"  Positive (expect MATCH)    : {n_pos}")
    print(f"  Negative (expect NO_MATCH) : {n_neg}")
    print(f"{'='*68}\n")

    results = []
    for case in all_cases:
        folder    = case["folder"]
        case_type = case["case_type"]
        expected  = case["expected"]
        label     = f"[{case_type[0].upper()}] {folder.name[:48]}"
        print(f"  > {label:<54}", end="", flush=True)

        res = run_one_folder(
            folder=folder,
            results_dir=results_dir,
            log_dir=log_dir,
            rotate=args.rotate,
            rng=rng,
        )
        res["case_type"] = case_type
        res["expected"]  = expected

        icon = _verdict_icon(res["verdict"])
        pf   = _pass_fail(res["verdict"], expected)
        pf_marker = "PASS" if pf == "PASS" else "FAIL"
        if res["verdict"] == "ERROR":
            pf_marker = "! ERROR"
        print(f"  {icon} {res['verdict']:<10}  {res['t_total']:.1f}s  {pf_marker}")

        results.append(res)

    print_summary_table(results, rot_label)

    n_pass = sum(1 for r in results if _pass_fail(r["verdict"], r["expected"]) == "PASS")
    n_total = len(results)
    final_verdict = "ALL PASS" if n_pass == n_total else f"{n_pass}/{n_total} PASS"
    print(f"  Final result : {final_verdict}")
    print(f"  Results saved to: {results_dir.resolve()}\n")


if __name__ == "__main__":
    main()
