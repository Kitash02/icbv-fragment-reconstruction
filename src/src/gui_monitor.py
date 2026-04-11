"""
GUI Monitor - Thread-safe pipeline execution with progress monitoring.

This module provides threading infrastructure for running the archaeological
fragment reconstruction pipeline in a non-blocking manner suitable for GUI
integration. It implements queue-based communication between the worker thread
and the GUI main loop.

Key components:
- PipelineRunner: Thread-based pipeline executor with exception handling
- ProgressCallback: Queue-based progress reporter for real-time updates
- run_pipeline_with_monitoring: Wrapper function integrating progress callbacks

Queue message protocol:
  ("progress", message: str, percent: float|None) - Progress update
  ("complete", results: dict) - Pipeline finished successfully
  ("error", error_message: str) - Pipeline crashed with exception

Usage from GUI:
    import queue
    import gui_monitor

    progress_queue = queue.Queue()
    runner = gui_monitor.PipelineRunner(args, progress_queue)
    runner.start()

    # Poll queue in GUI event loop (e.g., via after())
    try:
        msg_type, *data = progress_queue.get_nowait()
        if msg_type == "progress":
            message, percent = data
            # Update progress bar
        elif msg_type == "complete":
            results = data[0]
            # Display results
        elif msg_type == "error":
            error_msg = data[0]
            # Show error dialog
    except queue.Empty:
        pass

Course mapping: Not tied to specific lectures; provides infrastructure
for accessible GUI interaction with the core algorithms.
"""

import argparse
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable

import numpy as np

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import pipeline components
from preprocessing import preprocess_fragment
from chain_code import encode_fragment, contour_to_pixel_segments
from compatibility import (
    build_compatibility_matrix,
    compute_color_signature,
    color_bhattacharyya,
)
from relaxation import (
    run_relaxation,
    extract_top_assemblies,
    MATCH_SCORE_THRESHOLD,
    WEAK_MATCH_SCORE_THRESHOLD,
    ASSEMBLY_CONFIDENCE_THRESHOLD,
)
from visualize import (
    render_fragment_grid,
    render_compatibility_heatmap,
    render_assembly_proposal,
    render_convergence_plot,
)
from assembly_renderer import render_assembly_sheet
from shape_descriptors import pca_normalize_contour, log_shape_summary
from ensemble_postprocess import reclassify_borderline_cases

# Pipeline constants
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp'}
N_SEGMENTS = 4
N_TOP_ASSEMBLIES = 3
COLOR_PRECHECK_GAP_THRESH = 0.15
COLOR_PRECHECK_LOW_MAX = 0.75


class ProgressCallback:
    """
    Queue-based progress reporter for pipeline execution.

    Provides a thread-safe mechanism for worker threads to report progress
    updates back to the GUI main thread via a queue. All messages are
    formatted as tuples for easy unpacking in the GUI event loop.

    Attributes
    ----------
    queue : queue.Queue
        Thread-safe queue for progress messages

    Methods
    -------
    report(message, percent=None)
        Report a progress update to the GUI
    """

    def __init__(self, progress_queue: queue.Queue):
        """
        Initialize progress callback with a message queue.

        Parameters
        ----------
        progress_queue : queue.Queue
            Queue for sending progress updates to GUI thread
        """
        self.queue = progress_queue

    def report(self, message: str, percent: Optional[float] = None) -> None:
        """
        Report a progress update.

        Sends a formatted progress tuple to the queue for consumption by
        the GUI thread. Non-blocking operation.

        Parameters
        ----------
        message : str
            Human-readable progress message
        percent : float, optional
            Progress percentage (0-100), or None for indeterminate progress

        Examples
        --------
        >>> callback = ProgressCallback(queue.Queue())
        >>> callback.report("Loading fragments...", 10.0)
        >>> callback.report("Computing compatibility matrix...")
        """
        self.queue.put(("progress", message, percent))


