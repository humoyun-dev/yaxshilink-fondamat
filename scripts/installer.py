#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path
from datetime import datetime

APP_NAME = "yaxshilink"
SERVICE_NAME = "yaxshilink-fandomat"
LAUNCHD_LABEL = "com.yaxshi.fandomat"
TASK_NAME = "YaxshiLinkFandomat"

IGNORES = shutil.ignore_patterns(
    ".git", ".gitignore", ".venv", "__pycache__", ".DS_Store", "logs"
)


def run(cmd, check=True, env=None):
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, env=env)


def is_macos():
    return platform.system() == "Darwin"


def is_linux():
    return platform.system() == "Linux"


def is_windows():
    return platform.system() == "Windows"


def default_install_root() -> Path:
    if is_windows():
        local = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(local) / APP_NAME
    # macOS/Linux -> per-user install under home
    return Path.home() / f".{APP_NAME}"


def python_exe(venv_dir: Path) -> Path:
    if is_windows():
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def write_manifest(install_root: Path, manifest: dict):
    manifest_path = install_root / "install_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest_path


def read_manifest(install_root: Path):
    manifest_path = install_root / "install_manifest.json"
    if not manifest_path.exists():
        return None
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_user_systemd_service(install_root: Path, venv: Path, app_dir: Path):
    user_systemd = Path.home() / ".config" / "systemd" / "user"
    user_systemd.mkdir(parents=True, exist_ok=True)
    unit_path = user_systemd / f"{SERVICE_NAME}.service"
    exec_start = f"{python_exe(venv)} {app_dir / 'main.py'} --no-config-prompt"
    unit = f"""
[Unit]
Description=YaxshiLink Fandomat
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={app_dir}
ExecStart={exec_start}
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
""".strip()
    unit_path.write_text(unit, encoding="utf-8")
    # enable and start
    run(["systemctl", "--user", "daemon-reload"], check=False)
    run(["systemctl", "--user", "enable", "--now", SERVICE_NAME])
    return str(unit_path)


def remove_user_systemd_service():
    # disable and stop; ignore failures
    run(["systemctl", "--user", "disable", "--now", SERVICE_NAME], check=False)
    user_systemd = Path.home() / ".config" / "systemd" / "user"
    unit_path = user_systemd / f"{SERVICE_NAME}.service"
    if unit_path.exists():
        try:
            unit_path.unlink()
        except Exception:
            pass
    run(["systemctl", "--user", "daemon-reload"], check=False)


def create_launchd_plist(install_root: Path, venv: Path, app_dir: Path):
    launch_agents = Path.home() / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True, exist_ok=True)
    out_log = install_root / "logs" / "launchd.out.log"
    err_log = install_root / "logs" / "launchd.err.log"
    (install_root / "logs").mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents / f"{LAUNCHD_LABEL}.plist"
    program = str(python_exe(venv))
    arguments = [program, str(app_dir / "main.py"), "--no-config-prompt"]
    plist = f"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{LAUNCHD_LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{arguments[0]}</string>
    <string>{arguments[1]}</string>
    <string>{arguments[2]}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{app_dir}</string>
  <key>StandardOutPath</key>
  <string>{out_log}</string>
  <key>StandardErrorPath</key>
  <string>{err_log}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
