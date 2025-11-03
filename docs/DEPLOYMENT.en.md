# YaxshiLink Fandomat — 24/7 Deployment

This guide shows how to install and run the Fandomat runtime. You have two options:

- Universal per-user installer (recommended, cross‑platform)
- OS-specific service setup (advanced)

If you want the fastest path, use the Quick start below. For more control, use the Universal installer or manual OS‑specific setup.

---

## Quick start (one command)

This will install per‑user, create a virtualenv, prompt you for setup, and start the service automatically.

```bash
python3 scripts/bootstrap.py
```

After it finishes:

- macOS/Linux: the app lives in `~/.yaxshilink`
- Windows: the app lives in `%LOCALAPPDATA%\yaxshilink`
- The service is already running and will auto‑start on login.

## 1) Universal installer (all OS, per‑user)

The installer copies the app to a standard per‑user location, creates a virtualenv, registers a user-level background service, and writes a manifest so it can be fully uninstalled later.

Install:

```bash
# From the project root
python3 ./scripts/installer.py install
```

Uninstall:

```bash
python3 ./scripts/installer.py uninstall
```

Notes:

- Default install directory:
  - macOS/Linux: ~/.yaxshilink
  - Windows: %LOCALAPPDATA%\yaxshilink
- The installer registers a per‑user service and performs a non‑blocking first‑time setup sequence to avoid hanging:
  - Linux: systemd user service
  - macOS: launchd LaunchAgent
  - Windows: Scheduled Task (at user logon)
- First-time configuration: after install, run the one-time setup to store credentials and device ports. The installer’s auto-setup runs two short commands that exit immediately to avoid starting the long‑running app:

```bash
# 1) Save server credentials only (non-blocking)
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --configure-only   # macOS/Linux
# 2) Choose and save device ports (non-blocking)
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --device-setup-only
```

On Windows, replace the paths accordingly, e.g.:

```powershell
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --configure-only
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --device-setup-only
```

Once the first setup is done, the background service will run without prompts.

Upgrade (reinstall over existing):

```bash
python3 ./scripts/installer.py install
```

Custom install location:

```bash
python3 ./scripts/installer.py install --dir /path/to/custom/location
python3 ./scripts/installer.py uninstall --dir /path/to/custom/location
```

---

## 2) One-time setup (manual; optional alternative)

```bash
# Create venv and install deps
./scripts/setup_venv.sh

# Enter initial settings (WS_URL, FANDOMAT_ID, DEVICE_TOKEN) and save (non‑blocking)
./.venv/bin/python ./main.py --configure-only

# Choose and save device ports without starting the long‑running app (non‑blocking)
./.venv/bin/python ./main.py --device-setup-only

# Alternatively, do both in one interactive session (blocking run starts afterwards)
./.venv/bin/python ./main.py --setup
```

After the first successful interactive run, the app stores:

- WS_URL, FANDOMAT_ID, DEVICE_TOKEN
- SCANNER_PORT, ARDUINO_PORT
- BAUDRATE_SCANNER, BAUDRATE_ARDUINO

Subsequent runs won’t prompt again unless you pass `--setup`.

---

## 3) Linux (systemd) — manual

Edit paths in `scripts/systemd/yaxshilink-fandomat.service` to your project and venv. Then install:

```bash
# Copy to systemd
sudo cp scripts/systemd/yaxshilink-fandomat.service /etc/systemd/system/yaxshilink-fandomat.service

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable --now yaxshilink-fandomat.service

# Check status
sudo systemctl status yaxshilink-fandomat.service
# View logs
journalctl -u yaxshilink-fandomat -f
```

Tip: If you prefer user services (no root), use `~/.config/systemd/user/` and `systemctl --user` instead.

Service management (user scope):

```bash
systemctl --user start yaxshilink-fandomat.service
systemctl --user stop yaxshilink-fandomat.service
systemctl --user restart yaxshilink-fandomat.service
systemctl --user status yaxshilink-fandomat.service
journalctl --user-unit=yaxshilink-fandomat -f
```

