"""
py2app setup for Vocal Separator.
Build a standalone macOS .app bundle that includes Python and all dependencies.

Usage:
  pip install py2app
  python setup.py py2app

Result: dist/VocalSeparator.app

For development (alias mode, uses your env; faster):
  python setup.py py2app -A
"""

from setuptools import setup

APP = ["app_gui.py"]
OPTIONS = {
    "argv_emulation": True,  # Dropped files are passed as sys.argv
    "packages": ["requests", "urllib3", "certifi", "charset_normalizer", "idna"],
    "includes": ["dotenv", "rich", "separator"],
    "iconfile": None,  # Set to "icon.icns" if you add one
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
)
