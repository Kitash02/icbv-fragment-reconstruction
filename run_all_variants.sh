#!/bin/bash
# Run all 10 variants sequentially and save results

OUTPUT_DIR="outputs/variant_results"
mkdir -p "$OUTPUT_DIR"

echo "=================================="
echo "SEQUENTIAL VARIANT TESTING"
echo "=================================="
echo "Running 10 variants..."
echo ""

for i in {0..9}; do
    echo "[$( date +%H:%M:%S )] Starting Variant $i..."
    python run_variant$i.py --no-rotate > "$OUTPUT_DIR/variant_${i}_output.txt" 2>&1

    # Extract key metrics
    grep -E "Positive accuracy|Negative accuracy|OVERALL" "$OUTPUT_DIR/variant_${i}_output.txt" | head -3

    echo "[$( date +%H:%M:%S )] Variant $i completed"
    echo ""
done

echo "=================================="
echo "ALL VARIANTS COMPLETED"
echo "=================================="
echo "Results saved to: $OUTPUT_DIR/"
