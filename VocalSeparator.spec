# PyInstaller spec for Vocal Separator macOS .app
# Build: pyinstaller VocalSeparator.spec
# Output: dist/VocalSeparator.app

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ["app_gui.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "separator",
        "dotenv",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "rich",
        "rich.console",
        "rich.progress",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VocalSeparator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # no terminal window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=True,  # dropped files passed as argv on macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app bundle (built when console=False on macOS)
# Result: dist/VocalSeparator.app
