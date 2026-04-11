# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Fragment Reconstruction GUI application.

This spec file configures the build process to create a standalone Windows executable
that includes all necessary dependencies, data files, and documentation.

Build command: pyinstaller fragment_reconstruction.spec
"""

block_cipher = None

a = Analysis(
    ['launch_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/sample', 'data/sample'),
        ('config', 'config'),
        ('docs/README.md', 'docs'),
        ('docs/QUICK_START_GUI.md', 'docs'),
        ('docs/EXPERIMENT_DOCUMENTATION.md', 'docs'),
    ],
    hiddenimports=[
        # Tkinter and GUI components
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL._tkinter_finder',

        # Core scientific libraries
        'numpy',
        'cv2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',

        # Matplotlib and backends
        'matplotlib',
        'matplotlib.backends',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.pyplot',
        'matplotlib.figure',

        # SciPy modules
        'scipy',
        'scipy.ndimage',
        'scipy.signal',
        'scipy.spatial',
        'scipy.spatial.distance',

        # Configuration and utilities
        'yaml',
        'json',
        'logging',
        'pathlib',
        'dataclasses',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'pytest',
        'test',
        'tests',
        '_pytest',
        'pytest_mock',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FragmentReconstruction',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FragmentReconstruction',
)
