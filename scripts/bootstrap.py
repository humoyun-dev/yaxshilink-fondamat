#!/usr/bin/env python3
"""
One-shot bootstrap installer for YaxshiLink Fandomat.

- Creates a per-user installation in the standard location
- Creates a virtual environment and installs dependencies
- Runs interactive setup once (prompts for WS and device ports)
- Registers and starts a user-level background service (systemd/launchd/Task Scheduler)

Usage:
  python3 scripts/bootstrap.py
"""
import os
import sys
import subprocess
import platform
from pathlib import Path


def run(cmd, check=True):
    print(f"[RUN] {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, check=check)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    # Ensure Python 3
    if sys.version_info < (3, 8):
        print("Python 3.8+ is required.")
        return 1

    # Run the universal installer with auto-setup
    try:
        run([sys.executable, "scripts/installer.py", "install", "--auto-setup"])
    except subprocess.CalledProcessError as e:
        print(f"Installer failed with exit code {e.returncode}")
        return e.returncode

    print("\nAll done. The background service is installed and started.")
    print("You can manage it using your OS tools:")
    system = platform.system()
    if system == "Linux":
        print("  systemctl --user status yaxshilink-fandomat.service")
    elif system == "Darwin":
        print("  launchctl list | grep com.yaxshi.fandomat")
    elif system == "Windows":
        print("  schtasks /Query /TN YaxshiLinkFandomat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