---

## 4) macOS (launchd) — manual

Edit paths in `scripts/launchd/com.yaxshi.fandomat.plist`. Then:

```bash
# Create logs folder if missing
mkdir -p ./logs

# Install as a user LaunchAgent
cp scripts/launchd/com.yaxshi.fandomat.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
launchctl start com.yaxshi.fandomat

# Check status
launchctl list | grep com.yaxshi.fandomat
# Tail logs
tail -f ./logs/launchd.out.log ./logs/launchd.err.log
```

It will auto-start at login and restart if it crashes.

Service management:

```bash
# Stop
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
# Start
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
# (Re)start running job
launchctl start com.yaxshi.fandomat
```

---

## 5) Windows (Scheduled Task) — manual

Open PowerShell as Administrator and run:

```powershell
# Adjust paths with parameters if needed
scripts\windows\register_task.ps1 -ProjectDir "C:\\path\\to\\yaxshilink" -PythonExe "C:\\path\\to\\yaxshilink\\.venv\\Scripts\\python.exe"
```

The task runs at user logon and restarts on failure.

Service management:

```powershell
# Start now
schtasks /Run /TN YaxshiLinkFandomat
# Stop
schtasks /End /TN YaxshiLinkFandomat
# View
schtasks /Query /TN YaxshiLinkFandomat
```

To view logs, redirect output when running manually or use a logging solution (e.g., write to file within the app).

---

## 6) Operations

- Manual run (no prompts after first setup):

```bash
./.venv/bin/python ./main.py --no-config-prompt
```

- Force re-setup:

```bash
./.venv/bin/python ./main.py --setup
```

- Show serial ports:

```bash
./.venv/bin/python ./main.py --list-ports
```

### Global CLI (yaxshilink)

The installer adds a per-user command to control the app from anywhere. Open a new terminal after install so PATH updates take effect.

Common commands:

```bash
yaxshilink status        # Show service status
yaxshilink start         # Start background service
yaxshilink stop          # Stop background service
yaxshilink restart       # Restart service
yaxshilink update        # Pull latest from GitHub and restart

yaxshilink monitor       # Open interactive monitor (points to installed app)

yaxshilink setup         # One-time two-step setup (credentials + device ports)
yaxshilink configure     # Only WS_URL / FANDOMAT_ID / DEVICE_TOKEN
yaxshilink device-setup  # Only scanner/arduino ports

yaxshilink uninstall     # Unregister service and remove installation
yaxshilink where         # Print install folder (e.g., ~/.yaxshilink)
```

If your shell can’t find the command, ensure ~/.local/bin is on your PATH (Unix):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## OS‑specific notes and troubleshooting

### Linux

- The installer registers a systemd user service (no sudo). It runs while you’re logged in. For 24/7 without a login session, enable lingering:

```bash
loginctl enable-linger "$USER"
```

- Serial port permissions: ensure your user is in the serial group (often `dialout`, sometimes `uucp`/`plugdev`).

```bash
sudo usermod -a -G dialout "$USER" && newgrp dialout
```

### macOS

- LaunchAgent is installed in `~/Library/LaunchAgents` and starts at login. Logs go to `~/.yaxshilink/logs/` when using the universal installer.
- If you edit the plist, unload then load again:

```bash
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist || true
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
```

### Windows

- The installer creates `run.cmd` in the install folder so the task starts in the correct directory (ensuring `config.json` is found).
- If you need to change task settings, delete and reinstall, or adjust with `schtasks /Change`.

If you don’t see new logs or the app isn’t running, try running the app once in the foreground to surface errors:

```powershell
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --no-config-prompt
```

## Notes

- The app reconnects to WebSocket and serial devices automatically.
- Sessions auto-end after 90s of server inactivity, and Arduino is set to Idle (E).
- For environment-only configuration, set WS_URL, FANDOMAT_ID, DEVICE_TOKEN before running, or edit `config.json` directly.
- Make sure your user has permission to access serial ports (e.g., `dialout` group on Linux).