class PipelineRunner(threading.Thread):
    """
    Background thread for executing the reconstruction pipeline.

    Extends threading.Thread to run the full pipeline in a separate thread,
    preventing GUI freezing during long-running operations. Communicates
    results and progress via a queue.

    Attributes
    ----------
    args : argparse.Namespace
        Pipeline arguments (input, output, log directories)
    progress_queue : queue.Queue
        Queue for progress updates and results
    cancel_event : threading.Event
        Event for graceful cancellation (checked periodically)
    daemon : bool
        Set to True so thread terminates when main program exits

    Methods
    -------
    run()
        Execute pipeline (called automatically by thread.start())
    request_cancel()
        Signal the thread to cancel gracefully
    """

    def __init__(self, args: argparse.Namespace, progress_queue: queue.Queue):
        """
        Initialize pipeline runner thread.

        Parameters
        ----------
        args : argparse.Namespace
            Pipeline configuration with input/output/log paths
        progress_queue : queue.Queue
            Queue for sending progress updates and results to GUI
        """
        super().__init__()
        self.args = args
        self.progress_queue = progress_queue
        self.cancel_event = threading.Event()
        self.daemon = True  # Thread dies with main program

    def request_cancel(self) -> None:
        """
        Request graceful cancellation of the pipeline.

        Sets the cancel event flag. The pipeline should check this flag
        periodically and exit cleanly if cancellation is requested.
        """
        self.cancel_event.set()

    def run(self) -> None:
        """
        Execute the pipeline in the background thread.

        This method is called automatically by thread.start(). It wraps
        run_pipeline_with_monitoring() with exception handling and sends
        results or errors back to the GUI via the queue.

        Queue messages sent:
        - ("progress", message, percent): Progress updates
        - ("complete", results): Success with results dictionary
        - ("error", error_message): Failure with exception message
        """
        try:
            # Create progress callback for this thread
            callback = ProgressCallback(self.progress_queue)

            # Run pipeline with progress monitoring
            results = run_pipeline_with_monitoring(
                self.args,
                callback,
                self.cancel_event
            )

            # Send completion message with results
            if results is not None:
                self.progress_queue.put(("complete", results))
            else:
                # Pipeline was cancelled
                self.progress_queue.put(("error", "Pipeline execution was cancelled"))

        except Exception as e:
            # Send error message on any exception
            error_msg = f"{type(e).__name__}: {str(e)}"
            self.progress_queue.put(("error", error_msg))

            # Also log the full traceback for debugging
            import traceback
            traceback.print_exc()


