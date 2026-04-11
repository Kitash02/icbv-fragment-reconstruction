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
