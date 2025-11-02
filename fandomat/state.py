from __future__ import annotations

import threading
import queue
from typing import Optional

# Cross-module synchronization and shared runtime state
print_lock = threading.Lock()
state_lock = threading.Lock()

session_active: bool = False
current_session_id: Optional[str] = None
bottle_counter: int = 0

# Queues
outbox: "queue.Queue[dict]" = queue.Queue()
arduino_cmd_queue: "queue.Queue[str]" = queue.Queue()

# Stop flag for WebSocket thread
ws_stop_event = threading.Event()
