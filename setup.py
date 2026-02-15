"""
py2app setup for Vocal Separator.
Build a standalone macOS .app bundle that includes Python and all dependencies.

Usage:
  pip install py2app
  pip install -e .   # so vocal_separator is importable
  python setup.py py2app

Result: dist/VocalSeparator.app

For development (alias mode, uses your env; faster):
  python setup.py py2app -A
"""

import os
import subprocess

from setuptools import find_packages, setup

# Ensure app icon exists before build (create from assets/icon.png if needed)
_setup_dir = os.path.dirname(os.path.abspath(__file__))
_icon_icns = os.path.join(_setup_dir, "assets", "icon.icns")
_icon_png = os.path.join(_setup_dir, "assets", "icon.png")
if not os.path.isfile(_icon_icns) and os.path.isfile(_icon_png):
    _build_script = os.path.join(_setup_dir, "scripts", "build_icon.sh")
    if os.path.isfile(_build_script):
        subprocess.run(["/bin/bash", _build_script], cwd=_setup_dir, check=False)
_iconfile = _icon_icns if os.path.isfile(_icon_icns) else None

APP = ["run_gui.py"]
OPTIONS = {
    "argv_emulation": True,  # Dropped files are passed as sys.argv
    "packages": [
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "vocal_separator",
    ],
    "includes": ["dotenv", "rich"],
    "iconfile": _iconfile,
    "plist": {
        "CFBundleName": "VocalSeparator",
        "CFBundleDisplayName": "Vocal Separator",
        "CFBundleIdentifier": "com.audioshake.vocalseparator",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Audio File",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": [
                    "public.audio",
                    "public.mp3",
                    "public.mpeg-4-audio",
                    "com.microsoft.waveform-audio",
                    "org.xiph.flac",
                ],
            },
            {
                "CFBundleTypeName": "Folder",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": ["public.folder"],
            },
        ],
    },
}

setup(
    name="VocalSeparator",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
)
