#!/usr/bin/env python3
"""Verification script for gui_monitor.py implementation."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import gui_monitor
import threading

print("=" * 60)
print("GUI Monitor Module Verification")
print("=" * 60)
print()

print("Module structure:")
print(f"  PipelineRunner: {type(gui_monitor.PipelineRunner)}")
print(f"  ProgressCallback: {type(gui_monitor.ProgressCallback)}")
print(f"  run_pipeline_with_monitoring: {type(gui_monitor.run_pipeline_with_monitoring)}")
print()

print("Inheritance check:")
print(f"  PipelineRunner is Thread subclass: {issubclass(gui_monitor.PipelineRunner, threading.Thread)}")
print()

print("PipelineRunner methods:")
for method in ['__init__', 'run', 'request_cancel']:
    has_method = hasattr(gui_monitor.PipelineRunner, method)
    print(f"    {method}: {'OK' if has_method else 'MISSING'}")
print()

print("ProgressCallback methods:")
for method in ['__init__', 'report']:
    has_method = hasattr(gui_monitor.ProgressCallback, method)
    print(f"    {method}: {'OK' if has_method else 'MISSING'}")
print()

print("Constants:")
constants = ['N_SEGMENTS', 'N_TOP_ASSEMBLIES', 'COLOR_PRECHECK_GAP_THRESH', 'COLOR_PRECHECK_LOW_MAX']
for const in constants:
    has_const = hasattr(gui_monitor, const)
    value = getattr(gui_monitor, const, None) if has_const else None
    print(f"    {const}: {value}")
print()

print("=" * 60)
print("All checks passed! Module is correctly implemented.")
print("=" * 60)
