from __future__ import annotations

import time
from typing import Optional

from . import state
import logging

log = logging.getLogger("fandomat.scanner")
from .serial_utils import open_serial


def read_worker(port: str, baudrate: int, raw: bool, reconnect_delay: float, newline: str, stop_event) -> None:
    """Scanner reader thread: prints lines and enqueues CHECK_BOTTLE during active session."""
    ser = None
    while not stop_event.is_set():
        try:
            if ser is None or not ser.is_open:
                log.info(f"Connecting to {port} @ {baudrate}…")
                ser = open_serial(port, baudrate, timeout=1.0)
                log.info("Connected. Waiting for data…")
                with state.state_lock:
                    state.scanner_connected = True

            line: bytes = ser.readline()
            if not line:
                continue

            if raw:
                log.info(repr(line))
            else:
                text = line.decode("utf-8", errors="ignore").strip("\r\n")
                log.info(text)
                with state.state_lock:
                    state.last_scanner_line = text
                if text:
                    with state.state_lock:
                        active = state.session_active
                        sid = state.current_session_id
                    if active and sid:
                        state.outbox.put({
                            "type": "CHECK_BOTTLE",
                            "session_id": sid,
                            "sku": text,
                        })
                        log.debug(f"Queued CHECK_BOTTLE sku={text}")

        except Exception as e:
            log.error(f"Serial error: {e}")
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None
            with state.state_lock:
                state.scanner_connected = False
            if not stop_event.is_set():
                time.sleep(reconnect_delay)

    try:
        if ser is not None and ser.is_open:
            ser.close()
    except Exception:
        pass
    with state.state_lock:
        state.scanner_connected = False
    log.info("Stopped.")
