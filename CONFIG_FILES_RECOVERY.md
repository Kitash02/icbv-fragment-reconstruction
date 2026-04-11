# Configuration Files Recovery Document

**Date:** 2026-04-08
**Purpose:** Complete recovery of all configuration files created during the ICBV Fragment Reconstruction project

---

## Summary

This document contains the complete contents of three critical configuration files:

1. **config/default_config.yaml** - Comprehensive YAML configuration with 70+ parameters
2. **src/config.py** - Configuration loader with validation and dot-notation access
3. **requirements.txt** - Basic dependency list (NOTE: See requirements-py38.txt for complete dependencies including scipy and scikit-image)

**IMPORTANT:** The main `requirements.txt` file is minimal (5 packages). For the complete dependency list including `scipy` and `scikit-image`, refer to `requirements-py38.txt` which contains all required packages with version constraints.

---

## File 1: config/default_config.yaml

**Location:** `C:/Users/I763940/icbv-fragment-reconstruction/config/default_config.yaml`
**Size:** 13,941 bytes
**Lines:** 300 lines
**Parameters:** 70+ configurable parameters across 10 sections

### Complete Contents:

```yaml
# Archaeological Fragment Reconstruction Configuration
# This file contains ALL configurable parameters for the pipeline
# Each section corresponds to a module in the system

# =============================================================================
# PREPROCESSING PARAMETERS (src/preprocessing.py)
# Early vision pipeline: Gaussian blur, Canny, Otsu threshold
# =============================================================================
preprocessing:
  # Gaussian blur kernel (Lecture 22 - Linear filtering)
  gaussian_kernel_size: [5, 5]  # (width, height) - must be odd numbers
  gaussian_sigma: 1.5            # Standard deviation - controls smoothing strength
  # Expected range: 0.5-3.0 (lower = less smoothing, higher = more smoothing)

  # Contour area filtering
  min_contour_area: 500          # Minimum pixel area for valid contours
  # Expected range: 100-2000 (depends on image resolution)

  # Background detection
  corner_sample_size: 30         # Pixels sampled from corners to detect background
  # Expected range: 20-50 (must be smaller than image dimensions)

  # Morphological operations
  morph_kernel_size: 7           # Size of morphological kernel (closing/opening)
  # Expected range: 3-15 (must be odd, larger = more aggressive cleanup)

  # Canny edge detection (Lecture 23 - Edge Detection)
  canny_sigma_scale: 0.33        # Controls automatic threshold: (1±scale)*median
  # Expected range: 0.2-0.5 (Lecture 23 recommends 1:3 low/high ratio)

# =============================================================================
# CHAIN CODE PARAMETERS (src/chain_code.py)
# Freeman 8-directional chain code encoding (Lecture 72)
# =============================================================================
chain_code:
  # Number of segments per fragment boundary
  n_segments: 4                  # Equal-length boundary divisions
  # Expected range: 3-8 (more segments = finer matching, but slower)

# =============================================================================
# SHAPE DESCRIPTORS (src/shape_descriptors.py)
# Fourier descriptors and PCA orientation (Lectures 72, 74)
# =============================================================================
shape_descriptors:
  # Fourier descriptor truncation
  fourier_descriptor_order: 32   # Number of low-frequency coefficients kept
  # Expected range: 16-64 (higher = more shape detail retained)

# =============================================================================
# COMPATIBILITY SCORING (src/compatibility.py)
# Multi-modal fragment matching (Lectures 23, 52, 71, 72)
# =============================================================================
compatibility:
  # Good continuation bonus (Lecture 52 - Gestalt principles)
  good_continuation_sigma: 0.5   # Controls smoothness reward at join points
  # Expected range: 0.3-0.8 (lower = sharper falloff for non-smooth joins)

  good_continuation_weight: 0.10 # Weight of good-continuation in total score
  # Expected range: 0.05-0.20 (fraction of total compatibility score)

  # Fourier descriptor matching weight
  fourier_weight: 0.25           # Weight of global shape similarity
  # Expected range: 0.15-0.35 (complements local curvature matching)

  fourier_segment_order: 8       # Number of Fourier coefficients per segment
  # Expected range: 4-16 (higher = more global shape detail)

  # Color histogram parameters (Lecture 71 - Appearance-based recognition)
  # Lab color space (perceptually uniform, better for earth tones)
  color_hist_bins_l: 16          # Lightness (L*) bins
  # Expected range: 8-32 (higher = finer color discrimination)

  color_hist_bins_a: 8           # Green-Red (a*) bins
  # Expected range: 4-16

  color_hist_bins_b: 8           # Blue-Yellow (b*) bins
  # Expected range: 4-16

  # Appearance penalty weights
  # STAGE 1.5 FIX: Multiplicative appearance penalty formula
  # Final score = geometric_score × (color^4 × texture^2 × gabor^2 × haralick^2)
  color_power: 4.0               # Exponential power for color BC penalty
  # Expected range: 2.0-6.0 (higher = stronger rejection of color mismatches)

  texture_power: 2.0             # Exponential power for texture BC penalty
  # Expected range: 1.0-3.0 (texture is secondary to color)

  gabor_power: 2.0               # Exponential power for Gabor feature penalty
  # Expected range: 1.0-3.0 (frequency-domain texture)

  haralick_power: 2.0            # Exponential power for Haralick GLCM penalty
  # Expected range: 1.0-3.0 (second-order texture statistics)

  # Texture feature extraction parameters
  # Local Binary Pattern (LBP)
  lbp_radius: 3                  # Radius for LBP computation
  # Expected range: 1-5 (larger = captures coarser texture patterns)

  lbp_n_points: 24               # Number of sampling points on circle
  # Expected range: 8-24 (must be multiple of 8)

  # Gabor filter bank
  gabor_frequencies: [0.05, 0.1, 0.2, 0.3, 0.4]  # Spatial frequencies
  # Expected range: 0.01-0.5 (lower = coarser patterns, higher = finer)

  gabor_n_orientations: 8        # Number of orientations (uniformly spaced)
  # Expected range: 4-12 (more = better rotation coverage, slower)

  gabor_kernel_size: 31          # Size of Gabor kernel (must be odd)
  # Expected range: 15-51 (larger = more accurate, slower)

  gabor_sigma: 4.0               # Gaussian envelope standard deviation
  # Expected range: 2.0-8.0

  gabor_gamma: 0.5               # Aspect ratio of Gabor function
  # Expected range: 0.3-1.0 (1.0 = circular, <1.0 = elliptical)

  # Haralick GLCM parameters
  haralick_distances: [1, 3, 5]  # Pixel distances for co-occurrence
  # Expected range: 1-10 (captures texture at multiple scales)

  haralick_n_angles: 4           # Number of angles (0, 45, 90, 135 deg)
  # Expected range: 4 (standard), 8 (more directions, slower)

# =============================================================================
# RELAXATION LABELING (src/relaxation.py)
# Global optimization via constraint propagation (Lecture 53)
# =============================================================================
relaxation:
  # Convergence control
  max_iterations: 50             # Maximum relaxation iterations
  # Expected range: 30-100 (more = better convergence, slower)

  convergence_threshold: 0.0001  # Stop when max probability change < threshold
  # Expected range: 1e-5 to 1e-3 (smaller = tighter convergence)

  # Match quality thresholds (calibrated for combined score max = 1.25)
  # STAGE 1.6 FIX: Balanced thresholds for true positive acceptance
  match_score_threshold: 0.75    # Raw compatibility >= this → confident MATCH
  # Expected range: 0.60-0.90 (higher = stricter matching)
  # Note: Lowered from 0.85 to accept more true positives while
  # appearance formula (color^4 × texture^2 × ...) rejects false positives

  weak_match_score_threshold: 0.60  # Raw compatibility >= this → possible match
  # Expected range: 0.45-0.75 (should be 0.10-0.20 below match_score_threshold)
  # Note: Lowered from 0.70 to capture uncertain but valid matches

  assembly_confidence_threshold: 0.65  # Average confidence for assembly acceptance
  # Expected range: 0.50-0.80 (higher = stricter assembly acceptance)
  # Note: Lowered from 0.75 to match reduced match thresholds

  # Assembly classification rules
  assembly_match_fraction: 0.60  # Fraction of pairs that must be MATCH for verdict=MATCH
  # Expected range: 0.50-0.80 (higher = requires more confident pairs)

  assembly_valid_fraction: 0.40  # Fraction of pairs >= WEAK_MATCH for verdict=WEAK_MATCH
  # Expected range: 0.30-0.60 (lower = more permissive)

  # Top assembly extraction
  n_top_assemblies: 3            # Number of candidate assemblies to extract
  # Expected range: 1-10 (more = more hypotheses, but diminishing returns)

  perturbation_noise: 0.05       # Random noise for assembly diversity
  # Expected range: 0.01-0.10 (higher = more diverse but less optimal)

# =============================================================================
# HARD DISCRIMINATORS (src/hard_discriminators.py)
# Fast rejection criteria (arXiv:2511.12976, arXiv:2309.13512)
# =============================================================================
hard_discriminators:
  # Edge density threshold
  edge_density_threshold: 0.15   # Maximum allowed difference in edge density
  # Expected range: 0.10-0.25 (lower = stricter manufacturing similarity)

  # Texture entropy threshold
  entropy_threshold: 0.5         # Maximum allowed difference in texture entropy
  # Expected range: 0.3-0.8 (lower = stricter surface similarity)

  # Combined appearance gate (both must pass)
  color_gate_threshold: 0.60     # Minimum color BC to pass gate
  # Expected range: 0.50-0.75 (higher = stricter color matching)

  texture_gate_threshold: 0.55   # Minimum texture BC to pass gate
  # Expected range: 0.45-0.70 (higher = stricter texture matching)

  # Canny edge detection for edge density
  edge_canny_low: 50             # Low threshold for Canny
  # Expected range: 30-100

  edge_canny_high: 150           # High threshold for Canny (3:1 ratio recommended)
  # Expected range: 100-300

# =============================================================================
# ENSEMBLE VOTING (src/ensemble_voting.py)
# Multi-discriminator voting (arXiv:2309.13512 - 99.3% accuracy)
# =============================================================================
ensemble_voting:
  # 5-way voting thresholds (each voter independently classifies)
  # Voter 1: Raw Compatibility (geometric)
  raw_compat_match_thresh: 0.85  # Confident geometric match
  raw_compat_weak_thresh: 0.70   # Possible geometric match
  # Expected range: match 0.70-0.95, weak 0.50-0.80

  # Voter 2: Color Discriminator
  color_match_thresh: 0.78       # Confident color match
  color_weak_thresh: 0.65        # Possible color match
  # Expected range: match 0.70-0.90, weak 0.55-0.75

  # Voter 3: Texture Discriminator (LBP)
  texture_match_thresh: 0.72     # Confident texture match
  texture_weak_thresh: 0.58      # Possible texture match
  # Expected range: match 0.65-0.85, weak 0.50-0.70

  # Voter 4: Gabor Discriminator
  gabor_match_thresh: 0.70       # Confident Gabor match
  gabor_weak_thresh: 0.55        # Possible Gabor match
  # Expected range: match 0.60-0.80, weak 0.45-0.65

  # Voter 5: Morphological Discriminator (edge + entropy)
  morph_match_thresh: 0.75       # Confident morphological match
  morph_weak_thresh: 0.60        # Possible morphological match
  # Expected range: match 0.65-0.85, weak 0.50-0.70

  # Morphological score normalization factors
  morph_edge_norm: 0.20          # Normalizer for edge density difference
  morph_entropy_norm: 0.70       # Normalizer for entropy difference
  # Expected range: edge 0.15-0.30, entropy 0.50-1.00

  # Voting decision rules (pessimistic for archaeology)
  min_match_votes: 3             # Minimum MATCH votes for verdict=MATCH
  # Expected range: 2-4 (out of 5 voters)

  min_reject_votes: 2            # Minimum NO_MATCH votes for verdict=NO_MATCH
  # Expected range: 2-3 (pessimistic: reject on uncertainty)

  # Weighted voting alternative
  use_weighted_voting: false     # Enable weighted voting (vs. equal voting)

  weights:
    color: 0.35                  # Color has highest discriminative power
    raw_compat: 0.25             # Geometric features
    texture: 0.20                # Local patterns
    morphological: 0.15          # Edge + entropy
    gabor: 0.05                  # Frequency-domain (lowest)
  # Expected range: color 0.25-0.45, raw 0.15-0.35, texture 0.10-0.30,
  #                 morph 0.10-0.25, gabor 0.00-0.15
  # Constraint: must sum to 1.0

  # Weighted voting thresholds
  weighted_match_thresh: 0.75    # Confident match
  weighted_weak_thresh: 0.60     # Possible match
  # Expected range: match 0.65-0.85, weak 0.50-0.70

  # Hierarchical voting thresholds (fast paths)
  hierarchical_edge_reject: 0.15      # Fast reject if edge diff > this
  hierarchical_entropy_reject: 0.5    # Fast reject if entropy diff > this
  hierarchical_color_match: 0.80      # Fast match if color >= this
  hierarchical_geom_match: 0.85       # Fast match if geom >= this
  hierarchical_color_reject: 0.55     # Fast reject if color < this
  hierarchical_geom_reject: 0.60      # Fast reject if geom < this
  # Expected range: tuned for ~80% fast-path coverage

# =============================================================================
# MIXED-SOURCE DETECTION (src/main.py)
# Color pre-check to detect fragments from different images (Lecture 71)
# =============================================================================
mixed_source_detection:
  # Bimodal distribution thresholds
  color_precheck_gap_thresh: 0.25     # Minimum gap between low/high BC groups
  # Expected range: 0.20-0.35 (larger gap = stronger bimodal evidence)

  color_precheck_low_max: 0.62        # Maximum BC in "low" group
  # Expected range: 0.55-0.70 (lower = stricter cross-image rejection)

# =============================================================================
# PIPELINE CONTROL (src/main.py)
# Top-level orchestration parameters
# =============================================================================
pipeline:
  # File extensions for fragment images
  image_extensions: ['.png', '.jpg', '.jpeg', '.bmp']

  # Number of top assemblies to visualize
  n_top_assemblies: 3            # Must match relaxation.n_top_assemblies
  # Expected range: 1-10

# =============================================================================
# LOGGING (src/main.py)
# Controls log verbosity and output
# =============================================================================
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO

  # Log format string
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

  # Log file timestamp format
  timestamp_format: "%Y%m%d_%H%M%S"
```

