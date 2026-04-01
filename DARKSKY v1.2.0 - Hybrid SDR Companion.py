#!/usr/bin/env python3
"""
DARKSKY v1.2.0 - Hybrid SDR Companion
SDRConnect Bridge + Direct RTL-SDR Driver

Copyright (c) 2025 Jon Nicol & Claude / Anthropic
"""

import sys
import asyncio
import json
import logging
import os
import collections
import math
import struct
import subprocess
import threading
import time
import urllib.request
import urllib.error
import hashlib
import base64
import socket
import platform
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# --- DEFAULT ENGINE ---
SDR_ENGINE = "SDRCONNECT" # "SDRCONNECT" or "RTLSDR"

# --- PLATFORM ---
PLATFORM = platform.system()  # 'Darwin', 'Windows', 'Linux'
IS_MAC     = PLATFORM == 'Darwin'
IS_WIN     = PLATFORM == 'Windows'
IS_LINUX   = PLATFORM == 'Linux'

def _launch_browser(url):
    """Launch Chrome/Chromium cross-platform, fall back to system default browser."""
    # Candidate paths by platform
    candidates = []
    if IS_MAC:
        candidates = [
            ['open', '-a', 'Google Chrome', url],
            ['open', '-a', 'Chromium', url],
            ['open', '-a', 'Microsoft Edge', url],
        ]
    elif IS_WIN:
        candidates = [
            [r'C:\Program Files\Google\Chrome\Application\chrome.exe', url],
            [r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe', url],
            [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', url],
            ['chrome', url],
            ['msedge', url],
        ]
    elif IS_LINUX:
        candidates = [
            ['google-chrome', url],
            ['google-chrome-stable', url],
            ['chromium', url],
            ['chromium-browser', url],
            ['microsoft-edge', url],
        ]

    # Try each candidate
    for cmd in candidates:
        try:
            # On Windows/Linux, check if executable exists first
            if not IS_MAC:
                import shutil
                exe = cmd[0]
                if not (os.path.isfile(exe) or shutil.which(exe)):
                    continue
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.info(f"Browser: launched with {cmd[0]}")
            return
        except Exception:
            continue

    # Fall back to system default browser
    log.warning("Browser: Chrome/Edge not found — opening system default browser")
    webbrowser.open(url)

try:
    import websockets
    from websockets.exceptions import ConnectionClosed
except ImportError:
    print("ERROR: websockets not found. Run: pip install websockets")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("WARNING: numpy not found. Decoders and RTL-Spectrum will be disabled.")
    np = None

try:
    from rtlsdr import RtlSdr
except ImportError:
    RtlSdr = None

# ── Configuration ─────────────────────────────────────────────────────────────
SDRCONNECT_WS   = "ws://127.0.0.1:5454"
DARKSKY_PORT    = 8888          # DARKSKY web UI port — change if 8888 is in use
BRIDGE_WS_PORT  = 8889          # Internal WebSocket bridge port
VERSION         = "v1.2.0"
DARKSKY_HTML    = Path(__file__).parent / "DARKSKY.html"

# ── Paths — auto-detected, override here if needed ────────────────────────
SCRIPT_DIR      = Path(__file__).parent
WORKING_DIR     = str(SCRIPT_DIR)   # DAB bridge lives alongside the server
BRIDGE_PATH     = str(SCRIPT_DIR / ("darksky_dab_bridge.exe" if IS_WIN else "darksky_dab_bridge"))
DAB_BIN         = os.path.expanduser("~/dab-cmdline/example-2/build/dab-rtl_tcp-2")
# Audio output device name (platform-specific)
DAB_AUDIO_OUT   = "Speakers" if IS_WIN else ("pulse" if IS_LINUX else "MacBook Pro Speakers")

DAB_CHANNELS = {
    "11A":216.928,"11B":218.640,"11C":220.352,"11D":222.064,
    "12A":223.936,"12B":225.648,"12C":227.360,"12D":229.072
}

# ── dump1090 ADS-B integration ─────────────────────────────────────────────
# dump1090 exposes aircraft JSON at http://localhost:8080/data/aircraft.json
# Set DUMP1090_HOST to None to disable
DUMP1090_HOST   = "127.0.0.1"
DUMP1090_PORT   = 8080          # dump1090/dump1090-fa default JSON port
DUMP1090_POLL_S = 2.0   # poll interval in seconds

# ── WSJT-X FT8/WSPR integration ───────────────────────────────────────────
# WSJT-X broadcasts decoded messages via UDP multicast
# Standard port is 2237 — must match WSJT-X Settings > Reporting > UDP port
WSJTX_UDP_HOST  = "127.0.0.1"
WSJTX_UDP_PORT  = 2237

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("DARKSKY")

# ── Shared state ──────────────────────────────────────────────────────────────
state = {
    "connected": False, "vfo_hz": 0, "center_hz": 0, "mode": "USB",
    "bandwidth_hz": 3000, "signal_power": -50.0, "signal_snr": 0.0,
    "sample_rate": 2048000, "iq_streaming": False, "overload": False, "engine": SDR_ENGINE,
    "version": VERSION
}

_span_changing = False          # suppresses VFO/centre echo during sample rate changes
_span_change_handle = None      # asyncio handle to clear the flag

browser_clients = set()
sdr_send_queue = None
rtlsdr_obj = None
main_loop = None

# Integration state — only active when user enables them
_dump1090_task   = None
_wsjtx_task      = None
_wsjtx_transport = None

# ── RTL-SDR Direct Engine ─────────────────────────────────────────────────────
def run_rtlsdr_engine():
    global rtlsdr_obj, state
    if not RtlSdr:
        log.error("Engine: pyrtlsdr not installed. Cannot start RTL Engine.")
        return

    try:
        log.info("Engine Switch: Initializing RTL-SDR USB...")
        rtlsdr_obj = RtlSdr()
        rtlsdr_obj.sample_rate = 2048000
        rtlsdr_obj.center_freq = state["vfo_hz"]
        rtlsdr_obj.gain = 'auto'
        state["connected"] = True
        state["sample_rate"] = 2048000
        
        log.info(f"Engine: RTL-SDR Online @ {rtlsdr_obj.center_freq/1e6} MHz")
        asyncio.run_coroutine_threadsafe(broadcast_state(), main_loop)

        while state["engine"] == "RTLSDR" and state["connected"]:
            # 1. Read Raw IQ
            samples = rtlsdr_obj.read_samples(16384)
            
            # 2. Generate Spectrum for Waterfall (Python-Side FFT)
            if np:
                window = np.hanning(len(samples[:1024]))
                psd = np.abs(np.fft.fftshift(np.fft.fft(samples[:1024] * window)))**2
                psd_db = 10 * np.log10(psd + 1e-12)
                norm = np.clip((psd_db + 65) * (255/60), 0, 255).astype(np.uint8)
                asyncio.run_coroutine_threadsafe(
                    broadcast_raw(json.dumps({"type": "spectrum", "bins": norm.tolist()})),
                    main_loop
                )

            # 3. Feed DAB Bridge if running
            if dab_bridge.running:
                iq_u8 = np.empty(len(samples)*2, dtype=np.uint8)
                iq_u8[0::2] = np.clip((samples.real * 127 + 128), 0, 255).astype(np.uint8)
                iq_u8[1::2] = np.clip((samples.imag * 127 + 128), 0, 255).astype(np.uint8)
                try: dab_bridge.bridge_proc.stdin.write(iq_u8.tobytes())
                except: pass

            time.sleep(0.01) # Control CPU usage
            
        rtlsdr_obj.close()
        log.info("Engine: RTL-SDR Hardware Released.")
    except Exception as e:
        log.error(f"RTL-SDR Engine Error: {e}")
        state["connected"] = False
        asyncio.run_coroutine_threadsafe(broadcast_state(), main_loop)

# ── SDRConnect Engine ─────────────────────────────────────────────────────────
async def sdr_connect():
    global sdr_send_queue
    sdr_send_queue = asyncio.Queue()
    while True:
        if state["engine"] == "SDRCONNECT":
            try:
                async with websockets.connect(SDRCONNECT_WS, ping_interval=10) as ws:
                    state["connected"] = True
                    log.info("Engine: SDRConnect Link Active")
                    await broadcast_state()
                    await ws.send(json.dumps({"event_type": "spectrum_enable", "value": "true"}))
                    await ws.send(json.dumps({"event_type": "iq_stream_enable", "value": "true"}))
                    # Pull current SDRConnect state immediately on connect
                    for prop in ["device_vfo_frequency", "device_center_frequency", "device_sample_rate", "demodulator", "filter_bandwidth", "device_output_type", "overload"]:
                        await ws.send(json.dumps({"event_type": "get_property", "property": prop}))
                    
                    async def receiver():
                        async for msg in ws:
                            if state["engine"] != "SDRCONNECT": break
                            if isinstance(msg, bytes):
                                payload = msg[4:]
                                msg_type = struct.unpack_from("<H", msg, 0)[0]
                                if msg_type == 3: await broadcast_raw(json.dumps({"type": "spectrum", "bins": list(payload)}))
                                elif msg_type == 2:
                                    if not state["iq_streaming"]:
                                        state["iq_streaming"] = True
                                        await broadcast_state()
                                    if dab_bridge.running: dab_bridge.feed_iq(payload)
                            else:
                                d = json.loads(msg)
                                p, v = d.get("property"), d.get("value")
                                if p in ("device_vfo_frequency", "vfo_frequency"):
                                    if not _span_changing:
                                        state["vfo_hz"] = int(float(v))
                                        state["center_hz"] = int(float(v))
                                elif p == "device_center_frequency":
                                    if not _span_changing:
                                        state["center_hz"] = int(float(v))
                                elif p == "device_sample_rate":
                                    state["sample_rate"] = int(float(v))
                                elif p in ("demodulator", "device_mode"):
                                    state["mode"] = str(v).upper()
                                elif p == "device_output_type":
                                    # SDRConnect: "iq" = Full IQ, "if" or "baseband" = Compact
                                    state["iq_streaming"] = (str(v).lower() == "iq")
                                elif p in ("filter_bandwidth", "device_filter_bandwidth"):
                                    state["bandwidth_hz"] = int(float(v))
                                elif p in ("device_overload", "overload", "adc_overload", "rf_overload"):
                                    overloaded = str(v).lower() in ("true", "1", "yes")
                                    state["overload"] = overloaded
                                    # Send overload event immediately so UI reacts fast
                                    await broadcast_raw(json.dumps({"type": "overload", "active": overloaded}))
                                await broadcast_state()
                    async def sender():
                        while state["engine"] == "SDRCONNECT":
                            await ws.send(await sdr_send_queue.get())
                    
                    await asyncio.gather(receiver(), sender())
            except:
                state["connected"] = False; await broadcast_state(); await asyncio.sleep(5)
        else:
            await asyncio.sleep(1)

# ── DAB Bridge ────────────────────────────────────────────────────────────────
class DabBridge:
    def __init__(self):
        self.bridge_proc = None; self.dab_proc = None; self.running = False

    async def start(self, channel: str):
        if self.running: await self.stop()
        freq_mhz = DAB_CHANNELS.get(channel.upper(), 225.648)
        
        if state["engine"] == "RTLSDR" and rtlsdr_obj:
            rtlsdr_obj.center_freq = int(freq_mhz * 1e6)
            state["vfo_hz"] = rtlsdr_obj.center_freq
        else:
            await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"device_sample_rate","value":"2048000.0"}))
            await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"device_vfo_frequency","value":str(int(freq_mhz * 1e6))}))

        try:
            self.bridge_proc = subprocess.Popen([BRIDGE_PATH, "1234"], stdin=subprocess.PIPE, bufsize=0)
            await asyncio.sleep(0.6)
            self.dab_proc = subprocess.Popen([DAB_BIN, "-C", channel, "-G", "80", "-A", DAB_AUDIO_OUT], stderr=subprocess.DEVNULL)
            self.running = True
            log.info(f"DAB: Decoding {channel} ({freq_mhz} MHz)")
            await broadcast_raw(json.dumps({"type": "dab_started", "channel": channel, "freq_mhz": freq_mhz}))
        except Exception as e: log.error(f"DAB Error: {e}")

    async def stop(self):
        self.running = False
        if self.dab_proc: self.dab_proc.terminate()
        if self.bridge_proc: self.bridge_proc.terminate()
        log.info("DAB: Stopped")
        await broadcast_raw(json.dumps({"type": "dab_stopped"}))

    def feed_iq(self, raw_bytes: bytes):
        if not self.running or not self.bridge_proc or np is None: return
        try:
            data_s16 = np.frombuffer(raw_bytes, dtype='<i2')
            data_u8 = (data_s16 // 256 + 128).astype(np.uint8)
            self.bridge_proc.stdin.write(data_u8.tobytes())
        except: self.running = False

# ── Core Communication ────────────────────────────────────────────────────────
async def broadcast_state():
    await broadcast_raw(json.dumps({"type": "state", **state}))

async def start_dump1090():
    global _dump1090_task
    if _dump1090_task and not _dump1090_task.done():
        return  # already running
    if not DUMP1090_HOST:
        await broadcast_raw(json.dumps({"type": "adsb_error", "msg": "dump1090 disabled in config"}))
        return
    log.info(f"ADS-B: starting dump1090 poller")
    _dump1090_task = asyncio.create_task(dump1090_poller())

async def stop_dump1090():
    global _dump1090_task
    if _dump1090_task and not _dump1090_task.done():
        _dump1090_task.cancel()
        _dump1090_task = None
    log.info("ADS-B: dump1090 poller stopped")

async def start_wsjtx():
    global _wsjtx_task, _wsjtx_transport
    if _wsjtx_task and not _wsjtx_task.done():
        return  # already running
    log.info(f"FT8: starting WSJT-X listener on UDP {WSJTX_UDP_PORT}")
    _wsjtx_task = asyncio.create_task(wsjtx_listener())

async def stop_wsjtx():
    global _wsjtx_task, _wsjtx_transport
    if _wsjtx_transport:
        _wsjtx_transport.close()
        _wsjtx_transport = None
    if _wsjtx_task and not _wsjtx_task.done():
        _wsjtx_task.cancel()
        _wsjtx_task = None
    log.info("FT8: WSJT-X listener stopped")

async def broadcast_raw(msg: str):
    for client in list(browser_clients):
        try: await client.send(msg)
        except: browser_clients.discard(client)

async def switch_engine(new_engine):
    global rtlsdr_obj, state
    if new_engine == state["engine"]: return
    log.info(f"Engine Switch: {state['engine']} -> {new_engine}")
    
    # 1. Shutdown Current
    state["connected"] = False
    if rtlsdr_obj: 
        await asyncio.sleep(0.5) # Let thread exit
    
    # 2. Assign New
    state["engine"] = new_engine
    if new_engine == "RTLSDR":
        threading.Thread(target=run_rtlsdr_engine, daemon=True).start()
    else:
        log.info("Engine: Waiting for SDRConnect Network Link...")
    
    await broadcast_state()

async def browser_handler(websocket):
    browser_clients.add(websocket)
    try:
        await broadcast_state()
        async for msg in websocket:
            data = json.loads(msg)
            cmd = data.get("cmd")
            if cmd == "set_engine":
                await switch_engine(data["engine"])
            elif cmd == "tune":
                f_vfo = int(float(data["freq_mhz"]) * 1e6)
                f_lo  = int(float(data["center_mhz"]) * 1e6) if "center_mhz" in data else None
                mode  = data.get("mode", state.get("mode", "USB"))
                bw_hz = int(data.get("bw_hz", 3000))
                state["vfo_hz"]      = f_vfo
                state["mode"]        = mode
                state["bandwidth_hz"]= bw_hz
                if f_lo is not None:
                    state["center_hz"] = f_lo
                if state["engine"] == "RTLSDR" and rtlsdr_obj:
                    rtlsdr_obj.center_freq = f_lo if f_lo is not None else f_vfo
                    await broadcast_state()
                else:
                    if f_lo is not None:
                        await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"device_center_frequency","value":str(f_lo)}))
                    await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"device_vfo_frequency","value":str(f_vfo)}))
                    await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"demodulator","value":mode}))
                    await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"filter_bandwidth","value":str(float(bw_hz))}))
                    await broadcast_state()
            elif cmd == "adsb_start":
                await start_dump1090()
                await broadcast_raw(json.dumps({"type": "adsb_status", "active": True}))
            elif cmd == "adsb_stop":
                await stop_dump1090()
                await broadcast_raw(json.dumps({"type": "adsb_status", "active": False}))
            elif cmd == "ft8_enable":
                active = data.get("active", True)
                if active:
                    await start_wsjtx()
                    await broadcast_raw(json.dumps({"type": "ft8_status", "active": True}))
                else:
                    await stop_wsjtx()
                    await broadcast_raw(json.dumps({"type": "ft8_status", "active": False}))
            elif cmd == "dab_start": await dab_bridge.start(data["channel"])
            elif cmd == "dab_stop": await dab_bridge.stop()
            elif cmd == "get_state": await broadcast_state()
            elif cmd == "set_gain":
                lna = int(data.get("lna", 0))
                state["lna_state"] = lna
                await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"device_lna_state","value":str(lna)}))
                await broadcast_state()
            elif cmd == "set_bw":
                bw = int(data["bw_hz"])
                state["bandwidth_hz"] = bw
                await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"filter_bandwidth","value":str(bw)}))
                await broadcast_state()
            elif cmd == "set_sample_rate":
                global _span_changing, _span_change_handle
                hz = int(data["rate_hz"])
                state["sample_rate"] = hz
                # Suppress VFO/centre echo from SDRConnect for 1 second
                _span_changing = True
                if _span_change_handle:
                    _span_change_handle.cancel()
                loop = asyncio.get_event_loop()
                def _clear_span():
                    global _span_changing
                    _span_changing = False
                _span_change_handle = loop.call_later(1.0, _clear_span)
                await sdr_send_queue.put(json.dumps({"event_type":"set_property","property":"device_sample_rate","value":str(float(hz))}))
                await broadcast_state()
    except: pass
    finally: browser_clients.discard(websocket)

