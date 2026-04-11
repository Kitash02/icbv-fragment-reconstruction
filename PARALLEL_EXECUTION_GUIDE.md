# Parallel Execution Guide - 10 Agents Running All Samples

## What's Running Now

**Status**: ✅ 10 parallel agents are processing all fragment datasets

**Command**: `python run_all_samples_parallel.py`

## Datasets Being Processed

The system is running reconstruction on **10 datasets** in parallel:

### 1. Sample Dataset
- Location: `data/sample/`
- Fragments: 5 PNG files
- Category: Sample/Demo

### 2-10. Positive Example Datasets
- Location: `data/examples/positive/<name>/`
- Various fragment counts
- Category: Positive (known to be reconstructible)

Full list:
1. sample
2. gettyimages-1311604917-1024x1024
3. gettyimages-170096524-1024x1024
4. gettyimages-2177809001-1024x1024
5. gettyimages-470816328-2048x2048
6. high-res-antique-close-up-earth-muted-tones-...
7. scroll
8. shard_01_british
9. shard_02_cord_marked
10. Wall painting from Room H of the Villa of P. Fannius Synistor at Boscoreale

## Configuration

- **Parallel Agents**: 10 simultaneous processes
- **Timeout**: 10 minutes per dataset
- **CPU Usage**: Will utilize up to 10 CPU cores
- **Expected Duration**: 5-15 minutes total (depending on hardware)

## Output Locations

### Results (Assembled Images)
```
outputs/parallel_results/<dataset_name>/
├── fragment_contours.png
├── compatibility_heatmap.png
├── convergence.png
├── assembly_01.png
├── assembly_02.png
└── assembly_03.png
```

### Logs (Detailed Execution Logs)
```
outputs/parallel_logs/<dataset_name>/
└── run_YYYYMMDD_HHMMSS.log
```

## Monitoring Progress

### Check Real-Time Progress
The script prints status updates as each agent completes:
- ✅ SUCCESS: Dataset completed
- ❌ FAILED: Dataset failed (with error)
- ⏱️ TIMEOUT: Dataset exceeded 10 minutes

### Check Background Task
```bash
# View current output (updates in real-time)
tail -f C:\Users\I763940\AppData\Local\Temp\claude\C--Users-I763940\tasks\bfz215jv8.output
```

### Check System Resource Usage
```bash
# CPU/Memory usage
tasklist | findstr python
```

## Final Summary Report

When all agents complete, you'll see:

```
==========================================================================================
 PARALLEL EXECUTION SUMMARY
==========================================================================================
Dataset                             Frags   Status     Time (s)   Category
------------------------------------------------------------------------------------------
sample                              5       ✅ SUCCESS  45.2       sample
gettyimages-1311604917-1024x1024   12       ✅ SUCCESS  78.5       positive
...
------------------------------------------------------------------------------------------
Total: 10 datasets | Success: 10 | Failed: 0 | Total time: 145.3s
==========================================================================================

==========================================================================================
 PARALLELIZATION EFFICIENCY
==========================================================================================
Sequential time (estimated): 523.4s (8.7 min)
Parallel time (actual):      145.3s (2.4 min)
Speedup:                     3.6x
Efficiency:                  36.0%
==========================================================================================
```

## Understanding the Results

### Speedup
- **Sequential**: Running datasets one at a time
- **Parallel**: Running 10 datasets simultaneously
- **Speedup**: How much faster parallel is (e.g., 3.6x = 3.6 times faster)

### Efficiency
- **100% efficiency**: Perfect parallelization (10x speedup with 10 agents)
- **36% efficiency**: Typical due to:
  - I/O bottlenecks (disk reads/writes)
  - Synchronization overhead
  - Some datasets finish faster than others

## What This Demonstrates

1. **Scalability**: System can process multiple reconstructions simultaneously
2. **Resource Utilization**: Efficient use of multi-core CPUs
3. **Throughput**: Can handle batch processing for large archaeological collections
4. **Robustness**: Each agent runs independently (one failure doesn't affect others)

## After Completion

### View Results in GUI
```bash
python launch_gui.py
```
Then:
1. Click "Browse Folder..."
2. Navigate to `outputs/parallel_results/<dataset_name>/`
3. View reconstructed assemblies

### View Results Manually
```bash
# Open results folder
explorer outputs\parallel_results

# Each subfolder contains reconstruction results for one dataset
```

### Analyze Logs
```bash
# View detailed log for specific dataset
notepad outputs\parallel_logs\sample\run_*.log
```

## Stopping Execution

If you need to stop the parallel execution:

```bash
# Find Python processes
tasklist | findstr python

# Kill specific process (replace PID)
taskkill /F /PID <process_id>

# Or kill all Python processes (careful!)
taskkill /F /IM python.exe
```

## Re-Running

To run again (clears previous results):
```bash
python run_all_samples_parallel.py
```

To keep previous results and run with different parameters:
```bash
# Edit the script to change:
# - MAX_PARALLEL_AGENTS (line 13)
# - TIMEOUT_MINUTES (line 14)

python run_all_samples_parallel.py
```

---

## Current Status: RUNNING

The 10 agents are currently processing all datasets in parallel. You can:

1. **Wait for completion** - Check the output for the final summary report
2. **Ask questions** - I'm available to answer questions while it runs
3. **Monitor progress** - Use the tail command above to watch real-time output
4. **Check partial results** - Results appear in `outputs/parallel_results/` as each agent completes

**Estimated completion**: 5-15 minutes (depending on your hardware)
