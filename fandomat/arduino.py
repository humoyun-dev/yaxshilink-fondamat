from __future__ import annotations

import time
from .state import print_lock, arduino_cmd_queue
from .serial_utils import open_serial
import logging

log = logging.getLogger("fandomat.arduino")


def arduino_worker(port: str, baudrate: int, reconnect_delay: float, newline: str, stop_event) -> None:
    """Dedicated Arduino worker: reads lines and sends queued commands."""
    ser = None
    while not stop_event.is_set():
        try:
            if ser is None or not ser.is_open:
                log.info(f"Connecting to {port} @ {baudrate}…")
                ser = open_serial(port, baudrate, timeout=1.0)
                log.info("Connected. Waiting for data…")

            # Write pending commands
            wrote = False
            while True:
                try:
                    cmd = arduino_cmd_queue.get_nowait()
                except Exception:
                    break
                try:
                    payload = (cmd + "\n").encode()
                    ser.write(payload)
                    wrote = True
                    log.info(f"<- {cmd}")
                except Exception as e:
                    log.error(f"writer error: {e}")
                    break

            # Read line if available
            try:
                line: bytes = ser.readline()
            except Exception as e:
                log.error(f"read error: {e}")
                line = b""

            if line:
                text = line.decode("utf-8", errors="ignore").strip("\r\n")
                log.info(text)
            elif not wrote:
                time.sleep(0.01)

        except Exception as e:
            log.error(f"Serial error: {e}")
            if ser is not None:
                try:
                    ser.close()
                except Exception:
                    pass
                ser = None
            if not stop_event.is_set():
                time.sleep(reconnect_delay)

    try:
        if ser is not None and ser.is_open:
            ser.close()
    except Exception:
        pass
    log.info("Stopped.")


def send_arduino(cmd: str) -> None:
    if not cmd:
        return
    arduino_cmd_queue.put(cmd)
