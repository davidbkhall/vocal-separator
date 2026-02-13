# PyInstaller spec for Vocal Separator macOS .app
# Build: pyinstaller VocalSeparator.spec
# Output: dist/VocalSeparator.app
# Icon: built from assets/icon.png automatically when missing

# -*- mode: python ; coding: utf-8 -*-

import os
import subprocess
import sys

_block_cipher = None
# PyInstaller may exec this spec without __file__; use spec path from argv or cwd
try:
    _spec_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    if len(sys.argv) > 1 and sys.argv[1].endswith(".spec"):
        _spec_dir = os.path.dirname(os.path.abspath(sys.argv[1]))
    else:
        _spec_dir = os.getcwd()
_icon_icns = os.path.join(_spec_dir, "assets", "icon.icns")
_icon_png = os.path.join(_spec_dir, "assets", "icon.png")
if not os.path.isfile(_icon_icns) and os.path.isfile(_icon_png):
    _build_script = os.path.join(_spec_dir, "build_icon.sh")
    if os.path.isfile(_build_script):
        subprocess.run(["/bin/bash", _build_script], cwd=_spec_dir, check=False)
# Use absolute path so PyInstaller finds the icon when creating the .app bundle
icon_path = os.path.abspath(_icon_icns) if os.path.isfile(_icon_icns) else None
block_cipher = _block_cipher

# Bundle all of rich (including _unicode_data) so the frozen app does not fail at runtime
try:
    from PyInstaller.utils.hooks import collect_all
    _rich_datas, _rich_binaries, _rich_hidden = collect_all("rich")
except Exception:
    _rich_datas = []
    _rich_binaries = []
    _rich_hidden = ["rich", "rich.console", "rich.progress"]

a = Analysis(
    ["app_gui.py"],
    pathex=[],
    binaries=_rich_binaries,
    datas=_rich_datas,
    hiddenimports=[
        "separator",
        "dotenv",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
    ] + _rich_hidden,
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
    icon=icon_path,  # .icns for macOS .app (create with ./build_icon.sh)
)

# macOS .app bundle (built when console=False on macOS)
# Result: dist/VocalSeparator.app
