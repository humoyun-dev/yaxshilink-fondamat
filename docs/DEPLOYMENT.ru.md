# YaxshiLink Fandomat — Развёртывание 24/7 (Русский)

Это русская версия руководства по установке и запуску. Полную англоязычную версию см. в `docs/DEPLOYMENT.md`.

---

## Монитор (интерактивный)

Открыть интерактивный монитор статуса:

```bash
python3 scripts/monitor.py
```

Если приложение установлено через универсальный инсталлятор и нужно указать каталог установки явно:

```bash
python3 scripts/monitor.py --dir ~/.yaxshilink/app
```

---

## Быстрый старт (одна команда)

Установит приложение для текущего пользователя, создаст виртуальное окружение, задаст вопросы настройки и запустит сервис:

```bash
python3 scripts/bootstrap.py
```

После завершения:

- macOS/Linux: приложение в `~/.yaxshilink`

````markdown
# YaxshiLink Fandomat — Развёртывание 24/7 (Русский)

Это полное руководство по установке и эксплуатации рантайма Fandomat. Доступны два пути:

- Универсальный установщик для пользователя (рекомендуется, кросс‑платформенный)
- Ручная OS‑специфичная настройка сервисов (продвинутый вариант)

Для самого быстрого старта используйте раздел «Быстрый старт». Для тонкого контроля — универсальный установщик или ручную установку.

---

## Быстрый старт (одна команда)

Установит приложение для текущего пользователя, создаст виртуальное окружение, выполнит первичную настройку и запустит сервис автоматически.

```bash
python3 scripts/bootstrap.py
```

После завершения:

- macOS/Linux: приложение расположено в `~/.yaxshilink`
- Windows: приложение расположено в `%LOCALAPPDATA%\yaxshilink`
- Сервис уже работает и будет автоматически запускаться при входе в систему.

---

## 1) Универсальный установщик (все ОС, пользовательский)

Установщик копирует приложение в стандартный каталог пользователя, создаёт виртуальное окружение, регистрирует пользовательский фоновый сервис и формирует манифест для последующего полного удаления.

Установка:

```bash
python3 ./scripts/installer.py install
```

Удаление:

```bash
python3 ./scripts/installer.py uninstall
```

Примечания:

- Каталог установки по умолчанию:
  - macOS/Linux: `~/.yaxshilink`
  - Windows: `%LOCALAPPDATA%\yaxshilink`
- Установщик регистрирует пользовательский сервис и выполняет неблокирующую первичную настройку, чтобы исключить «зависание»:
  - Linux: пользовательский сервис systemd
  - macOS: LaunchAgent (launchd)
  - Windows: Планировщик заданий (Scheduled Task)
- Первичная конфигурация: после установки выполните двухшаговую короткую настройку (каждая команда завершается сразу, не запускает длительный процесс):

```bash
# 1) Сохранить параметры сервера (неблокирующе)
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --configure-only   # macOS/Linux
# 2) Выбрать и сохранить порты устройств (неблокирующе)
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --device-setup-only
```

В Windows используйте эквивалентные пути:

```powershell
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --configure-only
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --device-setup-only
```

Обновление (поверх существующей установки):

```bash
python3 ./scripts/installer.py install
```

Пользовательский каталог можно переопределить:

```bash
python3 ./scripts/installer.py install --dir /путь/к/каталогу
python3 ./scripts/installer.py uninstall --dir /путь/к/каталогу
```

---

## 2) Одноразовая настройка вручную (альтернатива)

```bash
# Создать venv и установить зависимости
./scripts/setup_venv.sh

# Ввести начальные параметры (WS_URL, FANDOMAT_ID, DEVICE_TOKEN) и сохранить (неблокирующе)
./.venv/bin/python ./main.py --configure-only

# Выбрать и сохранить порты устройств без запуска длительного процесса (неблокирующе)
./.venv/bin/python ./main.py --device-setup-only

# Либо выполнить всё в одной интерактивной сессии (после сохранения запустится длительный процесс)
./.venv/bin/python ./main.py --setup
```

После первой успешной настройки приложение сохраняет:

- WS_URL, FANDOMAT_ID, DEVICE_TOKEN
- SCANNER_PORT, ARDUINO_PORT
- BAUDRATE_SCANNER, BAUDRATE_ARDUINO

Повторные запуски не будут спрашивать параметры, если явно не передать `--setup`.

---

## 3) Linux (systemd) — ручная установка

Отредактируйте пути в `scripts/systemd/yaxshilink-fandomat.service` под ваш проект/venv. Затем:

```bash
# Копируем в systemd
sudo cp scripts/systemd/yaxshilink-fandomat.service /etc/systemd/system/yaxshilink-fandomat.service

# Перечитать и включить
sudo systemctl daemon-reload
sudo systemctl enable --now yaxshilink-fandomat.service

# Проверка статуса
sudo systemctl status yaxshilink-fandomat.service
# Просмотр логов
journalctl -u yaxshilink-fandomat -f
```