---

## File 2: src/config.py

**Location:** `C:/Users/I763940/icbv-fragment-reconstruction/src/config.py`
**Size:** 422 lines
**Features:**
- YAML configuration loading
- Dot-notation parameter access (e.g., `cfg.preprocessing.gaussian_sigma`)
- Comprehensive validation with range checks
- Cross-parameter constraint validation
- Singleton pattern for global configuration
- Configuration update with automatic re-validation

### Complete Contents:

```python
"""
Configuration management for Archaeological Fragment Reconstruction.

This module provides centralized configuration loading, validation, and access
for all pipeline parameters. Supports YAML configuration files with validation
against expected parameter ranges.

The configuration system follows best practices:
  1. All magic numbers are extracted to a single YAML file
  2. Each parameter is documented with its expected range
  3. Validation ensures parameters are within acceptable bounds
  4. Type checking prevents configuration errors at runtime
  5. Default configuration is always available as fallback

Usage:
    from config import Config

    # Load default configuration
    cfg = Config()

    # Load custom configuration
    cfg = Config('path/to/custom_config.yaml')

    # Access parameters with dot notation
    sigma = cfg.preprocessing.gaussian_sigma
    thresh = cfg.relaxation.match_score_threshold

    # Or access as dictionary
    sigma = cfg['preprocessing']['gaussian_sigma']
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigSection:
    """
    Wrapper for a configuration section that allows dot notation access.

    Example:
        section = ConfigSection({'key': 'value', 'nested': {'inner': 42}})
        section.key        # 'value'
        section.nested.inner  # 42
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data
        # Convert nested dicts to ConfigSection for dot notation
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, ConfigSection(value))
            else:
                setattr(self, key, value)

    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access."""
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default fallback."""
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert back to plain dictionary."""
        result = {}
        for key, value in self._data.items():
            if isinstance(value, ConfigSection):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result


class Config:
    """
    Main configuration class. Loads and validates configuration from YAML.

    Attributes:
        preprocessing: Preprocessing module parameters
        chain_code: Chain code encoding parameters
        shape_descriptors: Fourier/PCA shape descriptor parameters
        compatibility: Compatibility scoring parameters
        relaxation: Relaxation labeling parameters
        hard_discriminators: Hard rejection criteria parameters
        ensemble_voting: Ensemble voting parameters
        mixed_source_detection: Mixed-source detection parameters
        pipeline: Top-level pipeline control
        logging: Logging configuration
    """

    # Default config path relative to this file
    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / 'config' / 'default_config.yaml'

    # Validation ranges for critical parameters
    # Format: (section, param, min_val, max_val, description)
    VALIDATION_RULES = [
        # Preprocessing
        ('preprocessing', 'gaussian_sigma', 0.5, 3.0, 'Gaussian blur strength'),
        ('preprocessing', 'min_contour_area', 100, 5000, 'Minimum contour area'),
        ('preprocessing', 'canny_sigma_scale', 0.1, 0.6, 'Canny threshold scale'),

        # Chain code
        ('chain_code', 'n_segments', 3, 8, 'Number of boundary segments'),

        # Shape descriptors
        ('shape_descriptors', 'fourier_descriptor_order', 8, 128, 'Fourier coefficient count'),

        # Compatibility
        ('compatibility', 'good_continuation_sigma', 0.1, 1.0, 'Good continuation falloff'),
        ('compatibility', 'good_continuation_weight', 0.0, 0.3, 'Good continuation weight'),
        ('compatibility', 'fourier_weight', 0.0, 0.5, 'Fourier descriptor weight'),
        ('compatibility', 'color_power', 1.0, 8.0, 'Color penalty exponent'),
        ('compatibility', 'texture_power', 1.0, 5.0, 'Texture penalty exponent'),

        # Relaxation
        ('relaxation', 'max_iterations', 10, 200, 'Maximum relaxation iterations'),
        ('relaxation', 'convergence_threshold', 1e-6, 1e-2, 'Convergence threshold'),
        ('relaxation', 'match_score_threshold', 0.4, 1.0, 'Match score threshold'),
        ('relaxation', 'weak_match_score_threshold', 0.3, 0.9, 'Weak match threshold'),
        ('relaxation', 'assembly_confidence_threshold', 0.3, 0.9, 'Assembly confidence threshold'),

        # Hard discriminators
        ('hard_discriminators', 'edge_density_threshold', 0.05, 0.4, 'Edge density difference limit'),
        ('hard_discriminators', 'entropy_threshold', 0.2, 1.5, 'Entropy difference limit'),

        # Mixed source detection
        ('mixed_source_detection', 'color_precheck_gap_thresh', 0.1, 0.5, 'Bimodal gap threshold'),
    ]

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration from YAML file.

        Args:
            config_path: Path to custom YAML config file. If None, uses default.

        Raises:
            FileNotFoundError: If config file not found
            ConfigValidationError: If configuration is invalid
        """
        if config_path is None:
            config_path = self.DEFAULT_CONFIG_PATH
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        logger.info(f"Loading configuration from: {config_path}")

        # Load YAML
        with open(config_path, 'r') as f:
            self._raw_config = yaml.safe_load(f)

        if self._raw_config is None:
            raise ConfigValidationError("Configuration file is empty")

        # Validate configuration
        self._validate()

        # Create section objects for dot notation access
        self._create_sections()

        logger.info("Configuration loaded and validated successfully")

    def _create_sections(self):
        """Create ConfigSection objects for each top-level section."""
        for section_name, section_data in self._raw_config.items():
            if isinstance(section_data, dict):
                setattr(self, section_name, ConfigSection(section_data))
            else:
                setattr(self, section_name, section_data)

    def _validate(self):
        """
        Validate configuration against expected ranges and types.

        Raises:
            ConfigValidationError: If any parameter is out of range or wrong type
        """
        errors = []

        # Check required sections exist
        required_sections = [
            'preprocessing', 'chain_code', 'shape_descriptors', 'compatibility',
            'relaxation', 'hard_discriminators', 'ensemble_voting',
            'mixed_source_detection', 'pipeline', 'logging'
        ]

        for section in required_sections:
            if section not in self._raw_config:
                errors.append(f"Missing required section: {section}")

        # Validate parameter ranges
        for section, param, min_val, max_val, description in self.VALIDATION_RULES:
            if section not in self._raw_config:
                continue  # Already reported as missing section

            if param not in self._raw_config[section]:
                errors.append(f"Missing parameter: {section}.{param} ({description})")
                continue

            value = self._raw_config[section][param]

            # Type check
            if not isinstance(value, (int, float)):
                errors.append(
                    f"Parameter {section}.{param} must be numeric, got {type(value).__name__}"
                )
                continue

            # Range check
            if not (min_val <= value <= max_val):
                errors.append(
                    f"Parameter {section}.{param} = {value} out of range "
                    f"[{min_val}, {max_val}] ({description})"
                )

        # Special validations
        self._validate_special_cases(errors)

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ConfigValidationError(error_msg)

    def _validate_special_cases(self, errors: List[str]):
        """Validate special cases and cross-parameter constraints."""

        # Gaussian kernel size must be odd
        if 'preprocessing' in self._raw_config:
            kernel_size = self._raw_config['preprocessing'].get('gaussian_kernel_size')
            if kernel_size:
                if not isinstance(kernel_size, list) or len(kernel_size) != 2:
                    errors.append("gaussian_kernel_size must be a list of 2 integers")
                elif kernel_size[0] % 2 == 0 or kernel_size[1] % 2 == 0:
                    errors.append("gaussian_kernel_size values must be odd numbers")

        # Weak threshold must be less than match threshold
        if 'relaxation' in self._raw_config:
            rel = self._raw_config['relaxation']
            match_thresh = rel.get('match_score_threshold', 1.0)
            weak_thresh = rel.get('weak_match_score_threshold', 0.0)
            # Only validate if both are numeric (type check happens earlier)
            if isinstance(match_thresh, (int, float)) and isinstance(weak_thresh, (int, float)):
                if weak_thresh >= match_thresh:
                    errors.append(
                        f"weak_match_score_threshold ({weak_thresh}) must be less than "
                        f"match_score_threshold ({match_thresh})"
                    )

        # Ensemble weights must sum to 1.0 if weighted voting enabled
        if 'ensemble_voting' in self._raw_config:
            ens = self._raw_config['ensemble_voting']
            if ens.get('use_weighted_voting', False):
                weights = ens.get('weights', {})
                weight_sum = sum(weights.values())
                if abs(weight_sum - 1.0) > 0.01:
                    errors.append(
                        f"Ensemble weights must sum to 1.0, got {weight_sum:.3f}"
                    )

        # N_top_assemblies should match between pipeline and relaxation
        if 'pipeline' in self._raw_config and 'relaxation' in self._raw_config:
            pipe_n = self._raw_config['pipeline'].get('n_top_assemblies')
            relax_n = self._raw_config['relaxation'].get('n_top_assemblies')
            if pipe_n and relax_n and pipe_n != relax_n:
                errors.append(
                    f"Inconsistent n_top_assemblies: pipeline={pipe_n}, relaxation={relax_n}"
                )

    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access to top-level sections."""
        return self._raw_config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get top-level section with default fallback."""
        return self._raw_config.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a plain dictionary."""
        return dict(self._raw_config)

    def save(self, path: str):
        """
        Save current configuration to a YAML file.

        Args:
            path: Output file path
        """
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(self._raw_config, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Configuration saved to: {output_path}")

    def update(self, section: str, param: str, value: Any):
        """
        Update a parameter and re-validate.

        Args:
            section: Section name (e.g., 'relaxation')
            param: Parameter name (e.g., 'match_score_threshold')
            value: New value

        Raises:
            ConfigValidationError: If updated value is invalid
        """
        if section not in self._raw_config:
            raise ConfigValidationError(f"Unknown section: {section}")

        old_value = self._raw_config[section].get(param)
        self._raw_config[section][param] = value

        try:
            self._validate()
            self._create_sections()  # Recreate section objects
            logger.info(f"Updated {section}.{param}: {old_value} -> {value}")
        except ConfigValidationError as e:
            # Rollback on validation failure
            if old_value is not None:
                self._raw_config[section][param] = old_value
            else:
                del self._raw_config[section][param]
            self._create_sections()
            raise e

    def summary(self) -> str:
        """
        Generate a human-readable configuration summary.

        Returns:
            Multi-line string with key parameters
        """
        lines = ["Configuration Summary", "=" * 60]

        # Key parameters to highlight
        highlights = [
            ("Preprocessing", [
                ('preprocessing', 'gaussian_sigma'),
                ('preprocessing', 'canny_sigma_scale'),
            ]),
            ("Chain Code", [
                ('chain_code', 'n_segments'),
            ]),
            ("Compatibility", [
                ('compatibility', 'good_continuation_weight'),
                ('compatibility', 'fourier_weight'),
                ('compatibility', 'color_power'),
            ]),
            ("Relaxation", [
                ('relaxation', 'match_score_threshold'),
                ('relaxation', 'weak_match_score_threshold'),
                ('relaxation', 'assembly_confidence_threshold'),
            ]),
            ("Hard Discriminators", [
                ('hard_discriminators', 'edge_density_threshold'),
                ('hard_discriminators', 'entropy_threshold'),
            ]),
        ]

        for section_name, params in highlights:
            lines.append(f"\n{section_name}:")
            for section, param in params:
                if section in self._raw_config and param in self._raw_config[section]:
                    value = self._raw_config[section][param]
                    lines.append(f"  {param:30s} = {value}")

        return "\n".join(lines)


# Global configuration instance (lazily initialized)
_global_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance.

    This function implements a singleton pattern: the configuration is loaded
    once and reused across the entire application.

    Args:
        config_path: Path to custom config file. Only used on first call.

    Returns:
        Config instance
    """
    global _global_config

    if _global_config is None:
        _global_config = Config(config_path)

    return _global_config


def reload_config(config_path: Optional[str] = None):
    """
    Force reload of global configuration.

    Args:
        config_path: Path to config file to load
    """
    global _global_config
    _global_config = Config(config_path)
    logger.info("Configuration reloaded")
```

