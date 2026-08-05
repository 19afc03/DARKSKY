# DARKSKY NEXUS

**Signal intelligence companion for SDRplay receivers.** DARKSKY NEXUS is a WebSocket bridge and browser-based control/decode suite for the SDRplay RSPdx and other SDRplay units, built around [SDRConnect](https://www.sdrplay.com/) — with direct RTL-SDR USB dongle support (via `rtl_tcp`) also available with no SDRConnect required.

🌐 **Website:** [darksky-nexus.base44.app](https://darksky-nexus.base44.app)

Current release: **w035**

## What it does

NEXUS is a single Python backend (`w035_NEXUS.py`) plus a single browser frontend (`DARKSKY_NEXUS_w035.html`) — no build step, no framework, no install beyond Python + a browser. It bridges SDRConnect/RTL-SDR to a live spectrum/waterfall display and a wide catalog of built-in and external decoders, running entirely on your own machine.

### Decoders

| Category | Modes |
|---|---|
| Native (Compact/Full IQ) | FT8, WSPR Beacons, CW, RTTY, PSK31/PSK63/PSK125, NAVTEX, Olivia/Contestia/MFSK/Hell/DominoEX, Marine/VHF, Multimon, Numbers-Station/HF-Intel, FreeDV HF Digital Voice |
| Native (Full IQ) | WEFAX, SSTV, ACARS, Pager/POCSAG, AIS (dual-decoder: rtl-ais + Dire Wolf hybrid, merged by MMSI) |
| Bundled headless engines | DAB/DAB+ (`dab_radio_nexus`, built on [williamyang98/DAB-Radio](https://github.com/williamyang98/DAB-Radio)) — ensemble scan, live audio, DLS text, and MOT slideshow/logo; HD Radio/NRSC-5 (`nrsc5_nexus`, built on [theori-io/nrsc5](https://github.com/theori-io/nrsc5)) — all HD1–HD8 sub-programs at once, ID3 tags, station logo; DRM/DRM+ (`dream_nexus`, built on the [Dream](https://sourceforge.net/projects/drm/) decoder) — shortwave/mediumwave/VHF DRM with a 39-frequency quick-tune list. All three auto-launch with no separate install |
| External engines | ADS-B (dump1090), HFDL (dumphfdl), VDL2 (dumpvdl2), ISM Sensors 433/868/915MHz (rtl_433), Digital Voice (DSD+), Trunked P25/DMR/NXDN (OP25) |

### Other features

- Native **Reporting / Logbook** tab — manual and FT8-auto log entries, ADIF/CSV export, spots-per-band and SNR/DX-distance stats
- PSK Reporter spot upload (WSJT-X bridge, native WSPR, CW Skimmer, and FT8 INTERNAL)
- Live AIS vessel map, ADS-B aircraft map, band-plan strip and bookmarking
- CW Skimmer-style multi-channel scanning with a persistent tuned-decode ticker
- IQ/audio recording (REC)
- Startup connection picker (networked nRSP-ST, local/remote USB SDRplay, or RTL-SDR) with optional auto-launch of SDRConnect (headless or full GUI)

## Install

Prebuilt installers (macOS `.dmg`, Windows `.exe`) are attached to the [latest release](https://github.com/19afc03/DARKSKY/releases/latest).

Or run from source:

```bash
pip install -r requirements.txt
python3 w035_NEXUS.py
```

Then open `DARKSKY_NEXUS_w035.html` in a browser (Chrome/Edge recommended). NEXUS connects to SDRConnect over WebSocket by default, or to a plain RTL-SDR dongle via `rtl_tcp` — see the Quick Start guide below.

External decoder engines (dump1090, dumphfdl, dumpvdl2, rtl_433, DSD+, OP25) are optional, auto-launched by NEXUS if found on `PATH`, and installable via Homebrew/apt/your package manager of choice — each decoder panel shows its own install hint. DAB/DAB+, HD Radio, and DRM/DRM+ are the exception: their engines are bundled directly into the prebuilt installers, so they work out of the box with no separate install — building them from source is only needed if you're running from source yourself (see the Quick Start guide).

## Docs

- [Quick Start](docs/pdf/DARKSKY_NEXUS_w035_QuickStart.pdf)
- [User Manual](docs/pdf/DARKSKY_NEXUS_w035_UserManual.pdf)
- [Troubleshooting](docs/pdf/DARKSKY_NEXUS_w035_Troubleshooting.pdf)
- [Full changelog](CHANGELOG.md)

## Trademarks

DARKSKY NEXUS is an independent, freeware personal and educational project. It is not affiliated with, endorsed by, or sponsored by SDRplay Limited, Xperi Inc., or the DRM Consortium.

- **SDRplay®**, **RSPdx**, **nRSP-ST**, and **SDRconnect** are trademarks of SDRplay Limited. NEXUS interfaces with SDRplay hardware through SDRplay's own SDRconnect application — this is an independent third-party integration, not an SDRplay product.
- **HD Radio™** and the HD Radio logo are trademarks of Xperi Inc. NEXUS's HD Radio decoding is an independent, non-commercial implementation for personal listening, not a licensed or Xperi-authorized HD Radio product. Anyone wishing to build a commercial HD Radio product should contact Xperi directly ([HDRCEManufacturer@xperi.com](mailto:HDRCEManufacturer@xperi.com)).
- **DRM and DRM+** (Digital Radio Mondiale) decoding is implemented against the publicly published DRM standard for personal, non-commercial use. Commercial DRM products require a separate patent royalty license through [Via Licensing Alliance](https://www.via-la.com/) ([info@via-la.com](mailto:info@via-la.com)) and, where Journaline is used, Fraunhofer IIS.

NEXUS is provided free of charge for personal and educational use only, with no warranty. It is not for sale or commercial distribution.

## License

Creative Commons Attribution-NonCommercial 4.0 International — see [LICENSE](LICENSE).
