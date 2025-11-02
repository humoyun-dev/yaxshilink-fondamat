# YaxshiLink Fandomat — 24/7 Deployment

This is the primary deployment guide. Translations (full parity):

- English index: `docs/DEPLOYMENT.en.md`
- Русский: `docs/DEPLOYMENT.ru.md`
- O‘zbek: `docs/DEPLOYMENT.uz.full.md`

---

## Quick start (one command)

Install per-user, create a virtualenv, prompt for setup, and start the service automatically:

```bash
python3 scripts/bootstrap.py
```

- macOS/Linux install path: `~/.yaxshilink`
- Windows install path: `%LOCALAPPDATA%\yaxshilink`

## Universal installer (all OS)

Install / uninstall per-user service:

```bash
python3 scripts/installer.py install
python3 scripts/installer.py uninstall
```

First-time setup (saves WS_URL, FANDOMAT_ID, DEVICE_TOKEN and device ports):

```bash
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --setup   # macOS/Linux
```

On Windows, adapt the paths under `%LOCALAPPDATA%`.

## Monitor (interactive)

Open a live TUI showing OS metrics, devices, session, WebSocket, and queues:

```bash
python3 scripts/monitor.py
```

If installed with the universal installer, you can target the installed app directory:

```bash
python3 scripts/monitor.py --dir ~/.yaxshilink/app   # macOS/Linux
```

What you will see:

- OS metrics: CPU cores and usage, RAM usage, load average, GPU (if available), temperatures (Linux sensors, if available)
- Session: active/idle, session_id, bottle counter
- Devices: scanner/Arduino connected state, last lines, ports, baud
- WebSocket: connected, URL, last server event
- Queues: WS outbox size, Arduino command queue size

## Logs

Rotating logs (2MB × 5) are written per component and a general system log:

- system.log, scanner.log, arduino.log, websocket.log, session.log

Location:

- Installer: `~/.yaxshilink/logs/` (macOS/Linux), `%LOCALAPPDATA%\yaxshilink\logs\` (Windows)
- Manual runs: `./logs/`
- Override with `YAXSHILINK_LOG_DIR`

## Manual install (optional)

```bash
./scripts/setup_venv.sh
./.venv/bin/python ./main.py --configure-only
./.venv/bin/python ./main.py --setup
```

## Service management

- Linux (systemd user): `systemctl --user status yaxshilink-fandomat.service`
- macOS (launchd): `launchctl list | grep com.yaxshi.fandomat`
- Windows (Task Scheduler): `schtasks /Query /TN YaxshiLinkFandomat`

## Troubleshooting

- Serial permissions (Linux): add user to `dialout` (or `uucp`/`plugdev`)
- WS issues: verify `WS_URL`, internet, and firewall/proxy rules
- Scanner gibberish: check baud rate
- Session ends: 90s inactivity timeout auto-ends
