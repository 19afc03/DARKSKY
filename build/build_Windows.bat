@echo off
REM ============================================================
REM  DARKSKY NEXUS w033 — Windows build script
REM  Produces: build\dist\DARKSKY NEXUS w033 Windows\DARKSKY NEXUS w033 Windows.exe
REM
REM  Requirements:
REM    Python 3.9+ from python.org (add to PATH during install)
REM    pip install -r requirements.txt
REM
REM  Usage:
REM    Open Command Prompt in the build\ folder
REM    build_Windows.bat
REM ============================================================

setlocal EnableDelayedExpansion

REM Bump this on every release — it must match APP_VERSION_TAG in
REM DARKSKY_NEXUS_Windows.spec so the exe/folder name stays consistent.
set APP_VERSION_TAG=w033
set APP_NAME=DARKSKY NEXUS %APP_VERSION_TAG% Windows

set BUILD_DIR=%~dp0
set ROOT_DIR=%BUILD_DIR%..
set DIST_DIR=%BUILD_DIR%dist
set WORK_DIR=%BUILD_DIR%work

echo ============================================
echo   %APP_NAME% -- Build
echo ============================================
echo Root:  %ROOT_DIR%
echo Build: %BUILD_DIR%
echo.

REM ── SECURITY: never ship a developer's own aisstream.io key ────
REM (2026-07-17, user request: "when building win or macos this needs to
REM be removed. user must create own account and generate their own api
REM key." -- originally written for VesselAPI, removed 2026-07-18; same
REM requirement now applies to aisstream.io, NEXUS's remaining online AIS
REM enrichment source.) The .spec file's datas list is already an explicit
REM whitelist that doesn't include these -- this is a second, independent
REM warning in case that ever drifts. Each end user generates and enters
REM their own free aisstream.io key via the AIS tab's GUI field at runtime
REM (see User Manual) -- NEXUS never needs one bundled to build or run.
if exist "%ROOT_DIR%\.aisstream_key.json" (
    echo !! WARNING: %ROOT_DIR%\.aisstream_key.json exists on this machine
    echo !!          ^(your own dev/test key^) -- it will NOT be bundled ^(the
    echo !!          .spec datas list never references it^), but don't hand-add
    echo !!          it to datas= either.
)
echo.

REM ── Step 1: Check Python ─────────────────────────────────────
echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://python.org
    echo        Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

REM ── Step 2: Install dependencies ─────────────────────────────
echo.
echo [2/5] Installing dependencies...
pip install -r "%BUILD_DIR%requirements.txt"
if errorlevel 1 (
    echo ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

REM ── Step 3: Check icon ───────────────────────────────────────
echo.
echo [3/5] Checking icon...
if not exist "%BUILD_DIR%darksky_icon.ico" (
    echo WARNING: darksky_icon.ico not found in build\
    echo          App will use default PyInstaller icon.
) else (
    echo Icon found: darksky_icon.ico
)

REM ── Step 4: Clean previous build ─────────────────────────────
echo.
echo [4/5] Cleaning previous build...
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%WORK_DIR%" rmdir /s /q "%WORK_DIR%"

REM ── Step 5: Run PyInstaller ───────────────────────────────────
echo.
echo [5/5] Running PyInstaller...
cd /d "%BUILD_DIR%"
pyinstaller ^
    --clean ^
    --noconfirm ^
    --workpath "%WORK_DIR%" ^
    --distpath "%DIST_DIR%" ^
    DARKSKY_NEXUS_Windows.spec

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. See output above.
    pause
    exit /b 1
)

REM ── Post-processing ───────────────────────────────────────────
echo.
echo Copying data files...
set APP_DIR=%DIST_DIR%\%APP_NAME%

for %%f in (eibi.csv airports.csv airport-frequencies.csv darksky_bookmarks.json) do (
    if exist "%ROOT_DIR%\%%f" (
        copy "%ROOT_DIR%\%%f" "%APP_DIR%\%%f" >nul
        echo Copied: %%f
    )
)

echo.
echo Copying documentation...
REM Added w031 -- a user reported "Windows can't read the document files"
REM and it turned out no build ever shipped any docs at all. Copied into
REM a Docs subfolder next to the .exe; the .iss installer packages
REM %%APP_DIR%%\* recursively so this needs no separate installer change.
if not exist "%ROOT_DIR%\docs\pdf" (
    echo WARNING: %ROOT_DIR%\docs\pdf not found -- build will ship without bundled docs.
) else (
    if not exist "%APP_DIR%\Docs" mkdir "%APP_DIR%\Docs"
    for %%d in ("%ROOT_DIR%\docs\pdf\*.pdf") do (
        copy "%%d" "%APP_DIR%\Docs\" >nul
        echo Copied: %%~nxd
    )
)

echo.
echo Verifying no aisstream.io key/cache files were bundled...
set LEAKED=0
for %%f in (.aisstream_key.json ais_aisstream_store.json) do (
    if exist "%APP_DIR%\%%f" (
        echo !! ERROR: %%f was found INSIDE the built app folder -- this must
        echo !!        never ship. Remove it from datas= in the .spec file
        echo !!        and rebuild.
        set LEAKED=1
    )
    if exist "%APP_DIR%\_internal\%%f" (
        echo !! ERROR: %%f was found INSIDE _internal -- this must never ship.
        echo !!        Remove it from datas= in the .spec file and rebuild.
        set LEAKED=1
    )
)
if !LEAKED! == 1 (
    echo.
    echo BUILD ABORTED -- see errors above.
    pause
    exit /b 1
)
echo OK -- clean.

echo.
echo ============================================
echo   BUILD COMPLETE
echo ============================================
echo.
echo Executable: %APP_DIR%\%APP_NAME%.exe
echo Docs:       %APP_DIR%\Docs\  (Quick Start / User Manual / Troubleshooting PDFs)
echo.
echo IMPORTANT: The "_internal" folder inside %APP_DIR%
echo            is REQUIRED — it holds the Python runtime, libraries,
echo            and data files the .exe loads at startup. Do not
echo            separate the .exe from "_internal"; always keep and
echo            distribute the whole "%APP_NAME%" folder together.
echo.
echo To distribute:
echo   Zip the whole folder: %APP_DIR%
echo   Or build the installer: open DARKSKY_NEXUS_w033.iss in Inno Setup
echo   (Compile) — it packages %APP_DIR% into a single setup .exe.
echo.
echo To test:
echo   "%APP_DIR%\%APP_NAME%.exe"
echo.
pause
