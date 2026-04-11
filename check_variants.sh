#!/bin/bash
# Quick check script to verify all variant files are ready

echo "Checking Variant Files..."
echo "========================="

files=(
    "run_variant0.py"
    "run_variant1.py"
    "run_variant2.py"
    "run_variant3.py"
    "run_variant4.py"
    "run_variant5.py"
    "run_variant6.py"
    "run_variant7.py"
    "run_variant8.py"
    "run_variant9.py"
)

missing=0
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (MISSING)"
        missing=$((missing + 1))
    fi
done

echo ""
echo "Summary: $((${#files[@]} - missing))/${#files[@]} files ready"

if [ $missing -eq 0 ]; then
    echo ""
    echo "🎉 All variant files ready!"
    echo "Run: python parallel_variant_tester.py"
else
    echo ""
    echo "⚠ Waiting for $missing files..."
fi
