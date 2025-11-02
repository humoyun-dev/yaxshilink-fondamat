#!/usr/bin/env python3
from __future__ import annotations

import signal
import threading
from typing import Optional

from fandomat.cli import parse_args
from fandomat.serial_utils import list_ports, choose_port_interactive
from fandomat.config import ensure_server_config, ensure_server_config_interactive, load_existing_config, update_config
from fandomat.scanner import read_worker as scanner_read_worker
from fandomat.arduino import arduino_worker
from fandomat.ws_client import ws_thread_runner
from fandomat import state
from fandomat.logging_setup import setup_logging
from fandomat.status import status_writer
import logging


def main(argv: Optional[list[str]] = None) -> int:
    # Initialize logging ASAP
    logs_dir = setup_logging()
    log = logging.getLogger("fandomat")
    log.info(f"Starting Fandomat runtime. Logs at: {logs_dir}")
    args = parse_args(argv)

    if args.list_ports:
        list_ports()
        return 0

    # Configuration handling:
    # - --configure-only: always prompt and exit
    # - Else: ensure config exists; prompt only if first run or --setup
    # If running in non-interactive mode but config is missing, fail fast with guidance
    existing_cfg = load_existing_config()
    has_ws_cfg = bool(existing_cfg.get("WS_URL") and existing_cfg.get("FANDOMAT_ID") is not None and existing_cfg.get("DEVICE_TOKEN"))

    if args.configure_only:
        ensure_server_config_interactive()
        log.info("Configuration saved. Exiting as requested by --configure-only.")
        return 0
    else:
        # --setup forces prompt; otherwise only prompt on first run
        if args.no_config_prompt and not has_ws_cfg:
            log.error("Missing WS configuration and --no-config-prompt was provided. Run once with --configure-only to save WS_URL, FANDOMAT_ID, and DEVICE_TOKEN.")
            return 1
        if not args.no_config_prompt:
            ensure_server_config(setup=args.setup)

    # Load existing config to reuse saved device ports/baudrates
    cfg = load_existing_config()

    # Resolve scanner/arduino ports with precedence: CLI > saved config > interactive (if setup or missing)
    scanner_port = args.scanner_port or (args.port if args.port else None) or cfg.get("SCANNER_PORT")
    arduino_port = args.arduino_port or cfg.get("ARDUINO_PORT")

    # If --setup is provided, force re-prompt for device ports
    if args.setup or args.device_setup_only or not scanner_port:
        scanner_port = choose_port_interactive("Select SCANNER serial port:")
        if not scanner_port:
            log.error("No scanner port selected. Exiting.")
            return 1
        # Persist chosen scanner port
        cfg = update_config({"SCANNER_PORT": scanner_port})

    if args.setup or args.device_setup_only or not arduino_port:
        arduino_port = choose_port_interactive("Select ARDUINO serial port:")
        if not arduino_port:
            log.error("No arduino port selected. Exiting.")
            return 1
        # Persist chosen arduino port
        cfg = update_config({"ARDUINO_PORT": arduino_port})

    nl_map = {"\n": "\n", "\r\n": "\r\n", "": ""}
    newline = nl_map.get(args.newline, "\n")

    # Resolve baud rates: CLI > saved config > default
    baud_scanner = (args.baudrate_scanner if args.baudrate_scanner is not None else cfg.get("BAUDRATE_SCANNER")) or args.baudrate
    baud_arduino = (args.baudrate_arduino if args.baudrate_arduino is not None else cfg.get("BAUDRATE_ARDUINO")) or args.baudrate

    # If user forced setup or baudrates missing from config (and not set via CLI), persist them
    to_save = {}
    if args.setup or "BAUDRATE_SCANNER" not in cfg:
        to_save["BAUDRATE_SCANNER"] = int(baud_scanner)
    if args.setup or "BAUDRATE_ARDUINO" not in cfg:
        to_save["BAUDRATE_ARDUINO"] = int(baud_arduino)
    if to_save:
        update_config(to_save)

    # Device setup only: exit here without starting threads
    if args.device_setup_only:
        log.info("Device ports saved. Exiting as requested by --device-setup-only.")
        return 0

    stop_event = threading.Event()

    threads = [
        threading.Thread(target=scanner_read_worker, args=(scanner_port, baud_scanner, args.raw, args.reconnect_delay, newline, stop_event), daemon=True),
        threading.Thread(target=arduino_worker, args=(arduino_port, baud_arduino, args.reconnect_delay, newline, stop_event), daemon=True),
    ]
    # status writer thread (writes status.json next to config.json)
    threads.append(threading.Thread(target=status_writer, args=(stop_event,), daemon=True))

    ws_thread = threading.Thread(target=ws_thread_runner, args=(state.ws_stop_event,), daemon=True)
    ws_thread.start()

    for t in threads:
        t.start()

    def handle_sig(signum, frame):
        log.info(f"Signal {signum} received. Shutting down…")
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    try:
        while any(t.is_alive() for t in threads):
            for t in threads:
                t.join(timeout=0.2)
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt — stopping threads…")
        stop_event.set()
        for t in threads:
            t.join()
        state.ws_stop_event.set()
        ws_thread.join(timeout=2)
    log.info("Exited cleanly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

