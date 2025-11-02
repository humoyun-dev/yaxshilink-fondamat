from __future__ import annotations

import json
import os
import platform
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict

from . import state
from .config import load_existing_config
import os as _os

try:
    import psutil as _psutil  # type: ignore
except Exception:  # pragma: no cover
    _psutil = None  # type: ignore

try:
    import GPUtil as _gputil  # type: ignore
except Exception:  # pragma: no cover
    _gputil = None  # type: ignore


def snapshot() -> Dict[str, Any]:
    cfg = load_existing_config()
    with state.state_lock:
        sess = {
            "active": state.session_active,
            "session_id": state.current_session_id,
            "bottle_counter": state.bottle_counter,
        }
        devices = {
            "scanner": {
                "connected": state.scanner_connected,
                "last_line": state.last_scanner_line,
                "port": cfg.get("SCANNER_PORT"),
                "baud": cfg.get("BAUDRATE_SCANNER"),
            },
            "arduino": {
                "connected": state.arduino_connected,
                "last_line": state.last_arduino_line,
                "port": cfg.get("ARDUINO_PORT"),
                "baud": cfg.get("BAUDRATE_ARDUINO"),
            },
        }
        ws = {
            "connected": state.ws_connected,
            "url": cfg.get("WS_URL"),
            "last_event": state.last_ws_event,
            "last_server_msg_at": state.last_server_msg_ts,
        }
        queues = {
            "outbox_size": getattr(state.outbox, "qsize", lambda: -1)(),
            "arduino_cmd_queue_size": getattr(state.arduino_cmd_queue, "qsize", lambda: -1)(),
        }

    now = time.time()
    # System metrics (best-effort)
    cpu = {}
    mem = {}
    temps = {}
    gpus = []

    if _psutil:
        try:
            cpu = {
                "physical_cores": _psutil.cpu_count(logical=False),
                "logical_cores": _psutil.cpu_count(logical=True),
                "percent_total": _psutil.cpu_percent(interval=None),
                "percent_per_cpu": _psutil.cpu_percent(interval=None, percpu=True),
            }
            try:
                freq = _psutil.cpu_freq()
                if freq:
                    cpu["freq_mhz_current"] = freq.current
                    cpu["freq_mhz_min"] = freq.min
                    cpu["freq_mhz_max"] = freq.max
            except Exception:
                pass
        except Exception:
            pass
        try:
            vm = _psutil.virtual_memory()
            mem = {
                "total": vm.total,
                "available": vm.available,
                "used": vm.used,
                "percent": vm.percent,
            }
        except Exception:
            pass
        try:
            t = _psutil.sensors_temperatures()
            # Flatten: take a few common keys
            temps = {k: [
                {"label": it.label or str(idx), "current": it.current, "high": it.high, "critical": it.critical}
                for idx, it in enumerate(v)
            ] for k, v in (t or {}).items()}
        except Exception:
            temps = {}

    if _gputil:
        try:
            for g in _gputil.getGPUs():
                gpus.append({
                    "id": g.id,
                    "name": g.name,
                    "load": g.load,  # 0..1
                    "memory_total": g.memoryTotal,
                    "memory_used": g.memoryUsed,
                    "temperature": g.temperature,
                    "uuid": getattr(g, 'uuid', None),
                })
        except Exception:
            gpus = []

    # Platform-specific fallbacks
    _system = platform.system()

    # macOS CPU temperature via osx-cpu-temp if psutil didn't provide temps
    if _system == "Darwin" and not temps:
        for pth in ("/opt/homebrew/bin/osx-cpu-temp", "/usr/local/bin/osx-cpu-temp"):
            try:
                import subprocess as _sp
                res = _sp.run([pth], capture_output=True, text=True, timeout=0.5)
                if res.returncode == 0 and res.stdout:
                    out = res.stdout.strip()
                    # e.g., "55.0°C" or "55.0 C"
                    val = "".join(ch for ch in out if (ch.isdigit() or ch in ".-"))
                    if val:
                        try:
                            c = float(val)
                            temps = {"cpu": [{"label": "cpu", "current": c, "high": None, "critical": None}]}
                            break
                        except Exception:
                            pass
            except Exception:
                pass

    # macOS GPU names via system_profiler if GPUtil didn't provide GPUs
    if _system == "Darwin" and not gpus:
        try:
            import subprocess as _sp, json as _json
            res = _sp.run(["/usr/sbin/system_profiler", "SPDisplaysDataType", "-json"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0 and res.stdout:
                data = _json.loads(res.stdout)
                arr = data.get("SPDisplaysDataType", [])
                for it in arr:
                    name = it.get("sppci_model") or it.get("_name")
                    if name:
                        gpus.append({"id": None, "name": name, "load": None, "memory_total": None, "memory_used": None, "temperature": None, "uuid": None})
        except Exception:
            pass

    # Linux NVIDIA fallback via nvidia-smi
    if _system == "Linux" and not gpus:
        try:
            import shutil as _sh, subprocess as _sp
            if _sh.which("nvidia-smi"):
                res = _sp.run([
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,temperature.gpu,memory.total,memory.used,uuid",
                    "--format=csv,noheader,nounits"
                ], capture_output=True, text=True, timeout=1.5)
                if res.returncode == 0 and res.stdout:
                    for idx, line in enumerate(res.stdout.strip().splitlines()):
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 5:
                            name, util, temp, mem_total, mem_used = parts[:5]
                            uuid = parts[5] if len(parts) > 5 else None
                            try:
                                load_val = float(util) / 100.0
                            except Exception:
                                load_val = None
                            try:
                                temp_val = float(temp)
                            except Exception:
                                temp_val = None
                            gpus.append({
                                "id": idx,
                                "name": name,
                                "load": load_val,
                                "memory_total": float(mem_total),
                                "memory_used": float(mem_used),
                                "temperature": temp_val,
                                "uuid": uuid,
                            })
        except Exception:
            pass

    # Windows NVIDIA fallback via nvidia-smi
    if _system == "Windows" and not gpus:
        try:
            import shutil as _sh, subprocess as _sp
            smi = _sh.which("nvidia-smi.exe") or _sh.which("nvidia-smi")
            if smi:
                res = _sp.run([
                    smi,
                    "--query-gpu=name,utilization.gpu,temperature.gpu,memory.total,memory.used,uuid",
                    "--format=csv,noheader,nounits"
                ], capture_output=True, text=True, timeout=1.5)
                if res.returncode == 0 and res.stdout:
                    for idx, line in enumerate(res.stdout.strip().splitlines()):
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 5:
                            name, util, temp, mem_total, mem_used = parts[:5]
                            uuid = parts[5] if len(parts) > 5 else None
                            try:
                                load_val = float(util) / 100.0
                            except Exception:
                                load_val = None
                            try:
                                temp_val = float(temp)
                            except Exception:
                                temp_val = None
                            gpus.append({
                                "id": idx,
                                "name": name,
                                "load": load_val,
                                "memory_total": float(mem_total),
                                "memory_used": float(mem_used),
                                "temperature": temp_val,
                                "uuid": uuid,
                            })
        except Exception:
            pass

    # Windows CPU temperature via WMIC (deprecated but still present on many systems)
    if _system == "Windows" and not temps:
        try:
            import shutil as _sh, subprocess as _sp
            wmic = _sh.which("wmic")
            if wmic:
                res = _sp.run([wmic, "/namespace:\\\\\root\\wmi", "PATH", "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"],
                               capture_output=True, text=True, timeout=1.5)
                if res.returncode == 0 and res.stdout:
                    vals = []
                    for line in res.stdout.splitlines():
                        line = line.strip()
                        if not line or not line[0].isdigit():
                            continue
                        try:
                            # WMIC returns tenths of Kelvin
                            kelvin_tenths = float(line)
                            celsius = kelvin_tenths / 10.0 - 273.15
                            vals.append(celsius)
                        except Exception:
                            pass
                    if vals:
                        temps = {"cpu": [{"label": f"cpu{i}", "current": v, "high": None, "critical": None} for i, v in enumerate(vals)]}
        except Exception:
            pass

    # loadavg best-effort (POSIX)
    try:
        loadavg = _os.getloadavg()
    except Exception:
        loadavg = None

    info = {
        "time": now,
        "uptime_seconds": now - state.start_time,
        "os": {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "python": sys.version.split()[0],
            "cpu": cpu,
            "memory": mem,
            "temperatures": temps,
            "gpu": gpus,
            "loadavg": loadavg,
        },
        "process": {
            "pid": os.getpid(),
            "cwd": str(Path.cwd()),
        },
        "session": sess,
        "devices": devices,
        "websocket": ws,
        "queues": queues,
    }
    return info


def status_writer(stop_event: threading.Event, path: Path | None = None, interval: float = 1.0) -> None:
    """Periodically write a JSON status snapshot for external monitors."""
    if path is None:
        path = Path("status.json")
    while not stop_event.is_set():
        try:
            data = snapshot()
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(path)
        except Exception:
            # Avoid crashing status writer; best-effort
            pass
        stop_event.wait(interval)
