#!/bin/bash
# ============================================================
# DARKSKY NEXUS w033 — macOS build script
# Produces: dist/DARKSKY NEXUS w033 macOS.app
#           dist/DARKSKY_NEXUS_w033_macOS.dmg
#
# Requirements:
#   Python 3.9+ (Homebrew recommended: brew install python3)
#   pip install -r requirements.txt
#   Optional, for a proper "drag to Applications" DMG:
#     brew install create-dmg
#   (falls back to a plain hdiutil DMG if create-dmg isn't installed)
#
# Usage:
#   cd build/
#   chmod +x build_macOS.sh
#   ./build_macOS.sh
# ============================================================

set -e  # exit on any error

# Bump this on every release — it must match APP_VERSION_TAG in
# DARKSKY_NEXUS_macOS.spec so the app name stays consistent.
APP_VERSION_TAG="w033"
APP_NAME="DARKSKY NEXUS ${APP_VERSION_TAG} macOS"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$SCRIPT_DIR"
DIST_DIR="$SCRIPT_DIR/dist"
WORK_DIR="$SCRIPT_DIR/work"

echo "============================================"
echo "  $APP_NAME — Build"
echo "============================================"
echo "Root:  $ROOT_DIR"
echo "Build: $BUILD_DIR"
echo ""

# ── SECURITY: never ship a developer's own aisstream.io key ────
# (2026-07-17, user request: "when building win or macos this needs to be
# removed. user must create own account and generate their own api key."
# — originally written for VesselAPI, which was removed 2026-07-18; the
# same requirement now applies to aisstream.io, NEXUS's remaining online
# AIS enrichment source.) The .spec files' `datas` lists are already an
# explicit whitelist that doesn't include these — this check is a second,
# independent guard in case that ever drifts, and it fails the build
# LOUDLY rather than silently shipping someone's personal API key/lookup
# cache baked into a public installer. Each end user generates and enters
# their own free aisstream.io key via the AIS tab's GUI field at runtime
# (see User Manual) — NEXUS never needs one bundled to build or run.
for f in .aisstream_key.json ais_aisstream_store.json; do
    if [ -f "$ROOT_DIR/$f" ]; then
        echo "!! WARNING: $ROOT_DIR/$f exists on this machine (your own dev/test"
        echo "!!          key or lookup cache) — it will NOT be bundled (the .spec"
        echo "!!          datas list never references it), but leaving it in the"
        echo "!!          source tree is a reminder it's local-only. Safe to ignore"
        echo "!!          if you know it's yours; just don't hand-add it to datas=."
    fi
done
echo ""

# ── Step 1: Check Python ─────────────────────────────────────
echo "[1/7] Checking Python..."
python3 --version
PYTHON=$(which python3)
echo "Using: $PYTHON"

# ── Step 2: Install / verify dependencies ────────────────────
echo ""
echo "[2/7] Installing dependencies..."
pip3 install --break-system-packages -r "$BUILD_DIR/requirements.txt"

# ── Step 3: Check for icon ───────────────────────────────────
echo ""
echo "[3/7] Checking icon..."
if [ ! -f "$BUILD_DIR/darksky_icon.icns" ]; then
    echo "WARNING: darksky_icon.icns not found in build/"
    echo "         App will use default PyInstaller icon."
    echo "         To add an icon: place darksky_icon.icns in build/"
    # Remove icon references from spec to avoid build error
    ICON_ARG=""
else
    echo "Icon found: darksky_icon.icns"
    ICON_ARG=""
fi

# ── Step 4: Clean previous build ─────────────────────────────
echo ""
echo "[4/7] Cleaning previous build..."
rm -rf "$DIST_DIR" "$WORK_DIR"

# ── Step 5: Run PyInstaller ───────────────────────────────────
echo ""
echo "[5/7] Running PyInstaller..."
cd "$BUILD_DIR"
pyinstaller \
    --clean \
    --noconfirm \
    --workpath "$WORK_DIR" \
    --distpath "$DIST_DIR" \
    DARKSKY_NEXUS_macOS.spec

# ── Step 6: Post-processing ───────────────────────────────────
echo ""
echo "[6/7] Post-processing..."

APP="$DIST_DIR/$APP_NAME.app"

if [ ! -d "$APP" ]; then
    echo "ERROR: App bundle not found at: $APP"
    exit 1
fi

# Copy data files into app bundle Resources if not already there via datas=
RESOURCES="$APP/Contents/Resources"
for f in "$ROOT_DIR/eibi.csv" "$ROOT_DIR/airports.csv" \
          "$ROOT_DIR/airport-frequencies.csv" "$ROOT_DIR/darksky_bookmarks.json"; do
    if [ -f "$f" ]; then
        cp "$f" "$RESOURCES/" 2>/dev/null || true
        echo "Copied: $(basename $f)"
    fi
done

