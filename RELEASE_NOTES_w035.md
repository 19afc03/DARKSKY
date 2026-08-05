## DARKSKY NEXUS w035

Two new digital radio decoders, a real startup connection picker, and a long
list of DAB/DRM reliability fixes found through live testing.

### New: HD Radio (NRSC-5/iBOC) decoding

New headless engine, `nrsc5_nexus`, built on
[theori-io/nrsc5](https://github.com/theori-io/nrsc5). Decodes every
HD sub-program a station carries (HD1 through HD8) simultaneously, with
station name, slogan, program info, ID3 song/artist tags, and station logo
artwork. Bundled into the prebuilt installers, no separate install needed.

### New: DRM / DRM+ decoding

Brand-new decoder tab and engine, `dream_nexus`, built on the
[Dream](https://sourceforge.net/projects/drm/) DRM decoder. Covers
shortwave, mediumwave, and VHF/FM DRM+ trial broadcasts, with a ready-made
quick-tune list of 39 known active frequencies worldwide, live signal
quality, station name, and text message display. Also bundled, no separate
install needed.

### Smarter startup

- A real connection picker on first run — choose networked nRSP-ST, local
  USB, remote USB, or RTL-SDR — remembered from then on, instead of NEXUS
  guessing (and often guessing wrong).
- NEXUS can now launch SDRConnect for you, headless or full GUI, local or
  remote.
- Automatic "which radio?" prompt whenever both a USB and networked radio
  are available, instead of silently picking one.
- A live status strip narrates startup progress in plain English instead of
  a blank screen.

### Reliability & bug fixes

- DAB Band III scanning and decoding fixed end to end — two separate timing
  bugs (a sample-rate confirmation race and a hardware retune settle-time
  gap) were causing clean-looking scans to find zero ensembles.
- DAB/DAB+ station logos (MOT Slideshow) now actually appear once you tune
  to a station, instead of only being sent once, usually before you'd
  selected it.
- A side effect of the logo fix — DAB audio cutting out after ~10 seconds
  on logo-heavy stations — fixed by giving slideshow images their own
  delivery path instead of sharing the audio pipe.
- DRM audio playing slurred/slowed down, and DRM manual tuning always
  landing on 10 MHz regardless of input — both fixed.
- SDRConnect and decoder subprocesses (DAB/DRM/trunking) now shut down
  cleanly with NEXUS instead of lingering in the background.
- Device-choice popup clicks, USB-detected-late misses, and NEXUS silently
  never re-asking about a USB radio after choosing networked once — all
  fixed.
- A missing helper function meant ACARS/VDL2, WSPR, and Trunk (P25/DMR/NXDN)
  panels could silently fail to update — fixed across every affected panel.
- Packaged macOS builds could refuse to launch DAB/HD Radio/DRM on a Mac
  different from the one they were built on (a missing deployment-target
  pin plus a dylib-bundling gap) — both fixed; builds now correctly target
  macOS 14+.
- The guaranteed connection-error-then-retry on every SDRConnect
  auto-launch is gone — NEXUS now waits for the port to actually be ready.

### Interface

- Combined connection setup into one two-step flow.
- DRM tab redesigned as a clearer three-column layout with quick-tune
  stations as cards.
- Cinematic Mode "Retro" scene fully rebuilt — brass control panel, glowing
  nixie-tube frequency readout, live signal needle, and DAB now-playing
  support.
- Full documentation refresh (User Manual, Quick Start, Troubleshooting)
  covering DRM, HD Radio, and everything above.

### Install

- **macOS:** `DARKSKY_NEXUS_w035_macOS.dmg` (attached below) — now built as a
  universal2 binary (native Apple Silicon + Intel, one download for both)
- **Windows:** `DARKSKY_NEXUS_w035_Setup.exe` (attached below)
- **From source:** `pip install -r requirements.txt && python3 w035_NEXUS.py`, then open `DARKSKY_NEXUS_w035.html`

Docs: [Quick Start](docs/pdf/DARKSKY_NEXUS_w035_QuickStart.pdf) · [User Manual](docs/pdf/DARKSKY_NEXUS_w035_UserManual.pdf) · [Troubleshooting](docs/pdf/DARKSKY_NEXUS_w035_Troubleshooting.pdf) · [Full changelog](CHANGELOG.md)

Website: https://darksky-nexus.base44.app