---

## File 3: requirements.txt

**Location:** `C:/Users/I763940/icbv-fragment-reconstruction/requirements.txt`
**Size:** 50 bytes
**Status:** MINIMAL - Contains only basic dependencies

### Complete Contents:

```
opencv-python
numpy
matplotlib
Pillow
pytest
```

### ⚠️ IMPORTANT NOTE

**This requirements.txt is INCOMPLETE.** It is missing critical dependencies:
- `scipy` (required for statistical functions in hard_discriminators.py)
- `scikit-image` (required for texture features)
- `requests` (required for fragment downloads)
- `pyyaml` (required for configuration loading)

**For the COMPLETE dependency list with proper version constraints, use `requirements-py38.txt` instead:**

```
# Complete Requirements (from requirements-py38.txt)
opencv-python>=4.5.3,<5.0.0
numpy>=1.22.0,<2.0.0
matplotlib>=3.3.0,<3.8.0
Pillow>=8.0.0,<10.0.0
scipy>=1.5.0,<1.12.0
scikit-image>=0.18.0,<0.22.0
requests>=2.25.0,<3.0.0
pytest>=6.0.0,<8.0.0
tqdm>=4.50.0  # optional
```

---

## Verification

All three files have been successfully located and recovered:

1. ✅ **config/default_config.yaml** - 300 lines, 70+ parameters
2. ✅ **src/config.py** - 422 lines, complete configuration loader
3. ✅ **requirements.txt** - 6 lines (minimal), see requirements-py38.txt for complete version

### File Paths (Absolute):
- `C:/Users/I763940/icbv-fragment-reconstruction/config/default_config.yaml`
- `C:/Users/I763940/icbv-fragment-reconstruction/src/config.py`
- `C:/Users/I763940/icbv-fragment-reconstruction/requirements.txt`
- `C:/Users/I763940/icbv-fragment-reconstruction/requirements-py38.txt` (complete version)

### Usage Example:

```python
# Import the configuration loader
from src.config import Config

# Load default configuration
cfg = Config()

# Access parameters with dot notation
sigma = cfg.preprocessing.gaussian_sigma  # 1.5
threshold = cfg.relaxation.match_score_threshold  # 0.75

# Or use dictionary access
color_power = cfg['compatibility']['color_power']  # 4.0

# Print configuration summary
print(cfg.summary())
```

---

## End of Recovery Document