# Copy Quick Start / User Manual / Troubleshooting PDFs into the app bundle
# (added w031 — a user reported "Windows can't read the document files" and
# it turned out no build shipped any docs at all, not just a Windows-side
# issue). Bundled here for completeness; the DMG staging step below is what
# actually makes these visible to a person opening the DMG, since Resources
# is buried inside the app bundle.
DOCS_SRC="$ROOT_DIR/docs/pdf"
if [ -d "$DOCS_SRC" ]; then
    mkdir -p "$RESOURCES/Docs"
    cp "$DOCS_SRC"/*.pdf "$RESOURCES/Docs/" 2>/dev/null || true
    echo "Copied docs: $(ls "$DOCS_SRC"/*.pdf 2>/dev/null | wc -l | tr -d ' ') PDF(s) into Resources/Docs"
else
    echo "WARNING: $DOCS_SRC not found — DMG will ship without bundled docs."
fi

# Remove the loose onedir output (PyInstaller's intermediate COLLECT stage).
# The BUNDLE step above already copied everything needed into the .app, so
# the standalone executable and its "_internal" folder that COLLECT left
# next to the .app in dist/ are redundant build artifacts.
ONEDIR_EXE="$DIST_DIR/$APP_NAME"
ONEDIR_INTERNAL="$DIST_DIR/_internal"
if [ -f "$ONEDIR_EXE" ]; then
    rm -f "$ONEDIR_EXE"
    echo "Removed loose executable: $ONEDIR_EXE"
fi
if [ -d "$ONEDIR_INTERNAL" ]; then
    rm -rf "$ONEDIR_INTERNAL"
    echo "Removed intermediate build folder: $ONEDIR_INTERNAL"
fi

# ── Step 6b: SECURITY — verify no aisstream.io secrets got bundled ─
echo ""
echo "[6b/7] Verifying no aisstream.io key/cache files were bundled..."
LEAKED=0
for f in .aisstream_key.json ais_aisstream_store.json; do
    if find "$APP/Contents" -name "$f" 2>/dev/null | grep -q .; then
        echo "!! ERROR: $f was found INSIDE the built app bundle — this must"
        echo "!!        never ship. Remove it from datas= in the .spec file"
        echo "!!        and rebuild."
        LEAKED=1
    fi
done
if [ "$LEAKED" -eq 1 ]; then
    echo ""
    echo "BUILD ABORTED — see errors above."
    exit 1
fi
echo "OK — clean."

# ── Step 7: Create DMG ────────────────────────────────────────
echo ""
echo "[7/7] Creating DMG..."

DMG_PATH="$DIST_DIR/DARKSKY_NEXUS_w033_macOS.dmg"
rm -f "$DMG_PATH"   # hdiutil/create-dmg both refuse to overwrite silently

# Stage the .app plus a top-level "Docs" folder together so the PDFs are
# visible immediately when the DMG is opened, not buried inside the app
# bundle's Resources (see the Resources/Docs copy above — that copy is what
# NEXUS itself could read from at runtime if it ever needed to; this one is
# what a person actually sees).
STAGING_DIR="$DIST_DIR/dmg_staging"
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"
cp -R "$APP" "$STAGING_DIR/"
if [ -d "$DOCS_SRC" ]; then
    mkdir -p "$STAGING_DIR/Docs"
    cp "$DOCS_SRC"/*.pdf "$STAGING_DIR/Docs/" 2>/dev/null || true
fi

if command -v create-dmg &> /dev/null; then
    # Nicer "drag to Applications" layout. create-dmg exits non-zero on some
    # harmless warnings (e.g. Finder AppleScript timing) even on success, so
    # don't let `set -e` abort the whole script over that — just fall back
    # to plain hdiutil if the DMG genuinely wasn't produced.
    create-dmg \
        --volname "$APP_NAME" \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "$APP_NAME.app" 150 190 \
        --app-drop-link 450 190 \
        "$DMG_PATH" \
        "$STAGING_DIR" || true

    if [ ! -f "$DMG_PATH" ]; then
        echo "create-dmg did not produce a DMG — falling back to hdiutil."
        hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"
    fi
else
    echo "create-dmg not found (brew install create-dmg for a nicer installer layout)."
    echo "Falling back to a plain hdiutil DMG."
    hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"
fi

# Show result
echo ""
echo "============================================"
echo "  BUILD COMPLETE"
echo "============================================"
echo "App: $APP"
du -sh "$APP"
if [ -f "$DMG_PATH" ]; then
    echo "DMG: $DMG_PATH"
    du -sh "$DMG_PATH"
else
    echo "WARNING: DMG was not created — see errors above."
fi
echo ""
echo "To test:"
echo "  open \"$APP\""
echo ""
echo "To distribute (unsigned — users see 'unidentified developer' on first launch):"
echo "  Share \"$DMG_PATH\""
echo ""
echo "To notarise for wider distribution (requires an Apple Developer account):"
echo "  xcrun notarytool submit \"$DMG_PATH\" \\"
echo "    --apple-id \"your@email.com\" --team-id \"XXXXXXXXXX\" \\"
echo "    --password \"app-specific-password\" --wait"
echo "  xcrun stapler staple \"$DMG_PATH\""
echo ""
