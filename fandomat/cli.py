from __future__ import annotations

import argparse


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fandomat device runtime")
    parser.add_argument(
        "--port",
        default=None,
        help="Legacy: single serial port (treated as scanner port if provided)",
    )
    parser.add_argument(
        "--scanner-port",
        dest="scanner_port",
        default=None,
        help="Scanner serial device path (if omitted, you will be prompted)",
    )
    parser.add_argument(
        "--arduino-port",
        dest="arduino_port",
        default=None,
        help="Arduino serial device path (if omitted, you will be prompted)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="Default baud rate for both ports",
    )
    parser.add_argument(
        "--baudrate-scanner",
        dest="baudrate_scanner",
        type=int,
        default=None,
        help="Baud rate for scanner (defaults to --baudrate)",
    )
    parser.add_argument(
        "--baudrate-arduino",
        dest="baudrate_arduino",
        type=int,
        default=None,
        help="Baud rate for Arduino (defaults to --baudrate)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print raw bytes repr instead of decoding",
    )
    parser.add_argument(
        "--reconnect-delay",
        type=float,
        default=2.0,
        help="Delay seconds before reconnect on failure",
    )
    parser.add_argument(
        "--newline",
        choices=["\\n", "\\r\\n", ""],
        default="\n",
        help="Newline to display after each decoded line",
    )
    parser.add_argument(
        "--list-ports",
        action="store_true",
        help="List available serial ports and exit",
    )
    parser.add_argument(
        "--no-config-prompt",
        action="store_true",
        help="Do not ask for WS_URL/FANDOMAT_ID/DEVICE_TOKEN on startup",
    )
    parser.add_argument(
        "--configure-only",
        action="store_true",
        help="Prompt for WS settings, save to config.json, then exit",
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Force setup prompts even if config.json already exists",
    )
    parser.add_argument(
        "--device-setup-only",
        action="store_true",
        help="Prompt for device ports (and save) then exit without starting the runtime",
    )
    return parser.parse_args(argv)
