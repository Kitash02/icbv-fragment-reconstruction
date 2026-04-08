# Dependency Installation Guide
## ICBV Fragment Reconstruction System

**Last Updated**: 2026-04-08

---

## Quick Start

### For Python 3.10+ (Recommended)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python -c "import cv2, numpy, matplotlib, PIL, scipy, skimage; print('✓ All dependencies installed')"
```

### For Python 3.8-3.9 (Legacy)

```bash
# Use Python 3.8-compatible versions
pip install -r requirements-py38.txt
```

---

## Verification

### Test Core Imports

```bash
python -c "
import cv2
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import scipy
import skimage
print('✓ opencv-python:', cv2.__version__)
print('✓ numpy:', np.__version__)
print('✓ matplotlib:', plt.matplotlib.__version__)
print('✓ Pillow:', Image.__version__)
print('✓ scipy:', scipy.__version__)
print('✓ scikit-image:', skimage.__version__)
"
```

Expected output:
```
✓ opencv-python: 4.13.0
✓ numpy: 2.4.4
✓ matplotlib: 3.10.8
✓ Pillow: 12.2.0
✓ scipy: 1.17.1
✓ scikit-image: 0.26.0
```

### Run Test Suite

```bash
python -m pytest tests/ -v
```

### Run Sample Pipeline

```bash
python src/main.py --input data/sample --output outputs/test --log outputs/logs
```

---

## Security Audit

### Install Security Scanner

```bash
pip install pip-audit
```

### Run Security Check

```bash
pip-audit
```

Expected result: Only pip/setuptools vulnerabilities (build-time only, safe to ignore for runtime).

---

## Troubleshooting

### ImportError: No module named 'scipy'

**Cause**: scipy was missing from original requirements.txt
**Fix**: Update requirements.txt and reinstall:
```bash
pip install scipy>=1.16.0
```

### ImportError: No module named 'skimage'

**Cause**: scikit-image was missing from original requirements.txt
**Fix**: Update requirements.txt and reinstall:
```bash
pip install scikit-image>=0.26.0
```

### Version Conflicts

**Symptom**: Package installation fails with dependency conflicts
**Fix**: Use clean virtual environment:
```bash
rm -rf venv  # or rmdir /s venv on Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Python 3.8 Not Supported

**Symptom**: "Requires Python 3.9+" errors
**Fix**: Use Python 3.8-compatible versions:
```bash
pip install -r requirements-py38.txt
```

Or upgrade Python:
```bash
# Check current version
python --version

# If < 3.10, install Python 3.11 or later
# Download from: https://www.python.org/downloads/
```

### Security Vulnerabilities

**Check for vulnerabilities**:
```bash
pip-audit
```

**Update vulnerable packages**:
```bash
pip install --upgrade Pillow requests urllib3
```

**Update pip and setuptools** (build-time tools):
```bash
python -m pip install --upgrade pip setuptools
```

---

## Dependency Details

### Core Dependencies (Runtime Required)

| Package | Version | Purpose | File Size |
|---------|---------|---------|-----------|
| opencv-python | >=4.13.0 | Image processing, contour detection | ~60 MB |
| numpy | >=1.26.0 | Numerical operations | ~25 MB |
| matplotlib | >=3.10.0 | Visualization, plotting | ~35 MB |
| Pillow | >=12.1.1 | Image I/O, format conversion | ~3 MB |
| scipy | >=1.16.0 | Statistical functions (entropy) | ~40 MB |
| scikit-image | >=0.26.0 | Texture features (LBP, GLCM) | ~30 MB |
| requests | >=2.33.0 | HTTP downloads (scripts) | ~500 KB |

**Total**: ~200 MB

### Testing Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=9.0.0 | Unit/integration testing |

### Optional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| tqdm | >=4.67.0 | Progress bars (scripts) |

---

## Installation Time Estimates

| Environment | Time (approx.) |
|-------------|----------------|
| Fresh virtual environment | 2-5 minutes |
| Existing environment (upgrade) | 1-2 minutes |
| Global system installation | 3-8 minutes |

*Times vary based on internet speed and system performance*

---

## Platform-Specific Notes

### Windows

- Use `venv\Scripts\activate` to activate virtual environment
- Use backslashes in paths: `python src\main.py`
- May need to enable execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Linux/Mac

- Use `source venv/bin/activate` to activate virtual environment
- Use forward slashes in paths: `python src/main.py`
- May need to install system dependencies for opencv-python:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install libgl1-mesa-glx libglib2.0-0

  # macOS
  brew install opencv
  ```

### ARM Architectures (Apple M1/M2, Raspberry Pi)

Some packages may require compilation:
```bash
# Install build tools first
pip install --upgrade pip setuptools wheel

# Then install requirements
pip install -r requirements.txt
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Dependencies

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Security audit
      run: |
        pip install pip-audit
        pip-audit

    - name: Run tests
      run: pytest tests/
```

---

## Dependency Management Best Practices

### Version Pinning Strategy

The requirements.txt uses **compatible release** constraints (`>=X.Y.Z,<X+1.0.0`):

- **Major version**: Locked (breaking changes)
- **Minor version**: Flexible (new features)
- **Patch version**: Flexible (bug fixes)

Example: `numpy>=1.26.0,<3.0.0`
- ✓ Allows: 1.26.1, 1.27.0, 2.0.0, 2.5.3
- ✗ Blocks: 3.0.0, 1.25.0

### Lock File (Optional)

For exact reproducibility, generate a lock file:

```bash
pip freeze > requirements.lock
```

Install from lock file:
```bash
pip install -r requirements.lock
```

### Separate Development Dependencies

Create `requirements-dev.txt`:
```
-r requirements.txt
pytest>=9.0.0
pip-audit>=2.10.0
black>=24.0.0
flake8>=7.0.0
mypy>=1.8.0
```

---

## Security Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Security audit | Weekly | `pip-audit` |
| Package updates | Monthly | `pip list --outdated` |
| Major version review | Quarterly | Manual review |
| Full dependency rebuild | Annually | Clean venv + reinstall |

---

## Support

For dependency issues:

1. **Check this guide** for common solutions
2. **Review audit report**: `outputs/implementation/DEPENDENCY_AUDIT.md`
3. **Check package documentation**: [pypi.org](https://pypi.org)
4. **Report issues**: Include output of:
   ```bash
   python --version
   pip list
   pip-audit
   ```

---

## Changelog

### 2026-04-08 - Major Update
- ✅ Added missing dependencies: scipy, scikit-image
- ✅ Added version constraints to all packages
- ✅ Fixed 12 security vulnerabilities
- ✅ Created Python 3.8 compatibility file
- ✅ Tested clean installation
- ✅ Documented all dependencies

### Previous Version
- ❌ No version pins
- ❌ Missing scipy
- ❌ Missing scikit-image
- ❌ No security auditing
- ❌ No compatibility documentation

---

**Total Installation Time**: 15 minutes (estimated)
**Maintenance Effort**: Low (monthly security checks recommended)
