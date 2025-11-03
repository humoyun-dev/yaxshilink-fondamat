#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SERVICE_NAME = "yaxshilink-fandomat"
LAUNCHD_LABEL = "com.yaxshi.fandomat"
TASK_NAME = "YaxshiLinkFandomat"
REPO_URL = "https://github.com/humoyun-dev/yaxshilink-fondamat.git"


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


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_manifest(root: Path) -> dict | None:
    m = root / "install_manifest.json"
    if not m.exists():
        return None
    try:
        with m.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_manifest(root: Path, manifest: dict) -> None:
    m = root / "install_manifest.json"
    try:
        with m.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    except Exception:
        pass


def cmd_update(args) -> int:
    root = install_root()
    dst_app = app_dir()
    vpy = venv_python()

    print("[update] Stopping service…")
    try:
        cmd_stop(args)
    except Exception:
        pass

    with tempfile.TemporaryDirectory() as tmp:
        clone_dir = Path(tmp) / "repo"
        print(f"[update] Cloning repo {REPO_URL} → {clone_dir} …")
        res = run(["git", "clone", "--depth", "1", REPO_URL, str(clone_dir)], check=False)
        if res.returncode != 0 or not clone_dir.exists():
            print("[update] ERROR: Failed to clone repository. Ensure 'git' is installed and the URL is reachable.")
            return 2

        # Compute requirements hash from new source
        new_req = clone_dir / "requirements.txt"
        new_req_hash = _hash_file(new_req) if new_req.exists() else None

        # Replace app directory
        print(f"[update] Replacing installed app at {dst_app} …")
        try:
            if dst_app.exists():
                shutil.rmtree(dst_app, ignore_errors=True)
            ignore = shutil.ignore_patterns(".git", ".gitignore", ".venv", "__pycache__", ".DS_Store", "logs")
            shutil.copytree(clone_dir, dst_app, ignore=ignore)
        except Exception as e:
            print(f"[update] ERROR: Failed to copy files: {e}")
            return 3

    # Install dependencies if changed
    try:
        manifest = _read_manifest(root) or {}
        old_hash = manifest.get("requirements_hash")
        if new_req_hash and new_req_hash != old_hash:
            print("[update] Dependencies changed — installing requirements…")
            run([str(vpy), "-m", "pip", "install", "-r", str(dst_app / "requirements.txt")], check=False)
            manifest["requirements_hash"] = new_req_hash
        else:
            print("[update] Requirements unchanged — skipping dependency install.")
        # Update manifest metadata
        manifest["timestamp"] = datetime.utcnow().isoformat() + "Z"
        manifest.setdefault("app_name", "yaxshilink")
        manifest.setdefault("os", platform.system())
        manifest.setdefault("install_root", str(root))
        manifest.setdefault("app_dir", str(dst_app))
        manifest.setdefault("venv", str(root / ".venv"))
        manifest.setdefault("python", str(vpy))
        _write_manifest(root, manifest)
    except Exception as e:
        print(f"[update] WARN: Could not update manifest or install deps cleanly: {e}")

    print("[update] Restarting service…")
    try:
        cmd_restart(args)
    except Exception:
        # try start as fallback
        cmd_start(args)
    print("[update] Done.")
    return 0


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
    sub.add_parser("update", help="Update app from GitHub and restart service").set_defaults(func=cmd_update)
    sub.add_parser("uninstall", help="Unregister service and remove installation").set_defaults(func=cmd_uninstall)
    sub.add_parser("where", help="Print install root path").set_defaults(func=cmd_where)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
