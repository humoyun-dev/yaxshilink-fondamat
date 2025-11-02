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
- Windows: приложение в `%LOCALAPPDATA%\yaxshilink`
- Сервис запущен и будет стартовать при входе в систему.

---

## Универсальный установщик (все ОС, для пользователя)

- Установка:

```bash
python3 scripts/installer.py install
```

- Удаление:

```bash
python3 scripts/installer.py uninstall
```

- Первичная настройка (сохранит WS_URL, FANDOMAT_ID, DEVICE_TOKEN и порты):

```bash
~/.yaxshilink/.venv/bin/python ~/.yaxshilink/app/main.py --setup   # macOS/Linux
```

На Windows используйте соответствующие пути в `%LOCALAPPDATA%`.

- Обновление (повторная установка поверх):

```bash
python3 scripts/installer.py install
```

---

## Ручная установка (вариант)

```bash
./scripts/setup_venv.sh
./.venv/bin/python ./main.py --configure-only
./.venv/bin/python ./main.py --setup
```

---

## Управление сервисом

- Linux (systemd user):

```bash
systemctl --user status yaxshilink-fandomat.service
journalctl --user-unit=yaxshilink-fandomat -f
```

- macOS (launchd):

```bash
launchctl list | grep com.yaxshi.fandomat
```

- Windows (Планировщик задач):

```powershell
schtasks /Query /TN YaxshiLinkFandomat
```

---

## Журналы (логи)

Приложение пишет вращающиеся логи (2MB × 5):

- system.log — общие сообщения
- scanner.log — сканер штрихкодов
- arduino.log — ввод/вывод Arduino и отправленные команды
- websocket.log — подключение WS, передача и приём
- session.log — сессии (старт/отмена/таймаут/бутылки)

Расположение:

- При установке через инсталлятор: `~/.yaxshilink/logs/` (macOS/Linux) или `%LOCALAPPDATA%\yaxshilink\logs\` (Windows)
- При ручном запуске: `./logs/`
- Переопределение: переменная окружения `YAXSHILINK_LOG_DIR`

---

## Конфигурация

Файл `config.json` (рядом с `main.py` или в `~/.yaxshilink/app/` при установке):

- WS_URL — WebSocket адрес, напр. `wss://api.yaxshi.link/ws/fandomats`
- FANDOMAT_ID — числовой ID устройства
- DEVICE_TOKEN — токен доступа
- SCANNER_PORT / ARDUINO_PORT — последовательные порты
- BAUDRATE_SCANNER / BAUDRATE_ARDUINO — скорости (по умолчанию 9600)

Флаги `main.py` (выборочно): `--list-ports`, `--scanner-port`, `--arduino-port`, `--baudrate[-scanner|-arduino]`, `--setup`.

---

## Вопросы и проблемы (кратко)

- Нет доступа к последовательному порту (Linux): добавьте пользователя в группу `dialout` (`uucp`/`plugdev`).
- Нет связи с сервером (WS): проверьте `WS_URL`, интернет и правила фаервола.
- Неверные символы при сканировании: проверьте скорость порта.
- Сессия завершилась: неактивность 90 секунд завершает сессию автоматически.
