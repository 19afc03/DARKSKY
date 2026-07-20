; ============================================================
; DARKSKY NEXUS w033 — Windows installer (Inno Setup 6)
; Produces: dist\installer\DARKSKY_NEXUS_w033_Setup.exe
;
; Requirements:
;   Inno Setup 6 (free): https://jrsoftware.org/isinfo.php
;   build_Windows.bat must have already been run successfully —
;   this script packages its output (dist\DARKSKY NEXUS w033 Windows\)
;   into a single installer .exe. It does not invoke PyInstaller itself.
;
; Usage:
;   1. cd build\  &&  build_Windows.bat        (produces the onedir build)
;   2. Open this file in the Inno Setup IDE and click Compile,
;      or from the command line:  iscc DARKSKY_NEXUS_w033.iss
;
; On every release, bump MyAppVersionTag and MyAppVersion below —
; keep them in sync with the same two values in build_Windows.bat,
; DARKSKY_NEXUS_Windows.spec, and version_info.txt (see BUILD_NOTES.md).
; ============================================================

#define MyAppName "DARKSKY NEXUS"
#define MyAppVersionTag "w033"
#define MyAppVersion "0.3.3"
#define MyAppPublisher "Jon Nicol"
#define MyAppURL "https://github.com/"
#define MyAppFolderName "DARKSKY NEXUS w033 Windows"
#define MyAppExeName "DARKSKY NEXUS w033 Windows.exe"

[Setup]
; Fixed AppId (a GUID) — keep this the SAME across every future release so
; Windows treats successive versions as upgrades of the same product rather
; than unrelated installs. Only change it if you deliberately want old and
; new versions to be able to coexist side-by-side.
AppId={{6C6B6E3E-6F3A-4E38-9E42-2C6C6E3E7A11}
AppName={#MyAppName} {#MyAppVersionTag}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersionTag}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright=© 2025 Jon Nicol & Claude / Anthropic — Freeware, personal & educational use.
DefaultDirName={autopf}\{#MyAppName} {#MyAppVersionTag}
DefaultGroupName={#MyAppName} {#MyAppVersionTag}
DisableProgramGroupPage=yes
; Freeware, no admin requirement — installs per-user by default but lets
; the user elevate to install for all users if they choose to.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=dist\installer
OutputBaseFilename=DARKSKY_NEXUS_w033_Setup
SetupIconFile=darksky_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; The PyInstaller onedir build is large (numpy/scipy/etc, ~150-250 MB) —
; disable the "ready to install" disk space check quirks by just letting
; Inno compute it from the source files below.
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
; Checked by default (unlike desktopicon above) — this directly addresses a
; user report of not being able to find/open the docs (w031, 2026-07-16).
; Still fully opt-out: unticking the box on the Select Additional Tasks
; page skips the shortcut below entirely, the PDFs are still installed to
; {app}\Docs either way.
Name: "docsshortcut"; Description: "Add a Start Menu shortcut to the documentation (Quick Start / User Manual / Troubleshooting)"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Pulls in the entire PyInstaller onedir output — the .exe, the required
; "_internal" runtime/library folder, any data files (eibi.csv,
; airports.csv, etc.), and the Docs\ subfolder (Quick Start/User Manual/
; Troubleshooting PDFs) that build_Windows.bat copies in as post-processing
; steps. recursesubdirs/createallsubdirs is required because "_internal"
; and "Docs" are themselves folders, not loose files.
Source: "dist\{#MyAppFolderName}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Documentation"; Filename: "{app}\Docs"; Tasks: docsshortcut
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove the whole install directory on uninstall, including anything NEXUS
; wrote at runtime next to the exe (e.g. a first-run-downloaded eibi.csv
; that wasn't present at build time, or darksky_config.json).
Type: filesandordirs; Name: "{app}"
