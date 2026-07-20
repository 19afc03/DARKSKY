# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for DARKSKY NEXUS w033 — macOS .app bundle
# Build: pyinstaller DARKSKY_NEXUS_macOS.spec
# Output: dist/DARKSKY NEXUS w033 macOS.app
#
# NOTE: The app name below embeds both the version tag (w033) and the
# platform (macOS) so the Finder listing/Dock tooltip/About box make it
# obvious which build a user is running, without having to dig into Get
# Info. APP_VERSION_TAG is the short, no-dots version used in NEXUS's own
# UI/title/CHANGELOG (w033); APP_VERSION is the dotted semver form macOS
# metadata (CFBundleVersion/CFBundleShortVersionString) actually requires —
# bump both together on every release, they're intentionally two different
# formats of the same version, not two different versions.

import sys
from pathlib import Path

block_cipher = None

APP_VERSION_TAG = 'w033'                    # bump this each release — matches NEXUS's own version string
APP_VERSION = '0.3.3'                       # bump this each release — dotted semver for macOS metadata
APP_NAME = f'DARKSKY NEXUS {APP_VERSION_TAG} macOS'   # visible app/bundle name

# Data files bundled inside the app
# (HTML, CSV, JSON — all resolved relative to .py at runtime via SCRIPT_DIR)
#
# SECURITY (2026-07-17, updated 2026-07-18 after VesselAPI's removal): do
# NOT add .aisstream_key.json or ais_aisstream_store.json here. Those are
# per-machine aisstream.io credential/cache files (see AIS_AISSTREAM_KEYFILE
# / AIS_AISSTREAM_STORE_FILE in w033_NEXUS.py) — bundling one would ship
# the developer's own API key (and its resolved-vessel cache) inside every
# copy of the distributed app. Each end user generates and enters their
# own free aisstream.io key via the AIS tab's GUI field at runtime instead.
# build_macOS.sh verifies neither of these ended up in the built bundle
# and aborts the build if they do.
datas = [
    ('../DARKSKY_NEXUS_w033.html', '.'),
    ('../eibi.csv',                  '.'),   # may not exist — ok, auto-downloaded
    ('../airports.csv',              '.'),   # may not exist — ok, auto-downloaded
    ('../airport-frequencies.csv',   '.'),   # may not exist — ok, auto-downloaded
    ('../darksky_bookmarks.json',    '.'),   # may not exist — ok, auto-created
]

# Filter out missing optional files (eibi/airports downloaded on first run)
import os
datas = [(src, dst) for src, dst in datas if os.path.exists(src)]
# Always include the HTML
datas_required = [('../DARKSKY_NEXUS_w033.html', '.')]
for item in datas_required:
    if item not in datas:
        datas.append(item)

a = Analysis(
    ['../w033_NEXUS.py'],
    pathex=[str(Path('../').resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # websockets internal modules
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'websockets.legacy.client',
        'websockets.legacy.protocol',
        'websockets.connection',
        'websockets.frames',
        'websockets.http11',
        'websockets.streams',
        # scipy signal processing
        'scipy',
        'scipy.signal',
        'scipy.signal._upfirdn',
        'scipy.signal._upfirdn_apply',
        'scipy.special',
        'scipy.special._ufuncs',
        # sounddevice / PortAudio
        'sounddevice',
        '_sounddevice',
        # paramiko SSH
        'paramiko',
        'paramiko.transport',
        'paramiko.auth_handler',
        'paramiko.sftp_client',
        # numpy
        'numpy',
        'numpy.core',
        'numpy.fft',
        'numpy.linalg',
        # stdlib used at runtime
        'xmlrpc.client',
        'xmlrpc.server',
        'http.server',
        'multiprocessing',
        'multiprocessing.process',
        'multiprocessing.queues',
        'multiprocessing.pool',
        'multiprocessing.spawn',   # required on macOS — default start method since Python 3.8
        'encodings.utf_8',
        'encodings.ascii',
        'encodings.latin_1',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'PyQt5',
        'PySide2',
        'wx',
        'gi',
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
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # no terminal window — logs go to ~/Library/Logs/DARKSKY_NEXUS/
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,      # universal2 — set to 'arm64' or 'x86_64' to target one arch
    codesign_identity=None,
    entitlements_file=None,
    icon='darksky_icon.icns',   # place darksky_icon.icns in build/ folder
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

app = BUNDLE(
    coll,
    name=f'{APP_NAME}.app',
    icon='darksky_icon.icns',
    bundle_identifier='com.darksky.nexus',
    version=APP_VERSION,
    info_plist={
        'NSPrincipalClass':               'NSApplication',
        'NSAppleScriptEnabled':           False,
        'NSHighResolutionCapable':        True,
        'CFBundleShortVersionString':     APP_VERSION,
        'CFBundleVersion':                APP_VERSION_TAG,
        'CFBundleName':                   APP_NAME,
        'CFBundleDisplayName':            APP_NAME,
        'CFBundleExecutable':             APP_NAME,
        'NSRequiresAquaSystemAppearance': False,   # supports Dark Mode
        'LSBackgroundOnly':               False,
        'NSMicrophoneUsageDescription':   'DARKSKY NEXUS uses audio for signal decoding.',
        'LSUIElement':                    False,
    },
)
