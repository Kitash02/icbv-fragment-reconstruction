"""
Detailed EXE Package Inspection Report
Creates a comprehensive report of the built EXE package
"""
import os
from pathlib import Path
import json

def get_dir_size(path):
    """Calculate directory size"""
    total = 0
    try:
        for entry in Path(path).rglob('*'):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except (PermissionError, OSError):
                    pass
    except Exception:
        pass
    return total

def format_size(bytes):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def count_files_by_extension(root_path):
    """Count files by extension"""
    ext_count = {}
    for entry in Path(root_path).rglob('*'):
        if entry.is_file():
            ext = entry.suffix.lower() or '(no extension)'
            ext_count[ext] = ext_count.get(ext, 0) + 1
    return ext_count

def main():
    print("="*70)
    print("FRAGMENT RECONSTRUCTION EXE - DETAILED PACKAGE REPORT")
    print("="*70)
    print()

    dist_dir = Path("dist/FragmentReconstruction")

    if not dist_dir.exists():
        print("[ERROR] Distribution directory not found!")
        return

    # 1. EXE File Analysis
    print("1. EXE FILE ANALYSIS")
    print("-" * 70)
    exe_path = dist_dir / "FragmentReconstruction.exe"
    if exe_path.exists():
        size = exe_path.stat().st_size
        print(f"   File: {exe_path.name}")
        print(f"   Size: {format_size(size)}")
        print(f"   Path: {exe_path.resolve()}")
        print(f"   Exists: YES")
    else:
        print("   [ERROR] EXE file not found!")
    print()

    # 2. Package Structure
    print("2. PACKAGE STRUCTURE")
    print("-" * 70)
    internal_dir = dist_dir / "_internal"

    if internal_dir.exists():
        print(f"   _internal directory: EXISTS")

        # Check key subdirectories
        key_dirs = ['data', 'config', 'numpy', 'cv2', 'PIL', 'matplotlib', 'scipy', 'src']
        for dir_name in key_dirs:
            dir_path = internal_dir / dir_name
            if dir_path.exists():
                size = get_dir_size(dir_path)
                file_count = sum(1 for _ in dir_path.rglob('*') if _.is_file())
                print(f"   - {dir_name:20s}: {format_size(size):>10s} ({file_count:>4d} files)")
            else:
                print(f"   - {dir_name:20s}: NOT FOUND")
    else:
        print("   [ERROR] _internal directory not found!")
    print()

    # 3. Sample Data
    print("3. SAMPLE DATA")
    print("-" * 70)
    sample_dir = internal_dir / "data" / "sample"
    if sample_dir.exists():
        sample_files = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.jpg"))
        print(f"   Sample directory: EXISTS")
        print(f"   Sample images: {len(sample_files)}")
        for img in sample_files[:10]:  # Show first 10
            size = img.stat().st_size
            print(f"   - {img.name:30s} {format_size(size):>10s}")
        if len(sample_files) > 10:
            print(f"   ... and {len(sample_files) - 10} more files")
    else:
        print("   [ERROR] Sample directory not found!")
    print()

    # 4. Configuration Files
    print("4. CONFIGURATION FILES")
    print("-" * 70)
    config_dir = internal_dir / "config"
    if config_dir.exists():
        config_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
        print(f"   Config directory: EXISTS")
        print(f"   Config files: {len(config_files)}")
        for cfg in config_files:
            size = cfg.stat().st_size
            print(f"   - {cfg.name:30s} {format_size(size):>10s}")
    else:
        print("   [ERROR] Config directory not found!")
    print()

    # 5. Dependencies Check
    print("5. PYTHON DEPENDENCIES")
    print("-" * 70)
    deps = ['numpy', 'cv2', 'PIL', 'matplotlib', 'scipy', 'yaml', 'tkinter']
    for dep in deps:
        dep_path = internal_dir / dep
        if dep_path.exists():
            if dep_path.is_dir():
                size = get_dir_size(dep_path)
                print(f"   {dep:20s}: EXISTS ({format_size(size)})")
            else:
                size = dep_path.stat().st_size
                print(f"   {dep:20s}: EXISTS ({format_size(size)})")
        else:
            print(f"   {dep:20s}: NOT FOUND")
    print()

    # 6. File Statistics
    print("6. FILE STATISTICS")
    print("-" * 70)
    if internal_dir.exists():
        ext_count = count_files_by_extension(internal_dir)

        total_files = sum(ext_count.values())
        total_size = get_dir_size(internal_dir)

        print(f"   Total files: {total_files}")
        print(f"   Total size: {format_size(total_size)}")
        print()
        print("   File types:")

        # Sort by count
        sorted_ext = sorted(ext_count.items(), key=lambda x: x[1], reverse=True)
        for ext, count in sorted_ext[:15]:  # Show top 15
            print(f"   - {ext:20s}: {count:>5d} files")

        if len(sorted_ext) > 15:
            other_count = sum(count for ext, count in sorted_ext[15:])
            print(f"   - {'(others)':20s}: {other_count:>5d} files")
    print()

    # 7. Total Package Size
    print("7. TOTAL PACKAGE SIZE")
    print("-" * 70)
    if dist_dir.exists():
        total_size = get_dir_size(dist_dir)
        print(f"   Complete package: {format_size(total_size)}")

        exe_size = exe_path.stat().st_size if exe_path.exists() else 0
        internal_size = get_dir_size(internal_dir) if internal_dir.exists() else 0

        print(f"   - EXE file:      {format_size(exe_size)}")
        print(f"   - _internal:     {format_size(internal_size)}")
    print()

    # 8. Critical Files Check
    print("8. CRITICAL FILES CHECK")
    print("-" * 70)
    critical_files = [
        "_internal/base_library.zip",
        "_internal/python311.dll",
        "_internal/_tkinter.pyd",
        "_internal/config/default.yaml",
    ]

    for file_path in critical_files:
        full_path = dist_dir / file_path
        status = "EXISTS" if full_path.exists() else "MISSING"
        print(f"   {file_path:45s}: {status}")
    print()

    # 9. Verification Summary
    print("9. VERIFICATION SUMMARY")
    print("-" * 70)

    checks = [
        ("EXE file exists", exe_path.exists()),
        ("_internal directory exists", internal_dir.exists()),
        ("Sample data present", (internal_dir / "data" / "sample").exists()),
        ("Config files present", (internal_dir / "config").exists()),
        ("NumPy bundled", (internal_dir / "numpy").exists()),
        ("OpenCV bundled", (internal_dir / "cv2").exists()),
        ("PIL bundled", (internal_dir / "PIL").exists()),
        ("Matplotlib bundled", (internal_dir / "matplotlib").exists()),
        ("SciPy bundled", (internal_dir / "scipy").exists()),
    ]

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    for check_name, result in checks:
        status = "[PASS]" if result else "[FAIL]"
        print(f"   {status} {check_name}")

    print()
    print(f"   Score: {passed}/{total} checks passed")

    if passed == total:
        print()
        print("   [SUCCESS] Package appears complete and ready for distribution!")
    else:
        print()
        print("   [WARNING] Some checks failed. Review the package before distribution.")

    print()
    print("="*70)

if __name__ == "__main__":
    main()
