````markdown
# YaxshiLink Fandomat — 24/7 O‘rnatish (O‘zbek, to‘liq)

Bu to‘liq qo‘llanma Fandomat runtaymini o‘rnatish va ekspluatatsiya qilish bo‘yicha. Ikki yo‘l mavjud:

- Universal o‘rnatuvchi (tavsiya etiladi, kross‑platforma)
- OS‑ga xos qo‘lda servis sozlamalari (ilg‘or)

Eng tez yo‘l — “Tez start”. Batafsil boshqaruv uchun universal o‘rnatuvchi yoki qo‘lda o‘rnatishdan foydalaning.

---

## Tez start (bitta buyruq)

Foydalanuvchi darajasida o‘rnatadi, virtual muhit yaratadi, dastlabki sozlashni bajaradi va servisni avtomatik ishga tushiradi.

```bash
python3 scripts/bootstrap.py
```

Tugagach:

- macOS/Linux: dastur `~/.yaxshilink` ichida
- Windows: dastur `%LOCALAPPDATA%\yaxshilink` ichida
- Servis ishga tushgan bo‘ladi va login paytida avtomatik boshlanadi.

---

## 1) Universal o‘rnatuvchi (barcha OS, foydalanuvchi uchun)

O‘rnatuvchi ilovani foydalanuvchi katalogiga ko‘chiradi, virtual muhit yaratadi, foydalanuvchi darajasidagi fon servisni ro‘yxatdan o‘tkazadi va to‘liq o‘chirish uchun manifest yozadi.

O‘rnatish:

```bash
python3 ./scripts/installer.py install
```

O‘chirish:

```bash
python3 ./scripts/installer.py uninstall
```

Eslatmalar:

- Standart o‘rnatish katalogi:
  - macOS/Linux: `~/.yaxshilink`
  - Windows: `%LOCALAPPDATA%\yaxshilink`
- O‘rnatuvchi foydalanuvchi servisini ro‘yxatdan o‘tkazadi va “osilib qolish”ni oldini olish uchun bloklanmaydigan dastlabki sozlashni bajaradi:
  - Linux: systemd (foydalanuvchi servisi)
  - macOS: launchd (LaunchAgent)
  - Windows: Scheduled Task (foydalanuvchi loginda)
- Birinchi sozlash — ikki qisqa qadam (har biri darhol tugaydi):

```bash
# 1) Server parametrlarini saqlash (bloklanmaydi)
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --configure-only   # macOS/Linux
# 2) Qurilma portlarini tanlash va saqlash (bloklanmaydi)
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --device-setup-only
```

Windows misoli:

```powershell
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --configure-only
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --device-setup-only
```

Yangilash (ustiga o‘rnatish):

```bash
python3 ./scripts/installer.py install
```

Maxsus katalogga o‘rnatish:

```bash
python3 ./scripts/installer.py install --dir /yo‘l/kat
python3 ./scripts/installer.py uninstall --dir /yo‘l/kat
```

---

## 2) Qo‘lda bir martalik sozlash (alternativa)

```bash
# Venv yaratish va kutubxonalarni o‘rnatish
./scripts/setup_venv.sh

# Dastlabki sozlamalarni kiritish (WS_URL, FANDOMAT_ID, DEVICE_TOKEN) va saqlash (bloklanmaydi)
./.venv/bin/python ./main.py --configure-only

# Qurilma portlarini tanlash va saqlash (bloklanmaydi)
./.venv/bin/python ./main.py --device-setup-only

# Yoki barchasini bitta interaktiv sessiyada (keyin uzoq jarayon ishga tushadi)
./.venv/bin/python ./main.py --setup
```

Birinchi sozlashdan so‘ng saqlanadi:

- WS_URL, FANDOMAT_ID, DEVICE_TOKEN
- SCANNER_PORT, ARDUINO_PORT
- BAUDRATE_SCANNER, BAUDRATE_ARDUINO

Keyingi ishga tushirishlarda `--setup` bermasangiz, savollar takrorlanmaydi.

---

## 3) Linux (systemd) — qo‘lda o‘rnatish

`scripts/systemd/yaxshilink-fandomat.service` faylidagi yo‘llarni loyihangizga moslang. Keyin:

```bash
sudo cp scripts/systemd/yaxshilink-fandomat.service /etc/systemd/system/yaxshilink-fandomat.service
sudo systemctl daemon-reload
sudo systemctl enable --now yaxshilink-fandomat.service
sudo systemctl status yaxshilink-fandomat.service
journalctl -u yaxshilink-fandomat -f
```

Maslahat: root’siz foydalanuvchi servisidan foydalanish uchun `~/.config/systemd/user/` va `systemctl --user`:

```bash
systemctl --user start yaxshilink-fandomat.service
systemctl --user stop yaxshilink-fandomat.service
systemctl --user restart yaxshilink-fandomat.service
systemctl --user status yaxshilink-fandomat.service
journalctl --user-unit=yaxshilink-fandomat -f
```

