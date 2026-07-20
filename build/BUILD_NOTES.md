# DARKSKY NEXUS w033 — Build Notes

## Build folder contents

```
build/
├── requirements.txt              — pip dependencies for building
├── DARKSKY_NEXUS_macOS.spec      — PyInstaller spec for macOS .app
├── DARKSKY_NEXUS_Windows.spec    — PyInstaller spec for Windows .exe
├── build_macOS.sh                — macOS build script (run this)
├── build_Windows.bat             — Windows build script (run this)
├── DARKSKY_NEXUS_w033.iss        — Inno Setup script for the Windows installer (run after build_Windows.bat)
├── version_info.txt              — Windows EXE version resource
├── darksky_icon.icns             — macOS icon (YOU MUST PROVIDE THIS)
├── darksky_icon.ico              — Windows icon (YOU MUST PROVIDE THIS)
└── BUILD_NOTES.md                — this file
```

---

## App naming — version + platform are baked into the build

Both the macOS and Windows builds now produce an app whose visible name
includes the version number and the platform, e.g.:

- macOS: `DARKSKY NEXUS w033 macOS.app`
- Windows: `DARKSKY NEXUS w033 Windows\DARKSKY NEXUS w033 Windows.exe`

This is controlled by an `APP_VERSION_TAG` variable (the short, no-dots
form used in NEXUS's own UI/title/CHANGELOG, e.g. `w033`) defined near the
top of each build script (`build_macOS.sh`, `build_Windows.bat`) **and**
each `.spec` file (`DARKSKY_NEXUS_macOS.spec`, `DARKSKY_NEXUS_Windows.spec`)
— that's what the visible app/exe name is built from. A separate
`APP_VERSION` variable (dotted numeric, e.g. `0.3.3`) drives the OS-level
metadata fields (macOS `CFBundleShortVersionString`/`CFBundleVersion`;
Windows `version_info.txt`'s `FileVersion`/`ProductVersion`/`filevers`/
`prodvers`), which can't be the bare `w033` form — Windows in particular
requires a strictly numeric `(major, minor, build, revision)` tuple.
`APP_VERSION_TAG` and `APP_VERSION` are two different formats of the *same*
version (e.g. `w033` ↔ `0.3.3`), not two independently-tracked numbers.

**When cutting a new release, update both variables in all six files** so
the script output, the PyInstaller-built name, the OS metadata, and the
Windows installer all stay in sync:
1. `build_macOS.sh` — `APP_VERSION_TAG="w033"`
2. `DARKSKY_NEXUS_macOS.spec` — `APP_VERSION_TAG = 'w033'`, `APP_VERSION = '0.3.3'`
3. `build_Windows.bat` — `set APP_VERSION_TAG=w033`
4. `DARKSKY_NEXUS_Windows.spec` — `APP_VERSION_TAG = 'w033'`
5. `version_info.txt` — `filevers=(0, 3, 3, 0)`, `prodvers=(0, 3, 3, 0)`, and the `FileVersion`/`ProductVersion`/`InternalName`/`OriginalFilename` strings
6. `DARKSKY_NEXUS_w033.iss` — `MyAppVersionTag` and `MyAppVersion` near the top (Windows installer only; there's no macOS equivalent since the .app/.dmg naming is handled entirely by `build_macOS.sh`)

On macOS the version also still populates `CFBundleShortVersionString` /
`CFBundleVersion` in Info.plist (visible via Finder "Get Info"), so the
version is now surfaced in both the name and the metadata.

---

## Before Building

### 1. Provide an icon

- **macOS:** Place `darksky_icon.icns` in this `build/` folder
  - Create from a PNG: `iconutil -c icns darksky_icon.iconset/`
  - Or use Image2icon (Mac App Store)
  
- **Windows:** Place `darksky_icon.ico` in this `build/` folder
  - Create from a PNG using IcoFX, GIMP, or an online converter
  - Minimum recommended: 256×256 32-bit with 16×16, 32×32, 48×48, 256×256 sizes

If you skip the icon, the build still works — it just uses the default PyInstaller icon.

### 2. Install build dependencies

```bash
pip install -r requirements.txt
```

This includes PyInstaller itself plus all runtime dependencies.

---

## macOS Build

### Requirements
- macOS 11 (Big Sur) or later recommended
- Python 3.9+ (Homebrew: `brew install python3`)
- Xcode Command Line Tools: `xcode-select --install`
- Optional, for a proper "drag to Applications" DMG layout: `brew install create-dmg`
  (the script falls back to a plain `hdiutil` DMG automatically if this isn't installed)

### Steps
```bash
cd build/
chmod +x build_macOS.sh
./build_macOS.sh
```

Output:
- `build/dist/DARKSKY NEXUS w033 macOS.app`
- `build/dist/DARKSKY_NEXUS_w033_macOS.dmg` — built automatically as the script's last step (2026-07-14). No separate manual `hdiutil`/`create-dmg` command needed any more; re-running the script rebuilds both the `.app` and the DMG from scratch.

### Manual DMG creation (only needed if not using build_macOS.sh)
```bash
# Plain DMG:
hdiutil create \
  -volname "DARKSKY NEXUS w033 macOS" \
  -srcfolder "build/dist/DARKSKY NEXUS w033 macOS.app" \
  -ov -format UDZO \
  "DARKSKY_NEXUS_w033_macOS.dmg"

# Nicer "drag to Applications" layout (requires: brew install create-dmg):
create-dmg \
  --volname "DARKSKY NEXUS w033 macOS" \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "DARKSKY NEXUS w033 macOS.app" 150 190 \
  --app-drop-link 450 190 \
  "DARKSKY_NEXUS_w033_macOS.dmg" \
  "build/dist/DARKSKY NEXUS w033 macOS.app"
```

### Universal Binary (Apple Silicon + Intel)
To build a universal binary (runs natively on both M-series and Intel Macs), install Python and all packages for both architectures and add `target_arch='universal2'` in the spec, or build separately on each architecture and merge with `lipo`.

The simplest approach: build on an Apple Silicon Mac — the resulting arm64 binary runs on all modern Macs and runs under Rosetta 2 on older Intel Macs automatically.

### Gatekeeper / Notarisation
Without notarisation, users see "unidentified developer" on first launch. They can right-click → Open to bypass once. For distribution, notarise with an Apple Developer account:
```bash
xcrun notarytool submit "DARKSKY_NEXUS_w033_macOS.dmg" \
  --apple-id "your@email.com" \
  --team-id "XXXXXXXXXX" \
  --password "app-specific-password" \
  --wait
xcrun stapler staple "DARKSKY_NEXUS_w033_macOS.dmg"
```

---

## Windows Build

### Requirements
- Windows 10 / 11 64-bit
- Python 3.9+ from https://python.org (check "Add to PATH")
- Run Command Prompt as Administrator if needed

### Steps
```
cd build\
build_Windows.bat
```

Output: `build\dist\DARKSKY NEXUS w033 Windows\DARKSKY NEXUS w033 Windows.exe`

### Distribution
Zip the entire `DARKSKY NEXUS w033 Windows\` folder — it contains the exe and all dependencies. Users extract and run `DARKSKY NEXUS w033 Windows.exe` directly. No installer needed.

For a proper installer, use **Inno Setup** (free): https://jrsoftware.org/isinfo.php — `DARKSKY_NEXUS_w033.iss` in this folder is a ready-to-compile script targeting the `build_Windows.bat` output. Open it in the Inno Setup IDE (or run `iscc DARKSKY_NEXUS_w033.iss` from the command line) **after** `build_Windows.bat` has produced `dist\DARKSKY NEXUS w033 Windows\`; it packages that folder into a single `DARKSKY_NEXUS_w033_Setup.exe` in `dist\installer\`. Update `MyAppVersion` and `MyAppVersionTag` at the top of the .iss on every release, matching the other four files noted above.

### Windows Defender SmartScreen
Like macOS Gatekeeper, Windows SmartScreen warns on unsigned executables. Users click "More info" → "Run anyway". For wider distribution, sign with a code-signing certificate.

### Console vs Windowed
The spec uses `console=False` (no terminal window). For debugging, change to `console=True` in the spec to see log output in a console window.

---

## What Gets Bundled

The standalone app includes:
- `w033_NEXUS.py` (compiled to bytecode)
- `DARKSKY_NEXUS_w033.html` (the full UI)
- All Python dependencies (numpy, scipy, websockets, paramiko, sounddevice)
- Any data files present at build time (eibi.csv, airports.csv, etc.)

Data files NOT present at build time (eibi.csv, airports.csv, etc.) are downloaded on first run to the folder where the app is located (or `~/Library/Application Support/DARKSKY NEXUS/` if the app folder is not writable).

---

## Known Build Issues

### `ModuleNotFoundError` at runtime for websockets or scipy
Add the missing module to `hiddenimports` in the .spec file and rebuild.

### App crashes immediately on macOS with no error
Run from terminal to see the error:
```bash
"dist/DARKSKY NEXUS w033 macOS.app/Contents/MacOS/DARKSKY NEXUS w033 macOS"
```

### sounddevice fails to find PortAudio on macOS
PyInstaller sometimes misses the PortAudio dylib. Add to binaries in spec:
```python
binaries=[('/usr/local/lib/libportaudio.dylib', '.')],
```
Or install PortAudio: `brew install portaudio`

### Large app size
The bundled numpy/scipy add ~100–150 MB. This is expected for scientific Python bundles. UPX compression (enabled in spec) reduces this somewhat.
