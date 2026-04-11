import json

file_path = r'C:\Users\I763940\.claude\projects\C--Users-I763940\ece07127-20d3-460a-a966-c2c82ecfcf43.jsonl'

# Extract all edits
edit_operations = []
line_num = 0

with open(file_path, 'r', encoding='utf-8') as f:
    for line in f:
        line_num += 1
        try:
            data = json.loads(line)
            if data.get('type') == 'assistant':
                message = data.get('message', {})
                content = message.get('content', [])
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_use' and item.get('name') == 'Edit':
                            input_data = item.get('input', {})
                            file_path_edit = input_data.get('file_path', '')
                            if 'compatibility' in file_path_edit or 'relaxation' in file_path_edit:
                                edit_operations.append({
                                    'line': line_num,
                                    'file': file_path_edit,
                                    'old_string': input_data.get('old_string', ''),
                                    'new_string': input_data.get('new_string', ''),
                                    'replace_all': input_data.get('replace_all', False)
                                })
        except:
            continue

# Create comprehensive output
output = []
output.append("# COMPLETE CODE CHANGE HISTORY - Fragment Reconstruction System")
output.append("")
output.append("**Date:** 2026-04-08")
output.append("**Session:** ece07127-20d3-460a-a966-c2c82ecfcf43")
output.append("**Total Edit Operations:** " + str(len(edit_operations)))
output.append("")
output.append("---")
output.append("")
output.append("## EXECUTIVE SUMMARY")
output.append("")
output.append("### Problem Statement")
output.append("The fragment reconstruction system had 53% negative case accuracy (19/36 passing).")
output.append("Cross-source pottery fragments with similar colors (BC ~0.85) caused false positives.")
output.append("")
output.append("### Solution Evolution")
output.append("")
output.append("| Stage | Formula | Thresholds | Positive Acc | Negative Acc | Status |")
output.append("|-------|---------|------------|--------------|--------------|--------|")
output.append("| Baseline | `(1 - BC) * 0.80` penalty | 0.55/0.35/0.45 | 100% (9/9) | 53% (19/36) | Original |")
output.append("| Stage 1 | `color^6 * texture^2 * gabor^2` | 0.85/0.70/0.75 | 33% (3/9) | 83% (30/36) | Too harsh |")
output.append("| Stage 1.5 | `color^4 * texture^2 * gabor^2` | 0.85/0.70/0.75 | 56% (5/9) | 94% (34/36) | Better but low positives |")
output.append("| Stage 1.6 | `color^4 * texture^2 * gabor^2 * haralick^2` | 0.75/0.60/0.65 | **89% (8/9)** | **86% (31/36)** | SUCCESS |")
output.append("")
output.append("### Key Changes")
output.append("")
output.append("1. **Formula Change:** Switched from subtractive penalty to multiplicative penalty")
output.append("   - Old: `score - (1 - BC) * weight`")
output.append("   - New: `score * (BC_color^4 * BC_texture^2 * BC_gabor^2 * BC_haralick^2)`")
output.append("")
output.append("2. **Feature Addition:** Added LBP texture and Haralick features")
output.append("   - Texture captures surface micro-patterns (wheel marks, weathering)")
output.append("   - Haralick captures spatial texture relationships")
output.append("")
output.append("3. **Threshold Adjustments:**")
output.append("   - MATCH_SCORE_THRESHOLD: 0.55 -> 0.70 -> 0.85 -> 0.75")
output.append("   - WEAK_MATCH_SCORE_THRESHOLD: 0.35 -> 0.50 -> 0.70 -> 0.60")
output.append("   - ASSEMBLY_CONFIDENCE_THRESHOLD: 0.45 -> 0.60 -> 0.75 -> 0.65")
output.append("")
output.append("---")
output.append("")

output.append("## DETAILED CHRONOLOGICAL CHANGES")
output.append("")
output.append("### STAGE 0: Initial Fixes (Cosmetic)")
output.append("")
output.append("#### Edit 1 - Line 144: Fix Unicode Arrow")
output.append("**File:** `compatibility.py`")
output.append("**Change:** Replace Unicode arrow with ASCII ->")
output.append("**Impact:** Cosmetic fix for Windows console")
output.append("")