# ── HTTP Server (Direct WebSocket Patch) ─────────────────────────────────────
class DarkskyHTTP(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            try:
                content = DARKSKY_HTML.read_text(encoding="utf-8")
                # Patch Version and Port into HTML before serving
                content = content.replace("v1.2.0", state["version"])
                patched = content.replace(
                    "const BRIDGE_WS = 'ws://' + location.host;", 
                    f"const BRIDGE_WS = 'ws://' + location.hostname + ':{BRIDGE_WS_PORT}';"
                )
                self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers()
                self.wfile.write(patched.encode("utf-8"))
            except: self.send_error(404)
        else: self.send_error(404)

# ── Main Startup ──────────────────────────────────────────────────────────────
dab_bridge = DabBridge()

# ── dump1090 ADS-B poller ─────────────────────────────────────────────────
async def dump1090_poller():
    """Poll dump1090's aircraft.json and forward to browser clients."""
    url = f"http://{DUMP1090_HOST}:{DUMP1090_PORT}/data/aircraft.json"
    log.info(f"dump1090: starting poller → {url}")
    consecutive_fails = 0

    while True:
        await asyncio.sleep(DUMP1090_POLL_S)
        try:
            loop = asyncio.get_event_loop()
            def fetch():
                req = urllib.request.Request(url, headers={"User-Agent": "DARKSKY"})
                with urllib.request.urlopen(req, timeout=2) as r:
                    return json.loads(r.read())
            data = await loop.run_in_executor(None, fetch)
            aircraft = data.get("aircraft", [])
            # Normalise to DARKSKY adsb_state format
            planes = []
            for a in aircraft:
                if not a.get("lat"): continue
                planes.append({
                    "icao":     a.get("hex","").upper(),
                    "callsign": (a.get("flight","") or "").strip(),
                    "lat":      a.get("lat"),
                    "lon":      a.get("lon"),
                    "alt":      a.get("altitude") or a.get("alt_baro"),
                    "speed":    a.get("speed") or a.get("gs"),
                    "track":    a.get("track"),
                    "squawk":   a.get("squawk"),
                    "rssi":     a.get("rssi"),
                })
            await broadcast_raw(json.dumps({
                "type":     "adsb_state",
                "aircraft": planes,
                "source":   "dump1090",
                "count":    len(planes)
            }))
            consecutive_fails = 0
        except urllib.error.URLError:
            consecutive_fails += 1
            if consecutive_fails == 1:
                log.warning("dump1090: not reachable — is dump1090 running?")
            await asyncio.sleep(min(30, DUMP1090_POLL_S * consecutive_fails))
        except Exception as e:
            log.debug(f"dump1090: {e}")

# ── WSJT-X UDP listener ───────────────────────────────────────────────────
async def wsjtx_listener():
    """Listen for WSJT-X UDP datagrams and forward decoded FT8/WSPR to browser."""
    import struct as _struct

    # WSJT-X protocol magic number and schema version
    WSJTX_MAGIC   = 0xADBCCBDA
    MSG_DECODE     = 2   # Decode message type

    log.info(f"WSJT-X: listening on UDP {WSJTX_UDP_HOST}:{WSJTX_UDP_PORT}")

    loop = asyncio.get_event_loop()

    class WSJTXProtocol(asyncio.DatagramProtocol):
        def datagram_received(self, data, addr):
            try:
                if len(data) < 8: return
                magic, schema = _struct.unpack_from(">II", data, 0)
                if magic != WSJTX_MAGIC: return
                msg_type = _struct.unpack_from(">I", data, 8)[0]

                if msg_type == MSG_DECODE:
                    # Parse Decode message (type 2)
                    # Fields: magic(4) schema(4) type(4) id(str) new(1)
                    #         time(4) snr(4) dt(8) df(4) mode(str) msg(str) lowconf(1) offair(1)
                    off = 12
                    # Skip id string (pascal: 4-byte len + data)
                    id_len = _struct.unpack_from(">I", data, off)[0]
                    off += 4 + (id_len if id_len != 0xFFFFFFFF else 0)
                    is_new = data[off]; off += 1
                    if not is_new: return
                    time_ms = _struct.unpack_from(">I", data, off)[0]; off += 4
                    snr     = _struct.unpack_from(">i", data, off)[0]; off += 4
                    dt      = _struct.unpack_from(">d", data, off)[0]; off += 8
                    df      = _struct.unpack_from(">I", data, off)[0]; off += 4
                    mode_len = _struct.unpack_from(">I", data, off)[0]; off += 4
                    mode = data[off:off+mode_len].decode("utf-8","replace") if mode_len != 0xFFFFFFFF else ""; off += mode_len if mode_len != 0xFFFFFFFF else 0
                    msg_len  = _struct.unpack_from(">I", data, off)[0]; off += 4
                    message  = data[off:off+msg_len].decode("utf-8","replace") if msg_len != 0xFFFFFFFF else ""

                    asyncio.ensure_future(broadcast_raw(json.dumps({
                        "type":    "ft8_results",
                        "source":  "wsjtx",
                        "mode":    mode,
                        "results": [{
                            "snr":    snr,
                            "dt":     dt,
                            "df":     df,
                            "msg":    message,
                            "crc_ok": True
                        }],
                        "t0": time_ms / 1000
                    })))
            except Exception as e:
                log.debug(f"WSJT-X parse: {e}")

        def error_received(self, exc):
            log.debug(f"WSJT-X UDP error: {exc}")

        def connection_lost(self, exc):
            pass

    try:
        global _wsjtx_transport
        transport, protocol = await loop.create_datagram_endpoint(
            WSJTXProtocol,
            local_addr=(WSJTX_UDP_HOST, WSJTX_UDP_PORT)
        )
        _wsjtx_transport = transport
        log.info(f"WSJT-X: UDP listener active on port {WSJTX_UDP_PORT}")
        await broadcast_raw(json.dumps({"type": "ft8_status", "active": True, "source": "wsjtx"}))
        # Keep running until cancelled
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            transport.close()
    except OSError as e:
        log.warning(f"WSJT-X: could not bind UDP port {WSJTX_UDP_PORT} — {e}")
        log.warning("WSJT-X: check WSJT-X Settings > Reporting > UDP port matches")

async def main():
    global main_loop
    main_loop = asyncio.get_event_loop()
    
    # Start UI Server
    threading.Thread(target=lambda: ThreadingHTTPServer(("127.0.0.1", DARKSKY_PORT), DarkskyHTTP).serve_forever(), daemon=True).start()
    
    # Start WebSocket Bridge
    server = await websockets.serve(browser_handler, "127.0.0.1", BRIDGE_WS_PORT)
    
    # Start Hardware Engine
    if state["engine"] == "RTLSDR":
        threading.Thread(target=run_rtlsdr_engine, daemon=True).start()
    else:
        asyncio.create_task(sdr_connect())

    # dump1090 and WSJT-X are started on-demand when user enables them in the UI
    # (see adsb_start and ft8_enable command handlers in browser_handler)

    log.info("=" * 45)
    log.info(f" DARKSKY {VERSION} READY ")
    log.info(f" Platform:      {PLATFORM}")
    log.info(f" Active Engine: {state['engine']}")
    log.info(f" ADS-B:         dump1090 on-demand @ {DUMP1090_HOST}:{DUMP1090_PORT}")
    log.info(f" FT8/WSPR:      WSJT-X on-demand UDP port {WSJTX_UDP_PORT}")
    log.info("=" * 45)
    
    _launch_browser(f"http://127.0.0.1:{DARKSKY_PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: pass
