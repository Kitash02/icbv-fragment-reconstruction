#!/usr/bin/env python3
"""Temporary test script for Variant 6 iteration 2"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Monkey-patch compatibility_variant6 as 'compatibility'
import compatibility_variant6
sys.modules['compatibility'] = compatibility_variant6

# Run standard test
import run_test
run_test.main()