Login sessiyasiz 24/7 uchun:

```bash
loginctl enable-linger "$USER"
```

---

## 4) macOS (launchd) — qo‘lda o‘rnatish

```bash
mkdir -p ./logs
cp scripts/launchd/com.yaxshi.fandomat.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
launchctl start com.yaxshi.fandomat
launchctl list | grep com.yaxshi.fandomat
# Loglar
tail -f ./logs/launchd.out.log ./logs/launchd.err.log
```

Plist o‘zgarganda:

```bash
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist || true
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
```

---

## 5) Windows (Scheduled Task) — qo‘lda o‘rnatish

PowerShell’da (Administrator) ishga tushiring:

```powershell
scripts\windows\register_task.ps1 -ProjectDir "C:\\path\\to\\yaxshilink" -PythonExe "C:\\path\\to\\yaxshilink\\.venv\\Scripts\\python.exe"
```

Boshqarish:

```powershell
schtasks /Run /TN YaxshiLinkFandomat
schtasks /End /TN YaxshiLinkFandomat
schtasks /Query /TN YaxshiLinkFandomat
```

Qo‘lda ishga tushirganda loglarni ko‘rish uchun chiqishni faylga yo‘naltiring yoki ilovaning fayl loglaridan foydalaning.

---

## 6) Ekspluatatsiya

- Qo‘lda ishga tushirish (birinchi sozlashdan so‘ng savolsiz):

```bash
./.venv/bin/python ./main.py --no-config-prompt
```

- Qayta sozlashni majburlash:

```bash
./.venv/bin/python ./main.py --setup
```

- Portlarni ko‘rish:

```bash
./.venv/bin/python ./main.py --list-ports
```

### Global CLI (yaxshilink)

O‘rnatuvchi istalgan joydan boshqarish uchun buyruq qo‘shadi. O‘rnatilgandan keyin yangi terminal oching (PATH yangilanishi uchun).

Ko‘p ishlatiladigan buyruqlar:

```bash
yaxshilink status        # Servis holati
yaxshilink start         # Servisni ishga tushirish
yaxshilink stop          # Servisni to‘xtatish
yaxshilink restart       # Servisni qayta ishga tushirish

yaxshilink monitor       # Interaktiv monitorni ochish (o‘rnatilgan ilovaga yo‘naltirilgan)

yaxshilink setup         # Bir martalik ikki bosqichli sozlash (credentials + qurilma portlari)
yaxshilink configure     # Faqat WS_URL / FANDOMAT_ID / DEVICE_TOKEN
yaxshilink device-setup  # Faqat skaner/Arduino portlari

yaxshilink uninstall     # Servisni bekor qilish va o‘rnatishni o‘chirish
yaxshilink where         # O‘rnatish yo‘li (masalan, ~/.yaxshilink)
```

Agar buyruq topilmasa, ~/.local/bin ni PATH ga qo‘shing (Unix):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## OS bo‘yicha eslatmalar va nosozliklarni tuzatish

### Linux

- Serial ruxsatlar: foydalanuvchi `dialout` (yoki `uucp`/`plugdev`) guruhida bo‘lishi kerak

```bash
sudo usermod -a -G dialout "$USER" && newgrp dialout
```

### macOS

- LaunchAgent `~/Library/LaunchAgents` ichida; universal o‘rnatuvchi bilan loglar `~/.yaxshilink/logs/` ichida
- Plist o‘zgarganda unload/load qiling (yuqoridagi buyruqlar)

### Windows

- O‘rnatuvchi `run.cmd` ni yaratadi — vazifa to‘g‘ri ishchi katalogdan ishga tushishi uchun ( `config.json` topilishi uchun )
- Vazifa sozlamalarini o‘zgartirish kerak bo‘lsa, o‘chirib qayta o‘rnating yoki `schtasks /Change` dan foydalaning

Agar ilova ishlamayotgandek tuyulsa, foregraundda ishga tushirib diagnostika qiling:

```powershell
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --no-config-prompt
```

---

## Eslatmalar

- Ilova WebSocket va serial qurilmalarga avtomatik qayta ulanadi
- 90 soniya harakatsizlikdan so‘ng sessiya avtomatik tugaydi va Arduino Idle (E)
- Muhit o‘zgaruvchilari orqali sozlash mumkin (WS_URL, FANDOMAT_ID, DEVICE_TOKEN) yoki `config.json` ni tahrirlang
- Serial portlarga ruxsat borligiga ishonch hosil qiling (Linux’da `dialout` guruhi)

### Loglar

Har bir komponent uchun aylanadigan loglar (2MB × 5) va umumiy tizim logi yoziladi:

- system.log — umumiy xabarlar
- scanner.log — skaner kirishlari va hodisalar
- arduino.log — Arduino I/O va yuborilgan buyruqlar
- websocket.log — WS ulanishi, jo‘natish/qabul qilish
- session.log — sessiya hayotiy sikli (start, bekor qilish, timeout, qabul/rad etish)