### Logs

The app writes rotating logs (2MB x 5 backups) per component plus a general system log:

- system.log — general runtime messages
- scanner.log — barcode scanner input and events
- arduino.log — Arduino I/O and command writes
- websocket.log — WS connection, sends/receives
- session.log — session lifecycle (start, cancel, timeout, bottle outcomes)

Location:

- With the universal installer: inside the install folder’s `logs/` directory (e.g., `~/.yaxshilink/logs/` on macOS/Linux).
- Manual runs: `./logs/` under the current working directory.
- Override: set environment `YAXSHILINK_LOG_DIR` to a custom path.

---

## Monitor (interactive)

Open an interactive status monitor to see device and session state, WebSocket connectivity, OS info, queues, and more:

```bash
python3 scripts/monitor.py
```

If you installed via the universal installer and need to point to the installed app directory explicitly:

```bash
python3 scripts/monitor.py --dir ~/.yaxshilink/app   # macOS/Linux
```

On Windows, adapt the path under `%LOCALAPPDATA%\yaxshilink\app`.

---

## Configuration reference

File: `config.json` (created in the working directory of the app; with the universal installer this is inside the install folder’s `app/` directory)

- WS_URL: WebSocket endpoint, e.g. `wss://api.yaxshi.link/ws/fandomats`
- FANDOMAT_ID: integer device ID
- DEVICE_TOKEN: access token for authentication
- SCANNER_PORT: serial path to scanner (e.g., `/dev/ttyACM0`, `/dev/cu.usbmodem...`, `COM3`)
- ARDUINO_PORT: serial path to Arduino
- BAUDRATE_SCANNER: scanner baud rate (default 9600)
- BAUDRATE_ARDUINO: Arduino baud rate (default 9600)

> Tip: You can edit `config.json` while the app is stopped, then restart the service to apply changes.

### CLI flags (`main.py`)

- `--scanner-port`, `--arduino-port`: set device ports (overrides config for this run)
- `--baudrate`, `--baudrate-scanner`, `--baudrate-arduino`: set baud rates
- `--list-ports`: list available serial ports and exit
- `--raw`: print raw bytes instead of decoding
- `--reconnect-delay`: seconds before retry after disconnect (default 2.0)
- `--newline`: one of `\n`, `\r\n`, or empty string for how lines print
- `--no-config-prompt`: do not prompt for WS settings on startup
- `--configure-only`: prompt for WS settings, save to config.json, exit
- `--setup`: force interactive setup (WS + device ports), even if config exists
- `--device-setup-only`: prompt only for device ports/baud, save, then exit (non‑blocking)

---

## Network requirements

- Outbound access to the configured WS_URL over TLS (wss) or ws.
- If behind a firewall/proxy, ensure the host and port are allowed and WebSocket upgrade is permitted.

---

## Updating the app

Using the universal installer:

```bash
python3 scripts/installer.py install
```

This re-copies the app and re-installs requirements. Restart the service if needed.

Manual (repo checkout):

```bash
./scripts/setup_venv.sh
./.venv/bin/python ./main.py --no-config-prompt
```

---

## Uninstall

Universal installer:

```bash
python3 scripts/installer.py uninstall
```

Manual:

- Stop the service (see OS sections), then remove the files you installed.

---

## Troubleshooting quick checklist

- Serial port not found:
  - Run `--list-ports` and verify the device name.
  - Check permissions (Linux `dialout` group), cable, and drivers.
- Permission denied on serial (Linux):
  - Add your user to `dialout` (or `uucp`/`plugdev`) and re‑login or use `newgrp`.
- WS connection fails:
  - Verify WS_URL and internet connectivity; check firewall/proxy rules.
- Scanner reads but no server action:
  - Ensure a session is started from the server; the app only checks bottles during an active session.
- Wrong characters or missing scans:
  - Baud rate mismatch; set `--baudrate-scanner` correctly.
- Session ends unexpectedly:
  - A 90s inactivity timeout will end sessions automatically.
