# Configuration System Documentation

## Overview

The configuration system provides centralized management of all algorithmic parameters in the Archaeological Fragment Reconstruction pipeline. All magic numbers have been extracted from the code into a single YAML file with comprehensive documentation and validation.

## Quick Start

### Basic Usage

```python
from config import Config

# Load default configuration
cfg = Config()

# Access parameters with dot notation
sigma = cfg.preprocessing.gaussian_sigma
threshold = cfg.relaxation.match_score_threshold

# Or use dictionary notation
sigma = cfg['preprocessing']['gaussian_sigma']
```

### Custom Configuration

```python
# Load custom config file
cfg = Config('path/to/custom_config.yaml')

# Update parameters dynamically
cfg.update('relaxation', 'match_score_threshold', 0.80)

# Save modified configuration
cfg.save('experiments/experiment_001.yaml')
```

### Global Singleton

```python
from config import get_config

# Get global config instance (initialized once)
cfg = get_config()

# Reload global config from file
from config import reload_config
reload_config('custom_config.yaml')
```

## Configuration File Structure

### File Location

Default configuration: `config/default_config.yaml`

### Top-Level Sections

1. **preprocessing** - Image preprocessing parameters (Gaussian blur, Canny, thresholding)
2. **chain_code** - Freeman chain code encoding parameters
3. **shape_descriptors** - Fourier descriptors and PCA normalization
4. **compatibility** - Multi-modal fragment matching parameters
5. **relaxation** - Relaxation labeling convergence and thresholds
6. **hard_discriminators** - Fast rejection criteria (edge density, entropy)
7. **ensemble_voting** - 5-way voting system parameters
8. **mixed_source_detection** - Color pre-check for mixed-source fragments
9. **pipeline** - Top-level orchestration parameters
10. **logging** - Log level and format configuration

## Key Parameters

### Preprocessing

```yaml
preprocessing:
  gaussian_sigma: 1.5            # Blur strength (0.5-3.0)
  canny_sigma_scale: 0.33        # Automatic threshold (0.2-0.5)
  min_contour_area: 500          # Minimum valid contour (100-5000)
```

**Purpose**: Control edge detection and noise suppression.

**When to adjust**:
- Increase `gaussian_sigma` for noisy images
- Decrease `canny_sigma_scale` for weak edges
- Increase `min_contour_area` to filter small artifacts

### Compatibility Scoring

```yaml
compatibility:
  good_continuation_weight: 0.10  # Smooth join bonus (0.0-0.3)
  fourier_weight: 0.25            # Global shape weight (0.0-0.5)
  color_power: 4.0                # Color penalty exponent (1.0-8.0)
  texture_power: 2.0              # Texture penalty exponent (1.0-5.0)
```

**Purpose**: Control the relative importance of geometric vs. appearance features.

**When to adjust**:
- Increase `color_power` to reject color mismatches more aggressively
- Increase `fourier_weight` to emphasize global shape over local curvature
- Decrease `good_continuation_weight` if getting too many smooth joins

### Relaxation Thresholds

```yaml
relaxation:
  match_score_threshold: 0.75           # Confident match (0.6-0.9)
  weak_match_score_threshold: 0.60      # Possible match (0.45-0.75)
  assembly_confidence_threshold: 0.65   # Assembly acceptance (0.5-0.8)
```

**Purpose**: Control match sensitivity vs. specificity.

**When to adjust**:
- **Lower thresholds** (0.70/0.55/0.60) → Accept more matches, more false positives
- **Higher thresholds** (0.80/0.65/0.70) → Reject uncertain matches, more false negatives
- **Current values** (0.75/0.60/0.65) → Balanced for 85%+ positive and negative accuracy

## Validation

### Automatic Checks

The configuration system validates all parameters on load:

1. **Range validation** - Numeric parameters must be within documented ranges
2. **Type validation** - All parameters must have correct types
3. **Cross-validation** - Related parameters are checked for consistency

### Validation Examples

```python
# This will raise ConfigValidationError
cfg.update('relaxation', 'match_score_threshold', 2.0)  # Out of range [0.4, 1.0]

# This will raise ConfigValidationError
cfg.update('relaxation', 'match_score_threshold', 'invalid')  # Wrong type

# This will raise ConfigValidationError
cfg['relaxation']['weak_match_score_threshold'] = 0.80
cfg['relaxation']['match_score_threshold'] = 0.70
cfg._validate()  # Weak >= Match is invalid
```

### Custom Validation Rules

Add new validation rules in `Config.VALIDATION_RULES`:

```python
VALIDATION_RULES = [
    ('section', 'param', min_val, max_val, 'description'),
    # Example:
    ('relaxation', 'match_score_threshold', 0.4, 1.0, 'Match score threshold'),
]
```

## Integration Guide

### Step 1: Import Configuration

Replace hardcoded constants with config access:

**Before:**
```python
MATCH_SCORE_THRESHOLD = 0.75
WEAK_MATCH_SCORE_THRESHOLD = 0.60
```