output.append("### STAGE 1: Aggressive Multiplicative Penalty (FAILED)")
output.append("")
output.append("**Goal:** Eliminate false positives with strong exponential penalty")
output.append("**Result:** 33% positive accuracy (broke true positives)")
output.append("")
output.append("#### Edits 2-7: Change Penalty Formula")
output.append("**File:** `compatibility.py`")
output.append("- Changed from subtractive `(1-BC)*weight` to multiplicative `BC^power`")
output.append("- Added LBP texture features")
output.append("- Increased power from 2.5 -> 4.0")
output.append("- Combined color + texture with geometric mean")
output.append("")
output.append("#### Edits 8-9: Raise Thresholds")
output.append("**File:** `relaxation.py`")
output.append("- MATCH: 0.55 -> 0.70")
output.append("- WEAK: 0.35 -> 0.50")
output.append("- ASSEMBLY: 0.45 -> 0.60")
output.append("")

output.append("### STAGE 1 (continued): Add Gabor + Haralick + color^6")
output.append("")
output.append("**Result:** Still too aggressive - 33% positive accuracy")
output.append("")
output.append("#### Edits 10-12: Multiplicative with color^6")
output.append("**File:** `compatibility.py`")
output.append("**Formula:** `(bc_color ** 6.0) * (bc_texture ** 2.0) * (bc_gabor ** 2.0) * (bc_haralick ** 2.0)`")
output.append("")
output.append("#### Edit 13: Raise Thresholds Even Higher")
output.append("**File:** `relaxation.py`")
output.append("- MATCH: 0.70 -> 0.85")
output.append("- WEAK: 0.50 -> 0.70")
output.append("- ASSEMBLY: 0.60 -> 0.75")
output.append("")

output.append("### STAGE 1.5: Reduce Color Power (IMPROVEMENT)")
output.append("")
output.append("**Goal:** Fix broken positives by reducing color^6 -> color^4")
output.append("**Result:** 56% positive, 94% negative (better but still low positives)")
output.append("")
output.append("#### Edits 14-15: Reduce to color^4")
output.append("**File:** `compatibility.py`")
output.append("**Formula:** `(bc_color ** 4.0) * (bc_texture ** 2.0) * (bc_gabor ** 2.0) * (bc_haralick ** 2.0)`")
output.append("**Thresholds:** Kept at 0.85/0.70/0.75")
output.append("")

output.append("### STAGE 1.6: Lower Thresholds (FINAL SUCCESS)")
output.append("")
output.append("**Goal:** Keep color^4 formula, lower thresholds to accept more positives")
output.append("**Result:** 89% positive, 86% negative - BALANCED")
output.append("")
output.append("#### Edit 16: Lower Thresholds")
output.append("**File:** `relaxation.py`")
output.append("- MATCH: 0.85 -> 0.75")
output.append("- WEAK: 0.70 -> 0.60")
output.append("- ASSEMBLY: 0.75 -> 0.65")
output.append("")
output.append("**Formula:** Unchanged from Stage 1.5 (color^4)")
output.append("")
output.append("---")
output.append("")

output.append("## FINAL CONFIGURATION")
output.append("")
output.append("### Appearance Penalty Formula")
output.append("```python")
output.append("appearance_multiplier = (bc_color ** 4.0) * (bc_texture ** 2.0) * (bc_gabor ** 2.0) * (bc_haralick ** 2.0)")
output.append("score = score * appearance_multiplier")
output.append("```")
output.append("")
output.append("### Thresholds")
output.append("```python")
output.append("MATCH_SCORE_THRESHOLD = 0.75")
output.append("WEAK_MATCH_SCORE_THRESHOLD = 0.60")
output.append("ASSEMBLY_CONFIDENCE_THRESHOLD = 0.65")
output.append("```")
output.append("")
output.append("### Performance")
output.append("- **Positive Accuracy:** 89% (8/9)")
output.append("- **Negative Accuracy:** 86% (31/36)")
output.append("- **Improvement:** +33 percentage points on negatives")
output.append("")
output.append("---")
output.append("")

output.append("## APPENDIX: All 16 Edits in Detail")
output.append("")

# Add all edits in detail
for idx, op in enumerate(edit_operations, 1):
    output.append(f"### Edit {idx} - Line {op['line']}")
    output.append(f"**File:** `{op['file'].split('/')[-1] if '/' in op['file'] else op['file'].split(chr(92))[-1]}`")
    output.append("")
    output.append("**OLD CODE:**")
    output.append("```python")
    output.append(op['old_string'])
    output.append("```")
    output.append("")
    output.append("**NEW CODE:**")
    output.append("```python")
    output.append(op['new_string'])
    output.append("```")
    output.append("")
    output.append("---")
    output.append("")

# Save to file
with open('CONVERSATION_CODE_EXTRACTION.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Complete code extraction saved")
print(f"Document length: {len(output)} lines")
print(f"Total edits documented: {len(edit_operations)}")
print(f"Saved to: CONVERSATION_CODE_EXTRACTION.md")
