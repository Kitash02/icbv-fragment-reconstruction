# GUI Monitor Quick Reference

## Import and Setup

```python
import argparse
import queue
from src.gui_monitor import PipelineRunner, ProgressCallback

# Create arguments
args = argparse.Namespace(
    input='data/fragments',  # Input folder with fragment images
    output='outputs/results', # Output folder for results
    log='outputs/logs'        # Log folder
)

# Create queue and runner
progress_queue = queue.Queue()
runner = PipelineRunner(args, progress_queue)
```

## Start Pipeline

```python
# Start background thread (non-blocking)
runner.start()
```

## Poll Progress (Tkinter Example)

```python
def poll_queue():
    """Poll progress queue every 100ms."""
    try:
        msg_type, *data = progress_queue.get_nowait()

        if msg_type == "progress":
            message, percent = data
            # Update UI
            if percent is not None:
                progress_bar['value'] = percent
            status_label.config(text=message)

        elif msg_type == "complete":
            results = data[0]
            # Display results
            show_results(results)

        elif msg_type == "error":
            error_msg = data[0]
            # Show error
            messagebox.showerror("Error", error_msg)
            return  # Stop polling

    except queue.Empty:
        pass  # No message, continue polling

    # Schedule next poll
    root.after(100, poll_queue)

# Start polling
poll_queue()
```

## Cancel Pipeline

```python
def on_cancel_button():
    """User clicked cancel button."""
    runner.request_cancel()
    status_label.config(text="Cancelling...")
```

## Message Types

### Progress Update
```python
("progress", "Loading fragments...", 10.0)  # With percentage
("progress", "Running relaxation...", None) # Indeterminate
```

### Completion
```python
("complete", {
    'assemblies': [...],
    'verdict': 'MATCH',
    'elapsed_time': 42.5,
    ...
})
```

### Error
```python
("error", "FileNotFoundError: No images found in: data/invalid")
```

## Results Dictionary Keys

```python
results = {
    'assemblies': list,         # Assembly proposals
    'compat_matrix': ndarray,   # Compatibility scores
    'convergence_trace': list,  # Relaxation history
    'fragment_names': list,     # Fragment IDs
    'images': list,             # Fragment images
    'contours': list,           # Fragment contours
    'elapsed_time': float,      # Seconds
    'verdict': str,             # Overall verdict
    'any_match': bool          # At least one match?
}
```

## Progress Stages

| % | Stage |
|---|-------|
| 0 | Setting up logging |
| 5 | Loading images |
| 5-30 | Preprocessing fragments |
| 30 | Color pre-check |
| 40 | Compatibility matrix |
| 60 | Relaxation labeling |
| 75 | Extracting assemblies |
| 80 | Ensemble voting |
| 85 | Rendering visualizations |
| 85-95 | Rendering assemblies |
| 100 | Complete |

## Thread Safety

✓ Queue is thread-safe (no locks needed)
✓ Daemon thread (auto-terminates)
✓ Event-based cancellation (thread-safe)
✓ No shared mutable state

## Common Patterns

### Disable UI During Execution
```python
def run_pipeline():
    run_button.config(state='disabled')
    cancel_button.config(state='normal')
    runner.start()
    poll_queue()
```

### Re-enable UI on Completion
```python
if msg_type in ["complete", "error"]:
    run_button.config(state='normal')
    cancel_button.config(state='disabled')
```

### Show Final Summary
```python
if msg_type == "complete":
    results = data[0]
    n_assemblies = len(results['assemblies'])
    elapsed = results['elapsed_time']
    verdict = results['verdict']

    summary = f"Found {n_assemblies} assemblies in {elapsed:.1f}s\n"
    summary += f"Verdict: {verdict}"
    messagebox.showinfo("Complete", summary)
```

## Files

- **Implementation**: `src/gui_monitor.py` (567 lines)
- **Demo**: `demo_gui_monitor.py` (127 lines)
- **Full docs**: `GUI_MONITOR_USAGE.md` (398 lines)
- **This card**: `GUI_MONITOR_QUICK_REF.md`

## Verification

```bash
# Verify module loads
python verify_gui_monitor.py

# Run demo (requires data/sample)
python demo_gui_monitor.py
```
