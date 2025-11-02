from __future__ import annotations

import threading
import queue
from typing import Optional
import time

# Cross-module synchronization and shared runtime state
print_lock = threading.Lock()
state_lock = threading.Lock()

session_active: bool = False
current_session_id: Optional[str] = None
bottle_counter: int = 0

# Connectivity/status flags and last-seen data
scanner_connected: bool = False
arduino_connected: bool = False
ws_connected: bool = False

last_scanner_line: Optional[str] = None
last_arduino_line: Optional[str] = None
last_ws_event: Optional[str] = None

# Timestamps
start_time: float = time.time()
last_server_msg_ts: Optional[float] = None

# Queues
outbox: "queue.Queue[dict]" = queue.Queue()
arduino_cmd_queue: "queue.Queue[str]" = queue.Queue()

# Stop flag for WebSocket thread
ws_stop_event = threading.Event()
