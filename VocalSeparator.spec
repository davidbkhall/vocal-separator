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
    _build_script = os.path.join(_spec_dir, "scripts", "build_icon.sh")
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

# Tcl/Tk data are added by PyInstaller's hook-_tkinter when _tkinter is a dependency.
# Do not add them again here or COLLECT can hit IsADirectoryError (duplicate dest paths).

a = Analysis(
    ["run_gui.py"],
    pathex=[os.path.join(_spec_dir, "src")],
    binaries=_rich_binaries,
    datas=_rich_datas,
    hiddenimports=[
        "audioshake_separator",
        "audioshake_separator.separator",
        "audioshake_separator.batch",
        "audioshake_separator.app_gui",
        "_tkinter",
        "tkinter",
        "dotenv",
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
    ]
    + _rich_hidden,
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

# Onedir + COLLECT so we get a proper .app bundle on macOS (onefile does not create .app).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VocalSeparator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,  # no terminal window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=True,  # dropped files passed as argv on macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VocalSeparator",
)

# macOS: wrap COLLECT output in .app bundle so we get dist/VocalSeparator.app (and icon applied).
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="VocalSeparator.app",
        icon=icon_path,
        bundle_identifier=None,
        info_plist={"CFBundleIconFile": "icon"},
    )
