## DARKSKY NEXUS w034

The headline of this release is a brand-new **DAB/DAB+ engine**, replacing
the old external `dab-cmdline` dependency entirely.

### DAB/DAB+ — rebuilt from scratch

- New headless decode engine, `dab_radio_nexus`, built on top of
  [williamyang98/DAB-Radio](https://github.com/williamyang98/DAB-Radio).
  NEXUS pipes its own Full-IQ tap straight to the tool's stdin — every
  service on a multiplex decodes simultaneously (FIC+MSC+audio, DAB and
  DAB+ both), so switching station is instant, no relaunch.
- **Live audio + Dynamic Label text + MOT slideshow/station logo** in a
  dedicated Now Playing column.
- **Background Band III channel scanner** with ITU-region gating (skips
  scanning in the Americas, where DAB isn't broadcast).
- Ensemble/service list redesigned as a card grid for a non-technical
  audience; topbar polish (shorter channel grid, prominent ensemble lock).
- **One-click bundling** — the engine now ships inside the prebuilt
  installers on both platforms (dylib bundling on macOS, static
  `x64-windows-static` build on Windows), so DAB works out of the box with
  no separate install. Building it from source is only needed if you're
  running NEXUS from source yourself.
- A long list of accuracy/stability fixes along the way: scan
  misattributing ensemble data to the wrong channel, classic DAB (MP2)
  services silent while DAB+ (AAC) played fine, audio silence after
  retuning, MSC decode starved to a single thread, and more — see
  `CHANGELOG.md` for the full trail.
- UI trimmed back down after the above: a temporary manual-frequency-entry
  control and an audio-reactive equalizer graphic were both added then
  removed once the background scanner made the former redundant and the
  latter added no real signal-quality value.

### Docs

New w034 Quick Start / User Manual / Troubleshooting guides, covering the
DAB engine end to end.

### Install

- **macOS:** `DARKSKY_NEXUS_w034_macOS.dmg` (attached below)
- **Windows:** `DARKSKY_NEXUS_w034_Setup.exe` (attached below)
- **From source:** `pip install -r requirements.txt && python3 w034_NEXUS.py`, then open `DARKSKY_NEXUS_w034.html`

Docs: [Quick Start](docs/pdf/DARKSKY_NEXUS_w034_QuickStart.pdf) · [User Manual](docs/pdf/DARKSKY_NEXUS_w034_UserManual.pdf) · [Troubleshooting](docs/pdf/DARKSKY_NEXUS_w034_Troubleshooting.pdf) · [Full changelog](CHANGELOG.md)

Website: https://darksky-nexus.base44.app