**After:**
```python
from config import get_config
cfg = get_config()

# Use cfg throughout module
match_threshold = cfg.relaxation.match_score_threshold
weak_threshold = cfg.relaxation.weak_match_score_threshold
```

### Step 2: Update Function Signatures

**Before:**
```python
def run_relaxation(compat_matrix):
    # Uses global constants
    ...
```

**After:**
```python
def run_relaxation(compat_matrix, cfg=None):
    if cfg is None:
        cfg = get_config()

    max_iter = cfg.relaxation.max_iterations
    threshold = cfg.relaxation.convergence_threshold
    ...
```

### Step 3: Add CLI Argument

In `src/main.py`:

```python
parser.add_argument(
    '--config',
    help='Path to custom configuration file (default: config/default_config.yaml)'
)

# Load config at startup
cfg = get_config(args.config)
```

## Hyperparameter Tuning

### Creating Experiment Configs

```bash
# Start with default config
cp config/default_config.yaml experiments/exp_001_high_precision.yaml

# Edit thresholds for higher precision
# match_score_threshold: 0.85 (was 0.75)
# weak_match_score_threshold: 0.70 (was 0.60)

# Run experiment
python src/main.py --input data/test_set --config experiments/exp_001_high_precision.yaml
```

### Parameter Sweep Script

```python
from config import Config
import numpy as np

# Define parameter grid
thresholds = np.arange(0.60, 0.90, 0.05)

for match_thresh in thresholds:
    cfg = Config()
    cfg.update('relaxation', 'match_score_threshold', match_thresh)
    cfg.update('relaxation', 'weak_match_score_threshold', match_thresh - 0.15)

    # Save experiment config
    cfg.save(f'experiments/sweep_match_{match_thresh:.2f}.yaml')

    # Run experiment
    # (integrate with test harness)
```

## Best Practices

### 1. Never Modify Default Config

Always create experiment-specific configs:

```bash
# Good
cp config/default_config.yaml experiments/my_experiment.yaml
# Edit my_experiment.yaml

# Bad - don't edit default config directly
vim config/default_config.yaml
```

### 2. Document Parameter Changes

Add comments to custom configs:

```yaml
relaxation:
  # Lowered from 0.75 to 0.70 for experiment EXP-042
  # Hypothesis: scroll fragments have weaker matches due to paper texture
  match_score_threshold: 0.70
```

### 3. Version Control Experiment Configs

```bash
git add experiments/exp_042_scroll_optimization.yaml
git commit -m "EXP-042: Lower match threshold for scroll fragments"
```

### 4. Use Config Summary for Logging

```python
cfg = get_config()
logger.info("Configuration:\n" + cfg.summary())
```

## Troubleshooting

### Problem: ConfigValidationError on Load

**Cause**: Parameter out of valid range or wrong type

**Solution**: Check the error message for which parameter is invalid, then fix in YAML:

```
ConfigValidationError: Parameter relaxation.match_score_threshold = 2.0
out of range [0.4, 1.0] (Match score threshold)
```

### Problem: Module Still Uses Hardcoded Constants

**Cause**: Module not yet integrated with config system

**Solution**: Follow integration guide above to replace constants with config access

### Problem: Config Changes Not Taking Effect

**Cause**: Using global singleton without reloading

**Solution**: Reload configuration after changes:

```python
from config import reload_config
reload_config('new_config.yaml')
```

## Parameter Reference

See `config/default_config.yaml` for complete parameter documentation with:
- Description of each parameter
- Expected range with min/max values
- Purpose and when to adjust
- Default value and rationale

## Testing

Run configuration system tests:

```bash
python scripts/test_config_system.py
```

This validates:
1. Default config loads successfully
2. All sections are accessible
3. Validation catches invalid values
4. Dynamic updates work correctly
5. Save/reload preserves values
6. Configuration summary generation
7. Singleton pattern functions correctly

## Future Work

### Planned Enhancements

1. **Environment Variable Override**
   ```bash
   ICBV_MATCH_THRESHOLD=0.80 python src/main.py --input data/test
   ```

2. **Config Inheritance**
   ```yaml
   extends: config/default_config.yaml
   relaxation:
     match_score_threshold: 0.80  # Override only this parameter
   ```

3. **Automatic Parameter Tuning**
   - Bayesian optimization over parameter space
   - Grid search with parallel evaluation
   - Genetic algorithm for multi-objective optimization

4. **Configuration Profiles**
   ```bash
   # Predefined profiles for common scenarios
   python src/main.py --profile pottery_sherds
   python src/main.py --profile scroll_fragments
   python src/main.py --profile wall_paintings
   ```

## References

- Course Material: Lectures 21-23 (preprocessing), 52-53 (relaxation), 71-72 (recognition)
- Research Papers: arXiv:2309.13512 (ensemble voting), arXiv:2511.12976 (discriminators)
- Implementation: `src/config.py`, `config/default_config.yaml`
