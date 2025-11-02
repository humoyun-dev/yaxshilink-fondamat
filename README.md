# YaxshiLink Fandomat

Cross‑platform device runtime for barcode scanner + Arduino, with WebSocket integration and 24/7 operation.

- Quick start: `python3 scripts/bootstrap.py`
- Monitor (interactive): `python3 scripts/monitor.py`

## Documentation languages

- English: `docs/DEPLOYMENT.en.md` (full) (index + monitor)
- Русский: `docs/DEPLOYMENT.ru.md`
- O‘zbek: `docs/DEPLOYMENT.uz.md`

## Key scripts

- `scripts/bootstrap.py` — one-shot: install + setup + start service
- `scripts/installer.py` — install/uninstall per user (systemd/launchd/Scheduled Task)
- `scripts/monitor.py` — interactive status monitor (curses if available)

## Logs

Rotating logs (2MB × 5) are written per component plus a system log. See the Logs section in the docs for locations and details.