def run_pipeline_with_monitoring(
    args: argparse.Namespace,
    callback: ProgressCallback,
    cancel_event: Optional[threading.Event] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute the reconstruction pipeline with progress callbacks.

    This is the core wrapper function that runs the pipeline from main.py
    while injecting progress reporting at key stages. It mirrors the structure
    of main.run_pipeline() but adds callback.report() calls throughout.

    Parameters
    ----------
    args : argparse.Namespace
        Pipeline configuration (input, output, log directories)
    callback : ProgressCallback
        Progress reporter for sending updates to GUI
    cancel_event : threading.Event, optional
        Event to check for cancellation requests

    Returns
    -------
    results : dict or None
        Dictionary containing pipeline results:
          - 'assemblies': list of assembly proposals
          - 'compat_matrix': pairwise compatibility matrix
          - 'convergence_trace': relaxation convergence history
          - 'fragment_names': list of fragment identifiers
          - 'images': list of fragment images
          - 'contours': list of fragment contours
          - 'elapsed_time': wall-clock execution time
        Returns None if pipeline was cancelled.

    Raises
    ------
    FileNotFoundError
        If input directory contains no valid fragment images
    Exception
        Any exception from pipeline stages (preprocessing, compatibility, etc.)

    Examples
    --------
    >>> args = argparse.Namespace(input='data/sample', output='outputs', log='logs')
    >>> callback = ProgressCallback(queue.Queue())
    >>> results = run_pipeline_with_monitoring(args, callback)
    >>> print(f"Found {len(results['assemblies'])} assemblies")
    """
    # Setup logging
    callback.report("Setting up logging...", 0.0)
    os.makedirs(args.log, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_path = os.path.join(args.log, f'run_{timestamp}.log')

    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(),
        ],
    )
    run_logger = logging.getLogger('gui_pipeline')
    run_logger.info("Log file: %s", log_path)

    os.makedirs(args.output, exist_ok=True)
    start_time = time.time()

    # Check for cancellation
    if cancel_event and cancel_event.is_set():
        return None

    # Collect fragment images
    callback.report("Loading fragment images...", 5.0)
    paths = sorted(
        p for p in Path(args.input).iterdir()
        if p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if not paths:
        raise FileNotFoundError(f"No images found in: {args.input}")

    run_logger.info("Found %d fragment images in %s", len(paths), args.input)

    # Preprocess fragments
    images, contours, all_segments, all_pixel_segs, names = [], [], [], [], []

    for idx, fpath in enumerate(paths):
        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            return None

        percent = 5.0 + (idx / len(paths)) * 25.0
        callback.report(f"Preprocessing fragment {idx+1}/{len(paths)}: {fpath.stem}", percent)

        name = fpath.stem
        image, contour = preprocess_fragment(str(fpath))

        # PCA orientation normalization
        log_shape_summary(contour, name)
        pca_contour = pca_normalize_contour(contour)

        _, segments = encode_fragment(pca_contour, n_segments=N_SEGMENTS)
        pixel_segs = contour_to_pixel_segments(contour, N_SEGMENTS)

        images.append(image)
        contours.append(contour)
        all_segments.append(segments)
        all_pixel_segs.append(pixel_segs)
        names.append(name)

        run_logger.info(
            "Fragment %-20s  size=%dx%d  contour=%d pts  segments=%d",
            name, image.shape[1], image.shape[0], len(contour), len(segments),
        )

    # Color pre-check
    callback.report("Running color pre-check...", 30.0)

    # Check for cancellation
    if cancel_event and cancel_event.is_set():
        return None

    if len(images) >= 3:
        sigs = [compute_color_signature(img) for img in images]
        n = len(sigs)
        bcs = sorted(
            color_bhattacharyya(sigs[i], sigs[j])
            for i in range(n)
            for j in range(i + 1, n)
        )

        gaps = [(bcs[k + 1] - bcs[k], k) for k in range(len(bcs) - 1)]
        max_gap, gap_pos = max(gaps)
        low_group_max = bcs[gap_pos]

        is_mixed = (max_gap >= COLOR_PRECHECK_GAP_THRESH
                    and low_group_max <= COLOR_PRECHECK_LOW_MAX)

        run_logger.info(
            "Color pre-check: min_BC=%.3f  max_gap=%.3f  is_mixed=%s",
            bcs[0], max_gap, is_mixed,
        )

        if is_mixed:
            run_logger.warning(
                "Bimodal color distribution detected (gap=%.3f, min_BC=%.3f). "
                "Fragments appear to come from different source images.",
                max_gap, bcs[0],
            )
            # Return early with no match result
            results = {
                'assemblies': [],
                'compat_matrix': None,
                'convergence_trace': [],
                'fragment_names': names,
                'images': images,
                'contours': contours,
                'elapsed_time': time.time() - start_time,
                'verdict': 'NO_MATCH_COLOR',
                'color_gap': max_gap,
                'min_bc': bcs[0],
            }
            callback.report("Color pre-check failed: mixed source fragments detected", 100.0)
            return results

    # Build compatibility matrix
    callback.report("Computing pairwise compatibility matrix...", 40.0)

    # Check for cancellation
    if cancel_event and cancel_event.is_set():
        return None

    compat_matrix, appearance_mats = build_compatibility_matrix(
        all_segments, all_pixel_segs, images
    )

    # Log compatibility matrix
    summary = compat_matrix.mean(axis=(1, 3))
    run_logger.info("Pairwise compatibility matrix (mean over segments):")
    header = "         " + "  ".join(f"{n:>10}" for n in names)
    run_logger.info(header)
    for row_idx in range(compat_matrix.shape[0]):
        values = "  ".join(
            f"{summary[row_idx, col_idx]:10.4f}"
            for col_idx in range(compat_matrix.shape[0])
        )
        run_logger.info("%8s  %s", names[row_idx], values)

    # Run relaxation labeling
    callback.report("Running relaxation labeling...", 60.0)

    # Check for cancellation
    if cancel_event and cancel_event.is_set():
        return None

    probs, trace = run_relaxation(compat_matrix)
    run_logger.info(
        "Convergence trace (%d iterations): %s",
        len(trace),
        ", ".join(f"{v:.6f}" for v in trace),
    )

    # Extract top assemblies
    callback.report("Extracting top assembly proposals...", 75.0)

    # Check for cancellation
    if cancel_event and cancel_event.is_set():
        return None

    assemblies = extract_top_assemblies(
        probs, n_top=N_TOP_ASSEMBLIES, compat_matrix=compat_matrix
    )

    # Apply ensemble voting post-processing
    if appearance_mats is not None:
        callback.report("Applying ensemble voting post-processing...", 80.0)
        run_logger.info("Applying Track 3 (Ensemble Voting) post-processing...")

        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            return None

        assemblies = reclassify_borderline_cases(
            assemblies, compat_matrix, appearance_mats, images
        )

    # Log assembly report
    run_logger.info("=" * 60)
    run_logger.info(
        "MATCH REPORT  (per-pair thresholds: MATCH>=%.2f  WEAK>=%.2f)",
        MATCH_SCORE_THRESHOLD, WEAK_MATCH_SCORE_THRESHOLD,
    )
    run_logger.info("=" * 60)

    any_match = False
    for rank, assembly in enumerate(assemblies):
        verdict = assembly['verdict']
        confidence = assembly['confidence']
        n_m = assembly['n_match']
        n_w = assembly['n_weak']
        n_n = assembly['n_no_match']

        run_logger.info(
            "Assembly #%d  verdict=%-10s  confidence=%.4f  "
            "pairs: %d MATCH / %d WEAK / %d NO_MATCH",
            rank + 1, verdict, confidence, n_m, n_w, n_n,
        )

        if verdict != 'NO_MATCH':
            any_match = True

        for pair in assembly['pairs']:
            run_logger.info(
                "  frag%d[seg%d] <-> frag%d[seg%d]  "
                "raw=%.4f  prob=%.4f  [%s]",
                pair['frag_i'], pair['seg_a'],
                pair['frag_j'], pair['seg_b'],
                pair['raw_compat'], pair['score'],
                pair['verdict'],
            )

    run_logger.info("=" * 60)

    # Determine overall verdict
    if not any_match:
        verdict = 'NO_MATCH'
    else:
        accepted = [a for a in assemblies if a['verdict'] != 'NO_MATCH']
        verdict = "MATCH" if any(a['verdict'] == 'MATCH' for a in accepted) else "WEAK_MATCH"

    # Generate visualizations
    callback.report("Rendering visualizations...", 85.0)

    # Check for cancellation
    if cancel_event and cancel_event.is_set():
        return None

    render_fragment_grid(
        images, contours, names,
        os.path.join(args.output, 'fragment_contours.png'),
    )
    render_compatibility_heatmap(
        compat_matrix, names,
        os.path.join(args.output, 'compatibility_heatmap.png'),
    )
    render_convergence_plot(
        trace,
        os.path.join(args.output, 'convergence.png'),
    )

    for rank, assembly in enumerate(assemblies):
        # Check for cancellation
        if cancel_event and cancel_event.is_set():
            return None

        percent = 85.0 + (rank / len(assemblies)) * 10.0
        callback.report(f"Rendering assembly {rank+1}/{len(assemblies)}...", percent)

        out_path = os.path.join(args.output, f'assembly_{rank + 1:02d}.png')
        render_assembly_proposal(images, contours, assembly, names, rank, out_path)

        geo_path = os.path.join(args.output, f'assembly_{rank + 1:02d}_geometric.png')
        render_assembly_sheet(
            images, contours, assembly, names, N_SEGMENTS, geo_path
        )

    elapsed = time.time() - start_time
    run_logger.info("Pipeline completed in %.2f seconds.", elapsed)

    callback.report("Pipeline complete!", 100.0)

    # Return results dictionary
    results = {
        'assemblies': assemblies,
        'compat_matrix': compat_matrix,
        'convergence_trace': trace,
        'fragment_names': names,
        'images': images,
        'contours': contours,
        'elapsed_time': elapsed,
        'verdict': verdict,
        'any_match': any_match,
    }

    return results
