#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
import platform


def load_status(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def format_seconds(sec: float) -> str:
    sec = int(sec)
    d, r = divmod(sec, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    parts = []
    if d:
        parts.append(f"{d}d")
    if d or h:
        parts.append(f"{h}h")
    parts.append(f"{m}m {s}s")
    return " ".join(parts)


def render(screen, data: dict):
    lines = []
    if not data:
        lines.append("No status available. Is the app running? Expected status.json next to config.json.")
    else:
        lines.append("YaxshiLink Fandomat — Monitor")
        lines.append("")
        osinfo = data.get("os", {})
        proc = data.get("process", {})
        lines.append(f"OS: {osinfo.get('system')} {osinfo.get('release')} — Python {osinfo.get('python')}")
        lines.append(f"Uptime: {format_seconds(data.get('uptime_seconds', 0))} | PID: {proc.get('pid')} | CWD: {proc.get('cwd')}")
        # CPU / RAM / GPU / Temps
        cpu = osinfo.get('cpu') or {}
        mem = osinfo.get('memory') or {}
        loadavg = osinfo.get('loadavg')
        cpu_line = f"CPU: {cpu.get('physical_cores')} phys / {cpu.get('logical_cores')} log | total {cpu.get('percent_total')}%"
        if loadavg:
            cpu_line += f" | loadavg {tuple(loadavg)}"
        lines.append(cpu_line)
        if mem:
            total_gb = (mem.get('total', 0) or 0) / (1024**3)
            used_gb = (mem.get('used', 0) or 0) / (1024**3)
            lines.append(f"RAM: {used_gb:.1f} / {total_gb:.1f} GB ({mem.get('percent')}%)")
        gpus = osinfo.get('gpu') or []
        if gpus:
            g0 = gpus[0]
            lines.append(f"GPU: {g0.get('name')} | load {int((g0.get('load') or 0)*100)}% | temp {g0.get('temperature','?')}°C | mem {g0.get('memory_used','?')}/{g0.get('memory_total','?')} MB")
            if len(gpus) > 1:
                lines.append(f"(+{len(gpus)-1} more GPUs)")
        temps = osinfo.get('temperatures') or {}
        if temps:
            # show first key summary
            k = next(iter(temps.keys()))
            arr = temps.get(k, [])
            if arr:
                t0 = arr[0]
                lines.append(f"Temp: {k} {t0.get('current','?')}°C (high {t0.get('high')}, crit {t0.get('critical')})")
        lines.append("")
        sess = data.get("session", {})
        lines.append(f"Session: {'ACTIVE' if sess.get('active') else 'idle'} | ID: {sess.get('session_id')} | Bottles: {sess.get('bottle_counter')}")
        ws = data.get("websocket", {})
        lines.append(f"WebSocket: {'connected' if ws.get('connected') else 'disconnected'} | URL: {ws.get('url')} | Last: {ws.get('last_event')}")
        dev = data.get("devices", {})
        scn = dev.get('scanner', {})
        ard = dev.get('arduino', {})
        lines.append(f"Scanner: {'connected' if scn.get('connected') else 'disconnected'} | Port: {scn.get('port')} @ {scn.get('baud')} | Last: {scn.get('last_line')}")
        lines.append(f"Arduino: {'connected' if ard.get('connected') else 'disconnected'} | Port: {ard.get('port')} @ {ard.get('baud')} | Last: {ard.get('last_line')}")
        q = data.get("queues", {})
        lines.append(f"Queues: outbox={q.get('outbox_size')}  arduino_cmds={q.get('arduino_cmd_queue_size')}")
        lines.append("")
        lines.append("Press Q to quit. Auto-refreshing…")

    if screen is None:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n".join(lines))
        return

    h, w = screen.getmaxyx()
    screen.erase()
    for idx, ln in enumerate(lines[: h - 1]):
        try:
            screen.addstr(idx, 0, ln[: w - 1])
        except Exception:
            pass
    screen.refresh()


def monitor_loop(status_path: Path, use_curses: bool = True):
    if use_curses:
        try:
            import curses
        except Exception:
            use_curses = False

    if not use_curses:
        while True:
            data = load_status(status_path)
            render(None, data)
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
        return

    import curses

    def _ui(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        while True:
            data = load_status(status_path)
            render(stdscr, data)
            for _ in range(10):
                try:
                    ch = stdscr.getch()
                    if ch in (ord('q'), ord('Q')):
                        return
                except Exception:
                    pass
                time.sleep(0.1)

    curses.wrapper(_ui)


def _discover_status_path() -> Path | None:
    # 1) Env override
    p = os.environ.get("YAXSHILINK_STATUS_PATH")
    if p:
        pp = Path(p).expanduser()
        if pp.exists():
            return pp
    # 2) Current working dir
    cwd = Path.cwd() / "status.json"
    if cwd.exists():
        return cwd
    # 3) Installer default locations
    sysname = platform.system()
    if sysname in ("Linux", "Darwin"):
        cand = Path.home() / ".yaxshilink" / "app" / "status.json"
        if cand.exists():
            return cand
    elif sysname == "Windows":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            cand = Path(local) / "yaxshilink" / "app" / "status.json"
            if cand.exists():
                return cand
    return None


def main():
    import argparse
    p = argparse.ArgumentParser(description="Interactive monitor for YaxshiLink Fandomat")
    p.add_argument("--dir", help="Directory containing status.json (default: current working dir)")
    p.add_argument("--no-curses", action="store_true", help="Disable curses TUI; use simple refresh in terminal")
    args = p.parse_args()

    if args.dir:
        status_dir = Path(args.dir)
        status_path = status_dir / "status.json"
    else:
        status_path = _discover_status_path() or (Path.cwd() / "status.json")
    if not status_path.exists():
        print(f"Looking for {status_path}. If empty, start the app so it writes status.json.\n"
              f"You can also point to a directory with --dir or set YAXSHILINK_STATUS_PATH to the file path.")
    monitor_loop(status_path, use_curses=(not args.no_curses))


if __name__ == "__main__":
    sys.exit(main())