Совет: для пользовательских сервисов без root используйте `~/.config/systemd/user/` и `systemctl --user`.

Управление (пользовательский scope):

```bash
systemctl --user start yaxshilink-fandomat.service
systemctl --user stop yaxshilink-fandomat.service
systemctl --user restart yaxshilink-fandomat.service
systemctl --user status yaxshilink-fandomat.service
journalctl --user-unit=yaxshilink-fandomat -f
```

---

## 4) macOS (launchd) — ручная установка

Отредактируйте пути в `scripts/launchd/com.yaxshi.fandomat.plist`. Затем:

```bash
# Создать папку логов, если её нет
mkdir -p ./logs

# Установить как LaunchAgent пользователя
cp scripts/launchd/com.yaxshi.fandomat.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
launchctl start com.yaxshi.fandomat

# Проверить статус
launchctl list | grep com.yaxshi.fandomat
# Хвост логов
tail -f ./logs/launchd.out.log ./logs/launchd.err.log
```

Агент стартует при входе и перезапускается при сбое.

Управление:

```bash
# Остановить
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
# Запустить
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
# (Пере)запустить выполняющуюся задачу
launchctl start com.yaxshi.fandomat
```

---

## 5) Windows (Планировщик задач) — ручная установка

Откройте PowerShell (администратор) и выполните:

```powershell
# Отредактируйте пути через параметры при необходимости
scripts\windows\register_task.ps1 -ProjectDir "C:\\path\\to\\yaxshilink" -PythonExe "C:\\path\\to\\yaxshilink\\.venv\\Scripts\\python.exe"
```

Задача запускается при входе пользователя и перезапускается при сбое.

Управление задачей:

```powershell
# Запустить сейчас
schtasks /Run /TN YaxshiLinkFandomat
# Остановить
schtasks /End /TN YaxshiLinkFandomat
# Просмотреть
schtasks /Query /TN YaxshiLinkFandomat
```

Чтобы увидеть логи при ручном запуске, перенаправьте вывод в файл или используйте файловые логи приложения.

---

## 6) Эксплуатация

- Ручной запуск (без вопросов после первичной настройки):

```bash
./.venv/bin/python ./main.py --no-config-prompt
```

- Принудительная повторная настройка:

```bash
./.venv/bin/python ./main.py --setup
```

- Показать доступные последовательные порты:

```bash
./.venv/bin/python ./main.py --list-ports
```

### Глобальная CLI (yaxshilink)

Установщик добавляет пользовательскую команду для управления сервисом из любой директории. Откройте новый терминал после установки, чтобы PATH обновился.

Часто используемые команды:

```bash
yaxshilink status        # Статус сервиса
yaxshilink start         # Запустить сервис
yaxshilink stop          # Остановить сервис
yaxshilink restart       # Перезапустить сервис

yaxshilink monitor       # Открыть интерактивный монитор (указывает на установленное приложение)

yaxshilink setup         # Разовая двухшаговая настройка (учётные данные + порты устройств)
yaxshilink configure     # Только WS_URL / FANDOMAT_ID / DEVICE_TOKEN
yaxshilink device-setup  # Только выбор портов сканера/Arduino

yaxshilink uninstall     # Снять сервис и удалить установку
yaxshilink where         # Путь установки (например, ~/.yaxshilink)
```

Если команда не находится, добавьте ~/.local/bin в PATH (Unix):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## Особенности ОС и устранение неполадок

### Linux

- Установщик регистрирует пользовательский сервис systemd (без sudo). Он работает, пока вы залогинены. Для работы без активной сессии включите lingering:

```bash
loginctl enable-linger "$USER"
```

- Права на последовательный порт: добавьте пользователя в группу (часто `dialout`, иногда `uucp`/`plugdev`).

```bash
sudo usermod -a -G dialout "$USER" && newgrp dialout
```

### macOS

- LaunchAgent устанавливается в `~/Library/LaunchAgents` и стартует при входе. При установке универсальным установщиком логи находятся в `~/.yaxshilink/logs/`.
- Если меняли plist, разгрузите и загрузите его снова:

```bash
launchctl unload ~/Library/LaunchAgents/com.yaxshi.fandomat.plist || true
launchctl load ~/Library/LaunchAgents/com.yaxshi.fandomat.plist
```

### Windows

- Установщик создаёт `run.cmd` в папке установки, чтобы задача стартовала из правильного каталога (чтобы находился `config.json`).
- Для изменения настроек задачи удалите и переустановите, либо используйте `schtasks /Change`.

Если приложение не видно в логах или не стартует, попробуйте запустить его в форграунде для диагностики:

```powershell
& "$env:LOCALAPPDATA\yaxshilink\.venv\Scripts\python.exe" "$env:LOCALAPPDATA\yaxshilink\app\main.py" --no-config-prompt
```

---

## Примечания

