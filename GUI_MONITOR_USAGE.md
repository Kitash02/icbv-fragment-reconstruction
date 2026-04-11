# GUI Monitor Module - Usage Documentation

## Overview

The `gui_monitor.py` module provides thread-safe pipeline execution infrastructure for integrating the archaeological fragment reconstruction pipeline with graphical user interfaces. It enables non-blocking pipeline execution with real-time progress monitoring via queue-based communication.

## Architecture

### Components

1. **PipelineRunner (threading.Thread)**
   - Background thread for pipeline execution
   - Prevents GUI freezing during long operations
   - Handles exceptions gracefully
   - Supports cancellation via threading.Event

2. **ProgressCallback**
   - Queue-based progress reporter
   - Thread-safe communication channel
   - Sends formatted progress tuples

3. **run_pipeline_with_monitoring()**
   - Core wrapper around main.py's run_pipeline()
   - Injects progress callbacks throughout pipeline stages
   - Returns comprehensive results dictionary

### Queue Message Protocol

The module uses a simple tuple-based protocol for communication:

```python
# Progress update (sent periodically during execution)
("progress", message: str, percent: float | None)

# Successful completion (sent once at end)
("complete", results: dict)

# Error occurred (sent if exception raised)
("error", error_message: str)
```

## Usage Examples

### Basic Integration

```python
import argparse
import queue
from gui_monitor import PipelineRunner

# Setup pipeline arguments
args = argparse.Namespace(
    input='data/fragments',
    output='outputs/results',
    log='outputs/logs'
)

# Create queue and runner
progress_queue = queue.Queue()
runner = PipelineRunner(args, progress_queue)

# Start background execution
runner.start()

# Poll queue in GUI event loop
try:
    msg_type, *data = progress_queue.get_nowait()

    if msg_type == "progress":
        message, percent = data
        # Update progress bar and status label
        if percent is not None:
            progress_bar.set(percent)
        status_label.config(text=message)

    elif msg_type == "complete":
        results = data[0]
        # Display results, update UI
        show_assemblies(results['assemblies'])

    elif msg_type == "error":
        error_msg = data[0]
        # Show error dialog
        messagebox.showerror("Pipeline Error", error_msg)

except queue.Empty:
    # No message available, schedule next poll
    root.after(100, poll_queue)  # Check again in 100ms
```

### Tkinter Integration

```python
import tkinter as tk
from tkinter import ttk
import queue
from gui_monitor import PipelineRunner

class PipelineGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.progress_queue = None
        self.runner = None

        # Create progress bar
        self.progress = ttk.Progressbar(
            self,
            mode='determinate',
            maximum=100
        )
        self.progress.pack(pady=20, padx=20)

        # Create status label
        self.status = tk.Label(self, text="Ready")
        self.status.pack(pady=10)

        # Create run button
        self.run_btn = ttk.Button(
            self,
            text="Run Pipeline",
            command=self.run_pipeline
        )
        self.run_btn.pack(pady=10)

    def run_pipeline(self):
        """Start pipeline execution."""
        args = argparse.Namespace(
            input='data/sample',
            output='outputs/results',
            log='outputs/logs'
        )

        self.progress_queue = queue.Queue()
        self.runner = PipelineRunner(args, self.progress_queue)
        self.runner.start()

        # Disable button during execution
        self.run_btn.config(state='disabled')

        # Start polling
        self.poll_queue()

    def poll_queue(self):
        """Poll progress queue in GUI event loop."""
        try:
            msg_type, *data = self.progress_queue.get_nowait()

            if msg_type == "progress":
                message, percent = data
                if percent is not None:
                    self.progress['value'] = percent
                self.status.config(text=message)

            elif msg_type == "complete":
                results = data[0]
                self.status.config(
                    text=f"Complete! Found {len(results['assemblies'])} assemblies"
                )
                self.run_btn.config(state='normal')
                return  # Stop polling

            elif msg_type == "error":
                error_msg = data[0]
                self.status.config(text=f"Error: {error_msg}")
                self.run_btn.config(state='normal')
                return  # Stop polling

        except queue.Empty:
            pass  # No message available

        # Schedule next poll (every 100ms)
        self.after(100, self.poll_queue)

if __name__ == "__main__":
    app = PipelineGUI()
    app.mainloop()
```

### Cancellation Support

```python
import queue
import threading
from gui_monitor import PipelineRunner

# Create and start runner
args = argparse.Namespace(input='data', output='out', log='logs')
progress_queue = queue.Queue()
runner = PipelineRunner(args, progress_queue)
runner.start()

# User clicks cancel button
def on_cancel_clicked():
    """Request graceful cancellation."""
    runner.request_cancel()
    status_label.config(text="Cancelling...")

# The runner checks cancel_event periodically and exits cleanly
```

## Progress Tracking

The pipeline reports progress at the following stages:

| Percent | Stage                                  |
|---------|----------------------------------------|
| 0%      | Setting up logging                     |
| 5%      | Loading fragment images                |
| 5-30%   | Preprocessing fragments (incremental)  |
| 30%     | Running color pre-check                |
| 40%     | Computing compatibility matrix         |
| 60%     | Running relaxation labeling            |
| 75%     | Extracting assembly proposals          |
| 80%     | Applying ensemble voting               |
| 85%     | Rendering visualizations               |
| 85-95%  | Rendering assemblies (incremental)     |
| 100%    | Complete                               |

