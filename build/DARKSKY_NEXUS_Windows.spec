# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for DARKSKY NEXUS w033 — Windows .exe
# Build: pyinstaller DARKSKY_NEXUS_Windows.spec
# Output: dist\DARKSKY NEXUS w033 Windows\DARKSKY NEXUS w033 Windows.exe
#         (one-folder build — zip the folder to distribute)
#
# NOTE: The folder/exe name below embeds both the version tag (w033) and
# the platform (Windows) so it's obvious at a glance which build a user
# has, without opening Properties > Details. APP_VERSION_TAG is the short,
# no-dots version used in NEXUS's own UI/title/CHANGELOG (w033);
# APP_VERSION is the dotted numeric form version_info.txt's FileVersion/
# ProductVersion actually require — bump both together on every release.

import sys
import os
from pathlib import Path

block_cipher = None

APP_VERSION_TAG = 'w033'                            # bump this each release — matches NEXUS's own version string
APP_VERSION = '0.3.3'                               # bump this each release — dotted numeric, must match version_info.txt
APP_NAME = f'DARKSKY NEXUS {APP_VERSION_TAG} Windows'  # visible exe/folder name

# Data files bundled inside the app
#
# SECURITY (2026-07-17, updated 2026-07-18 after VesselAPI's removal): do
# NOT add .aisstream_key.json or ais_aisstream_store.json here. Those are
# per-machine aisstream.io credential/cache files (see AIS_AISSTREAM_KEYFILE
# / AIS_AISSTREAM_STORE_FILE in w033_NEXUS.py) — bundling one would ship
# the developer's own API key (and its resolved-vessel cache) inside every
# copy of the distributed app. Each end user generates and enters their
# own free aisstream.io key via the AIS tab's GUI field at runtime instead.
# build_Windows.bat verifies neither of these ended up in the built app
# folder and aborts the build if they do.
datas = [
    ('../DARKSKY_NEXUS_w033.html', '.'),
]
# Add optional data files if they exist
for fname in ['eibi.csv', 'airports.csv', 'airport-frequencies.csv', 'darksky_bookmarks.json']:
    src = f'../{fname}'
    if os.path.exists(src):
        datas.append((src, '.'))

a = Analysis(
    ['../w033_NEXUS.py'],
    pathex=[str(Path('../').resolve())],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # websockets
        'websockets',
        'websockets.legacy',
        'websockets.legacy.server',
        'websockets.legacy.client',
        'websockets.legacy.protocol',
        'websockets.connection',
        'websockets.frames',
        'websockets.http11',
        'websockets.streams',
        # scipy
        'scipy',
        'scipy.signal',
        'scipy.signal._upfirdn',
        'scipy.signal._upfirdn_apply',
        'scipy.special',
        'scipy.special._ufuncs',
        # sounddevice
        'sounddevice',
        '_sounddevice',
        # paramiko
        'paramiko',
        'paramiko.transport',
        'paramiko.auth_handler',
        'paramiko.sftp_client',
        # numpy
        'numpy',
        'numpy.core',
        'numpy.fft',
        'numpy.linalg',
        # stdlib
        'xmlrpc.client',
        'xmlrpc.server',
        'http.server',
        'multiprocessing',
        'multiprocessing.process',
        'multiprocessing.queues',
        'multiprocessing.pool',
        'multiprocessing.spawn',
        'encodings.utf_8',
        'encodings.ascii',
        'encodings.latin_1',
        'encodings.cp1252',
        # Windows-specific asyncio
        'asyncio.windows_events',
        'asyncio.windows_utils',
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
    console=False,          # no console window — set to True for debug builds
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='darksky_icon.ico',    # place darksky_icon.ico in build\ folder
    version='version_info.txt', # optional: Windows version info resource
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