Joylashuv:

- Universal o‘rnatuvchi bilan: `~/.yaxshilink/logs/` (macOS/Linux), `%LOCALAPPDATA%\yaxshilink\logs/` (Windows)
- Qo‘lda ishga tushirish: `./logs/`
- O‘zgartirish: `YAXSHILINK_LOG_DIR` muhit o‘zgaruvchisi

---

## Monitor (interaktiv)

Qurilmalar, sessiya, WS, OS metrikalari va navbatlar holatini ko‘rsatuvchi interaktiv monitorni oching:

```bash
python3 scripts/monitor.py
```

Agar universal o‘rnatuvchi bilan o‘rnatilgan bo‘lsa va aniq papkani ko‘rsatish kerak bo‘lsa:

```bash
python3 scripts/monitor.py --dir ~/.yaxshilink/app   # macOS/Linux
```

Windows’da `%LOCALAPPDATA%\yaxshilink\app` ostidagi yo‘lni bering.

---

## Konfiguratsiya ma’lumotnomasi

Fayl: `config.json` (ilovaning ishchi katalogida; universal o‘rnatuvchi bilan `app/` ichida)

- WS_URL: WebSocket manzili, masalan `wss://api.yaxshi.link/ws/fandomats`
- FANDOMAT_ID: qurilma ID (butun son)
- DEVICE_TOKEN: kirish tokeni
- SCANNER_PORT: skaner porti (masalan, `/dev/ttyACM0`, `/dev/cu.usbmodem...`, `COM3`)
- ARDUINO_PORT: Arduino porti
- BAUDRATE_SCANNER: skaner tezligi (standart 9600)
- BAUDRATE_ARDUINO: Arduino tezligi (standart 9600)

> Eslatma: `config.json` ni ilova to‘xtatilgan holatda tahrirlang, so‘ng servisni qayta ishga tushiring.

### CLI bayroqlar (`main.py`)

- `--scanner-port`, `--arduino-port`: qurilma portlarini belgilash (shu ishga tushirishda config’ni bosib yozadi)
- `--baudrate`, `--baudrate-scanner`, `--baudrate-arduino`: tezliklarni belgilash
- `--list-ports`: portlarni ko‘rsatish va chiqish
- `--raw`: baytlarni dekodsiz chiqarish
- `--reconnect-delay`: uzilishdan keyin kutish (sekund; standart 2.0)
- `--newline`: `\n`, `\r\n` yoki bo‘sh — satrlar qanday chiqariladi
- `--no-config-prompt`: ishga tushishda WS savollarini bermaslik
- `--configure-only`: WS sozlamalarini so‘rash, `config.json` ga saqlash va chiqish
- `--setup`: interaktiv sozlash (WS + qurilma portlari), hatto config bo‘lsa ham
- `--device-setup-only`: faqat qurilma port/baud savollari, saqlash va chiqish (bloklanmaydi)

---

## Tarmoq talablari

- `WS_URL` ko‘rsatilgan xostga tashqi chiqish (wss/ws) ruxsat etilgan bo‘lishi kerak
- Firewall/proksi ortida bo‘lsangiz, xost/port va WebSocket upgrade’ga ruxsat bering

---

## Dastur yangilash

Universal o‘rnatuvchi orqali:

```bash
python3 scripts/installer.py install
```

Qo‘lda (repo):

```bash
./scripts/setup_venv.sh
./.venv/bin/python ./main.py --no-config-prompt
```

---

## O‘chirish

Universal o‘rnatuvchi:

```bash
python3 scripts/installer.py uninstall
```

Qo‘lda:

- Servisni to‘xtating (OS bo‘limlariga qarang), so‘ng o‘rnatilgan fayllarni o‘chiring.

---

## Tezkor nosozliklar ro‘yxati

- Port topilmadi:
  - `--list-ports` bilan ishga tushiring va qurilma nomini tekshiring
  - Ruxsatlar (Linux: `dialout` guruhi), kabel va drayverlarni tekshiring
- Portda "Permission denied" (Linux):
  - `dialout` (yoki `uucp`/`plugdev`) guruhiga qo‘shing va qayta login qiling yoki `newgrp` ishlating
- WS ulanmayapti:
  - `WS_URL`, internet aloqasi va firewall/proksi qoidalarini tekshiring
- Skaner o‘qiydi, ammo server javob bermaydi:
  - Sessiya serverdan boshlanganiga ishonch hosil qiling; ilova faqat faol sessiyada tekshiradi
- Keraksiz belgilar/yo‘qolishlar:
  - Tezlik mos emas; to‘g‘ri `--baudrate-scanner` ni bering
- Sessiya kutilmaganda tugadi:
  - 90 soniya faol emaslikdan so‘ng sessiya avtomatik yakunlanadi
````
