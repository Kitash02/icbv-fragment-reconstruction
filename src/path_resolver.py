"""
Path resolver module for handling file paths in both development and frozen (PyInstaller) modes.

This module provides utilities to correctly resolve paths whether the application is:
- Running in development mode (normal Python execution)
- Running as a frozen executable (PyInstaller bundled .exe)

Key concepts:
- Bundle root: Where the application code and bundled resources are located
- User directories: Writable locations for outputs, logs, and user data
- Resource paths: Read-only resources like configs and sample data

Author: ICBV Fragment Reconstruction Project
"""

import os
import sys
from pathlib import Path
from typing import Optional


def is_frozen() -> bool:
    """
    Check if the application is running as a PyInstaller frozen executable.

    Returns:
        bool: True if running as frozen executable, False if running in dev mode
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_bundle_root() -> Path:
    """
    Get the root directory of the application bundle.

    In frozen mode: Returns sys._MEIPASS (PyInstaller's temporary extraction folder)
    In dev mode: Returns the project root directory (parent of src/)

    Returns:
        Path: The bundle root directory
    """
    if is_frozen():
        # PyInstaller extracts to a temporary folder and sets _MEIPASS
        return Path(sys._MEIPASS)
    else:
        # In development, go up one level from src/ to project root
        return Path(__file__).parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    Get the absolute path to a bundled resource.

    Use this for read-only resources that are bundled with the application,
    such as configuration files, sample data, templates, etc.

    Args:
        relative_path: Path relative to the bundle root (e.g., "config/settings.json")

    Returns:
        Path: Absolute path to the resource

    Example:
        >>> get_resource_path("config/settings.json")
        Path("C:/Users/.../icbv-fragment-reconstruction/config/settings.json")
    """
    return get_bundle_root() / relative_path


def get_user_base_dir() -> Path:
    """
    Get the base directory for user-writable files.

    In frozen mode: Returns ~/Documents/ICBV_FragmentReconstruction/
    In dev mode: Returns the project root directory

    Returns:
        Path: The user base directory
    """
    if is_frozen():
        # Use Documents folder for user data when running as executable
        user_base = Path.home() / "Documents" / "ICBV_FragmentReconstruction"
        # Ensure the directory exists
        user_base.mkdir(parents=True, exist_ok=True)
        return user_base
    else:
        # In development, use project root
        return get_bundle_root()


def get_output_dir() -> Path:
    """
    Get the directory for output files (reconstructed images, etc.).

    In frozen mode: ~/Documents/ICBV_FragmentReconstruction/output/
    In dev mode: <project_root>/output/

    The directory is created if it doesn't exist.

    Returns:
        Path: The output directory
    """
    output_dir = get_user_base_dir() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_log_dir() -> Path:
    """
    Get the directory for log files.

    In frozen mode: ~/Documents/ICBV_FragmentReconstruction/logs/
    In dev mode: <project_root>/logs/

    The directory is created if it doesn't exist.

    Returns:
        Path: The logs directory
    """
    log_dir = get_user_base_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_sample_data_dir() -> Path:
    """
    Get the directory containing sample fragment images.

    This is a read-only resource bundled with the application.

    Returns:
        Path: Path to data/sample/ directory
    """
    return get_resource_path("data/sample")


def get_config_file(filename: str) -> Path:
    """
    Get the path to a specific configuration file.

    Configuration files are read-only resources bundled with the application.

    Args:
        filename: Name of the config file (e.g., "settings.json", "algorithms.yaml")

    Returns:
        Path: Absolute path to the configuration file

    Example:
        >>> get_config_file("settings.json")
        Path("C:/Users/.../icbv-fragment-reconstruction/config/settings.json")
    """
    return get_resource_path(f"config/{filename}")


def get_docs_file(filename: str) -> Optional[Path]:
    """
    Get the path to a documentation file if it exists.

    Documentation files are read-only resources bundled with the application.

    Args:
        filename: Name of the documentation file (e.g., "README.md", "docs/EXPERIMENT_DOCUMENTATION.md")

    Returns:
        Path: Absolute path to the documentation file if it exists, None otherwise

    Example:
        >>> get_docs_file("README.md")
        Path("C:/Users/.../icbv-fragment-reconstruction/README.md")
    """
    doc_path = get_resource_path(filename)
    return doc_path if doc_path.exists() else None


def get_data_dir() -> Path:
    """
    Get the main data directory (for bundled read-only data).

    Returns:
        Path: Path to data/ directory
    """
    return get_resource_path("data")


def get_temp_dir() -> Path:
    """
    Get a temporary directory for intermediate processing files.

    In frozen mode: ~/Documents/ICBV_FragmentReconstruction/temp/
    In dev mode: <project_root>/temp/

    The directory is created if it doesn't exist.

    Returns:
        Path: The temporary directory
    """
    temp_dir = get_user_base_dir() / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_executable_dir() -> Path:
    """
    Get the directory containing the executable or main script.

    In frozen mode: Returns the directory containing the .exe file
    In dev mode: Returns the project root directory

    Returns:
        Path: The executable directory
    """
    if is_frozen():
        # sys.executable points to the .exe file
        return Path(sys.executable).parent
    else:
        return get_bundle_root()


def ensure_user_directories() -> None:
    """
    Ensure all user-writable directories exist.

    Call this during application initialization to create necessary folders.
    """
    get_output_dir()
    get_log_dir()
    get_temp_dir()


def get_path_diagnostics() -> dict:
    """
    Get diagnostic information about all resolved paths.

    Useful for debugging path resolution issues.

    Returns:
        dict: Dictionary containing path information and diagnostic data
    """
    diagnostics = {
        "is_frozen": is_frozen(),
        "sys.executable": sys.executable,
        "sys.argv[0]": sys.argv[0] if sys.argv else None,
        "bundle_root": str(get_bundle_root()),
        "bundle_root_exists": get_bundle_root().exists(),
        "user_base_dir": str(get_user_base_dir()),
        "user_base_dir_exists": get_user_base_dir().exists(),
        "output_dir": str(get_output_dir()),
        "output_dir_exists": get_output_dir().exists(),
        "log_dir": str(get_log_dir()),
        "log_dir_exists": get_log_dir().exists(),
        "temp_dir": str(get_temp_dir()),
        "temp_dir_exists": get_temp_dir().exists(),
        "sample_data_dir": str(get_sample_data_dir()),
        "sample_data_dir_exists": get_sample_data_dir().exists(),
        "executable_dir": str(get_executable_dir()),
        "executable_dir_exists": get_executable_dir().exists(),
    }

    # Add _MEIPASS if frozen
    if is_frozen():
        diagnostics["sys._MEIPASS"] = sys._MEIPASS

    # Check for config directory
    config_dir = get_resource_path("config")
    diagnostics["config_dir"] = str(config_dir)
    diagnostics["config_dir_exists"] = config_dir.exists()

    # Check for data directory
    data_dir = get_data_dir()
    diagnostics["data_dir"] = str(data_dir)
    diagnostics["data_dir_exists"] = data_dir.exists()

    return diagnostics


def print_diagnostics() -> None:
    """
    Print diagnostic information about path resolution.

    Useful for debugging during development or troubleshooting issues.
    """
    diagnostics = get_path_diagnostics()

    print("=" * 70)
    print("PATH RESOLVER DIAGNOSTICS")
    print("=" * 70)
    print(f"Execution Mode: {'FROZEN (PyInstaller EXE)' if diagnostics['is_frozen'] else 'DEVELOPMENT (Python)'}")
    print()

    print("System Information:")
    print(f"  sys.executable: {diagnostics['sys.executable']}")
    print(f"  sys.argv[0]: {diagnostics['sys.argv[0]']}")
    if 'sys._MEIPASS' in diagnostics:
        print(f"  sys._MEIPASS: {diagnostics['sys._MEIPASS']}")
    print()

    print("Bundle/Project Paths (Read-Only Resources):")
    print(f"  Bundle Root: {diagnostics['bundle_root']}")
    print(f"    Exists: {diagnostics['bundle_root_exists']}")
    print(f"  Config Dir: {diagnostics['config_dir']}")
    print(f"    Exists: {diagnostics['config_dir_exists']}")
    print(f"  Data Dir: {diagnostics['data_dir']}")
    print(f"    Exists: {diagnostics['data_dir_exists']}")
    print(f"  Sample Data Dir: {diagnostics['sample_data_dir']}")
    print(f"    Exists: {diagnostics['sample_data_dir_exists']}")
    print()

    print("User Paths (Writable Directories):")
    print(f"  User Base Dir: {diagnostics['user_base_dir']}")
    print(f"    Exists: {diagnostics['user_base_dir_exists']}")
    print(f"  Output Dir: {diagnostics['output_dir']}")
    print(f"    Exists: {diagnostics['output_dir_exists']}")
    print(f"  Log Dir: {diagnostics['log_dir']}")
    print(f"    Exists: {diagnostics['log_dir_exists']}")
    print(f"  Temp Dir: {diagnostics['temp_dir']}")
    print(f"    Exists: {diagnostics['temp_dir_exists']}")
    print()

    print("Executable Location:")
    print(f"  Executable Dir: {diagnostics['executable_dir']}")
    print(f"    Exists: {diagnostics['executable_dir_exists']}")
    print("=" * 70)


if __name__ == "__main__":
    # When run directly, print diagnostics
    print_diagnostics()
