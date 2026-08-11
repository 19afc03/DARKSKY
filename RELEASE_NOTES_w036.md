## DARKSKY NEXUS w036

Full gain/AGC/overload controls, four new Cinematic Mode scenes plus a
cross-scene visual FX layer, a hardened AIS decode pipeline, and a big
batch of reliability fixes found through systematic testing against
real captured IQ files.

### New: Gain, AGC & Overload controls (Ch.8 parity)

Implements the SDRplay owner's manual's gain/AGC/overload chapter in
full:

- **RF Gain panel** — click the GAIN stat in the top bar for a slider
  with a true gain-index readout and an ATT button. SDRplay hardware
  reports gain as an LNA-state index where a *lower* index means *more*
  gain — the slider is always drawn so right/up means more gain, with
  the true raw index shown underneath so the inversion is never hidden.
- **AGC threshold** — a dedicated threshold slider next to the AGC
  ON/OFF button (default ~30, the manual's suggested starting point).
  Automatically disables itself once tuned to WFM, matching SDRConnect's
  own on/off-only behaviour in that mode.
- **Real OVERLOAD banner** — now actually appears when SDRConnect
  reports ADC clipping, with a gain-reduce button and notch-filter
  guidance.
- **GAIN GUIDE wizard** — a guided 5-step walkthrough for setting gain
  correctly from a quiet spot on the band.
- Fixed two related bugs along the way: the existing "reduce gain"
  button moved the SDRplay gain index in the wrong direction (making
  overload worse, not better), and AGC ON/OFF wasn't reliably reaching
  SDRConnect due to a case-mismatch in the boolean sent over the API.

### New: Cinematic Mode — four new scenes plus a cross-scene FX layer

Cinematic Mode grew from 5 scenes to 9: **Orbit** (planetary sweep),
**Grid** (tactical HUD), **Topology** (signal terrain), and **Theater**
("Now Showing" — decoder captions and a title card). A new "Part B" FX
layer (film grain, scanlines, ambilight edge bleed, idle-fade chrome,
flash pulse and boot splash) now overlays every scene, plus a per-scene
colour palette picker.

### New: In-GUI Start/Stop stream control

Start and stop the SDRConnect stream directly from NEXUS instead of
needing SDRConnect's own window.

### AIS decoding hardened

A full external-review pass over the AIS decode pipeline: stricter
message-type/bit-length validation, per-field source and timestamp
provenance, extended MMSI plausibility checks, tuner-offset digital
remixing, UDP/NMEA hardening, raw-frame diagnostic logging, and a
capture-based regression suite validated against real off-air IQ.

### CW decoder DSP overhaul

Reworked filtering (decimate-after-mixdown, speed-aware bandwidth),
fixed dot/dash classifier boundary and debounce/hysteresis behaviour,
richer handling of unrecognised Morse patterns, and hardened
Skimmer-pool candidate detection and PSK Reporter spotting.

### Reliability & bug fixes

- Systematic testing against real captured IQ files (7 sample
  recordings across CW, ACARS, AIS, SSTV, WEFAX) turned up and fixed a
  real ACARS crash plus a preamble-sync bug, and a WEFAX phasing-sync
  gap.
- Spectrum/waterfall trace could visibly misalign with the tune line
  near the bottom of a wide-span band (a display-clamping mismatch
  between the axis and the renderers) — fixed.
- Dragging the frequency axis to pan felt slow/laggy — fixed (redraw
  work is now throttled to once per animation frame instead of once per
  raw mouse-move event).
- Frequency Lists: a CSV-import delimiter mis-sniff and a kHz/MHz unit
  bug could scramble imported station lists; FM entries quick-tuned
  with the wrong (narrowband) bandwidth; the green "In range" badge's
  wording was easy to misread as a signal-strength claim — all fixed or
  clarified.
- Full IQ on nRSP-ST could produce zero binary IQ frames under certain
  connect sequences — fixed.
- Switching from Compact to Full IQ could deadlock SDRConnect's event
  channel entirely — fixed.
- DX Spots timeout error — switched to plain HTTP.
- Several DAB fixes: GRID scene text/bar overlap, Now Playing hero
  avatar stuck on initials, non-BBC-Guide station logos never appearing
  on shared-carousel ensembles.

### Removed

- **rtl_433** (ISM-band sensor decoding) removed completely — its
  networked-SDR limitations meant it never worked reliably against
  NEXUS's primary SDRplay/SDRConnect signal path.

### Also in this release

- Early Linux build support (`build_Linux.sh`, PyInstaller spec) — code
  is in place but not yet verified end-to-end on a physical Linux
  machine; treat as experimental if you try it.
- macOS builds continue to ship as two separate downloads (Apple
  Silicon / Intel) rather than a universal2 binary — this was tried
  again and reverted, same as w035.

### Install

- **macOS (Apple Silicon):** `DARKSKY_NEXUS_w036_macOS_AppleSilicon.dmg` — for M1/M2/M3/M4 Macs
- **macOS (Intel):** `DARKSKY_NEXUS_w036_macOS_Intel.dmg` — for Intel Macs. Not sure which you have? Apple menu → About This Mac tells you.
- **Windows:** `DARKSKY_NEXUS_w036_Setup.exe`
- **From source:** `pip install -r requirements.txt && python3 w036_NEXUS.py`, then open `DARKSKY_NEXUS_w036.html`

Docs: [Quick Start](docs/pdf/DARKSKY_NEXUS_w036_QuickStart.pdf) · [User Manual](docs/pdf/DARKSKY_NEXUS_w036_UserManual.pdf) · [Troubleshooting](docs/pdf/DARKSKY_NEXUS_w036_Troubleshooting.pdf) · [Full changelog](CHANGELOG.md)

Website: https://darksky-nexus.base44.app
