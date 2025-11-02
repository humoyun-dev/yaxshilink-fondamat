from __future__ import annotations

import sys
from typing import Optional


def available_ports():
    try:
        from serial.tools import list_ports
    except Exception as e:
        print(f"Failed to import pyserial for port listing: {e}")
        sys.exit(1)
    return list(list_ports.comports())


def list_ports() -> None:
    ports = available_ports()
    if not ports:
        print("No serial ports found.")
        return
    for idx, p in enumerate(ports):
        print(f"[{idx}] {p.device}\t{p.description}")


def choose_port_interactive(prompt: str = "Select a serial port:") -> Optional[str]:
    while True:
        ports = available_ports()
        if not ports:
            print("No serial ports found. Connect a device and press 'r' to rescan or 'q' to quit.")
        else:
            print(prompt)
            for idx, p in enumerate(ports):
                print(f"  [{idx}] {p.device}\t{p.description}")

        choice = input("Enter number, full device path, 'r' to rescan, or 'q' to quit: ").strip()
        if choice.lower() in {"q", "quit", "exit"}:
            return None
        if choice.lower() in {"r", "rescan", "refresh"}:
            continue
        if choice.isdigit():
            i = int(choice)
            if 0 <= i < len(ports):
                return ports[i].device
            else:
                print("Invalid index. Try again.")
                continue
        if choice:
            return choice
        print("Please enter a valid selection.")


def open_serial(port: str, baudrate: int, timeout: float = 1.0):
    try:
        import serial  # type: ignore
    except Exception as e:
        print(f"pyserial is required to open serial ports: {e}")
        print("Install it with: pip install pyserial")
        sys.exit(1)
    return serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
