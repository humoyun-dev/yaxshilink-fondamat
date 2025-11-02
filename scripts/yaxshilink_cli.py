#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "yaxshilink-fandomat"
LAUNCHD_LABEL = "com.yaxshi.fandomat"
TASK_NAME = "YaxshiLinkFandomat"


def is_linux() -> bool:
    return platform.system() == "Linux"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_windows() -> bool:
    return platform.system() == "Windows"


def install_root() -> Path:
    if is_windows():
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local) / "yaxshilink"
    return Path.home() / ".yaxshilink"


def venv_python() -> Path:
    root = install_root()
    if is_windows():
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def app_dir() -> Path:
    return install_root() / "app"


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check)


def cmd_start(args) -> int:
    if is_linux():
        run(["systemctl", "--user", "start", SERVICE_NAME], check=False)
    elif is_macos():
        # ensure loaded, then start
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        if plist.exists():
            run(["launchctl", "load", str(plist)], check=False)
        run(["launchctl", "start", LAUNCHD_LABEL], check=False)
    elif is_windows():
        run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
    else:
        print("Unsupported OS")
        return 1
    print("Started")
    return 0


def cmd_stop(args) -> int:
    if is_linux():
        run(["systemctl", "--user", "stop", SERVICE_NAME], check=False)
    elif is_macos():
        run(["launchctl", "stop", LAUNCHD_LABEL], check=False)
        run(["launchctl", "unload", str(Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist")], check=False)
    elif is_windows():
        run(["schtasks", "/End", "/TN", TASK_NAME], check=False)
    else:
        print("Unsupported OS")
        return 1
    print("Stopped")
    return 0


def cmd_restart(args) -> int:
    if is_linux():
        run(["systemctl", "--user", "restart", SERVICE_NAME], check=False)
    elif is_macos():
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        run(["launchctl", "unload", str(plist)], check=False)
        run(["launchctl", "load", str(plist)], check=False)
        run(["launchctl", "start", LAUNCHD_LABEL], check=False)
    elif is_windows():
        run(["schtasks", "/End", "/TN", TASK_NAME], check=False)
        run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
    else:
        print("Unsupported OS")
        return 1
    print("Restarted")
    return 0


def cmd_status(args) -> int:
    if is_linux():
        run(["systemctl", "--user", "status", SERVICE_NAME], check=False)
        return 0
    elif is_macos():
        run(["launchctl", "list"], check=False)
        return 0
    elif is_windows():
        run(["schtasks", "/Query", "/TN", TASK_NAME], check=False)
        return 0
    print("Unsupported OS")
    return 1


def cmd_monitor(args) -> int:
    py = venv_python()
    script = app_dir() / "scripts" / "monitor.py"
    if not script.exists():
        print("Monitor script not found in installed app.")
        return 1
    return run([str(py), str(script), "--dir", str(app_dir())], check=False).returncode


def cmd_setup(args) -> int:
    # Non-blocking, two short steps
    py = venv_python()
    main_py = app_dir() / "main.py"
    run([str(py), str(main_py), "--configure-only"], check=False)
    run([str(py), str(main_py), "--device-setup-only"], check=False)
    return 0


def cmd_configure(args) -> int:
    py = venv_python()
    main_py = app_dir() / "main.py"
    return run([str(py), str(main_py), "--configure-only"], check=False).returncode


def cmd_device_setup(args) -> int:
    py = venv_python()
    main_py = app_dir() / "main.py"
    return run([str(py), str(main_py), "--device-setup-only"], check=False).returncode


def _remove_install_root(root: Path):
    try:
        shutil.rmtree(root, ignore_errors=True)
    except Exception as e:
        print(f"Failed to remove {root}: {e}")


def cmd_uninstall(args) -> int:
    root = install_root()
    # stop and deregister service first
    if is_linux():
        run(["systemctl", "--user", "disable", "--now", SERVICE_NAME], check=False)
        user_systemd = Path.home() / ".config" / "systemd" / "user"
        unit = user_systemd / f"{SERVICE_NAME}.service"
        if unit.exists():
            try:
                unit.unlink()
            except Exception:
                pass
        run(["systemctl", "--user", "daemon-reload"], check=False)
    elif is_macos():
        plist = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
        run(["launchctl", "unload", str(plist)], check=False)
        if plist.exists():
            try:
                plist.unlink()
            except Exception:
                pass
    elif is_windows():
        run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], check=False)
    else:
        print("Unsupported OS")
    _remove_install_root(root)
    print("Uninstalled.")
    return 0


def cmd_where(args) -> int:
    print(install_root())
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="yaxshilink", description="Control YaxshiLink Fandomat service")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("start", help="Start the background service").set_defaults(func=cmd_start)
    sub.add_parser("stop", help="Stop the background service").set_defaults(func=cmd_stop)
    sub.add_parser("restart", help="Restart the background service").set_defaults(func=cmd_restart)
    sub.add_parser("status", help="Show service status").set_defaults(func=cmd_status)
    sub.add_parser("monitor", help="Open interactive monitor").set_defaults(func=cmd_monitor)
    sub.add_parser("setup", help="Run initial two-step setup (credentials + device ports)").set_defaults(func=cmd_setup)
    sub.add_parser("configure", help="Configure WS_URL/FANDOMAT_ID/DEVICE_TOKEN only").set_defaults(func=cmd_configure)
    sub.add_parser("device-setup", help="Choose and save device ports only").set_defaults(func=cmd_device_setup)
    sub.add_parser("uninstall", help="Unregister service and remove installation").set_defaults(func=cmd_uninstall)
    sub.add_parser("where", help="Print install root path").set_defaults(func=cmd_where)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
