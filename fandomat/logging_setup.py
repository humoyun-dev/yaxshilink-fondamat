from __future__ import annotations

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def _resolve_logs_dir() -> Path:
    # Priority 1: explicit env var
    env = os.environ.get("YAXSHILINK_LOG_DIR")
    if env:
        p = Path(env).expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return p

    cwd = Path.cwd()
    # If running from installer layout (~/.yaxshilink/app), prefer sibling logs folder
    if cwd.name == "app" and cwd.parent.exists():
        logs = cwd.parent / "logs"
    else:
        logs = cwd / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs


def _rotating_file(path: Path, level: int) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        filename=str(path),
        maxBytes=2 * 1024 * 1024,  # 2MB
        backupCount=5,
        encoding="utf-8",
    )
    handler.setLevel(level)
    fmt = logging.Formatter(fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(fmt)
    return handler


def _console_handler(level: int) -> logging.Handler:
    ch = logging.StreamHandler()
    ch.setLevel(level)
    fmt = logging.Formatter(fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    ch.setFormatter(fmt)
    return ch


def setup_logging(log_dir: Optional[str | Path] = None, console: bool = True, level: int = logging.INFO) -> Path:
    """Configure rotating file logs per component and a general system log.

    Log files created:
      - system.log (root: fandomat)
      - scanner.log (logger: fandomat.scanner)
      - arduino.log (logger: fandomat.arduino)
      - websocket.log (logger: fandomat.websocket)
      - session.log (logger: fandomat.session)

    Returns the Path to the logs directory.
    """
    logs_path = Path(log_dir).expanduser() if log_dir else _resolve_logs_dir()

    # Root logger for general/system
    root = logging.getLogger("fandomat")
    root.setLevel(level)
    root.propagate = False
    # Avoid duplicate handlers if setup_logging is called twice
    if not any(isinstance(h, RotatingFileHandler) and getattr(h, "_yl_tag", None) == "system" for h in root.handlers):
        h_sys = _rotating_file(logs_path / "system.log", level)
        setattr(h_sys, "_yl_tag", "system")
        root.addHandler(h_sys)
    if console and not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(_console_handler(level))

    # Component loggers
    def _attach(name: str, filename: str):
        lg = logging.getLogger(name)
        lg.setLevel(level)
        lg.propagate = False
        if not any(isinstance(h, RotatingFileHandler) and getattr(h, "_yl_tag", None) == name for h in lg.handlers):
            h = _rotating_file(logs_path / filename, level)
            setattr(h, "_yl_tag", name)
            lg.addHandler(h)
        # also forward to root console by adding the root handlers as parents via manual attach
        for h in root.handlers:
            if isinstance(h, logging.StreamHandler) and not any(isinstance(x, logging.StreamHandler) for x in lg.handlers):
                lg.addHandler(_console_handler(level))

    _attach("fandomat.scanner", "scanner.log")
    _attach("fandomat.arduino", "arduino.log")
    _attach("fandomat.websocket", "websocket.log")
    _attach("fandomat.session", "session.log")

    return logs_path