</dict>
</plist>
""".strip()
    plist_path.write_text(plist, encoding="utf-8")
    # load and start
    run(["launchctl", "unload", str(plist_path)], check=False)
    run(["launchctl", "load", str(plist_path)])
    run(["launchctl", "start", LAUNCHD_LABEL], check=False)
    return str(plist_path)


def remove_launchd_plist():
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
    run(["launchctl", "unload", str(plist_path)], check=False)
    if plist_path.exists():
        try:
            plist_path.unlink()
        except Exception:
            pass


def create_windows_task(install_root: Path, venv: Path, app_dir: Path):
    # Create a wrapper cmd that cd's into app_dir so config.json is resolved correctly
    runner = install_root / "run.cmd"
    py = python_exe(venv)
    content = (
        "@echo off\r\n"
        f"cd /d \"{app_dir}\"\r\n"
        f"\"{py}\" main.py --no-config-prompt\r\n"
    )
    runner.write_text(content, encoding="utf-8")

    # schtasks: create or update the task to run the wrapper on user logon
    run([
        "schtasks", "/Create", "/TN", TASK_NAME,
        "/SC", "ONLOGON", "/TR", str(runner), "/F"
    ])
    # try to start immediately once created
    run(["schtasks", "/Run", "/TN", TASK_NAME], check=False)
    return TASK_NAME


def remove_windows_task():
    run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], check=False)


def create_venv(install_root: Path):
    venv = install_root / ".venv"
    if venv.exists():
        return venv
    run([sys.executable, "-m", "venv", str(venv)])
    return venv


def pip_install(venv: Path, app_dir: Path):
    pip = python_exe(venv)
    req = app_dir / "requirements.txt"
    if not req.exists():
        # fallback to repo root requirements if not copied
        req = Path.cwd() / "requirements.txt"
    run([str(pip), "-m", "pip", "install", "--upgrade", "pip", "wheel", "setuptools"])
    run([str(pip), "-m", "pip", "install", "-r", str(req)])


def copy_project(src_root: Path, install_root: Path):
    app_dst = install_root / "app"
    if app_dst.exists():
        shutil.rmtree(app_dst)
    shutil.copytree(src_root, app_dst, ignore=IGNORES)
    return app_dst


def install(install_root: Path):
    src_root = Path.cwd()
    install_root.mkdir(parents=True, exist_ok=True)
    app_dir = copy_project(src_root, install_root)
    venv = create_venv(install_root)
    pip_install(venv, app_dir)

    created = []
    service_ref = None
    service_type = None

    if is_linux():
        unit_path = create_user_systemd_service(install_root, venv, app_dir)
        created.append(unit_path)
        service_ref = unit_path
        service_type = "systemd-user"
        # Serial permissions hint (best-effort): check common groups
        try:
            import grp, getpass
            user = getpass.getuser()
            groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]
            if not any(g in groups for g in ("dialout", "uucp", "plugdev")):
                print("[NOTE] Your user may need to be in 'dialout' (or uucp/plugdev) to access serial ports.\n"
                      "       Example: sudo usermod -a -G dialout $USER && newgrp dialout")
        except Exception:
            pass
    elif is_macos():
        plist_path = create_launchd_plist(install_root, venv, app_dir)
        created.append(plist_path)
        service_ref = plist_path
        service_type = "launchd"
    elif is_windows():
        task = create_windows_task(install_root, venv, app_dir)
        created.append(f"schtasks:{task}")
        service_ref = task
        service_type = "schtasks"
    else:
        print("Unsupported OS for service setup. Install will copy files and create venv only.")

    manifest = {
        "app_name": APP_NAME,
        "os": platform.system(),
        "install_root": str(install_root),
        "app_dir": str(app_dir),
        "venv": str(venv),
        "python": str(python_exe(venv)),
        "service_type": service_type,
        "service_ref": service_ref,
        "created": created,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": 1
    }
    mpath = write_manifest(install_root, manifest)

    print("\nInstall complete.")
    print(f"Install root: {install_root}")
    print(f"Manifest: {mpath}")
    print("Next steps:")
    print("- If this is the first run, run initial setup once to store config and device ports:")
    print(f"  {python_exe(venv)} {app_dir / 'main.py'} --setup")


def uninstall(install_root: Path):
    manifest = read_manifest(install_root)
    if not manifest:
        print(f"No manifest found at {install_root / 'install_manifest.json'}. Proceeding with best-effort cleanup.")

    if is_linux():
        remove_user_systemd_service()
    elif is_macos():
        remove_launchd_plist()
    elif is_windows():
        remove_windows_task()

    # remove install root
    if install_root.exists():
        print(f"Removing {install_root} ...")
        shutil.rmtree(install_root, ignore_errors=True)

    print("Uninstall complete.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Universal installer for YaxshiLink Fandomat (per-user).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_install = sub.add_parser("install", help="Install the app and register a per-user background service")
    p_install.add_argument("--dir", dest="install_dir", help="Install root directory (default: per-user)")
    p_install.add_argument("--auto-setup", action="store_true", help="Run initial interactive setup after install")

    p_un = sub.add_parser("uninstall", help="Stop service and remove the installation")
    p_un.add_argument("--dir", dest="install_dir", help="Install root directory (default: per-user)")

    args = parser.parse_args()

    install_root = Path(args.install_dir) if args.install_dir else default_install_root()

    if args.cmd == "install":
        install(install_root)
        if getattr(args, "auto_setup", False):
            # Run interactive setup in foreground
            app_dir = Path(install_root) / "app"
            venv = Path(install_root) / ".venv"
            run([str(python_exe(venv)), str(app_dir / "main.py"), "--setup"], check=False)
    elif args.cmd == "uninstall":
        uninstall(install_root)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())
