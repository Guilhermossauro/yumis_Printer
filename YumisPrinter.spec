# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

root = Path.cwd()

datas = [
    (str(root / "templates"), "templates"),
    (str(root / "static"), "static"),
]

a = Analysis(
    ['run.py'],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "webview.platforms.winforms",
        "webview.platforms.edgechromium",
        "win32print",
        "win32api",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # ML / data science — not used by this app
        "torch", "torchvision", "torchaudio",
        "tensorflow", "keras",
        "scipy", "sklearn", "pandas",
        "cv2", "matplotlib", "seaborn",
        "nltk", "transformers", "datasets",
        "onnxruntime",
        # CLI / cloud tools
        "yt_dlp", "boto3", "botocore", "awscrt",
        "pyarrow", "sqlalchemy", "psycopg2",
        "openpyxl",
        # Notebooks / interactive
        "IPython", "jupyter", "notebook",
        "mako", "alembic",
        # Tk not needed (using Qt via pywebview)
        "tkinter", "_tkinter",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='YumisPrinter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)