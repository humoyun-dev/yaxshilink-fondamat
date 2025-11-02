# YaxshiLink Fandomat — 24/7 O‘rnatish (O‘zbek)

Bu hujjat Fandomat dasturini o‘rnatish va 24/7 ishlatish bo‘yicha qo‘llanma. To‘liq inglizcha qo‘llanma `docs/DEPLOYMENT.md` faylida.

---

## Monitor (interaktiv)

Interaktiv monitorni ochish:

```bash
python3 scripts/monitor.py
```

Agar universal o‘rnatuvchi orqali o‘rnatilgan bo‘lsa va aniq manzil ko‘rsatmoqchi bo‘lsangiz:

```bash
python3 scripts/monitor.py --dir ~/.yaxshilink/app
```

---

## Tez start (bitta buyruq)

Bu buyruq foydalanuvchi darajasida o‘rnatadi, virtual muhit yaratadi, sozlash savollarini beradi va servisni ishga tushiradi:

```bash
python3 scripts/bootstrap.py
```

Tugagach:

- macOS/Linux: dastur `~/.yaxshilink` ichida
- Windows: dastur `%LOCALAPPDATA%\yaxshilink` ichida
- Servis ishga tushgan bo‘ladi va login paytida avtomatik boshlanadi.

---

## Universal o‘rnatuvchi (barcha OS, foydalanuvchi uchun)

- O‘rnatish:

```bash
python3 scripts/installer.py install
```

- O‘chirish:

```bash
python3 scripts/installer.py uninstall
```

- Dastlabki sozlash (WS_URL, FANDOMAT_ID, DEVICE_TOKEN va portlar saqlanadi):

```bash
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --setup   # macOS/Linux
```

Windowsda mos yo‘llarni `%LOCALAPPDATA%` dan foydalanib kiriting.

- Yangilash (ustiga qayta o‘rnatish):

```bash
python3 scripts/installer.py install
```

---

## Qo‘lda o‘rnatish (alternativ)

```bash
./scripts/setup_venv.sh
./.venv/bin/python ./main.py --configure-only
./.venv/bin/python ./main.py --setup
```

---

## Servisni boshqarish

- Linux (systemd user):

```bash
systemctl --user status yaxshilink-fandomat.service
journalctl --user-unit=yaxshilink-fandomat -f
```

- macOS (launchd):

```bash
launchctl list | grep com.yaxshi.fandomat
```

- Windows (Scheduled Task):

```powershell
schtasks /Query /TN YaxshiLinkFandomat
```

---

## Loglar

Dastur aylanadigan (rotating) loglarni yozadi (2MB × 5):

- system.log — umumiy xabarlar
- scanner.log — skaner o‘qishlari va hodisalar
- arduino.log — Arduino I/O va yuborilgan buyruqlar
- websocket.log — WS ulanishi va xabarlar
- session.log — sessiya (start/cancel/timeout/bottle)

Manzil:

- O‘rnatuvchi bilan: `~/.yaxshilink/logs/` (macOS/Linux) yoki `%LOCALAPPDATA%\yaxshilink\logs\` (Windows)
- Qo‘lda ishga tushirish: `./logs/`
- O‘zgartirish: `YAXSHILINK_LOG_DIR` muhit o‘zgaruvchisi

---

## Konfiguratsiya

`config.json` fayli (asosiy papkada yoki o‘rnatuvchi bilan `~/.yaxshilink/app/` ichida):

- WS_URL — WebSocket manzili (masalan, `wss://api.yaxshi.link/ws/fandomats`)
- FANDOMAT_ID — qurilma ID (butun son)
- DEVICE_TOKEN — autentifikatsiya tokeni
- SCANNER_PORT / ARDUINO_PORT — port yo‘llari
- BAUDRATE_SCANNER / BAUDRATE_ARDUINO — tezlik (standart 9600)

Asosiy flaglar: `--list-ports`, `--scanner-port`, `--arduino-port`, `--baudrate[-scanner|-arduino]`, `--setup`.

---

## Muammolar va yechimlar (qisqa)

- Linux’da port ruxsati yo‘q: foydalanuvchini `dialout` (yoki `uucp`/`plugdev`) guruhiga qo‘shing.
- WS ishlamayapti: `WS_URL`, internet va firewall/proksi qoidalarini tekshiring.
- Skaner noto‘g‘ri belgilar: baudrate ni tekshiring.
- Sessiya to‘satdan tugadi: 90 soniya harakatsizlikdan so‘ng sessiya avtomatik tugaydi.
