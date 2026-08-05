# DARKSKY NEXUS w035 — Build History

WebSocket bridge and signal intelligence companion for SDRplay RSPdx and
compatible SDRplay receivers. Interfaces with SDRConnect via WebSocket.
Also supports RTL-SDR USB dongles via rtl_tcp (direct, no SDRConnect needed).

© 2025 Jon Nicol & Claude / Anthropic — Freeware, personal & educational use.

DARKSKY NEXUS is not affiliated with, endorsed by, or sponsored by SDRplay
Limited, Xperi Inc., or the DRM Consortium. SDRplay, RSPdx, nRSP-ST, and
SDRconnect are trademarks of SDRplay Limited. HD Radio is a trademark of
Xperi Inc.; NEXUS's HD Radio decoding is an independent, non-commercial
implementation for personal listening, not a licensed Xperi product. DRM/
DRM+ decoding is implemented against the published open DRM standard for
personal, non-commercial use. See Appendix C in the User Manual for the
full trademark and licensing notice.

### Changed: macOS distribution model reverted from universal2 to two separate single-arch builds (2026-08-05)

Same day universal2 shipped, reverted it. The main Python app merges into
a universal2 binary cleanly — every C-extension dependency has prebuilt
wheels for both arches — but the three bundled companion engines (DAB, HD
Radio, DRM) are each a separately compiled C/C++ binary with its own
native library chain (librtlsdr, libusb, libfftw3f, libnrsc5, Dream's own
deps). There's no "pip install --only-binary" equivalent for those;
cross-compiling and lipo-merging three more binaries — and every dylib
each one links against — is a much bigger, more fragile undertaking than
the Python side ever was, for a benefit (one download instead of two) that
doesn't outweigh it. `build_macOS.sh` now produces two separate downloads
— `DARKSKY_NEXUS_w035_macOS_AppleSilicon.dmg` and
`DARKSKY_NEXUS_w035_macOS_Intel.dmg` — matching the existing Windows
build's single-target model. Companion engines are now looked up
per-architecture (`build/bundled/<arch>/<name>`); the DAB/HD Radio engines
currently only have arm64 builds, so the Intel download ships without
those two working until x86_64 versions are built and placed there — a
known, explicitly-flagged gap, not a regression introduced by this change
(they were never universal2 either, even during the one day universal2
was live). See BUILD_NOTES.md's "Two Separate Builds" section for the
full technical writeup.

### Fixed: universal2 x86_64 build could pick up wrong-architecture packages from a shared site-packages directory (2026-08-05)

Found live producing the first real universal2 `.dmg`: the x86_64 build
pass kept failing PyInstaller's COLLECT stage with
`IncompatibleBinaryArchError` on a different package each retry (first
numpy/cryptography, then cryptography again via a source-build fallback,
then markupsafe — a transitive import never even listed in
requirements.txt). Root cause: the machine's x86_64 Python
(`/usr/local/bin/python3`, a python.org universal2 framework install) has
exactly ONE site-packages directory shared by both its arm64 and x86_64
slices, so any package ever installed there under the native arm64 slice
sits as a wrong-arch `.so` indefinitely — no per-package fix could close
this off, since PyInstaller can surface a new offender from anywhere in
the dependency graph. Fixed properly: `build_macOS.sh` now installs the
x86_64 dependencies into a throwaway venv (`build/venv_x86_64`), wiped and
recreated fresh on every run, instead of into that shared framework
site-packages at all — nothing can leak in by construction. The
PyInstaller x86_64 pass now also runs against that venv's Python.
`--only-binary=:all:` (added earlier the same day) is kept alongside this,
since it solves an independent problem: source builds of Rust-extension
packages like `cryptography` not respecting the `arch -x86_64` wrapper.
First confirmed successful universal2 `.dmg` build same day.

### Fixed: build_macOS.sh shipped zero bundled docs since the docs/pdf layout gained per-version subfolders (2026-08-05)

Caught live running the first real build after the universal2 change
above: `Copied docs: 0 PDF(s) into Resources/Docs`. `DOCS_SRC` pointed at
`docs/pdf` directly; the real PDFs live at `docs/pdf/w035/` (a per-version
subfolder added at some point after the original w031 fix for this exact
"no docs got bundled" problem — see that fix's own comment, still in the
script). So every build since that subfolder was introduced has silently
shipped without the Quick Start/User Manual/Troubleshooting PDFs in either
the app bundle's Resources or the DMG's top-level Docs folder — same
symptom as the w031 bug, different cause. Fixed by pointing `DOCS_SRC` at
`docs/pdf/$APP_VERSION_TAG` instead. Also fixed an unrelated cosmetic bug
in the same section: an unquoted `$(basename $f)` on a path containing
spaces ("Darksky Project") printed the filename split across two lines.

### macOS build is now universal2 (arm64 + x86_64), automatically (2026-08-05)

`build_macOS.sh` now produces a genuine universal2 `.app` by building the
whole PyInstaller pipeline twice — once under a native arm64 Python, once
under a native x86_64 Python (Intel Homebrew running under Rosetta 2 on
Apple Silicon, the normal case) — and merging the two resulting bundles
file-by-file with `lipo -create` wherever a Mach-O file differs between
them (main executable, every bundled `.so`/`.dylib`), then re-signing the
merged app ad-hoc. Non-Mach-O files (Info.plist, bundled HTML/CSV/PDF
data) are copied once, since they don't vary by architecture.

Deliberately does NOT use PyInstaller's own `target_arch='universal2'`
spec setting — that only produces a real universal2 binary if the Python
interpreter itself is a universal2 framework build AND every C-extension
dependency (numpy, scipy, sounddevice, paramiko's cryptography) ships a
universal2 wheel, neither of which holds for a typical Homebrew Python
install; it would silently produce a single-arch binary while claiming
success. `DARKSKY_NEXUS_macOS.spec`'s `target_arch` now reads a
`NEXUS_BUILD_ARCH` env var the script sets explicitly per invocation
instead, so each single-arch build is unambiguous rather than relying on
auto-detect.

**Cross-arch Python requirement:** needs a second, opposite-architecture
Python on the build machine (e.g. Intel Homebrew at `/usr/local` on an
Apple Silicon Mac). The script detects whether this is present; if not,
it prints the exact `softwareupdate`/`brew` setup commands and falls back
to today's single-arch build with a clear warning in both the running log
and the final summary — never fails, never silently claims a single-arch
build is universal. Going the other direction (building arm64 from an
Intel Mac) isn't possible via Rosetta, since Rosetta only translates
x86_64 code to run on arm64 hardware, never the reverse — that direction
needs actual Apple Silicon hardware.

**Companion engines (DAB/HD Radio/DRM) made universal2-capable too, per
explicit request** (not just the main app, which was the recommended
default): each engine's own `NEXUS_*_build_macOS.md` gained a new
"Universal2 build" section documenting the same build-twice-then-`lipo`
pattern for the engine's own executable and its bundled Homebrew-sourced
dylibs (`libfftw3f.3.dylib` for DAB; `libnrsc5.dylib` +
`libfftw3f.3.dylib` + `librtlsdr.0.dylib` + `libusb-1.0.0.dylib` for HD
Radio; `libspeexdsp.1.dylib` + `libfftw3.3.dylib` (double-precision —
distinct file from DAB/HD Radio's float variant) + `libfdk-aac.2.dylib` +
`libsndfile.1.dylib` + `libportaudio.2.dylib` for DRM). These are manual,
by-hand build docs (companion engines are built outside this repo's own
build scripts) — not yet verified end-to-end on a real build, unlike the
rest of each doc's steps.

`build_macOS.sh`'s companion-engine check (Step 4, renumbered from
3b/3c/3d) now also reports each bundled engine's `lipo -archs` output and
flags single-arch engines explicitly — a single-arch companion engine
bundled inside an otherwise-universal2 app would silently fail to launch
on whichever architecture it's missing, since the main app itself would
still launch fine, masking the gap.

`BUILD_NOTES.md`'s "Universal Binary" section rewritten to describe what
the script now does automatically, replacing stale manual-lipo guidance
that predated this work.

### Trademark/affiliation notice added (2026-08-04) — see CHANGELOG entry above and UserManual.docx Appendix C

### Wired, not yet tested (2026-08-03) — dream_nexus Windows bundling plumbing + new build doc

Following macOS's dream_nexus bundling being fully confirmed (see the
entry directly below), started the equivalent Windows work. Unlike
macOS, HD Radio's own Windows build doc (`NEXUS_nrsc5_build_windows.md`)
was already written back on 2026-07-30 but never build-tested — both HD
Radio and DRM now need a real live build pass on Windows.

**Spec/bat plumbing (mirrors DAB/HD Radio's existing pattern exactly):**
`DARKSKY_NEXUS_Windows.spec` now checks for `build\bundled\dream_nexus.exe`
and bundles it automatically if found — plus, unlike DAB/HD Radio, it
also globs and bundles any `.dll` files sitting alongside it in
`build\bundled\`, since (per the plan below) this build isn't expected to
be fully static the way DAB's vcpkg build is. `build_Windows.bat` gained
a matching "Checking for bundled DRM engine..." informational step
(Step 3d), same pattern as the existing DAB/HD Radio checks. Confirmed
`_drm_find_binary()` in `w035_NEXUS.py` already had full Windows PATH-search
support (`dream_nexus.exe`, `C:\dream_nexus\dream_nexus.exe`,
`%LOCALAPPDATA%\dream_nexus\dream_nexus.exe`) from whenever the DRM
integration was originally written — no Python changes needed, this was
purely a build-script gap.

**New doc:** `NEXUS_dream_drm_build_windows.md` — written following the
same honest "not yet build-tested" convention every other Windows doc in
this project started with. Planned route: Qt's official MSVC kit (not
MinGW) for `qmake`, plus vcpkg's **dynamic** triplet (`x64-windows`, not
DAB's static `x64-windows-static`) for the five dependencies
(fftw3/speexdsp/libsndfile/fdk-aac/portaudio) — the dynamic choice is
deliberate: Qt's prebuilt MSVC kits use the dynamic MSVC runtime, and
pairing that with vcpkg's static triplet risks the same
`LNK2038: mismatch detected for 'RuntimeLibrary'` class of error DAB's
own Windows doc hit and fixed via `CMP0091`, except qmake has no
equivalent single-flag fix for that the way CMake does. Carries forward
the macOS doc's confirmed "dream_nexus links zero Qt frameworks/DLLs at
runtime" finding as an expectation to verify, not yet confirmed on
Windows.

### Confirmed (2026-08-03) — dream_nexus macOS bundling proven end-to-end; all three companion engines now confirmed

`dream_nexus` (DRM/DRM+) rebuilt from source with `MACOSX_DEPLOYMENT_TARGET=14.0`
and fully bundled into `build/bundled/`, completing the same treatment
already proven for `dab_radio_nexus` and `nrsc5_nexus` below. Resolved
this doc's own previously-flagged uncertainty: `dream_nexus` links **zero**
Qt frameworks (confirmed via its real saved link command,
`~/dream/link_dream_nexus.sh` — only `speexdsp`/`fftw`/`libsndfile`/
`fdk-aac`/`portaudio` plus macOS system frameworks), so the simple
DAB/nrsc5-style `install_name_tool` loop applies; `macdeployqt` was never
needed.

Needed **five** from-source dependencies — the most of any of the three
engines — because Homebrew's own bottles for `speexdsp`, `fftw`,
`libsndfile`, `fdk-aac`, and `portaudio` are all built against whatever
macOS version the bottle was compiled on, and (confirmed empirically)
Homebrew's `superenv` build system ignores `MACOSX_DEPLOYMENT_TARGET`
even under `--build-from-source`. All five were built from source outside
Homebrew into the same shared `~/fftw-local` prefix already used for DAB
and nrsc5's own from-source deps — `fftw` needed a second, double-precision
build alongside the existing float build (`libfftw3.3.dylib` for dream vs.
`libfftw3f.3.dylib` for DAB/nrsc5), reusing the same source tree via
`make distclean` + reconfigure. `libsndfile` was built with
`-DENABLE_EXTERNAL_LIBS=OFF`/`-DENABLE_MPEG=OFF` to avoid pulling in
further Homebrew-bottled codec deps it doesn't need. All six bundled files
(`dream_nexus` + 5 dylibs) confirmed `minos 14.0` and fully
`@executable_path`-relative — no absolute Homebrew/`/Users/...` paths
left anywhere in the chain — and `dream_nexus --help` runs cleanly
straight out of `build/bundled/`.

`NEXUS_dream_drm_build_macOS.md`'s Step 6 rewritten to document the real
confirmed recipe in place of the earlier speculative Qt-branching
language.

**All three w035 companion engines (DAB, HD Radio, DRM) are now confirmed
bundled end-to-end for macOS distribution at `minos 14.0`.**

### Confirmed (2026-08-02) — dab_radio_nexus and nrsc5_nexus macOS bundling proven end-to-end

Both engines rebuilt from source with `MACOSX_DEPLOYMENT_TARGET=14.0` and
fully bundled into `build/bundled/` with zero remaining Homebrew/dev-machine
dylib references — confirmed via `otool -L`/`otool -l` on every file, and
by actually running each binary straight out of `build/bundled/` (the real
deploy location, not the build tree).

**dab_radio_nexus:** links against a from-source `libfftw3f.3.dylib`
(Homebrew's own bottle can't be re-targeted — its `superenv` build system
ignores `MACOSX_DEPLOYMENT_TARGET` and always targets the current OS).
Reconfigured DAB-Radio's own cmake to link directly against the custom
fftw build via `CMAKE_PREFIX_PATH`/`PKG_CONFIG_PATH`, avoiding any
dylib-swap version-compatibility risk. Both files confirmed `minos 14.0`.

**nrsc5_nexus:** turned out to need three from-source dependencies, not
one — `libfftw3f.3.dylib` (shared with DAB, same build reused), plus
`librtlsdr` and `libusb` (neither anticipated in the original build doc,
which had guessed `libao`/FAAD2 as the Homebrew deps needing bundling;
those turned out to only matter for nrsc5's own unused CLI demo tool, not
`libnrsc5.dylib`). `nrsc5`'s CMake option `-DUSE_SYSTEM_RTLSDR=OFF`
(vendor-build librtlsdr statically, avoiding the dylib entirely) was
attempted first but hit a real upstream bug — current `osmocom/rtl-sdr`
installs `librtlsdr.a`, but nrsc5's CMakeLists.txt expects
`librtlsdr_static.a` — so librtlsdr and libusb were both built from
source independently instead, into the same shared `~/fftw-local`
prefix used for fftw. All four bundled files (`nrsc5_nexus`,
`libnrsc5.dylib`, `librtlsdr.0.dylib`, `libusb-1.0.0.dylib`) confirmed
`minos 14.0` and fully `@executable_path`-relative — no absolute
Homebrew/`/Users/...` paths left anywhere in the chain.

`NEXUS_nrsc5_build_macOS.md`'s Step 6 rewritten to document the real
recipe in place of the original speculative one.

### Fixed + Added (2026-08-02) — macOS release bundling: dylib bundling bug, DRM bundling plumbing added

**Bugfix:** `DARKSKY_NEXUS_macOS.spec` bundled the DAB/HD Radio engine
executables into the packaged `.app` but never bundled the Homebrew
dylibs sitting alongside them in `build/bundled/` (e.g.
`libfftw3f.3.dylib` for DAB) — each build doc's own bundling steps
repoint the executable's dependency to `@executable_path/...`, which only
resolves if that dylib is actually present next to the binary at
runtime. PyInstaller only collects files explicitly listed in
`Analysis(binaries=...)`, so the dylib silently never made it into the
real packaged app, even though manual testing (running the binary
straight out of `build/bundled/`, where the dylib happens to sit right
there) never caught it. Fixed: the spec now bundles every `.dylib` in
`build/bundled/` alongside whichever engine executable(s) are present,
deduplicated.

**Added:** DRM (`dream_nexus`) bundling plumbing — `build_macOS.sh`
(new Step 3d check) and the `.spec`'s binaries list never had any
bundling support for it at all, unlike DAB and HD Radio (a real gap, not
a stale reference — DRM's own live-wiring is still in progress). The
Python side was already ready (`_drm_find_binary()` already checks
`sys._MEIPASS` for a bundled copy, mirroring `_dab_find_binary()`/
`_hd_find_binary()` exactly) — only the build script and spec needed the
same plumbing the other two engines already had.

**Also (2026-08-02):** all three companion-engine build docs
(`NEXUS_dab_radio_build_macOS.md`, `NEXUS_dream_drm_build_macOS.md`,
`NEXUS_nrsc5_build_macOS.md`) now explicitly pin
`MACOSX_DEPLOYMENT_TARGET=14.0` — building on a newer macOS (e.g.
Tahoe/26) without this silently stamps the CURRENT OS as each binary's
minimum required version, which macOS's own loader then enforces at
launch (refuses to run on Sequoia/Sonoma, no explanatory error). Confirmed
live: the `dab_radio_nexus` and `libfftw3f.3.dylib` already sitting in
`build/bundled/` (built 2026-07-26, before this fix) both reported Min OS
26.0.0 via `otool -l` — genuine, not theoretical. `build_macOS.sh` and
`DARKSKY_NEXUS_macOS.spec` were already fixed for the main app itself in
an earlier pass this session (`MACOSX_DEPLOYMENT_TARGET` export +
`LSMinimumSystemVersion`).

### Diagnostic (2026-08-01) — "no ensemble detected" on 12B traced to dab_radio_nexus being SIGTERM'd ~30s after launch, not a scan failure

Live report: DAB started cleanly on 12B, fed real IQ for ~30s (confirmed by
frame counters), then no ensemble ever appeared. Added returncode logging to
`dab_engine()`'s watchdog (w035_NEXUS.py) revealed the subprocess wasn't
crashing — it was found already dead with `returncode=-15` (SIGTERM) right
before being silently relaunched, meaning something in NEXUS itself killed
it mid-scan.

`_dab_proc.terminate()` only has one call site in the whole file —
`_dab_terminate()` — which itself is only reachable from 3 places: the
`dab_stop` WS handler, the `dab_set_channel` WS handler, and
`dab_engine()`'s own graceful-stop branch. None of the three had an obvious
trigger in the captured log (no `dab_stop`/retune from the frontend visible
in the ~30s window). Added a one-time diagnostic: `_dab_terminate()` now
logs a short call stack whenever it fires against a still-running
subprocess, so the next reproduction pins down exactly which of the three
call sites — or an as-yet-unfound fourth one — is actually firing.

Python-only change, no C++ rebuild required — just restart NEXUS.

### Diagnostic (2026-08-01) — instrumented shared-carousel MOT Slideshow data to find why individual stations never get a logo on ensembles with a "Guide"-style shared data service

Live report on 12B: tuning to "BBC Guide" shows a real slideshow image, but
tuning to an ordinary station (e.g. BBC Radio1Dance) on the same ensemble
never gets one — "No slideshow image yet" permanently.

Root cause hypothesis (grounded in DAB-Radio source, not yet confirmed
live): `resolve_audio_subchannel_for_data_component()` in
`dab_radio_nexus.cpp` re-tags every slideshow image from a data-packet
component with the subchannel of whichever service *owns* that physical
data component. Services like "BBC Guide" own their own data component, so
their images always resolve correctly — but this means a single shared MOT
carousel broadcasting a *directory* of every station's logo (a known
real-world DAB pattern) can only ever reach the one owning service, never
the other stations whose logos it's actually carrying. DAB-Radio's own
`Basic_Slideshow` struct (`basic_slideshow.h`) already carries per-object
fields (`name` / MOT ContentName, `category_id`, `slide_id`,
`category_title`, `transport_id`) that our code currently discards — these
are the likely place the broadcaster encodes which station each image in
the carousel belongs to.

Added two new `dab_debug` stderr events to `dab_radio_nexus.cpp`, both
diagnostic-only (no behaviour change yet):
- `slideshow_meta` — dumps every per-object field on `Basic_Slideshow`
  (name/category_id/slide_id/category_title/transport_id/trigger_time/
  expire_time) for every image completed on the MSC packet-mode path,
  before it gets reduced to raw image bytes for the wire.
- `service_components_dump` — dumps every service (SId + label) and every
  service component including data components (SId, component_id,
  subchannel_id, transport_mode, label), fired once per newly-discovered
  data packet channel, so `slideshow_meta`'s fields can be hand-correlated
  against real station SIds/labels.

Next: capture these logs live on 12B while BBC Guide's carousel is running,
identify the actual encoding, then build a cross-station mapping so an
individual station's logo resolves correctly instead of only the carousel's
owning service. Scoped purely to the packet-mode "shared carousel" case —
does not touch the already-working PAD slideshow path or the temp-file
delivery mechanism.

### Fixed (2026-08-01) — DAB audio played ~10 seconds then went silent on every channel, after the MOT Slideshow FEC-gate patch

Direct follow-up to the FEC-gate patch and its diagnostic instrumentation
below. Live report, reproduced twice in a row on a fresh SDRConnect
restart (ruling out the earlier session's crash as the cause): audio
played for roughly 10 seconds after selecting any channel, then went
silent, every time. The new `dab_debug` instrumentation made the cause
directly visible in the log: `packet_slideshow_complete` fired **20+
times within about a minute**, several images 10-22KB each, immediately
followed by the reported silence window.

Root cause: `write_frame()` (real-time audio PCM, the `"DAB1"` stdout
frame) and `write_slideshow()` (MOT images, `"DAB2"`) shared the exact
same `StdoutFrameWriter::m_mutex` *and* the exact same OS stdout pipe —
harmless while packet-mode slideshow was still gated off entirely (see
the FEC-gate entry below), but the fix that unblocked it also unblocked a
genuinely busy MOT carousel on this ensemble. A single OS pipe has a
small kernel buffer; once the image traffic backed it up, the blocking
`fwrite()`/`fflush()` call stalled whichever thread was holding
`m_mutex` at the time — which stalled *every* other subchannel's
`write_frame()` too, since they all share that one lock. `_serve_dab_audio()`
already has its own 10-second staleness timeout that closes the HTTP
audio stream once no new PCM arrives (added long before this bug, for a
different reason) — that's exactly what "10 seconds then silence" was.

Fix: `write_slideshow()` no longer touches stdout or `m_mutex` at all.
Each completed image is now written to a small OS temp file
(`std::filesystem::temp_directory_path()`), and only a short JSON pointer
(`{"type":"dab_slideshow_file","path":"...",...}`, not the image bytes)
goes out over the existing stderr status channel — stdout is audio-only
again, exactly as it was before this feature existed. `w035_NEXUS.py`'s
`_dab_stderr_thread_fn()` reads the file directly (off the hot audio
path entirely), caches/broadcasts it exactly as the old inline frame
used to, then deletes the temp file. Requires a further
`dab_radio_nexus` rebuild — same clone/patch/build cycle as the FEC-gate
fix.

### Diagnostic (2026-08-01) — instrumented both MOT Slideshow transports in dab_radio_nexus.cpp to pin down why logos still don't appear after the DAB-Radio library patch

Direct follow-up to the FEC-gate patch below. User applied the two `sed`
patches to their local `~/DAB-Radio` checkout and rebuilt, but the logo
still never appeared — with genuinely no way to tell from the existing
wire protocol *why*: whether the patch didn't actually take effect in the
running binary, whether a `Basic_Data_Packet_Channel` is now being
constructed but no MOT object is ever completing, or whether the problem
is actually downstream in NEXUS's own Python/JS delivery path (the
2026-08-01 fix two entries below).

Added a shared `emit_debug()` stderr-JSON emitter and four call sites:
`pad_slideshow_complete` (PAD/X-PAD transport, in `attach_audio_channels()`)
and `data_packet_channel_discovered` + `packet_slideshow_complete`
(MSC packet-mode transport, in `attach_data_packet_channels()`). The
`data_packet_channel_discovered` line firing at all is the direct,
unambiguous proof the local library patch actually took effect — if it
never appears, the patch isn't live in whatever binary is actually
running (stale build, wrong binary earlier on PATH than
`/usr/local/bin`). `w035_NEXUS.py`'s `_dab_stderr_thread_fn()` now handles
`dab_debug` messages with `log.warning`, so all of this surfaces directly
in the console without needing to enable `--radio-enable-logging` (which
the 2026-07-27 investigation already found degrades live audio across a
full multi-service ensemble). Diagnostic only — no behavioural change;
requires the same rebuild + reinstall cycle as the FEC-gate patch before
it takes effect.

### Fixed (2026-08-01) — DAB station logos (MOT Slideshow) never appeared, even though audio/DLS/EPG all worked correctly

Live diagnostic request: "why do DAB/DAB+ station logos never appear, even
though audio, PAD/DLS, and EPG decoding all work correctly." Traced end to
end through `dab_radio_nexus.cpp`'s FIC/MSC/MOT wiring (both the PAD-based
and, since the 2026-07-27 fix, MSC packet-mode `Basic_Data_Packet_Channel`
transports — see that entry's own comment for the BBC Radio6Music
investigation that added the second path) and confirmed the whole decode
chain was correct: completed slideshow images were being reassembled and
written to `w035_NEXUS.py`'s `_dab_slideshow[subchannel_id]` cache exactly
as designed.

The actual break was one hop further downstream, in the WebSocket delivery
path — not a decode bug at all. `_dab_stdout_thread_fn()` only ever
broadcast a freshly-arrived slideshow image ONCE, live, to whichever
browsers happened to be connected at that exact instant. The frontend's
`dabUpdateSlideshow()` only accepts an image if it's for whatever station
is *already* `_dabPlayingSid` at that moment. But `dab_radio_nexus` decodes
every discovered subchannel simultaneously in the background from the
moment the ensemble locks — regardless of what the user has clicked
"Play" on — so in practice a station's logo is almost always decoded and
broadcast-and-discarded well before the user ever selects that station.
After that, nothing ever re-sent it: `_dab_slideshow`'s cached bytes were
only ever read back once more anywhere in the file, purely to set an
informational `has_slideshow: true` flag on the next `dab_ensemble`
snapshot (never the actual image bytes) — no `dab_get_slideshow` command,
no `/dab_slideshow?sid=` HTTP endpoint (unlike audio's own `/dab_audio`),
and the existing `dab_play_service` WS handler was a pure
`state['dab_play_sid'] = sid` state flip with no cache lookup at all. A
code comment at the frontend call site had explicitly flagged this exact
gap as a known, accepted limitation at the time DLS's own
snapshot-hydration was added (2026-07-25) but never closed for slideshow.

Fix: `dab_play_service`'s WS handler now looks up the target service's
real `subchannel_id` and, if `_dab_slideshow` already has a cached image
for it, unicasts it to just that client immediately in the exact same
`dab_slideshow` message shape the live broadcast already uses — so
`dabUpdateSlideshow()` on the frontend needed zero changes. Deliberately
keys the lookup off `subchannel_id` (always correct) rather than the
`sid` that happened to be resolved at original-broadcast time, which
sidesteps a related edge case: a slideshow arriving before FIC has
finished populating `_dab_services` would previously be cached correctly
but broadcast with `sid: None`, making it permanently unmatchable by the
frontend's `msg.sid !== _dabPlayingSid` check even on a lucky live-timing
hit. Also added the equivalent hydration to `browser_handler()`'s
initial-state block for `state.get('dab_play_sid')`, so a browser refresh
while a station with an already-decoded logo is playing no longer blanks
it either.

### Fixed (2026-07-31) — DAB still found zero ensembles after the sample-rate-confirmation fix, even against a strong, visually confirmed OFDM signal

Direct follow-up. After the sample-rate snap-back guard fix below, a fresh
live test confirmed the resampler was now correctly computing
`2000000 Hz -> 2048000 Hz (ratio 128/125)` on every channel — but a manual
retune to 12B (BBC National DAB) still showed "No ensemble locked", despite
a screenshot showing a strong, clearly OFDM-shaped ~1.5MHz-wide signal
sitting right on 225.648 MHz (+1.7dB SNR, -79dBm, gain 16dB, Antenna A) —
ruling out "nothing on air" or an antenna/gain problem the same way the
2026-07-30 DRM 125kSPS bug was ruled in.

Root cause: `dabStart()`'s `setSampleRate(2000000)` request and its
`sendCmd({cmd:'dab_start'})` call fired in the same synchronous tick — even
with the confirmation now getting through NEXUS's own state correctly, the
RSPdx hardware itself still needs real time to physically finish retuning
its ADC clock after a sample-rate change. Every other retune-adjacent path
in this file already builds in a settle wait (server-side
`_DAB_RETUNE_SETTLE_S` drops IQ for 1s after a channel change;
`device_release_wait` waits ~2s for SDRConnect to release a device before
relaunching) — this one had none, so `dab_radio_nexus` could start reading
IQ before the hardware had actually finished switching rate, not just
before NEXUS's own bookkeeping caught up.

Fix: `dabStart()` is now `async` and, only when it actually had to change
the rate, awaits a 2s settle delay before sending `dab_start`. Skipped
entirely when the rate was already 2 MSPS (repeat starts, or after a scan
already set it), so no needless delay on the common case.
`dabScanChannels()` now `await`s `dabStart()` directly instead of firing it
and racing a fixed sleep against it.

Traced via a timeline audit request ("give me a timeline... in case we need
to select a rollback point"): last confirmed real ensemble decode was
2026-07-27 in w034, on this exact channel (12B). `dabStart()`'s
`setSampleRate(2000000)` auto-call was added 2026-07-30, in the same batch
of work as DRM's own sample-rate fix — the two live bugs found today (the
snap-back guard below, and this settle-timing gap) are both regressions
introduced by that one change, not anything DAB's own DSP code did wrong.
A full rollback wasn't needed; both bugs were fixable in place once traced.

### Fixed (2026-07-31) — DAB scan launched cleanly on every channel but found zero ensembles

Live user report: "ive just scan dab, and nexus is not picking up any
ensembles." Log showed `dab_radio_nexus` launching and running cleanly on
all ~38 Band III channels, with NEXUS logging `"DAB: resampling 5000000
Hz -> 2048000 Hz"` on every single one — identical every time, never
changing, even right after DAB's own `dabStart()` had just requested
SDRConnect switch to 2 MSPS. That request log line
(`"SDRConnect sample rate → 2.0000 MSPS"`) is only the outgoing request,
not confirmation — the real bug was that the confirmation never got
applied.

Root cause: a pre-existing "snap-back guard" (`_sr_set_time`, inherited
from the w026-era codebase) unconditionally ignores every
`device_sample_rate` update from SDRConnect for 3 seconds after any
`set_sample_rate` command, to stop a stale echo of the OLD rate from
clobbering a fresh user choice. It never distinguished a stale echo from
the genuine confirmation of the NEW rate — it just dropped everything in
that window. `dabStart()` (added 2026-07-30) chains
`setSampleRate(2000000)` straight into `dab_start` with no delay, so DAB
began reading `state['hw_sample_rate']` well inside that 3s guard.
SDRConnect's real confirmation of the switch to 2 MSPS arrived during the
window and was silently dropped, and nothing else re-queried it
afterward — so `state['hw_sample_rate']` stayed frozen at the stale
pre-DAB value (5,000,000 Hz) for the rest of the session. `_dab_feed_iq()`
kept computing its resample ratio (256/625) against that stale 5 MSPS
figure while the real IQ bytes were actually arriving at 2 MSPS, corrupting
the timebase of every packet fed to `dab_radio_nexus` — explaining clean
launches with zero real decodes.

Fix: new `_sr_set_target` remembers the exact rate just requested; the
guard now reads `time.time() - _sr_set_time > 3.0 or hw_sr == _sr_set_target`
— a confirmation matching the requested rate is always accepted
immediately, regardless of the 3s window, since it can never be a stale
echo of something else. Stale echoes of any OTHER rate are still
correctly suppressed for the full 3s as before.

### Added (2026-07-31) — Startup sequence UX pass: live status strip, ambiguity-vs-auto-stream race fixed, combined connection+launch picker

User request after today's whole DAB/Result-108 saga: "examine the start
up sequence for the user, as even for me it's a bit disjointed." Audit
found the actual sequence was almost entirely invisible in the UI — every
real decision (auto-launching SDRConnect, connecting, device ambiguity,
final device confirmation) only ever showed up as a Python console log
line, and `connection_mode`/`local_launch_mode` were two separate config
axes in two different wizard panes that could silently disagree (exactly
what caused today's Result-108 confusion). Three changes:

- **Live startup status strip.** New `_broadcast_startup_status()`
  broadcasts a short line at each real step — "Launching SDRConnect
  (GUI)…", "Connected to SDRConnect — checking devices…", "Both X and Y
  found — choose one", "Connected: RSPdx (Full IQ)" — rendered by a new
  persistent (not stacking-toast) strip at the top of the page
  (`#startup-status-strip` / `_showStartupStatus()`). Settles/fades 4s
  after the final "Connected:" line; warnings and in-progress steps stay
  up until replaced. This is the single biggest lever here — most of
  today's back-and-forth came down to "paste me the terminal log" because
  the UI itself said nothing.
- **Device-ambiguity vs. auto-stream race fixed.** `_deferred_iq_enable()`
  (the handler that confirms/enables streaming on whatever device
  SDRConnect reports active, ~1s after connect) now holds off, up to 15s,
  while a `device_choice_available` ambiguity is unresolved (new
  `_device_choice_pending` flag, set when the ambiguity is broadcast,
  cleared by `select_device`). Previously the popup could appear while
  audio was already flowing from the device the user didn't pick.
- **Combined connection + launch-mode picker.** The startup picker's two
  local options (nRSP-ST / USB-local) now advance to a second step —
  "Should NEXUS start SDRConnect for you?" (None/Headless/Full GUI + app
  path) — instead of finishing immediately; both `set_connection_mode`
  and `set_local_launch_mode` are sent together from one flow. Reachable
  both on first run and via the top-bar Connection control reopening it
  (always resets to step 1). The advanced wizard pane's separate controls
  are unchanged/still there — this is a faster combined path to the same
  settings, not a new source of truth.

### Confirmed (2026-07-31) — DAB decoding real audio again on 12B, end-to-end

Live test success after the full chain of fixes above: sample-rate
snap-back guard (`_sr_set_target`), `dabStart()` settle delay, and the
Result-108 device-release polling fix. With RSPdx properly selected (not
nRSP-ST — device selection was a live variable across these tests too) and
SDRConnect cleanly handed over to NEXUS, 12B locked and played real DAB
audio. No rollback to w034 was needed; every bug traced back to the single
2026-07-30 `dabStart() auto-sets 2 MSPS` change plus one unrelated,
independently-discovered device-handover timing bug, both now fixed in
place in w035.

### Fixed (2026-07-31) — "Open Failed / Result 108" recurred when the pre-existing SDRConnect had been actively streaming

Direct follow-up to the fix below. That fix (kill + fixed 2s wait) was
confirmed working once, but recurred on a later live test: this time the
user had manually started SDRConnect and left it actively tuned/streaming
for a while before starting NEXUS with `local_launch_mode='gui'`. An
actively-connected SDRplay session takes measurably longer to release its
USB/API handle on SIGTERM than a freshly-launched idle one (the case the
first fix happened to be tested against) — the fixed 2s window wasn't
always enough.

`_kill_existing_sdrconnect()` now polls (`pgrep`/`tasklist`) for the
process to genuinely exit, up to ~5s, escalating to SIGKILL on POSIX if
it's still alive with 2s left on the clock, then adds a 1.5s buffer for
the SDRplay driver layer itself to release the device — instead of
guessing one fixed delay that only covered the idle-process case.

### Fixed (2026-07-31) — Local GUI auto-launch could collide with an already-running SDRConnect ("Open Failed / Result 108")

Live user report + screenshot: right after switching `local_launch_mode`
to `gui`, SDRConnect showed "Open Failed / Result 108" (SDRplay API's
device-already-claimed error) instead of opening the RSPdx. Root cause:
`_local_launch_sdrconnect()` launched a brand-new SDRConnect instance
without first checking whether one was already running — which, per the
pre-existing "audio persists" issue in this same file, it very often is
(SDRconnect_headless runs independent of NEXUS/the browser and nothing
auto-quits it). Two SDRConnect processes both trying to open the same
physical USB device is exactly what error 108 means.

- Added `_kill_existing_sdrconnect()` — kills any running
  `SDRconnect_headless` AND full-GUI `SDRconnect` process by name, mirrors
  `_kill_sdrconnect_headless()`'s existing pattern exactly.
- `_local_launch_sdrconnect()` now calls it and waits ~2s for the RSPdx to
  release before launching the new instance, for the same reason
  `_ssh_stop_local_client()`'s `device_release_wait` exists — reopening
  too fast can hold a stale handle and crash SDRConnect outright, not just
  fail to open.

### Fixed (2026-07-31) — Device-choice popup's clicks were silently broken (HTML attribute escaping bug)

Live user report, immediately after the ambiguity-ask precedence fix below
made the popup actually appear for the first time: "the pop up appears but
nrsp-st starts before selection made. when i make my selectiion ...
nothing happens." Root cause found in `_showDeviceChoiceModal()` in
`DARKSKY_NEXUS_w035.html`: each button's `onclick` was built as a template
literal with `JSON.stringify(d.name)` spliced directly into a
DOUBLE-quoted HTML attribute. `JSON.stringify` always wraps its output in
double quotes too, so for any real device name (e.g. `'nRSP-ST
(240517b350) (IQ Lite)'`) the attribute closed right after `_pickDevice(`
and the rest became stray unparsed HTML — the button rendered fine but its
click handler was silently broken, for every device, every time. This bug
has existed since the modal was first built (2026-07-29) but was dormant:
nothing had ever made the ambiguity path reachable in a real session until
today's precedence fix.

- Rebuilt `_showDeviceChoiceModal()` using `createElement`/`textContent`/
  `addEventListener` instead of string-interpolated `onclick` attributes —
  no HTML/JS-escaping pitfalls possible with this approach, unlike the
  inline-onclick pattern used (safely, only ever with static string
  literals) elsewhere in this file.

Separately confirmed via the live log the user also has to look out for: a
different, pre-existing handler (`elif prop in ('active_device', ...)`)
reacts to whatever device SDRConnect reports as *already* active and
unconditionally confirms/enables its streaming ~1s later — this is
necessary for normal single-device operation and was NOT touched, but it
does mean that if SDRConnect auto-resumes streaming from its last device
before you answer the popup, your click may need to fight a device that's
already actively streaming. Per this file's own prior direct confirmation
(see the `iq_streaming`/`selected_device_name` comments above,
2026-07-2x), SDRConnect may not honour a live device/mode switch while
already streaming — untested whether that applies to switching between
two genuinely different physical devices (RSPdx vs nRSP-ST) rather than
just switching stream mode on the same device. Flagged for the user to
verify live now that the click itself actually works.

### Fixed (2026-07-31) — Remembered connection_mode was silently hiding the USB/nRSP-ST ambiguity ask

Live user report: "i just started nexus via idle, and it went straight to
mainscreen with nrsp-st running in iqlite, even though i also have my
rsp-dx connect to usb." Root cause: the 2026-07-29 startup connection-mode
picker persists a chosen mode (`nrsp_ws`/`usb_local_ws`) and reapplies it
silently on every future launch via `_apply_connection_mode()`, which
forces `device_preference` to `'nrsp'`/`'usb'`. That forced value was
checked BEFORE `_evaluate_device_selection()`'s "both a USB device and a
networked device are present — ask the user" branch, so once you'd ever
picked nRSP-ST, NEXUS would keep silently choosing it forever, never
re-offering USB even after plugging the RSPdx in. Asked what behaviour was
wanted: "i would like to choose what to connect to if both devices are
available."

- Reordered `_evaluate_device_selection()` in `w035_NEXUS.py`: the
  both-present ambiguity check (and the "already chose this session"
  short-circuit) now run BEFORE the forced `pref == 'usb'`/`'nrsp'`
  branches, for every device_preference value — not just `'auto'`. A
  forced preference still fully applies whenever only one device type is
  actually present (nothing to choose), it just no longer overrides a
  genuine both-present ambiguity.
- No frontend changes needed — reuses the existing `device_choice_available`
  modal / `select_device` command from the 2026-07-29 device-choice feature.

### Added (2026-07-31) — Startup option: headless or GUI SDRConnect (local + remote)

User request: "at nexus startup, could we add an option whether to have
headless or not?" Two independent, both opt-in, additions — every default
leaves prior behaviour completely unchanged:

- **Local auto-launch (new capability).** Previously, for the local
  connection modes (nRSP-ST WS / USB WS), NEXUS never launched SDRConnect
  itself — the user always had to already have it running. New
  `local_launch_mode` config (`none` default / `headless` / `gui`) plus
  `local_sdrconnect_path`: when not `none`, `sdr_bridge()` now calls
  `_local_launch_sdrconnect()` once at startup (before its connect loop),
  launching either `SDRconnect_headless --websocket_port=5454` from inside
  the configured `.app` bundle, or the full GUI app, via the existing
  `_ssh_launch_local_client()` launch logic (reused as-is). Best-effort —
  any failure just falls back to the pre-existing "wait for the user to
  start it" behaviour, exactly the old failure mode.
- **Remote Headless/GUI toggle.** The SSH launcher pane's `remote_command`/
  `local_client` fields (already headless-by-default since the 2026-07-29
  SSH wizard change) previously required two separate hand-edits to switch
  to the legacy `--server` + local-GUI-client combo. New
  `_apply_remote_launch_mode(mode, cfg)` rewrites both fields consistently
  from one `remote_launch_mode` choice (`headless` default / `gui`),
  preserving any custom remote install directory already in
  `remote_command`.
- New WS commands `set_local_launch_mode` / `set_remote_launch_mode`,
  deliberately added directly to the main command dispatcher rather than
  routed through `_handle_ssh_cmd`/`ssh_` prefix — see the removed Auto/
  Force USB/Force nRSP-ST button row's 2026-07-29 comment for why an
  unprefixed cmd name landing in that dispatcher is a real, previously-hit
  trap in this file (`_handle_ssh_cmd()` only ever fires for
  `cmd.startswith('ssh_')`).
- `_graceful_shutdown()` now also terminates a NEXUS-launched local GUI
  process directly via its `Popen` handle (the `gui` local-launch case);
  the `headless` case needed no new code — already covered unconditionally
  by the existing `_kill_sdrconnect_headless()` pkill-by-name.
- Frontend: new "Launch SDRConnect automatically at NEXUS startup"
  None/Headless/Full GUI control + app-path field in the Connection Setup
  wizard's nRSP-ST/Local pane, and a Headless/Full GUI toggle in the SSH
  pane above REMOTE CMD — both persisted immediately on click, both fields
  remain manually editable as before.

### Docs (2026-07-30) — Official User Manual/Troubleshooting/Quick Start updated for HD Radio (no source scripts available in this folder)

The three official docx/pdf docs (User Manual, Troubleshooting, Quick
Start) had never actually gained an HD Radio section despite earlier
tasks marking that work "done" — they were last rebuilt 2026-07-29
13:50-13:57, before today's HD Radio work existed. No
`build_usermanual.js`/`build_troubleshooting.js`/`build_quickstart.js`
source exists anywhere in `w035/` to regenerate from (checked; only
present in `OLD VERSIONS/w023` through `w032`), so this pass edited the
existing `.docx` files directly (unzip → edit `word/document.xml` →
rezip → XSD-validate), matching each doc's exact existing formatting
conventions rather than reconstructing a build pipeline. Also caught
Live Translation's own doc entry from earlier today's removal — turned
out none had ever been added to these three files either, so nothing
needed deleting there.

- **User Manual:** new "6.20 HD Radio (NRSC-5/iBOC)" section (mirrors
  6.19 DRM's structure exactly), plus a clause appended to the existing
  w035 version-highlights table row.
- **Troubleshooting:** new "HD Radio Issues (w035 only)" section (mirrors
  "DRM Issues"), covering the `dyld: Library not loaded` deploy-location
  bug found live today, the "what sample rate for HD Radio" Q&A, and a
  "shows no signal" note explaining the North America-only coverage
  constraint.
- **Quick Start:** new `nrsc5_nexus` row in the optional-external-tools
  table, and a new "Want to decode HD Radio..." callout (mirrors the DRM
  one) with the same North America caveat.

All three re-zipped and validated with `validate.py --original` (clean
diffs: +8/+9/+4 paragraphs respectively, no other structural changes),
rendered to PDF and visually confirmed via `pdftoppm` page renders before
being copied into `docs/word/w035/` and `docs/pdf/w035/`.

### Fixed + Confirmed (2026-07-30) — HD Radio's full NEXUS-side wiring proven end-to-end; silent relaunch-loop diagnostic gap closed

Follow-up to the two confirmations above. User is in Aberdeen (no HD
Radio coverage -- NRSC-5 is North America-only), so "wire nrsc5_nexus
into live NEXUS" was validated by replaying the same real off-air sample
through the actual production code path instead: new
`test_hd_pipeline.py` imports `w035_NEXUS.py` directly, sets
`state['hd_active']=True`, and drives `hd_engine()` + `_hd_feed_iq()`
with the real sample fed in small chunks, mirroring `sdr_bridge()`'s live
per-packet call pattern -- exercising the real resampler (gcd/ratio math
on the fractional native rate) and the JSON status parser, not just
`nrsc5_nexus.c` standalone.

First run failed silently: `hd_engine()` relaunched `nrsc5_nexus` every
~0.25s forever, `_hd_status` stayed `{}`, zero log explaining why. Root
cause: `nrsc5_nexus` had been copied to `/opt/homebrew/bin/` (Step 5, since
`/usr/local/bin` needed `sudo` on this Mac) without also copying
`libnrsc5.dylib` there -- `-rpath,@executable_path` resolves relative to
wherever the binary *currently* lives, so the exact same dyld issue Step 2
already fixed once (for `~/nrsc5/`) recurred at the new deploy location.
Confirmed via `/opt/homebrew/bin/nrsc5_nexus --help` reproducing the exact
`dyld: Library not loaded: @rpath/libnrsc5.dylib` error directly. Real fix:
`cp libnrsc5.dylib /opt/homebrew/bin/`.

The silence itself was a separate, real diagnostic gap worth closing on
its own: `hd_engine()` had no "process died unexpectedly" log (DAB/DRM
both already have this), and `_hd_stderr_thread_fn` logged non-JSON
stderr lines -- which is exactly where the real dyld error text was
sitting the whole time -- at `log.debug` (invisible by default). Both
fixed in `w035_NEXUS.py`, mirroring `drm_engine()`'s existing pattern
exactly: `hd_engine()` now logs `"HD Radio: nrsc5_nexus exited
unexpectedly (code N) -- relaunching"` before each relaunch attempt, and
the stderr line promoted to `log.warning`. `python3 -m py_compile` clean.

After the dylib fix, `test_hd_pipeline.py` re-run confirmed full success:
single clean launch (no relaunch spam), correct `1488375 Hz -> 744187.5 Hz
(FM, ratio 1/2)` resample log, and a fully populated final `_hd_status`
matching Step 4's direct-binary result (`locked:true`, station name/
slogan, ID3, program info) plus 2,000,000 bytes of real decoded PCM
buffered per program (HD1 and HD2). This proves the entire NEXUS-side HD
Radio pipeline -- launch, resample, feed, JSON parse, audio buffering --
against real broadcast data, with only genuine over-the-air reception
(needs a receiver actually inside HD Radio's North America coverage area)
left unverified. `NEXUS_nrsc5_build_macOS.md` updated: Step 5 now
requires the dylib copy at every deploy location, new Step 7 documents
the full pipeline test, Step 6's bundling section corrected to run
`otool -L` on `libnrsc5.dylib` (not just `nrsc5_nexus`, which only shows
`@rpath/libnrsc5.dylib` + the system lib) to find the real Homebrew
dependency chain, and two new Troubleshooting entries added.

### Confirmed (2026-07-30) — nrsc5_nexus (HD Radio) builds and passes its silence smoke test on real hardware

First real build attempt against `nrsc5_nexus.c` (Apple Silicon, Homebrew
toolchain). Compile step (`clang -c nrsc5_nexus.c -Iinclude`) needed zero
changes — clean against the real upstream `nrsc5.h`, matching this file's
own claim of having been written directly against the real header rather
than guessed. One real fix was needed at link time: `-Wl,-rpath,
@executable_path` only makes the loader search beside the executable, but
CMake leaves `libnrsc5.dylib` in `build/src/` — running the linked binary
failed with `dyld: Library not loaded: @rpath/libnrsc5.dylib` until
`cp build/src/libnrsc5.dylib .` copied it next to `nrsc5_nexus`. After
that, `otool -L` shows only `@rpath/libnrsc5.dylib` (resolved) and the
system `libSystem.B.dylib` -- no direct fftw3/ao/rtlsdr deps on the
wrapper itself (pulled in transitively via `libnrsc5.dylib`). Silence
smoke test (piped `/dev/zero`) then passed clean: `hd_status
running:true` on start, `running:false` on EOF-triggered exit, 0-byte
stdout, no crash. `NEXUS_nrsc5_build_macOS.md` updated with the confirmed
link recipe, Step 3 result, and a new Troubleshooting entry for the exact
dyld error. Step 4 (real off-air signal decode test) still pending.

### Confirmed (2026-07-30) — nrsc5_nexus decodes real off-air HD Radio IQ end-to-end

Follow-up to the build/link/silence-test confirmation above. The original
Step 4 test plan assumed a same-rate cu8→cs16 format conversion for the
bundled `support/sample.xz` -- wrong: reading nrsc5's own `src/input.c`
showed `input_push_cu8()` always applies an internal ÷2 halfband
decimation before decoding (FM), while `input_push_cs16()` (what
`nrsc5_nexus.c` uses) has no decimation stage and expects samples already
at the native rate. A same-rate conversion would have silently fed double
the intended sample rate and likely produced zero lock -- easy to
misdiagnose as a real bug in the wrapper. New `convert_nrsc5_sample.py`
(in `w035/`) does the real conversion: cu8 → nrsc5's own `U8_Q15`
amplitude scaling → anti-aliased ÷2 decimation to the native FM rate →
cs16, mirroring the real `_hd_feed_iq()` production path rather than
nrsc5's exact internal FIR taps. Piped into `nrsc5_nexus`, it locked
immediately and decoded real broadcast data out of the bundled sample:
station name/ID (`KUT `, University of Texas at Austin, matching its
real-world slogan text pulled from the same broadcast), station location,
audio service info, and real ID3 metadata ("You're Listening to Q with
Jian Ghomeshi"). One brief lock/re-lock blip mid-stream (MER dipped to
-14.16 dB, BER spiked to 0.197 for one cycle) before settling back to
clean decodes -- a real acquisition event, not a bug. `/tmp/hd_stdout.bin`
came out at 4,035,384 bytes of real `HDR1`-framed PCM, confirming the
audio path end-to-end too. `NEXUS_nrsc5_build_macOS.md` Step 4 updated
with the corrected recipe and full confirmed output; overall doc status
line updated to "fully confirmed working end-to-end." Next real step:
wire `nrsc5_nexus` into a live NEXUS session against actual over-the-air
HD Radio.

### Removed (2026-07-30) — Live Translation feature

Explicit user request: "remove the translate feature that was implemented
earlier." Fully reverted the faster-whisper + LibreTranslate/deep-translator
Live Translation feature added earlier in the w035 cycle (2026-07-29):

- Backend (`w035_NEXUS.py`): removed the optional `faster_whisper`/
  `deep_translator` imports and `_HAVE_FASTER_WHISPER`/
  `_HAVE_DEEP_TRANSLATOR` flags, the `sdr_bridge()` audio-feed hook, the
  retune-clear block, the `translate_start`/`translate_stop` WS command
  handlers, and the entire 218-line "LIVE TRANSLATION" engine section
  (in-process background threads, 6-second rolling audio chunks,
  generation-counter guard). Verified with `python3 -m py_compile` after
  every removal step.
- Frontend (`DARKSKY_NEXUS_w035.html`): removed the `.has-translate`/
  `.si-col-translate` CSS block, the 6th "Col 6" translate column div
  inside `#hf-si-grid` (grid reverts to its base 5-column layout), the
  `translate_status`/`translate_line` message-dispatcher cases, and the
  100-line JS function block (`hfTranslateToggle()`, `hfTranslateStart()`,
  `hfTranslateStop()`, `_translateSetGridVisible()`, `_translateOnScroll()`,
  `translateUpdateStatus()`, `translateAddLine()`, plus the
  `_translateRunning`/`_translateUserScrolledUp` state vars). Verified with
  a full `<script>`-block JS syntax check and an HTML div-balance check
  (the file is structurally sound; a raw regex div-count off-by-one traced
  to `<div`/`</div>` text inside an HTML comment, not a real markup bug).
- Build (`build/DARKSKY_NEXUS_macOS.spec`, `build/DARKSKY_NEXUS_Windows.spec`):
  removed the `faster_whisper`/`deep_translator` `hiddenimports` entries
  and their ctranslate2 bundling-caveat comments.
- Known gap: the w035 User Manual docx/pdf (built outside this session,
  no `build_usermanual.js` source present in this folder) still documents
  the removed feature. Not rebuilt here since no doc-build source was
  available in `w035/` -- flagging for a future doc pass if noticed.

### Fixed (2026-07-30) — DRM stuck at 125 kSPS Full-IQ, zero decode despite a strong, correctly-shaped signal

Live user report + screenshot ("no drm decode ..... strong signal"):
the DRM tab's ENGINE panel showed SAMPLE RATE 125 kSPS, and the
waterfall clearly showed a strong, correctly-shaped ~20kHz-wide DRM
signal sitting right on 13.730 MHz -- ruling out "nothing on air".
`dream_nexus` had run cleanly and continuously for 7+ minutes with zero
crashes (confirming the drm_set_frequency no-op-relaunch fix from
earlier today held), yet SNR/MER stayed flatlined at exactly 0.0 the
entire time -- "No station decoded yet" never budged. That combination
(strong real RF + a healthy running decoder + a status that never once
wobbled off exactly zero) points at the receive chain never getting
real samples worth processing, not weak propagation.

125 kSPS is well below the 2 MSPS Full-IQ rate already confirmed live-
working for DAB on this exact hardware (see the entry below) -- neither
`drmStart()` nor `drmSetFrequency()` had ever touched sample rate at
all, so DRM was silently inheriting whatever was last dialed in from an
unrelated earlier session/test. Fix: both now call the same
`setSampleRate(2000000)` guard `dabStart()` uses (skipped in IQ Lite
mode, skipped if already at 2 MSPS).

### Added (2026-07-30) — dabStart() auto-sets 2 MSPS

Live user request: "when we start dab decoder can you auto set
samplerate to 2msps?" `dabStart()` now calls the existing `setSampleRate()`
helper with 2,000,000 Hz before sending `dab_start`, so the user doesn't
have to remember to dial it in manually first -- 2 MSPS is the exact rate
this was live-tested and confirmed working against (NEXUS resamples that
up to `dab_radio_nexus`'s required 2.048 MSPS internally, see
`_dab_feed_iq()`). Skipped in IQ Lite mode (fixed 192 kSPS hardware rate;
`setSampleRate()` only adjusts the display zoom span there, and IQ Lite
doesn't deliver raw IQ for DAB anyway) and skipped entirely if the rate is
already 2 MSPS, so no redundant toast/network chatter on repeat starts.

### Fixed (2026-07-30) — dream_nexus survives NEXUS shutting down (requires rebuild)

Live user report: "dream_nexus is still running (activity monitor) even
when nexus is shut down." `_drm_proc` was already in
`_graceful_shutdown()`'s termination list (2026-07-29 fix), so this isn't
that gap recurring -- the actual cause is upstream of Python entirely.
The user runs `w035_NEXUS.py` from IDLE (confirmed by the "= RESTART:
..." banner in their pasted console output), and IDLE's "Restart Shell"
tears down the running interpreter directly rather than going through
Python's normal signal-handling path -- `_graceful_shutdown()` never
runs, so `proc.terminate()` is never called on `_drm_proc` at all. No
signal ever reaches `dream_nexus`, and nothing in `dream_nexus.cpp`
itself would reliably exit on a closed stdin pipe either (`Read()`
correctly returns "error" on EOF, but whether that unwinds
`DRMReceiver.process()` and stops the main loop depends on Dream's own
internal handling, not something this file controls) -- so it can run on
indefinitely as a true orphan, reachable only from Activity Monitor.

Fix: added a parent-death watchdog directly in `dream_nexus.cpp` --
captures its real parent PID via `getppid()` once at startup, polls for
a change every second on a background thread, and self-terminates
(`std::_Exit(0)`) the moment it detects it's been orphaned (reparented to
launchd/PID 1). This is independent of signals entirely, so it catches
every ungraceful-parent-death case (IDLE kill, a crash, Activity Monitor
force-quitting the Python process, anything), not just this one. POSIX-
only for now (`#ifdef`'d out on Windows, which has no `getppid()`
equivalent) -- `dream_nexus.exe` still relies on the normal
`terminate()` call there until a Windows-specific watchdog is written.

**Requires a rebuild** -- this is a source change to `dream_nexus.cpp`,
not something that takes effect until it's recompiled per
`NEXUS_dream_drm_build_macOS.md`'s Step 2. `dab_radio_nexus.cpp` and
`nrsc5_nexus.c` likely share this identical latent gap (same
piped-subprocess architecture) -- not yet mirrored there since their
main-loop shape wasn't checked in the same pass; worth the same fix as a
follow-up.

### Fixed (2026-07-30) — drm_set_frequency force-relaunched dream_nexus even on a no-op duplicate frequency

Direct follow-up to the diagnostics fix just below — with the new logging
in place, a second live test against the same real Radio Romania
International DRM broadcast (9570 kHz) caught the actual bug on the first
retry: `dream_nexus` launched cleanly at 19:12:42, then 7 seconds later
(19:12:49) the log showed `DRM: dream_nexus exited unexpectedly (code
-15) -- relaunching` — code -15 is SIGTERM, i.e. NEXUS itself killed it,
not a real crash. Cause: a second `drm_set_frequency` call arrived for
the exact same 9.570000 MHz already active (visible as a duplicate
"SDRConnect tune → 9.570000 MHz" line), and the handler force-relaunched
unconditionally on every call, with no check for whether the frequency
had actually changed. That wipes out an in-progress DRM sync attempt for
no reason — DRM sync routinely takes longer than 7 seconds, especially
with `rxmode=0` (auto-detect) scanning across robustness modes A-D.

Fix: `drm_set_frequency` is now a no-op if `dream_nexus` is already
running against the exact frequency being requested. DAB (`dab_set_channel`)
and HD Radio (`hd_set_frequency`) share the identical unconditional-
relaunch design and could show the same symptom under a duplicate/
redundant call — not fixed here since neither has a live report of it
happening, but worth the same guard if one shows up.

Also worth noting from the same log: `dream_nexus`'s startup stderr
listed "No usable FAAD2 aac decoder library found" / "No usable FAAC aac
encoder library found" / "No usable Opus library found" alongside "Adding
FDK codec" — read together, this looks like normal codec-probe logging
(FAAD2/FAAC/Opus are alternate libraries it checked for and didn't need)
rather than a failure, since FDK-AAC — the codec the build guide already
has the user install via `brew install fdk-aac`, and what DRM broadcasts
actually use — was found and added successfully. Not treated as a bug
fix; flagged here in case decode still fails after the relaunch fix and
this needs a second look.

### Fixed (2026-07-30) — DRM engine gave no log evidence either way on "no drm decode" report

Live test against a real, scheduled DRM broadcast (Radio Romania
International, 9570 kHz, German, 1800-1900 UTC, Tiganesti 90kW — confirmed
against drmrx.org's current A26-season schedule, so this wasn't a "nothing
on air" case). Log showed `dream_nexus` launched twice ~4.3s apart
(19:04:18 → 19:04:23) with nothing in between explaining why, and no
confirmation either way of whether the second instance ever locked.

Root cause of the *missing evidence* (not yet a confirmed root cause of
the decode failure itself): `_drm_stderr_thread_fn()` only ever
`log.debug`'d non-JSON stderr lines — exactly where a `dream_nexus`
crash/assert/usage message would land — and never logged lock
acquired/lost transitions at all (only broadcast to the browser). Default
log level is INFO, so both were invisible in the log file. Separately,
`drm_engine()`'s poll loop silently relaunched on any crash with no log
line distinguishing "fresh start" from "just crashed."

Fix (diagnostics only, not a decode fix): promoted non-JSON stderr lines
to `log.warning`, added `log.info` on lock acquired/lost transitions
(mode/station/SNR/MER), and added a `log.warning` when `drm_engine()`
detects `dream_nexus` died after a successful launch. Next time this
happens, the log file alone will show whether it crashed (and the real
error text) or ran clean but never locked.

### Fixed (2026-07-30) — SDRconnect_headless kept running (and playing audio) after closing the browser

Live user report + Activity Monitor screenshot: after diagnosing the
2026-07-29 "audio persists" fix as unrelated to this case (user confirmed
always on SDRConnect/nRSP-ST, never RTL-SDR direct mode), the actual
process still shown running post-close was `SDRconnect_headless` itself —
13.5% CPU, 1:41 CPU time, still alive after the Chrome tab was closed.

Root cause: `SDRconnect_headless` is not one of NEXUS's own
`subprocess.Popen` children (unlike `_dab_proc`/`_hd_proc`/`_drm_proc`/etc,
which the 2026-07-29 fix already added to `_graceful_shutdown()`'s
termination list). The common case is the user starts it independently
(or it's already running); NEXUS only ever *talks to* it over its own
WebSocket API on port 5454/50000. So even a full, correct NEXUS shutdown
never touched it — it kept running, with whatever local audio monitor it
has, indefinitely.

Fix: added `_kill_sdrconnect_headless()`, called first thing in
`_graceful_shutdown()` — `pkill -TERM -x SDRconnect_headless` on
macOS/Linux, `taskkill /IM SDRconnect_headless.exe /F` on Windows.
Best-effort and silent (a no-match just means it wasn't running, the
normal case for RTL-SDR-only sessions). This rides the *existing*
"browser closed" shutdown trigger (`_watch_clients_loop()` — last WS
client disconnects, 5s grace period to survive a page reload, then
`_request_shutdown()`), so no new detection logic was needed — per
explicit user request, this now happens automatically and immediately
every time the browser is closed, no opt-in toggle.

### Fixed (2026-07-30) — Translate column visible before being toggled on (live user report)

Live screenshots: the `🌐 TRANSLATE` column appeared on page load, stacked
in a narrow strip directly under the BROADCAST MATCHES column, before the
toggle was ever pressed — instead of staying hidden until turned on.

Root cause: a CSS cascade ordering bug, not a JS one. `.si-col-translate {
display:none; }` was declared *before* the general `.si-col { display:flex;
... }` rule in the stylesheet — both single-class selectors, equal
specificity, so the later `.si-col` rule won the cascade and overrode the
hide regardless of the element also matching `.si-col-translate`. With the
column rendered but `#hf-si-grid` still at its default `repeat(5,1fr)`
(no `.has-translate` class yet, since that's only added once the toggle
actually fires), CSS grid auto-placement wrapped the 6th DOM child into a
new implicit row using column 1's own track width — exactly the "stacked
under column 1" look in the screenshot. Confirmed correct once toggled on
(second screenshot) purely because `#hf-si-grid.has-translate
.si-col-translate { display:flex; }`'s higher specificity (ID + 2 classes)
was never in question — only the *default-hidden* state was broken.

Fix: raised the hide rule's specificity so it can't lose to `.si-col`
regardless of source order — `.si-col-translate { display:none; }` →
`.si-col.si-col-translate { display:none; }` (two-class selector).

### Added (2026-07-30) — Wire HD Radio + translation into the packaged builds

Live user question: "when i build for macos or windows are translate and
hd-radio bundled?" — answer at the time was no, neither had been wired
into the PyInstaller spec files or build scripts, same gap DAB's own
bundling closed on 2026-07-26 (see that section below) but hadn't yet been
repeated for these two newer features. Closed now, "like we did for DAB":

- `DARKSKY_NEXUS_macOS.spec` / `DARKSKY_NEXUS_Windows.spec`: added an
  `nrsc5_nexus`/`nrsc5_nexus.exe` optional-bundled-binary check, byte-for-
  byte the same pattern as `dab_radio_nexus`'s own existing block — checks
  `build/bundled/nrsc5_nexus[.exe]`, bundles it if present, falls back to
  `_hd_find_binary()`'s normal PATH/Homebrew search at runtime if not.
  Also added `faster_whisper`/`deep_translator` to both specs'
  `hiddenimports` lists, with an explicit caveat comment: ctranslate2
  (faster-whisper's backend) has a real history of needing
  `--collect-all ctranslate2` beyond plain hiddenimports once frozen —
  not build-tested here, flagged rather than silently assumed to work.
- `build_macOS.sh` / `build_Windows.bat`: added a "Checking for bundled HD
  Radio engine..." step (3c) immediately after the existing DAB check
  (3b), identical informational-only pattern — the .spec file itself
  decides whether to actually bundle it.
- `NEXUS_nrsc5_build_macOS.md`: new "Step 6 — Bundling for distribution"
  section, adapted from `dab_radio_nexus`'s own proven `otool -L` /
  `install_name_tool` / `codesign` recipe (in `NEXUS_dab_radio_build_macOS.md`)
  since the exact Homebrew dylibs `nrsc5_nexus` links against aren't
  confirmed yet (no real build performed) — framed as "adapt to your own
  `otool -L` output," not copy-pasted specifics.
- New `NEXUS_nrsc5_build_windows.md` — nrsc5's own upstream README
  documents MSYS2 or mingw-w64 cross-compilation for Windows, *not* an
  MSVC/vcpkg path the way DAB-Radio's own Windows build does — this
  follows nrsc5's actual documented route rather than assuming DAB-Radio's
  toolchain would also work for a different upstream project. Flags the
  MinGW-runtime-DLL bundling question (static link vs. bundle DLLs
  individually) as genuinely open, pending a real build to check with
  `dumpbin`/`Dependencies`.

Translation has no equivalent native-binary bundling step — it's pure
Python packages (`faster-whisper`/`deep-translator`), not a subprocess
tool like DAB/DRM/HD Radio — so `pip install` into the build environment
before running PyInstaller is the only additional step needed for those
to end up in the frozen app, once the ctranslate2-collection caveat above
is confirmed one way or the other.

**Status: spec/script changes are syntax-verified (`ast.parse` on both
.spec files, `bash -n` on build_macOS.sh) but not build-tested** — same
honest caveat as the underlying HD Radio/translation features themselves.
Nobody has actually run PyInstaller with a real `nrsc5_nexus` binary or a
real `faster-whisper` install present yet to confirm the bundling
actually works end-to-end.

### Added (2026-07-30) — Live translation (faster-whisper + LibreTranslate/deep-translator)

New feature: translates whatever's currently tuned and shows the result as
text — no speech synthesis, matching the original ask exactly ("this do
not need to be spoken, but rather translate the selected audio and then
show the translated text"). Design went through two rounds of user
feedback before implementation: first request specified a popup that
stops translating entirely when closed; follow-up question asked whether
the HF Utility tab (like DAB's DLS/FM RDS RadioText scroll) had room
instead. Investigated both existing scroll widgets
(`.dab-np-dls-track`'s marquee vs `.si-col-body`'s append-log) and
recommended append-log — a marquee loses text the instant it scrolls past,
which defeats the point for a conversation transcript rather than a
"now playing" fact that gets re-sent every few seconds. Confirmed via
AskUserQuestion (append-log, `base` Whisper model, LibreTranslate
self-hosted default, curated language shortlist — all four "Recommended").
Full design: `NEXUS_live_translation_integration_plan.md`.

- **No subprocess of its own** — unlike DAB/DRM/HD Radio's bundled-tool
  model, STT/MT run in-process via a background daemon thread per audio
  chunk (`faster-whisper`'s `model.transcribe()` is CPU-bound/blocking and
  would stall the event loop — spectrum/waterfall updates for every
  connected client — if called directly from the audio-feed coroutine).
  Nothing new needed in `_graceful_shutdown()`'s termination list as a
  result — the threads are short-lived and already `daemon=True`.
- **Audio tap**: the same `mono` 48kHz array `sdr_bridge()`'s `t == 1`
  branch already feeds to every other audio-domain decoder
  (`cw_dec`/`rtty_dec`/`fax_dec`/etc.) — one more `.active`-gated call
  alongside them (`state['translate_active']`, not a bare module global —
  matches `dab_active`/`drm_active`/`hd_active`'s own convention rather
  than needing separate `global` statements in the WS dispatcher).
- **STT**: `faster-whisper`, `base` model, lazy-loaded on first use and
  kept warm (not reloaded on every start/stop toggle — model load takes a
  couple of seconds). Rolling 6-second non-overlapping chunks, each
  transcribed then translated in its own background thread; a
  generation-counter guard (mirrors `_dab_generation`'s straggler-frame
  pattern, applied here to a thread instead of a subprocess) discards a
  chunk's result if it's gone stale by the time inference finishes — with
  one deliberate asymmetry from every other engine's generation counter in
  this file: `translate_stop` does **not** bump the generation (the plan
  explicitly asks for the last already-dispatched chunk's result to still
  be delivered — "better UX than truncating mid-sentence" — only a
  **retune** or a fresh **start** discards in-flight work).
- **MT**: `_translate_text()` tries a self-hosted LibreTranslate instance
  first (`NEXUS_LIBRETRANSLATE_URL` env var, defaults to
  `http://127.0.0.1:5000` — assumed already running by the user, NEXUS
  doesn't launch/manage it as its own subprocess), falls back to
  `deep-translator`'s Google backend automatically if unreachable, and as
  a last resort returns the original transcribed text unchanged
  (labelled `'none'`) rather than silently dropping the line — a
  translation-backend outage shouldn't mean losing the transcript too.
  Uses `urllib.request` (already imported) for the LibreTranslate POST —
  no new hard dependency just for that.
- **Lifecycle**: `translate_start`/`translate_stop` WS commands. Retuning
  the VFO while active clears the transcript panel and restarts the
  rolling buffer (a new frequency is a different signal — carrying over
  stale text would be actively misleading) — wired into the existing
  `'tune'` WS handler, which now also broadcasts `{cleared:true}` so the
  frontend can clear its own displayed log in step with the backend's
  buffer reset.
- **Frontend**: new 6th column (`🌐 TRANSLATE`) in the HF Utility tab's
  `#hf-si-grid`, hidden by default (`grid-template-columns` only expands
  from `repeat(5,1fr)` to `repeat(6,1fr)` once toggled on — users who
  never touch the feature don't lose any width to it, same reasoning as
  `#device-select-strip`'s own conditional visibility elsewhere). Header
  carries a curated 9-language `<select>` and an ON/OFF toggle, mirroring
  the ↻ refresh buttons already in the other four column headers. Body is
  a genuine append-log — each entry shows the translated line, the
  original transcribed text as smaller subtext underneath (useful for
  checking the translation against what was actually said, especially on
  a noisy signal where STT itself may have mis-heard), and which backend
  produced it. Auto-scrolls to the newest line unless the user has
  manually scrolled up (tracked via a scroll-position check, not a
  library) — same "don't yank the view out from under someone reading"
  consideration the DAB DLS/tech-panel scroll areas already handle.
- **Dependencies** (optional, graceful degradation matching the existing
  `_HAVE_SCIPY`/`_HAVE_SOUNDDEVICE` pattern): `pip install faster-whisper`
  (required for STT — `translate_start` returns an error status if
  missing, rather than silently doing nothing) and `pip install
  deep-translator` (optional fallback path only).

**Status: implemented, not yet live-tested against a real tuned signal**
(no network access in this sandbox to install `faster-whisper`/
`ctranslate2`, and no live SDRConnect connection available here either).
Code paths were verified by direct reading against `faster-whisper`'s and
`deep-translator`'s real documented APIs, and `python3 -m py_compile` /
`node --check` both pass clean, but "compiles" isn't the same claim as
"decodes real speech and translates it correctly" — that verification is
still open follow-up work, same honest caveat as HD Radio above.

### Added (2026-07-30) — HD Radio / NRSC-5 decoder (nrsc5_nexus, piped IQ)

New decoder, architecturally the closest sibling to the DAB engine (not
DRM's): like a DAB ensemble, HD Radio decodes every discovered program
(HD1-HD8) simultaneously from one IQ feed, so this reuses DAB's
per-subchannel-buffer/program-card-grid shape rather than DRM's
single-stream one. Built from `NEXUS_nrsc5_hdradio_integration_plan.md`
(w034), refreshed against the real upstream `nrsc5.h`
(theori-io/nrsc5, fetched 2026-07-30) rather than trusting that plan's
approximate sketch — several details differed from the plan once checked
against the real header:
- The native IQ rate constants are `NRSC5_SAMPLE_RATE_CS16_FM` (744187.5 Hz)
  and `NRSC5_SAMPLE_RATE_CS16_AM` (46511.71875 Hz), not the guessed
  `_NATIVE_FM`/`_NATIVE_AM` names — and both are fractional, unlike DAB's
  clean 2.048 MSPS or DRM's clean 48000 Hz, so the IQ resampler needed a
  different ratio-computation approach (see below).
- Audio output is always the fixed `NRSC5_SAMPLE_RATE_AUDIO` (44100 Hz) —
  there's no per-event sample rate to read, simpler than DAB's
  per-subchannel `BasicAudioParams` or DRM's xHE-AAC/SBR rate drift.
- MER, BER, and lock/sync are three separate event types
  (`NRSC5_EVENT_MER` with `lower`/`upper` floats, `NRSC5_EVENT_BER` with
  `cber`, `NRSC5_EVENT_SYNC`/`NRSC5_EVENT_LOST_SYNC`), not one combined
  status event.
- Confirmed nrsc5's own README: `NRSC5_SAMPLE_RATE_CS16_FM` /
  `NRSC5_SAMPLE_RATE_CS16_AM` exactly match the stock CLI's documented
  `--iq-input-format cs16` rates (744188/46512 SPS, FM/AM) — good
  independent confirmation the header wasn't misread.

**New file `nrsc5_nexus.c`** (~400 lines) — headless wrapper, same overall
shape as `dab_radio_nexus.cpp`/`dream_nexus.cpp`: `nrsc5_open_pipe()` +
`nrsc5_set_mode(FM|AM)` + `nrsc5_set_callback()` + `nrsc5_start()`, then a
blocking `fread()`/`nrsc5_pipe_samples_cs16()` loop. stdout emits one frame
type, `"HDR1"` (4-byte magic + 1-byte program 0-7 + 1-byte is_stereo +
4-byte payload_len + PCM). stderr emits one JSON line per event —
`hd_status`/`hd_id3`/`hd_station_name`/`hd_station_slogan`/
`hd_station_message`/`hd_station_id`/`hd_station_location`/
`hd_audio_service`/`hd_sync`/`hd_emergency_alert`/`hd_lot` (station
logo/album art, base64-embedded if under 200KB). Includes its own JSON
string escaper (untrusted broadcast text) and a minimal base64 encoder for
LOT images — no third-party dependency pulled in just for those two things.

**Python backend** (`w035_NEXUS.py`) — `hd_engine()` mirrors
`dab_engine()`'s subprocess-lifecycle shape (0.25s poll, launch-on-active/
terminate-on-inactive, generation-counter dedup against straggler frames
from a just-killed subprocess). `_hd_feed_iq()`'s resampler handles the
fractional native rate by noting FM's rate is exactly 16× AM's rate
(`744187.5 / 46511.71875 == 16.0` exactly — both derived from the same
nrsc5 master clock) — so `FM×2` and `AM×32` both land on the same integer,
`1488375` (which is also `NRSC5_SAMPLE_RATE_CU8`, not a coincidence),
giving one canonical integer `math.gcd()` target instead of two separate
fractional-rate code paths. `_hd_store_audio()`/`_serve_hd_audio()` mirror
DAB's per-program buffer dict + WAV-header-per-connection HTTP streaming
exactly (`/hd_audio`, `hd_play_program` selects which HD1-HD8 buffer
drains — pure Python-side selection, no relaunch). New WS commands:
`hd_start`/`hd_stop`/`hd_set_frequency`/`hd_play_program`/
`hd_stop_program`. Full-IQ dispatcher hook added alongside the existing
independent `dab_active`/`drm_active` checks (not an elif-chain — the
integration plan's own sketch assumed one existed; the real code doesn't).
`_hd_proc` added to `_graceful_shutdown()`'s termination list (the exact
same orphaned-subprocess bug class fixed for `_dab_proc`/`_drm_proc`
2026-07-29 — closed here from the start rather than found later).

**Frontend** — new `#tab-hdradio` panel: frequency input (Tune), a
read-only MODE readout that follows the VFO's own AM/FM demod (not
user-selectable — HD Radio's native rate depends on it, so a mismatched
manual override would just decode nothing), a program card grid (reusing
DRM's `.drm-qt-grid`/`.drm-qt-card` CSS — visually identical pattern to a
quick-tune grid, repurposed for program selection instead), and a station-
status/now-playing column reusing DAB's `.dab-lock-dot`/
`.dab-np-hero-avatar`/`.dab-signal-bars`/`.dab-np-dls-wrap` classes (station
logo swaps in over the initials avatar once an `hd_lot` arrives; ID3
title/artist shown under the station name). Region gate: **inverted** from
DAB's — HD Radio is shown as unsupported everywhere *except* `_bpRegion ===
'ITU-2'` (the Americas), the exact opposite condition from
`_dabRegionUnsupportedHTML()`'s own gate, reusing the same `_bpRegion`
geo-detection with no new location code. Added to `DECODERS_DB.external`,
`decoderTabs`, and the message dispatcher (`hd_status`/`hd_sync`/`hd_id3`/
`hd_station_name`/`hd_station_slogan`/`hd_station_message`/
`hd_audio_service`/`hd_lot`/`hd_emergency_alert`).

**Status: implemented but not yet build-tested against real nrsc5 source
or live hardware** — unlike the DRM integration (which went through eleven
+ seven + one real fixes once actually compiled against Dream's source
tree), `nrsc5_nexus.c` has only been written against the fetched header,
not yet compiled. nrsc5's own upstream README confirms the real dependency
list (`cmake autoconf libtool libao-dev libfftw3-dev librtlsdr-dev` on
Linux; a Homebrew `--HEAD` formula on macOS) and that the stock CLI's
`--iq-input-format cs16` rates match the header's constants exactly — good
signs, but real compilation and a real-signal test (same two-stage
validation DRM went through: stock CLI first, then the custom wrapper) are
still open follow-up work. See `NEXUS_nrsc5_build_macOS.md` (new).

### Added (2026-07-29) — Startup connection picker: a real gate, not a reactive prompt

Live user reports, in sequence: "when starting nexus, the nrsp-st always
connects first and am unable to switch to the usb device" → shipped the
device-choice modal (below) → "w035 still starts first before i make a
selection" → confirmed via live Claude-in-Chrome inspection that the modal
appeared but SDRConnect/nRSP-ST was already live behind it → root-caused to
`_auto_select_device()`'s one-shot 5s poll (fixed above) → even after that
fix, user pushed back with the real architectural ask: "i think we need to
add another screen at startup which basically states how do you wish to
connect? 1. NSRP-ST (WS), 2. SDRPlay Device (USB), 3. SDRPlay Device (WS),
4. RTL-SDR". Investigation confirmed this was the right call: `main()`
calls `asyncio.create_task(sdr_bridge())` *and*
`asyncio.create_task(rtl_bridge())` unconditionally, both fully decoupled
from any frontend state — so no amount of reactive modal logic could ever
truly "wait", because the connection was never actually gated on anything.

- New `connection_mode` config field (persisted alongside the existing SSH
  config): `'nrsp_ws'` / `'usb_local_ws'` / `'usb_remote_ws'` / `'rtlsdr'`.
- New `_connection_mode_ready` asyncio.Event — a real block. Both
  `sdr_bridge()` and `rtl_bridge()` now `await` it before attempting *any*
  connection, and stand down entirely (not just skip a step) if the
  resolved mode isn't theirs to handle. Resolved either from a previous
  session's persisted choice (checked in `main()`, gate opens immediately,
  no picker shown) or from the new `set_connection_mode` WS command on
  first run.
- New `_apply_connection_mode()` helper translates the chosen mode into the
  pre-existing `device_preference` ('nrsp'/'usb') and `state['engine']`
  ('SDRCONNECT'/'RTLSDR') knobs, so `_evaluate_device_selection()` and
  `rtl_bridge()`'s existing per-iteration engine check didn't need any
  mode-aware branches of their own.
- Frontend: new `#connection-picker-modal` — four large option cards
  (nRSP-ST WS / SDRplay USB local / SDRplay USB remote / RTL-SDR), shown
  full-screen and blocking only when `state.connection_mode` arrives empty
  (no remembered choice). Picking "SDRplay Device (WS)" (remote USB) opens
  the existing SSH/Connection-Setup wizard's SSH pane, since that's the
  existing remote-launch machinery — no new remote-connection code needed,
  just routing.
- The old `#conn-wizard` (SSH/Connection Setup) no longer shows
  unconditionally on every launch — that's now this picker's job. The
  wizard is still reachable on demand (automatically for the remote-USB
  choice, or manually via the new top-bar "Choose connection" control's
  "Advanced connection settings" link) for editing SSH host details,
  default device, timing, etc.
- New always-visible "Choose connection ▾" control in the top bar shows
  the current mode and reopens the picker to change it. Per explicit
  decision: changing it saves the new choice and shows a "restart NEXUS to
  apply" toast rather than live-switching bridges — deliberately simpler
  and lower-risk than tearing down an in-flight SDRConnect/rtl_tcp
  connection (including any auto-launched rtl_tcp subprocess) while NEXUS
  is running.
- Removed the now-redundant "DEVICE PREFERENCE" Auto/Force USB/Force
  nRSP-ST button row from the wizard's nRSP-ST/Local pane — connection_mode
  already sets the equivalent `device_preference` value under the hood, so
  a second control for the same setting would just be a way for the two to
  desync. While removing it, found this row was also silently dead code:
  its `set_device_pref` command doesn't start with `'ssh_'`, so it never
  reached `_handle_ssh_cmd()` — the buttons visually toggled but never
  actually persisted anything server-side. Not fixed (moot now), just
  noted here for the record.

### Fixed (2026-07-29) — Device choice never re-checked after the initial 5s connect-time poll

Follow-up to the wizard-copy fix below: user confirmed via macOS System
Information (USB pane, vendor 0x1df7 = SDRplay) and SDRConnect's own device
dropdown that the RSPdx genuinely was detected, both at the OS level and by
SDRConnect itself — so the earlier "SDRConnect just hasn't seen it" theory
wasn't the whole story. Re-reading `_auto_select_device()` found the actual
bug: it ran exactly once, via `asyncio.create_task()` right after connecting,
polled `state['valid_devices']` for up to 5 seconds, made its one decision,
and then never looked again for the rest of that SDRConnect connection. If
SDRConnect took longer than 5s to finish enumerating a USB RSP — plausible
right after a fresh plug-in, or if NEXUS simply connects before SDRConnect
has caught up — the one-shot check saw only the nRSP-ST entries, logged "No
USB RSP... leaving selection unchanged," and gave up permanently. The later
`valid_devices` update (once SDRConnect did see the RSPdx) was received and
stored in `state`, but nothing ever re-evaluated it.

- Split the decision logic out of `_auto_select_device()` into a new
  `_evaluate_device_selection(trigger)` that reads `state['valid_devices']`
  as-is (no polling) and can be called repeatedly, not just once.
- `_auto_select_device()` is now just the initial "wait up to 5s, then
  evaluate" call — same starting behaviour as before.
- The `valid_devices` property-changed handler (where `state['valid_devices']`
  gets updated from live SDRConnect messages) now also calls
  `_evaluate_device_selection('valid_devices updated')` whenever the string
  actually changes, so a USB device that shows up late — or gets plugged in
  after NEXUS is already running — still triggers the choice/auto-select
  logic instead of being silently missed.
- Added dedup (`_device_choice_last_pair`) so an unchanged USB/nRSP-ST pair
  doesn't re-broadcast `device_choice_available` repeatedly if SDRConnect
  resends `valid_devices` for unrelated reasons.

### Fixed (2026-07-29) — Clarified misleading Connection Setup wizard copy (USB detection dependency)

Live follow-up to the device-choice prompt above: user reported "w035 still
starts first before i make a selection" (meaning nRSP-ST specifically), with
the RSPdx physically connected via USB. Live inspection via Claude in Chrome
(DOM state + on-screen NEXUS log) showed this wasn't a bug in the new
ambiguity-detection logic — the new `#device-choice-modal` was correctly
hidden, and the modal the user was actually seeing was the pre-existing,
unrelated `#conn-wizard` (SSH/Connection Setup wizard, which opens on every
launch). The real cause: `valid_devices` from SDRConnect only listed the
three nRSP-ST stream-mode variants — SDRConnect itself wasn't reporting the
RSPdx at all (`_auto_select_device()` log: "No USB RSP and no default_device
configured"), most likely because SDRConnect hadn't detected/claimed the USB
device rather than anything NEXUS controls.

The wizard's "nRSP-ST / Local" tab copy claimed NEXUS "auto-prefers any
directly-connected USB RSP over a networked nRSP-ST" without mentioning this
only works once SDRConnect's own device list actually includes the USB
device — reading like a NEXUS bug when the real gap was upstream, in
SDRConnect's own hardware detection.

- Reworded the nRSP-ST/Local pane explainer, the `DEFAULT DEVICE` field's
  tooltip, and the `Auto (USB first)` button's tooltip to state plainly that
  NEXUS can only choose between devices SDRConnect's own `valid_devices`
  list reports, and that a USB device missing from that list needs fixing on
  the SDRConnect/hardware-detection side, not in NEXUS.
- No backend/logic changes — the device-choice feature itself (`Added
  (2026-07-29)` entry below) was confirmed working as designed.

### Added (2026-07-29) — Device-choice prompt: stop guessing nRSP-ST vs USB on startup

Live user report: "when starting nexus, the nrsp-st always connects first
and am unable to switch to the usb device. can there be a 'wait' until
user selects what they want to connect to?" — followed by "can we not add
a detection which shows the devices available to the user?"

`_auto_select_device()`'s `'auto'` mode always silently preferred a USB
device over a networked nRSP-ST when both were present — but SDRConnect
often already has the nRSP-ST actively streaming (its own persisted
last-used device) by the time NEXUS's one-shot, connect-time selector
runs, and switching a live device is unreliable without a proper
send + confirm handshake. In practice this meant the nRSP-ST effectively
always won, with no way to switch to USB short of unplugging it.

- `_auto_select_device()` (`'auto'` mode only — `'usb'`/`'nrsp'` forced
  preferences are unchanged) now detects the genuinely ambiguous case —
  a USB device AND a networked nRSP-ST both visible in `valid_devices` at
  once — and instead of guessing, broadcasts `device_choice_available`
  with both options and leaves SDRConnect's current selection alone.
  Falls through to the old auto-select behaviour when there's only one
  real device (no ambiguity, nothing to ask).
- New `select_device` WS command: sends `selected_device_name` then
  re-requests `active_device` after a short settle delay, reusing
  `set_stream_mode`'s already-live-tested confirm-handshake pattern so the
  IQ-enable sequence actually re-runs for the newly-selected device.
- The user's choice is remembered for the rest of the NEXUS process
  (`_user_selected_device`) so a WebSocket reconnect re-applies the same
  device instead of re-prompting or silently reverting to USB.
- Frontend: a device-choice modal appears when the backend broadcasts
  `device_choice_available`, listing each device with a 💻 USB / 🌐
  Network tag — click one to select it. A new "— device —" dropdown also
  appears in the top bar itself (independent of the SSH launcher's own
  device selector, which only shows during an active SSH session)
  whenever more than one real device is visible, so switching isn't a
  one-time startup-only choice — it's available any time from then on.

### Housekeeping (2026-07-29) — Folder tidy + docs updated for recent work

Cleared build clutter (`__pycache__`, an empty stray log file) and removed
~42MB of redundant old-version doc copies (`docs/{pdf,word}/w031–w034`,
`docs/md/w032`) that had been getting copied forward at every fork — each
of those versions already has its own complete copy in its own version
folder. w035/docs now holds only w035's own docs.

Updated all three w035 docs (User Manual, Quick Start, Troubleshooting)
for everything since the last doc build: the DRM audio slurred/slowed fix,
the bookmark Name/Notes fix, the audio-persists-after-quit fix, the SSH
wizard's default-to-Headless change, and the new device preference
feature — plus a brand new User Manual section (6.19) documenting the DRM
decoder itself, which had no documentation at all despite being fully
integrated. Also fixed a real pre-existing bug found along the way: all
three docs' running headers/footers said "w034" instead of "w035" (a
stale leftover from the w034→w035 fork), and several code-example lines
still referenced `w033_NEXUS.py` / `DARKSKY NEXUS w033 macOS.app` instead
of the current w035 filenames.

### Fixed (2026-07-29) — Bookmark notes shown instead of name

Live user report: fills in both Name and Notes in the bookmark dialog, but
the spectrum/waterfall label and the ⭐ BM panel card showed Notes instead
of Name. Root cause: both `drawSpectrumMarkers()` and `renderBookmarkPanel()`
had a heuristic that swapped in `bm.notes` as the primary label whenever
`bm.name` was 4 characters or shorter — which silently overrides any short
name (e.g. "BBC", "GB3", "R4", "4XZ") even when the user deliberately typed
one. Removed the length-based swap in both places: Name is now always the
primary label when present, Notes is only ever a fallback (spectrum pill)
or secondary sub-line (BM panel card) — never a silent override.

### Fixed (2026-07-29) — Audio persists after quitting NEXUS

Live user report: "when i quit and shutdown nexus .... audio persists".
`_graceful_shutdown()` terminates a fixed list of tracked subprocesses on
quit (`_rtl_proc`, `_hfdl_proc`, `_vdl2_proc`, `_dsd_proc`), but three
native decoder engines added since that list was written were never added
to it: `_dab_proc` (dab_radio_nexus), `_drm_proc` (dream_nexus), and
`_trunk_proc` (DSD trunking). All three open the SDR/network source
directly and just pipe raw PCM to Python over stdout — nothing else owns
that stream. `subprocess.Popen` children aren't killed automatically when
the parent process dies, so on quit these were left running as orphans,
still decoding and still holding the audio pipe open — exactly matching
the report. Added `_dab_proc`, `_drm_proc`, `_trunk_proc`, and
`_rtl433_proc` (same gap, no audio but same orphan risk) to the shutdown
termination loop.

### Added (2026-07-29) — Explicit device preference: USB RSP vs. nRSP-ST

`_auto_select_device()` previously had one rule: prefer a directly-connected
USB RSP if `valid_devices` contains one, otherwise fall back to the
configured Default Device (typically the nRSP-ST). That's wrong for anyone
who has both a USB RSP and a networked nRSP-ST reachable at the same time
and actually wants the nRSP-ST — there was no way to override it short of
unplugging the USB device.

- `SSH_DEFAULT_CONFIG["device_preference"]` — new key, `"auto"` /
  `"usb"` / `"nrsp"`, defaults to `"auto"` (old behaviour, unchanged).
- `_auto_select_device()` now branches on it: `"usb"` only ever selects the
  USB entry (no nRSP-ST fallback even if USB briefly drops off the list);
  `"nrsp"` always selects the networked nRSP-ST entry (or the configured
  Default Device) regardless of USB presence; `"auto"` keeps the original
  USB-first-then-default logic exactly as it was.
- New WS command `set_device_pref` — validates the value, persists it to
  `ssh_config.json`, updates the live in-memory config, broadcasts
  `{type:"device_pref", pref}` to all connected clients.
- Connection Setup wizard (nRSP-ST/Local tab) — new DEVICE PREFERENCE row
  with three buttons (Auto / Force USB RSP / Force nRSP-ST). Selecting one
  calls `_wzSetDevicePref()`, which sends `set_device_pref` and highlights
  the active choice immediately; the choice also reflects correctly when
  the wizard reloads via the existing `ssh_config` message, and syncs
  across any other open tab via the `device_pref` broadcast.

### Changed (2026-07-29) — SSH connection wizard: default to remote SDRconnect Headless

The "SDRConnect Server" tab's Mode A (SSH into a remote box, start SDRConnect
there, connect NEXUS) predates SDRconnect Headless (added in SDRconnect
1.0.7, Feb 2026) — its whole design was: run the old `--server` (raw
hardware bridge, port 50000 only, no WebSocket API) on the remote box,
then ALSO launch a full local SDRconnect GUI on this Mac just so
*something* exposes the WebSocket API at 127.0.0.1:5454 for NEXUS to talk
to. Headless makes that whole second hop unnecessary — it can open the RSP
*and* serve the WebSocket API entirely on the remote box by itself.

- `SSH_DEFAULT_CONFIG["remote_command"]` default changed from
  `./SDRconnect --server` to `./SDRconnect_headless --websocket_port=5454`
  (the frontend's own JS fallback already assumed this — only the Python
  default was stale).
- Added `_sdr_set_target(host, port)` — repoints the live SDRConnect
  WebSocket bridge (`SDRCONNECT_WS`) at runtime. `sdr_bridge()`'s reconnect
  loop reads that global by name fresh every iteration, so this takes
  effect on the very next (re)connect with no restart.
- `_ssh_do_launch()`'s "no local client configured" branch used to just log
  a message and do nothing else — NEXUS was still hardcoded to
  `127.0.0.1:5454`, which nothing was listening on, so this path never
  actually worked. Now calls `_sdr_set_target(ssh_host, 5454)` and polls
  the *remote* host's port 5454 for readiness (previously only the local-
  client branch was ever polled/verified).
- `_ssh_do_stop()` now reverts the target back to `127.0.0.1` on stop (only
  if this session had set it), and the remote pkill pattern is now derived
  from the actual configured `remote_command` instead of being hardcoded to
  `'SDRconnect --server'` — that pattern never matched a running
  `SDRconnect_headless` process, so stopping a headless remote session used
  to leave it running.
- `_ssh_launch_local_client()` now accepts a full command line (shlex-split)
  instead of only a bare path, so a *local* headless client with its
  `--websocket_port=` flag is also a supported LOCAL CLIENT value, not just
  local-GUI-with-no-args. Backward compatible with existing `.app`/plain-
  executable configs.
- Old `--server` + local-GUI-client path (Mode A's original design) still
  works unchanged if `local_client` is explicitly set — this wasn't ripped
  out, just no longer the default.
- Cleared a stale saved SSH config (`~/.darksky_nexus/ssh_config.json`)
  pointing at a private LAN address left over from earlier testing — not a
  live setup, confirmed with user.

### Changed (2026-07-28) — DRM tab: quick-tune as cards, 3-column layout

Live user feedback: the quick-tune list was a cramped scrollable row-list
squeezed into the same 220px sidebar as the frequency/robustness-mode
controls. Reworked into individual card buttons (`.drm-qt-card`, same grid/
card convention as DAB's `.dab-svc-grid`/`.dab-svc-card`) in their own
flexible grid column, with group headers as full-width grid items. Tab is
now 3 columns: controls (170px) / quick-tune card grid (flexible, main
real estate) / now-playing status (280px), instead of the old 2-column
sidebar+main split.

Researched Dream's own plot data (`PlotManager.h/cpp`, `ChannelEstimation`,
`CReceiveData` — all public methods `dream_nexus.cpp` can already reach)
for a possible "eye candy" visualization (input PSD spectrum, power delay
spectrum/impulse response, per-carrier SNR profile, transfer function, SNR
history) — genuinely feasible without touching Dream internals, but would
need a new emitted frame type + Python parser + frontend canvas + another
compile/link/deploy cycle. Deferred by user request ("keep this for
another day") — not implemented.

### Fixed (2026-07-28) — DRM audio "slurred/slowed" during live SDRConnect testing

Live-tested against a real off-air DRM signal (SNR Tiganesti E1, RRI relay,
9570 kHz, SDRConnect Full-IQ at 250 kSPS into `dream_nexus`) — real audio
came through, but stuttered/buffered and played back "slurred... slowed".
Root cause: `_serve_drm_audio()` (mirrors `_serve_dab_audio()`'s pattern)
writes the WAV header exactly once per HTTP connection, using whatever
`entry['sr']` was at that moment. DAB's per-subchannel sample rate is
fixed for the life of the broadcast, so that pattern is safe there — but
DRM's xHE-AAC/SBR codec can report a different `sample_rate` on later
frames than the very first one or two (the core decoder locks onto the
OFDM frame structure before SBR/bandwidth-extension is confirmed).
`_drm_store_audio()` already updates `entry['sr']` fresh on every incoming
`DRM1` frame, but the already-sent WAV header can't retroactively change —
once the true rate diverges from the header's declared rate, every further
PCM chunk plays back at the wrong speed under a now-stale header, which is
exactly what "slurred/slowed" sounds like (higher actual data rate than
declared → stretched out, lower pitch).

Fix: `_serve_drm_audio()` now closes the HTTP response the moment
`entry['sr']` diverges from the rate already baked into the header sent on
that connection, instead of continuing to stream mismatched data.
Frontend: added `ended`/`error` listeners on `#drm-audio` (new, DRM only —
DAB doesn't need this since its rate never changes mid-broadcast) that
reconnect with a fresh `/drm_audio` request whenever the stream ends
unexpectedly while `_drmRunning` is still true, which picks up a brand-new
WAV header at the by-then-stable rate. Gated on a new `_drmRunning` flag so
a deliberate `drmStop()`/`drmClear()` doesn't trigger an unwanted
reconnect.

### Fixed (2026-07-28) — `_escHtml` was never actually defined (app-wide, pre-existing)

Found while live-testing the DRM quick-tune list below: `_escHtml(...)` is
called throughout this file (ACARS/VDL2, WSPR, Trunk P25/DMR/NXDN
rendering, and now DRM) as if it were a shared global HTML-escaping
helper, but no such global function actually existed anywhere in the
file — the only `escapeHtml` present is a `const` scoped inside one
unrelated renderer, invisible to every other call site. Every one of
those call sites has been silently throwing `ReferenceError: _escHtml is
not defined` and failing to render whenever that code path actually ran,
masked completely by `handleJSONFrame`'s own `catch(e) { /* ignore
malformed */ }` around incoming WS message handling — no console error,
no visible crash, the row/panel in question just silently never updates.
Confirmed by bypassing that catch and calling a renderer directly in the
console. Fix: added a real global `_escHtml()` right before
`handleJSONFrame`, which fixes every pre-existing call site at once, not
just the new DRM one that surfaced it. Worth keeping an eye out for
whether any of those previously-silent failures were mistaken for "no
data" in ACARS/VDL2/WSPR/Trunk panels during past testing — this bug
would have made a message that should have rendered look like nothing
arrived instead.

### Fixed/Added (2026-07-28) — DRM tab: manual-tune bug + quick-tune frequency list

Found while starting Step 5's live SDRConnect wiring test: the DRM tab's
manual frequency entry silently did nothing useful — typing any
frequency and hitting Tune always retuned the SDR to 10 MHz regardless of
input. Root cause: `drmSetFrequency()` sent the retune as `{cmd:'tune',
freq: Math.round(mhz*1e6)}` (Hz, field named `freq`), but every other
tune call site in the app — and the backend's actual `tune` WS handler —
uses `{freq_mhz: <MHz>}`. The backend reads `d.get('freq_mhz', 10)`, so
the missing field silently fell back to its own default. One-line fix:
send `freq_mhz` like everything else does.

Also added a persisted DRM quick-tune list (`darksky_drm_quicktune.json`,
same load/save/WS-handler pattern as bookmarks: `drm_qt_list`,
`drm_qt_save`, `drm_qt_delete`), seeded with 39 publicly reported real DRM
frequencies grouped into AIR (India) mediumwave (24 channels, reported
24/7), shortwave DRM broadcasters (BBC WS, Radio Romania International,
Music 4 Joy, TDF, RNZI), and DRM+ VHF/FM trial frequencies (Germany,
Switzerland, France — experimental, may not currently be active). Manual
entry alone isn't very useful for DRM since there's no dial-scanning
convention most users already know the way there is for broadcast
FM/AM — a starting list of known frequencies is what actually gets
someone to a real signal on the first try. Fully user-editable after the
seed: a `+` button saves the currently tuned/entered frequency under a
custom label, each entry has its own remove control.

### Update (2026-07-28) — DRM build: Step 4 — `dream_nexus` confirmed genuinely decoding real DRM content

Follow-up to the entry below. `dream_nexus` now decodes real DRM audio
end-to-end through its own `CPipeSoundIn`/`CPipeSoundOut` pipe
interfaces — not just running cleanly (Step 3), but producing a real
decoded station label, real SNR, and real PCM audio from real DRM signal
content. Full methodology in `NEXUS_dream_drm_build_macOS.md`'s Step 4
section and Troubleshooting entry 19.

No genuine DRM I/Q capture was available to test with, so a real Dream
sample recording (`FMGold_xHE_ModeB_9khz.flac`, from the Dream project's
own public sample library on SourceForge — mono/real-valued, Dream's
classic file format, not complex I/Q) was converted into genuine complex
baseband I/Q via a measured-frequency Hilbert transform, then
cross-validated as a genuinely valid, decodable signal against Dream's
own stock binary (`-c 6`/`CS_IQ_POS_ZERO` inchansel mode) *before* being
trusted as a test input for `dream_nexus` itself — this two-step
validation is what made the eventual bug diagnosable rather than
ambiguous ("is it my synthesized signal or my new code?").

First attempt through `dream_nexus` produced silence — no lock, no audio
— despite the same I/Q being independently confirmed valid. Root cause:
`CDRMReceiver::LoadSettings()` unconditionally sets the receiver's
input-channel-selection mode from the settings file (or `CS_MIX_CHAN` —
average both channels into one real signal — if no settings file value
exists), and `dream_nexus.cpp` never overrode this. Averaging I and Q
together silently destroys a complex signal with no error, no crash, and
no obviously-wrong output shape — exactly the kind of bug a compiler and
even a plumbing-only smoke test (silence in, silence out — which passed
cleanly in the Step 3 entry below) can never catch. Fix: one line,
`DRMReceiver.GetReceiveData()->SetInChanSel(CS_IQ_POS_ZERO);`, placed
after `LoadSettings()` (must be after — `LoadSettings()` would otherwise
overwrite an earlier call).

After the fix: confirmed real decode. Status JSON showed
`station_label:"AIR Journaline"` (a genuine DRM service name pulled live
from SDC data), `snr_db:20.6`, and ~10.7MB of real `DRM1`-framed PCM
written to stdout.

**Known follow-up, not blocking:** the `locked` field in the status JSON
stayed `false` throughout this successful decode.
`GetAcquiState()==AS_WITH_SIGNAL` is the same check Dream's own
`ReceptLog.cpp`/`spectrumanalyser.cpp` use internally for "signal
present," so it's not obviously the wrong flag — but it may behave
differently on genuine live SDR I/Q (with real front-end AGC/noise-floor
characteristics) than on this synthesized test signal. Worth re-checking
once this is wired into live SDRConnect (Phase 2's `_drm_feed_iq()`).
Also still open: `--rxmode` (forcing a specific DRM robustness mode)
isn't wired up, and the DRM text-message/PAD field is stubbed empty.

**Still outstanding:** running `dream_nexus` against a genuine live
SDRConnect I/Q feed (as opposed to this file-based synthesized test) —
Phase 2's Python-side integration exists in the codebase but hasn't been
exercised against a running `dream_nexus` process yet.

### Update (2026-07-28) — DRM build: Step 3 (`dream_nexus` binary) confirmed working end-to-end

Follow-up to the entry below. `dream_nexus.cpp` now compiles and links
against a real `rafael2k/dream` checkout on Apple Silicon, producing a
working `dream_nexus` binary (`./dream_nexus --help` prints its own real
usage text — `--sample-rate`, `--rxmode`, `--freq-khz`). Full detail
(seven real API fixes, the standalone-compile + `make -n`-extracted-link
approach actually used instead of the originally-planned qmake-target/
CMakeLists routes) is in `NEXUS_dream_drm_build_macOS.md`'s Step 3 section
and its Troubleshooting entries 12-18.

Summary of the seven fixes, all against `dream_nexus.cpp` itself (as
opposed to Step 2's fixes, which were all in Dream's own upstream code):
`CDRMReceiver` has no `SetSoundInInterface`/`SetSoundOutInterface` of its
own — sound I/O is injected via `GetReceiveData()->SetSoundInterface()`/
`GetWriteData()->SetSoundInterface()` instead; `SetInitialRobustnessMode()`
doesn't exist on `CDRMReceiver` at all (no robustness-mode-forcing API was
located — `--rxmode` is accepted but not yet wired up, falls back to
auto-detect); `CParameter::Lock()` is a method, not a `std::mutex` object,
so the status thread's `std::lock_guard` had to become direct
`Lock()`/`Unlock()` calls; `CParameter` has no `TextMessage` field (stubbed
empty pending further investigation of the real `TextMessage.h` classes);
`CPipeSoundOut` was missing two of `CSoundOutInterface`'s pure virtuals
(`GetVersion()`, `GetItem()`), making it abstract; a dead
`GetSampleRate() override` referenced a virtual that doesn't exist; and
`argparse`'s `std::filesystem` usage needed a `10.15` deployment target
floor instead of Step 2's `10.13`.

**Still outstanding:** Step 4 — actually running `dream_nexus` against a
real DRM/DRM+ IQ capture or live SDRConnect feed. The binary runs and
parses its own CLI correctly; no audio has been decoded through it yet.
Also open: the `--rxmode` robustness-mode-forcing API and the real
DRM text-message/PAD source, both noted above.

### Update (2026-07-28) — DRM build: Step 2 (stock Dream console binary) confirmed working

Follow-up to the entry below. Jon ran the actual build on a real Apple
Silicon Mac and got `dream.app/Contents/MacOS/dream --help` printing
Dream's own usage text — the stock, unmodified Dream console binary now
builds and runs end-to-end from a fresh `rafael2k/dream` clone, following
`NEXUS_dream_drm_build_macOS.md`. Getting there took eleven real fixes
(full detail in that doc's Troubleshooting section): several Apple
Silicon Homebrew-path issues (`pkg-config` hardcoded to `/usr/local`,
`fftw`/`INCLUDEPATH` likewise, `speexdsp` being a separate package from
`speex`, `fdk-aac` simply not installed) and — more notably — four
genuine bugs in `rafael2k/dream`'s own `src/sound/drm_portaudio.h`/
`.cpp`/`soundfactory.cpp` unrelated to this integration at all (duplicate
base class, a stray typo character breaking a method declaration, wrong
class names in `soundfactory.cpp`, a method declared but never defined,
and a missing linker flag). None of that portaudio-backend code will
actually be used by `dream_nexus` itself (it injects `CPipeSoundIn`/
`CPipeSoundOut` directly, bypassing device enumeration entirely), but
fixing it through was worthwhile as an end-to-end toolchain sanity check
before touching `dream_nexus.cpp`.

**Still outstanding: Step 3** — adding `dream_nexus.cpp` itself to the
build and getting a working `dream_nexus` binary. That file's own API
usage (`CDRMReceiver` constructor/setters, `CSoundOutInterface`'s real
virtual list, `ERobMode` spellings, `CParameter` accessors) remains
unverified against a real compile, same caveat as before.

### Added (2026-07-28) — DRM / DRM+ decoder integration (Dream / `dream_nexus`)

New "DRM / DRM+" decoder tab, following `NEXUS_DRM_Dream_integration_plan.md`
closely and mirroring the DAB/DAB+ integration's own piped-subprocess
architecture (`dab_radio_nexus` → `dream_nexus`, same conventions).

**Status: code-complete but unbuilt/untested.** No C++ toolchain or Dream
source tree was available in this sandbox — `dream_nexus.cpp` has never
been compiled against a real Dream checkout. Several Dream API names
(`CDRMReceiver` constructor, `SetSoundInInterface`/`SetSoundOutInterface`,
`CSoundOutInterface`'s virtual method list, `ERobMode` enumerator spellings,
`CParameter` accessors) are best-effort from the integration plan's own
research and are flagged inline as likely needing small fixes on first
real build — see `NEXUS_dream_drm_build_macOS.md`'s own "first draft, NOT
yet build-tested" notice and its "things most likely to need adjusting"
list. Python and JS sides were verified for syntax only (`py_compile`,
`node --check`), not exercised against a live subprocess.

New/changed files:
- **`dream_nexus.cpp`** (new) — headless Dream wrapper. `CPipeSoundIn`
  reads interleaved int16 I/Q from stdin (Dream's own `CAudioFileIn` can't
  stream from a pipe — it `sf_seek()`s on open, which silently fails on a
  non-seekable pipe with zero/garbage audio, no error). `CPipeSoundOut`
  (this project's own addition — the integration plan only worked out the
  input side) captures Dream's decoded audio and frames it to stdout as
  `"DRM1" + sample_rate + is_stereo + bytes_per_sample + payload_len +
  payload`. Status snapshots (`locked`, `robustness_mode` A–E,
  `station_label`, `text_message`, `snr_db`, `mer_db`) are polled every
  500ms and emitted as `{"type":"drm_status",...}` JSON lines on stderr,
  rate-limited to >0.3dB SNR/MER changes.
- **`NEXUS_dream_drm_build_macOS.md`** (new) — build guide mirroring
  `NEXUS_dab_radio_build_windows.md`'s structure; explicitly marked
  untested, with a numbered list of the exact API-name risks to check
  against a real `src/DrmReceiver.h`/`src/sound/soundinterface.h`/
  `src/GlobalDefinitions.h`/`src/Parameter.h` once cloned.
- **`w035_NEXUS.py`** — full DRM backend: `_drm_launch()`/`_drm_terminate()`/
  `_drm_find_binary()` (mirrors the DAB trio exactly), `_drm_feed_iq()`
  (resamples raw hardware-rate IQ to 48000 Hz via `resample_poly`, writes
  interleaved int16 to `dream_nexus`'s stdin — DRM uses PCM16, not
  DAB's float32), `_drm_stdout_thread_fn()`/`_drm_stderr_thread_fn()`
  (demux "DRM1" audio frames / parse `drm_status` JSON), `drm_engine()`
  (0.25s subprocess lifecycle poll, same shape as `dab_engine()`),
  `_serve_drm_audio()` (dynamic-WAV-header HTTP stream at `/drm_audio`,
  simpler than DAB's since there's only ever one stream). New WS commands:
  `drm_start`, `drm_stop`, `drm_set_frequency`, `drm_set_rxmode`. Same
  generation-counter (`_drm_generation`) and retune-settle-window
  (`_DRM_RETUNE_SETTLE_S`) conventions as DAB, to stop stale frames from a
  just-killed subprocess bleeding into a new frequency's stream.
- **`DARKSKY_NEXUS_w035.html`** — new `#tab-drm` panel: frequency input +
  Tune button, robustness-mode selector (Auto/A–D), lock-status pill,
  station name/avatar, SNR/MER readout with signal bars (reusing DAB's
  `.dab-signal-bars`/`.dab-lock-dot`/`.dab-np-*` CSS classes — global, not
  scoped to the DAB panel, so no new CSS was needed), scrolling text
  message ticker (reuses `.dab-np-dls-track`), and an `<audio>` element
  pointed at `/drm_audio`. Registered `'drm'` alongside `'dab'` in every
  decoder-registry point: `DECODER_SLUGS`, `DECODERS_DB.external.items`,
  `_WIDEBAND_DECODERS`, `_IQ_DECODERS`, `decoderTabs`. New `case
  'drm_status':` in the WS message dispatch → `drmUpdateStatus()`;
  `drmStart()`/`drmStop()`/`drmClear()`/`drmSetFrequency()`/
  `drmSetRxmode()` send the corresponding WS commands. DRM is a
  single-station decoder (not DAB's multi-service ensemble grid), so the
  UI shape is closer to DSD/Trunk's simpler layout than DAB's card grid.

**To actually use this:** clone `github.com/rafael2k/dream` (or the
`F4JTV/dream` fork), follow `NEXUS_dream_drm_build_macOS.md` to build
`dream_nexus`, fix forward against whatever API names have drifted (the
doc explains exactly where to look), place the binary where
`_drm_find_binary()` looks (`/usr/local/bin/dream_nexus` on macOS, or
bundle it the same way `dab_radio_nexus` is bundled — see that binary's
own spec-file wiring for the pattern), then restart NEXUS. A Windows
build guide analogous to `NEXUS_dab_radio_build_windows.md` has not been
written yet — Phase 1 only produced the macOS doc, since that's what this
sandbox could reason about without a toolchain either way.

### Fixed (2026-07-28) — Windows build: cmd window flashes open/closed during DAB channel scan

Live user report on the Windows build: running the DAB Band III scan
flashed a console (cmd) window open and closed at every channel tested.
Cause: `dab_radio_nexus.exe` is a console application, and the NEXUS
backend itself is built `--windowed`/`--noconsole` — with no parent
console for the child process to attach to, Windows opens a brand new
one for it. `dabScanChannels()` relaunches `dab_radio_nexus` once per
channel (see `_dab_launch()`), so the scan looked like a rapid-fire
window flash. Fixed by passing `creationflags=CREATE_NO_WINDOW` to that
`subprocess.Popen()` call — no-ops harmlessly on macOS/Linux dev
machines via a `getattr(subprocess, 'CREATE_NO_WINDOW', 0)` fallback.

Follow-up: applied the same `creationflags=CREATE_NO_WINDOW` fix to the
other console-tool subprocess launches — `_launch_rtl433()`,
`_launch_dumphfdl()`, `_launch_dumpvdl2()`, the DSD engine loop, and the
OP25/trunk-recorder engine loop. All five now guard with
`getattr(subprocess, 'CREATE_NO_WINDOW', 0)`, a no-op on macOS/Linux.
DSD+'s own GUI audio-config window (Windows-only alternative to DSD) is
unaffected — CREATE_NO_WINDOW only suppresses the OS-allocated console
for a console-subsystem child, not a window the app creates itself.

Not touched: `fldigi.exe` and WSJT-X's launch are genuine Windows GUI
applications (confirmed by reading their launch sites) — CREATE_NO_WINDOW
wouldn't apply anyway, a GUI-subsystem executable never gets an OS
console regardless of this flag. `rtl_tcp` IS a real console tool and
would flash too, but it's launched once at RF-source startup rather
than repeatedly like the DAB scan — left alone for now since it's a
single flash, not a rapid-fire one; same one-line fix if it's worth
doing.

### Fixed (2026-07-28) — DAB: station card grid blanking when switching off "BBC Guide"

Live user report: on 12B/BBC National DAB, the 15-card station grid
stayed populated while "BBC Guide" was selected, but switching to "BBC
Radio3" (or any other real station) blanked it back to the scanning
placeholder — audio/Now Playing switched fine, only the grid broke.

Root cause: `dabUpdateEnsemble()` treated *any* `dab_ensemble` broadcast
with an empty `services` array as "not locked yet" and unconditionally
replaced the rendered grid with `DAB_SCANNING_HTML`. BBC runs dynamic
ensemble reconfiguration on 12B, and "BBC Guide" specifically is a
non-audio EPG/MOT data service whose own subchannel gets reallocated as
part of that reconfiguration — so `dab_radio_nexus` can legitimately
emit a momentary empty/partial `dab_ensemble` line while re-parsing the
MCI after a reconfig event, with nothing actually broken. A real DAB
receiver doesn't blank its station list over that.

Fixed by falling back to the already-cached last-known-good snapshot in
`_dabEnsembleHistory[ch]` (which the same function already maintains)
instead of discarding a working grid — only shows the scanning
placeholder if this channel has genuinely never locked at all. Also
made the ensemble-name text and "locked" dot/status-pill state consider
the cached snapshot, not just the current broadcast, so they don't
flicker unlocked during the same momentary gap.

Decoding "BBC Guide"'s actual EPG payload (FIC parsing, MSC packet-mode
reassembly, MOT objects, TS 102 818 schedule data) is a distinct,
much larger potential feature — out of scope for this fix, noted as a
possible future project if wanted.

### Redesigned (2026-07-28) — Retro scene: dial/signal gauge moved down near scene buttons

User request: move the tuning dial and SIGNAL needle down, closer to the
cinematic scene-select buttons, to free up vertical space in the middle
of the panel for the station name/DLS text (see previous fix). Moved
`cy` from `H*0.66` to `H*0.82`; extended `panelH` from `H*0.68` to
`H*0.86` so the brass chassis frame grows to actually enclose the
relocated dial instead of it floating below the panel edge; dropped
`#cin-info`'s retro `bottom%` override from 66% to 58% to keep the meta
line/exit hint paired just above the dial's new position. Checked
clearance numerically at H=600/800/1080 — smallest margin (H=600) is
14px between the dial's lowest label and the panel edge, 22px to the
scene-bar row; both positive at every size tested.

### Fixed (2026-07-28) — Retro scene: station name/DLS text overlaid on nixie tubes

Screenshot showed "BBC RADIO6MUSIC" and the DAB DLS "Now Playing…" line
printed straight across the middle of the nixie digits. `#cin-station`
had a fixed `top:12%`, but `#cin-nixie` is sized in px/vw (not vh) so its
rendered height varies with window size/aspect — no static percentage
holds at every window size. Fixed with a measured layout instead of a
guessed one: `_cinLayoutRetroStation()` reads `#cin-nixie`'s actual
`getBoundingClientRect()` and places `#cin-station` 14px below its
bottom edge. Runs on scene switch to Retro and on window resize while
Retro is active; other scenes still use the default CSS `top:12%`.

### Redesigned (2026-07-28) — Retro panel: brass hardware pass

User compared the live screenshot against a steampunk reference render
(brass control panel, rivets, engraved gauge housing, glass reflection)
and it didn't land — the panel read as a soft translucent overlay, not
metal hardware. Added: bolt-head rivets spaced along the panel border +
reinforced L-bracket corners (`_cinDrawRivets`/`_cinDrawCornerBracket`);
a brass bezel ring around the tuning dial with two end-cap housings at
the arc's terminals (mimicking a physical meter bolted to the panel); a
diagonal glass-reflection highlight clipped to the dial face; a
GOOD/FAIR/WEAK signal-quality word under the SIGNAL label, mirroring the
reference's paired labels. Panel fill/border also darkened and thickened
for a more solid "brass plate" read instead of glass.

Deliberately did not restyle the NEXUS/RETRO/BARS/PHOSPHOR/POLAR scene
tab bar — that's shared chrome across all 5 cinematic scenes, not
Retro-specific, so turning it into brass knobs would look wrong under
the other 4 scenes.

### Redesigned (2026-07-28) — Nixie readout rebuilt as real SVG, not canvas

Third pass on the Cinematic Retro nixie display. Canvas `shadowBlur` was
always an approximation of glow; rebuilt the whole readout as an inline
SVG element (`#cin-nixie`, positioned over the canvas via CSS) so the
glow is a genuine `feGaussianBlur` filter. Each digit tube is now a
capsule-shaped glass body (`rx=ry=width/2` rounded rect, like a real
IN-14/IN-17 envelope) with straight cathode-grid wires clipped to the
glass, a warm top-of-tube ambient glow, and a filled+stroked digit sat
on a `feColorMatrix`-tinted blurred halo — closer to the reference nixie
photos than the earlier dome-path/diagonal-mesh/stroke-only-wire canvas
version. No third-party image assets used (researched first — no
suitably licensed free nixie asset pack exists — so this is entirely
self-authored SVG/JS, avoiding any licensing risk).

`_cinSceneRetro()` no longer draws the readout itself; it just calls
`_cinNixieUpdate(freqStr)`, which rebuilds the SVG's digit group only
when the displayed string actually changes (not every animation frame).
Old canvas helpers (`_cinNixieDomePath`, `_cinDrawNixieBase`,
`_cinDrawNixieDigit`, `_cinDrawNixieSpacer`) removed entirely.

### Fixed (2026-07-28) — Cinematic HUD: "DAB · BBC National DAB" text stutter

`_cinMetaLine()` always led with a `DAB`/`DAB+` badge before the ensemble
name, but most UK ensemble names already contain the word "DAB" (e.g. "BBC
National DAB"), producing a visible stutter. Now checks the ensemble label
with `/\bdab\b/i` first and only shows the leading badge when the name
doesn't already say it.

### Fixed (2026-07-28) — Nixie digits were solid filled blocks, not glowing wire

Live screenshot showed the digits rendering as thick filled sans-serif
characters — looked like a printed number, not a nixie tube. Real
nixie/wire-filament digits are thin glowing *outlines*; the fix was to
stop using `fillText()` for the digit and switch to a two-pass
`strokeText()`: a wide, heavily-blurred stroke first for the ambient
glow bleed, then a thin crisp stroke on top for the visible filament
line. Also bumped the cathode-mesh backdrop opacity (0.10→0.16) and made
it an actual crossed lattice instead of one diagonal direction, and
strengthened the glass envelope's outline/added a faint inset rim line
so individual tubes read as distinct glass shapes rather than merging
into one glow blob. Re-verified via the same Node Canvas2D mock harness
(no headless browser/`node-canvas` available — no network access in the
sandbox to install either); still needs a live look to confirm the wire
effect actually reads as intended.

### Redesigned (2026-07-28) — Retro scene: nixie-tube frequency readout replaces the valve row

User feedback on the valve row: "the valves look more like fake candles" —
and asked for a nixie-tube-clock-style readout instead (referencing
vintage/steampunk nixie clock photos). Replaced both the valve row and the
plain neon `#cin-freq-display` numeral with one glass tube per digit,
standing on a wood-plank base:

- New helpers `_cinDrawNixieDigit()`, `_cinDrawNixieSpacer()`,
  `_cinDrawNixieBase()`, `_cinNixieDomePath()`. The glass dome is built
  from two `quadraticCurveTo()` curves rather than `ctx.arc()` — arc's
  start/end-angle sweep direction is easy to get backwards; the bezier
  approach is unambiguous.
- Digits come from the live tuned frequency (`toFixed(3)`, split into
  integer/decimal parts), laid out dynamically so it works whether the
  band shows 1, 2, or 3 integer digits (3.500 / 14.074 / 225.648 all
  tested). A slim decorative "spacer" tube with a tiny glowing dot marks
  the decimal point — the same trick real nixie-clock kits use for a
  colon/separator tube — so the reading stays unambiguous, not just
  decorative filler.
- Digit glow brightness is NOT tied to spectrum energy (unlike the old
  valves) — it's real information, so it stays a small, non-data-driven
  flicker (0.94–1.0) for atmosphere instead of dimming unreadable when a
  band happens to be quiet.
- `#cin-overlay[data-scene=retro] #cin-freq-display{display:none}` added
  so the old plain-neon numeral doesn't double up with the new tubes.
- Re-verified with the Node Canvas2D mock harness across 4 test
  frequencies (1/2/3-digit MHz values) and 2 frames each — all draw calls
  finite, base+tube row width stays well inside the panel bounds. Same
  caveat as before: no headless browser or `node-canvas` available in the
  sandbox (no network access), so this is geometry/NaN verification only,
  not a real screenshot.

### Fixed (2026-07-28) — Retro scene: dial arc was colliding with the frequency readout

Live screenshot from the user caught the real problem with the first pass:
`#cin-info` (the giant frequency number, DAB/RDS meta line, and exit hint)
is pinned by CSS at `bottom:66%` for this scene — a value tuned for the
old, thinner ruler-band dial. The new bigger semicircular arc rose right
through that text, so the tick marks and the "225.648" numerals were
overlapping and hard to read.

- Dial recentred lower and shrunk (`cy: H*0.66`, `dr: mm*0.24`, was
  panel-relative `*0.74`/`*0.30`) so the arc's top edge sits at ~41% down,
  clear of the text block's ~34% bottom edge.
- Panel silhouette was also nearly invisible in the screenshot — bumped
  gradient/border opacity, grain-line opacity, and added a thin inner
  bevel highlight so it actually reads as a recessed chassis panel.
- Panel enlarged (`panelH: H*0.68`, was `*0.64`) to comfortably contain
  the now-lower dial with less unused space at the bottom.
- Re-verified with the same Node Canvas2D mock harness (still no headless
  browser/`node-canvas` available in the sandbox — no network access to
  install either) and manually confirmed the arc-top vs text-bottom
  vertical math clears with margin. Needs one more live look to confirm
  the fix actually reads correctly on screen.

### Redesigned (2026-07-28) — Cinematic Mode "Retro" scene: vintage valve radio

Rebuilt `_cinSceneRetro()` from scratch as a proper vintage tube-radio
panel, per a design brief agreed with the user (hybrid dark/wood-panel
silhouette, semicircular needle dial, glowing valve row, fully
signal-reactive):

- New soft wood/Bakelite panel silhouette (rounded rect, subtle grain
  lines, brass-toned border) frames the scene without fighting NEXUS's
  dark theme — replaces the previous plain radial-gradient background.
- The old horizontal frequency ruler + separate quarter-circle VU meter
  are merged into one big backlit semicircular dial: fixed tick marks
  and a hairline mark the tuned frequency (the displayed span is always
  centred on it), while an amber needle sweeps live with signal strength
  off the same pivot — a classic combined dial/S-meter layout.
- The 5 bottom-right glow blobs (driven by per-band spectrum energy, kept
  from the old version) are now drawn as an actual row of vacuum tubes
  across the top — glass envelope, glowing filament, socket base with
  pins — instead of plain circles.
- Verified with a Node-based Canvas2D mock harness (no headless browser
  available in the build sandbox): ran the extracted function against
  realistic bin/level data across two frames, checked all ~1,170 drawing
  coordinates for NaN/Infinity, and confirmed panel/dial/tube bounds sit
  sensibly within the canvas. Visual confirmation still needed live.

### Added (2026-07-28) — Cinematic Mode now shows DAB now-playing info

Cinematic Mode's station name, scrolling subtitle, and mode/rate HUD line
were entirely unaware of DAB — they're all driven off the primary VFO
(mode, freq, RDS), but DAB decodes a whole ensemble independently of VFO
tuning. Result: with a DAB service actively playing, Cinematic Mode kept
showing whatever the VFO last did (e.g. leftover WFM/RDS station info),
never the DAB station.

- `_cinGetStationName()`: now checks `_dabPlayingSid` first and returns the
  playing DAB service's name (from the live ensemble message, falling back
  to the player column's own label) — takes priority over RDS/EIBI/
  bookmark since it's an explicit user pick, not passive tuning.
- `_cinUpdateStation()`: the scrolling subtitle now shows the DAB Dynamic
  Label (DLS) text in place of RDS RadioText while a DAB service plays.
- New shared `_cinMetaLine()` helper replaces three copies of the same
  "mode · rate · quality" string-building logic (VFO state-update handler,
  Cinematic Mode entry, and the per-frame HUD refresh). For DAB it renders
  `DAB/DAB+ · <ensemble> · CH <channel>` instead of `<mode> · <MSPS> · SNR`.

### Fixed (2026-07-28) — FM RDS PI code now actually reaches the display

PI was decoded by the backend (passthrough from SDRConnect's own RDS
decoder) but never made it to screen. Two separate bugs:
- Backend: `rds_ps`/`rds_radiotext` broadcast the consolidated state
  immediately on change; `rds_pi`/`rds_pty` didn't — they only went out
  whenever some other property happened to trigger a broadcast. Added the
  missing `await broadcast_json({"type": "state", **state})` to both
  branches (`w035_NEXUS.py`).
- Frontend: the `#rds-pi` span existed and was already being written to
  (`"PI:" + pi`) by `_rdsUpdate()`, but was hardcoded `style="display:none"`
  — dead on arrival regardless of the backend fix. Un-hidden and given a
  small muted style matching `#rds-pty`, positioned between PTY and
  RadioText in the RDS strip (`DARKSKY_NEXUS_w035.html`).

### Removed (2026-07-28) — DAB tab: "How this works" engineering-detail panel

Removed the collapsible "How this works" panel from the DAB diagnostics
drawer (the `dab_radio_nexus` ensemble-decode explainer with the amber/
blue/green bullet lines). It rendered with hardcoded mid-sentence `<br>`
breaks that didn't adapt to the panel's actual width, so on wide screens
it stacked into a choppy single-phrase-per-line column instead of wrapping
naturally. Rather than fix the wrapping, removed the panel outright per
user call — it was optional engineering trivia, not something end users
need. Removed the HTML block, its dedicated CSS rules (`.dab-info-card`,
`.dab-details-toggle`, `.dab-details-panel`, etc.), and the
`dabToggleDetails()` JS function; confirmed no other references remain.

### Forked (2026-07-28) — w035 created from w034

w035 forked directly from w034 (published release). All new work now
happens here; w034 is frozen as the last published version. Known items
carried over, not yet actioned:
- FM RDS PI code display — fixed same day, see "Fixed (2026-07-28)" entry
  above.
- DAB MOT slideshow never appears for BBC Radio6Music — investigation
  still open (see "Diagnostic (2026-07-27)" entry below, carried from w034).
- w035 DRM/DREAM integration is the planned headline feature — see
  `WRITING/` planning doc from the w034 research pass.

w030 is forked directly from w026 — **not** from w029. w027/w028 were
Jon's own dockable-window UI experiments (not wanted for NEXUS going
forward); w026 is the actually-deployed baseline. w029 turned out to be a
mis-fork (see below) and is being superseded by this folder. Everything
below "## w030" is new; everything under "## Inherited history" is
unchanged from `../w026/CHANGELOG.md` (that file remains the authoritative
copy for the full w0.0.5→w0.2.6 history) — reproduced here for continuity
since `w030_NEXUS.py`'s docstring only carries the current version's
summary.

---

### Verified (2026-07-27) — Windows DAB engine build, first real end-to-end run

`WRITING/NEXUS_dab_radio_build_windows.md` had never actually been run
against a real Windows machine (flagged as such in the doc itself since
2026-07-26). Jon ran it end-to-end today — build succeeded and the engine
was confirmed decoding a live ensemble (BBC National DAB, 12B / 225.648
MHz) via a real RSPdx through SDRConnect, with audio playing.

**Real-build fix:** Step 3's static-linking flags
(`-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded`) didn't take effect even
after a full clean `rmdir /s /q build` + reconfigure — `dumpbin
/dependents` on the resulting `dab_radio_nexus.exe` still showed
`MSVCP140.dll`/`VCRUNTIME140.dll`/`VCRUNTIME140_1.dll`, meaning the exe
was still linking the dynamic MSVC runtime. Root cause: DAB-Radio's own
`CMakeLists.txt` declares `cmake_minimum_required(VERSION 3.10)`, and
CMake's `CMP0091` policy — which is what makes
`CMAKE_MSVC_RUNTIME_LIBRARY` do anything at all — only defaults to `NEW`
when the project requests CMake 3.15+. Below that, the policy silently
stays `OLD` and the runtime-library setting is ignored outright, with no
warning. Fix (no edit to DAB-Radio's own `CMakeLists.txt` needed): add
`-DCMAKE_POLICY_DEFAULT_CMP0091=NEW` to the Step 3 configure command.
Confirmed: `dumpbin` afterward showed only `KERNEL32.dll`, matching the
doc's original expected output. `WRITING/NEXUS_dab_radio_build_windows.md`
updated with this flag baked into Step 3's command, a new explanation
paragraph, and a corrected Troubleshooting entry (the doc previously
attributed this failure mode purely to a stale `build\` folder, which
real testing showed doesn't fix it on its own).

**Also documented:** Step 5's raw-file test needs a capture at exactly
2.048 MSPS, which SDRConnect on this project's hardware can't produce
directly (only fixed rates like 2 or 5 MSPS) — the doc now notes
resampling the file yourself first, or the simpler alternative used for
this real run: running `w034_NEXUS.py` itself against live SDRConnect,
since `_dab_feed_iq()` already resamples arbitrary source rates and this
exercises the whole real pipeline rather than the engine in isolation.

---

### Added (2026-07-27) — Troubleshooting doc: macOS "app is damaged" Gatekeeper entry

Live user report: downloading the w033 `.dmg` in Brave produced `"DARKSKY
NEXUS w033 macOS.app" is damaged and can't be opened. You should eject the
disk image.` — a much scarier message than the existing "unidentified
developer" warning already documented, even though the root cause is the
same (unsigned, non-notarized build + browser quarantine flag). macOS
Ventura and newer show this "damaged" wording instead of "unidentified
developer" once Gatekeeper's signature check fails outright rather than
just missing a signature — the download itself is not corrupted. Added a
new entry right after the existing one in the macOS Specific section
covering both fixes: `xattr -cr` in Terminal (fastest), and the no-Terminal
System Settings → Privacy & Security → "Open Anyway" path. Also fixed a
stale "DARKSKY NEXUS w033 macOS" reference in the existing entry's
instructions (should have read w034). Rebuilt docx + PDF and verified via
LibreOffice render.

---

### Changed (2026-07-27) — DAB tab: removed manual tune control + Now Playing bar-graph

Live user request, two items:

1. **Manual [MHz] Tune removed.** The free-entry frequency input next to
   the Band III quick-tune grid is redundant now that the background
   scanner (`dabScanChannels()`) already covers every Band III channel —
   nothing manual entry could reach that scan doesn't already find.
   Removed the `.dab-manual-tune` CSS block, the `<div id="dab-manual-tune">`
   markup (input + Tune button), the `dabManualTune()` function, and the
   `manualEl` show/hide references in `dabPopulateChannels()`.
2. **Now Playing bar-graph removed.** The 20-bar orange equalizer
   (`#dab-eq`/`.dab-np-eq`) under the slideshow art was a real Web Audio
   `AnalyserNode` tap on the decoded PCM (not decorative), but added no
   real value for an SDR tool — it visualizes the audio codec's output,
   not RF signal quality, which is what a DAB user actually cares about.
   Removed the CSS, the `<div id="dab-eq">` markup, `_dabEnsureAnalyser()`,
   and the `_dabEqTick()` rAF loop. That loop was also the ~1s throttle
   driving the signal-bars/elapsed-time/diagnostics-drawer refresh, so it
   was replaced (not just deleted) with a plain `setInterval`-based ticker
   (`_dabStartNpTicker()`/`_dabStopNpTicker()`) that keeps those three real
   readouts updating exactly as before, without any audio analysis or
   bar rendering.

No backend changes — both were frontend-only. Verified both inline
`<script>` blocks with `node --check` after the edits.

---

### Diagnostic (2026-07-27) — DAB MOT slideshow never appears (BBC Radio6Music)

Live user report: BBC Radio6Music (BBC National DAB, 12B) plays audio and
updates DLS text ("Lauren Laverne" etc.) perfectly, but the NOW PLAYING
column never shows a slideshow image. Side-by-side comparison against
AbracaDABra on the exact same station/channel/moment confirmed the
broadcast genuinely IS carrying an MOT slideshow (BBC 6 Music logo) right
now — so this is a real decode gap in NEXUS, not a "station doesn't send
one" situation. Traced the whole pipeline: frontend `dabUpdateSlideshow()`,
`w034_NEXUS.py`'s DAB2-frame relay, and `dab_radio_nexus.cpp`'s subscribe-
and-forward wiring to DAB-Radio's `Basic_Slideshow_Manager` are all
confirmed correct — none of them are where this is being lost. Since DLS
text (which rides the same underlying `PAD_Processor`) works fine on this
exact station, PAD/X-PAD data is provably reaching the decoder; the
remaining suspect is upstream, inside DAB-Radio's own MOT reassembly/
classification (`Basic_Slideshow_Manager::Process_MOT_Entity()` silently
returns nullptr — no log line — for any completed MOT entity whose
content_type/content_sub_type doesn't map to exactly IMAGE_JPEG/IMAGE_PNG).

Added a temporary diagnostic hook (`emit_mot_debug()` + a new
`channel.OnMOTEntity().Attach(...)` subscription in `attach_audio_channels()`,
`dab_radio_nexus.cpp`) onto `Basic_Audio_Channel`'s existing but previously
unused `OnMOTEntity()` observable, which receives every completed MOT
entity `Process_MOT_Entity()` rejected as non-slideshow. Emits a
`dab_mot_debug` stderr JSON line with subchannel_id/transport_id/
content_type/content_sub_type/header_size/body_size/content_name for each
one. Next build+test on BBC Radio6Music will show either (a) this never
fires — bug is further upstream in `PAD_MOT_Processor`'s X-PAD reassembly
never completing — or (b) it fires with a content_type/sub_type that isn't
IMAGE_JPEG/IMAGE_PNG — BBC is sending a slideshow variant DAB-Radio's
classification doesn't recognise, needing a small upstream fix. Purely
additive/diagnostic — no existing behaviour changed. Remove once the root
cause is confirmed.

---

### Fixed (2026-07-26) — DAB player Dynamic Label (DLS) text clipped top/bottom

Live user report with screenshot: the scrolling "now playing" text under
the slideshow art (station DLS feed — song title, "Call the Shots", etc.)
looked visually cut, like characters were sliced in half. Root cause:
`.dab-np-dls-wrap` was 15px tall (border-box), minus its 1px top/bottom
borders and 2px top/bottom padding left only 9px of content area for a
10px-font `.dab-np-dls-track` with normal line-height (~12px) — the
`overflow:hidden` needed for the scroll animation was clipping every
glyph's ascenders/descenders. Bumped the wrap to 20px (14px content area),
made it `display:flex;align-items:center` so text centers regardless of
exact font metrics, and set the track's `line-height:1` to tighten its own
box. No JS changes — pure CSS fix.

### Fixed (2026-07-26) — DAB never counted toward "Active decoders: N"

Live user report: the bottom status bar reads "Active decoders: 0" the
entire time DAB is genuinely decoding. Root cause: every other decoder
(cw/rtty/wefax/ft8/acars/pocsag/scanner/ais/fldigi) goes through a shared
`activate_decoder`/`deactivate_decoder` WS command that broadcasts
`{"type":"decoder_status","slug":...,"active":...}` — the message
`_updateDecoderBar()`/`DS._activeDecoders` (and the status-bar count/pill
list it drives) actually listens for. DAB was built later as its own fully
independent subsystem (`dab_start`/`dab_stop`/`dab_set_channel`, its own
subprocess lifecycle) and never participated in that shared mechanism, so
it never sent this message at all — not a bug in the counting logic
itself, just a decoder that was silently invisible to it. Since the
frontend handler is slug-agnostic (`DS._activeDecoders[msg.slug] =
msg.active`), no frontend change was needed: added the same
`decoder_status` broadcast to `dab_start`/`dab_stop` (`w034_NEXUS.py`).
Also added a `dab` entry to the frontend's `DECODER_COLOURS` lookup
(`DARKSKY_NEXUS_w034.html`) so it gets a proper "📻 DAB/DAB+" pill instead
of falling back to a bare uppercased slug.

**Python-only + browser reload — no C++ rebuild.** Restart
`w034_NEXUS.py` and refresh; starting DAB should now show "Active
decoders: 1" with a DAB pill, same as every other decoder.

### Investigated (2026-07-26) — station logo never appears in DAB player

Live user report: no MOT Slideshow image ever shows for the station
they're listening to. Traced the entire pipeline end to end rather than
guessing — all four layers check out correct:

- **`dab_radio_nexus.cpp`**: `radio.On_Audio_Channel().Attach(...)` fires
  once per newly-discovered subchannel, and *inside* that per-subchannel
  callback, `channel.GetSlideshowManager().OnNewSlideshow().Attach(...)`
  is registered individually for every service (not just one channel by
  mistake) — confirmed by reading the actual attachment code, not assumed.
- **`_dab_stdout_thread_fn()`** (`w034_NEXUS.py`): correctly demuxes
  `"DAB2"` slideshow frames alongside `"DAB1"` audio frames, generation-
  gates them the same way audio is gated, and broadcasts
  `{"type":"dab_slideshow",...,"image_b64":...}` correctly.
- **`dabUpdateSlideshow()`** (`DARKSKY_NEXUS_w034.html`): correctly filters
  to `msg.sid === _dabPlayingSid` (same guard `dabUpdateDls()` uses) and
  renders the base64 image with the right MIME type once that matches.

No bug found anywhere in the chain. The far more likely explanation,
already anticipated in this codebase's own comments
(`_dabResetDlsAndSlideshow()`: "not every station sends one"): MOT
Slideshow is optional broadcaster-side encoding, and plenty of UK local/
regional DAB+ stations only send DLS text, never a logo image — this is
normal, not a defect. Worth confirming by tuning to a station more likely
to actually broadcast one (e.g. BBC National DAB) before assuming this is
still a NEXUS-side bug.

### Fixed (2026-07-26) — Scan STILL misattributing one real ensemble to every channel (real root cause this time)

Live user report, with screenshot, of the exact same symptom the
2026-07-25/26 generation-counter and launch-time-channel fixes (above)
were supposed to have closed: every channel from 5A through 10D listed
in both the sidebar and the "other ensembles" grid rows as "Aberdeen,
15 stations" — a single real ensemble smeared across 20+ channels that
can't possibly all be broadcasting the identical multiplex.

Re-verified the earlier fixes are actually solid: `_dab_generation` is
bumped and checked correctly, and `dab_ensemble` broadcasts really do
carry `channel` captured once at each subprocess's own launch time, never
re-read live. So this is a **different bug wearing the same symptom** —
not mislabelling, but genuinely stale RF content reaching a correctly
labelled subprocess. `_dab_feed_iq()` is called inline, synchronously, for
every raw IQ packet the instant SDRConnect delivers it — there's no
buffering on NEXUS's own side to flush on a channel change. The
`dab_set_channel` handler's own comment assumed "by the time this branch
runs, the hardware is already retuned" — untested, and wrong: an SDR's LO
PLL lock time plus SDRConnect's command round-trip isn't guaranteed to fit
inside the gap between sending 'tune' and this handler running,
especially across a fast 32-channel scan where each channel gets only
1–3 seconds. `dab_radio_nexus` was being fed (and decoding) IQ still
physically centred on the *previous* channel for a beat after every
retune — genuinely, correctly decoding whatever real ensemble was
actually there (Aberdeen), and correctly labelling it with the *new*
channel because that's what `state['dab_channel']` said by then.

Fixed with a settle gate, not a re-litigation of the tagging logic: new
`state['dab_channel_changed_at']`, stamped in the `dab_set_channel`
handler; `_dab_feed_iq()` now drops any IQ arriving within
`_DAB_RETUNE_SETTLE_S` (350ms) of the last channel change instead of
feeding it to the subprocess at all, so no transitional-frequency content
can ever reach it. 350ms is under 10% of the scan's existing 3.5s
per-channel budget (`_DAB_SCAN_TIMEOUT_MS` in the frontend, unchanged) —
deliberately short, but should safely clear typical SDRplay LO settle
time.

**Python-only — no C++ rebuild, no frontend change.** Restart
`w034_NEXUS.py` and re-run the scan to verify: this needs a real
over-the-air retest since it depends on actual SDR settle timing, not
something a syntax check can confirm.

### Fixed (2026-07-26, part 2) — 350ms settle gate wasn't nearly enough

Live re-test, after a confirmed clean run (backend restarted, browser
`_dabEnsembleHistory` cleared first — so this genuinely wasn't stale
client-side state): the identical symptom persisted, now with a
screenshot showing the scan's own found/miss tally correctly narrowed to
just 11C/12A/12B (proving the generation-counter and channel-tag fixes
above really do work), while the sidebar/collapsed-grid ensemble history
*still* showed 5A through 8A all as the same real 29-station national
multiplex. That ruled out mislabelling as the cause a second time and
pointed squarely at the settle gate's duration: 350ms was an arbitrary
guess. This exact tuning pipeline already has its own, already-established
estimate for real SDR/driver settle time — the `'tune'` WS handler sets
`ignore_center_until = time.time() + 0.8` specifically because it doesn't
trust SDRConnect's own retune-confirmation echo to land any sooner. Raised
`_DAB_RETUNE_SETTLE_S` to 1.0s (a little margin over that existing 0.8s
precedent) instead of inventing another number. Also checked whether the
SDRConnect command queue itself could be backing up under a fast scan's
rapid tune commands (would make any fixed delay unreliable regardless of
its length) — its drain loop (`tx()`) sends immediately with no rate
limiting, so queue backlog isn't the bottleneck; this is genuinely just
hardware/driver settle time.

**Python-only — restart `w034_NEXUS.py` and re-scan to verify.** If this
still reproduces, the next thing to check is whether the SDR is actually
confirming the new center frequency at all within a few seconds (add
temporary logging around the `center_hz` echo handler) rather than
guessing at a longer timer again.

### Fixed (2026-07-26) — DAB equalizer: right-hand bars dead, panel "bouncing"

Live user report with screenshot, two symptoms circled on the NOW PLAYING
equalizer (`_dabEqTick()`, tapped off a real Web Audio AnalyserNode on the
`#dab-audio` element — not a decorative canned animation):

**"These bars never move":** each of the 20 bars sampled exactly one FFT
bin, spread linearly across the analyser's 32 bins (`fftSize=64`). That put
the right-hand bars on the highest-frequency bins, which sit near-silent
for typical DAB content (speech/talk radio — the screenshot was talkSPORT
commentary — and most music besides). They weren't frozen, they were
honestly reporting close to zero energy up there; it just looked broken.
Changed to a log-scale band grouping (squaring the fractional bar
position widens each band toward the high end, concentrating resolution
where energy actually lives) with a **peak** (not average) taken across
each bar's band, so every bar now reflects real content regardless of
program material.

**"Graph causing slideshow box and text to bounce":** the bar height
formula could reach `2 + 1×33 = 35px` — 3px taller than `.dab-np-eq`'s
fixed 32px box, which had no `overflow:hidden`. Since `.dab-player` (the
whole NOW PLAYING column) has `overflow-y:auto`, that intermittent 3px
overflow nudged the panel's scrollable content height every time a bar
peaked, jittering every sibling above it (slideshow art, DLS text) at
whatever rate the audio was peaking. Added `overflow:hidden` to
`.dab-np-eq` as a hard backstop, and capped the new peak formula at
`2 + v×28 = 30px` so the box is never actually pushed to clip anything in
normal operation.

### Added (2026-07-26) — Manual DAB frequency entry

Live user request: let users tune to any frequency, not just the fixed
32-button Band III grid. As investigated above, this needed **zero
backend changes** — `dab_set_channel` already accepts any channel label +
`freq_mhz` with no validation, and `dabTuneChannel()` is the same
channel-agnostic retune entry point every existing DAB UI trigger already
uses. Added a compact "Manual [MHz input] Tune" widget to the DAB topbar,
right next to the channel grid (`#dab-manual-tune`, styled to match the
grid's density). Enter key or the Tune button both call the new
`dabManualTune()`, which parses the typed value, rejects non-numeric input
and anything outside a loose 174–240 MHz Band III sanity range (via
`toast(..., 'error')`, same pattern used elsewhere for bad frequency
entry), then calls `dabTuneChannel('Manual ' + freq.toFixed(3), freq)` —
identical retune path to clicking a grid button, so hardware retune,
subprocess relaunch, and now-playing state reset all just work. Hidden for
ITU-2 (Americas) the same way the grid itself is, via a small addition to
`dabPopulateChannels()` that toggles the widget's visibility alongside the
existing region check.

Live user report after completing their first macOS bundled build: scan
runs (log confirms `dab_radio_nexus` launches and stays alive on every
channel — checked with `ps aux` mid-scan, not crashing), but finds zero
ensembles anywhere, including channels confirmed working moments earlier
via `python3 w034_NEXUS.py` on the same machine/hardware.

Ruled out: binary discovery (`_dab_find_binary()` correctly resolves
`/usr/local/bin/dab_radio_nexus` in both cases — log shows identical
launch command both times) and a crash (process stays alive, confirmed
via `ps aux`, and no crash report). Also checked that scipy's compiled
`.so` extensions are genuinely present in the built `.app` (`Contents/
Frameworks/scipy`, symlinked from `Contents/Resources/scipy` — standard
PyInstaller layout, not obviously broken).

**Found a real bug either way, whether or not it's the actual root cause
here:** `_dab_feed_iq()` (the function that resamples raw hardware IQ down
to DAB's fixed 2.048 MSPS and writes it to the subprocess's stdin) wraps
its work in a bare `except Exception as e: log.debug(...)` — but
`logging.basicConfig(level=logging.INFO, ...)` means DEBUG-level calls
never reach the log file at all. Any real exception in the resample step
(scipy/numpy issue, bad math, anything) would be swallowed with zero
trace, while the subprocess sits starved of IQ and correctly reports no
ensembles on every channel — indistinguishable from "no signal" without
this being visible. Changed to `log.warning` with the exception type
included. Also added two one-line startup log entries reporting whether
`scipy` and `sounddevice` imported successfully at all — neither failure
was ever logged anywhere before this, despite scipy underlying DAB's IQ
feed, CW/RTTY/AIS filtering, and WSPR decimation.

**Next step:** rebuild (Python-only — `build_macOS.sh`, no C++ rebuild
needed since `dab_radio_nexus.cpp` didn't change) and re-run the same
scan. Check `~/Library/Logs/DARKSKY NEXUS/darksky_nexus.log` for a
`Startup: scipy ...` line and any `DAB IQ feed error: ...` lines — those
two will tell us definitively whether this is the actual cause or whether
the search continues elsewhere (SDRConnect connection during the .app
run, a Full-IQ tap timing difference, or something not yet considered).

---

### Fixed (2026-07-26) — channel text nearly invisible, player column too cramped

Live user report + screenshot: "Channel text is partially obscured. could
we make the player column a bit bigger, and reduce the size of the
station cards?"

**Root cause of the obscured text:** `.dab-ch-miss` (a Band III channel
the scan tested and found nothing on) set its label's text colour to
`var(--border)` — a hairline-outline colour, not a text colour. In the
dark theme `--border` (`#1e2530`) sits almost exactly on top of the panel
background (`#0f1318`), so a "miss" channel's label — 8D in the
screenshot — rendered nearly invisible rather than just de-emphasised.
Switched to `var(--muted)` (tuned per-theme for legible secondary text)
dimmed further with `opacity:.55`, so a miss still reads as clearly
lower-priority without disappearing into the background.

**Player column widened** 230px → 290px, and the **station card grid
densified** to make room for it: min column width 150px → 128px, card
padding/gap and every text size inside a card (name, sid, badges) trimmed
by 1-2px each. Individually small changes, but the combined effect is a
noticeably bigger player column with the same number of stations
comfortably fitting in less width.

Pure CSS — browser reload only, no restart needed.

---

### Added (2026-07-26) — Optional one-click bundling of the DAB engine

User asked: can DAB be bundled so an installed user just clicks DAB and it
works, no separate build/install step? Answer: yes, and this wires up the
software side of it — the actual compiling still has to happen once per
platform, on a real macOS/Windows machine (this sandbox can't do it).

**`_dab_find_binary()` (`w034_NEXUS.py`):** now checks a bundled location
first when running as a packaged app — `sys._MEIPASS` (the same place
`_find_html()` already reads the bundled HTML from: `Contents/MacOS/`
inside the `.app` on macOS, the `_internal/` folder next to the `.exe` on
Windows) — before falling through to today's PATH/Homebrew search. Also
added Windows-specific candidate paths, which DAB never had (every other
decoder with a Windows-aware search — multimon-ng, freedv_rx, wsprd — already
does).

**Both `.spec` files:** `binaries=[]` is now populated conditionally from
`build/bundled/dab_radio_nexus` (macOS) / `build/bundled/dab_radio_nexus.exe`
(Windows) if either exists at build time — falls back to the unmodified
behaviour (nothing bundled, DAB looks itself up at runtime) if not, so
this is fully backward compatible with every existing build.

**`WRITING/NEXUS_dab_radio_build_macOS.md`:** added a new "Bundling for
distribution" section (Step 7) — the built binary's one non-system
dependency (Homebrew's `libfftw3f.dylib`) needs `install_name_tool`-ing to
`@executable_path/...` and re-signing before it's safe to ship on a Mac
that doesn't have Homebrew's fftw installed. Untested against a real
build yet — flagged as such in the doc itself.

**`WRITING/NEXUS_dab_radio_build_windows.md` (new):** DAB-Radio officially
supports Windows (their own CI builds it via vcpkg + MSVC) even though
this project never had a Windows DAB build before. Uses vcpkg's
`x64-windows-static` triplet specifically so the result has zero DLL
dependencies of its own — much simpler to bundle than chasing down
glfw3/portaudio/fftw3 DLLs individually. Also untested end-to-end.

**`build_macOS.sh` / `build_Windows.bat`:** added an informational
"checking for bundled DAB engine" step so the build output tells you
which case you're in, without needing to go check `build/bundled/`
yourself.

**Net effect once both binaries have actually been built once:** an end
user who downloads the installer gets a DAB tab that works immediately —
no separate install, matching what was asked. Until then, behaviour is
unchanged from today (DAB looks for a manually-installed binary at
runtime, per the existing build guide).

---

### Added (2026-07-26) — w034 User Manual / Quick Start / Troubleshooting docs

w034 never had its own docx doc set (only w031/w032/w033 do) — user copied the
w033 set into `docs/word/w033` as a starting point and asked for it updated.
The original JS build pipeline that generated the w033 docx isn't present
anywhere in the project (only the final built files survived), so these were
updated by editing the actual `.docx` XML directly rather than reconstructing
that pipeline — same net result, different route.

**User Manual:** rewrote Section 6.17 (DAB/DAB+) top to bottom — it still
described the old dab-cmdline engine (per-service relaunch, no scan, no
player column). Now covers `dab_radio_nexus` (any IQ source, not just a
direct RSPdx), the Band III scan grid, the dedicated player column, and
live DLS/MOT Slideshow. Added a w034 overview callout (same style as the
existing w031 one) summarizing the engine swap and the two scan/audio bugs
fixed along the way. Fixed the Appendix C credits line, which still
credited dab-cmdline — now credits williamyang98/DAB-Radio instead.

**Troubleshooting:** added a new "DAB / DAB+ Issues (w034 only)" section
with three entries — classic DAB (MP2) silence, the scan
channel-misattribution bug, and the topbar's channel-grid height/selection-
colour polish.

**Quick Start:** added `dab_radio_nexus` to the "Optional external tools"
table — it (and dab-cmdline before it) had never actually been listed
there, alongside fldigi/dumphfdl/dumpvdl2/multimon-ng/DSD+/freedv_rx. Note:
`rtl_433` (added in w033) has the same gap and still isn't listed — not
fixed here since it wasn't part of this ask, flagging for a future pass.

All three also got a long-standing footer bug fixed for free: the footer
said "DARKSKY NEXUS w0.2.3" all the way from w031 through w033 (never
updated after the version-number → codename switch); now reads "w034"
like the header already did.

---

### Changed (2026-07-26) — DAB topbar polish: shorter channel grid, prominent lock, fixed selection color

Live user feedback on the topbar (channel grid / scan ring / ensemble
status row): "a lot of redundant space... could reduce the height",
"the locked ensemble could also be more prominent", and "the ensemble
button when selected remains the same colour."

**1. Shorter channel grid.** The Band III quick-tune grid was capped at
`max-width:296px`, forcing all 32 channels into 4 wrapped rows even
though the rest of the topbar (scan ring, ensemble status, device badge)
left most of the row's width empty. Widened to `620px` (fits ~16
chips/row, so 2 rows instead of 4) and tightened chip padding, row gap,
and topbar padding — cuts the topbar's height roughly in half.

**2. Locked ensemble is now visually prominent.** The ensemble name used
to render at the same 10px/weight-500 as every other label in the
topbar. `dabUpdateEnsemble()` (and `dabClear()`) now toggle a `.locked`
class on the status pill itself, driven by the same "services.length > 0"
condition already used for the lock dot; CSS steps the name up to 13px/
bold/green with a subtle pill background when actually locked, while the
idle "No ensemble locked" state stays exactly as understated as before.

**3. Fixed: selected channel indistinguishable from a merely-"found"
one.** `.dab-qt-btn.active` (the currently-tuned channel) set its own
color/border-color to the orange "selected" accent, but
`.dab-ch-found`/`.dab-ch-miss`/`.dab-ch-testing` each mark color/
border-color `!important` — so once a scan had also flagged that same
channel as found/missed/tested, its scan-result color won and the
"currently selected" state became invisible; a selected-and-found channel
looked identical to every other green "found" channel. Moved `.active`
after the scan-result rules and marked its own properties `!important`
too — equal selector specificity + later source order wins, so the
active chip always shows the orange selected treatment regardless of
what scan state it also carries.

**Browser reload only — no rebuild, no restart.** Pure CSS/HTML/JS in
`DARKSKY_NEXUS_w034.html`; nothing backend-side changed.

---

### Fixed (2026-07-25) — scan still misattributing stale ensemble data to the wrong channel

Follow-up to the generation-counter scan fix directly below this entry:
user reported, with screenshots, that a scan still marked 11D as "found"
using an ensemble ("D1 National", 29 stations) that wasn't actually
transmitting on 11D — then reported the same thing happening on 12C and
12D. The generation counter closes the race where a stale thread keeps
running after its subprocess should have died, but it doesn't fix a
second, separate bug: the `dab_ensemble` broadcast tagged its data with
`state['dab_channel']` read live, *at the moment the message was built* —
not the channel that was actually current when the underlying
`dab_radio_nexus` subprocess was launched. Since `state['dab_channel']`
updates synchronously the instant the scan moves to the next channel, a
still-generation-valid message describing data captured on channel N could
end up broadcast carrying channel N+1's (or later) tag if the scan had
already advanced by the time the message went out — same "found" flag,
same station list, wrong channel.

Fixed in two places: **backend root cause**, `w034_NEXUS.py` —
`dab_engine()` now captures `launch_channel` once, right before calling
`_dab_launch()`, and threads it through to `_dab_stderr_thread_fn()` (new
`channel` parameter) so the `dab_ensemble` broadcast's `channel` field is
always the channel that was live when *that specific subprocess* was
started, never a later live read of shared state. **Frontend
defense-in-depth**, `DARKSKY_NEXUS_w034.html` — `dabScanChannels()` now
records the channel it's currently probing in `_dabScanTargetChannel`
before each tune, and the scan's early-resolve check in
`dabUpdateEnsemble()` now requires `msg.channel === _dabScanTargetChannel`
in addition to `services.length`, so even a mistagged message can no
longer resolve the wrong channel's scan step as a "found."

**Python-only + browser reload — no C++ rebuild needed.** Neither
`dab_radio_nexus.cpp` nor its wire protocol changed; restart
`w034_NEXUS.py` and refresh the tab.

---

### Added (2026-07-25) — dedicated player column with live DLS text + MOT slideshow, and a scan-accuracy fix

Two pieces of work from the same live-testing session, right after the
classic-DAB-silent fix documented just below this entry:

**1. Dedicated player column with live Dynamic Label text and MOT
Slideshow images**, per explicit user request. The now-playing bar moved
off the bottom of the tab into its own fixed-width column alongside the
sidebar and station grid — always visible rather than a collapsed/expanded
overlay, with room for a station logo/album-art image and a scrolling text
ticker. Researched DAB-Radio's real PAD-decode API before touching
anything: `SetIsDecodeData(true)` (previously off) makes the library run
its own `PAD_Processor` internally and hand back *finished* text/images —
`Basic_Audio_Channel::OnDynamicLabel()` for DLS text,
`GetSlideshowManager().OnNewSlideshow()` for a ready-to-decode JPEG/PNG
byte buffer — no PAD/X-PAD/MOT parsing of our own needed. `dab_radio_nexus`
now emits DLS updates as a `dab_dls` stderr JSON line and slideshow images
as a new binary stdout frame type (`"DAB2"`, alongside the existing PCM
`"DAB1"` frames); `w034_NEXUS.py` demuxes both, caches the latest of each
per subchannel (enriching the `dab_ensemble` broadcast the same way
`buffer_bytes`/`sample_rate` already were), and forwards live updates to
the browser (slideshow images base64'd into the WS message — small/
infrequent enough that the ~33% overhead doesn't matter). DLS is
deliberately one freeform scrolling text field, not separate structured
song/artist/headline/weather/traffic fields — that's genuinely all DAB
gives you; what shows up depends entirely on what the broadcaster sends.

**2. Band III scanner missing real ensembles and reporting fake ones** —
user report: "not capturing an ensemble where there is DAB transmission,
and capturing ensembles where there is no DAB transmission." Root cause,
in `w034_NEXUS.py`: every channel change during a scan starts a new
`dab_radio_nexus` subprocess and a new pair of stdout/stderr reader
threads, but neither thread ever checked whether the subprocess it was
reading from was still the *current* one. `_dab_terminate()` reset
`_dab_services` immediately, but the old subprocess doesn't die the
instant SIGTERM is sent — its stderr thread could keep running for a beat
and still deliver one more *genuine* `dab_ensemble` message detected on
the *previous* channel, misattributed to whatever channel the scan had
since moved to (the message carries no channel tag of its own). A channel
that genuinely has DAB could lose its own real result to this and get
marked "miss," while a DAB-less channel next in the scan order could
inherit that stale real result and get marked "found." Fixed with a
monotonic `_dab_generation` counter, bumped on every launch/terminate and
checked by both reader threads before touching shared state or
broadcasting anything. Also removed two sources of pure timing-budget
loss that made the scan's tight ~3.5s per-channel window worse than it
needed to be: `_dab_terminate()` used to block the *entire asyncio event
loop* for up to 3s waiting for the old subprocess to actually exit
(`proc.wait(timeout=3)` called synchronously from the WS handler) — it now
just signals and returns; and `dab_engine()`'s own relaunch-detection poll
dropped from a 2s tick to 0.25s, so a real ensemble gets close to its full
scan window to prove it instead of losing most of it to backend
bookkeeping alone.

**Requires rebuilding `dab_radio_nexus`** (item 1 touches the C++ engine)
and simply restarting `w034_NEXUS.py` (item 2 is Python-only). See
`WRITING/NEXUS_dab_radio_build_macOS.md` for the rebuild steps.

---

### Fixed (2026-07-25) — DAB "no audio" after retuning, and total audio silence introduced by the two fixes above

Two separate bugs, found live in the same session as the tab rebuild and
the two backend fixes below it, both reported simply as "no audio":

**1. Stale now-playing indicator after a channel retune (frontend).**
`dab_set_channel`'s WS handler correctly resets `state['dab_play_sid']` to
`None` on every retune (the old subchannel's decode is meaningless once the
hardware retunes to a different channel) — but `dabTuneChannel()` in
`DARKSKY_NEXUS_w034.html` never mirrored that reset client-side, so the
now-playing bar and the "playing" card glow kept pointing at a `sid` the
backend had already forgotten. Confirmed live: a direct
`fetch('/dab_audio?sid=...')` for the still-"playing" station returned
`503 DAB engine not running or no service selected` while the UI showed
it as happily playing. Fixed by calling `dabStopPlayback()` up front
whenever the channel actually changes.

**2. Total audio silence — zero PCM bytes ever, for every service, DAB
and DAB+ alike (backend, `dab_radio_nexus.cpp`).** Once bug 1 stopped
masking things, `/dab_audio` reliably returned `200`, but with an empty,
never-ending body — confirmed by reading the raw response stream directly
in the browser (bypassing the `<audio>` element, which never surfaces a
"connected but nothing arriving" state clearly). Root cause: this
session's *station-names* fix (below) added a background thread that
polls `BasicRadio::GetDatabaseStatistics().nb_updates` every 750ms and,
on change, re-serializes the whole ensemble — but it did that **while
holding `radio.GetMutex()` for the entire walk** (services × components,
plus string formatting and an `fprintf`). That same session's
*thread-count* fix (also below) had just raised MSC/audio decode from 1
thread to up to 9 (`--radio-total-threads`) — and the pre-existing
`On_Audio_Channel` call site that this new thread copied its
`emit_ensemble_snapshot()` call from had **never** taken that lock itself,
relying instead on already running inside the library's own synchronized
callback context. Adding an explicit, comparatively long-held lock on a
750ms timer, right as up to 9 independent audio-decode worker threads
started needing the same mutex to commit each decoded frame, serialized
— and very plausibly deadlocked — the two fixes against each other:
station names kept updating (FIG parsing apparently doesn't contend the
same lock the same way), while MSC audio decode never produced a single
frame. Fixed by shrinking the lock to just the `nb_updates` compare (a
single `size_t` read) and calling `emit_ensemble_snapshot()` unlocked
afterwards — matching the original call site's convention exactly.

**Requires rebuilding `dab_radio_nexus`** (C++ change) — bug 2 is not
fixable by a browser reload or a Python restart alone. See
`WRITING/NEXUS_dab_radio_build_macOS.md` for the rebuild steps.

---

### Fixed (2026-07-25) — classic DAB (MP2) services silent while DAB+ (AAC) plays fine

User report, live, after the mutex-serialization fix above landed:
every DAB+ service on the multiplex now played correctly, but every
classic DAB (MPEG-1 Layer II) service stayed completely silent — no
error, no crash, `/dab_audio` streamed a valid WAV header and then
nothing.

Researched the actual DAB-Radio library source
(`williamyang98/DAB-Radio`) rather than guessing: `attach_audio_channels()`
in `dab_radio_nexus.cpp` calls `controls.SetIsDecodeAudio(true)` and
`controls.SetIsPlayAudio(false)` on every discovered channel (the `false`
was written assuming "play audio" meant *local hardware* playback, which
NEXUS never wants since it's the audio sink itself). It turns out that
flag means something different depending on the channel type:
`Basic_DAB_Plus_Channel` (DAB+/AAC) emits its decoded PCM to our
`OnAudioData` callback whenever `GetIsDecodeAudio()` is true — so DAB+
worked regardless of `SetIsPlayAudio()`. `Basic_DAB_Channel` (classic
DAB/MP2) decodes every frame either way, but only calls the same emit
path when `GetIsPlayAudio()` is true — with it left `false`, MP2 frames
were decoded and then silently thrown away, never reaching our stdout
writer at all. Fixed by setting `SetIsPlayAudio(true)` too — harmless for
DAB+ channels (they ignore it), required for MP2 channels to emit
anything.

**Requires rebuilding `dab_radio_nexus`** again — same rebuild steps as
above.

---

### Rebuilt (2026-07-25) — DAB Decoder tab, full spec revision

Full rebuild of the DAB tab per a detailed spec: top bar (Band III
quick-tune + a real circular scan-progress ring + ensemble/lock status +
device label + a diagnostics gear), a favourites row (tap to play, long
-press to remove, persisted in `localStorage`), an ensemble-grouped
station grid (the currently-tuned multiplex renders full cards; any other
ensembles found earlier this session collapse to a click-to-retune
summary row instead of showing fabricated "still there?" station tiles
for a channel we're not tuned to and can't verify), a bottom-pinned
now-playing bar with collapsed/expanded states (mini equalizer, elapsed
-time ticker, stereo/mono + DAB/DAB+ badges, and a hidden "Technical
Details" drawer), and a scan-manager sidebar (progress bar + a real
per-session list of ensembles found, click to retune).

Two decisions made explicitly with the user before starting: (1) palette
reuses NEXUS's existing `--bg`/`--panel`/`--accent`/`--orange` etc.
variables rather than the spec's own `#0C0C1A`/`#6A4BFF` scheme, so the
tab inherits dark/light theming for free and stays visually consistent
with the rest of the app instead of standing apart; (2) the spec's
`<dab-topbar>`/`<dab-favourites>`/etc. module names are plain `<div>`
sections using those names as id/class hooks, not real Web Components —
nothing else in this 25,000+ line file uses shadow DOM, and introducing
it for one tab would fight the existing CSS-variable cascade instead of
using it.

Backend addition to make the "Technical Details" drawer honest rather
than empty: `w034_NEXUS.py`'s `dab_ensemble` broadcast now enriches each
service with `sample_rate`/`stereo`/`bits_per_sample`/`buffer_bytes` (read
from `_dab_audio`, already populated per-frame by `_dab_store_audio()`)
plus a top-level `buffer_max_bytes`, once that service's first PCM frame
has actually decoded — fields stay absent until then rather than being
guessed. Codec mode (HE-AAC vs MPEG-1 Layer II) is shown as a fact of the
DAB+/DAB standard itself rather than a per-stream measurement, which is
accurate rather than assumed.

All "real data or nothing" conventions from the rest of this session's DAB
work carried forward unchanged: the background per-channel scanner, the
real Web Audio-driven equalizer, the ITU-region gate, and the shared-SNR
signal reading (DAB has no meaningful per-service SNR).

---

### Fixed (2026-07-25) — DAB station names blank for most services on a full multiplex

User report, live (BBC-format ensemble, 31 services after a scan): only 6
of 31 stations ever showed a real name — the rest stayed on the "—"
placeholder permanently, even though the ensemble had clearly locked and
audio played fine for the ones with names.

Root cause, in `dab_radio_nexus.cpp`: `emit_ensemble_snapshot()` (which
serializes the current service list, including each service's `.label`,
to stderr JSON) was only ever called from inside
`On_Audio_Channel().Attach(...)`'s callback — a signal that fires once per
newly-*discovered* subchannel (FIG 0/2 linking a service to a subchannel)
and then goes quiet once every subchannel in the ensemble has been found,
typically within the first couple of seconds. A station's actual name
comes from a *different* FIG (1/0, "service label") that cycles on its own
schedule, independently of and often much slower than FIG 0/2 — on a
30+-service multiplex, covering every service's label in the FIG 1/0
rotation can take a good deal longer than "every subchannel discovered".
So most labels finished decoding well after the last snapshot had already
gone out, and — because nothing else ever triggered another snapshot —
were simply never sent to the frontend at all, forever, even though
`BasicRadio` had them internally the whole time.

Fix: added a small background thread that polls
`BasicRadio::GetDatabaseStatistics().nb_updates` (a monotonic counter the
library already increments on every accepted FIG write, including label
writes) roughly twice a second, and only re-runs `emit_ensemble_snapshot()`
when that counter has actually moved since the last check — so newly
-arrived labels get pushed out promptly without blind-resending the whole
list on a fixed timer when nothing changed. Reads `GetDatabase()` under
`GetMutex()` since FIC processing runs on its own thread and the database
isn't otherwise synchronized.

**Requires rebuilding `dab_radio_nexus`** (this is a source change to the
C++ tool itself, not the Python bridge) — see
`NEXUS_dab_radio_build_macOS.md` for the build steps.

---

### Fixed (2026-07-25) — DAB audio never plays: MSC decode starved to a single thread

User report, live on real hardware (RSPdx via USB, SDRConnect Full IQ @
2 MSPS): channel scan works fine, ensemble locks, all 15 real BBC National
DAB 12B services show up — but clicking any station produces no audio at
all, no error, nothing.

Confirmed live by hitting the stream endpoint directly
(`GET /dab_audio?sid=C336`) from the browser console: it returns
`200 audio/wav` with correct headers, and then... nothing. Zero PCM bytes,
no timeout, no disconnect — the connection just sits open forever.

Root cause: `_dab_launch()` in `w034_NEXUS.py` never passed
`--radio-total-threads` to `dab_radio_nexus`, so `Basic_Radio_Block`
defaulted to a single thread. `attach_audio_channels()` in
`dab_radio_nexus.cpp` deliberately decodes **every** discovered audio
subchannel simultaneously (no per-service enable/disable control channel —
see the w034 DAB engine entry below for why), which is fine for FIC (the
small, cheap, ensemble-wide scan that produces the service list) but is a
real load-bearing decision for MSC: Reed-Solomon + AAC/MP2 decoding a
dozen-plus full audio services at once on one thread can't keep up with
2.048 MSPS in real time. FIC kept locking and reporting services correctly
(giving every appearance the engine was fully working), while MSC decode
permanently fell behind and never finished a single superframe for any
subchannel — so `_dab_store_audio()` was never called, `_dab_audio` stayed
empty forever, and `_serve_dab_audio()`'s `entry is None: time.sleep(0.1);
continue` loop spun silently with the connection open and zero bytes
written, matching the live repro exactly.

Fix: `_dab_launch()` now passes `--radio-total-threads` sized to
`max(2, cpu_count - 1)`, giving MSC decode real parallelism across
services. OFDM demod itself stays single-threaded (`--ofdm-total-threads`
untouched) since it's comparatively cheap and single-threaded was never
the bottleneck.

**Requires restarting `w034_NEXUS.py`** — this is a subprocess launch
argument, not something a browser reload picks up.

---

### Added (2026-07-25) — location-aware DAB channel gating + real background scan

Follow-up to "would it be possible to only show channels available in the
user's area — and does the current setup even work for the US?" Checked
rather than assumed on the US question: the US never adopted Eureka-147
DAB (this decoder's actual standard) — it picked HD Radio/IBOC in 2002,
a fundamentally different in-band-on-channel technology this decoder
can't read, and Canada wound its own experimental L-band DAB network down
starting 2010. So the entire Band III channel grid is dead air anywhere
in North or South America regardless of which channels are shown.

Two pieces, deliberately different in approach:

1. **ITU-region gate** (coarse, free). Reuses `_bpRegion`, a global
   already geo-detected on page load via `navigator.geolocation` for the
   band-plan strip's own ITU-1/2/3 coloring (`_bpAutoDetect()`) — no new
   location code needed. `dabPopulateChannels()` now checks it: if
   `ITU-2` (the Americas), the whole channel grid is replaced with a
   plain explanation instead of 32 buttons that will never do anything.
   Hooked `_bpSetRegion()` to force-refresh the DAB tab too, since
   geolocation resolves asynchronously and can land after the tab was
   already opened (defaults to ITU-1 until then).
2. **Real background scan** (fine-grained, self-updating). Rather than
   shipping a static per-country/per-region DAB channel-plan database —
   which goes stale the moment a multiplex is added, dropped, or
   relicensed, and would make an active claim about the local airwaves
   that could just be wrong — `dabScanChannels()` does a real sweep:
   retunes through every Band III channel in turn (reusing the existing
   `dabTuneChannel()`/`dab_set_channel` path, no backend changes needed),
   waits up to 3.5s for a real `dab_ensemble` broadcast with actual
   services, and only highlights the channels that genuinely answered
   (green = found, dim = checked and empty, amber pulse = currently
   testing). `dabUpdateEnsemble()` resolves the wait early the moment a
   real ensemble lock arrives rather than always burning the full
   timeout. Works identically in any country with zero geo/database
   lookup for this part — it's reporting what's actually in the air
   right now, not what a list says should be there.

Also fixed a real bug found while in this code: the `case 'dab_clear':`
WS-message handler set `dab-svc-rows.innerHTML = ''` directly, which
stomped the friendly `DAB_EMPTY_HTML` empty state `dabClear()` had just
set locally the instant the backend's rebroadcast of the same clear
command echoed back to the sender — the nice empty state would flash for
an instant then go blank. Now reuses the same constant.

---

### Redesigned (2026-07-25) — DAB tab rebuilt for a non-technical audience

Follow-up to the card-grid pass earlier the same day: asked directly "if
you had free reign, how would you lay this out for maximum visual impact,
aimed at a non-tech user." Rebuilt the tab around that brief rather than
just polishing the existing engineering-console layout:

- **Now-playing hero.** Station name in large type, a circular monogram
  avatar whose gradient color is deterministically hashed from the station
  name (`_dabColorFromName`/`_dabHash`) so a given station is always the
  same color, and a real 20-bar audio-reactive equalizer — a Web Audio
  `AnalyserNode` tapped directly off the actual `#dab-audio` element via
  `createMediaElementSource` (same lazy-AudioContext-on-first-gesture
  pattern already used by `_freedvEnsureContext()`/`audioContext_ft8`
  elsewhere in this file), not a decorative canned animation. Bars settle
  flat automatically whenever nothing is playing, no extra state needed.
- **One honest signal reading, not a fabricated one.** DAB doesn't have a
  meaningful *per-service* SNR — every station in an ensemble rides the
  same RF channel — so rather than inventing a different number per card,
  the hero's 4-bar signal indicator reuses the same link SNR already
  shown in the main toolbar (`DS.vfos.a.snr`), bucketed into 4 tiers.
- **Jargon moved, not deleted.** The old always-visible engineering bullet
  list (dab_radio_nexus, Full-IQ tap, 2.048 MSPS, FIC/MSC) is now behind a
  "How this works ▾" expander, collapsed by default. What a first-time
  user sees instead: "Free digital radio, out of thin air" + one line
  about tapping Start — the technical detail is still there for anyone
  curious, just not shoved in front of everyone by default.
- **Friendlier empty/scanning states.** Replaced the plain "Start decoder
  — requires dab_radio_nexus, Full IQ stream" text with a broadcast-wave
  icon + "No stations yet" / "Tap Start above..." copy, and a separate
  pulsing variant ("Searching the airwaves…") for the actual scanning
  state instead of static "Scanning ensemble…" text.
- Renamed "SERVICE" → "STATIONS" in the list header and "click a card to
  play" → "tap a station to play" — small wording choices, same idea of
  addressing a listener, not an engineer.

Nothing about the underlying dab_radio_nexus/Full-IQ pipeline changed —
this is presentation only, built on the same `dab_play_service`/
`dab_stop_service` commands and `dab_ensemble` broadcasts as before.

---

### Fixed + Redesigned (2026-07-25) — DAB player never appeared; service list is now a card grid

Two more things found live-testing the working DAB ensemble lock (BBC National
DAB, 12B, 8 services):

1. **The player panel never appeared, no matter what was clicked.**
   `dabPlayService()` set `wrap.style.display = ''` on click, which clears
   the *inline* style but doesn't remove a matching external rule —
   `#dab-player-wrap{...display:none}` in the stylesheet (a leftover from
   an earlier iteration of this panel) still applied, so the panel stayed
   hidden regardless of clicking a service. No error anywhere; it just
   silently never showed. Fixed by setting an explicit `'flex'` instead of
   `''`, which wins over the external rule.

2. **Redesigned the service list from a scrollable row list into a card
   grid**, per direct request. New `.dab-svc-grid`/`.dab-svc-card` classes
   follow the same `repeat(auto-fill,minmax(...))` convention already used
   by `.dec-params`/`.sig-grid` elsewhere in this file, so cards reflow
   into however many columns fit the panel width. Each card shows the
   station name, SID, a DAB/DAB+ type badge, and a play/now-playing
   indicator (filled square + amber border + a small pulsing dot,
   matching the existing amber DAB accent color rather than introducing a
   new one). Removed the now-unused old `.dab-svc-row`/`.dab-service-list`
   CSS (leftovers from a prior iteration that predated the current
   `dab-svc-rows` markup and were no longer referenced anywhere).
   Restyled the player panel itself to match — a "NOW PLAYING" eyebrow +
   pulsing dot + station name row above the native `<audio>` control,
   instead of a bare label.

---

### Fixed (2026-07-25) — IQ-enable guard still stale on mode revisit; HTML still said w033

Two bugs found during live Full IQ @ 2 MSPS DAB testing:

1. **`_iq_enabled_modes` guard was a set, not a "last mode" tracker.** The
   July 24 fix (see below) correctly re-fires the enable handshake
   (`set_primary_device_enable`/`device_stream_enable`/`iq_stream_enable`)
   once per distinct mode name, but a `set` remembers every mode ever seen
   for the life of the connection — so re-entering a mode already visited
   earlier in the same session (Full IQ -> IQ Lite -> back to Full IQ) never
   refired it. Confirmed live: a 20+ second window showed the type-2 tally
   frozen at a fixed count while type-1/type-3 kept climbing normally —
   SDRConnect's own stream-enable state doesn't persist across a mode
   switch on its end, so a stale "already enabled" guard silently starved
   real IQ frames with no error anywhere. Replaced the set with a single
   `_iq_last_enabled_mode = [None]` tracker: fires on every actual mode
   transition, including revisits, and still only once per transition.

2. **`DARKSKY_NEXUS_w034.html` still said "w033" everywhere it matters.**
   The w033->w034 fork (2026-07-24) never got a version-identity pass (the
   w031->w032 and w032->w033 forks both had one as a dedicated step; this
   one was missed). `<title>`, both `w033` version badges (connection-setup
   dialog and the main `#brand-version` brand-bar badge), and — the one with
   real live impact — the JS version-mismatch check, were all still
   hardcoded to `'w033'` while the Python backend already correctly sends
   `VERSION = "w034"` as `server_version`. Net effect: every single page
   load fired a spurious "Version mismatch: bridge is w034 but HTML is
   w033 — Cmd+Shift+R to reload" warning, even on a perfectly matched
   w034/w034 pair. Fixed the title, both badges, and the mismatch check
   (now compares against `'w034'`), plus three internal comments that
   cross-reference "w033_NEXUS.py" as a file path (now w034_NEXUS.py) since
   that file doesn't exist in this folder. Left ~34 genuinely historical,
   dated comments alone (e.g. "SSTV (w033 fork, 2026-07-19)", "added
   w033") — those are accurate feature-origin/bugfix history, not identity
   strings, and should stay as-is per the same convention used throughout
   this file's own "PRIOR VERSION" sections.

---

### Added (2026-07-24) — SSTV Robot 36/72 decode (previously detected-only)

Follow-up to a self-audit ("is there anything in w033 that needs attention?")
that turned up one real, still-open gap: the SSTV decoder (added 2026-07-19)
fully decodes Martin M1/M2 and Scottie S1/S2/DX but only *recognised* Robot 36
and Robot 72 — VIS header detected, mode name shown, a toast fired ("detected
but decoding that mode isn't implemented yet") — because their YCbCr format
with alternating/subsampled chroma was judged too easy to get subtly wrong
without a real signal to check against.

Implemented both properly using the numeric scan-line timing table (Table
4.3) in Martin Bruchanov OK2MNM's public SSTV Handbook (sstv-handbook.com) —
the same source already cited for the existing Martin/Scottie constants.
Robot 36 is YCbCr 4:2:0: one chroma channel (Cr or Cb) per line, alternating
by line parity; the channel not present on a given line is held over from
whichever line last supplied it (`_last_cr`/`_last_cb` on `SstvDecoder`,
reset to neutral 128 on a fresh tune) — the standard way every real Robot 36
decoder handles the format's vertical chroma subsampling. Robot 72 is YCbCr
4:2:2: both Cr and Cb sent every line, no alternation, no hold-over needed.
Added a new `_decode_line_robot()` method (separate from the existing
`_decode_line()`, which assumes direct RGB channel tags and doesn't apply
here) doing the YCbCr→RGB conversion; `_compute_line_layout()` gained
`robot420`/`robot422` branches building the segment lists from each mode's
published sync/Y/chroma durations.

Verified two ways before shipping: (1) each mode's line-segment durations
were summed and checked against its published lines-per-minute figure —
Robot 36's 10.5+90+4.5+45ms sums to exactly 150ms at 400lpm, Robot 72's
12+138+6+69+6+69ms sums to exactly 300ms at 200lpm; (2) the YCbCr→RGB
formula was round-tripped numerically against several test RGB triples
(pure red/green/blue/white/black plus two arbitrary colours) and reconstructed
each within <1/255 (clipping-only) error.

**Caveat, unchanged from the original SSTV work**: like Martin/Scottie before
it, this has not been checked against a real captured Robot 36/72
transmission — only against the published spec and the round-trip math
above. The even/odd Cr/Cb parity convention (even line = Cr, odd = Cb) is
the standard one, but if colours come out swapped on real traffic, that
parity assumption in `_decode_line_robot()` is the first thing to flip.

Frontend: updated the SSTV panel's Start button tooltip and status-bar note,
which both still said Robot 36/72 were detected-only.

---

## w034

w034 is forked directly from w033 (2026-07-24), specifically to replace the
DAB/DAB+ engine's underlying decoder. Nothing in w033 was touched — it
remains a separate, stable release using dab-cmdline, per an explicit
decision to keep it as a fallback while this fork's DAB work was in
progress.

**Why**: w033's DAB engine (`dab-cmdline`'s `example-3` binary) opens the
SDRplay API directly and grabs the RSPdx itself, which only works if the
device is physically USB-attached to the same machine NEXUS runs on. It
cannot read from SDRConnect's own network protocols, and cannot see a
networked nRSP-ST at all — confirmed against SDRplay's own API
documentation, which doesn't enumerate network-only devices. This surfaced
while debugging a `dyld` rpath error on macOS building dab-cmdline, and led
to evaluating three alternative DAB backends: welle.io (GPL-2, unmaintained
on macOS/Apple Silicon per its own README), DABlin (GPL-3, but does no
OFDM/FIC/Reed-Solomon at all — needs an external demodulator upstream, so
it can't replace dab-cmdline standalone), and DAB-Radio (MIT,
williamyang98) — chosen because its library API cleanly exposes a
per-subchannel PCM callback independent of its GUI/PortAudio code, and its
own examples already demonstrate raw-IQ-over-stdin piping as a first-class
pattern.

**New engine — `dab_radio_nexus`**: a new headless C++ tool
(`examples/dab_radio_nexus.cpp`, ~300 lines) added to a clone of
DAB-Radio, registered as a new CMake target via a small patch to
`examples/CMakeLists.txt`. It owns no hardware at all:
- **stdin**: interleaved 32-bit float IQ (`raw_f32l`), fed continuously by
  NEXUS.
- **stdout**: every discovered audio subchannel decodes simultaneously
  (same "decode all, serve on demand" trade-off as welle-cli's own `-Dw`
  flag) and is written as a small self-describing frame (`DAB1` magic +
  subchannel id + sample rate + channel count + bit depth + payload) so
  multiple subchannels share one stdout stream.
- **stderr**: one JSON line per ensemble/service discovery
  (`{"type":"dab_ensemble", ...}`) and a status line at startup/exit
  (`{"type":"dab_status", ...}`) — deliberately matching the JSON shape
  NEXUS's frontend already expected, so the UI needed almost no changes.

Built by subscribing to `Basic_Audio_Channel::OnAudioData()` (a public
callback independent of DAB-Radio's PortAudio/GUI code, found by reading
`src/basic_scraper/basic_scraper.cpp`'s existing usage as a template) —
DAB-Radio's own shipped CLI example (`basic_radio_app_cli`) excludes the
entire audio-output path behind a `#if`, so this had to be written fresh
rather than reused.

**Verification**: syntax-validated with `g++ -fsyntax-only` against the
real upstream headers (two genuine bugs found and fixed: missing logging
macro defines, missing `#include <fmt/ranges.h>` for `fmt::join`) — zero
errors after. A real `libfftw3f` shared object (extracted from the
`pyFFTW` manylinux wheel, matching architecture) was linked and its 541
`fftwf_*` symbols confirmed present, validating the one genuine precision-
sensitive external dependency. A full CMake configure+build+run test could
not be completed in the sandbox this was built in: DAB-Radio's root
`CMakeLists.txt` unconditionally requires GLFW3 and OpenGL (for its GUI
targets, even when building only this headless target), and CMake refuses
to disable `REQUIRED` `find_package()` calls — installing real GLFW3/
OpenGL dev packages needs `apt`/root, unavailable there. This final
build+run verification needs to happen on a real macOS machine via
Homebrew (see `NEXUS_dab_radio_build_macOS.md`).

**Real-build fix (2026-07-24, found during Jon's actual macOS build)**: the
`target_link_libraries` in the CMakeLists.txt patch above originally
omitted `basic_scraper`, since `dab_radio_nexus` doesn't use any scraper
functionality. That broke the build with `use of undeclared identifier
'BASIC_SCRAPER_LOGGER'` — `examples/app_helpers/app_logging.h`'s shared
`setup_easylogging()` helper unconditionally references that constant, but
it's only declared once something links `basic_scraper` (its own
`CMakeLists.txt` exposes the enabling macro as a `PUBLIC` compile
definition, propagated only to linked targets — not a global setting).
This is exactly the class of bug the sandbox's syntax-only check couldn't
catch (it's a link-graph propagation issue, not a syntax error) and is
also why `basic_radio_app_cli` links `basic_scraper` despite not scraping
anything either. Fixed by adding `basic_scraper` to `dab_radio_nexus`'s
link list — both `NEXUS_dab_radio_build_macOS.md` and this repo's
`CMakeLists.txt` patch instructions now include it correctly.

**Real-build fix #2 (2026-07-24, same build)**: after the fix above,
compiling succeeded but linking failed with `Undefined symbols ...
el::base::elStorage`, referenced from `dab_radio_nexus.cpp.o`.
easyloggingpp requires the `INITIALIZE_EASYLOGGINGPP` macro invoked exactly
once, in exactly one translation unit of the final binary, to instantiate
its global storage object -- `dab_radio_nexus.cpp` never included it.
`basic_radio_app.cpp` and `radio_app.cpp` both place this macro on its own
line directly before their own `main()`; `dab_radio_nexus.cpp` now does the
same. Also a link-only bug the sandbox's `-fsyntax-only` check couldn't
have caught. Both `dab_radio_nexus.cpp` and
`NEXUS_dab_radio_build_macOS.md` are updated.

**Python side (`w034_NEXUS.py`)**: replaced the entire dab-cmdline engine
(`_dab_find_binary`, `_dab_launch`, `dab_engine`, `_dab_parse_line`,
`_dab_reader_thread`, `_serve_dab_audio`, `_wav_header` usage) with:
- `_dab_feed_iq()` — resamples NEXUS's raw, undecimated Full-IQ tap (the
  same tap point `_rec_write_iq()` already used for IQ recording) down to
  DAB's fixed 2.048 MSPS OFDM rate via `scipy.signal.resample_poly`, with a
  short carried-sample history across packets to smooth the polyphase
  FIR's transient at packet boundaries, and writes it to the subprocess's
  stdin.
- `_dab_stdout_thread_fn()` / `_dab_store_audio()` — demux the framed
  stdout stream into one PCM buffer per subchannel, capped at ~2MB each so
  an unwatched service can't grow unbounded.
- `_dab_stderr_thread_fn()` — parses the JSON status lines and rebroadcasts
  `dab_ensemble`/`dab_status` exactly as before.
- `_serve_dab_audio()` — rewritten to stream whichever subchannel
  `dab_play_sid` currently selects, with a WAV header built from that
  service's REAL sample rate/channel count/bit depth (previously hardcoded
  48000/2/16 for every service).
- `dab_set_channel` WS handler — a channel change now needs the actual
  SDRConnect hardware to retune (dab_radio_nexus has no hardware access of
  its own, unlike dab-cmdline); confirmed the frontend's existing
  `dabTuneChannel()` already sends a normal `tune` command before
  `dab_set_channel`, so no new retune code was needed there — only the
  forced-relaunch bookkeeping.
- Service switching (`dab_play_service`) no longer relaunches the
  subprocess at all — every service already has a live buffer, so it's a
  pure Python-side selection change.

**Frontend**: removed the 3-second relaunch delay before pointing `<audio>`
at `/dab_audio` (no longer needed — playback starts instantly now),
replaced the now-nonexistent `bitrate` column with a DAB/DAB+ type badge
(`is_dab_plus`), and rewrote the DAB tab's stale left-sidebar description
and button tooltips/labels that still referenced dab-cmdline/example-3.

**Docs**: added `NEXUS_dab_radio_build_macOS.md` (clone + patch + build
steps for `dab_radio_nexus`) and a pointer note in the existing
`NEXUS_decoder_build_macOS.md` (Part 4, dab-cmdline) directing w034 users
to the new document; Part 4 itself is left unchanged as w033's own
documentation.

**Live-test fix (2026-07-24, found testing the built binary end to end in
NEXUS against a real nRSP-ST)**: `dab_radio_nexus` built and ran, but never
received any real IQ -- the backend log showed only spectrum (t==1) and
audio (t==3) frames the entire session, never a single raw-IQ (t==2) frame,
even minutes after switching the device to Full IQ mode. Root cause predates
this fork entirely and isn't specific to DAB: NEXUS's SDRConnect enable
handshake (`set_primary_device_enable` / `device_stream_enable` /
`iq_stream_enable`) was gated by a one-shot-per-connection flag
(`_iq_bounce_done`). SDRConnect exposes IQ Lite/Compact/Full IQ as separate
selectable device entries (confirmed via the `SDRConnect available devices`
log line listing all three plus `IQ File`), each needing its own enable
sequence -- but the flag fired once, against whichever mode was active at
connect time (nRSP-ST defaults to IQ Lite, which never sends real IQ frames
by design per this code's own earlier comments), and never fired again when
the session later switched to Full IQ (e.g. via `dabTuneChannel()`'s
1536000 Hz tune triggering `set_stream_mode`). Fixed by tracking enabled
modes as a set (`_iq_enabled_modes`) instead of a single boolean, so the
handshake re-fires once per distinct mode actually selected during a
connection, not just once ever. This is a real, general Full-IQ bug --
would have silently blocked any Full-IQ-dependent feature (DAB, HFDL,
VDL2, AIS, ...) in a session that starts in IQ Lite/Compact and switches
later, not just DAB. Also added server-side `log.warning()` logging for
`dab_status` error messages (e.g. "stdin IQ stream ended"), previously only
reaching connected browsers as an easy-to-miss toast.

**Live-test fix #2 (2026-07-24, same investigation)**: even with the
per-mode handshake fix above, the enable sequence never actually re-fired
for Full IQ, because the code that fires it lives entirely inside the
`active_device` property handler, which only runs reactively when
SDRConnect itself pushes a `property_changed`/`get_property_response` for
that property. `set_stream_mode`'s WS command handler sent
`selected_device_name` and then optimistically set `state['stream_mode']`
locally, broadcasting a `stream_mode_changed` message to the browser UI --
but never actually confirmed with SDRConnect that the switch happened, and
never requested that confirmation either. Confirmed live: switching IQ
Lite -> Full IQ produced zero further `Device: ...` log lines, meaning the
`active_device` handler (and the IQ-enable handshake nested inside it)
never ran again for the new mode -- the UI showed "Full IQ" as active while
SDRConnect may never have actually completed the switch, or NEXUS was
simply never told either way. Fixed per the official WebSocket API's
documented `get_property`/`get_property_response` round-trip: after sending
`selected_device_name`, `set_stream_mode` now explicitly requests
`active_device` again (0.5s settle delay) instead of assuming success,
guaranteeing the confirmation -- and the enable handshake it triggers --
actually happens. Verified the official spec (fetched directly from
sdrplay.com/docs/SDRconnect_WebSocket_API.pdf, v1.0.3) before writing this
fix, after a pasted third-party summary claimed two API fields
(`vrx_index`, `iq_stream_sample_rate`) that turned out not to exist
anywhere in the real spec -- neither is real, and no code was written
against them.

---

### Improved (2026-07-22) — FT8 INTERNAL toolbar: spread controls out to fill the row

User-reported (with screenshot): every control in the FT8 toolbar was bunched
at the left edge, leaving a large dead gap before the timer/status cluster on
the right — same story one row down for the band quick-tune chips, and again
for the Decodes/Callsigns/Countries stat badges. No new elements added (that
direction was offered and declined in favor of just spreading out what's
already there): the control row's single flex-spacer became two (row gap
6px→10px), the monitor volume slider widened 60px→110px, the band chips'
gap/padding both increased (3px→8px gap, 1px 6px→4px 14px padding), and the
three stat badges now use flex:1 + centered text to stretch across the row
instead of hugging the left.

---

### Added (2026-07-22) — "Populate Log" button inside the FT8 INTERNAL panel

Previously the only way to import a session's FT8 decodes into the
Reporting/Logbook tab was `populateLogbookFromFT8()`, wired to a button that
only existed inside the Reporting tab — meaning logging your decodes meant
switching away from the FT8 panel first. Added a second button directly in
the FT8 toolbar (next to Clear) that calls the exact same
`populateLogbookFromFT8()` function — no logic duplicated, both buttons
trigger identical dedup/import behavior and toast feedback.

---

### Fixed (2026-07-22) — FT8 INTERNAL "Hop" button did nothing

`openHopModal()` was declared twice at the same top-level scope: once near
the ft8ts banner comment (correctly calling `_ensureHopModal()` to build the
modal's DOM, then `renderHopModal()`), and again later near
`loadHopConfig()`/`toggleHopping()` (missing the `_ensureHopModal()` call).
JS silently lets a later function declaration override an earlier same-named
one in the same scope, so the second, broken definition was always the one
actually bound to `openHopModal` and invoked by `ft8HopBtn`'s `onclick`.
Since it never created `#hopModal`, `document.getElementById('hopModal')`
returned `null` and the assignment to `.style.display` threw immediately —
silently, since it's an inline `onclick` handler — before the modal could
ever appear. Same failure mode as the earlier `openStationMapModal` bug
(see that fix's own comment further down in this file).

Fixed by adding the missing `_ensureHopModal()` call to the surviving
(active) `openHopModal()`, and removing the dead, shadowed duplicate
entirely so this can't silently recur. Verified `closeHopModal`,
`renderHopModal`, `toggleHopping`, `addHopRow`, `resetHopStats`, `advanceHop`
each now have exactly one definition in the file.

---

### Improved (2026-07-21) — Multimon-NG Quick Tune: 2-column grid + live per-mode dimming

Follow-up to the Marine channel-grid fix, applied to Multimon-NG's Quick Tune
list at the user's request. Also answered a question raised alongside it:
Quick Tune entries are NOT filtered by which demodulator checkboxes are
ticked — it's a fixed set of 11 buttons (POCSAG×3, APRS×3, FLEX×3, NOAA
WX×2), deliberately limited to modes with one universal, well-known
frequency (DTMF/ZVEI/EEA/EIA/CCIR/FSK9600/MORSE were excluded from Quick
Tune from the start, since those selcall/data modes have no single
canonical frequency).

Converted the list from a single-column stack of full-width buttons to a
2-column grid (matching Marine's tile style: frequency on top, description
below, ellipsis+title for anything too long) and added the filtering the
user asked for — as a live visual hint rather than a hard gate. Each tile
now carries `data-mmon-modes` (the `.mmon-mode` checkbox value(s) it's
relevant to; the three POCSAG baud-rate checkboxes all count as "relevant"
for any POCSAG tile since the quick-tune frequency doesn't depend on baud
rate). `_mmonUpdateQuickTuneHighlight()` dims a tile to 40% opacity when
none of its modes are currently checked, full opacity when at least one is,
and runs on page load plus on every `.mmon-mode` checkbox's `onchange`
(wired individually — Multimon doesn't have a single "modes changed" event,
Apply only fires on the button click). Clicking a dimmed tile still tunes
normally — this doesn't gate the action, since tuning first and enabling
the demodulator + Apply afterward is a reasonable order to do things in.

Caught and fixed a bug in my own first pass at this: the initial rewrite of
the Quick Tune block accidentally dropped both the section's outer wrapper
div and its "QUICK TUNE" label entirely (only the button grid content
survived), which both broke the visible label and left the file with an
unbalanced `<div>`/`</div>` count for the whole panel. Found via the
per-panel div-balance check (opens≠closes within `tab-multimon`'s exact
span), traced to the missing wrapper, and restored it around the grid.

---

### Improved (2026-07-21) — Marine/VHF channel list: button grid, sorted by frequency

User-reported layout issue, with a screenshot: the CHANNELS column (220px
wide) rendered all 16 channels as a category-grouped, full-width stacked
list, so the last several channels (Port Operations onward) needed a
vertical scroll to reach, while the right-hand "Now Tuned" column sat mostly
empty. Rewrote `_populateMarineChannels()` to render a 2-column button grid
instead — narrowed the column to 170px (freeing width for the still-empty
right side isn't the fix here, but the narrower list column is now
proportionate to a grid rather than a full-width list) and switched the sort
from category grouping to straight frequency order, per the user's own
suggestion. Each tile now shows just the channel number and frequency
(previously a two-line row with the full purpose text visible) — the full
"Ch NN — freq MHz — purpose (category)" text moved into the tile's `title`
tooltip so nothing was actually lost, just made click-to-reveal instead of
always-on. All 16 channels now fit in the column with no scrolling.
`MARINE_CHANNELS` itself is untouched (still declared in its original
category order with the `cat` field intact for the tooltip) — sorting
happens at render time via an index array, so `_marineTune(idx)` still
indexes straight into the unsorted source array with no other call site
needing to change.

**Follow-up (same day):** the first pass above dropped the purpose text down
to the tooltip-only, which turned out to lose more than intended — user
asked for the description back. Widened the column 170px→240px (still a
2-column grid, still sorted by frequency, still no scrolling) and gave each
tile a third line for the description, truncated with `overflow:hidden;
text-overflow:ellipsis;white-space:nowrap` per the app's established
truncation convention — the tile's own `title` tooltip still carries the
full untruncated text for anything long enough to get cut off (e.g. Ch
22A's "Coast Guard Liaison / Safety Info").

---

### Changed (2026-07-21) — App-wide font swap: Share Tech Mono → Radio Canada

Followed up on the earlier "does Radio Canada actually show up anywhere"
question. It didn't — the `--ui` custom property existed but had exactly one
call site (the `html,body` fallback), while `--mono` (Share Tech Mono) was
still driving all 1112 other font-family declarations across the app:
buttons, tabs, badges, labels, tables, logs, and every data readout. Explored
splitting the two — UI chrome to Radio Canada, genuinely data-like content
(frequencies, callsigns, decode logs) staying monospace — but the app's
retro-terminal look comes from Share Tech Mono being used *everywhere*
uniformly, and 256 CSS rules plus 846 scattered inline `style=` attributes
mix both categories in ways that don't split mechanically. Asked and the
answer was simpler than a split: replace Share Tech Mono outright, app-wide,
no split.

Implementation was a single-point change rather than 1112 edits: `--mono`'s
*value* was redefined from `'Share Tech Mono',monospace` to `'Radio
Canada',sans-serif` (the variable name stayed `--mono` — renaming it would've
meant touching every one of those 1112 call sites for no functional gain).
Every element using `var(--mono)` picked up the new font automatically.
Separately fixed 3 canvas `ctx.font` strings (waterfall frequency-axis
ticks, spectrum dB-grid labels, bookmark waterfall pins) that hardcode the
family name directly, since canvas text can't read CSS custom properties —
these don't reference `--mono` at all and would've kept rendering Share Tech
Mono silently otherwise. Also dropped the now-unused Share Tech Mono weight
from the Google Fonts `<link>` import (Radio Canada + Orbitron remain).
Verified via grep that no code (only this changelog/comment) still names
Share Tech Mono, and re-ran the `node --check` JS-syntax pass clean.

---

### Fixed (2026-07-21) — CW/RTTY/ACARS/Multimon/AIS: closing out the UI/UX audit on the "top tier" panels

These five were rated most-polished in the original audit. Re-checked each
against the specific conventions found broken (and fixed) elsewhere this
session, rather than assuming they were fine. Multimon and AIS came back
genuinely clean — no changes. The other three had real, concrete issues:

- **RTTY — Clear button was under-clearing.** It set two divs' `innerHTML`
  directly instead of calling `rttyClear()`, a function that already
  existed and already correctly reset the char counter, the FIGS/LTRS
  badge, and both decode panes to a proper placeholder — same bug class as
  CW's own Clear button had before an earlier fix. Wired the button to
  call `rttyClear()`. Also added an empty-state placeholder to
  `rtty-decode-out-nexus` (RTTY's default-engine output pane had none,
  unlike every sibling fldigi/NEXUS decode-out pane in the app), and fixed
  an unguarded `getElementById(...).textContent` in `rttyHandleFrame()` —
  four id lookups (`rtty-live-baud/-shift/-mark/-space`) had no null check,
  unlike the identical id list three lines below in `rttyHandleAutodetect()`
  which already guards them. Those ids don't exist anywhere in the current
  HTML (leftover from an earlier layout), so any `rtty_frame` carrying
  `msg.baud`/`shift`/`mark_hz`/`space_hz` would throw and silently abort the
  rest of the handler — meaning the badge/log update at the end of that
  function never ran for that frame. Guarded to match the established
  pattern used everywhere else in the file.
- **CW — Clear button left the TUNED DECODE ticker stale.** `cwClear()`
  reset the char count, activity scope, WPM trend, and decode log, but not
  `cw-tuned-ticker` — after Clear it kept showing the last decoded snippet
  until the next frame overwrote it. Added the reset.
- **ACARS — badge contradicted the app's own gating code.** The panel
  header said "● COMPACT" (audio-only), but ACARS is in both
  `_WIDEBAND_DECODERS` and `_IQ_DECODERS`, and the Decoders dropdown
  already lists it under FULL IQ — starting it in Compact mode gets
  toast-blocked with "ACARS requires IQ stream…", directly contradicting
  what the tab's own badge claimed. Corrected the badge to "○ FULL IQ" to
  match the dropdown and the actual enforcement code. Also removed a
  stray orphaned `<!-- AIS -->` comment sitting near ACARS/tab-sigint
  (confirmed still present from the earlier full-app audit) — harmless,
  but confusing leftover from a past tab reorganization.

### Fixed/Improved (2026-07-21) — PSK31/NAVTEX/Olivia/Rivet/FreeDV/ADS-B: the mid-tier panels, per the same UI/UX audit

- **PSK31 and NAVTEX** — read through both in full; genuinely solid,
  consistent with the RTTY/CW fldigi-column convention. No changes needed.
- **Olivia — real capability gap, not just polish.** Of the five
  fldigi-engine tabs (CW/RTTY/PSK31/NAVTEX/Olivia), Olivia was the only one
  with no waterfall at all — you could see numeric telemetry (the Live
  Status box) but never the actual spectrum, and had no way to toggle AFC
  or squelch. Added the same waterfall+carrier+AFC+SQL block NAVTEX uses
  (Olivia has no adjustable BW either, so no drag brackets, matching
  NAVTEX exactly) by adding `'olivia'` to the frontend's `_FLDIGI_TAGS`
  list and teaching `_fldigiModeToTag()` to route OLIVIA/CONTESTIA/MFSK/
  FELDHELL/DOMINOEX there — the resize, PNG-waterfall-render, carrier
  overlay, and AFC/SQL sync code all already iterate that tag list, so
  this needed no new rendering logic, just the markup and the routing.
  Removed the now-redundant "Carrier" row from the Live Status box since
  the waterfall's own CARRIER readout replaces it.
- **Rivet — reordering bug.** The 240px detail column had DSC QUICK TUNE
  *below* the Decode Detail pane — the opposite order Multimon already
  uses for the identical layout, and exactly the bug Multimon's own
  2026-07 fix addressed (an empty detail pane's `flex:1` claims the whole
  column height, pushing Quick Tune out of reach). Reordered to match.
- **FreeDV** — was the only decoder panel with no Clear button. Added one,
  wired to the existing `_freedvResetScope()` (previously only called on
  Stop) since FreeDV has no message log to clear — just the SNR/sync
  trend scope, the same kind of rolling history CW's WPM sparkline has.
- **ADS-B — nested double-scroll.** The aircraft table had two independent
  scroll regions nested inside each other (outer wrapper `max-height:160px`
  and `#adsb-rows` `max-height:130px`, both `overflow-y:auto`), so the list
  had two different scrollbars with ~30px of dead space between their
  limits. Collapsed to one scroll region on the outer wrapper — the header
  row's `position:sticky` already does its job across a single container.

### Improved (2026-07-21) — HFDL/VDL2/rtl_433/DSD/DAB/Trunk: consistency pass on the "external tool" panel family

Follow-up to the UI/UX audit below: these six panels share a near-identical
template (install-notes column + message table) and were flagged as
competent but generic, with a few small cross-panel inconsistencies:

- **Missing tooltips.** Every Stop and Clear button across all six had no
  `title` attribute (only Start did) — added, matching every other decoder
  panel in the app.
- **Architecture badge was inconsistent and, in one case, missing real
  information.** Trunk alone carried an "◈ EXTERNAL" badge; HFDL, VDL2, and
  rtl_433 have the exact same architecture (their own subprocess grabs the
  SDR hardware directly — see "SDRConnect must be closed first" in HFDL/
  VDL2's own info boxes, and the 2026-07-20 rtl_433 device-autodetect work)
  but showed no such indicator. Added the same EXTERNAL badge to all three.
  DSD is architecturally different — it reads a *virtual audio* input
  (BlackHole/VB-Cable), never touching the SDR at all — so it got a
  distinct "◆ AUDIO IN" badge instead of an inaccurate reused EXTERNAL one.
  DAB's existing "▢ FULL IQ" badge was left as-is — unlike the other five,
  DAB genuinely does depend on NEXUS's own Full-IQ stream mode
  (`_IQ_DECODERS`/`_WIDEBAND_DECODERS` in the frontend), so that badge was
  already correct.
- **Row text could overflow and break table alignment.** HFDL/VDL2/DSD/
  Trunk's message-table rows had no width constraint on their last (message/
  status) column — an unusually long value would wrap and grow that one row
  taller than its neighbours. Added the same `overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap` + hover-title convention
  Multimon/POCSAG already use. Safe to truncate since the full text remains
  visible in each panel's own scrolling decode-out log just below the
  table. (rtl_433 left alone — its reading strings are already capped at
  construction time, and it has no decode-out pane to duplicate into.)

Deliberately did *not* add a click-to-detail pane (the ACARS/Multimon/
POCSAG pattern) to these five — HFDL/VDL2/DSD/Trunk already show the full
message text in their decode-out log, so a second detail view would just
duplicate it. DAB already has better-than-detail-pane interactivity (click
a row to actually play the service).

### Fixed/Improved (2026-07-21) — Marine/WEFAX/SSTV/POCSAG: the four weakest decoder panels, per a full-app UI/UX audit

A layout review of every decoder panel flagged these four as noticeably
thinner than the rest of the app — Marine was mostly empty space, WEFAX/SSTV
had no progress feedback or history, and POCSAG had a real bug: its message
list was never actually connected to anything.

**POCSAG — real bug, not just thin UI.** `pocsag_message` events were only
ever mirrored into the shared `#hf-decode-out` log; the tab's own
`#pocsag-decode-out` div existed in the markup but nothing ever wrote to it,
so the POCSAG tab always looked empty even while pages were decoding fine.
Replaced with a proper message table (TIME/CAPCODE/FUNC/MESSAGE) + detail
pane, the same list/detail shape ACARS/Multimon/Rivet already use. Also
added the message-count badge and Clear button every other panel has (both
were missing).

**WEFAX — no Clear button, no progress feedback, images vanished on the next
decode.** `wefax_clear` was already a working backend command but nothing in
the UI ever sent it. Added: a Clear button; a status bar showing live line
count + elapsed time; a Download PNG button; a real empty-state message
instead of a blank div; and a small history strip that archives the current
image (cropped to its actual height, not the over-allocated canvas) before
it's replaced, so switching away from a fax you were watching doesn't just
destroy it.

**SSTV — same treatment.** Added a progress readout (X / Y lines, from the
VIS header's known height), elapsed time, Download PNG, and the same
image-history strip, archiving the previous image whenever a new VIS header
arrives (a new transmission starting) as well as on Clear.

**Marine/VHF — was a channel list next to a redirect notice, roughly
two-thirds of the tab empty.** Marine has no decoder of its own by design
(audio-only channel monitoring — see the 2026-07-17 AIS-removal note above),
so this wasn't about faking a decoder UI. Added: a live "Now Tuned" readout
that updates when you click a channel; the channel list expanded from 8 to
16 channels and grouped by purpose (Distress & Calling / Navigation Safety /
Port Operations / Coastguard & SAR / Ship-to-Ship & Leisure), the way a
printed VHF channel card is laid out — channel 70 (DSC) is labelled clearly
as data-only so it's obvious why it doesn't sound like voice; a custom-
frequency quick-tune for local/regional channels not in the list; and the
AIS jump-link demoted to a small secondary card instead of being the
dominant element on the tab.

### Changed (2026-07-21) — UI font: Rajdhani → Radio Canada; Orbitron wordmark now actually used

`--ui` was set to Rajdhani but only had one live use in the whole stylesheet
(`--mono`/Share Tech Mono covers ~1000+ selectors — labels, readouts, panel
titles, table cells), so the visible effect of this swap is concentrated on
that one spot plus the body-level fallback. Orbitron had been imported since
the original build but never applied anywhere (0 CSS matches) — it's now
wired to a new `--brand` var and applied to `#brand-name` (the "DARKSKY
NEXUS" wordmark in the brand bar), which previously rendered in Share Tech
Mono like everything else.

- Google Fonts `<link>`: `Rajdhani:wght@300;400;600` → `Radio+Canada:wght@300;400;500;600`, kept Share Tech Mono + Orbitron
- `--ui` → `'Radio Canada',sans-serif`; added `--brand:'Orbitron',sans-serif`
- `#brand-name` now uses `var(--brand)` at weight 700 instead of `var(--mono)`

Checked `sn.textContent = 'DARKSKY NEXUS — Live Spectrum Intelligence'`
(line ~11650, `cin-signal-name`) as a possible second wordmark — that id has
no matching element anywhere in the markup, so it's a dead reference (the
`if (sn)` guard just no-ops). `#brand-name` is the only real rendered
wordmark.

Broader "reclassify general UI text from mono to Radio Canada" pass not
done here — out of scope for this request, flagged as an optional follow-up.

### Added (2026-07-20) — rtl_433 device autodetection (rtlsdr vs SDRplay)

User asked how to point rtl_433 at SDRplay hardware (per the ISM panel's own info text, "set device to a SoapySDR driver name"), then asked whether this could be autodetected instead of hand-set. It turned out the backend already fully supported an explicit override (`rtl433_start`'s `device` field → `state['rtl433_device']` → `-d driver=<name>`), matching HFDL/VDL2's own `hfdl_device`/`vdl2_device` pattern — but there was no frontend control for it at all, and the hardcoded default was always `"rtlsdr"` (a plain dongle), unlike HFDL/VDL2 which both already default to `"sdrplay"`.

**Added:** `_detect_rtl433_device()` (`w033_NEXUS.py`), called by `_launch_rtl433()` whenever `rtl433_device` is left at its new default of `"auto"`. Resolution order: (1) a real RTL-SDR dongle actually plugged in, detected via a quick `rtl_test -t` probe, always wins — this preserves the common "cheap dedicated dongle running rtl_433 while the SDRplay does everything else" setup with zero config; (2) otherwise, if NEXUS itself currently has an SDRplay connected (`state['active_device']`, populated from SDRConnect's own device-info report), fall back to `driver=sdrplay` automatically — covers the single-SDRplay-only setup without ever touching a config field; (3) otherwise fall back to the historical `"rtlsdr"` default. The chosen device and reason are logged (`rtl_433: autodetected device=... (...)`) at launch. Explicitly setting `device` on the `rtl433_start` command still overrides autodetection entirely — this only changes what happens when nothing more specific has been requested.

Updated the ISM Sensors panel's info text to describe the new automatic behavior instead of the old manual-only instructions.

---

### Fixed (2026-07-20) — ISM (rtl_433) quick-tune buttons didn't tune the main VFO

User report: "ism quick tune buttons do not tune vfo." The three ISM frequency chips (433.92 / 315.0 / 915.0 MHz) in the Decoders → ISM Sensors panel called `rtl433SetFreq(mhz)`, which only ever set `_rtl433Freq` — the frequency rtl_433's own independent subprocess/device uses next time it's (re)started — and never touched the main NEXUS VFO/waterfall at all. Every other quick-tune control in NEXUS (band-plan strip, Bands panel, WSPR band buttons) calls `tuneVFO()`/`_tuneTo()` to move the main receiver's LO so the clicked frequency is actually visible on screen; this one silently didn't. Same category of bug as the earlier FT8 quick-tune-not-retuning-SDR-LO fix.

**Fix:** `rtl433SetFreq()` now also calls `tuneVFO(mhz)`. rtl_433 itself still runs its own independent device, so this doesn't change what rtl_433 decodes — it makes the main spectrum/waterfall jump to the clicked ISM frequency too, so the raw RF activity NEXUS itself is receiving there is actually visible. Frontend-only fix — hard-reload the browser to pick it up, no Python restart needed.

---

### Fixed (2026-07-20) — AIS: DC/LO-leakage spike on the tuned AIS channel corrupting decode

User report: "i have dc spike on the ais freq. does sdrplay have iq correction or can we introduce this to nexus." Investigated whether SDRplay's hardware DC-offset/IQ-imbalance calibration (present in the API, and already applied automatically by SDRConnect, which manages the RSPdx here) would cover this — it doesn't, fully: that calibration zeroes the *receiver's own* internal DC term, but on any zero-IF/direct-conversion SDR, whatever sits exactly on the tuned LO frequency always shows up as a residual spike at 0 Hz baseband, no matter how good the calibration is. Tuning directly onto 161.975/162.025 MHz (as needed to decode AIS) puts that spike right on top of the channel of interest.

**Root cause (confirmed by reading the code):** both `AisDecoder.process_iq()` and `AisDecoderDireWolf.process_iq()` are fed the raw Full-IQ tap (`_fiq_c`) with zero offset-mixing — unlike RTTY/CW, which get a `vfo_offset_hz` correction, AIS decodes straight off whatever's sitting at the hardware LO center, with no DC handling anywhere in the front end. Because the FM discriminator both decoders use is a nonlinear product (`s[n] * conj(s[n-1])`), a strong stationary DC term doesn't just add a fixed bias — it beats against the real GMSK signal and can dominate the discriminator output, corrupting the zero-crossing PLL/bit-slicer well before CRC gets a chance to reject anything. This is the same class of issue rtl-ais's own README warns about (advising against center-tuning directly on the channel of interest) — this codebase's `AisDecoder` is a near-literal port of rtl-ais's receiver.c but never carried over any DC handling.

**Fix:** added a persistent one-pole complex DC-block high-pass filter (`y[n] = x[n] − x[n-1] + R·y[n-1]`) to both decoders, applied to the raw IQ *before* the FM discriminator. `R` is recomputed from the actual `sr` on every sample-rate change so the cutoff stays fixed at ~50 Hz regardless of what rate the Full-IQ tap is running at (it varies a lot, unlike the multimon-ng path's fixed-22050Hz DC block elsewhere in this file) — comfortably below AIS's 9600-baud/±4.8kHz GMSK signal band, so the spike is removed without meaningfully touching real signal energy. Verified standalone: a synthetic strong DC term (fixed complex offset) is suppressed from full amplitude down to ~1e-16 after settling, while a 1kHz test tone standing in for real signal content loses <1% of its amplitude through the same filter.

**Requires a Python restart** (backend-only fix). Not yet re-verified against a live DC-spike capture — the standalone numerical test confirms the filter design behaves correctly (kills a stationary term, passes signal-band content), but this hasn't been confirmed against the user's actual RF yet.

---

### Fixed (2026-07-20) — Logbook "SPOTS PER BAND" always shows Unknown, FREQ column near-zero

User report: in the REPORTING – LOGBOOK tab, every FT8 auto-populated entry's FREQ (MHz) column showed implausible near-zero values (0.0002–0.0024 MHz instead of ~14.074 MHz), and the "SPOTS PER BAND" stats panel bucketed all 504 entries as "Unknown" — despite the real band ("20m") clearly being known, since it rendered correctly as plain text in the same rows' Notes column. User's own diagnosis pointed the right direction: "we already click the band in the quicktune."

**Root cause:** `_ft8DecodeToLogEntry()` (`DARKSKY_NEXUS_w033.html`) built each LogEntry's `frequency` field as `d.freq / 1e6`. `d.freq` is the FT8 decode's AUDIO TONE offset within the passband (~200–2900 Hz) — not an absolute RF frequency — so dividing it by 1e6 produced a near-zero "MHz" value instead of the real dial frequency. This exact distinction was already documented (and handled correctly) a few hundred lines below, in the PSK Reporter forward code added earlier this cycle, which computes `dialHz + d.freq` before treating the result as RF Hz. The Notes column still showed the correct band because `band` there comes from `getCurrentBandName()` — the quick-tune band selection, a completely separate and already-correct lookup — but the stats panel and the band filter dropdown both bucket by `logBandFromFreq(e.frequency)`, reading the broken `frequency` field, so they never matched any band range and always fell back to "Unknown."

**Fix:** `_ft8DecodeToLogEntry()` now adds the current dial/VFO frequency (`DS.vfos.a.freq`, falling back to `DS.liveCenter`) to `d.freq` before converting to MHz, matching the working PSK Reporter calculation. New entries logged after this fix will carry the correct FREQ and band; entries already in the Logbook from before the fix keep their stored (wrong) frequency value until re-logged or manually corrected.

---

### Fixed (2026-07-20) — macOS build fails looking for w032

User report: running `build_macOS.sh` in w033 failed looking for w032 files. Root cause: when w033 was forked from w032, only the docs build scripts were updated for the new version ("Fork docs build scripts w032→w033" — see below); the entire `build/` folder (build_macOS.sh, build_Windows.bat, DARKSKY_NEXUS_macOS.spec, DARKSKY_NEXUS_Windows.spec, DARKSKY_NEXUS_w032.iss, BUILD_NOTES.md, version_info.txt) was never touched and still referenced `../w032_NEXUS.py` and `../DARKSKY_NEXUS_w032.html` — files that don't exist in the w033 folder (only `w033_NEXUS.py`/`DARKSKY_NEXUS_w033.html` do), so PyInstaller's Analysis step failed immediately.

**Fix:** replaced every `w032` reference with `w033` across all seven build/installer files, bumped the dotted version 0.3.2 → 0.3.3 to match, and renamed `DARKSKY_NEXUS_w032.iss` → `DARKSKY_NEXUS_w033.iss`. Verified: both `.spec` files and `version_info.txt` pass `py_compile`, `build_macOS.sh` passes `bash -n`, and every remaining path reference now points at files that actually exist in the w033 folder. w032 itself untouched.

---

### Fixed (2026-07-20) — RTTY tone scope still jumping (worse) — real root cause: two disagreeing audio_fft broadcasters

The confidence-gate fix above (previous entry) stopped the auto-detect mark hopping, but user reported the tone scope was still jumping — "worse" — after restarting NEXUS. Live instrumentation (polling `DS.audioFftMeta` every 250ms while RTTY ran) caught it directly: the frontend was receiving *two different* `audio_fft` broadcasts in alternation — one steady one at `carrier_hz≈mark, sr=48000, 256 bins` and an intermittent one at `carrier_hz=0, sr=50000, 492 bins` — flickering between them every couple of seconds.

**Root cause:** the Full-IQ `audio_fft` broadcaster (both its base and zoom paths, `w033_NEXUS.py`) only ever re-centered its output for CW (`if active_decoder_slug == 'cw' and cw_dec.active`). There was no equivalent branch for RTTY. When RTTY was the active decoder instead, the broadcaster fell through reporting the raw VFO-offset-from-hardware-LO as `carrier_hz` (0 whenever the VFO sits exactly on the hardware center, as in the live repro) instead of the RTTY mark tone the Compact-mode broadcaster (`_carrier_hz_r`, a separate, correct code path) already centers on. Because an nRSP-ST device streams Compact-mode audio continuously *regardless of display mode* (the same fact behind this session's earlier FT8 Full-IQ regression), both broadcasters run simultaneously and race — the frontend's single RTTY tone scope has no way to prefer one over the other, so whichever packet lands last wins, and they disagree about where the center of the window is, at what sample rate, and how many bins.

**Fix, take one:** the Full-IQ broadcaster (base and zoom paths) now recognizes RTTY the same way it already recognized CW — shifting the raw hardware-LO-centered IQ to VFO-relative baseband, then reporting `carrier_hz` as the live RTTY mark tone (matching the Compact-mode broadcaster's convention) instead of 0.

**Still jumping after restart — fix, take two:** live-instrumented `DS.audioFftMeta` again post-restart and confirmed take-one's centering fix WAS active (`carrier_hz` now showed the real mark tone, not 0) — but the two broadcasters were still alternating every ~1s, because they still differ in native sample rate and bin count (48000/256 bins for Compact vs `_fiq_afft_sr`/~512 bins for Full IQ), so switching between them still visibly changed the trace's resolution/shape even with the same centre. Realigning *what* they reported wasn't enough — they're still two independent, competing sources for one on-screen widget. Since an nRSP-ST device's Compact-mode broadcast already covers CW/RTTY correctly by itself (same fact behind both bugs above), the Full-IQ audio_fft broadcast (both paths) is now suppressed entirely whenever `_is_nrsp_st` is true — it now only fires for direct-USB devices (e.g. RSPdx) that get no Compact-mode stream at all, mirroring the exact device-type distinction the FT8 Full-IQ fix already established. Verified via `py_compile`; w032 untouched (hash unchanged). Needs a NEXUS restart to take effect.

---

### Fixed (2026-07-20) — RTTY tone scope waterfall/spectrum "jumping" after restart

User report (after restarting NEXUS to pick up the fix below): "look at live tonescope waterfall/spectrum it's jumping and it didn't do that before." Screen recording confirmed the tone scope's M (mark) marker hopping from 1022 Hz to 899 Hz mid-session with no user action, dragging the whole displayed trace along with it.

**Root cause:** `rttyHandleAutodetect()` applied *every* successful auto-detect reply unconditionally — overwriting the live mark/space and re-sending `rtty_set_params` to retune the decoder on every ~1s capture cycle, regardless of how weak that individual capture's confidence was. On a marginal real signal, the SNR gate added by the fix above only asks "is this above the noise floor at all" (confirmed live: genuine confidence as low as ~27%), so successive 1-second capture windows can each land on a slightly different candidate peak pair. Every accepted-but-weak reply yanked the tone scope's markers (and the live decoder's actual tuning) out from under a perfectly good existing lock.

**Fix:** retuning is now gated on the same 0.45 "not WEAK" confidence boundary already shown in the on-screen quality label. A weak/marginal reply still updates the status text (so the user can see WEAK/Searching) but no longer touches the live mark/space or re-tunes anything until a confident-enough reply arrives — holding the last good lock steady instead of chasing noise.

---

### Fixed (2026-07-20) — RTTY INTERNAL auto-detect confidently "locks" onto noise, producing scrambled decoded text

User report: "rtty internal is running in chrome... decoded text is scrambled." Live repro with Auto-detect baud & shift enabled: the detector locked onto mark=455 Hz/space=302 Hz/100 Bd at a displayed "85% confidence, Signal locked, GOOD" — while the live decoder's own separate squelch simultaneously reported NO SIGNAL on the same audio. Two disagreeing answers to "is there a signal here" from the same feature.

**Root cause, two bugs stacked:**

1. `RttyDecoder.analyse()` (the auto-detect algorithm) only ever checked *relative* fit — is the second spectral peak at least 20% of the first, do the bit-run lengths statistically line up with a standard baud rate — never whether the detected mark/space tones carry any real power above the noise floor. A pair of peaks right at the 300 Hz edge of its own search band (almost certainly a filter-edge artifact, not real signal) satisfied both relative checks and was reported as a confident detection.
2. The frontend's `rttyHandleAutodetect()` read `msg.confidence || 0.85` — but the backend never actually included a `confidence` field in its reply, so this line silently defaulted to a **hardcoded 85% on every single response**, real detection or not. The "85% / GOOD / Signal locked" UI was not measuring anything.

**Fix:** `analyse()` now gates on absolute SNR using the same spectral-noise-reference technique (`_goertzel_power` at `mark_hz + 2.5×shift`) the live decoder's own squelch already uses, and returns a genuine confidence score blending timing-fit quality with measured SNR margin. The backend now sends this real value; the frontend reads it directly (`msg.confidence ?? 0`, no more silent 85% fallback). Verified with a synthetic test: a strong real signal now scores ~0.86 confidence, a noise pattern matching the exact frequencies from the live bug report is correctly rejected (previously silently accepted), and a weak-but-real signal scores a moderate ~0.57 rather than a flat 85% regardless of quality.

---

### Fixed (2026-07-20) — FT8 INTERNAL zero decodes in Full IQ, again — RSPdx/direct-USB regression from yesterday's fix

Yesterday's fix (below, "FT8 INTERNAL still 0 decodes...") removed Full IQ's
own FT8 audio broadcast entirely, reasoning that SDRConnect's Compact-mode
audio broadcast supplies the FT8 buffer in every display mode regardless.
That's true for networked nRSP-ST units, but not for a directly-connected
RSPdx (`state['device_type'] == 'RSPdx'`, not `'nRSP-ST'`) — SDRConnect
never sends a Compact-mode audio stream for that connection type at all, in
any display mode. Full IQ is the *only* mode a direct RSPdx has, so removing
its FT8 broadcast left it with zero path to the decoder.

Confirmed live: a Chrome-side packet counter on `handleBinaryFrame` showed
zero `0x02` (audio) frames over a 15+ second FT8-enabled window with a
strong on-screen FT8 signal and `device_type: "RSPdx"`.

**Fix:** restored the Full-IQ branch's `_ft8_broadcast_audio()` call, this
time correcting the actual bug the original (pre-2026-07-19) version had —
mixing `_fiq_c` down by `_fiq_vfo_off` (shifting the tuned VFO frequency to
DC) before taking the real part, instead of broadcasting `_fiq_c.real`
un-shifted (hardware-LO-centered, not VFO-centered — the original root
cause). Verified with a synthetic-tone test: a tone placed 1500 Hz above the
tuned frequency lands at exactly 1500 Hz in the demodulated output. Both
device types now get a working FT8 audio feed in Full IQ: nRSP-ST via the
Compact-mode broadcast (unaffected by this change), RSPdx via this
corrected Full-IQ broadcast.

Also noted in passing, now fixed below: the "Full IQ (USB direct)" status
badge shows whenever `device_type` is merely known and isn't literally
`'nRSP-ST'` — it doesn't verify an actual direct-USB connection, so it can
display for a networked/remote RSPdx (e.g. accessed via SSH to a remote
host, as in this user's setup) just as readily as a genuinely local one.

---

### Fixed (2026-07-20) — misleading "Full IQ (USB direct)" status badge wording

Follow-up to the entry above. Relabeled to **"Full IQ (only mode)"** and
reworded its tooltip to state the fact this badge can actually verify — that
SDRConnect exposes no Compact/IQ-Lite mode selector for this device type, so
it's always genuinely Full IQ once connected — without implying a literal
local USB cable, which the underlying check (`device_type` known and not
`'nRSP-ST'`) never actually confirms. No logic change; the badge still
appears under the same condition, just describes what that condition
actually means.

---

### Added (2026-07-19) — REPORTING tab: Logbook for SWL reception reports, FT8 decodes, and mission-based logging (w033 only)

New first-class tab (📒 REPORTING) for capturing every loggable event —
manual entries and auto-populated FT8 decodes alike — not scoped to ham-radio
QSOs. Originally spec'd assuming a Vue 3 + Tailwind + Base44-entity stack;
w033 has none of that (single Python backend + single HTML/vanilla-JS
frontend, no build step), so the feature was implemented natively instead,
reusing every existing convention in the app rather than introducing a new
framework:

- **Backend** (`w033_NEXUS.py`): `LOGBOOK_FILE` JSON persistence
  (`darksky_logbook.json`), mirroring the bookmarks load/save pattern. New WS
  commands `log_list`, `log_save` (upsert by id), `log_delete`,
  `log_bulk_save` (FT8 bulk import, replies with `log_bulk_result`). Full
  list sent on every browser connect, same as bookmarks.
- **Frontend**: `#tab-reporting` panel — sortable/filterable table (time,
  callsign, frequency, mode, SNR, grid, mission, notes), search box,
  mode/band/date filters, mission-tag filter chips (`LOG_MISSIONS` palette:
  FT8/HF Utility/Airband/Marine VHF/Broadcast/AIS/SIGINT/General SWL),
  pagination, and a collapsible stats panel (spots/band, SNR distribution,
  DX-distance histogram, spots/mission — all dependency-free bar/histogram
  rendering, no chart library).
- **Add/Edit modal + delete confirmation**: reuses this session's
  bookmark-popup bugfixes (synchronous focus, mousedown+click backdrop-close
  guard, global-keydown-guard on the popup's own open state) from the start.
  Ctrl+N opens the add modal from anywhere in the app.
- **Export**: ADIF (.adi) and CSV, both scoped to the currently filtered/
  visible rows.
- **FT8 auto-populate**: `appendFT8Decode()` is wrapped (not edited) to
  mirror every raw decode into a rolling `ft8RecentDecodes` buffer; "⭳
  Populate from FT8" converts new (deduped) decodes into log entries using
  the app's existing geo/parsing helpers (`extractFT8Callsign`,
  `extractFT8Grid`, `callsignToCountry`, `gridToLatLon`, `_haversineKm`,
  `_hfBearing`, `getCurrentBandName`, `HF_LOC`) — no duplicate geo/parsing
  code added server-side. Country, band, distance, bearing, dt, and the raw
  FT8 message are folded into the entry's notes field.

Confirmed not to touch `w032_NEXUS.py` (md5 unchanged throughout:
`038252cbc1e9643dc48177ea21c5d81a`). Both files verified via `py_compile`
and a Node.js syntax check of the extracted inline script.

---

### Fixed (2026-07-19) — FT8 INTERNAL still 0 decodes in Full IQ after the sample-rate fix (actual root cause: wrong signal, not just wrong rate)

Follow-up to the sample-rate entry directly below, after the user reported
the resample fix alone didn't resolve it ("no decodes coming through
despite fix"). The sample-rate mismatch was real and worth fixing, but
wasn't the actual blocker — reinstalled a live Chrome-side hook on
`ft8HandleAudioFrame()` and found incoming 0x02 audio frames alternating
1:1 between two completely different streams while Full IQ was active:
one near-silent with a variable length (~4500-6100 samples), one healthy
with a constant 960-sample length and real peak amplitude. That's two
distinct broadcasts landing in the same buffer, not natural variance in
one.

Root cause: Full IQ's `_ft8_broadcast_audio(_rcap_real, ...)` call site
sends `_fiq_c.real` — the real part of Full IQ's wideband complex baseband
IQ, centered on the **hardware LO**, not the tuned VFO (see `_fiq_vfo_off`
a few lines below it, which RTTY/the CW skimmer pool/AIS all have to
explicitly correct for when using this same `_fiq_c`). It was never a
demodulated single-channel USB audio signal, so FT8's tones don't land
anywhere near the 200-3000 Hz band `ft8ts` searches — no amount of
resampling fixes that. Meanwhile SDRConnect turns out to keep sending its
own correctly VFO-centered, already-demodulated audio (the same stream the
Compact-mode `t == 4` branch broadcasts from) continuously, regardless of
which display mode the UI has selected — so that correct stream was
*already* reaching the browser the whole time, just getting scrambled
together with Full IQ's irrelevant raw-IQ contribution in the single
shared `ft8AudioBuffer`.

Confirmed conclusively live: with everything else unchanged (same VFO,
same USB mode, same FT8-internal session), switching the engine mode from
Full IQ to Compact produced a real decode within one cycle
(`IU7BSQ/P FV9MQR/P R JL76`, France, -22 dB). Fix: removed the Full IQ
branch's `_ft8_broadcast_audio()` call entirely (and the now-unused resample
cache from the first fix attempt) — Compact mode's broadcast already
supplies clean audio to the FT8 buffer independent of Full IQ, so FT8
internal should now work correctly in Full IQ mode too, not just Compact.
Not yet re-verified live in Full IQ after this second fix (needs another
server restart); the Compact-mode decode above is what's actually been
confirmed working end-to-end so far. w033 only.

---

### Fixed (2026-07-19) — FT8 INTERNAL decoder never decodes in Full IQ mode (silently wrong sample rate)

User report: "ft8 internal no longer decodes when running despite strong
signal incoming." Reproduced live: Full IQ mode @ 250 kSPS, tuned to
14.074.000 USB, strong FT8 traffic clearly visible in the mini-scope
(multiple simultaneous tones, +6 to +12 dB SNR) — the internal ft8ts
decoder ran every 15s cycle (confirmed `ft8DecodeEnabled`, `ft8WorkerReady`,
full 720,000-sample buffer each cycle) but consistently reported 0 decodes.

Root cause: Full IQ's audio-tap sample rate (`_fiq_afft_sr`) is variable —
chosen to land as close to 48kHz as possible *without going below it* (see
the decimation-factor logic added for the CW/RTTY tone-scope resolution
fix), so it's only exactly 48000 Hz by coincidence. At 250 kSPS it lands on
50000 Hz instead (dec factor 5); at 62.5 kSPS it's 62500 Hz (no decimation
at all — 30% off). `_ft8_broadcast_audio()`'s wire format does embed the
real sample rate in its header, but the browser-side consumer
(`ft8AudioTap()` / the worker source built in `loadFT8Worker()`, in
`DARKSKY_NEXUS_w033.html`) never reads it back out — it hardcodes a 4:1
48000→12000 decimation and always tells `ft8ts`'s `decodeFT8()`
`sampleRate: 12000`. Compact mode and IQ Lite both sit at a fixed, exact
48000 Hz (`DECODER_SR`), so this mismatch was invisible there — only Full
IQ's variable-rate decimation exposes it. Even a ~4% sample-rate error
shifts FT8's whole audio passband enough to break Costas-array sync,
dropping every decode despite strong, clearly-visible tones.

Fixed backend-side rather than in the browser: at the Full IQ
`_ft8_broadcast_audio()` call site (the same real IQ (`_rcap_real`)
already computed for the RTTY capture feed just above it), resample to a
true 48000 Hz via `scipy.signal.resample_poly()` (rational ratio from
`Fraction(48000/_fiq_afft_sr).limit_denominator(1000)`, cached and only
recomputed when the hw sample rate actually changes) before handing it to
`_ft8_broadcast_audio()`. This keeps the 48000 Hz contract the browser
worker assumes true for every caller, without needing to touch the
worker's decimation/rate-handling logic at all. Falls back to the old
(rate-mismatched) behaviour if scipy isn't available, matching this file's
existing no-scipy degraded-mode pattern elsewhere. Verified the resample
math directly (`resample_poly` at the computed up/down ratios for 62.5
kSPS, 250 kSPS, 500 kSPS, and 2 MSPS all land on exactly 48000 samples/sec
of output); not yet re-verified against a live decode (needs the user to
restart the Python server, since this is a backend/`.py` fix — the
in-browser mini-scope showing tones isn't enough to confirm actual
decodes, that requires a full 15s cycle with the fix loaded). w033 only.

---

### Fixed (2026-07-19) — Bookmark popup also closed on an overshot text-selection drag (w033 only, follow-up to the focus-race fix above)

Follow-up live report, after confirming (via hard refresh) that the
focus-race fix above was working: "changed the text in the first line,
selected all the text in the second line, and the dialogue box closed."
Narrowed down live: Tab-navigating between the three fields works fine,
and typing/editing in all three fields (already re-verified after the
focus-race fix) works fine — only a text-*selection* gesture (drag-select
or triple-click, i.e. what "select all" in a short text field usually
looks like physically) reproduces a close.

Root cause: `#bm-popup-overlay`'s `onclick="if(event.target===this)
closeBookmarkPopup()"` closed the popup whenever a `click` event's target
was the backdrop itself — `#bm-popup-box`'s own `onclick="event.
stopPropagation()"` normally prevents this for ordinary clicks on the
fields, but only because those clicks' *target* is inside the box to
begin with, so the event never reaches the backdrop's own handler via
bubbling. A selection drag that starts inside the (fairly narrow, 320px)
box but overshoots past its edge before the mouse is released ends up
with the browser's synthesized `click` event targeting the *backdrop*
directly (since that's where the mouseup landed) — box's stopPropagation
never runs for that event at all, because the event's target was never a
descendant of box in the first place. From the old code's perspective
this was indistinguishable from a genuine "click outside to dismiss."

Fixed by requiring both the `mousedown` *and* the `click` to have
targeted the backdrop before closing: added `onmousedown="window.
_bmOverlayMousedownOnBackdrop = (event.target === this)"` to the overlay,
and changed its `onclick` to additionally check that flag. A real
dismiss-click satisfies both (mousedown and click both land directly on
the backdrop); an overshot selection-drag that starts inside the box
(mousedown target = an input, not the backdrop) no longer does, even
though its terminating click event's target happens to be the backdrop.

Not yet re-verified live — the Claude in Chrome extension disconnected
mid-session before this fix could be retested the same way the focus-race
fix was (open popup, reproduce the exact reported gesture, confirm no
close). w032 confirmed byte-identical (md5 unchanged) — w033-only.

---

### Fixed (2026-07-19) — Bookmark popup: typed keystrokes leaked to global keyboard shortcuts instead of the name field (w033 only)

Live-reported: "when i press the bookmark button and attempt to enter
text, it closes unexpectedly." Reproduced directly in a connected live
session: clicking the ⭐ Bookmark button opens the popup correctly, but
typing "test bookmark" immediately after did not appear in the Name field
at all — instead it opened the Signal Radar modal (the 'r' in "bookmark")
and the Bands panel (the 'b'), i.e. the keystrokes were being consumed by
`window.addEventListener('keydown', ...)`'s single-key shortcut switch,
not the popup's focused input.

Root cause: `openBookmarkPopup()` set the overlay visible
(`style.display = 'flex'`) and then deferred focusing the name field via
`setTimeout(fn, 0)`. That created a real window between the popup
becoming visible and the input actually receiving focus. Any keydown
landing in that window — fast typing, or a key auto-repeating right after
the click — still saw `document.activeElement` as the Bookmark button (or
`<body>`), not the input, so the shortcut switch's activeElement guard
didn't catch it and the keystroke fell straight through to shortcuts like
'r' (Radar) and 'b' (Bands panel). Confirms this general class of bug
already seen elsewhere this session (state not syncing until a specific
event fires) can also show up as a UI *input* race, not just a *display*
one.

Fixed two ways: (1) `openBookmarkPopup()` now calls `.focus()`
synchronously right after setting `display:flex`, instead of deferring it
— Chrome allows focusing an element the instant it's `display`-visible,
so the `setTimeout(0)` was pure unneeded risk, not a required delay; (2)
added a guard at the top of the global keydown handler —
`if (document.getElementById('bm-popup-overlay')?.style.display ===
'flex') return;` — mirroring the existing `cmd-overlay` check just above
it, so shortcuts are blocked by the popup's own open/closed state rather
than relying on focus timing at all (defense in depth against any future
similar race).

Verified live: reran the exact repro (open popup, immediately type "test
bookmark") after the fix — the text now appears correctly in the Name
field (appended to the auto-prefilled "Lightning Sferics" guess right
where the cursor was) and neither Signal Radar nor the Bands panel opened.
w032 confirmed byte-identical (md5 unchanged) — w033-only.

---

### Fixed (2026-07-19) — SSTV caused progressively worsening spectrum/waterfall stutter/freeze when no VIS header ever locked (w033 only)

Live-reported: "sstv decoder running. spectrum and waterfall stutter/freeze."
Root cause: `SstvDecoder._scan_for_vis()`'s existing "memory bound" (trims
`self._freq_buf` once `self._searched_upto` grows past 5s) only fires once
`_searched_upto` has advanced past a leader-tone run that was actually
found — either locked into a real header or conclusively rejected. If the
tuned signal never produces a matching 1900Hz leader tone at all (the
`near_leader`/`all_leader_runs` check comes back empty every single pass —
the ordinary case while SSTV sits on a channel with no valid transmission
yet, or one that never arrives), `_searched_upto` stays at 0 forever and
that trim never triggers. `_freq_buf` then grows unbounded, and every
`process_iq()` call rescans the *entire* buffer for the leader tone — an
O(n) `np.abs(...)` pass with n growing every call, so total cost is O(n²)
the longer SSTV runs without locking a header. That scan runs
synchronously inline with the exact code path (all 5 of `sstv_dec`'s call
sites) that also computes and broadcasts the spectrum/waterfall FFT bins,
so it directly delays them — explaining a stutter that gets progressively
worse over time rather than a one-off glitch.

Fixed with a hard cap on `_freq_buf`'s length, independent of
`_searched_upto`: added a check right after the buffer is appended to in
`process_iq()` that trims it to at most 8 seconds (`_SSTV_SR * 8`,
comfortably longer than one nominal ~620ms VIS header so a genuine header
in progress is never cut off), adjusting `_searched_upto` down by the same
trim amount (clamped to 0).

Verified via a stress test (not just synthetic single-header decode, like
the original SSTV validation) — extracted the current `SstvDecoder` fresh
from the file and fed it 2 minutes of pure phase noise (chunk-by-chunk,
20ms chunks at 48kHz, never producing a valid leader tone) through
`process_iq()`, timing every call. Before this fix, `_freq_buf` would grow
to the full 2 minutes' worth of samples (~5.76M) with per-call cost
climbing the whole time; after the fix, the buffer hits its 384,000-sample
(8s) cap by chunk 500 (~10s in) and stays flat for the remaining ~110s of
the run, with per-call cost settling at roughly 1ms instead of continuing
to climb. w032 confirmed byte-identical (md5 unchanged) — w033-only.

---

### Fixed (2026-07-19) — AIS Idle/Active badge and Start/Stop buttons never synced from the server on connect (w033 only)

Live-diagnosed via a fresh browser tab connected to a real, running session
(Full IQ, 250kSPS, tuned to 161.975 MHz, `ais_active: true` confirmed
directly from the server's own state) — the AIS tab still showed
"○ Idle" / "▶ Start" and the top-bar decoder badge said "No decoder
active", even though AIS was genuinely running. Root cause: `applyState()`
(the handler for the server's `get_state`/`state` snapshot, which already
carries `ais_active` on every connect and on most state-changing events)
never read that field at all — `_decoderUpdateUI()` already knows how to
flip `#dec-badge-ais`/`#dec-start-ais`/`#dec-stop-ais`, it just was never
called from `applyState()`. Fixed by adding a check at the end of
`applyState()`: `if (s.ais_active !== undefined) _decoderUpdateUI('ais',
s.ais_active)`. Deliberately does not touch `_activeDecoderSlug` (the
"only one decoder exclusively active" tracker), since `"type":"state"` is
broadcast constantly during normal use — on VFO tune, mode change, sample-
rate change, and dozens of other events, not just once on connect — so
forcing `_activeDecoderSlug` to `'ais'` on every one of those broadcasts
would fight with switching to a different decoder locally while AIS keeps
running server-side in the background.

Verified live: reloaded the connected browser tab from scratch — badge
and buttons now correctly show "● Active" / "■ Stop" and the top-bar
badge shows "● AIS active" immediately on load, with zero clicks. Other
Full-IQ/external decoders (`wefax_active`, `pocsag_active`, `adsb_active`,
etc.) likely have the identical gap — none of them are read in
`applyState()` either — but this fix is scoped to AIS only, since that's
what was reported and verified live; a future pass could generalize it to
the rest. w032 confirmed byte-identical (md5 unchanged) — w033-only.

Separately (not a bug, just a finding from the same live session): AIS
was confirmed genuinely active with correct settings but had decoded zero
vessels so far. The waterfall showed real burst-like activity on both AIS
channels, but frames_seen/frames_crc_ok — the diagnostic that would show
whether the demodulator is finding candidate packets that fail CRC versus
finding nothing — is only ever `log.info()`'d server-side, never broadcast
over the WebSocket, and the mounted log-folder copy of `darksky_nexus.log`
turned out to be stale (last entry July 17), so this couldn't be confirmed
remotely. Left as an open item for the user to check directly in their
own terminal output.

---

### Changed (2026-07-19) — Decoders tab redesigned as a category-tab + button-grid panel, matching the bands dropdown (w033 only)

The DECODERS tab's old dropdown was a click-to-open vertical list: 23
`<div class="dropdown-item">` rows grouped under 3 collapsible headers
(COMPACT/FULL IQ/EXTERNAL). Per user request ("redesign the layout of the
decoders tab to match the layout and style of the bands dropdown ie
buttons"), it's now a floating panel — opened via `toggleDecodersPanel()`,
rendered by `_renderDecoderPanel()` from a new `DECODERS_DB` table — with
category tabs across the top (COMPACT/FULL IQ/EXTERNAL, one visible at a
time) and a 2-column grid of `.dec-nb-btn` buttons below, the same
structural pattern `_renderBandPanel()`/`BANDS_DB` already used for the
bands dropdown. Differences from the bands panel are deliberate: 560px
wide (vs 500px) and a 2-column grid (vs 6-column), since decoder names run
much longer than a frequency label ("Olivia / Contestia / MFSK / Hell /
DominoEX" vs "20m"); violet (`#a78bfa`) used for the active-category-tab
and currently-running-decoder highlight instead of the bands panel's
orange, matching the DECODERS tab's own existing accent color.

All 23 decoder entries carried over 1:1 (same slugs, tag text, tag
colors) — this is a pure layout change, no decoder was added, removed, or
reassigned to a different tier. The old "Stop active decoder" row is
preserved, now rebuilt from live state (`_activeDecoderSlug`/`ft8Running`)
on each panel open rather than living as an always-in-DOM row toggled by
`_decDropdownStopRow()` (that function is left in place — harmless no-op
now that its target elements are gone — since other call sites weren't
audited for removal). The old `.dropdown-item`/`.dec-group-hdr` CSS/markup
is removed from the decoders tab's own dropdown; the underlying
`.dropdown-menu`/`.dropdown-toggle`/`toggleDropdown()`/`closeAllDropdowns()`
plumbing is left alone since it isn't decoders-specific dead code — no
other tab used it, but nothing on this pass confirmed removing it
wouldn't affect something un-audited.

Verified: `#tab-dec-btn` kept its id/class so `showTab()`'s existing
"light up DECODERS when any decoder sub-tab is active" logic needed no
change (only its CSS selector, `#tab-dec-btn.selected` instead of the old
`#drop-decoders>.dropdown-toggle.tab.selected`, since the `#drop-decoders`
wrapper no longer exists). Toggling the decoders panel now also closes the
bands panel and BW panel if open (and vice versa), matching the existing
mutual-exclusion behavior between the bands and BW panels. All `<script>`
blocks re-verified via Node `new Function()` syntax check; w032 confirmed
byte-identical (md5 unchanged) — this change is w033-only.

---

### Fixed (2026-07-19) — WEFAX image never rendered in the UI; `sr=` crash risk on 2 call sites (w033 only)

Both bugs were found while building SSTV's image renderer above and
fixed here at the user's request, in w033 only (w032 untouched).

- **Frontend never drew the WEFAX image.** `wefax_line`'s WS handler
  only appended a text log line (`[WEFAX line N]`) and never read
  `msg.image_b64` or touched the `wefax-image-container` div, which sat
  permanently empty — the backend had been streaming real per-line
  PNGs the whole time. Fixed with a real canvas renderer
  (`wefaxHandleLine()`/`wefaxReset()`), same technique as SSTV's new
  renderer above (each row is its own tiny PNG, decoded via the
  browser's native `Image()`). Unlike SSTV, WEFAX has no VIS-style
  header telling the frontend the final line count up front, so the
  canvas grows in 600px chunks as more lines arrive instead of being
  sized once. Reset on both Start (`decoderStart('wefax')`) and the
  existing `wefax_clear` command.
- **`WefaxDecoder.process_iq()` didn't accept the `sr=` keyword** two
  Full-IQ call sites were already passing it
  (`fax_dec.process_iq(iq_c, sr=48000)` / `sr=DECODER_SR`) — an
  uncaught `TypeError` here would have killed the whole `rx()` bridge
  loop, the exact crash class already fixed for `ft8_dec`/
  `PocsagDecoder` elsewhere in this file. Both sites always pass 48000
  in practice (`DECODER_SR` is 48000), so this was a live but latent
  crash risk rather than a silent wrong-rate bug. Fixed properly (not
  just papered over): `process_iq()` now accepts `sr` and resamples to
  48000 first if it's ever anything else, the same pattern
  `AisDecoder`/`SstvDecoder`/`RttyDecoder` already use. Verified with a
  synthetic test: the exact previously-crashing call
  (`sr=48000`) now completes without error, and a genuinely different
  rate (96kHz) was also tested end-to-end through the resample path to
  confirm it produces output rather than just not-crashing.

---

### Added (2026-07-19) — SSTV (native) and rtl_433 (ISM-band sensors) decoders, closing two gaps found against an OpenWebRX+ feature comparison

User uploaded an "OpenWebRX+ Decoded Signal Types & Backend Decoders"
reference spreadsheet and asked for w033 to be compared against it
(FT8/WSPR and AIS excluded from the comparison — already covered/being
worked on separately). Findings: w033 already matches OpenWebRX+ on
most categories (pagers/selcall via multimon-ng, HFDL/VDL2/ADS-B via
the same dumphfdl/dumpvdl2/dump1090 tools, APRS via direwolf KISS-TCP,
DAB/DAB+ via dab-cmdline, digital voice via DSD/DSD+, PSK31/Olivia/
NAVTEX/etc. via an fldigi bridge) — but had no SSTV and no ISM-band
sensor (rtl_433) decoding at all. Also surfaced, as a side effect of
the comparison: SSTV/FLEX/RDS were previously logged in project memory
as "Phase 2B Tier 2 Complete," but no SSTV code or CHANGELOG entry
actually exists anywhere in this codebase — that memory note was stale
and has been corrected.

User chose to add both gaps to **w033 only** (not w032), keeping w032
as the unmodified main release.

**SSTV** — new `SstvDecoder` class, native Python DSP (no external
binary), following the same FM-discriminate → instantaneous-frequency
→ fixed-timing-scan approach `WefaxDecoder` already uses for HF FAX,
extended to auto-detect the mode via the VIS calibration header
(1900Hz leader / 1200Hz break / 1900Hz leader / 7-bit code + parity,
each bit 1300Hz=0 / 1100Hz=1) and produce RGB (not greyscale) output.
Decodes Martin M1/M2 and Scottie S1/S2/DX in full; Robot 36/72 are
recognised via their VIS code (so the UI shows the detected mode name)
but not decoded — that format's line-alternating, 2:1 vertically
subsampled luma/chroma layout was judged too easy to get subtly wrong
without a captured real signal to validate against, so it's left for a
future, validated pass rather than shipped guessed. Wired into all 5
IQ call sites `WefaxDecoder`/`PocsagDecoder` already use (SDRplay Full
IQ, IQ-Lite, Compact-mode audio, RTL-SDR path, and the two raw-bytes
fallback shims), a new `sstv_enable` WS command (mirroring
`wefax_enable`) plus a `sstv` case in the generic `decoder_enable`
handler, and a `SstvDecoder()` instance added to `deactivate_all_decoders()`.

Frontend: new SSTV tab with a canvas that renders the streamed
single-row PNGs as they arrive (each row decoded via the browser's own
`Image()`, not a hand-rolled PNG parser) — genuinely working image
display, unlike the existing WEFAX tab (see BUGFIX note below, found
while building this).

**VALIDATION CAVEAT**: unlike `AisDecoder`/`AisDecoderDireWolf`
(validated this session against several real captured WAV files),
SSTV has **not** been validated against a real captured SSTV
transmission — none was available. The VIS header detection and
Martin M1/Scottie S1 line decoding were validated against synthetic
test signals (known frequencies fed through the exact same FM-
discriminator/IQ round-trip the real pipeline uses) and decode with
high accuracy there (Martin M1: exact pixel match; Scottie S1: within
~7% due to boundary interpolation at channel edges) — this confirms
the algorithm and timing tables are internally consistent and
correctly implemented, but does **not** confirm real-world SSTV audio
(with actual radio noise, Doppler, clock drift, and AGC behavior)
decodes correctly. Recommend capturing a real transmission (a ham SSTV
net, e.g. 14.230 MHz USB, or an ISS SSTV event) and validating/tuning
against it before relying on this for anything that matters.

Two real bugs were found and fixed during this synthetic validation,
both in the VIS header search logic, before it was considered working:
the lookahead window used to detect the second leader tone was sized
to `leader_min` (150ms) instead of the tone's full nominal length
(300ms), so a genuinely-present leader could never pass its own length
check; and the buffer-trimming fallback (meant only to bound memory on
a channel that's never had SSTV on it) was eroding data out from under
a header that was still validly in-progress across chunk boundaries,
so a real header spanning multiple ~20ms audio chunks could never
complete. Rewritten so the search pointer only advances past a
candidate that's been *conclusively* rejected (rejected with enough
surrounding data to be sure), never past one that's merely incomplete
so far.

**rtl_433 (ISM-band sensors)** — new engine following the exact same
subprocess + UDP-JSON pattern as the existing HFDL/VDL2 engines:
`_find_rtl433()`/`_launch_rtl433()` locate and spawn the `rtl_433`
binary (github.com/merbanan/rtl_433) with `-F udp:127.0.0.1:5558`,
`_Rtl433UdpProtocol` listens and parses each JSON reading (rtl_433's
schema varies per device — temperature/humidity/pressure/wind/rain
fields are surfaced when present, the full raw object is always kept
too), `rtl433_udp_server()` manages the listener + auto-relaunch
watchdog, and new `rtl433_start`/`rtl433_stop`/`rtl433_clear` WS
commands mirror `hfdl_start`/`vdl2_start`. Defaults to a plain RTL-SDR
dongle (`-d 0`); set `rtl433_device` to a SoapySDR driver name (e.g.
`sdrplay`) to use SDRplay hardware instead, same convention
`hfdl_device`/`vdl2_device` already use. Frontend: new tab with a live
reading table, following the HFDL/VDL2 tab layout.

**BUGFIX note (found, not fixed — out of scope for this entry, filed
for awareness)**: while building SSTV's image renderer, discovered the
existing WEFAX tab's frontend never actually renders the fax image —
`wefax_line`'s handler only appends a text log line
(`appendDecode('hf-decode-out', '[WEFAX line N]', ...)`) and never
reads `msg.image_b64` or touches the `wefax-image-container` div, which
sits permanently empty. The backend has been streaming real per-line
PNGs all along; the frontend just never draws them. Also found: two of
the four `fax_dec.process_iq(iq_c, sr=...)` call sites (the two `t==1`
"standard RSPdx" PCM-audio branches) pass a `sr=` keyword argument that
`WefaxDecoder.process_iq(self, iq_c)` doesn't accept at all — the exact
crash class already documented and fixed for `ft8_dec` elsewhere in
this file (an exception here would kill the whole `rx()` bridge loop).
Neither issue affects SSTV (built with its own working canvas renderer
and a `sr`-aware `process_iq`) or anything in this entry; both are
pre-existing in w032 as well and are left for the user to decide how
to prioritize.

---

### Added (2026-07-19) — w033 forked from w032: second AIS front end (Dire Wolf-derived) merged in alongside the rtl-ais port

**w033 forked from w032.** w032 is unchanged and remains a separate,
independent release — this and all following w033 entries apply to w033
only.

Follow-on from the rtl-ais AIS decoder rebuild below, via an explicitly
scoped research/experiment thread ("id like to experiment"): evaluated two
alternative AIS front-end designs against the production `AisDecoder`
using real captured IQ and a ground-truth bit-level diagnostic (spy on
`AisDecoder`'s own confirmed-correct bit stream via its
`_protodec_decode_bit`, isolate the real-signal sub-window around each
confirmed CRC-OK frame, then measure bit-error-rate at every offset/
polarity — this caught bugs a raw pass/fail CRC-OK count alone would have
missed).

- A **Gemini-generated Gardner-timing-recovery decoder** was evaluated,
  patched (missing NRZI decode step, a cold-start deadlock in its cubic
  interpolator, insufficient left-context for its mid-point sample) and
  tested — it never achieved a single CRC-OK frame on real captures after
  fixing every identified bug, so it was **not** carried forward.
- A **Dire Wolf-derived (github.com/wb2osz/direwolf) multi-slicer front
  end** was ported: `demod_9600.c`'s peak/valley AGC, 5-slice parallel
  HDLC decoding (each biased by a different DC offset), and an
  interpolated zero-crossing PLL with an added Type-2 (phase + frequency)
  loop so it tracks the actually-observed symbol rate instead of assuming
  nominal 9600 baud is exactly right. Reuses `AisDecoder`'s own validated
  36-tap FIR and `_protodec_*` HDLC/CRC backend rather than re-deriving
  framing logic.
  - Initial testing found two real, previously-unidentified, rate-
    dependent bugs: (1) Dire Wolf's AGC time constants were tuned assuming
    ~48kHz internal audio — applied unscaled at NEXUS's native 125kHz/
    250kHz capture rates the AGC settles too fast in wall-clock terms
    (fixed via `_dw_rate_scaled_alpha()`); (2) the borrowed 36-tap FIR
    assumes input already resampled to 48kHz/5-samples-per-symbol —
    applied directly to native-rate discriminator output its real-Hz
    bandwidth is proportionally too wide (~2.6x at 125kHz, ~5.2x at
    250kHz), which alone explained why the 250kHz captures were totally
    broken (0 candidates) while 125kHz partially worked (fixed by
    resampling to `AisDecoder.TARGET_SR` before filtering, same order
    `AisDecoder` itself uses).
  - After both fixes, validated against production `AisDecoder` on 3 real
    WAV captures (2 original + 1 brand-new, independently recorded): exact
    CRC-OK match on 2 of 3 (9/9 at 125kHz; 7/7 at 250kHz, on a file that
    was totally broken through every earlier iteration); on the 3rd (a
    low-amplitude, `max|iq|=0.008` capture) it found 13 CRC-OK frames / 8
    unique MMSIs vs `AisDecoder`'s 12 frames / 9 MMSIs — 7 MMSIs in
    common, each catching some the other missed. **Not** a strict
    superset of `AisDecoder` on its own.

Shipped to `w033_NEXUS.py` as a new `AisDecoderDireWolf` class, running
**alongside** `AisDecoder` (not replacing it) — both feed the same
`_ais_update_vessel()`/`ais_vessels` merge-by-MMSI path the UDP/aisstream.io
sources already share, tagged `decoder_source='direwolf'` vs `'native'` so
the frontend can show which decoder(s) confirmed each vessel. Re-validated
the merged pair (extracted directly from the actual `w033_NEXUS.py`, not
the research scratch files) against all 3 real captures: the **merge beats
either decoder alone on every file** — e.g. on the 3rd (fresh) capture,
`AisDecoder` alone found 9 unique MMSIs and `AisDecoderDireWolf` alone found
8, but the merge found **10**, confirming the two front ends genuinely
catch different marginal-SNR frames rather than one being a strict subset
of the other. `aisstream.io` integration untouched throughout.

Both decoders share `ais_dec`'s existing `ais_active` on/off gate at the
one Full-IQ AIS call site (`w033_NEXUS.py`, SDRplay Full IQ branch) — a
single AIS on/off switch for the user, not two separate ones — and both are
reset together whenever AIS is (re-)enabled.

---

### Changed (2026-07-19) — Native AIS decoder rebuilt from scratch as a faithful rtl-ais port; AIS-catcher bridge removed entirely
User directive after two AIS-adjacent crashes surfaced this session (the
`PocsagDecoder`/`AisCatcherBridge.feed_iq()` crash-class fixes below): *"strip
out the ais decoder completely, and rebuild from scratch ... if a better
solution is to implement a known sourcecode that works then do so, but do not
use ais catcher."* Both the previous from-scratch native `AisDecoder` (energy-
gated burst segmentation + Gaussian-matched filter + bang-bang PLL + a batch/
rescan HDLC frame-finder) and the `AisCatcherBridge` subprocess wrapper added
2026-07-18 (see below) are now gone completely — no external AIS-catcher
dependency remains anywhere in NEXUS, backend or frontend.

In their place, `AisDecoder` is rebuilt as a near-literal Python port of
**rtl-ais** (github.com/dgiardini/rtl-ais, GPL v2 — Ruben Undheim & Heikki
Hannikainen 2008, later AISDecoder/AISHub fork), the mature, decade-old,
widely-deployed RTL-SDR AIS receiver, rather than another from-scratch design:

- **receiver.c's 36-tap fixed receive FIR** (exact published coefficients)
  applied to the FM-discriminated signal before bit-slicing.
- **receiver.c's fixed-point zero-crossing PLL** bit-sync + inline NRZI
  decode, with rtl-ais's own tuned constants unchanged (`pllinc = 0x10000/5`,
  nudge divisor 16).
- **protodec.c's streaming HDLC state machine** (`ST_SKURR`/`ST_PREAMBLE`/
  `ST_STARTSIGN`/`ST_DATA`/`ST_STOPSIGN`), including its exact bit-destuffing
  logic and its CRC-via-magic-residual check (pack payload+FCS together,
  standard CRC-16/X.25, valid iff the result equals the fixed residual
  `0x0f47`) — ported bit-for-bit rather than re-derived.
- Runs as one continuous streaming receiver with no burst/energy gating,
  matching rtl-ais's own always-on model (its framing state machine + CRC
  check reject noise on their own; no separate squelch layer needed).

This is architecturally the **same non-coherent FM-discriminator family** as
the old design, not a coherent detector like AIS-catcher — the value here is
a far more battle-tested, proven implementation of that family (real
deployed fixes and tuned constants), not a sensitivity-improving
architecture change. rtl-ais's own NMEA-sentence text generation
(`protodec_getdata`/`protodec_generate_nmea`) was deliberately **not**
ported: once a frame passes the new CRC check, its raw destuffed payload
bits are handed to NEXUS's existing, independently-validated
`_ais_bits_to_bytes()` → `_ais_bytes_to_sixbit_ascii()` → `_ais_decode_payload()`
pipeline, unchanged from before.

**aisstream.io integration is completely untouched** — the background
WebSocket client, key storage/load/save, persistent vessel store, and its
GUI key-entry row all remain exactly as they were; only the RF-side native
decoder and the AIS-catcher bridge were touched.

**Validated** against two real captures used throughout this session's AIS
work (`SDRconnect_IQ_20260717_203346_161975000HZ.wav`, 30.5s @ 125kHz;
`SDRconnect_IQ_20260718_110222_162025000HZ.wav`, 30.7s @ 250kHz), run through
the actual production `AisDecoder` code (extracted verbatim into a standalone
harness) fed in packet-sized chunks: 9–11 CRC-OK frames per file across
5ms–whole-file chunk sizes (consistent, real MMSIs recovered across all
chunk sizes tested — not noise), msg types {8, 10, 12}. As expected, this
does not close the long-message-type (1/2/3/4/5/18/24, Class A/B position
reports) gap versus AIS-catcher's coherent detection — that was never the
goal of this rebuild — but the candidate-to-CRC-OK hit rate is markedly
better than the old design's noise-dominated frame-finder (most detected
candidates now pass CRC, vs. the old design's ~98% noise-triggered false
positives noted 2026-07-17).

Removed: `AisCatcherBridge` class, its `feed_iq()`/`start()`/`stop()`/
`get_status()` methods, its Full-IQ call site, WS commands
`ais_catcher_bridge_start`/`_stop`/`_status`, its shutdown-cleanup call, and
the frontend's AIS-catcher toggle row + `aisCatcherBridgeToggle()`/
`_aisCatcherBridgeRenderStatus()` JS + `aiscatcher_bridge_status` WS case +
its status-request on connect.

### Fixed (2026-07-19) — Starting POCSAG crashed the entire SDRConnect bridge (waterfall/spectrum "blank, then frozen")
User report: "when i start the pocsag decoder the waterfall and spectrum go
blank, then reappear frozen." Confirmed via the user's own terminal log —
this was a hard crash, not a UI glitch: `PocsagDecoder.process_iq()` had no
`sr` parameter at all, but three call sites (the `t==1` PCM-audio branch,
the Full IQ `_fiq_c` branch, and the IQ-Lite branch) called it as
`poc_dec.process_iq(iq_c, sr=...)` — every sibling decoder (`cw_dec`,
`rtty_dec`, `fax_dec`) had long since been updated to accept `sr=` as part
of a uniform calling convention; `PocsagDecoder` was simply never updated
to match. The instant POCSAG's Start toggle went active, the very next
packet raised `TypeError: PocsagDecoder.process_iq() got an unexpected
keyword argument 'sr'` inside `asyncio.gather(rx(), tx())` in
`sdr_bridge()` — an unhandled exception there kills the *entire*
SDRConnect bridge connection, not just POCSAG's own output, which is why
the whole waterfall/spectrum went blank rather than just POCSAG failing
quietly. The outer reconnect-with-backoff loop then reconnects 5 seconds
later, briefly shows live frames again while it re-negotiates the stream,
and hits the identical crash the instant the next packet reaches
`poc_dec.process_iq()` (since `poc_dec.active` was never reset to `False`
by the crash) — an endless blank/flicker/freeze cycle for as long as
POCSAG stayed toggled on, exactly matching the reported symptom.

**Fix:** `process_iq()` now has a real `sr` parameter (default `48000`,
preserving the two call sites that never passed one), and actually uses it
in `samples_per_bit` instead of a hardcoded `48000` regardless of the real
rate a caller passed. Also capped `_get_bit_power()`'s Goertzel input at
`GOERTZEL_MAX_N = 2000` samples (decimated down from whatever arrives) as
a secondary defensive fix — Full IQ mode can hand this tens of thousands of
raw samples per call, and `_get_bit_power()` → `_goertzel_power()`
allocates a fresh `np.arange()`/`np.exp()` reference array sized to the
full input on *every* call with no caching, twice per packet (mark +
space); harmless at typical packet sizes but capped now so it can't become
its own, much smaller, source of loop lag.

### Fixed (2026-07-19) — "SDRConnect"/"Full IQ (USB direct)" status badges stayed green after disconnect
Reported via the community wall (Ash Nallawalla, Windows 11, w032): the
`rspdx-strip`/`nrsp-strip` badges (and the underlying `DS.device_type` they
key off) were only ever updated inside `applyState()`, which only runs when
a live `state` message actually arrives from the backend. There was no code
path that hid them again on disconnect, so once shown they stayed frozen on
whatever they last said — even with SDRConnect.exe fully closed and
`setConnected(false)` correctly flipping the *main* connection dot/label to
OFFLINE the whole time. Confusing symptom: the primary indicator correctly
read OFFLINE, but these two secondary badges kept reading "connected"
because nothing ever told them the connection was gone, making it look like
NEXUS had a live SDRConnect link with zero data flowing rather than simply
no connection at all.

**Fix:** `setConnected(false)` now explicitly hides `rspdx-strip` and
`nrsp-strip` and clears `DS.device_type`, so a genuine disconnect always
resets these badges to neutral — they can only go green again once a fresh
`state` message actually arrives on a new connection.

### Added (2026-07-18) — AIS-catcher bridge: real external decoder as a second AIS option
Deep investigation this session confirmed the native AIS decoder has a genuine
architectural sensitivity gap: it only ever recovers short message types (8,
10, 12) and never the long ones (1, 2, 3, 4, 5, 18, 24 — including Class A/B
position reports, the dominant real-world traffic), because it demodulates via
FM discrimination (non-coherent detection), which is well-established in
communications theory to be several dB less sensitive than coherent detection
performed directly on the complex IQ domain. A from-scratch Python port of a
Gardner timing-error-detector replacement, and later a faithful port of
AIS-catcher's own coherent multi-phase-bank detector (`PhaseSearchEMA`),
were both prototyped and validated against real captured IQ this session —
the coherent-detector port was proven algorithmically correct against a
synthetic known-bit GMSK signal, but real-world performance still fell short
of AIS-catcher's own binary (likely due to AIS-catcher's proprietary matched-
filter tap coefficients not being reproducible from the fetched source alone).
Rather than continuing that open-ended DSP port, added `AisCatcherBridge`: a
class that runs the real, free, open-source AIS-catcher binary
(github.com/jvde-github/AIS-catcher) as a subprocess, fed with NEXUS's own
live Full-IQ stream over a pipe (no second SDR/dongle needed, and no
conflict over exclusive SDR access).

- **Single-channel constraint handled in software**: NEXUS/SDRconnect only
  ever captures one AIS channel at a time (161.975 or 162.025 MHz, ≤31.5kHz
  bandwidth) — it cannot capture both AIS1+AIS2 simultaneously the way a
  dedicated AIS-catcher+RTL-SDR setup normally would. AIS-catcher's channel
  filters assume a virtual 162.000MHz reference DC with channel A at −25kHz
  and channel B at +25kHz from that point (confirmed empirically this
  session: a 162.025MHz-centered capture decoded zero messages through
  AIS-catcher until frequency-shifted, then decoded ~80 real messages
  including position reports once corrected). `AisCatcherBridge.feed_iq()`
  continuously re-centres the single tuned channel to that virtual
  162.000MHz reference in software (a pure complex-multiply frequency
  shift, no extra bandwidth needed) before handing samples to AIS-catcher's
  default dual-channel (`-c AB`) scan — the real content lands in whichever
  of the two ±25kHz slots matches the actual tuned channel.
- Feeds AIS-catcher via `-r CF32 stdin -s 200000 -o 2 -u 127.0.0.1 10110`
  (raw CF32 stdin, resampled to 200kHz — safely inside AIS-catcher's
  documented 96K–12288K sample-rate range), and its NMEA output lands on
  the same UDP:10110 port NEXUS's existing `_AisUdpProtocol` already
  listens on, so decoded vessels merge into `ais_vessels` exactly like any
  other UDP feed (tagged `decoder_source='udp'`, same 🛰️/⚡ tagging added
  earlier this session).
- New WS commands `ais_catcher_bridge_start` / `_stop` / `_status`, and a
  toggle row in the AIS tab ("AIS-catcher (external decoder)") — independent
  on/off from the native decoder's own Start/Stop, so both can run
  side-by-side for direct comparison, which was the user's original request
  at the start of this investigation.
- Requires AIS-catcher installed separately and on `PATH`; the bridge
  detects common install locations (Homebrew, Program Files, etc.) and
  surfaces a clear "not found" toast/status if it isn't available, same
  pattern as the existing `MultimonDecoder`/`dumphfdl`/`dumpvdl2` subprocess
  wrappers.
- Native `AisDecoder`'s underlying sensitivity gap remains open (task
  tracked separately) — this bridge is the pragmatic path to full message-
  type coverage in the meantime, not a fix to the native decoder itself.

### Fixed (2026-07-18) — REC IQ-mode "Saved" toast never showed the sample rate
`rec_stopped` already carried `sample_rate` (see `_rec_stop_and_report()`) but
the toast only rendered duration and file size, so anyone needing the exact
rate for an external tool (e.g. feeding a `.cf32` capture into AIS-catcher,
which requires `-s` to match exactly) had to go dig through terminal
scrollback for a `sr=...` log line instead. Toast now shows it directly:
`Saved: <path>  (12.3s, 4567KB, 50000Hz)`.

### Added (2026-07-18) — AIS RF-overload diagnostic + reference-decoder comparison tagging
Two additions to help isolate why the native AIS decoder's `msg_types`
histogram was only ever showing 8/10/12 (binary/inquiry/safety) and never
1/2/3/18 (Class A/B position reports) despite confirmed nearby real vessel
traffic (VesselFinder cross-check):

1. **Clip/overload counter** — `AisDecoder` now tracks `clip_samples`,
   `total_samples`, and `max_abs_iq` on the raw incoming IQ chunk (never
   the rolling buffer, so overlapping scan windows can't double-count),
   surfaced as `clip%=` and `max|iq|=` in the periodic `[AIS-DIAG]` log
   line. Tests the theory that a too-high rfgain setting is clipping/
   intermodulating the ADC specifically on the strongest, most frequent
   signals near the receiver -- which would be exactly the Class A/B
   position-report traffic from nearby moving vessels -- while weaker,
   less frequent base/binary/safety messages survive untouched. A dropping
   `clip%` alongside `msg_types` finally showing 1/2/3/18 after reducing
   rfgain would confirm this without needing any decoder code change.

2. **`decoder_sources` vessel tag** — every `decoded` dict passed to
   `_ais_update_vessel()` is now tagged `decoder_source: 'native'` (from
   `AisDecoder._decode_segment()`) or `'udp'` (from
   `_AisUdpProtocol.datagram_received()`, i.e. an external decoder like
   AIS-catcher feeding NEXUS's existing UDP:10110 listener). Both sources
   accumulate into `vessel['decoder_sources']` rather than overwriting, so
   a vessel decoded by only one path stays visibly distinguishable from
   one decoded by both. Frontend: MMSI cell shows 🛰️ for udp-only (with a
   tooltip explaining NEXUS's own decoder never recovered that frame) and
   ⚡ when both agree -- no tag at all for the default native-only case, so
   normal single-decoder operation is visually unchanged.

   Context: NEXUS's own antenna/SDR is only reachable over SDRConnect's
   WebSocket (nRSP-ST is not a locally-hardwired dongle on this machine),
   so a live dual-decoder test isn't possible via a splitter + second
   dongle. The intended comparison path is file-replay: capture Full IQ
   with the existing REC feature (already writes AIS-catcher-compatible
   CF32, see `_rec_write_iq()`), then feed that exact file through
   AIS-catcher (`AIS-catcher -r <file> -ga FORMAT CF32 -s <rate> -u
   127.0.0.1 10110`) so it decodes into the same `ais_vessels` table via
   the pre-existing UDP path -- no new NEXUS code required for the
   comparison itself, only the tagging above to make the result legible.

### Removed (2026-07-18) — VesselAPI integration (user request: "not using it anymore")
Deleted the entire VesselAPI per-MMSI REST lookup path: key load/save
helpers, the 90-day expiry checker, the persistent MMSI store and its
150-call budget tracker, `_ais_lookup_poller()`, the three GUI key-management
WS commands, and the matching frontend key-entry panel/warning banner/
`name_source: 'lookup'` UI branches. aisstream.io is now the sole online
vessel-enrichment source. `.vesselapi_key.json`, `.vesselapi_call_count.json`,
and `ais_mmsi_store.json` are no longer read or written by NEXUS -- safe to
delete manually if present from a previous run. Also updated: build script/
`.spec` security guards (previously checking for a bundled VesselAPI key,
now checking for aisstream.io's) and the User Manual/Troubleshooting docs
(section 6.9a rewritten for aisstream.io; docx/pdf rebuilt and copied to
`docs/word/w032/` and `docs/pdf/`).

### Added (2026-07-18) — MMSI plausibility filter (reject impossible identities)
Prompted by a user-supplied VesselFinder screenshot showing a real, nearby,
actively-transmitting vessel (MMSI 316003140, a validly-assigned Cayman
Islands MID) completely absent from NEXUS's own 38-vessel list, while most
of what NEXUS WAS tracking had MIDs that cannot correspond to any real
registered station at all under the ITU numbering scheme (e.g. 119xxxxxx,
120xxxxxx, 848xxxxxx, 790xxxxxx -- all outside the 201-775 range assigned
to ship MIDs, confirmed against navcen.uscg.gov). Added `_ais_mmsi_plausible()`
and gated `_ais_update_vessel()` on it, so an MMSI failing this check is
never added to the vessel table at all, regardless of message type or CRC
status. Deliberately narrow: only validates the plain-ship-MMSI and AIS-AtoN
(`99MIDxxxx`) shapes against the 201-775 range -- doesn't attempt to
validate every special-purpose prefix (group ship, coast station, SAR
aircraft, SART/MOB/EPIRB), to avoid false-rejecting a legitimate but rarer
category. This does not fix the underlying question of WHY these implausible
MMSIs are being produced in the first place (still under investigation --
see next entry); it only stops them from cluttering the displayed list.

### Fixed (2026-07-18) — aisstream.io: "no close frame received or sent" every ~5 seconds
A second, separate bug discovered immediately after the SSL fix above went
live: every connection died again after roughly 5 seconds with
`AIS: aisstream.io connection error: no close frame received or sent`, in a
tight endless reconnect loop -- meaning the connection never stayed open
long enough to receive anything, independent of whatever else was wrong.
Root cause: wrapping `ws.recv()` in `asyncio.wait_for(..., timeout=5.0)` to
periodically check whether a resubscribe was due, even with no incoming
traffic. Cancelling a pending `recv()` this way is a known problem with the
`websockets` library -- the cancellation doesn't always cleanly abort the
underlying read, leaving the connection's internal state corrupted, which
then surfaces as this exact error on the next read or write. The failure
timing (consistently ~5s after every single connect, matching the timeout
value exactly) was the tell. Fixed by never cancelling `recv()`: a separate
concurrent task (`_periodic_resubscribe()`) now drives the resubscribe timer
on its own 5s loop, independent of the main receive loop, which does a
plain, uninterrupted `await ws.recv()`. The periodic task is cancelled
cleanly in a `finally` block when the connection closes for any other
reason.

### Added (2026-07-18) — TEMPORARY: known-active test MMSI for aisstream.io receive diagnostics
After both bugs above were fixed, a live restart confirmed connection and
subscription both now succeed (no errors), but `received=0 matched=0` on
every periodic check across ~1 minute and two subscription refreshes (1
then 8 MMSIs). Not necessarily still broken -- plausible this specific set
of MMSIs (several confirmed non-standard/invalid MIDs, the rest only ever
seen locally via binary/safety messages) just has nothing being relayed by
any other station in aisstream's network. To tell "pipeline broken" apart
from "these specific vessels are quiet," added
`AIS_AISSTREAM_DIAG_TEST_MMSI` ('368207620', a real always-active vessel
lifted from aisstream.io's own documentation example) to every
subscription alongside the user's real tracked MMSIs, plus a distinct
`AIS-DIAG-TEST` log line that fires the moment any data for it arrives --
independent of the normal apply-message vessel-membership gate, so it
proves receipt even though this MMSI is never added to the displayed
vessel table. **Explicitly temporary** -- remove `AIS_AISSTREAM_DIAG_TEST_MMSI`
and its two use-sites (search the name) once the pipeline is confirmed
working or the investigation concludes it's a coverage/data-availability
issue rather than a bug.

### Fixed (2026-07-18) — aisstream.io: SSL CERTIFICATE_VERIFY_FAILED on every connection
The `websockets` import fix below (necessary but not sufficient) let the
next restart surface a second, unrelated bug on every single attempt:
`[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get
local issuer certificate`. Same root cause as the existing EIBI/AOKI HTTPS
downloader elsewhere in this file: a python.org-installed Python on macOS
doesn't use the system certificate store by default, so any TLS connection
via the default `ssl` context fails unless the user has separately run
"Install Certificates.command". aisstream.io's `wss://` feed is the first
*encrypted* WebSocket connection anywhere in this file -- `sdr_bridge()`'s
own `websockets.connect()` only ever talks to a local, unencrypted `ws://`
endpoint (SDRConnect), so this class of bug had never come up in AIS work
before. Fixed the same way already established for EIBI/AOKI: build an
explicit SSL context with `verify_mode = ssl.CERT_NONE` and pass it to
`websockets.connect(..., ssl=ctx)`, rather than pulling in a new dependency
(e.g. `certifi`) for one connection.

### Added (2026-07-18) — aisstream.io received/matched message counters
User report after the `websockets` NameError fix below: 40+ tracked vessel
MMSIs, still nothing pulled from aisstream.io. NEXUS runs from source in
this environment (no file logging active -- see MMSI decode notes above),
so the only diagnostic channel is a live terminal paste, and the existing
logging couldn't tell "still not connecting" apart from "connecting and
subscribed fine, but aisstream.io genuinely has no data for any of these
MMSIs" (a real possibility -- several of the tracked MMSIs turned out to
have MIDs outside the ITU-assigned 201-775 range, meaning they're not
standard registered ship identities at all, per the earlier "MMSI decoded
incorrectly?" investigation). Added `recv_count`/`match_count` counters
that piggyback on the existing periodic resubscribe log line, so the next
terminal paste shows `(received=N matched=M since last check)` alongside
the subscription-updated message -- N=0 means the connection/subscription
is still broken; N>0 with M=0 means aisstream.io is alive and subscribed
but has nothing on these specific MMSIs.

### Fixed (2026-07-18) — aisstream.io never actually connected: `websockets` module not imported
Terminal output after a restart showed the real, previously-invisible root
cause: every single connection attempt logged
`AIS: aisstream.io connection error: name 'websockets' is not defined`. The
`websockets` package is imported elsewhere in this file (`sdr_bridge()` for
the SDRConnect link, and the browser WS server), but only as a **local**
import inside those specific functions -- it was never imported at module
scope, so `_aisstream_client()` (a separate top-level function) had no
`websockets` name available to it at all. This meant the subscription-window
fix below, while a real and necessary fix, could never have taken effect on
its own -- the code was raising a `NameError` before it ever got far enough
to hit that logic. Fixed by adding a local `import websockets` at the top of
`_aisstream_client()`, matching the existing pattern used elsewhere in the
file. Confirmed via terminal log that both bugs needed fixing together;
this was the one actually blocking every connection attempt end-to-end.

### Fixed (2026-07-18) — aisstream.io key configured but nothing ever came through
User report after adding a key and starting AIS: the panel showed zero
aisstream.io activity at all, no matter how long it ran. Root cause: the
subscription-refresh logic added `_resubscribe_if_due()` `return`ed
immediately whenever the wanted-MMSI list came out empty -- which it
always does on the very first check of every session, since `ais_vessels`
starts empty (`ais_stop` clears it) and nothing's been RF-decoded yet at
the moment the connection opens. aisstream.io requires a subscription
message within 3 seconds of connecting or it closes the connection outright
-- so NEXUS was sending nothing in that window on essentially every
attempt, getting disconnected every time, and retrying forever without
ever once successfully subscribing. Invisible from the outside: the
connection attempt, failure, and backoff all happened silently (only a
`log.warning` on the connection-error path, easy to miss without watching
the terminal continuously).

Fixed with two changes together: (1) always send a subscription within the
window -- omitting `FiltersShipMMSI` entirely (rather than sending an empty
list, whose "match nothing" vs. "no filter" semantics aren't documented)
when there's nothing to filter on yet, which subscribes unfiltered to
aisstream.io's entire global feed until NEXUS has RF-decoded at least one
real MMSI to narrow it down to; (2) `_aisstream_apply_message()` now
ignores any MMSI not already present in `ais_vessels`, so that brief global
firehose (~300 msg/s per their docs) gets silently discarded instead of
flooding the vessel table with thousands of unrelated ships -- this is what
makes sending an unfiltered subscription safe at all. Also removed the
normal 30s resubscribe throttle specifically during this "no real filter
sent yet" bootstrap window, so the unfiltered period lasts only as long as
it takes NEXUS to decode its first vessel (typically seconds) rather than
up to a full 30 seconds every time.

### Added (2026-07-18) — aisstream.io resolved MMSIs now persist across sessions
Follow-up to the aisstream.io integration below (same day): user question
("is the data persistent, so eventually it will only have to check for
vessels that are new") exposed a real gap -- `_aisstream_apply_message()`
only wrote into the in-memory `ais_vessels` dict, which `ais_stop` clears
and a restart wipes entirely, so a previously-resolved vessel would need
re-subscribing (and re-waiting for aisstream.io to send its data again)
every session, unlike VesselAPI's results which already survive restarts
via `ais_mmsi_store.json`.

Added a parallel persistent store, `ais_aisstream_store.json`, but
deliberately NOT a shared one with VesselAPI's -- only FIXED/durable
fields ever get written to it (name, callsign, ship_type, destination,
and lat/lon *only* for base stations/AtoN, which are fixed infrastructure).
A moving vessel's position/speed/course is never persisted here: that data
goes stale within minutes, and blindly replaying a week-old "current
position" on a later sighting would be actively misleading, unlike a
ship's name which essentially never changes. `_ais_update_vessel()` (the
RF-decode path) now checks this store as a second free hit alongside the
existing VesselAPI one; `_aisstream_client()` checks it before including
an MMSI in the next subscription refresh, so an already-resolved vessel
neither re-touches the network nor wastes one of the 50 filter slots that
a genuinely new, still-unknown MMSI could use instead.

### Added (2026-07-18) — aisstream.io live-feed cross-reference (second AIS enrichment source)
Follow-up to VesselAPI's lookup exhausting its 150-call free-tier budget
(previous entry) with zero vessels resolved -- traced to VesselAPI being a
per-MMSI *commercial vessel registry* lookup, while everything NEXUS's own
antenna has decoded so far (types 8/10/12) tends to come from senders that
simply aren't in that kind of registry (buoys, AtoN, safety/binary
broadcast systems). aisstream.io is a different shape of service: a free
(beta) WebSocket feed aggregating live AIS traffic from thousands of
contributed receivers worldwide, with no lifetime call cap. Added as a
second, independent enrichment source (`_aisstream_client()`), alongside
VesselAPI rather than replacing it -- either, both, or neither can be
configured.

Implementation: one persistent WebSocket connection to
`wss://stream.aisstream.io/v0/stream`, subscribed with a world bounding box
plus `FiltersShipMMSI` set to whichever up-to-50 MMSIs NEXUS is currently
tracking without a name or position (their own hard limit on that filter);
the subscription is periodically refreshed (every `AIS_AISSTREAM_RESUB_SECS`)
by resending it, since aisstream.io documents that as swap-and-replace
rather than merge. Parses `PositionReport`/`StandardClassBPositionReport`/
`ExtendedClassBPositionReport` (position/speed/course/heading/status),
`ShipStaticData`/`StaticDataReport` (name/callsign/type/destination),
`BaseStationReport` and `AidsToNavigationReport` (tagged `station_type`,
same non-ship treatment as the native type-4 decoder above) into the same
`ais_vessels` dict the RF decoder and VesselAPI both write to -- so a
vessel resolved by any one source shows up complete regardless of which
one supplied which field. Names/positions sourced this way are tagged
`name_source: 'aisstream'` (📡 in the UI) so they read as "another receiver's
live decode", distinct from VesselAPI's 🌐 ("static registry lookup") and
plain RF-decoded fields (no tag).

Same GUI key-entry pattern as VesselAPI (env var `DARKSKY_AISSTREAM_KEY` or
a local `.aisstream_key.json`, pasteable from the AIS Maritime panel) --
new `ais-aisstream-key-config` block sits directly under the existing
VesselAPI one, wired through the same `ais_key_status` message shape now
carrying a `provider` field (`'vesselapi'` or `'aisstream'`) so one
frontend handler (`_aisRenderKeyStatus()`) serves both instead of a
near-duplicate copy.

### Added (2026-07-17) — AIS Base Station Report (type 4) decoding + raw msg-type diagnostic
Live-testing session after the Full IQ stream got unstuck (see the
"AIS decoder shows no vessels" investigation below this entry): with real
frames now flowing (500+ CRC-OK, 47+ vessels), every single decoded/counted
message was type 8 (binary broadcast), 10 (UTC/date inquiry), or 12
(addressed safety-related) — none of which carry name, position, speed, or
course per the ITU-R M.1371 spec, so the vessel table filled with MMSI-only
rows. That part is correct, documented behaviour (see the DIAG comment in
`_decode_segment()`), not a bug. The `msg_types` histogram total also didn't
add up to `frames_crc_ok` (e.g. 482 CRC-OK frames vs. only 306 counted),
which initially looked like message types silently falling through
`_ais_decode_payload()`'s `else: return None`. Added a second counter,
`all_msg_type_counts`, that tags every CRC-OK frame's real msg_type
regardless of whether the payload parser recognizes it, now included in
the periodic `[AIS-DIAG]` log line — but a live restart with it running
showed the gap is actually just `frames_crc_ok` counting re-detections of
the *same* frame across overlapping burst windows before the
already-existing dedup (`_seen_frame_hashes`) drops them, not missing
message types — `all_msg_type_counts` and `msg_types` track each other
exactly once dedup is accounted for. Worth keeping the counter anyway:
it's the direct way to answer "what's really on the air here" instead of
guessing, next time the traffic mix looks suspicious.

BUGFIX (same day, caught before shipping): the first cut of
`all_msg_type_counts` read `payload_bytes[0] >> 2`, silently assuming
MSB-first bit order within a byte — but `_ais_bits_to_bytes()` packs
LSB-first (see its own docstring), so that pulled out a meaningless mix of
bits 2-7 instead of the real msg_type. It happened to look self-consistent
in a live test because msg types 8/10/12 all share the same top two bits
(all in the 001xxx range), so the remapping was accidentally bijective for
exactly the traffic seen — but would have mislabeled anything else,
including the type-4 traffic this same fix was added to surface. Fixed by
reading msg_type off the already-correct `sixbit_str` (same value
`_ais_decode_payload()` itself computes via `get_uint(0,6)`) instead of
re-deriving bit order by hand.

Also implemented type 4 (Base Station Report) itself — shore AIS base
stations repeat it every ~10s, and it was the only message this common
with a fully-specified, simple layout (168 bits, same length family as
1/2/3/18) that wasn't handled at all. Decodes MMSI + position (lon/lat at
bit offsets 79/107 — different from mobile stations' 61/89 because the UTC
timestamp fields sit where nav-status/SOG normally do) and tags the vessel
record `station_type: 'base'` so it doesn't get merged with real ship data.
Frontend: base-station entries now render as a small grey square marker
(not the ship arrow — they have no heading) and read "Base Station"
instead of "Unknown" in the vessel list, map popup, and detail modal.

### Fixed (2026-07-17) — AIS decoder showed no vessels despite Full IQ mode selected
Live-testing the DSP rework below in the running app (not just the offline
validation capture): the AIS Maritime panel showed "No vessels decoded yet"
indefinitely, "FULL IQ" highlighted in the UI, AIS toggled active, and a
real signal visible on the waterfall at 161.975/162.025MHz. The `[AIS-DIAG]`
log line (frames_seen/frames_crc_ok/msg_types, gated on native-decoder
calls) never appeared even once across the entire log history, despite AIS
having been active for many minutes at a time. Root cause, found in the
running backend's own log rather than the code: NEXUS had correctly sent
SDRConnect a `set_stream_mode: 'Compact' → 'Full IQ'` request and updated
its own UI accordingly, but SDRConnect never actually started emitting
type-2 (Full IQ) frames afterward — the per-100-frame `SDRConnect frame
types` log line showed only `{1: ..., 3: ...}` (Compact PCM audio +
spectrum) for the entire session, zero type-2 frames. AIS's native decoder
(like every other Full-IQ-only decoder) only runs off type-2 frames, so it
had zero samples the whole time — not a DSP bug, a stream-mode desync
between NEXUS's displayed state and what SDRConnect actually delivered
(same class of issue as the previously-documented SDRConnect Compact-mode
demod-stuck case — SDRConnect's own internal state not responding to an
otherwise-correct API-driven request). Resolution: re-toggling the device
mode in NEXUS (away from and back to Full IQ) got SDRConnect to actually
start streaming type-2 frames; no NEXUS code change was needed for this
part.

### Fixed (2026-07-17) — REC recordings now save to the user's Documents folder
Follow-up to the REC feature below: `REC_DIR` was `os.path.dirname(__file__)`,
which is fine when running from Python source but breaks under a packaged
build — in a frozen `.app`/`.exe` that path resolves inside PyInstaller's
read-only bundle extraction dir (`sys._MEIPASS` on macOS) or an installed
Program-Files-style folder on Windows, neither writable nor a place a user
would think to look for their own recordings. Recordings (both AUD/.wav and
IQ/.cf32) now always save to `~/Documents/DARKSKY NEXUS/Recordings/`
(`Documents\DARKSKY NEXUS\Recordings\` on Windows), created on first use,
regardless of whether NEXUS is frozen or run from source. The actual save
path is still echoed back to the GUI in the `rec_started` WS message, so the
on-screen path is always accurate.

### Reworked (2026-07-17) — AIS front-end DSP overhaul: burst squelch + GMSK-matched filter (2x decode yield)
Follow-up to the REC feature below: once REC could capture raw IQ, it
became possible to record a real 30.5s 161.975MHz AIS session and
cross-validate NEXUS's native decoder against AIS-catcher (a mature
open-source reference decoder) on the *exact same signal* for the first
time. NEXUS decoded far fewer messages, and only two low-information
message types (8, 10) — never any position/voyage reports. Initial
hypothesis was that the zero-crossing PLL bit-sync was the weak link, so
several days were spent building and testing a proper interpolating
timing-error-detector (Gardner TED) to replace it — this was the wrong
target and never shipped. Rigorous testing disproved it conclusively:
a brute-force search trying 20 phase offsets against all 391 candidate
HDLC frames the old pipeline found recovered **zero** additional frames
beyond the 6 the old zero-crossing PLL already got. Bit-sync quality was
never the bottleneck.

Power analysis of those 391 candidates found the real problem: the 6 real
decodes sat at 5.6x–39x the background noise floor, while the other 385
"candidate frames" had *median power at or below the noise floor* — they
were noise-triggered false 0x7E flag-pattern matches, not real AIS
bursts. The old pipeline ran its filters and PLL continuously across the
whole stream with no burst detection at all.

Replaced the AIS front-end with:
- **Burst/energy squelch** — causal sliding-window IQ power detector
  (2ms window, running noise-floor EMA, 6dB threshold) isolates real
  burst windows before any decode is attempted, instead of scanning
  continuous noise. Cut candidate frames from 391 to ~13–17 on the same
  capture.
- **GMSK-matched Gaussian receive filter** (BT=0.5, 63 taps) replacing
  the old generic 5760Hz-cutoff low-pass — shaped to AIS's actual
  modulation instead of a generic anti-alias filter, recovering
  materially more marginal-SNR bursts. BT swept 0.3–0.7 against the real
  capture; 0.5 (not the nominal transmit-side 0.4) gave the best yield.
- **Per-burst DC-mean removal** replacing the old continuously-running
  DC/CFO high-pass tracker — a burst-local bias estimate is more accurate
  than a slow global tracker for a ~30–70ms burst (linear detrending was
  also tried and made things worse — kept the simpler mean-subtraction).
- 15ms of padding either side of each burst gives the resample/filter
  chain time to settle past its startup transient before the region
  that's actually scored — cold per-burst filtering was initially
  *losing* known-good frames purely from filter warm-up until this was
  added.
- The existing zero-crossing PLL is unchanged (proven adequate — see
  above) and the HDLC frame sync/CRC/payload decoder are untouched.

**Validated** against the real 161.975MHz capture (same file used for the
AIS-catcher cross-check), run through the actual production `AisDecoder`
class in small streaming chunks (matching how live IQ arrives): **12
unique decoded messages / 11 MMSIs**, vs. the old design's **6 messages /
5 MMSIs** — roughly 2x, plus message type 12 (safety-related) recovered
for the first time. Still well short of AIS-catcher's full yield on the
same capture (which also does coherent frequency tracking and proper
soft-decision decoding — a larger undertaking than this pass), but a
real, measured improvement with no regressions on the previously-working
6 messages.

Applied identically to w031 and w032 (`_ais_gaussian_lpf_taps()` +
reworked `AisDecoder` class in both `w031_NEXUS.py` and `w032_NEXUS.py`).

### Added (2026-07-17) — REC button now actually records (AUD/IQ modes)
User request: "add a select toggle for demodulated/IQ when Rec is
pressed." Turned up something worth flagging while implementing it: the
REC button has existed in the toolbar for a long time, but `toggleRecord()`
was a pure UI stub — it flipped the icon and popped a toast (misleadingly
claiming "IQ Recording started" regardless of the button's own tooltip,
which said "saves demodulated audio"), but never sent anything to the
backend, and there was no backend recording code at all, for either mode.
Nothing has ever actually been saved by pressing REC until now.
- New **AUD | IQ** pill next to REC — persistent (localStorage), set once,
  every REC press uses whatever's selected. AUD works in any stream mode;
  IQ requires Full IQ device mode (backend rejects the request with a
  toast otherwise, rather than silently writing an empty file).
- **AUD mode:** demodulated audio → WAV file. Tapped from the same `mono`
  buffer already fed to the CW/RTTY/FAX/POCSAG/ACARS decoders in the t==1
  PCM-audio branch.
- **IQ mode:** raw Full IQ → `.cf32` file (interleaved float32 I/Q —
  `np.complex64.tobytes()` *is* CF32, no header). Tapped from `_fiq_i`/
  `_fiq_q` at the earliest point in the Full IQ branch, before any of
  NEXUS's own anti-alias/decimation filtering — i.e. the same raw
  hardware-rate samples SDRConnect delivered, byte for byte. This exists
  specifically so a capture can be replayed through an external decoder
  (e.g. AIS-catcher's `-r` file input with `-ga FORMAT CF32`) for a fair,
  apples-to-apples comparison against NEXUS's own native decoders,
  without needing to fight over exclusive access to a live SDR device —
  came up directly from a real AIS decode-quality investigation this
  session where the actual SDR turned out to be a standalone network
  receiver, unreachable by any second program's local hardware driver.
- Backend: new `rec_start`/`rec_stop` WS commands, `_rec_write_audio()`/
  `_rec_write_iq()`/`_rec_stop_and_report()`. Files save to a `recordings/`
  folder next to the script, named `darksky_rec_<mode>_<timestamp>.wav`
  or `.cf32`. `rec_stopped` reports the saved path, duration, size, and
  sample rate back to the UI as a toast.

### Fixed (2026-07-17) — AIS: VesselAPI lookup was hitting the wrong endpoint entirely, never resolved a single vessel name
Live-tested with a real, correctly-configured key and a healthy 150-call
budget — still zero names, zero SOG/COG/status, zero map markers after
12+ minutes tracking 54 vessels. Checked VesselAPI's actual live API docs
(vesselapi.com/docs/vessels) against what the code was calling and found
two compounding mistakes, both present since the GUI key-entry feature
was first built:
- **Wrong URL:** was `GET /v1/vessels/{mmsi}` (plural, no query param).
  The real endpoint is singular — `GET /v1/vessel/{id}?filter.idType=mmsi`
  — and the `filter.idType` param is required (the same `{id}` slot also
  accepts an IMO number, so the API can't tell which one you're passing
  without it). Every single call 404'd.
- **Wrong response shape:** even reaching the endpoint, the code was
  looking for `vesselName`/`callsign`/`vesselType`/`flag` at the top
  level. The real response nests fields under a `"vessel"` key with
  snake_case names — `name`/`call_sign`/`vessel_type`/`country`.
- Both mistakes were invisible in normal operation: the HTTP failure was
  caught by a blanket `except Exception` and logged at DEBUG level only.
  Added a dedicated `HTTPError` handler that logs any non-404 response
  (401/403 bad key, 429 rate-limited, 5xx outage) at INFO level, so a
  broken integration doesn't go silently unnoticed again — a plain 404
  (vessel genuinely not in VesselAPI's database) stays quiet since that's
  expected and common.
- Reminder: this fixes the **name/callsign/flag** lookup only. SOG, COG,
  and nav status are never sourced from VesselAPI in NEXUS's current
  integration — those only come from decoded AIS position reports (msg
  types 1/2/3/18) off the RF stream itself. If those still show blank
  after this fix, that's the separate `msg_type_counts` RF-decode
  question, not a VesselAPI problem.

### Removed/Fixed (2026-07-17) — Marine/VHF tab: dropped embedded AIS panel, fixed dead channel-list refresh
The Marine/VHF tab is badged ● COMPACT in the Decoders dropdown — its
channel quick-tune list is pure tuning, works on any stream mode, no
decoder of its own. It also used to embed a full AIS Vessels sub-panel
(quick-tune buttons, toggle, vessel list), but that panel is Full-IQ-only
and simply cannot function while the tab it lives in is audio-mode native.
User flagged the mismatch directly: "in audio marine, do we need ais
decoder here?"
- Removed the AIS Vessels panel (buttons, toggle, `#marine-vessel-list`)
  from `tab-marine` entirely. Replaced with a short note plus an **Open
  AIS tab →** button (`showTab('ais')`) for anyone who lands here looking
  for vessel tracking. AIS now lives in exactly one place: the dedicated
  AIS tab.
- **Bugfix found while editing this code:** `showTab()`'s marine case (and
  the page-load init list) called `populateMarineChannels()` — no such
  function exists, only `_populateMarineChannels()` (with underscore) is
  defined. The call was wrapped in `try/catch`, so it silently no-opped
  every time; harmless in practice since the channel list is static and
  was already populated once at page load, but a genuine dead reference.
  Fixed both call sites to use the correct underscored name.

### Added (2026-07-17) — AIS: GUI VesselAPI key entry, so distributed builds never bundle a personal key
Follow-up to the VesselAPI diagnostic below — since the free-tier 150-call
budget is a personal, per-account allowance, it can't be baked into a
build shared with other users. Previously the only way in was
`DARKSKY_VESSELAPI_KEY` (an env var, invisible if NEXUS is launched from
IDLE — see below) or hand-editing `.vesselapi_key.json`.
- New **VesselAPI lookup** field in the AIS tab: paste a key, click
  **Save**, done — no restart needed. Shows live status (`not configured`
  / `configured (…XXXX)`), a **Clear** button, and a direct link to
  generate a free key at dashboard.vesselapi.com.
- Backend: new `ais_set_vesselapi_key` / `ais_get_vesselapi_key_status` /
  `ais_clear_vesselapi_key` WS commands, writing through the existing
  `_ais_vesselapi_save_key()`. Saving a new key also resets the local
  150-call budget counter, since a different key means a different
  VesselAPI account with its own separate allowance — without this, a
  fresh key would be wrongly throttled by whatever count the *previous*
  key had accumulated.
- **Bugfix while wiring this up:** `_ais_lookup_poller()` used to check
  for a configured key exactly once, before entering its loop, and exit
  permanently if none was found at startup — meaning a key added later via
  this new GUI field would never actually be picked up without a full app
  restart. The check now runs every cycle instead, so a freshly-saved key
  takes effect within ~5 seconds.
- **Build scripts now guard against ever shipping a personal key:**
  `build_macOS.sh`/`build_Windows.bat` warn if `.vesselapi_key.json`
  exists locally, and hard-abort the build if any of
  `.vesselapi_key.json` / `.vesselapi_call_count.json` /
  `ais_mmsi_store.json` are found inside the built output — on top of the
  `.spec` files' `datas` lists already being an explicit whitelist that
  never referenced them. Each end user is expected to generate and enter
  their own key via the GUI field above.
- Documented in User Manual section 6.9a and a new Troubleshooting entry.

### Added (2026-07-17) — AIS map: same style picker as the FT8 maps
User request: "in the iq ais decoder pane, add the same map options
pulldown as ft8". Added a CARTO Dark/Light/Voyager, OpenStreetMap, Esri
Satellite picker next to the AIS map, mirroring `changeFt8BridgeMapProvider()`
almost exactly (own provider table, `bringToBack()` on switch so a newly
added tile layer doesn't cover the QTH marker/vessel icons, choice
persisted to `localStorage`).
- Also fixed **while implementing this**: `aisClear()` only ever cleared
  `#ais-vessel-table` (the standalone AIS tab), so clicking Clear from the
  Marine tab left stale rows sitting in `#marine-vessel-list` — same root
  cause as the vessel-list render bug above, just a different call site.
  Now clears both containers.

### Diagnostic (2026-07-17) — AIS vessel table: all-MMSI rows, blank NAME/SOG/COG/STATUS
Follow-up to the VesselAPI note below — SOG/COG/STATUS come from decoded
RF (message types 1/2/3/18), not the online lookup, so this needed its
own investigation. Read through `_ais_update_vessel()`: it only merges
nav/name fields for `msg_type` in (1,2,3,5,18,24). Types 8 (Binary
Broadcast — commonly sent by shore/base stations and AtoN buoys, not just
ships), 10 (UTC/Date Inquiry), and 12 (Addressed Safety Message) are also
decoded by `_ais_decode_payload()` but were never given a merge case —
by design, since those message types genuinely carry no nav/name data in
the base spec — so a vessel entry built from one of those alone will
*permanently* show MMSI-only, with no bug required to explain it, if
that MMSI never also happens to transmit a type 1/2/3/5/18/24 message.
Whether that's actually what's happening (vs. a genuine decode-accuracy
problem in the type 1/2/3/18 path) can't be told apart from the terminal
alone yet, so:
- Added `AisDecoder.msg_type_counts` (a running histogram of every
  successfully-decoded `msg_type`), surfaced in the periodic `[AIS-DIAG]`
  log line as `msg_types={...}`. Next run's terminal output will show
  the actual distribution — if it's dominated by 8/10/12, that's the
  full explanation and no further code fix is needed; if 1/2/3/18 show
  up in real numbers but still produce blank fields, that's a genuine
  bug still to chase down.

### Diagnostic (2026-07-17) — AIS VesselAPI lookup: no visibility into whether it's actually running
User-reported: expected online MMSI-name lookup (VesselAPI) to fill in
vessel names, but every decoded vessel showed MMSI only. `_ais_lookup_poller()`
was already correctly written to no-op silently when no key is configured
(an intentional "opt-in feature, stay out of the way entirely" design) —
but that meant there was no way to tell "not configured" apart from
"configured but nothing resolved yet" just from the terminal log.
- Added an explicit one-time startup log line: `AIS: VesselAPI lookup
  ENABLED` (with the key's last 4 chars, for confirmation without
  exposing the whole key) or `AIS: VesselAPI lookup DISABLED — no
  DARKSKY_VESSELAPI_KEY env var or .vesselapi_key.json found`.
- **Worth knowing if you launch NEXUS from IDLE (Run Module/F5) rather
  than a Terminal:** `DARKSKY_VESSELAPI_KEY` is read via `os.environ` —
  IDLE's process only inherits env vars from the shell that launched IDLE
  itself, not from `~/.zshrc`/`~/.bash_profile` in general, so a key
  exported there can be genuinely set and still invisible to NEXUS when
  run this way. The local keyfile path (see `_ais_vesselapi_save_key()`)
  sidesteps this since it doesn't depend on how the process was launched.
- Separately, and unrelated to VesselAPI: the same live vessel table also
  showed blank SOG/COG/STATUS (not just NAME) for every one of 17
  vessels — those three fields come from decoded RF (message types
  1/2/3/18), not the online lookup, so this points at something else
  worth a closer look if it persists.

### Fixed (2026-07-17) — Marine tab AIS panel: vessel count updated live, list stayed on "Awaiting AIS…"
User-reported (live, immediately after the DC/CFO fix below): the Decoders
> Marine/VHF panel's header correctly showed "AIS Vessels 5 vessels", but
the list underneath it never left its static "Awaiting AIS…" placeholder.
- **Cause:** there are two separate AIS vessel-list containers in the
  page — `#ais-vessel-table`, in the standalone "AIS Maritime" tab
  (`tab-ais`), and `#marine-vessel-list`, in the Decoders > Marine/VHF
  panel (`tab-marine`) most people actually use day to day. Only the first
  one was ever wired to `updateAISDisplay()`. The Marine tab's own vessel
  *count* pill (`#ais-vessels-pill-marine`) was separately, correctly
  wired directly in the `ais_update` message handler — which is exactly
  why the count updated live while the list right below it never did:
  two different code paths, only one of them complete.
- **Fix:** extracted the per-vessel row-building logic out of
  `updateAISDisplay()` into a shared `_aisBuildVesselRow()` helper, and
  `updateAISDisplay()` now renders into *both* `#ais-vessel-table` and
  `#marine-vessel-list` from the same vessel data. Hard-reload the browser
  (Cmd+Shift+R / Ctrl+Shift+R) to pick up this frontend-only fix — no
  Python restart needed.

### Fixed (2026-07-17) — Native AIS decoder: real signal on the waterfall, zero decodes
User-reported (live, 161.975 MHz / CH87B, Full IQ, SDRConnect connected):
AIS toggled on, genuine burst-shaped RF activity visible right on the AIS
channel in the waterfall, yet the vessel table stayed on "Awaiting AIS…"
indefinitely. Investigation found the AIS toggle itself was off going into
the test (0 active decoders) — starting it live confirmed correct tuning,
Full IQ, and real bursts, but still 0 decodes after ~45 seconds.
- **Cause:** `_ais_pll_clock_recovery_nrzi()` slices GMSK bits with a bare
  `x > 0` threshold against the raw FM-discriminator output, assuming the
  signal's frequency deviation is centred exactly on 0 Hz. Nothing in the
  pipeline ever compensated for the small DC bias this threshold is
  actually sensitive to — and AIS/ITU-R M.1371 explicitly allows
  transmitters up to ±500 Hz of carrier tolerance, on top of whatever PPM
  error the receiving SDR's own LO has. That's normally enough to bias the
  discriminator output off true zero and corrupt every zero-crossing
  slicer decision, well before CRC gets a chance to reject anything — this
  was never carried over from the original `ais_decoder_dev.py` proof-of-
  concept, which was only ever validated against a handful of captures
  clean enough not to expose it.
- **Fix:** Added a 1-pole IIR high-pass ("DC/CFO tracker", 75 Hz cutoff at
  the 48 kHz decode grid) in `AisDecoder`, applied after the existing
  receive low-pass and before the PLL slicer, continuously removing slow
  bias while passing the much faster GMSK symbol transitions the slicer
  needs.
- **Also added:** a rate-limited `[AIS-DIAG]` log line (every 5s while AIS
  is active) reporting `frames_seen` vs `frames_crc_ok` vs `vessels` — if
  `frames_seen` stays 0 that points to a deeper frame-sync/PLL problem (or
  genuinely no AIS energy); `frames_seen > 0` with `frames_crc_ok` still 0
  means frame sync is working but bits are still wrong, i.e. this fix
  needs further tuning rather than being the whole story. Check the
  terminal NEXUS was launched from after restarting to pick this up.
- **Requires a Python restart** (backend-only fix) — a browser reload
  alone will not pick this up.
- **Not this:** an unrelated question came up about whether the
  jvde-github/AIS-catcher v0.70 release (an external, separate program
  some users feed into NEXUS via UDP 10110 as an alternative source) might
  help here — it doesn't apply to this issue. It's a different program
  from NEXUS's own native decoder above, and v0.70 itself only touches
  network-layer robustness (rewritten TCP server, bounded output queues,
  a dropped-message counter) plus two unrelated bug fixes (ADS-B callsign
  padding, a CTRL-C hang) — nothing in it changes signal decoding.
- **AIS channel bandwidth, for reference:** confirmed 25 kHz, not
  12.5 kHz — NEXUS's own `aisAutoTune()` already tunes CH87B/88B at
  `bw_hz=25000` ("AIS = 25 kHz channel"), matching the global AIS1/AIS2
  channel spacing under ITU-R M.1371.

### Fixed (2026-07-17) — FT8 INTERNAL quick-tune/Hop mode never actually retuned the SDR
User-reported (screenshot): the FT8 mini-spectrum/waterfall looked wrong
compared to the User Manual's reference screenshot — a single peak near
0 Hz tapering to flat, instead of the expected forest of peaks across the
passband. Follow-up report: pressing an FT8 band quick-tune chip left the
main spectrum/waterfall completely unchanged and put the tuning cursor at
the very left edge of the display. Both turned out to be the same root
cause, confirmed live in the browser.
- **Cause:** `setFTband()` (manual band quick-tune) and `advanceHop()`
  (automated Band Hopping) fired 5 raw low-level SDRConnect `set_property`
  commands back-to-back with no delay — `device_sample_rate`,
  `device_center_frequency`, `device_vfo_frequency`, `demodulator`,
  `filter_bandwidth` — ported directly from the standalone reference
  `websocketft48` tool this panel was originally adapted from. This
  bypasses NEXUS's own `cmd:'tune'` handler entirely, which exists
  specifically because SDRConnect/nRSP-ST needs its demodulator
  re-asserted ~350ms after a genuine LO move or it silently drops the
  retune (see the `cmd == 'tune'` handler in `w032_NEXUS.py`). Confirmed
  live: clicking a band chip updated the VFO digit display, but the LO
  (and therefore the actual received passband) never moved — NEXUS kept
  listening to whatever band it was on before, so the FT8 decoder had
  nothing real to decode, the main display didn't change, and the tune
  cursor rendered off-screen because the VFO frequency was now far outside
  the LO span that never actually updated. Automated Band Hopping had the
  same bug, meaning an unattended multi-band scan never actually changed
  bands on the radio, only in the UI.
- **Fix:** both functions now call `tuneVFO()` — the same proven call
  every other band-change mechanism in NEXUS already uses (WSPR band
  buttons, the Bands panel, quick-tune segments, bookmarks) — instead of
  reimplementing an uncoordinated version of the same thing.
  `device_sample_rate` is no longer force-set on every click either: FT8
  already runs at a fixed 500 kSPS, and forcing a sample-rate change (a
  full stream restart) on every single band click only added more
  settling-time risk for no benefit.
- **Verified live** (RSPdx, Compact mode, 20m): before the fix, 0 decodes
  after several minutes with the LO stuck on the previous band; after the
  fix, switching to 20m and starting the decoder produced 26 decodes /
  26 callsigns / 9 countries within about a minute, with the mini-spectrum
  showing the expected multi-peak shape and the main waterfall correctly
  centred on the new band.

---

### Fixed (2026-07-16, inherited from w031) — SSH Launcher shipped with the developer's own personal connection details
Same fix as w031 — see that CHANGELOG entry for the full write-up. A
different user's screenshot of the Connection Setup screen showed a real
SSH connection attempt (and timeout) against `jon@192.168.1.114`, the
developer's own private home LAN address, hardcoded as the default in
`SSH_DEFAULT_CONFIG`. `ssh_host`, `ssh_user`, and `local_client` now
default to blank instead of the developer's personal values; the SSH
Host/Username input placeholders were also genericised.

---

### Added (2026-07-16) — CW mini-waterfall zoom is now a real "zoom FFT", not a crop
Follow-up to the resolution fix directly below. `DS.cwWfZoom` (the −/+
zoom control above the CW mini-waterfall) used to be purely cosmetic: the
backend always sent the same fixed-resolution bins, and zooming just
cropped and linearly interpolated that same array client-side — adding no
real information, the same "fake zoom" limitation flagged in the earlier
resolution discussion. This is now a genuine zoom, matching the technique
dedicated SDR panadapters (SDR#, CubicSDR, SDRuno) use: since Hz/bin =
sample-rate/FFT-size, a real increase in resolution needs a genuinely
longer observation window, not just more display pixels.
- The frontend now sends the current zoom level to the backend (new `cw_wf_zoom`
  WS command) whenever it changes via `cwWfAdjustZoom()`.
- The backend (`w032_NEXUS.py`, IQ-Lite and Full IQ audio_fft branches)
  scales its FFT size with the requested zoom level (base 4096-pt → up to
  32768-pt at 8×) and runs it over a rolling raw-IQ buffer, rather than the
  fixed 4096-pt overlap-averaged FFT the base (1×) path uses. The result:
  zooming in on the mini-waterfall shows genuinely finer detail, not a
  blurrier crop of the same 512 bins.
- **This is a real trade-off, not a free upgrade:** the STFT uncertainty
  principle (Δf·Δt ≥ 1) means a longer window needed for finer frequency
  resolution is, unavoidably, a longer window in time too — window
  duration grows from ~85ms at 1× to ~683ms at 8×, so the mini-waterfall
  updates more slowly and blurs fast keying transitions more at high zoom.
  This is expected, and matches how real panadapters behave when zoomed in
  — the CW mini-waterfall's job is frequency identification ("where is
  this signal"), not showing individual key-down timing (that's what the
  separate keying/activity scope is for).
- Scoped to IQ-Lite and Full IQ (the complex-IQ paths) — Compact-mode's
  audio_fft is already close to its native resolution at the existing FFT
  size and its audio is already BW-filtered by the time NEXUS sees it, so
  there's comparatively little left to zoom into there; it keeps the old
  crop/interpolate behaviour for now.

---

### Fixed (2026-07-16) — CW mini-waterfall was discarding half its real resolution
User asked how leading SDR apps get sharper waterfalls, which turned up a
genuine inefficiency: the `audio_fft` broadcast (the CW mini-waterfall's,
RTTY tone scope's, and fldigi waterfall's shared data source) computed a
native FFT slice — around 512 bins at ~11.7 Hz/bin for the IQ-Lite/Full IQ
paths (4096-pt FFT on 48kSPS decimated IQ) — then resampled it down to a
fixed 256 bins via `np.interp` before sending it to the browser, and the
browser then re-interpolated those 256 values back up across a ~450px-wide
waterfall canvas. Real data was being thrown away on the way out and
fabricated back on the way in.
- All three `audio_fft` broadcast branches (IQ-Lite, Full IQ, Compact-mode)
  now send their native FFT slice directly, unresampled — the `_AUDIO_FFT_OUT
  = 256` downsample step is removed. This roughly doubles genuine displayed
  frequency resolution on the IQ-Lite/Full IQ paths (Compact-mode's native
  slice was already close to 256 bins, so no meaningful change there).
  Bandwidth cost is negligible (a few hundred extra bytes at 10Hz over a
  local WebSocket).
- No frontend change was needed: `_renderCwNexusWf`, `_renderCwNexusSpectrum`,
  and the RTTY tone scope all already read `bins.length` dynamically rather
  than assuming a fixed 256.
- **Not changed (documented, not fixed):** true zoom on the CW mini-waterfall
  (`DS.cwWfZoom`) still crops and interpolates this same bin array
  client-side rather than re-decimating the IQ and re-running the FFT at a
  lower sample rate for the zoomed span — the technique real "zoom FFT"
  panadapters (SDR#, CubicSDR, SDRuno) use to get genuinely finer resolution
  when zoomed in, not just a smoother-looking crop of the same underlying
  data. Flagged as a follow-up, not implemented in this pass.

---

### Added (2026-07-16) — Build scripts now bundle the docs
Same website feedback that flagged "Windows can't read the document files"
turned up a real gap: neither `build_macOS.sh` nor `build_Windows.bat` ever
copied the Quick Start/User Manual/Troubleshooting PDFs into the built app
at all — there was nothing local to open, on either platform, in any prior
release.
- **Windows:** `build_Windows.bat` now copies `docs/pdf/*.pdf` into a new
  `Docs\` subfolder next to the .exe as a post-processing step (same
  pattern already used for `eibi.csv`/`airports.csv`/etc.). No `.iss`
  change needed — the installer already packages the whole app folder
  (`dist\...\*`) recursively, so `Docs\` is picked up automatically;
  updated its `[Files]` comment to say so explicitly.
- **macOS:** `build_macOS.sh` copies the same PDFs into
  `Contents/Resources/Docs` inside the `.app` bundle (for completeness),
  but more importantly now stages the `.app` together with a top-level
  `Docs/` folder in a new `dmg_staging/` directory before building the DMG,
  so the PDFs are visible immediately when a user opens the DMG rather than
  buried inside "Show Package Contents." Both `create-dmg` and the
  `hdiutil` fallback now build from that staged folder instead of the
  `.app` directly.
- Both scripts warn (non-fatally) and continue if `docs/pdf/` doesn't
  exist at build time, rather than failing the build.
- **Windows installer:** added a new opt-out `docsshortcut` Task to
  `DARKSKY_NEXUS_w031.iss` — checked by default (unlike the existing
  `desktopicon` Task, which stays opt-in) since it directly addresses the
  reported problem, adds a Start Menu → Documentation shortcut pointing at
  `{app}\Docs`. The PDFs are installed either way; this only controls
  whether a shortcut to them is created. No `[Files]` change was needed —
  see above.

---

### Fixed (2026-07-16) — CW SKIMMER/SINGLE toggle could hide itself
User-reported (screenshot, Compact mode): "no toggle visible for single
decode or skimmer." Root cause: the SKIMMER/SINGLE toggle buttons
(`#cw-view-skimmer-btn`/`#cw-view-single-btn`, added 2026-07-15) lived
inside `#cw-skimmer-panel`'s own header — but `_cwApplyDecodeView()` sets
that whole panel to `display:none` whenever SINGLE view is active, which
took the only way back to SKIMMER view down with it. Anyone who ended up
in SINGLE view (a prior session's `localStorage` value, or FLDIGI engine
forcing it) had no UI path back to Skimmer. Moved the toggle out of the
panel it controls and into the tab's persistent header row (next to
Engine/Clear, always visible in both views) — same element IDs, so
`cwSetDecodeView()`/`_cwApplyDecodeView()` needed no logic changes, just a
DOM relocation.

### Not a bug — CW mini-waterfall still BW-limited in Compact mode
Same report also flagged the mini-waterfall as "still effected by bw
settings." Confirmed via the screenshot (COMPACT mode selected in the top
bar): this is the already-documented Compact-mode limitation, not a
regression of the 2026-07-15 wideband-scope fix. That fix's ±3000 Hz
BW-independent scope only applies to IQ-Lite/Full IQ streams, where the
backend computes it from unfiltered complex IQ — in Compact mode
SDRConnect has already band-limited the audio to the selected BW before
NEXUS ever sees it, so there's no wider signal left to show regardless of
span setting (see the Troubleshooting Guide's CW waterfall section).
Switching to IQ Lite or Full IQ gives the true BW-independent view.

---

### Fixed (2026-07-16) — Dark theme secondary text failed WCAG contrast
User feedback (via website): "very difficult to read anything on the screen
with the dark format. Not enough contrast." Measured it — `--muted`
(labels, units, sub-text throughout the app) was `#4a5a6a` on `#0a0c0f`,
~2.8:1 contrast against WCAG's 4.5:1 minimum for normal text. Main body
text (`--text`) was fine at ~13.5:1; this was specifically the dimmer
secondary text. Lightened `--muted` to `#7a8da0` (~5.7:1) in dark theme
only — still visibly dimmer than `--text` so the hierarchy is unchanged,
just actually readable now. Light theme's `--muted` measured ~4.5:1
(right at the cutoff) and was left alone, since the report was specifically
about dark mode.

---

### Docs (2026-07-16) — User Manual + Troubleshooting Guide caught up to code
Two gaps found when auditing docs against recent changes: the User Manual
never mentioned the new "My QTH" map marker (added below), and the
Troubleshooting Guide's "Address already in use" entry still described the
old manual-kill-it-yourself fix, not the automatic self-heal added the same
day. Added a QTH-marker note to the User Manual's map sections and rewrote
the Troubleshooting entry to lead with "usually automatic now," keeping the
manual macOS/Linux/Windows kill commands as the fallback for the (rare)
case where the port is held by something that isn't NEXUS. `w031 Release
Notes.md` also updated with the Windows self-heal fix. Docx/PDF rebuilt for
both.

---

### Fixed (2026-07-16) — Windows port self-heal was a silent no-op
A user (pre-w030 build) hit a hard crash on launch — `OSError: [WinError 10048]`
failing to bind port 8889 — and reported it via the new website Community
Wall feedback form. Root cause: `_free_stale_port()` (added to auto-recover
from a previous NEXUS instance not shutting down cleanly) always shelled out
to `lsof`/`ps`/`os.kill` to find and kill the stale process holding the
port — all Unix-only. On Windows, `lsof` doesn't exist, so the function hit
its own `except FileNotFoundError: pass` and did nothing, meaning Windows
never actually got the self-heal at all — a leftover process (from a crash,
a Task Manager "End Task", or just double-launching the app before the
first instance finished starting — there's no console window on a windowed
build, so there's no visual sign it's already running) just crashed the
next launch outright. Added a Windows branch using `netstat -ano` +
`tasklist` + `taskkill /F`, mirroring the same "only kill things that look
like NEXUS/python" safety check the Unix path already had. Also updated
both HTTP/WebSocket bind-failure log messages, which previously only
printed a macOS `lsof` remedy command, to give Windows users a relevant
"check Task Manager" message instead.

---

### Fixed (2026-07-16) — Skimmer candidate detection now uses real SNR, not display bins
Per the CW decoder evaluation: `_skDetectLoop()` picked candidate frequencies
from `DS.liveBins`, the same per-frame, self-normalizing, log-compressed
array used to draw the visible spectrum — not a stable measurement. Its
"floor + 30" threshold was an arbitrary distance in a unit that rescales to
fit each frame's own peak, with no fixed relationship to real SNR;
`CWSkimmerPool`'s own diagnostic broadcast had already shown candidates it
promoted often sat at 0-1.5dB real SNR against the 8dB a `MorseDecoder`
actually needs to decode — genuinely weak-but-decodable signals could be
rejected by this display-only heuristic before ever reaching a real decoder.
- New `_cw_scan_candidates_from_mag()` (backend) scans the real (fftshifted,
  linear-magnitude, pre-log/pre-rescale) FFT array the nRSP-ST/IQ-Lite path
  already computes for its own spectrum display (`_nrsp_fft_avg`) — zero new
  DSP cost, just reading the array before the display-only `log1p`/rescale
  steps mutate it. Floor is a trailing-window minimum in real dB (same
  technique already proven in `MorseDecoder.process_iq()`'s noise-floor
  tracking), threshold is floor + 8dB (matching the decoder's own default),
  width filtering is in real Hz rather than an arbitrary display-bin count.
- New `skimmer_candidates` broadcast (real `freq_mhz`/`snr_db`/`width_khz`
  per candidate, plus the actual scanned `span_hz`/`center_mhz`) replaces
  the unused legacy stub of the same name. New `skimmer_detect` WS command
  toggle (`cmd:'skimmer_detect', active: true/false` — the frontend already
  sent this; the backend used to just acknowledge it as a no-op) now
  actually turns the scan on/off so idle connections don't pay for it.
- Frontend: new `skHandleRealCandidates()` consumes the real backend list
  with the same persistence/eviction window `_skDetectLoop()` always had, so
  switching between the real backend path and the old client-side fallback
  never causes rows to just vanish. `_skDetectLoop()`'s original
  `DS.liveBins` scan is kept as a fallback specifically for Full IQ/Compact
  connections, where the backend doesn't yet compute an equivalent real
  wideband array (Full IQ currently relays SDRConnect's own native spectrum
  for display rather than computing its own — see the w0.2.3 decision
  further down this file) — it auto-resumes if real candidates go stale.
- Scan range is no longer tied to the main spectrum's zoom/pan state (which
  was implicit and easy to miss — surfaced only as a small muted readout).
  For the real-SNR path it's now the actual scanned span, always accurate.

### Fixed (2026-07-16) — Unmatched Morse patterns no longer silently dropped
Also per the CW decoder evaluation: `MorseDecoder.process_iq()` rendered a
non-empty symbol buffer that didn't exactly match `morse_table` as an empty
string — any timing error (a QSB-distorted dash, keyer weighting, a dropped
dit) just silently ate the character, indistinguishable from "nothing was
sent." A genuinely non-empty, unmatched buffer now renders `#` instead, so a
run of timing errors is visible as a run of `#`s rather than invisible gaps.
An empty buffer (a long trailing gap with nothing typed — not an error)
still stays silent, unchanged.

### Changed (2026-07-16) — CW tab layout: persistent decode ticker, channel overlay, consolidated toolbar
Implements the remaining layout items from the CW decoder/tab evaluation
above (candidate-detection and error-placeholder fixes landed separately,
just above). All four changes are purely visual/layout — no change to the
decode algorithm, WS protocol, or backend.
- **Persistent "Tuned Decode" ticker:** a single-line, tail-truncated
  readout showing the single-channel decoder's live text was added between
  the CW stats bar and the three sub-columns, always visible regardless of
  SKIMMER/SINGLE view. Previously the single-channel decode text
  (`#cw-decode-out`) was only reachable by switching to SINGLE view,
  hiding the Skimmer channel list — there was no way to watch the dial
  frequency and the Skimmer pool at the same time. Fed from the same
  `cw_frame` messages `#cw-decode-out` already uses (`cwHandleFrame`), just
  mirrored into the new `#cw-tuned-ticker` element.
- **Skimmer channel markers on the mini-waterfall:** each active Skimmer
  channel now gets a coloured tick + callsign/SNR (or frequency, before a
  callsign is extracted) label drawn directly on the CW mini-waterfall, at
  its actual frequency offset from the VFO. Colour-matched to that
  channel's row in the Skimmer Channels list (`skRenderChannels()` now
  assigns each row a colour from a fixed 10-colour palette by list
  position, stored on the shared `_skChanText` row object; `_renderCwNexusWf()`
  reads the same colour back). This was the biggest gap versus real CW
  Skimmer/CwGet: with up to 20 channels decoding at once there was
  previously no way to see where any of them actually sat on the waterfall.
  Only drawn in SKIMMER view.
- **Waterfall toolbar consolidated:** the zoom/colour-palette row and the
  floor/range row (previously two separate full-width rows, added in
  separate June 2026 requests) are now one row with a thin divider between
  the two control clusters. Same buttons/handlers, just less vertical
  space spent on chrome.
- **TONE readout demoted:** the read-only "TONE (FROM WATERFALL)" value
  (just reflects the waterfall drag-cursor position, not an editable
  control) shrank from its own full-width labelled block down to a single
  small inline line, so it no longer competes visually with KEY THRESHOLD,
  the control directly below it that the user actually adjusts.
- **Skimmer scan range surfaced prominently:** the scan-range readout
  moved from a small muted line buried in the Skimmer Channels panel
  header (which disappears entirely in SINGLE view — the same "control
  vanishes with its panel" problem the SKIMMER/SINGLE toggle itself had
  before its own earlier fix) to a coloured chip in the always-visible tab
  header, right next to the SKIMMER/SINGLE toggle it's most relevant to.
- **Waterfall/spectrum canvases grown:** the vertical space freed by the
  toolbar consolidation went into the mini-waterfall (220px → 260px) and
  its spectrum trace (70px → 90px) instead of being left blank — the
  waterfall is the most information-dense element in that sub-column.

---

## w032 — CW decoder + CW tab layout overhaul

### Why this exists
Forked from w031 (2026-07-16) after a requested evaluation of the internal
CW decoder's operation (both single-channel and Skimmer) and the CW tab's
layout against best practice and dedicated CW tools (CW Skimmer, CwGet,
fldigi). The evaluation found the decode algorithm itself solid but flagged
Skimmer's candidate-detection front-end as relying on display-only spectrum
bins rather than real SNR, silent character drops on unmatched Morse
patterns, and a layout that buries the decoded text (the actual point of
the tab) behind a hard SKIMMER/SINGLE toggle with no visual link between
the Skimmer channel list and the waterfall. This fork implements the fixes
proposed in that evaluation; see each dated entry below for specifics as
they land.

---

## w031 — Live decoder-testing pass + PSK Reporter spot upload

### Why this exists
Forked from w030 (2026-07-15) specifically to hold the results of a live,
in-Chrome testing pass across the decoders not already confirmed working by
Jon (FT8 INTERNAL, the WSJT-X bridge, and fldigi-routed decoders were
excluded — already confirmed working) — WSPR Beacons, CW (NEXUS engine),
Marine/VHF, Multimon, Numbers-Station/HF-Intel (Rivet), and FreeDV — plus
the previously-scaffolded PSK Reporter spot-upload feature (callsign/locator
fields were added 2026-07-13 with the comment "not sent anywhere yet").

### Live testing results (2026-07-15, RSPdx via SDRConnect, 20m/CW/DSC-calling
frequencies, real air signals)
- **Rivet (Numbers-Station/HF-Intel):** started/stopped cleanly on both DSC
  and Baudot modes, tuned correctly to the 8414.5 kHz DSC distress/calling
  quick-tune, no console errors. No live DSC traffic decoded in the ~25s
  observation window — expected, real DSC calls are sporadic, not a bug.
- **FreeDV:** failed to start with a clear, correctly-surfaced error
  (`freedv_rx not found — build codec2 and ensure it is on PATH`) — a
  missing dependency on the host machine, not a NEXUS bug. Degrades
  gracefully; no crash.
- **WSPR Beacons:** started cleanly, `wsprd` binary found, correctly
  detected the live UTC even-minute capture window and began a fresh
  110.6s capture right at the `:20` boundary in real time. No decode
  observed in the ~100s test window (a full cycle needs ~110s+ processing;
  not run to completion given session time budget).
- **CW (NEXUS engine, Skimmer/monitor mode):** reproduced a real bug — see
  Fixed below.
- **Marine/VHF (AIS):** reproduced a real bug — see Fixed below.

### Fixed (2026-07-15)
- **WSPR — no anti-aliasing filter before decimation.** `WsprDecoder.process_iq()`
  decimated 48kHz/2MSPS baseband down to 12kHz for `wsprd` via a bare
  strided slice (`base[::dec]`) with no low-pass filter first — the
  adjacent comment even said "low-pass and decimate" but the low-pass was
  never actually written. Energy above the new Nyquist folded straight
  back into the WSPR passband (1400-1600Hz) on every call, corrupting
  decode on all three feed paths (Compact, IQ-Lite, Full-IQ). Now uses
  `scipy.signal.decimate(..., ftype='fir', zero_phase=True)` (falls back to
  the old unfiltered slice only if scipy is unavailable).
- **WSPR — wrong sample rate on the RTL-SDR path.** `wspr_dec.process_iq()`
  was passed `state.get('sample_rate')` (the raw/undecimated hardware
  rate) instead of `_rtl_dec_sr` (the actual rate of the decimated signal
  being passed in) — the exact bug class already fixed for `cw_dec`/
  `rtty_dec`/`cw_skimmer_pool` two lines above in the same block, just
  missed for WSPR. Now passes `sr=_rtl_dec_sr`.
- **Multimon — fed audio through a raw-IQ FM discriminator, with the wrong
  sample rate.** `MultimonDecoder.process()` expects genuine, not-yet-
  demodulated raw IQ (it runs its own FM discriminator internally) and
  internally defaulted to `state.get('sample_rate')` (the RF/hardware
  rate) for its resample math. It was being called identically from four
  places, but two of them (the Compact-mode "t==1" stereo-audio path and
  the "t==4" Compact-mode-audio path) only ever have *already-demodulated*
  audio at ~48000Hz available — not raw IQ. Running a meaningless FM
  discriminator over audio (in the t==1 case, literally treating
  left/right stereo channels as I/Q pairs), on top of a badly wrong
  sample-rate assumption, meant Multimon (POCSAG/FLEX/EAS/DTMF/selcall/
  MORSE_CW/AFSK1200/FSK9600) was completely non-functional in Compact
  mode — badged "COMPACT" in the decoder dropdown — with no error or
  indication anything was wrong. Added `MultimonDecoder.process_audio()`,
  a separate path that skips the discriminator and takes an explicit
  `sr`, for the two Compact/IQ-Lite call sites; `process()` (genuine raw
  IQ, Full-IQ path only) now also takes an explicit `sr` instead of
  relying on its internal fallback.
- **Marine/VHF (AIS) — silent failure in Compact/IQ-Lite mode.** The
  `ais_start` WS command handler was the one decoder-enable handler in the
  whole file that never called `_check_iq_mode()` — the function every
  *other* Full-IQ-only decoder's start handler already calls to warn the
  browser ("iq_mode_warning" toast) when the connected stream can't
  actually deliver what the decoder needs. AIS's only decode call site
  (`ais_dec.process_iq()`) is Full-IQ-only, so starting it from the
  Marine/VHF tab in Compact/IQ-Lite mode showed "running: True" with zero
  vessels and zero indication anything was wrong. Now calls
  `_check_iq_mode()` like every other decoder does.
- **CW Skimmer — "ACTIVE" but never finds any candidates at default zoom.**
  Live-reproduced: `_skDetectLoop()`'s false-positive width filter
  (`widthKhz < 2.0`) didn't account for spectrum bin resolution. At the
  default 1x/whole-band zoom (coarse bins, ~3.4kHz/bin on a ~1.75MHz span),
  even a real, strong, genuinely narrow CW carrier can only ever measure
  as ≥1 whole bin wide (≥3.4kHz), so it always failed the flat 2.0kHz
  ceiling — Skimmer showed "ACTIVE" with a clearly visible signal on
  screen but "Skimmer Channels (0)" forever. The ceiling now scales with
  bin resolution (`max(2.0kHz, 2.5 bins)`), so genuinely wide/non-CW
  signals are still rejected at fine zoom while narrow real signals aren't
  rejected purely as a bin-averaging artifact at coarse zoom.

### Added (2026-07-15) — PSK Reporter spot upload
Implements the pskreporter.info UDP/IPFIX reporting protocol (see
https://pskreporter.info/pskdev.html) — the same "de callsign callsign"
propagation-reporting network WSJT-X, JTDX, and fldigi already report to.
- New `PskReporterUploader` class (`w031_NEXUS.py`): builds and sends
  IPFIX-format UDP datagrams to `report.pskreporter.info:4739`, batching
  spots and respecting the protocol's ~5-minute minimum send interval and
  per-callsign de-dupe window; resends the record-format-descriptor
  templates for the first 3 packets and hourly thereafter, per spec.
- Wired into three decode paths: FT8/WSPR via the WSJT-X ALL.txt bridge
  (best-effort callsign extraction from the free-text message), native
  WSPR (`wsprd`, already-structured call/freq/snr fields), and CW Skimmer
  callsign decodes. FT8 INTERNAL (client-side `ft8ts`) is **not** wired up
  yet — those decodes never reach the backend process today.
- New `psk_reporter_config` WS command; new "PSK Reporter" checkbox next to
  the callsign field in the HF Utility location bar (frontend), reusing the
  existing callsign/locator fields rather than adding a new settings
  surface. Locator sent to the backend is computed from the existing
  lat/lon location setting via a new `latLonToGrid()` (Maidenhead 6-char),
  the inverse of the existing `gridToLatLon()`.

### Not yet resolved
- **Decoder dropdown reorg (Internal/Compact/Full-IQ/External):** DAB/DAB+
  was moved from FULL IQ to EXTERNAL in w030 (dab-cmdline opens the SDRplay
  device directly, bypassing NEXUS's own IQ stream). The broader ask — a
  clean 4-way Internal/Compact/Full-IQ/External split — doesn't fit the
  current architecture cleanly: CW, RTTY, and FT8/WSPR are each dual-mode
  at *runtime* (NEXUS-native engine vs. external fldigi/WSJT-X, toggled by
  the user, not fixed per decoder), so they can't be statically pinned to
  either "Internal" or "External". Recommend keeping the existing
  COMPACT/FULL IQ/EXTERNAL section groups and instead making the
  per-row engine badge (already present on CW/RTTY/FT8) the "Internal vs
  External" signal for those three, rather than duplicating rows or
  building a 4th static group — proposed to Jon, not yet actioned pending
  his call.
- GitHub research into upstream improvements (multimon-ng, wsprd, codec2)
  was not pursued — all three are mature, actively-maintained tools; every
  bug found this pass was in NEXUS's own integration code, not upstream.

### Added (2026-07-15) — Windows installer script
- New `build/DARKSKY_NEXUS_w031.iss` (Inno Setup 6) — the first installer
  script for the project; prior versions only shipped a zip of the
  PyInstaller onedir build. Packages `build_Windows.bat`'s output into a
  single `DARKSKY_NEXUS_w031_Setup.exe`, with a fixed `AppId` GUID so future
  releases install as upgrades rather than side-by-side copies,
  `PrivilegesRequired=lowest` (freeware, no admin requirement), and an
  `[UninstallDelete]` rule that removes the whole install directory
  (including any config/cache files NEXUS writes at runtime next to the
  exe) on uninstall.
- Audited and fixed stale `w030` references left over from the fork across
  `build_macOS.sh`, `build_Windows.bat`, both `.spec` files, and
  `version_info.txt` (version bumped `0.3.0`→`0.3.1` to match); updated
  `BUILD_NOTES.md`'s "on every release" checklist from 5 to 6 files to
  include the new `.iss`.

### Fixed (2026-07-15) — CW tab: keying-scope digit jump, mini-waterfall not starting, stuck 3rd-column placeholder
Three bugs reported together from a live Chrome session with CW Skimmer
running against 14 active channels:
- **Keying scope jumped horizontally as SNR digits changed width.** The
  TONE/SPEED/SNR stat boxes had no fixed width, so e.g. `9.2 dB` → `12.4 dB`
  changed the box's rendered width and visibly shifted the whole keying
  scope sideways on every update. Fixed with `min-width` on each stat box
  and `font-variant-numeric: tabular-nums` on the value text so digits
  occupy a constant width regardless of value.
- **CW mini-waterfall not starting.** Root cause traced to the CW mini-
  waterfall being driven by a server-computed FFT (`audio_fft` broadcast
  messages) that was never sent unless FT8 INTERNAL's audio feed happened
  to also be active — CW's own decoder starting didn't turn that feed on.
  Rather than patch the gating, redesigned CW's mini-waterfall to work the
  same way FT8 INTERNAL's tone/waterfall already does: a client-side FFT
  computed in the browser directly from the existing raw-audio binary
  stream (`0x02` frames), instead of a separate server-side computation.
  New `cwAudioTap()`/`_cwClientComputeFFT()`/`cwHandleAudioFrame()` in the
  frontend; backend gate on `_ft8_broadcast_audio()` widened from
  `ft8_internal_active` to `ft8_internal_active or cw_dec.active` at all 5
  call sites so the audio stream is actually flowing whenever CW decode is
  running, regardless of FT8 INTERNAL's state. The old server `audio_fft`
  broadcast is kept for RTTY/fldigi, which still use it.
- **3rd column stuck on a fixed placeholder message.** The CW Skimmer pool
  and the single-channel CW decoder write to two separate DOM elements
  (kept apart since a June 2026 fix to stop their text interleaving); when
  only the Skimmer pool was active, the single-channel decoder's own panel
  never got any text and so never cleared its idle "Click Start" notice —
  even though Skimmer channels were visibly decoding elsewhere on screen.
  The notice now swaps its wording (not its target panel) to point at the
  Skimmer Channels list once Skimmer decodes start arriving, if the
  single-channel decoder itself hasn't produced any text yet.

### Changed (2026-07-15) — CW tab layout: 3 sub-columns + Skimmer/Single toggle
Per request, removed the CW tab's always-visible 3rd "decoded text" column
as a permanent fixture (it forced scrolling to reach the panels below the
mini-waterfall) and replaced it with a SKIMMER/SINGLE toggle:
- The NEXUS-engine panel is now 3 side-by-side sub-columns instead of 2 —
  waterfall + zoom/floor/colour controls | tone/threshold + Last Chars +
  sweep config | speed trend + Skimmer Channels — so nothing stacks below
  the waterfall on a normal-height window.
- The single-channel decoder's own text panel (`#cw-decode-out`) is no
  longer permanently on screen; a new SKIMMER/SINGLE toggle in the third
  sub-column shows it on demand. Default view is SKIMMER. Switching to the
  FLDIGI engine always force-shows it regardless of the toggle (fldigi has
  no Skimmer pool of its own). Preference persists across reloads.

### Fixed (2026-07-15) — BW dropdown rendering far wider than its content
User-reported and confirmed via screenshot: the BW preset dropdown was
rendering nearly the full width of the window for as few as 5 short
presets, next to the properly-sized Bands dropdown. Root cause: a legacy
CSS rule (`#bw-panel { position:absolute; top:100%; right:0; ... }`) from
an earlier, pre-`toggleBWPanel()` implementation of the same element was
still declaring `right:0`. The current implementation only ever sets `left`
and `top` inline at runtime and never touches `right` — so with
`position:fixed` (set inline) plus a computed `left` and a leftover
`right:0`, the browser stretched the box to fill the gap between them
instead of shrink-wrapping to its content. Added `right:auto` to the
element's inline style to override the stale declaration; also tightened
the preset grid from 3 to 2 columns and matched the panel's corner-radius/
shadow to `#nexus-bands-panel` for visual consistency between the two
dropdowns.

### Fixed (2026-07-15) — FT8 SOURCE buttons looked like info text, not buttons
The inactive FT8 SOURCE button (INTERNAL or WSJT-X, whichever wasn't
selected) had `border: none; background: none` — indistinguishable from
plain label text next to a bullet character. `.ft8-src-btn` now always
renders with a visible border/background (matching `.ft8-ctrl-btn`/
`.ft8-band-chip` elsewhere in the same tab), with a hover state added and
the active state additionally getting an accent-coloured border.

### Fixed (2026-07-15) — FT8 INTERNAL monitor audio distortion; new volume slider
User-reported audible distortion when FT8 INTERNAL decode starts, requiring
the OS volume to be turned down to compensate. Root cause: the existing
low-SDRConnect-volume gain-compensation curve in `ft8HandleAudioFrame()`
(added 2026-07-12 to fix a related complaint) was unbounded as volume
dropped — roughly 5.6x at 20% device volume, ~26.8x by 0% — and every
sample was then hard-clamped to ±1, a brick-wall clip that produces
audible crackling on any sample the curve pushed past full-scale. Fixed in
two passes:
- Capped the compensation multiplier (`FT8_MAX_GAIN`, tightened from an
  initial 2.5 down to 1.6 after user follow-up) and replaced the hard clamp
  with `Math.tanh()`, a soft-knee curve that rounds off peaks smoothly
  instead of flat-topping them.
- Added a **MON VOL** slider to the FT8 INTERNAL toolbar (default 50%,
  persisted via localStorage) that scales only the local browser playback
  in `ft8HandleAudioFrame()` — independent of `DS.volume` (the actual
  SDRConnect/receiver volume) and applied *after* the signal is handed to
  `ft8AudioTap()`, so turning the monitor volume down never affects decode
  sensitivity, only how loud the monitor audio is in your speakers.

### Fixed (2026-07-15) — FT8 INTERNAL gain-cap regression hurt decode count
Follow-up to the distortion fix above: user reported fewer decodes after the
gain cap was tightened, and asked whether that was the cause — yes. The
first pass of the distortion fix capped the compensation gain and ran it
through `Math.tanh()` on the *same* `mono` array that was also handed to
`ft8AudioTap()` for decoding, not just to the speaker output. Capping the
boost reduced the amplitude reaching the decoder at low SDRConnect volumes,
and `tanh`'s soft-knee saturation — applied to a passband that normally
holds several simultaneous FT8 signals, not just one tone — introduces
intermodulation distortion across all of them, which can bury weaker
signals. Neither concern applies to a `Float32Array` that only ever gets
FFT/LDPC-processed in JS (no hardware clipping is possible there); they
only matter for what comes out of the speakers. Fully separated the two
paths: the decode tap now gets the original linear compensation gain,
**uncapped** and with no soft-clip; the speaker-output copy is computed
separately and is the only one that gets `FT8_MAX_GAIN`/`tanh`/MON VOL
applied. The gain cap is now purely a playback-loudness knob and no longer
trades off against decode sensitivity.

### Added (2026-07-15) — CW quick-tune highlight fix, FT8 stat prominence, FT8 INTERNAL → PSK Reporter
- **FT8 band quick-tune chips now stay highlighted after clicking.**
  User-reported: pressing a band chip (160m-6m) didn't visibly stay
  selected, but hovering over one did. Root cause: the click handler ran
  `setFTband(num)` before `_ft8HighlightBand(num)` in the same inline
  `onclick` — if `setFTband` took a moment or threw, the highlight call
  after it could be skipped or delayed. Also, `.active` and `:hover` used
  the exact same border/text colour, differing only by a barely-visible
  10%-opacity background tint, so even a correctly-applied selection looked
  almost identical to the unselected state. Fixed by highlighting first
  (instant feedback, independent of whether the tune logic that follows
  succeeds), tracking the selection in `ft8SelectedBandNum` so it survives
  a chip-list rebuild, and giving `.active` a solid, bold, unmistakable
  fill.
- **Decodes/Callsigns/Countries counters made prominent.** Were 9px muted
  text easy to miss; now rendered as bold, colour-coded badges (13px,
  cyan/green/violet) in the FT8 INTERNAL toolbar.
- **FT8 INTERNAL decodes now reach PSK Reporter.** User reported 828 local
  decodes / 118 callsigns / 20 countries with nothing showing up under
  their callsign on pskreporter.info. Root cause: FT8 INTERNAL decodes
  entirely client-side (the `ft8ts` Web Worker) and never sent a single
  decode to the Python backend — the only process that can open a UDP
  socket to `report.pskreporter.info`. This was a known, documented gap
  from the original PSK Reporter implementation earlier the same day (see
  above). New `ft8_internal_spot` WS command: `appendFT8Decode()` forwards
  each decode's callsign/frequency/mode/SNR to the backend — only when
  `ft8Source === 'internal'` (the WSJT-X-bridge path already reports via
  its own backend-side ALL.txt-tailing `FT8Decoder`, so forwarding those
  too would double-report) and only while PSK Reporter is enabled. Absolute
  frequency is computed client-side as dial/VFO frequency + the decode's
  audio tone offset, matching how the WSJT-X-bridge path already derives
  its own frequency field. Also fixed a stale "not sent anywhere yet"
  message left in the callsign-entry popup from before PSK Reporter upload
  was wired up — it now reflects whether uploading is actually on.

### Fixed (2026-07-15) — CW mini-waterfall never moved when retuning the VFO
User-reported, with screenshot: a dense noise blob permanently stuck on the
left half of the CW mini-waterfall (labelled -3000..-1000 Hz), nothing on
the right half, unchanged no matter how the VFO was retuned. Two compounding
bugs in the client-side FFT tap added earlier the same day:
- `_cwClientComputeFFT()` centred its slice on the decoder's live tone
  reading (~700 Hz) with a ±3000 Hz span, clamping the low end to 0 without
  adjusting the displayed range to match — so the real data (0 to ~3700 Hz
  of raw absolute audio spectrum) got stretched across the *entire* canvas
  width, while the axis labels (`-3000..+3000`, from `_cwNexusWfHzBounds()`)
  were computed completely independently and never corresponded to what was
  actually in the bins.
- That ±span "0 Hz = VFO" symmetric convention was inherited from the OLD
  backend implementation, which achieved it via a genuine complex IQ
  frequency shift (see the "Mini-waterfall freeze" entry earlier in this
  file). It's physically impossible to reproduce from the new data source:
  0x02 frames carry already-demodulated, real-valued mono audio, which for
  USB/CW demodulation only ever has content at *positive* Hz — audio Hz
  already equals the RF offset above the VFO dial directly, there's no
  negative side to show. The symmetric axis was guaranteed to put real
  content on one side and nothing on the other regardless of the slicing
  bug above.
- Fixed by removing the tone-centring entirely and slicing straight from
  0 Hz (= VFO dial) to +3000 Hz — the same 0..+span mapping FT8 INTERNAL's
  own waterfall already uses. `_cwNexusWfHzBounds()` now returns `{lo:0,
  hi:span_hz}` instead of `{lo:-span_hz, hi:span_hz}`; the drag-to-tune
  handler, cursor overlay, and axis-tick drawing all read that function
  generically, so retuning-by-drag, the cursor position, and the axis
  labels all stayed in sync with a single change.
- Also stopped writing to the shared `DS.audioFftMeta` object from this
  client-side CW tap — RTTY's tone scope and the fldigi waterfall still
  read that object from the server's own `audio_fft` broadcast, and CW's
  writes to the same object would have silently corrupted whichever one ran
  more recently if CW and RTTY/fldigi decode were ever active together. CW
  now maintains its own `DS.cwAudioFftMeta`.

### Changed (2026-07-15) — CW mini-waterfall reverted to server-side wideband scope; new spectrum trace added
Following the fix above, Jon asked "CW WATERFALL DOESNT CHANGE WHEN I CHANGE
VFO" (fixed above), then "WHEN I CHANGE BW THE CW WATERFALL CHANGES" — which
turned out not to be a bug, but the expected consequence of the client-side
tap genuinely reflecting the CW decoder's own BW-filtered audio. Jon then
asked for the opposite: "For the CW waterfall, rather than change with bw,
can it not be fixed span like ft8 internal... would be good to add spectrum
also", and confirmed, being a Full IQ user (0.5/1/2 MSPS): "in the main
spectrum and waterfall, i am usually looking at 2, 1 or 0.5 msps. Having the
cw spectrum waterfall at 3000hz would provide me with a close up scope which
is what i need."

Investigating turned up that the backend already had exactly this,
untouched the whole time: a server-side `audio_fft` broadcast for both
IQ-Lite and Full IQ mode, computed from genuine *unfiltered* complex IQ
(not the BW-filtered demodulated audio the client-side tap used), VFO-
centred via `_audio_fft_center_hz()`, at a fixed ±3000 Hz span — immune to
the CW decoder's own narrow BW filter by construction. This was the
original pre-w031 mechanism; the same-day client-side-tap redesign had
disconnected CW from it without knowing it already covered this need.

- Reverted the CW mini-waterfall (and the new spectrum trace below) back to
  consuming the server's `audio_fft` broadcast: the WS message handler's
  `case 'audio_fft':` now again calls `_renderCwNexusWf(msg)` and
  `_renderCwNexusSpectrum(msg)` whenever CW is the active NEXUS decoder,
  populating the CW-only `DS.cwAudioFftMeta` from the server message.
- `_cwNexusWfHzBounds()` reverted to the symmetric `{lo:-span_hz,
  hi:span_hz}` window — correct again now that the source is genuine
  complex IQ (which really can have content on both sides of a VFO shifted
  to DC), not one-sided real audio.
- `cwHandleAudioFrame()` (the client-side tap entry point) is now a no-op;
  `_ft8_broadcast_audio()`'s internal gate and all five of its call sites
  in `w031_NEXUS.py` dropped the `or cw_dec.active` added earlier the same
  day, back to `ft8_internal_active` only — CW no longer needs that 0x02
  raw-audio stream, so this also saves the bandwidth/CPU of broadcasting it
  when only CW (not FT8 internal) is running. `cwAudioTap()`,
  `_cwClientComputeFFT()`, and `_cwFFT()` are left in place as unused code
  rather than deleted.
- Added a new spectrum trace (`_renderCwNexusSpectrum()`, cyan line plot on
  a new `#cw-nexus-spectrum-canvas`) above the mini-waterfall, sharing the
  exact same zoom/floor/range and Hz-axis mapping as the waterfall so the
  two stay pixel-aligned — the FT8-internal-style pairing Jon asked for.
- Also fixed a related, previously-undiagnosed axis bug in the Compact-mode
  `audio_fft` block (`w031_NEXUS.py`, the `t==1` branch): it clamped its
  low bin to 0 (real audio has no negative Hz) without shifting the window
  to compensate, silently narrowing the reported span while still claiming
  `carrier_hz` was the nominal CW tone/RTTY mark — not the actual centre of
  what got sliced. Now shifts the window up to preserve the full requested
  width when clamped, and reports the true centre.

### Added (2026-07-15) — "My QTH" home marker on every NEXUS map
Jon: "on any maps in nexus, can you add a distinguishing mark on my qth?"
Audited all six maps in the app. The WSJT-X bridge map (`ft8Map`) and the
WSPR spot map already had a home marker (the WSPR one was just a small
plain circle labelled "RX"); the ADS-B, AIS, ACARS position, and FT8
Skimmer/station (MapLibre) maps had none at all.

- Added a shared `_addQthMarker(map)` / `_qthHomeIcon()` helper — the same
  orange pin+dot SVG icon and "My QTH" popup `ft8InitMap()` already used,
  now reused everywhere instead of being drawn ad hoc per map. Reads live
  from `HF_LOC` (the HF Utility tab's location bar), with the same
  53.4°N/-3.0°W fallback the WSJT-X bridge map already used if no location
  has been set.
- Wired it into `adsbInitMap()`, `aisInitMap()`, and `_acarsInitMap()`
  (all previously marker-less).
- Upgraded the WSPR spot map's plain "RX" circle to the same pin icon for
  visual consistency across every map (its `_rxLL` receiver-position
  tracking used for arc lines to spots is unchanged).
- The FT8 Skimmer/station map runs on MapLibre GL JS, not Leaflet, so it
  has no `L.divIcon` equivalent — added a plain `maplibregl.Marker` built
  from the same SVG string directly in `initStationMapInstance()`'s
  `on('load', ...)` handler instead of going through the shared Leaflet
  helper.

---

## w030 — Native FT8/FT4 decoder, ported from w029 onto the w026 baseline

### Why this exists
Jon asked for w029 to be examined. w029 looked like a large, legitimate
piece of new work (a client-side FT8/FT4 decoder, `ft8ts` by Roger Need,
GPL v3 — decodes FT8/FT4 entirely in-browser via a Web Worker, no WSJT-X
required) — but its HTML (`DARKSKY_NEXUS_w029.html`) turned out to be
forked from the ancient **w0.1.2** snapshot (`../OLD VERSIONS/w012`), not
from w026, w027, or w028. Internal markers gave it away: the `<title>` and
the JS section header both still literally read `w0_1_2`. Its Python
backend (`w029_NEXUS.py`), separately, was a byte-for-byte copy of w026's
— so the two halves came from different, non-adjacent points in the
project's history.

Net effect: relative to w026 (the deployed baseline), w029's frontend was
missing HFDL, VDL2, RIVET, and Trunk decoding entirely; RTTY was gutted to
a fraction of its w026 implementation; AIS, ACARS, DAB, POCSAG, and CW
Skimmer were all cut down to old, much smaller w0.1.2-era versions; and
the light/dark theme toggle was gone. The Dockview dockable-panel UI from
w028 was also absent, but per Jon that's expected/wanted — w027/w028 were
his own UI testing, not something to carry forward into NEXUS.

Decision: keep w029's one genuinely new contribution (the native FT8/FT4
decoder) and move it onto w026, rather than trying to backfill everything
w029 was missing.

### Added: native/internal FT8 & FT4 decoding (no WSJT-X required)
- New **FT8 SOURCE** toggle at the top of the FT8/WSPR tab: **WSJT-X**
  (default — the existing, unchanged ALL.txt-bridge mode from w026) or
  **INTERNAL** (new — decodes FT8/FT4 entirely client-side).
- Vendored `ft8ts` (GPL v3, © Roger Need, https://github.com/e04/ft8ts) —
  a from-scratch JS/TS port of the WSJT-X v2.7 FT8/FT4 algorithm — inline
  in the page, running inside a dedicated Web Worker so decoding (LDPC
  belief-propagation, FFT correlation, etc.) doesn't block the UI thread.
- New spectrum/waterfall canvases, band-quick-tune chips, and a
  decode-list/QSO-detail panel for the internal decoder, separate from
  (and not disturbing) the existing WSJT-X-bridge table/map UI, which is
  now wrapped in its own `#ft8-bridge-panel` and stays the default.
- Backend: real demodulated mono audio is now streamed to the browser for
  the internal decoder. New `ft8_internal_active` flag + `ft8_internal_enable`
  WS command, gated so it only costs bandwidth/CPU when INTERNAL mode is
  actually selected *and* decoding is turned on — bridge-mode users (the
  default) and idle users are unaffected. New binary wire format,
  `_ft8_broadcast_audio()` in `w030_NEXUS.py`: `byte[0]=0x02` (audio —
  previously a reserved no-op in `handleBinaryFrame`), `bytes[1:3]`=
  uint16-LE sample rate in Hz, `bytes[3:]`=int16-LE mono PCM. Wired in at
  every demod hook point (SDRConnect PCM, IQ-Lite, Full IQ, RTL-SDR,
  Compact-mode).

### Fixed: FT8 bridge mode was silently crashing the SDRConnect connection
Found while wiring up the audio feed above, not something w029 introduced
— this bug has been present since `FT8Decoder` was written (inherited by
w027/w028/w029 too, since they all carry the same class): `FT8Decoder` only
tails WSJT-X's `ALL.txt` file for spots — it has no `process()` or
`process_iq()` method. But five call sites across the SDRConnect/RTL-SDR
demod paths called exactly those non-existent methods whenever
`ft8_dec.active` was true (i.e. whenever the FT8 tab's bridge mode was
turned on). Every one of those call sites sits inside the same
`try: ... except Exception: log "SDRConnect bridge error… retrying in 5s"`
block that wraps the whole SDRConnect message loop — so enabling FT8 threw
`AttributeError` on the very next audio packet, which silently tore down
and reconnected the entire SDRConnect bridge (dropping spectrum/audio
momentarily), then did it again on the next audio packet, in a continuous
crash-reconnect loop for as long as FT8 stayed enabled. All five dead call
sites removed; four of them repurposed to feed the new native-decoder audio
broadcast described above instead.

### Known gaps carried over from w029, not fixed here (flagged, not fabricated)
- `getWinSec()`/`getCollectSamples()`/`cycleFT8Depth()` referenced
  `FT8_WIN_SEC`/`FT4_WIN_SEC`/`FT8_COLLECT_SAMPLES`/`FT4_COLLECT_SAMPLES`/
  `ft8CurrentMode`/`ft8Depth` — none of which were ever declared anywhere
  in w029. Calling any of them would have thrown `ReferenceError`. Defined
  now using standard WSJT-X cycle lengths (FT8=15s, FT4=7.5s @ 48kHz).
- `countryToLatLon()`/`callsignToCountry()` (used by the QSO propagation
  map's country grouping/coloring) referenced `DXCC_CENTROIDS`/
  `DXCC_PREFIXES` — also never defined anywhere in w029. Stubbed as empty
  objects rather than fabricated (a real DXCC prefix table is ~400+
  entries and needs a verified source) — the map still works, just without
  country grouping/coloring, until a real table is sourced.
- The propagation map itself (`loadStationMapDeps`/`initStationMapInstance`)
  pulls MapLibre GL JS + tile styles from `cdnjs.cloudflare.com` and
  `tiles.openfreemap.org` — same "no general internet access on the
  Chromebook deployment device" constraint already documented for
  Dockview in `../w028/CHANGELOG.md`. It degrades to an on-screen message
  rather than crashing, but won't render there as-is.
- A pre-existing minor precision note, not a bug: on the RTL-SDR path, the
  internal decoder's audio arrives at whatever `cur_sr / dec_r` actually
  works out to (not always exactly 48000 Hz — `cur_sr // dec_r` is an
  integer floor division, documented in several existing BUGFIX comments
  in `w030_NEXUS.py`). The client always knows the true rate (it's in the
  wire format), but still assumes a fixed 4:1 decimation to 12kHz — a
  fully sample-accurate fix means resampling that tap to a true 48000 Hz
  stream, which wasn't done here.
- Two small harmless duplicate function definitions inherited verbatim
  from w029 (`openStationMapModal`/`closeStationMapModal`, and a `ts()`
  timestamp helper, each defined twice within the ported FT8 section).
  JS just uses the later definition; left as-is rather than risk an edit
  during an already-large merge.

### Also fixed while merging (not FT8-related, just found along the way)
- w029's copy of the FT8/FT4 code declared `const FT8_BANDS =
  {1:1840000, ...}` (exact dial frequencies for band-hop quick-tune chips,
  keyed 1-11) — but w026 already has a **different**, pre-existing global
  `const FT8_BANDS = [{lo,hi,name,color}, ...]` (a generic amateur-band
  lookup-by-frequency table used elsewhere, e.g. `ft8BandInfo()`). Same
  name, incompatible shapes — `const` can't be redeclared, so this was a
  hard `SyntaxError` that would have broken the *entire* app the moment
  this code was merged in as-was. Renamed the new one to
  `FT8_HOP_BANDS`/`FT4_HOP_BANDS`.

### Docs and build/ packaging scripts synced to match (w026 → w030)
Following the same convention as past releases: `docs/md/w030/` (QuickStart,
User Manual, Troubleshooting — updated for the new FT8 SOURCE toggle, the
INTERNAL native decoder, and the WSJT-X-bridge crash fix, with every
pre-existing historical `(w0.2.6)`/`(w0.2.x)` version tag left untouched
rather than rewritten as `(w030)`, since those document *when* each past
change actually shipped) and matching `docs/word/w030/*.docx`, built via
the existing `docs/_docx_build/` node/docx pipeline (`build_quickstart.js`,
`build_usermanual.js`, `build_troubleshooting.js`) with the same content
changes mirrored into each build script. `build/` packaging scripts
(`build_macOS.sh`, `build_Windows.bat`, both `.spec` files,
`version_info.txt`, `BUILD_NOTES.md`) also ported: the app-name construction
now uses a dedicated `APP_VERSION_TAG` (`w030`, matching NEXUS's own
version string everywhere else) kept separate from `APP_VERSION` (`0.3.0`,
the dotted-numeric form the macOS/Windows metadata fields actually require)
— building both from the same variable the way w026's scripts did would
have produced an app named "w0.3.0" instead of "w030", inconsistent with
every other self-identifying string in the app (title, `#brand-version`,
`VERSION` constant, this CHANGELOG).

### Fixed (post-release, live-tested): `_find_html()` fallback still pointed at the old filename
First real run of w030 failed at startup with "DARKSKY UI not found —
expected: .../DARKSKY_NEXUS_w0_2_6.html". `_find_html()`'s same-stem check
(comparing the .py filename to the .html filename) has never actually
matched in this codebase — `w030_NEXUS.py` vs `DARKSKY_NEXUS_w030.html` are
different naming patterns, so it always falls through to a glob (looking
for `DARKSKY*w0_2_6*.html`) and a hard-coded fallback path, both of which
still said `w0_2_6` in three places. These weren't caught by the earlier
version-string sweep because they're deep inside a helper function, not
near the file's obvious self-identifying strings (title, `VERSION`, etc.).
Fixed all three references to `w030`; verified against the real file that
the glob now resolves correctly.

### Fixed (post-release, live-tested): shutdown always ended in a `RuntimeError`
Closing the browser tab (or Ctrl+C/SIGTERM) correctly ran the full
shutdown sequence — child processes terminated, HTTP server stopped,
background tasks cancelled, "NEXUS shutdown complete." logged — but then
`asyncio.run(main())` raised `RuntimeError: Event loop stopped before
Future completed.` on every single exit. Pre-existing, inherited from
w026 unchanged (this shutdown code isn't something w030 touched) — found
because it showed up in the terminal on first live test. Root cause:
`main()` idles forever on a bare `await asyncio.Future()` that can never
resolve on its own; `_graceful_shutdown()` called
`asyncio.get_running_loop().stop()` directly to end the program, which
halts the loop while `main()`'s task is still suspended on that
unresolvable Future — so `asyncio.run()`'s own internal bookkeeping sees
its top-level task as never having completed, and raises. Confirmed with
a minimal standalone repro before and after. Fixed by introducing a
module-level `_shutdown_event` (`asyncio.Event`): `main()` now awaits
`_shutdown_event.wait()` instead of the bare Future, and
`_graceful_shutdown()` calls `_shutdown_event.set()` instead of
`loop.stop()` — `main()` wakes up and returns normally, so `asyncio.run()`
completes without an exception. Also excluded `main()`'s own task from the
shutdown's "cancel every other task" sweep (it's tracked via a new
`_main_task` global set at the top of `main()`), since the intent is for
it to return normally, not be cancelled out from under itself.

### Fixed (post-release, live-tested): VFO, spectrum, and waterfall all stopped rendering
App connected fine but showed no VFO readout, no spectrum, no waterfall —
found via live report immediately after the shutdown fix above. Root
cause: the three FT8 integration "monkey-patch" wrappers added to the
frontend —

```js
const _origHandleBinaryFrame = handleBinaryFrame;
function handleBinaryFrame(buf) { _origHandleBinaryFrame(buf); ... }
```

— used a `function` declaration to redefine a name that already had a
`function` declaration earlier in the same script. JS hoists function
declarations before any code runs, and when the same name is declared
twice in one scope the *last* declaration wins during that hoisting pass.
So by the time `const _origHandleBinaryFrame = handleBinaryFrame` actually
executed, `handleBinaryFrame` had already been rebound to the wrapper
itself — making `_origHandleBinaryFrame === handleBinaryFrame` and turning
every call into infinite self-recursion (stack overflow, silently caught
inside the WS message handler's try/except-equivalent, so nothing ever
rendered). This hit all three wrapped functions: `handleBinaryFrame`
(every spectrum/waterfall frame), `handleJSONFrame` (VFO/state updates),
and `showTab` (tab switching) — fully explaining the symptom. Confirmed
with a standalone Node.js repro before fixing, and again after. Fixed by
changing all three wrappers from a `function name(){}` redeclaration to a
plain assignment (`name = function(){}`), which only ever declares the
name once and avoids the hoisting collision entirely.

### Fixed (post-release, live-tested): FT8 INTERNAL source threw on first click — "FT8 internal not working"
Clicking the FT8 tab, or clicking the INTERNAL source toggle, or clicking
Decode On, each immediately threw `ReferenceError: ft8WorkerReady is not
defined` — so the native ft8ts decoder never actually started. Root
cause: the native-decoder integration has an entire `State` section
header (`// State`, just above `// Init`) that was left completely empty —
about 30 variables (`ft8Worker`, `ft8WorkerReady`, `ft8Decoding`,
`ft8AudioBuffer`, the FFT/waterfall buffers `ft8FftBuffer`/`ft8FftMag`/
`ft8FftCumSum`/`ft8WfAvgSum` and their size constants `FT8_FFT_SIZE`/
`FT8_FFT_HOP`/`FT8_DISPLAY_BINS`/`FT8_BINS_PER_PX`, the cycle-timing state
`ft8CycleBoundaryTime`/`ft8NextBoundaryMs`/`ft8CycleTimerInterval`, the
UI-mode state `ft8CountryMode`/`ft8CumulativeMode`/`ft8WfSpeed`/
`ft8CurrentBandName`/`ft8TrackedFreq`, plus `FT8_GRID_FALSE_POSITIVES` and
`vfoInitialised`) were referenced throughout the ported code but never
declared with `let`/`const`/`var` anywhere. An assignment like
`ft8Worker = new Worker(...)` silently creates an implicit global the
first time it runs, but reading a name before its first assignment —
e.g. `if (!ft8WorkerReady)` on the very first click — throws immediately,
since the identifier has no binding at all yet. Filled in the whole
block: FFT sizing chosen as a 4096-point FFT on the 48kHz audio tap
(≈11.7 Hz/bin) with `FT8_DISPLAY_BINS` covering the same 0–3320 Hz
passband the spectrum/waterfall grid already draws; `FT8_GRID_FALSE_POSITIVES`
stubbed as an empty `Set` (same "no fabricated ham-radio reference data"
approach as `DXCC_CENTROIDS`/`DXCC_PREFIXES`); UI-mode defaults
(`ft8CountryMode='all'`, `ft8CumulativeMode=true`, `ft8WfSpeed=4`) matched
to the button labels already shipped in the HTML (Country All /
Cumulative / Slow). Verified via live click-through in Chrome (INTERNAL
toggle → Decode On → worker loads, `ft8WorkerReady` becomes `true`, zero
console errors) after the fix; reproduced the exact three-error sequence
before it.

### Fixed (post-release, live-tested): dead `window.onload` block threw on every page load
Separately, every page load logged `ReferenceError: buildSmeter is not
defined` from a `window.onload` handler, before anything else in that
handler could run. Investigated and found the entire block was foreign,
non-functional code: none of the four functions it called
(`buildSmeter`, `buildAudioMeter`, `updateSliderFill`,
`updateButtonStates`) or the DOM ids it referenced (`ipInput`,
`portInput`, `ipDropdown`, `volumeSlider`) exist anywhere in this
codebase or in w026 — it doesn't match NEXUS's actual connection modal
(SSH Host/Port/User/Password) or its actual meters (header SNR/dBm
readouts). Removed the block entirely; changes nothing functionally
since none of it ever executed successfully, it just removes a
guaranteed startup console error.

### Investigated (live-tested + user's own server log): FT8 INTERNAL still shows no decodes/waterfall on nRSP-ST + Compact mode — not a NEXUS bug
After the two fixes above, clicked through the full INTERNAL flow live
(same running backend/session the user was on, via a second browser tab)
with instrumentation on `handleBinaryFrame`/`handleJSONFrame`: source
toggle and Decode On both fire with zero JS errors, the backend
acknowledges `ft8_internal_status: active=true` and logs "FT8 internal
(native ft8ts) audio feed: ON" — but zero `0x02` FT8 audio frames ever
arrived browser-side. First hypothesis (that the pre-existing
`_check_iq_mode()` "no raw IQ in Compact/IQ-Lite on nRSP-ST" warning
explained this) was wrong and got corrected: that diagnostic is
specifically about type-2 IQ frames, not type-4 audio — Compact mode
exists precisely to send demodulated audio *instead of* raw IQ, so its
absence is normal and doesn't imply audio is missing too. Settled by
the user's own server log (`SDRConnect frame types: {...}`, which this
codebase already logs every 100 frames): over ~15 minutes and 9000+
frames, with the FT8 feed confirmed ON throughout, **every single frame
was type 3 (spectrum) — zero type 1, zero type 2, zero type 4** — despite
`set_primary_device_enable`/`device_stream_enable`/`iq_stream_enable`
all completing and SDRConnect reporting `'started': True`. So the `t==4`
"Compact mode audio IQ" code path (where the FT8 broadcast hook lives,
alongside CW/RTTY's Compact-mode handling) is correctly written but has
never once fired on this connection — SDRConnect itself isn't emitting
any binary audio or IQ data in this mode on this hardware, only
spectrum. Same root cause class as the already-documented type-2 IQ
finding for Compact/IQ-Lite on nRSP-ST, now confirmed to extend to
audio too. No code fix applies — switch SDRConnect to **Full IQ** mode
(the one mode this file's own comments confirm, via prior SDRplay
support contact, actually delivers binary signal data over this bridge
on the nRSP-ST), or use the RSPdx directly / RTL-SDR engine. Separately
fixed one small pre-existing mislabel found along the way: the new
`_ft8_broadcast_audio(p, sr=state.get('sample_rate', 48000))` call at
the `t==4` site was passing the RF/hardware sample rate (e.g. 500000
for 500 kSPS) as the audio sample rate — copied from
`_rtty_capture_feed`'s call two lines above it, which has the same
pre-existing mislabel (left alone, out of scope). Changed the FT8 call
to a fixed `sr=48000`, matching every other audio-broadcast call site.
Requires a NEXUS restart to take effect (Python changes, unlike the
HTML, aren't picked up on next page load).

### Fixed (root cause, user-confirmed via independent reference client): SDRConnect never streamed audio at all — NEXUS was missing `audio_stream_enable`
The "Full IQ required" theory above (both the first, wrong version citing
the type-2 IQ warning, and the corrected version resting on the 9000+
spectrum-only frames in the user's log) turned out to be the wrong fix,
even though the log evidence itself was accurate. User supplied a
separate, independently-written standalone tool
(`WebsocketFT48_v1.html`) that connects directly to SDRConnect and does
successfully decode FT8 — 41 decodes, real S-meter/audio-meter/waterfall
— on the exact same nRSP-ST in Compact mode. Diffing its connect
sequence against NEXUS's found the actual gap: on `ws.onopen` it sends
`device_stream_enable`, then **`audio_stream_enable`**, then
`audio_mute=false` (plus `demodulator=USB`, `filter_bandwidth=3000`,
`audio_volume_percent`). NEXUS's connect sequence
(`set_primary_device_enable` → `device_stream_enable` →
`iq_stream_enable`, in the deferred-enable block around line 7051) never
sent `audio_stream_enable` anywhere in the file — confirmed by grep, zero
matches as an outbound command. `audio_stream_enable` is a separate gate
from `iq_stream_enable`, apparently unconditional on device mode:
without it SDRConnect sends spectrum only, forever, in Compact **or**
Full IQ; Full IQ mode was never actually the requirement — it just
happened to be untested since nobody had tried FT8 INTERNAL/CW/RTTY on
this exact nRSP-ST + Compact combination with `audio_stream_enable` sent
before now. Also explains why CW/RTTY were silently non-functional on
Compact mode this whole time (same missing command, same t==1/t==4 code
paths). Fixed: added `audio_stream_enable` (0.3s after `iq_stream_enable`)
and `audio_mute=false` (0.2s after that) to the same deferred-enable
sequence, same wire format/timing pattern as the existing three sends.
Once this lands, SDRConnect should start sending real type-1 audio
frames — which the existing t==1 branch (line ~6264) already forwards to
`_ft8_broadcast_audio()` when `ft8_internal_active` is on, no further
change needed there. Requires a NEXUS restart; not yet re-verified live
against a running NEXUS instance (only against the reference tool
directly) — confirm FT8 INTERNAL actually decodes after restart.

### Fixed (live-tested, post-restart): three more bugs that only surfaced once real audio actually started flowing
After the `audio_stream_enable` fix above, restarted NEXUS and confirmed
real `0x02` audio frames finally arrive (869 binary frames in 6s: 147
spectrum + 722 audio). This exercised code paths that had never once run
against real data before, surfacing three more bugs:
1. **`RangeError: start offset of Int16Array should be a multiple of 2`**
   in `ft8HandleAudioFrame` — `new Int16Array(buf, 3)` where the wire
   header is 3 bytes (1 type + 2 sample-rate); byte offset 3 isn't
   2-aligned, which `Int16Array` requires. Fixed to `new
   Int16Array(buf.slice(3))` — slicing copies into a fresh, always-aligned
   buffer.
2. **Tab froze solid** — `ft8NextBoundaryMs` defaulted to `0` (added in
   the earlier state-variables fix), but `ft8AudioTap`'s catch-up loop
   does `while (nowMs >= ft8NextBoundaryMs) ft8NextBoundaryMs += cycleMs`
   against a real Unix epoch `nowMs` (~1.78e12 ms) — from 0, that's
   ~100 billion iterations. Never triggered before since `ft8AudioTap`
   was never called with zero audio frames ever arriving. Fixed the
   default to `Date.now()`, and added a safety-cap guard in the loop
   itself (jump straight to the next real boundary if
   `ft8NextBoundaryMs` is ever more than an hour stale, instead of
   incrementing one cycle at a time) so no future variant of this can
   recur.
3. **`IndexSizeError: createImageData... source width is zero`** in
   `ft8DisplayFrame` — `spCanvas.offsetWidth` is 0 whenever the canvas
   isn't laid out (FT8 tab not open, panel hidden), and
   `createImageData(0, 1)` throws. Added a guard to skip the frame
   instead of crashing.

With all three fixed: clicked through the real UI (Decoders → FT8/WSPR →
INTERNAL → Decode On) and got a genuinely working pipeline — real
spectrum trace and waterfall rendering in the FT8 panel, `triggerFT8Decode`
firing every 15s with full 720000-sample windows, the worker responding
in under a second, zero JS errors. This is the first time any of this
has actually run against live data.

### Investigated (live-tested, unresolved): pipeline fully healthy, decoder still returns 0 results every cycle
Despite everything above working, 8+ consecutive 15s cycles all returned
`resultsLen: 0` from the ft8ts worker — while the user's reference tool
got 41 decodes on the same band minutes earlier. Ruled out, with live
measurements:
- **Silence**: no — RMS ~0.033, real non-zero signal content, matching
  visible peaks in the rendered spectrum/waterfall.
- **Sample count/window**: no — consistently 719040-720000 samples
  (15s × 48kHz), correct.
- **Sample rate mismatch**: no — measured real wall-clock-vs-sample-count
  implied rate at 48154 Hz against a declared 48000 Hz — 0.3% off,
  nowhere near enough to break FT8 sync.
- **Mode/bandwidth/frequency**: no — confirmed via `get_state`: USB,
  3000 Hz BW, 14074000 Hz VFO, exactly matching the reference tool's
  settings and the correct FT8 dial frequency.
- **Audio level**: partially — NEXUS never set `audio_volume_percent`
  at all, inheriting whatever SDRConnect's last-remembered value was.
  Tested live (via the browser's existing `set_property` passthrough,
  no restart needed): the original level measured RMS ~0.033 (quiet);
  75% overshot into hard clipping (samples pinned at ±0.9999); 45%
  measured clean (0% samples above 0.95, RMS ~0.166) — a sane level with
  real headroom. Fixed in the backend to send `audio_volume_percent=45`
  in the same enable sequence. Still 0 decodes at this clean level,
  across multiple cycles, so audio level alone isn't the full
  explanation either — though it was a real, separate bug worth fixing
  regardless (the original level really was too quiet).
- **Downmix logic**: compared byte-for-byte against the reference tool's
  `handleAudio()` — both do the identical `(left+right)*0.5` stereo
  interleaved int16 downmix. Not a divergence point.

No confirmed root cause yet for the remaining gap between "pipeline is
provably healthy on every measurable axis" and "decoder finds zero sync
candidates." Worth trying next: run the reference tool and NEXUS
side-by-side against the same moment's audio to see whether the
reference tool decodes what NEXUS's own worker is being fed (would
isolate the ft8ts integration itself vs. some remaining audio-quality
factor not yet measured), and/or add raw-audio capture/playback in
NEXUS for direct A/B listening.

---

### Resolved (live-tested, real decodes): the zero-decode mystery is over
After the fixes below (quicktune buttons, active-decoder count, the 2nd
batch of undeclared variables), re-ran the same live test that had
previously returned `resultsLen: 0` on every cycle. Tuned to 20m
(14074000 Hz, USB, 3000 Hz BW — same settings as every earlier failed
test), enabled FT8 INTERNAL decode, and captured two consecutive real 15s
cycles via direct worker-message instrumentation:

- Cycle 1 (boundary 09:49:15Z): **5 decodes** — `<...> UA3PAB KO84`,
  `EA5IH TF5B -05`, `YO8CNA HB9SDO JN37`, `DL6PCS DL1UDO R+04`,
  `UT7UJ F4LQJ R-09` — SNRs -10 to -20 dB, all plausible.
- Cycle 2 (boundary 09:49:30Z): **5 more decodes** — `R9IT HB9TIH JN36`,
  `EA1KCN OK1UOZ JO70`, `OE5GTE DK7ZT -04`, `OZ5ADW/P R2AL 73`,
  `TF5B EA5IH R-19`.

Both cycles' results also rendered correctly in the actual decode-list UI
(`#ft8DecodeList`), and `DS._activeDecoders` correctly showed
`{"ft8":true}` throughout — confirming the whole pipeline end to end, not
just the worker in isolation.

No single smoking gun isolates which fix tipped this over — the most
likely candidate is the `sendCmd` adapter fix (below): before it, every
3-arg `sendCmd()` call from the FT8-ported code silently sent malformed
JSON, which plausibly means earlier "confirmed correct via `get_state`"
checks were reading stale/default SDRConnect state rather than state this
code had actually, successfully requested. Combined with the earlier
Int16Array-alignment and `ft8NextBoundaryMs` timing fixes (which could
each have quietly corrupted or misaligned every decode window before this
session), it's plausible no prior test ever actually reached the decoder
with a valid, correctly-configured, correctly-aligned window at all. Not
re-litigating further since it's now demonstrably working; flagging the
uncertainty rather than claiming a single root cause we can't fully prove.

---

### Fixed (live-tested): "Active decoders" stuck at 0, and FT8 quicktune buttons non-functional
Two separate bugs reported together, both in the FT8 INTERNAL path:

- **Active decoders showed 0**: `toggleFT8Decode()` flipped `ft8DecodeEnabled`
  and started/stopped the audio feed and cycle timer, but never touched
  `DS._activeDecoders` — the object that actually drives the top status
  bar's "Active decoders: N" count and pill list. Only the older
  bridge-mode `ft8Enable()` path did that (same `'ft8'` slug). Fixed by
  adding `_decoderUpdateUI('ft8', ft8DecodeEnabled);` as the last line of
  `toggleFT8Decode()` — `_decoderUpdateUI()` already null-guards every DOM
  lookup inside it, so it's safe even for a source (INTERNAL) that has no
  dedicated `dec-start-ft8`/`dec-stop-ft8`/`dec-badge-ft8` elements of its
  own. Live-tested: `DS._activeDecoders` now correctly flips
  `{} → {"ft8":true} → {}` across an on/off toggle.

- **Quicktune buttons did nothing**: two compounding bugs, both found via
  live instrumentation (wrapping `sendCmd` to log real calls, then calling
  `setFTband()` directly in the browser console):
  1. The `sendCmd` **adapter was defined but never wired in**. The
     ft8ts-ported code (from the original `WebsocketFT48_v1.html` reference
     tool) calls `sendCmd(eventType, property, value)` — three string
     args — but NEXUS's own `sendCmd(obj)` takes a single object. An
     adapter function (`_ft8SendCmd`) existed to translate between the two
     conventions, but nothing ever pointed the real `sendCmd` identifier at
     it, so every 3-arg call in the ~10 ft8-ported call sites (including
     `setFTband`, hop-mode band switching, mode/bandwidth changes) was
     silently sending malformed JSON instead of a real command. Fixed by
     reassigning the actual `sendCmd` global to a small dispatcher that
     detects both calling conventions and forwards to the original
     object-based `sendCmd`.
  2. Once real commands started firing, `setFTband()` immediately threw
     `TypeError: Cannot read properties of null (reading 'value')` at
     `document.getElementById('filterBWInput').value` —  `filterBWInput`
     is a DOM id from the original reference tool's own standalone UI and
     does not exist anywhere in NEXUS (confirmed via DOM query, zero
     matches; NEXUS's real bandwidth control is the `bw-btn`/`bw-panel`
     click-driven widget, not a plain `<input>`). Fixed both occurrences
     (`setFTband()` and the hop-mode band-switch handler) to read
     `DS.vfos.a.bw`, the same Hz-valued store `tuneVFO()`/`_tuneTo()`
     already read/write elsewhere in this file.
  3. Also part of the same bug class: a second batch of undeclared
     variables beyond the first sweep (which only caught `ft8`-prefixed
     names) — `BAND_COLORS`, `BAND_COLOR_DEFAULT`, `HOP_BAND_NAMES`,
     `HOP_BAND_NUMS`, `hopActive`, `hopCurrentIdx`, `hopCyclesDone`,
     `hopRows`, `sessionCalls`, `sessionDXCC`, `sessionDecodes`,
     `stationMap`, `stationMapInstance`, `stationMapLoading`,
     `stationMapPopup`, `stationMapReady`. `HOP_BAND_NAMES` in particular
     was the first thing `setFTband()` touched, so its missing declaration
     was the actual, literal cause of the button doing "nothing" (silent
     `ReferenceError` before any `sendCmd()` could run at all). Declared
     all of them alongside the first FT8 state-variable batch, with values
     inferred from how each is read/written elsewhere (e.g. `hopRows`
     defaults to `[]`, since `loadHopConfig()` already populates it for
     real at startup from localStorage or its own 20m/17m/15m default).

  Live-tested end to end after all three fixes: `setFTband(9)` now fires
  five correct `sendCmd` object calls (`device_sample_rate`,
  `device_center_frequency`, `device_vfo_frequency`, `demodulator`,
  `filter_bandwidth`) with real, correctly-computed values (e.g. 12m →
  24905000/24915000 Hz), no exceptions, and `ft8CurrentBandName` matches
  the frequency actually sent.

Note: `calculateGain()` (ported verbatim from the reference tool) and its
`audioVolumePercent` variable are still dead/orphaned — never called
anywhere, and would throw on a missing `volumeSlider` DOM element if they
were. Left as-is for now since it's unreachable, not something a user can
trigger; flagged here in case it turns out to matter for the still-open
zero-decode investigation below.

---

## Inherited history (from ../w026/CHANGELOG.md)

## w0.0.5 — DSP performance pass (no feature changes)
- OPT-1: All IIR filters converted to SOS form (sosfilt) with persistent zi state across batches — stable Butterworth, no batch-edge glitch.
- OPT-2: AM DC-block Python loop replaced with vectorised sosfilt.
- OPT-3: np.exp tone correlator replaced with cached Goertzel dot-product in MorseDecoder, AutoCWDetector, RttyDecoder, PocsagDecoder (~4×).
- OPT-4: Decimation anti-alias filter cached; only recomputed on SR change.
- OPT-5: WefaxDecoder buffer changed from Python list to numpy array; PNG zlib compression level 1 (3× faster encode, ~10% larger).
- OPT-6: All decoders gain process_iq(complex64) — RTL bridge passes decimated IQ directly, eliminating float32→int16→bytes→float32 round-trip. process(bytes) shim retained for SDRConnect path.

## w0.0.6 — Band framing fix
Debounced frequency updates (150ms) to prevent VFO/LO display jitter when SDRConnect band framing rapidly changes center freq. Reduced sample_rate re-query spam (was firing on every center change).

## w0.0.7 — VFO-only tuning fix
Server now respects vfo_only=true flag, preventing waterfall pan when user clicks to tune within visible span. Browser-side _updateBandTuned() fix: band button label now updates correctly when selecting different bands. UI enhancements: axis contrast (+93% brightness), marker visibility (+87% opacity on dashed lines), frequency axis grid darker background. Improved readability across all zoom levels.

## w0.0.8
Reserved for debugging iteration (never released).

## w0.0.9 — VFO-only waterfall lock
Complete fix for SDRConnect path. Backend no longer sends device_center_frequency when vfo_only=true, keeping hardware LO locked while VFO marker moves. Waterfall stays anchored to original center frequency during VFO-only clicks. VFO persists and does not revert. Fixed variable scoping bug in SDRConnect tune handler.

## w0.1.0 — DARKSKY NEXUS frontend rewrite
Ring buffer waterfall, digit VFO display, five-column HF intelligence panel, EIBI/AOKI lookup, DX spots, NCDXF beacons, space weather, SigIDWiki, VOLMET/reference channels, band condition matrix with propagation reachability scoring, numbers stations, frequency list importer. Spectrum ring buffer enables instant floor/range/palette recolour without re-render.

## w0.1.1 — Signal intelligence expansion
BUILTIN_SIGNALS database (60 utility/military/maritime/aviation/digital signal entries) merged into lookup() alongside EIBI — returns results for non-broadcast frequencies. OurAirports.com integration: get_air_freqs command downloads and caches airports.csv + airport-frequencies.csv, returns nearby VHF airport frequencies sorted by distance. EIBI auto-download on startup when files missing. lookup command accepts freq_mhz override parameter. Space weather via bridge (get_space_weather command) bypasses browser CORS restrictions on NOAA SWPC endpoints.

## w0.1.2 — Tuning architecture overhaul
_tuneTo() helper with inSpan/forceMoveLO logic centralises all tuning paths. setMode() gains silent flag to prevent race condition with tuneVFO(). VFO/LO display swapped to match SDRConnect convention. Tune line recoloured red (#ff2244) for visibility. WebSocket ping_interval=None disables keepalive disconnect on browser background. Bookmark persistence via bridge bm_save/bm_delete/bm_list. Spectrum markers (bookmarks + EIBI ghost markers) drawn on sp-canvas. PEAK hold, dB GRID, LABEL toggle replace TSM/AI/Noise stubs.

## w0.1.3 — RDS display
Inline brand-bar strip shows PS name, PTY, radiotext when WFM tuned with RDS lock. SNR colour-coded (+green/yellow/orange) with signal power readout. BW preset dropdown with mode-aware presets. Bands button moved alongside BW below mode group. Enhanced cinematic mode: live spectrum horizon mirror, station name resolution (RDS/EIBI/bookmark), SNR signal bar, space weather panel, signal-reactive particles, smart floating labels from bookmarks. SIG INTEL dedicated tab with three-column layout. Signal Intel tab wires lookup results across EIBI + SigDB sources with SigIDWiki article lookup.

## w0.1.4
(frontend iteration — see DARKSKY_NEXUS.html changelog)

## w0.1.5 — nRSP-ST / IQ-Lite groundwork
- Device detection — active_device and valid_devices queried on connect. nRSP-ST detected by device name; state gains device_type and iq_lite_capable. device_caps broadcast to frontend on connect.
- Binary router fix: type 1 (PCM audio 48kHz) was silently dropped on RSPdx — now downmixed to mono complex64 and fed to decoders via process_iq(), restoring decoder operation on the standard audio path.
- IQ-Lite type 2 handler: branches on iq_lite_capable; applies 5-pole Butterworth LPF then decimates 4× (192kHz→48kHz) before decoders.
- ADS-B: removed duplicate adsb_poller stub and duplicate create_task. Added readsb (brew) probe URLs; frontend notices updated for macOS.
- HFDL/VDL2 auto-launch infrastructure added: _find_dumphfdl/vdl2, _launch_dumphfdl/vdl2, process watchdog in UDP server loops. hfdl_start/vdl2_start accept device/freqs/sample_rate overrides.
- Frontend notice panels updated with accurate macOS build instructions.

## w0.1.6 — nRSP-ST connection architecture clarified
WebSocket API (port 5454) lives in SDRConnect desktop, not nRSP-ST firmware. nRSP-ST exposes port 9001 (browser UI) and port 50000 (SDRConnect client protocol). _is_nrsp_st now set solely by active_device name (not --sdr host). Stream mode parsed from active_device suffix e.g. "(IQ Lite)" — authoritative on every property_changed, handles Compact/IQ Lite/Full IQ correctly including mode switches from the frontend button strip. set_stream_mode selects exact entry from valid_devices list (base name matched) — fixes previous bug where mode suffix was appended to the already-suffixed active_device name, producing an invalid selector.

sample_rate reported as 192000 when iq_lite_capable; hw_sample_rate preserved for mode switches. Frontend applyState forces liveSR=192000 in IQ Lite. center_hz processed before vfo_hz in applyState — fixes stale liveCenter when SDRConnect auto-changes sample rate.

Click-to-tune LO lock fix: spectrum and waterfall click handlers pass forceMoveLO=true; _wfClick/_spClick updated to match; duplicate addEventListener calls removed (were double-firing every click). Demodulator re-assertion 350ms after LO move — fixes audio drop on nRSP-ST when SDRConnect resets pipeline on device_center_frequency. Startup LO re-centre: _recentre_lo_on_vfo task fires 1.5s after connect; rebroadcasts state without moving hardware (moving LO caused SDRConnect to cascade VFO offset, changing tuned frequency).

fldigi frequency sync: full LO tunes now call set_frequency() on fldigi. VFO-only micro-tunes do not spam fldigi. fldigi toast: transition guard (false→true only); silent flag on browser_handler and fldigi_tune status responses.

Spectrum colour panel: BASIC row deduplicated (8 distinct hues); WATERFALL row replaced with one swatch per palette pulled from each palette's actual signal peak stop — no duplicates across either row.

Version string broadcast to frontend (server_version); mismatch toast added to catch stale cached HTML (Cmd+Shift+R prompt). All version strings updated from w0_1_4 → w0_1_5.

## w0.1.7 — SSH Launcher integrated (Connection Wizard modal)
On startup, a full-screen wizard modal blocks the main UI and offers two modes: SDRConnect Server (SSH) or nRSP-ST / Local.

SSH mode: paramiko connects to remote Linux host, starts sdrconnect --server, waits startup_delay seconds, launches local SDRConnect.app via open -a. All SSH I/O runs in daemon threads; results streamed to browser via existing broadcast_json channel.

Stop sequence preserved exactly from app.py (critical order):
1. Close local SDRConnect (pkill -TERM -x \<appname\>)
2. Wait device_release_wait seconds for RSPdx handle release
3. Kill remote server (pkill via fresh SSH connection)
4. Close original SSH channel and connection

Device release wait is mandatory — skipping it causes SIGSEGV in swig_bindings.dylib on next SDRConnect launch.

SSH config persisted to ~/.darksky_nexus/ssh_config.json. Passwords never written to disk (session-only). ssh_get_config, ssh_get_status, ssh_test, ssh_launch, ssh_stop, ssh_reset commands handled in browser_handler via _handle_ssh_cmd(). SSH status and last 50 log lines replayed to late-joining browsers. Brand bar: ssh-strip with ⬡ SSH badge and Stop button appears when SSH session is running; turns amber during device release wait.

PyInstaller packaging: _resource_path() helper added for frozen bundle compatibility; spec file, build scripts, requirements.txt, and README_BETA.md produced for macOS and Windows release builds. New dependency: paramiko (pip install paramiko).

## w0.1.8 — Performance optimisation pass (no feature changes)
**Python (PY-01–PY-23):**
- PY-01: _UI_FRAME_DT constant replaces 1.0/MAX_UI_FPS division per frame.
- PY-02: Pre-allocated bytearray frame buffer — no per-frame byte concat.
- PY-04: FFT accumulator averaged into pre-allocated _fft_avg buffer.
- PY-05: fftshift applied once per display frame (was once per FFT chunk).
- PY-06: log1p + normalise in-place; single np.multiply, no temp arrays.
- PY-07: IQ float conversion (uint8→float32) in-place with np.subtract/multiply — eliminates two intermediate arrays per RTL batch.
- PY-09: broadcast_json caches last serialised state; skips json.dumps when state dict is unchanged (fired on every property change).
- PY-13: Hot-path regex patterns (APRS weather, callsign, course, alt) compiled once at module level, not per-call.
- PY-14: Dead import (numpy.lib.stride_tricks.as_strided) removed from RttyDecoder.analyse().
- PY-17: asyncio.get_event_loop() replaced with get_running_loop() throughout (10 sites) — correct modern API, avoids deprecation.
- PY-19: _adsb_fetch closure hoisted above adsb_poller while-loop — no new function object created on every 1s iteration.
- PY-20: rigctld dump_state response hoisted to module-level bytes constant — no per-connection string build/encode.
- PY-22: WSJTX UDP helpers (struct packs, socket, helper fns) hoisted to module level — no per-ft8_tune import/def/pack.
- PY-23: SDRConnect catch-all property/event log calls downgraded from log.info to log.debug — f-strings not built at INFO level.

**JavaScript (JS-01–JS-11):**
- JS-01: Waterfall inner loop uses wfColormap LUT for colour lookup — 3 array reads replaces per-pixel gradient interpolation loop.
- JS-02: Five frequently-queried static DOM elements cached at init.
- JS-04: Nine frequency digit elements cached after initDigits(); no getElementById on every animLoop frame (60fps).
- JS-05: _drawBandplan gated on _bpDirty flag; only redraws when liveCenter or liveSR changes.
- JS-06: updateLiveFreqAxis() skips redraw when center/SR/zoom key unchanged since last paint.
- JS-08: _wfBufInterp (Catmull-Rom) inlined into waterfall pixel loop — eliminates one function call per pixel.
- JS-09: Math.pow skipped in waterfall loop when wfGamma === 1.0.
- JS-11: applyState coalesces axis/tune-line flushes to a single RAF per message instead of firing up to twice per state update.

## w0.1.9 — Critical fixes and new features
- iq_stream_enable gated — was sent unconditionally, crashing RSPdx in Compact mode. Now only sent for nRSP-ST in IQ Lite/Full IQ mode.
- WSPR decoder: wsprd integration with live decode table, SNR/drift display, callsign/grid/power columns. Two-minute cycle tracking.
- WSPRnet propagation map: replaced blocked iframe with self-hosted Leaflet map (CartoDB Dark tiles). Spots plotted as colour-coded circle markers with dashed great-circle arc lines from RX home. SNR colour coding: green >−10, amber >−20, blue otherwise.
- Freq axis cache fix: canvas.width|height included in cache key so initCanvases() blank does not suppress redraw on resize.
- Waterfall click fix: explicit withinSpan check gates forceMoveLO — in-span clicks move VFO only; out-of-span clicks recentre & flush.
- BW dropdown lazy init: _elBwPanel assigned on first click, not at parse time (element defined later in document).
- BW panel compact: reduced padding; removed "OTHER" section; 160px.
- Bands panel: 40m moved to first position in second row (spacer div).

## w0.2.0 — fldigi embedded control surface
- Live fldigi waterfall canvas in each decoder tab right column, polled via wf.get_data() XML-RPC at 5 fps, rendered onto \<canvas\>.
- Carrier line overlay drawn on waterfall; draggable to retune decoder.
- Click on waterfall sets modem carrier via modem.set_carrier().
- BW bracket handles for PSK/RTTY/Olivia — drag to set modem.set_bandwidth().
- Per-mode controls: AFC toggle, squelch on/off + level, CW WPM slider.
- Backend: wf_poller() asyncio task polls wf.get_data()+wf.get_size() and broadcasts fldigi_wf WS messages.
- New WS commands: fldigi_set_carrier, fldigi_set_bw, fldigi_set_wpm, fldigi_set_afc, fldigi_set_squelch — map directly to XML-RPC calls.
- fldigi runs hidden in background; NEXUS is sole user interface.

## w0.2.1 — Custom frequency list integration (forked from w0.2.0)
- Imported frequency lists (Frequency Lists drop zone, HF_CUSTOM_LISTS) now participate in frequency lookup, not just storage.
- hfCustomListLookup() matches imported list entries against the tuned frequency (±5 kHz HF / ±25 kHz VHF+, same tolerance as EIBI/SigID) and injects them into the shared results array used by SW SCHEDULE, the freq-intel bar, and the SIG INTEL tab.
- New 'CUSTOM' source tag/colour wired into siRenderSWL, the SIG INTEL broadcast column, and the freq-intel bar chip rendering.
- No backend changes — matching is entirely client-side against already-imported lists; existing EIBI/AOKI/SigID lookups unaffected.

## w0.2.2 — New decoder capability fork (forked from w0.2.1)
- Rivet-derived numbers-station/spy-HF decoder: Baudot, CIS-36-50, CCIR 493-4, CROWD-36, FSK200/500, FSK200/1000, XPA/XPA2.
- FreeDV HF digital voice decoding (Codec2-based), filling the gap left by DSD+ (VHF/UHF trunked voice only, no HF SSB digital voice).
- SigDigger-inspired signal-analysis aids under evaluation (phase-plane/constellation display, SNR estimation) — GPLv3 licensing implications to be assessed before any direct porting.

## w0.2.3 — IQ Lite myth-busting (forked from w0.2.2)
- Confirmed via SDRplay's own RawIqWriter reference client + decoded packet capture + direct SDRplay support confirmation: IQ Lite and Compact modes NEVER deliver binary type-2 IQ frames on the nRSP-ST. They exist only for demodulated/decoder-rate audio streaming at low bandwidth — not raw IQ. The w0.1.5 "IQ-Lite type 2 handler" groundwork was speculative (built from API spec inference) and was never actually confirmed working; it has never decoded a real signal. iq_lite_capable is now hardcoded False — the dead 192kHz decode branch is left in place but permanently unreachable.
- preferred_stream_mode default changed from 'IQ Lite' to 'Full IQ'. Bandwidth re-tested directly: nRSP-ST → Mac over Wi-Fi sustained 2 MSps Full IQ (~64 Mbps) cleanly for 30+ seconds via RawIqWriter, zero dropped/irregular frames. The original "bandwidth too limited for Full IQ" conclusion was wrong when tested in isolation — however Jon separately observed a real "fulliq stopped due to insufficient bandwidth" failure with NEXUS AND SDRConnect BOTH running simultaneously. This was NOT reproduced by today's isolated RawIqWriter test and needs validation with the full NEXUS pipeline live before Full IQ is trusted as default for real use.
- _check_iq_mode warning previously fired only for Compact mode and trusted SDRConnect's self-reported iq_streaming/full_iq/streaming_mode property rather than counting actual type-2 frames. Now also warns for IQ Lite, and is frame-count based (no type-2 frame for 3+ seconds = warn), matching the actual failure mode diagnosed rather than trusting a property that may not reflect reality.

## w0.2.3.1
Built .app: erratic/jumping spectrum (smooth in SDRConnect itself). Root cause: the .tobytes() fix made the Full-IQ self-computed FFT broadcast finally succeed (previously crashed every frame, silently caught) — but it broadcasts as a competing 0x01 spectrum frame alongside SDRConnect's own native type-3 spectrum, which was ALSO broadcasting all along. Two independent spectra (512-bin native vs 1024-bin self-computed, different scaling) interleaving on the same canvas looks exactly like erratic jumping. Confirmed via rotating log file (~/Library/Logs/DARKSKY NEXUS/darksky_nexus.log) showing zero errors and steady climbing frame counts — backend was healthy, this was a frontend display collision, not a crash or data problem.

Fix: disabled the Full-IQ FFT recompute + broadcast entirely — native type-3 already covers Full IQ correctly. Decoders unaffected (they read raw bytes directly, not the FFT output). Old code kept commented for reference.

## w0.2.4 — Decoder tab UI audit + RTTY scope refinements (forked from w0.2.3)
- RTTY tone scope: narrowed scope canvas, added a dedicated decoded-text column beside it; refined waterfall colour LUT, added EMA smoothing + curve-smoothed line rendering + Hz gridlines.
- RTTY zoom/pan: replaced fixed [0,hi] zoom levels with an independent width+pan model (500 Hz – 5000 Hz widths, clamped to the backend's real -1500..4500 Hz audio_fft span); added click-and-drag panning of the scope view and a "centre on tones" button.
- Olivia/Contestia/MFSK/Hell/DominoEX: added a dedicated Start button (previously only Stop existed; starting relied entirely on clicking a mode button).
- CW (NEXUS engine): was leaving most of the panel blank — the 260px stats/sliders column had no decoded-text output at all, and the fldigi column (the only place text appeared) is hidden in NEXUS mode. Added a decoded-text box to the NEXUS column.
- PSK31 / NAVTEX: these are fldigi-only decoders with no real NEXUS decode path, yet exposed a NEXUS/FLDIGI engine toggle that just showed an empty gap in NEXUS mode. Removed the toggle.
- FreeDV: the panel was almost entirely empty space around a small 320x48 VU meter. Added a fuller live signal scope.
- ACARS: added a live map (Leaflet, matching the WSPR/FT8/AIS pattern) showing aircraft positions when lat/lon is present in decoded messages — previously table + static text only, no positional display at all.

## w0.2.6 — Re-synced from w0.2.4 (2026-06-23)
The original w0.2.4→w0.2.6 fork was taken before several w0.2.4 fixes landed, leaving w0.2.6 stale. Replaced w0_2_6_NEXUS.py and DARKSKY_NEXUS_w0_2_6.html wholesale with current w0.2.4 content (self-references renamed; historical changelog entries above preserved as-is). Pulls in, among other w0.2.4-era fixes: the CW/RTTY engine-toggle-stuck-on-fldigi fix (with toast warning), and the AIS speed/course/heading/status/destination field-name fix. Docs (md + docx) and build/packaging scripts (macOS/Windows spec + build scripts, BUILD_NOTES.md) synced to match.

**Fixed (2026-06-23):** CW Skimmer "active but no signals" bug — the main CW Start button (decoderStart('cw') -> skStart('monitor')) only changed a badge label and sent a no-op probe; it never set skDetectOn or started _skDetectLoop(), the loop that scans the spectrum for candidate signals and feeds them to the backend's CWSkimmerPool via skimmer_set_channels. Result: the header/footer showed "CW Skimmer active" and the decoder itself was genuinely running, but the Skimmer waterfall and decoded-text panels stayed on placeholder text indefinitely unless the user separately clicked "Start Detection" in the Skimmer Channels panel. skStart() now mirrors skToggleDetect()'s logic for monitor mode so the main Start button drives detection directly (HTML/JS only — no backend change needed).

**Added (2026-07-09):** Light/dark theme toggle. New 🌙/☀ button next to the UI-scale control in the brand bar; persisted via `localStorage('nexus_theme')`, same pattern as the existing UI-scale control (`_uiScaleInit`/`_uiScaleSet`). Structural chrome colours that were hardcoded hex scattered across the stylesheet's three `<style>` blocks (brand bar, modal overlays, waterfall info popups, input fields) were pulled into new CSS variables (`--bar-bg`, `--scrim-67`, `--scrim-80`, `--tag-bg`, `--input-bg`) so a new `:root[data-theme="light"]` override block can retheme them in one place. The wide semantic/decorative colour palette (`--green`/`--yellow`/`--red`/`--orange`/`--purple`/`--teal`/`--violet`/`--amber`/`--cyan`/`--lime`, used for per-decoder/per-signal-type colour coding) is left unchanged in both themes — meaningful data colours, not chrome. The spectrum/waterfall canvas, the Signal Radar/DSP-graph scope canvases, and Cinematic Mode's dark theatrical overlay are also deliberately left dark in both themes: every SDR app keeps its RF display dark regardless of UI theme, and Cinematic Mode is its own intentionally theatrical dark viewing mode.

**Fixed (2026-07-09):** Northsound 1 misidentified in the RDS strip as "ALL FM 96.9 · Independent". `UK_FM_DB`'s Northsound 1 entries (96.9/97.6/103.0 — its local relay frequencies) all listed `ps:'NS1'`, but the station's real on-air RDS PS code is `N'Sound1` — confirmed via a live capture on w028. `_ukFmEnhance()` matches by exact PS string, so the mismatch always fell through to the generic "unidentified station on this shared frequency" placeholder. Corrected to `ps:"N'Sound1"` in all three occurrences (same table, same fix applied to w027 and w028). This is a single confirmed data-quality fix, not a full audit of the table.

**Added (2026-07-12):** FT8 INTERNAL audio clip protection + gain compensation, ported from `WebsocketFT48_v1.html`'s proven design (user-reported: "if its too high in nexus i hear distortion"). Two things were missing entirely:

1. **Auto-reduce on clip.** `ft8HandleAudioFrame()` now scans every raw incoming audio packet's int16 samples for clipping (`> 0.99` full-scale) before any gain is applied — clipping originates at SDRConnect's own device-side `audio_volume_percent`, not from anything client-side. The instant a clipped sample is found (and a 1s cooldown has elapsed, to avoid a burst of clipped packets firing a flurry of commands), it steps `DS.volume` down by 4 and sends `set_property audio_volume_percent` back to SDRConnect through the same path the main toolbar's VOL nudge buttons use, and updates the `vol-val` display + a toast so it's visible when it happens. Live-tested with a synthetic clipped frame (76% → 76 sent as 72... confirmed exact -4 step and correct `sendCmd` payload), confirmed the cooldown blocks an immediate repeat, and confirmed a quiet frame never touches volume.
2. **Gain compensation.** Cross-checked against the reference tool's own reverse-engineered SDRConnect volume-response curve (`0.8070 / (0.0301 * 10**(0.034*pct))`, 1.0 above 42%) — applied to the mono samples before they reach both the decoder and playback, so reducing volume to fix clipping doesn't leave things sounding too quiet. NEXUS has no separate local-only playback slider (the reference tool's extra `slider` factor), so this is just the correction term on its own.

Also found and fixed a related contributing cause while tracing this: NEXUS's main toolbar VOL control (`adjustVolume()`, default 80%) sends `audio_volume_percent` completely independently of the FT8-specific connect-time value, with no clip protection of its own — so any manual VOL nudge could silently override a safe level with zero feedback. The new auto-reduce logic now catches that in real time regardless of how the volume got high, so it self-corrects going forward. Backend default (`w030_NEXUS.py`) also dropped from 45 to 25 on connect, matching the reference tool's own proven-safe starting point — live-tested afterward: 398 real audio frames over 8 seconds at the new default, zero clipping, zero reductions needed.

**Fixed (2026-07-12):** FT8 INTERNAL spectrum/waterfall left a growing block of dead black space on the right after the column was widened 340px→440px (user-reported, screenshot). `FT8_DISPLAY_BINS` (~284 bins, fixed by the 3320 Hz passband and FFT size — independent of canvas width) was being drawn with a fixed 1-bin-per-pixel mapping (`FT8_BINS_PER_PX = 1`) baked in when the column was still 340px wide, close enough to 284 that the ~56px shortfall wasn't obvious. At 440px the shortfall grew to ~156px: every x beyond ~284 read past the end of the `ft8FftMag`/`ft8FftCumSum` arrays (`undefined`), which the `-999`-initialized fallback then drew as "no signal." `ft8DisplayFrame()` now computes bins-per-pixel from the real canvas width every frame (`binsPerPx = bins / W`) and handles both directions — stretch (nearest-bin lookup) when the canvas is wider than the available bins, the original compress-and-take-max behavior when it isn't — so the trace and waterfall always fill the actual column width.

**Fixed (2026-07-12):** FT8 INTERNAL decode-list rows (UTC/dB/DT/Hz/Message columns) were unreadable in the light theme — user-reported, screenshot. `appendFT8Decode()` hardcoded row text color as `#c9d1d9`, a near-white light grey chosen to read well against NEXUS's dark background, `#3fb950` for CQ rows — literal hex instead of the theme-aware `var(--text)`/`var(--green)` this app already uses everywhere else (see the `:root[data-theme="light"]` override block; light/dark toggle added 2026-07-09). Near-white text on the light theme's near-white background was effectively invisible. Swapped both to `var(--text)`/`var(--green)`, which resolve correctly in both themes — live-tested in light mode, rows now render as dark, readable text with the CQ row still clearly green. The Country column's separate `#8b949e` (mid-grey, already legible against both light and dark backgrounds) was left as-is — not part of what was reported.

**Fixed (2026-07-12):** RTTY (NEXUS engine) decoded noise into plausible-looking garbage text with zero indication anything was wrong — user-reported ("im currently tuned to ddw on 30m ... check") while trying to decode DWD Pinneberg weather RTTY. Live-verified two ways: tuned to a frequency confirmed via a zoomed waterfall screenshot to have no visible carrier at all, and the decoder still produced continuous uppercase text ("ZBAKDEIVKJDGUTWK" etc.); separately, correctly-tuned DDK9 reception (real signal confirmed present, 8.2dB SNR, autodetect independently found a genuine 50-baud 2-tone pair at 85% confidence) *still* produced unreadable text with no recognisable synoptic groups, ruling out mistuning as the sole cause.

Root cause, in `RttyDecoder._process_bit_block()` (`w030_NEXUS.py`): the bit decision (`bit = 1 if s_p > m_p else 0`) only ever compared mark-tone power to space-tone power *against each other* — there was no check anywhere that either tone actually cleared the noise floor. Two independent noise-power readings are still "greater than" each other roughly half the time, which is enough for the Baudot start/stop framing check to pass by chance often enough to keep grinding out characters indefinitely. The CW decoder (`MorseDecoder`) in the same file has exactly this kind of gate (`threshold_db`/live `snr`, trailing-minimum noise floor); RTTY never got one.

`MorseDecoder`'s trailing-minimum-power-over-time technique doesn't transfer to RTTY: CW has genuine on/off keying, so its floor naturally tracks the quiet gaps between dits/dahs, but RTTY has no gaps — mark or space is continuously transmitted for the whole duration of a real signal, so total (mark+space) power stays roughly constant whether it's real signal or just band noise. Fix: added a third Goertzel reading at `mark + 2.5*shift` (a patch of passband that should be empty during a real signal) as a live *spectral* noise reference each sub-block, computed an SNR (`self._snr_db`, default `squelch_db = 6.0`), and gated new start-bit acquisition on `self._locked` — an already-in-flight frame is left alone (the existing stop-bit check still discards it if it's genuinely bad), this only blocks *starting* new frames on pure noise. Backend broadcasts the live lock state/SNR (`rtty_signal`, throttled to 2/s) so the frontend can show it honestly instead of only ever showing scrolling text with no way to tell "no signal" from "confidently decoding noise" apart — new Signal: LOCKED/NO SIGNAL badge + dB readout in the RTTY Parameters panel, wired via `rttyHandleSignal()`.

Also fixed while investigating: the "Auto-detect baud & shift" status label got permanently stuck on "Capturing…" whenever a capture reply was correctly discarded as stale (e.g. right after unchecking the box mid-capture) — nothing ever reset the text back to idle. `rttyApplyParams()` now resets it to `—` at the point it bumps the generation counter.

Note: the DDK9/DDK2/DDH7/DDH47 preset frequencies were re-examined during this investigation (following a live retune that briefly suggested a ~900Hz preset error) and found to already be correctly calibrated — DDK9 specifically carries a June 2026 code comment documenting a real 30.8s IQ-capture calibration (204/204 chars, 0% stop-bit failure) at its current mark=1022Hz/shift=446Hz/dial=10.100MHz values. No preset changes were made; the earlier live "fix" during investigation (retuning to 10099.103 MHz) was based on a transcription slip (used mark=1922Hz instead of the preset's actual 1022Hz) and was reverted.

**Added (2026-07-12):** RTTY live sync-health diagnostics, to keep chasing the "still unreadable even while LOCKED" question above without needing server console access. `RttyDecoder` now tracks a second, never-reset set of counters (`_ui_start_armed`/`_ui_stop_ok`/`_ui_stop_fail`/`_ui_margin_sum`/`_ui_margin_n`, mirroring the existing `_diag_*` fields used by the server-side 5s log but kept independent so reading them doesn't race with that log's own reset cycle) and includes them in the `rtty_signal` broadcast's `diag` field; frontend stashes the raw message on `window._rttyLastSignal` for inspection. Live capture against a genuinely LOCKED DDK9 signal (10.4dB SNR): mark/space margin 0.508 (healthy — rules out a tone/frequency mismatch), stop-bit failure 20.9% (much improved vs. the historical 45-100% that characterized the pre-PLL-fix state, but nonzero), yet the actual decoded text still had zero recognisable synoptic-bulletin structure. Conclusion: most likely genuinely marginal real-world HF propagation on 30m at the time of testing rather than a remaining software bug — the moderate SNR and mid-range margin are consistent with a real but weak signal, and bit-level errors inside frames that still pass the coarse stop-bit check wouldn't show up in `stop_fail_pct` at all. Left open rather than guessing further; a longer raw recording (NEXUS's existing REC button) during a stronger propagation window, brute-force-analysed offline the same way the original PLL/bit-polarity bugs were actually proven, would be the next concrete step if this needs revisiting.

**Fixed (2026-07-12):** FT8/WSPR bridge panel (`#tab-ft8`, the WSJT-X-source panel — a different, older panel than the FT8 INTERNAL tab fixed earlier in this session) had a neon lime (`#c8ff00`) color clash in the light theme — user-reported, screenshot. The FT8 mode tab, Start button, mode-selector buttons, and all 11 quick-tune frequency chips (plus their "FT8" label, which was a stray inline-style duplicate of the already-existing-but-unused `.ft8-freq` class) rendered in bright lime-yellow, which reads as harsh and low-contrast against the light theme's white panels — this whole panel's neon-glow scheme was designed for the dark theme and was never touched by the 2026-07-09 light-theme pass (which only covered app chrome, not this panel's per-mode decorative palette). Added a `:root[data-theme="light"]` override for `.tab.t-ft8.active`, `.ft8-btn.go`, `.ft8-mode-btn.active`, `.ft8-freq`, `.ft8-freq-btn` (+ hover/active states), `.map-toggle-btn.active`, and `#rtty-mark-label` (the RTTY tone-scope's "M" marker, same lime, same problem, fixed proactively while the override pattern was already in hand) — darkened to an olive/chartreuse (`#6f8f00`) that keeps the same hue identity but is actually legible on white. The other 6 quick-tune-row accent colors (teal/orange/violet/blue/pink/green, one per mode) were deliberately left untouched: those are cooler, mid-toned hues that already contrast fine against white, unlike lime — the same reasoning already applied to `.ais-freq-btn`'s cyan chips earlier in the file. Live-verified via zoomed screenshot in light mode.

**Fixed (2026-07-13):** FT8 INTERNAL's "Decode On"/"Decode Off" toggle button was hard to read in *both* themes, and inconsistent with every other decoder in the app — user-reported, two screenshots (light + dark). Root cause wasn't theme-specific: `toggleFT8Decode()`'s ON state set hardcoded inline `background:'#0F6E56'`/`borderColor:'#1D9E75'` but never touched the button's text color away from `var(--muted)` — a deliberately low-contrast, secondary-looking tone by design — so muted grey-blue text sat on a fixed dark teal background regardless of theme. A `.ft8-ctrl-btn.decode-on` CSS class already existed with the correct green-on-tinted-green styling but was dead code, never applied. Rather than just fix the color, converted the single toggle into a `▶ Start` (green) / `■ Stop` (red) button pair — matching the convention every other decoder in the app already uses (RTTY, CW, and the WSJT-X FT8 bridge panel directly above this one in the same tab). `toggleFT8Decode()` now shows/hides the pair instead of relabeling one button; added idempotent `ft8NativeStart()`/`ft8NativeStop()` wrappers so the two buttons can't double-toggle state; updated `resetFT8()` and `toggleHopping()`'s button-locking logic for the new two-button structure. Live-verified: Start (green) ↔ Stop (red) swap correctly on click.

**Added (2026-07-13):** Drag-to-resize handle between FT8 INTERNAL's decode-list and propagation-map columns — user-reported (fullscreen screenshots): the map was fixed at 340px while the Message column had unused whitespace on wide displays. Added a 6px `#ft8MapResizeHandle` splitter (col-resize cursor, highlights on hover/drag) that adjusts `#ft8MapCol`'s width live via mousemove, calls `stationMapInstance.resize()` during the drag so the map repaints instead of going blank/clipped (MapLibre caches its canvas size), and persists the final width to `localStorage['nexus_ft8_map_w']` (clamped 220–900px) so it's remembered across reloads. Live-verified: dragged 340px→440px, map/decode-list columns resized correctly, survived a full page reload.

**Fixed (2026-07-13):** FT8 INTERNAL's propagation map wiped every station marker and decode-list row the instant you clicked a different band button — user raised this after the HamDash comparison ("persistence of 'spots' during a session, if i have decodes from multiple bands on the map"). `setFTband()` (the manual band quick-tune handler) called `clearFT8Decodes()` on every switch, which does a full `stationMap.clear()` + list wipe — Hop mode's own band-advance path (`advanceHop()`) never did this (it only appends a separator row), so a Hop session already accumulated multi-band spots for free while manual band-switching didn't. Brought manual switching in line with Hop mode: `setFTband()` now appends a `'{BAND} ({MODE})'` separator into the decode list instead of clearing it, and leaves `stationMap` alone, so markers from every band visited this session stay on the map — already distinguishable by the existing per-band `BAND_COLORS` marker coloring and the map's band-color legend. `clearFT8Display()` (spectrum/waterfall canvas reset — unrelated to decodes/map, just stale-bin cleanup for the new band's frequencies) is still called, and the explicit "Clear" button still does a full wipe via unchanged `clearFT8Decodes()`. `toggleFT8Mode()` (FT8⇄FT4 switch) still clears everything too, deliberately left alone — the two modes' decodes aren't really comparable on one map.

**Added (2026-07-13):** Map style picker for the FT8 INTERNAL propagation map, following on from the persistence fix above (user asked "be able to select different opensource maps?"). New dropdown in the map column header, next to "PROPAGATION MAP", switching between 5 no-API-key raster providers: CARTO Dark (existing default, unchanged), CARTO Light, CARTO Voyager, OpenStreetMap Standard, and Esri World Imagery (satellite). Implementation: `initStationMapInstance()`'s hardcoded CARTO-only raster source/layer (`carto-dark`/`carto-dark-layer`) was generalised to `basemap`/`basemap-layer`, driven by a new `MAP_PROVIDERS` table; `changeStationMapProvider(key)` removes and re-adds that source+layer (inserted below the `station-circles` marker layer so pins stay on top) rather than using the raster source's `setTiles()` method, since each provider needs its own attribution string too, not just new tile URLs. Selection persists to `localStorage['nexus_ft8_map_provider']` and is restored on next load. Live-verified all 5 providers render correctly (Esri satellite imagery over the Alps, OSM/Voyager label tiles over Europe); two providers briefly *appeared* blank in screenshots taken immediately after switching, but MapLibre's own tile-cache state (`loaded`) and a direct pixel-content check both confirmed the tiles were actually present — the same screenshot-capture lag already seen and worked around earlier this session, not a real rendering bug.

**Added (2026-07-13):** 3D globe view with home-QTH propagation arcs for the FT8 INTERNAL map, following the HamDash comparison earlier in this session. New "🌐 Globe" button next to the map-style dropdown toggles the existing MapLibre instance between the flat 2D map and a rotatable 3D globe (`map.setProjection({type:'globe'})`), which required bumping the loaded MapLibre GL JS version from 4.7.1 → 5.1.0 (cdnjs) — globe projection doesn't exist at all in v4.x. Checked v5's breaking-changes list against everything this file actually calls; nothing used here is affected.

Deliberately built as its own toggle rather than folded into the app's existing "Cinematic Mode" (🎬) — that's a generic full-screen ambient FFT-bin visualizer (5 abstract scenes: nexus/retro/bars/phosphor/polar) that works from any tab and has nothing to do with FT8 or maps; reusing it here would mean feeding it completely unrelated data and would surprise anyone who already knows what 🎬 does elsewhere in the app. The name collision with HamDash's own "Cinema Mode" branding is coincidental.

Arcs: `greatCircleLine()` (standard spherical slerp, 64 segments) draws a proper curved geodesic — a straight 2-point line would cut through the globe rather than follow its surface — from `HF_LOC` (the existing HF Utility "your location" setting, already lat/lon with its own geocode-search UI; no new Maidenhead-locator input needed) to every entry in `stationMap`, colored by the station's band via the existing `BAND_COLORS` table. Necessarily home-centric (spokes from one point), not HamDash's many-to-many "cloud" — NEXUS only has its own receiver's decodes, not PSK Reporter's aggregated network (a separate reporting feature, not yet built — see below). A distinct home-QTH marker (white fill, cyan ring) sits at `HF_LOC` regardless of globe/flat mode; arcs themselves are hidden in flat mode (a `visibility` layout toggle, not removed) since they're only really legible on the globe. Globe/flat state and the arc geometry both refresh live if the user changes their saved location via the HF Utility "Change" link. Live-verified with synthetic station data (US/Australia/South Africa entries): arcs rendered with correct great-circle curvature and per-band legend colors, home marker positioned correctly over the UK, and toggling back to flat mode correctly hid the arcs layer while leaving station markers visible.

Not built yet, flagged as a separate follow-up: reporting NEXUS's own FT8 decodes out to PSK Reporter (WSJT-X-style spot upload) — backend work, needs PSK Reporter's actual ingestion protocol confirmed before implementation.

**Fixed (2026-07-13):** Globe arcs were invisible whenever a non-default map style was selected — user-reported, screenshot showing 20 real decodes and an active Globe toggle with no visible arcs. Root cause: `changeStationMapProvider()` re-inserts `basemap-layer` using `stationMapInstance.addLayer(layer, 'station-circles')` — which places the new layer *immediately below* `station-circles`, i.e. **above** `station-arcs-layer` and `home-qth-layer`, both added earlier in the original layer stack. Switching away from the default CARTO Dark style (added the day before) silently painted opaque basemap tiles right over the arcs and home marker on every subsequent redraw — they were still being drawn, just hidden underneath. Fixed by choosing the `beforeId` from the lowest overlay layer that actually exists (`station-arcs-layer` → `home-qth-layer` → `station-circles`, in that preference order) so the swapped-in basemap always lands at the very bottom of the stack regardless of which layers have been added. Live-verified: switched to CARTO Light with real decodes on the map, confirmed layer order via `getStyle().layers` (`basemap-layer, station-arcs-layer, home-qth-layer, station-circles`), and visually confirmed both arcs render on top of the new basemap.

**Added (2026-07-13):** Maidenhead grid locator input for the "set your location" modal (HF Utility tab) — user asked "where do i put my location (IO87WC)" after the globe/arcs work made home-QTH accuracy more visible. The location modal previously only accepted a city-name search (geocoded via Nominatim) or raw `lat,lon`; it now also recognises a 4- or 6-character Maidenhead grid (e.g. `IO87` or `IO87wc`) typed directly, converted via the same `gridToLatLon()` the FT8 propagation map already uses to plot decoded stations' grid squares. That function was extended to optionally use 6-char subsquare precision when present (falls back to the existing 4-char-square-center behavior otherwise, so FT8's own always-4-char grid lookups are unaffected). Placeholder text and status hints updated to mention grid locators. Live-verified: typing "IO87WC" shows a single "IO87WC (grid locator)" result (57.10°, -2.13°), and pressing Enter updates `HF_LOC` and the HF Utility location display correctly.

**Added (2026-07-13):** Callsign field in the HF Utility location bar — user asked "WHERE DO I PUT IN MY CALLSIGN?"; there was no such field anywhere in NEXUS. Confirmed with the user this is specifically prep for the not-yet-built PSK Reporter spot-upload feature (see the follow-up noted above), so kept deliberately minimal: a new `MY_CALL` global (mirrors `HF_LOC`'s own localStorage-backed pattern, key `my_callsign`), a "📻 Your callsign" row next to "Your location" with its own small Change modal (reuses the location modal's CSS classes/overlay pattern rather than duplicating them, own IDs so the two modals don't collide), and a loose shape check (letters/digits/slash, 3–12 chars — not a real per-country ITU validator, just enough to reject empty/garbage input). Not wired into the map or sent anywhere yet — purely a settings field ready for the reporting feature once that's built. Live-verified: saving "g0abc" uppercases to G0ABC, persists to localStorage, and updates the display; invalid input ("@@") is rejected with the modal staying open and the previous value untouched.

**Added (2026-07-13):** Map style picker for the FT8/WSPR bridge panel's Leaflet map too (`ft8-map`/`ft8Map`) — user asked for this right after the FT8 INTERNAL map got its picker the day before ("add map picker to wstjx mode"). Same 5 no-API-key providers (CARTO Dark/Light/Voyager, OpenStreetMap, Esri Satellite), reimplemented against Leaflet's `L.tileLayer()` API in a new `FT8_BRIDGE_MAP_PROVIDERS` table — a separate table from the FT8 INTERNAL map's `MAP_PROVIDERS` rather than a shared one, since Leaflet wants a single `{s}/{r}` URL template + a `subdomains` option while MapLibre's raster sources want an array of already-expanded URLs; same 5 providers, different shape per library. `changeFt8BridgeMapProvider(key)` swaps the tile layer via `removeLayer()`/`addLayer()` and calls `bringToBack()` on the new layer — applying the exact z-order lesson from the same-day MapLibre arcs-hidden-under-basemap bug preemptively, so a freshly-added tile layer can never cover the home marker or station dots here either. Selection persists to `localStorage['nexus_ft8_bridge_map_provider']`, independent of the FT8 INTERNAL map's own saved provider (each panel remembers its own style choice). Not yet live-tested in a browser (Chrome extension was disconnected at the time of this change) — syntax-checked only; flagged for a live pass next session.

**Removed (2026-07-13):** The 🌐 Globe view (great-circle arcs from home QTH, added earlier the same day) — removed after user asked directly "does the globe really add anything useful?" and, on reflection together, the honest answer was: less than it looked. It's a real capability a flat 2D projection genuinely cannot show correctly (true bearing/long-path vs short-path — a straight line on a flat map lies about direction for anything far from the equator), but that's a narrower use case than the "band conditions at a glance" motivation that prompted it, the arcs always draw the geometrically shorter great-circle path with no way to know if a signal actually took the long path, and it's still one-to-many from a single station rather than the aggregated many-to-many view that actually shows band-opening activity — the flat map's per-band marker colouring already covers most of that ground with less interaction cost (no rotating a small embedded panel). Removed: the Globe button (HTML+CSS), `toggleStationMapGlobe()`/`applyStationMapGlobeMode()`/`greatCircleLine()`/`buildArcsGeoJSON()`/`buildHomeQthGeoJSON()`, the `station-arcs`/`home-qth` sources and layers, the arc/home-marker refresh hooks in `pushStationData()` and `hfApplyLocation()`, and the `stationMapGlobeMode` state + its localStorage key. Also reverted the MapLibre GL JS version bump (5.1.0 → back to 4.7.1) and simplified `changeStationMapProvider()`'s layer-insertion point back to its pre-Globe form, since both existed solely to support the feature that's now gone — no reason to carry the extra dependency version or z-order complexity for nothing. The map style picker and per-band station markers (not Globe-specific) are unaffected and stay. UserManual/Troubleshooting docs and the `w030_NEXUS.py` build-history docstring updated to match — documented as added-then-removed rather than silently erased, for the same reason the DDK9 preset mistake earlier this session was documented rather than quietly reverted.

**Added (2026-07-14):** Real screenshots embedded in QuickStart.docx and UserManual.docx, replacing the dashed-border placeholder boxes both docs had shipped with since their creation. User captured and saved 7 PNGs (`01a`/`01b_connection_wizard.png` — the Connection Setup modal's two source modes; `02_main_dashboard.png`; `03a`/`03b_decoders_dropdown.png` — the DECODERS dropdown's COMPACT vs Full IQ/External category views; `04_airband_tab.png`; `05_ft8_wspr_panel.png`) into a new `docs/_docx_build/images/` folder. Added `_pngSize()`/`image()` helpers to `helpers.js` (a raw PNG IHDR-chunk parser gets real width/height without a heavier image-decoding dependency, then scales to a max 620px width — the docx page's content width at 96 DPI — preserving aspect ratio; falls back to the existing `imagePlaceholder()` if a named file is missing, so a partial screenshot set never breaks the build). Every `H.imagePlaceholder(...)` call in `build_quickstart.js` (3) and `build_usermanual.js` (4) swapped for `H.image(...)` (spread, since it returns an array of 1-2 paragraph nodes rather than a single node). Also fixed a stale "3D globe view" mention in `build_quickstart.js`'s FT8-INTERNAL bullet, left over from before the Globe feature was removed above — that doc had not been rebuilt since the removal.

**Fixed (2026-07-14):** UserManual.docx audited against the actual current app (not just against its own prior version) after the user asked directly whether the manual covers everything — it didn't. Full pass comparing every tab/panel/button in `DARKSKY_NEXUS_w030.html` against the manual's table of contents turned up real gaps, not just wording drift:
- **RDS decode** (FM broadcast Program Service/Radiotext/Program Type, shown inline in the top bar in WFM and feeding the HF Utility "Broadcast Matches" column plus auto-bookmarking) had no documentation anywhere — added as new Section 3.1b.
- **Section 4 (HF Utility Tab)** described a stale 5-column layout from an earlier build. Rewritten to match the real current columns (Broadcast Matches, Live DX Spots, Beacons, Reference, Signal Intel), plus the Numbers Stations reference panel, the Live Decode mirror panel, and the location/callsign bar (including the callsign field and grid-locator input added earlier this week) — none of which were previously documented at all.
- **Three entire decoders had no section**: WEFAX, DAB/DAB+, and Trunked P25/DMR/NXDN (OP25/trunk-recorder) all exist as full tabs with their own quick-tune lists, setup instructions, and status displays, visible right there in the Decoders dropdown screenshot, but the manual's decoder list jumped straight from AIS to HFDL without mentioning any of them. Added as new Sections 6.16–6.18.
- **WSPR Beacons** turned out to be its own separate tab (its own Decoders-menu entry, band buttons 630m–10m, `wsprd` status bar, WSPRnet link, capture indicator) rather than a feature of the FT8/WSPR tab as the manual's four one-line WSPR bullets implied — expanded in place within Section 6.6 with a note clarifying it's a separate tab.
- **Waterfall colour palette** was only namechecked ("colour swatches — palette selector") with no list of what's actually available — added the real 8-palette list (Classic SDR, Heat, Viridis, Greyscale, Midnight Blue, Solar, Inferno, DARKSKY Neon) to Section 3.4.
- **Pro Mode** (an entire DSP-controls strip — noise reduction, squelch, AGC, low-cut filter, NFM de-emphasis, WFM stereo, audio limiter — plus a DSP Graph visual chain view) had no documentation despite being a full top-bar toggle — added as new Section 3.4a.
- **Band Plan strip** (the ITU region strip above the waterfall, with region-cycling) — added as new Section 3.4b.
- **Cinematic Mode** (full-screen ambient visualisation, 5 scenes, number-key scene switching) and the **theme toggle**/**Bookmark quick-button** were present as top-bar buttons but absent from Section 3.1's button list — added.
Nothing was removed or renumbered to make room — all additions use sub-letters (3.1b, 3.4a, 3.4b) or slot into the existing 6.x decoder numbering (6.16–6.18) so no existing cross-reference in the other two docs breaks. Rebuilt via `node build_usermanual.js`; verified via `unzip -l` that all 5 embedded images survived the rebuild.

**Added (2026-07-14):** Appendix C — Credits & Acknowledgments, in UserManual.docx — user asked for a compiled credits section naming SDRplay and Claude specifically. Previously the only credit anywhere was a one-line footer copyright ("© 2025 Jon Nicol & Claude / Anthropic"); there was no section crediting the actual third-party hardware, decoder binaries, libraries, or data sources NEXUS depends on or auto-launches. Compiled from every external tool/source actually referenced in `DARKSKY_NEXUS_w030.html` (cross-checked against the same audit pass used for the gaps above, not written from memory): Development (Jon Nicol, Claude/Anthropic); Hardware & Core Platform (SDRplay — RSPdx/nRSP-ST/SDRConnect, the primary supported platform; RTL-SDR); Decoder Engines & External Tools (WSJT-X, wsprd, ft8ts/Roger Need, fldigi/W1HKJ, dump1090-fa/readsb, dumpvdl2/szpajder, dumphfdl, DSD+/szechyjs, dab-cmdline/JvanKatwijk, OP25/boatbod, trunk-recorder/robotastic, codec2/freedv_rx, multimon-ng); Mapping & Visualization (MapLibre GL JS, Leaflet, CARTO/OpenStreetMap/Esri); Data Sources (NOAA SWPC, EIBI, AOKI, SigIDWiki, OurAirports, radio-browser.info, NCDXF, the DX cluster network). Each entry cross-references the manual section it powers. Added as new Appendix C, after the existing Appendix B, so no existing section numbering shifts. Rebuilt via `node build_usermanual.js`; verified all 5 embedded images survived.

**Fixed (2026-07-14):** FT8 INTERNAL's Band Hopping feature was completely non-functional — user reported "it doesn't work" right after the feature was explained. Root cause: the "Hop Off"/"Hop On" button on the main FT8 panel only calls `openHopModal()`, which opens the band-hopping config table (add/remove rows, set band/mode/cycles per row) — but the actual state toggle, `toggleHopping()`, was never wired to anything clickable anywhere in the UI. It's a complete, correct function (locks Start/Stop/mode/band while active, kicks off `advanceHop()`, etc.) and is referenced by `document.getElementById('hopStartBtn')` inside itself, but no element with that id existed anywhere — `_ensureHopModal()`'s modal template only had "+ Row", "Reset Stats", and "Close" buttons. Same story for three status readouts (`hopCurBand`, `hopCyclePos`, `hopNextHop`) that `renderHopModal()` already updates every render — the elements those ids point to were also never added to the modal template, so those updates silently no-op'd (each is guarded by `if (el)`). In short: the entire hop-scheduling engine was fully wired and working, just missing its own "on" switch and status display in the modal HTML. Fixed by adding a status/control row to `_ensureHopModal()`'s template (between the "Band Hopping" heading and the row table): **Current** / **Cycle** / **Next** readouts plus a **Start** button (`id="hopStartBtn"`, `onclick="toggleHopping()"`) that `toggleHopping()`'s existing logic already knows how to relabel to "Stop" (red) when active. No JS logic changed — this was purely a missing piece of HTML that the working JS had been reaching for all along. Verified via `node --check` on the extracted inline scripts; not yet live-tested in a browser this session — flagged for a live click-through next time NEXUS is running. Also added a "Band Hopping (FT8 INTERNAL)" subsection to UserManual.docx (Section 6.6) documenting the feature for the first time — it existed in code but was never in the manual either, alongside the same modal-vs-JS gap above. Rebuilt via `node build_usermanual.js`; verified all 5 embedded images survived.

**Fixed (2026-07-14):** Band plan strip, waterfall, and spectrum all went stale/blank together after changing bands — user-reported ("something strange happening with bandplan, waterfall and spectrum" when changing bands), live-diagnosed in Chrome. Root cause: `_zoomFreqRange()` (the single function every one of these — band plan strip, spectrum trace, waterfall, frequency axis — calls to work out what frequency span is currently visible) prefers `DS.zoomCenter` over `DS.liveCenter` whenever `zoomCenter` is set. `zoomCenter` gets set by the **CTR** button (or by zooming in past 1×) as a deliberate, documented "recenter the display on my signal" convenience — but nothing ever cleared it again on a genuine band change. Reproduced live: clicked **CTR** at 25.200 MHz (sets `zoomCenter = 25.2e6`), then changed band to 6m via the Bands panel — the VFO correctly retuned to 50.150 MHz (confirmed in the digit readout and status bar), but the band plan strip, frequency axis, spectrum trace, and waterfall all stayed frozen on the old ~25 MHz span, since `_zoomFreqRange()` kept returning a range centered on the stale `zoomCenter` instead of the new `liveCenter`. Fixed in `_tuneTo()`: added `DS.zoomCenter = null;` alongside the existing `DS.liveCenter = hz;` inside the `if (!inSpan)` block — this block already runs for exactly the right cases (every genuine LO-moving retune: band-plan strip clicks, the Bands panel, every quick-tune chip across the app, since they all call `_tuneTo(freq, mode, bw, true)`), so a deliberate band change now always drops back to centering the display on the real new frequency, while **CTR** remains available afterward to recenter on whatever's now being looked at. Live-verified after the fix: repeated the exact CTR→band-change repro at 500 kSPS (14 MHz→50.15 MHz) and again at 2 MSPS (14.2 MHz→156.8 MHz, VHF Marine) — band plan label, frequency axis, and spectrum trace all updated correctly and immediately in both cases, zero console errors either time.

**Added (2026-07-14):** Automated DMG creation in `build/build_macOS.sh` — user asked how to turn the built `.app` into a DMG, then asked to have it automated. Noticed while looking into this that the current `build/dist/` output on this machine was a bare PyInstaller onedir folder (executable + `_internal/`), not the `.app` bundle the `.spec`'s `BUNDLE()` stage is supposed to produce — flagged to the user as worth re-running the build to confirm before relying on this, since a DMG step can't do anything with a missing `.app`. New Step 7/7 added after the existing post-processing step: builds `dist/DARKSKY_NEXUS_w030_macOS.dmg` from the `.app` automatically. Prefers `create-dmg` (Homebrew) for a real "drag to Applications" layout (app icon + Applications shortcut, positioned window) if installed; falls back to a plain `hdiutil create -format UDZO` DMG otherwise, so the script still completes on a machine without `create-dmg`. `create-dmg` is invoked with `|| true` since it's known to sometimes exit non-zero on harmless Finder/AppleScript timing warnings even when the DMG was produced correctly — the script checks for the actual output file afterward rather than trusting the exit code, and only falls back to `hdiutil` if the DMG genuinely wasn't created. Step numbering in the script's echo output updated from `[n/6]` to `[n/7]` throughout; final summary now reports the DMG path/size alongside the `.app`, and the old "here's the command to run yourself" echo block was replaced with real notarization instructions (unchanged from before, just no longer needed for the DMG step itself). `BUILD_NOTES.md` updated to match: manual `hdiutil`/`create-dmg` commands moved under a new "only needed if not using build_macOS.sh" heading rather than presented as the primary path. Verified via `bash -n` that the updated script is syntactically valid; not yet run end-to-end on an actual Mac (this session has no macOS/PyInstaller environment to test against) — flagged for a live run next time the app is actually built.

**Fixed (2026-08-03):** DAB regression live-diagnosed end to end after a "no ensemble locked" report with a confirmed strong 12B signal. Two independent, unrelated causes stacked on top of each other: (1) `sudo cp`-ing the freshly rebuilt `dab_radio_nexus`/`libfftw3f.3.dylib` into `/usr/local/bin/` left the dylib at mode `700` (root-only) — `dab_radio_nexus` runs as the regular user, so dyld failed with `errno=13` (EACCES) on every launch, producing a tight crash-relaunch loop that looked like "no signal" from the UI. Fixed with `chmod 755`. (2) Even after that, SDRConnect never emitted a single type-2 (raw IQ) WebSocket frame despite `can_control`/`started` both reporting healthy and every `*_stream_enable` property write acking successfully — traced by adding up frame-type tallies already logged every 100 frames (`SDRConnect frame types: {3: N, 1: N}`, never a `2:` key) across a long elimination pass (SDRConnect config reset, `sdrplay_apiService` LaunchDaemon restart, RSPdx-via-USB vs nRSP-ST-via-WiFi) that ruled out corrupted config, a stuck daemon, and network bandwidth in turn. Actual root cause: the nRSP-ST's firmware had just been reflashed (deliberately, via SDRplay's own nRSP Updater) and left the SDRplay API service's raw-IQ streaming path stale against the new firmware, even though the lightweight property-control channel kept working throughout — hence audio/spectrum/control all looking perfectly healthy while raw IQ silently never flowed. Resolved by a plain SDRConnect + API-service restart after the firmware update settled. No code changes were needed for either cause — both were environment/permissions state on Jon's Mac, not application bugs — but see the startup-latency fix immediately below, prompted by the same live session.

**Fixed (2026-08-03):** Local SDRConnect auto-launch (`local_launch_mode` != `'none'`) used to fire `sdr_bridge()`'s very first `websockets.connect()` attempt immediately after spawning the SDRConnect process — guaranteed to fail with `ConnectionRefusedError` (full traceback logged) on every single such startup, since SDRConnect's WebSocket API takes several seconds to initialise after launch. User feedback, prompted by today's long DAB live-debugging session where this fired on every restart: startup "feels clunky" compared to w034 (which had no auto-launch at all — the user started SDRConnect themselves first, so this race never existed). Comparing w034's and w035's frontend directly confirmed the actual startup *picker* (connection mode + headless/GUI choice) isn't the culprit — it only ever shows once and is remembered thereafter (`_handleConnectionModeState()`'s `_connModeResolved` guard) — the guaranteed-fail race was the real, reproducible source of startup noise. Added `_wait_for_sdrconnect_port()`: polls a raw `asyncio.open_connection()` against the target host/port (0.3s between attempts, 20s timeout) right after `_local_launch_sdrconnect()` returns a process, before entering the existing connect-retry loop. Falls through to the unchanged retry loop unchanged on timeout — pure latency/log-noise optimisation, not a new failure mode or a required gate. Only applies to the local-launch path; `local_launch_mode='none'` (start SDRConnect yourself, then run NEXUS) and the SSH/remote launcher are untouched. Verified via `python3 -m py_compile`; not yet live-restart-tested this session (verify next NEXUS restart that the `Connect call failed` traceback no longer appears on a local-launch startup).