- Приложение автоматически переподключается к WebSocket и последовательным устройствам.
- Сессии автоматически завершаются при неактивности 90 секунд, и Arduino переводится в Idle (E).
- Для конфигурации через окружение можно указать WS_URL, FANDOMAT_ID, DEVICE_TOKEN перед запуском или вручную отредактировать `config.json`.
- Убедитесь, что у пользователя есть доступ к последовательным портам (например, группа `dialout` в Linux).

### Логи

Пишутся вращающиеся логи (2MB × 5 бэкапов) по компонентам и общий системный лог:

- system.log — общие сообщения
- scanner.log — ввод сканера и события
- arduino.log — I/O Arduino и отправленные команды
- websocket.log — подключение WS, отправка/приём
- session.log — жизненный цикл сессий (старт, отмена, таймаут, приём/отказ бутылок)

Расположение:

- Универсальный установщик: `~/.yaxshilink/logs/` (macOS/Linux), `%LOCALAPPDATA%\yaxshilink\logs/` (Windows)
- Ручной запуск: `./logs/`
- Переопределение: переменная окружения `YAXSHILINK_LOG_DIR`.

---

## Монитор (интерактивный)

Откройте интерактивный монитор со статусом устройств, сессии, WS, метриками ОС и очередями:

```bash
python3 scripts/monitor.py
```

Если устанавливали универсальным установщиком и нужно явно указать папку приложения:

```bash
python3 scripts/monitor.py --dir ~/.yaxshilink/app   # macOS/Linux
```

В Windows используйте путь под `%LOCALAPPDATA%\yaxshilink\app`.

---

## Справочник по конфигурации

Файл: `config.json` (создаётся в рабочем каталоге приложения; при универсальной установке — внутри каталога `app/`).

- WS_URL: конечная точка WebSocket, напр. `wss://api.yaxshi.link/ws/fandomats`
- FANDOMAT_ID: целочисленный ID устройства
- DEVICE_TOKEN: токен доступа
- SCANNER_PORT: порт сканера (например, `/dev/ttyACM0`, `/dev/cu.usbmodem...`, `COM3`)
- ARDUINO_PORT: порт Arduino
- BAUDRATE_SCANNER: скорость сканера (по умолчанию 9600)
- BAUDRATE_ARDUINO: скорость Arduino (по умолчанию 9600)

> Совет: редактируйте `config.json`, когда приложение остановлено, затем перезапустите сервис, чтобы применить изменения.

### Флаги CLI (`main.py`)

- `--scanner-port`, `--arduino-port`: задать порты устройств (перекрывают config для текущего запуска)
- `--baudrate`, `--baudrate-scanner`, `--baudrate-arduino`: задать скорости
- `--list-ports`: показать доступные порты и выйти
- `--raw`: печатать «сырые» байты без декодирования
- `--reconnect-delay`: пауза перед повторным подключением (секунды; по умолчанию 2.0)
- `--newline`: `\\n`, `\\r\\n` или пусто — как печатать строки
- `--no-config-prompt`: не спрашивать параметры WS при запуске
- `--configure-only`: спросить параметры WS, сохранить в config.json и выйти
- `--setup`: выполнить интерактивную настройку (WS + порты устройств), даже если конфиг уже есть
- `--device-setup-only`: спросить только порты/baud устройств, сохранить и выйти (неблокирующе)

---

## Сетевые требования

- Исходящий доступ к хосту из `WS_URL` по TLS (wss) или ws.
- При наличии прокси/фаервола — разрешить хост/порт и апгрейд WebSocket.

---

## Обновление приложения

Через универсальный установщик:

```bash
python3 scripts/installer.py install
```

Это заново копирует приложение и переустанавливает зависимости. Перезапустите сервис при необходимости.

Ручной способ (из исходников):

```bash
./scripts/setup_venv.sh
./.venv/bin/python ./main.py --no-config-prompt
```

---

## Удаление

Универсальный установщик:

```bash
python3 scripts/installer.py uninstall
```

Ручное:

- Остановите сервис (см. разделы по ОС), затем удалите установленные файлы.

---

## Чек‑лист по устранению неполадок

- Порт не найден:
  - Запустите с `--list-ports` и проверьте имя устройства.
  - Проверьте права (Linux: группа `dialout`), кабель и драйверы.
- «Permission denied» на порту (Linux):
  - Добавьте пользователя в `dialout` (или `uucp`/`plugdev`) и перелогиньтесь либо используйте `newgrp`.
- Не подключается к WS:
  - Проверьте `WS_URL`, доступ в интернет и правила фаервола/прокси.
- Сканер читает, а сервер не реагирует:
  - Проверьте, что сессия запущена с сервера; приложение проверяет бутылки только в активной сессии.
- Кракозябры/потери при сканировании:
  - Несовпадение скорости; укажите правильный `--baudrate-scanner`.
- Сессия внезапно завершилась:
  - Встроенный таймаут 90 секунд завершает неактивные сессии автоматически.
````
