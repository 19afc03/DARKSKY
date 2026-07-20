## DARKSKY NEXUS w033

The repo's file content was already updated to w033, but GitHub Releases are separate from that — this is the release/tag GitHub Releases actually reads, which is why v1.7.5 was still showing as "Latest."

This release replaces the old `DarkSky v1.x` line entirely with **DARKSKY NEXUS**, a from-scratch rebuild: single-file Python backend + HTML frontend, no build step required to run from source.

### Highlights since v1.7.5

- **AIS** — dual-decoder (rtl-ais + Dire Wolf hybrid front ends, merged by MMSI), live vessel map
- **New decoders** — SSTV, ISM Sensors (rtl_433: TPMS, weather stations, smart meters), HFDL, VDL2, DAB/DAB+, Digital Voice (DSD+), Trunked P25/DMR/NXDN
- **Native Reporting / Logbook tab** — manual + FT8-auto entries, ADIF/CSV export, spots-per-band and SNR/DX-distance stats
- **PSK Reporter** spot upload from WSJT-X bridge, native WSPR, CW Skimmer, and FT8 INTERNAL
- CW Skimmer-style multi-channel scanning, ADS-B aircraft map, band-plan strip, bookmarking, IQ/audio recording
- Full decoder catalog: FT8, WSPR, CW, RTTY, PSK31/63/125, NAVTEX, Olivia/Contestia/MFSK/Hell/DominoEX, Marine/VHF, Multimon, Numbers-Station/HF-Intel, FreeDV, WEFAX, ACARS, POCSAG, ADS-B, plus everything above

### Install

- **macOS:** `DARKSKY_NEXUS_w033_macOS.dmg` (attached below)
- **Windows:** `DARKSKY_NEXUS_w033_Setup.exe` (attached below)
- **From source:** `pip install -r requirements.txt && python3 w033_NEXUS.py`, then open `DARKSKY_NEXUS_w033.html`

Docs: [Quick Start](docs/pdf/DARKSKY_NEXUS_w033_QuickStart.pdf) · [User Manual](docs/pdf/DARKSKY_NEXUS_w033_UserManual.pdf) · [Troubleshooting](docs/pdf/DARKSKY_NEXUS_w033_Troubleshooting.pdf) · [Full changelog](CHANGELOG.md)

Website: https://darksky-nexus.base44.app