## Results Dictionary

When pipeline completes successfully, the results dictionary contains:

```python
{
    'assemblies': [          # List of assembly proposals
        {
            'verdict': str,          # 'MATCH', 'WEAK_MATCH', or 'NO_MATCH'
            'confidence': float,     # Average confidence score
            'n_match': int,          # Number of MATCH pairs
            'n_weak': int,           # Number of WEAK_MATCH pairs
            'n_no_match': int,       # Number of NO_MATCH pairs
            'pairs': [...]           # List of fragment pair details
        },
        ...
    ],
    'compat_matrix': ndarray,        # Pairwise compatibility matrix
    'convergence_trace': list,       # Relaxation convergence history
    'fragment_names': list,          # Fragment identifiers
    'images': list,                  # Fragment images (numpy arrays)
    'contours': list,                # Fragment contours
    'elapsed_time': float,           # Wall-clock execution time (seconds)
    'verdict': str,                  # Overall verdict
    'any_match': bool               # True if any assembly accepted
}
```

### Special Cases

**Color pre-check failure** (mixed source fragments):
```python
{
    'assemblies': [],
    'compat_matrix': None,
    'convergence_trace': [],
    'verdict': 'NO_MATCH_COLOR',
    'color_gap': float,    # Bimodal gap size
    'min_bc': float,       # Minimum Bhattacharyya coefficient
    ...
}
```

**Cancellation**:
```python
# Returns None from run_pipeline_with_monitoring()
# Sends ("error", "Pipeline execution was cancelled") to queue
```

## Thread Safety

- **Queue operations**: Thread-safe by design (Python's queue.Queue)
- **Daemon thread**: Runner is daemon=True, terminates with main program
- **Cancel event**: Thread-safe via threading.Event
- **No shared state**: Results passed via queue, no global variables

## Error Handling

The module handles errors at multiple levels:

1. **Import errors**: Logged if pipeline modules unavailable
2. **Runtime exceptions**: Caught in PipelineRunner.run(), sent as ("error", msg)
3. **File not found**: Raised if input directory empty
4. **Cancellation**: Checked periodically, returns None cleanly

## Testing

### Unit Test Example

```python
import unittest
import queue
import argparse
from gui_monitor import PipelineRunner, ProgressCallback

class TestGUIMonitor(unittest.TestCase):
    def test_progress_callback(self):
        """Test progress callback sends messages to queue."""
        q = queue.Queue()
        callback = ProgressCallback(q)

        callback.report("Test message", 50.0)

        msg_type, message, percent = q.get()
        self.assertEqual(msg_type, "progress")
        self.assertEqual(message, "Test message")
        self.assertEqual(percent, 50.0)

    def test_runner_initialization(self):
        """Test runner can be initialized."""
        args = argparse.Namespace(
            input='data/sample',
            output='outputs',
            log='logs'
        )
        q = queue.Queue()
        runner = PipelineRunner(args, q)

        self.assertTrue(runner.daemon)
        self.assertIsNotNone(runner.cancel_event)
```

### Integration Test

Run the provided `demo_gui_monitor.py`:

```bash
python demo_gui_monitor.py
```

This simulates GUI integration by:
1. Creating a pipeline runner
2. Polling the progress queue
3. Displaying progress updates
4. Showing final results

## Best Practices

1. **Always poll queue**: Use GUI's event loop (tkinter's after(), Qt's QTimer)
2. **Handle all message types**: Progress, complete, and error
3. **Don't block**: Use get_nowait() or get(timeout=small_value)
4. **Disable UI during run**: Prevent multiple simultaneous executions
5. **Join thread on exit**: Ensure clean shutdown
6. **Check cancellation**: Support user cancellation for long operations

## Troubleshooting

### Issue: GUI freezes during pipeline execution

**Cause**: Running pipeline in GUI main thread instead of background thread

**Solution**: Always use PipelineRunner, never call run_pipeline_with_monitoring() directly from GUI thread

### Issue: Progress updates not appearing

**Cause**: Not polling queue frequently enough

**Solution**: Poll every 50-200ms using after() or QTimer

### Issue: Thread doesn't terminate

**Cause**: Pipeline stuck in long operation without cancellation checks

**Solution**: Verify cancel_event is checked in pipeline stages

### Issue: Import errors in worker thread

**Cause**: Missing dependencies or incorrect sys.path

**Solution**: Ensure all pipeline modules are installed and src/ is in path

## Performance Notes

- **Thread overhead**: Minimal (<50ms startup)
- **Queue overhead**: <1ms per message
- **Polling frequency**: 50-200ms recommended (responsive without excessive CPU)
- **Memory**: Results dict may be large for many fragments (MB range)

## Future Enhancements

Potential improvements for future versions:

1. **Streaming results**: Send partial results as available
2. **Progress estimation**: More granular percent tracking
3. **Multiple workers**: Parallel processing of independent fragments
4. **Persistent state**: Save/resume interrupted pipelines
5. **Live visualization**: Stream intermediate images to GUI

## See Also

- `src/main.py` - Core pipeline implementation
- `src/gui_main.py` - GUI application main window
- `src/gui_components.py` - GUI panel implementations
- `demo_gui_monitor.py` - Integration demonstration script

## License

Part of the Archaeological Fragment Reconstruction System
Course: Introduction to Computational and Biological Vision (ICBV)
