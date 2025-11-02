from __future__ import annotations

import asyncio
import contextlib
import datetime as _dt
import json

import websockets
import logging

from . import state
from .config import load_existing_config, DEFAULT_WS_URL, DEFAULT_FANDOMAT_ID, DEFAULT_DEVICE_TOKEN
from .arduino import send_arduino

log_ws = logging.getLogger("fandomat.websocket")
log_session = logging.getLogger("fandomat.session")


async def _ws_sender(ws):
    while True:
        try:
            msg = state.outbox.get_nowait()
        except Exception:
            await asyncio.sleep(0.05)
            continue
        try:
            await ws.send(json.dumps(msg))
            with state.print_lock:
                print(f"[WS->] {msg}")
        except Exception as e:
            with state.print_lock:
                print(f"[WS sender] send error: {e}")
            await asyncio.sleep(0.2)


def _gen_bottle_code(fandomat_id: int) -> str:
    # local import to modify global in state safely
    with state.state_lock:
        state.bottle_counter += 1
        cnt = state.bottle_counter
    return f"BTL-{fandomat_id:03d}-{cnt:05d}"


async def _ws_run_forever(stop_event):
    cfg = load_existing_config()
    ws_url = cfg.get("WS_URL", DEFAULT_WS_URL)
    fandomat_id = int(cfg.get("FANDOMAT_ID", DEFAULT_FANDOMAT_ID))
    device_token = cfg.get("DEVICE_TOKEN", DEFAULT_DEVICE_TOKEN)
    version = "1.0.0"
    SESSION_TIMEOUT_SECONDS = 90
    session_timeout_task = None
    last_server_msg_at = _dt.datetime.utcnow()

    while not stop_event.is_set():
        try:
            log_ws.info(f"Connecting to {ws_url} …")
            async with websockets.connect(ws_url) as ws:
                log_ws.info("Connected")
                with state.state_lock:
                    state.ws_connected = True

                hello = {
                    "type": "HELLO",
                    "fandomat_id": fandomat_id,
                    "device_token": device_token,
                    "version": version,
                }
                await ws.send(json.dumps(hello))
                log_ws.info(f"-> {hello}")

                sender_task = asyncio.create_task(_ws_sender(ws))
                try:
                    async for raw in ws:
                        # Any server message counts as activity (resets session inactivity timer)
                        last_server_msg_at = _dt.datetime.utcnow()
                        with state.state_lock:
                            state.last_server_msg_ts = last_server_msg_at.timestamp()
                        try:
                            data = json.loads(raw)
                        except Exception:
                            log_ws.warning(f"<- non-JSON: {raw!r}")
                            continue

                        mtype = data.get("type")
                        log_ws.info(f"<- {data}")
                        with state.state_lock:
                            state.last_ws_event = data.get("type")

                        if mtype == "OK":
                            pass
                        elif mtype == "ERROR":
                            log_ws.error(f"ERROR: {data.get('error')}")
                        elif mtype == "PING":
                            await ws.send(json.dumps({"type": "PONG"}))
                            log_ws.debug("-> {'type': 'PONG'}")
                        elif mtype == "START_SESSION":
                            sid = data.get("session_id")
                            with state.state_lock:
                                state.current_session_id = sid
                                state.session_active = True
                            log_session.info(f"started {sid}")
                            state.outbox.put({"type": "SESSION_STARTED", "session_id": sid})
                            send_arduino("S")
                            # Start/Restart session timeout watcher
                            if session_timeout_task and not session_timeout_task.done():
                                session_timeout_task.cancel()
                            async def _watch_timeout(expected_sid: str):
                                nonlocal last_server_msg_at
                                while True:
                                    await asyncio.sleep(1)
                                    now = _dt.datetime.utcnow()
                                    if (now - last_server_msg_at).total_seconds() >= SESSION_TIMEOUT_SECONDS:
                                        with state.state_lock:
                                            if state.session_active and state.current_session_id == expected_sid:
                                                state.session_active = False
                                                ended_sid = state.current_session_id
                                                state.current_session_id = None
                                            else:
                                                ended_sid = None
                                        if ended_sid:
                                            log_session.warning(f"timeout after {SESSION_TIMEOUT_SECONDS}s, ending {ended_sid}")
                                            state.outbox.put({"type": "SESSION_END", "session_id": ended_sid})
                                            send_arduino("E")
                                        return
                            session_timeout_task = asyncio.create_task(_watch_timeout(sid))
                        elif mtype == "CANCEL_SESSION":
                            sid = data.get("session_id")
                            with state.state_lock:
                                if state.current_session_id == sid:
                                    state.session_active = False
                                    state.current_session_id = None
                            log_session.info(f"cancelled {sid}")
                            send_arduino("E")
                            if session_timeout_task and not session_timeout_task.done():
                                session_timeout_task.cancel()
                        elif mtype == "BOTTLE_CHECK_RESULT":
                            sid = data.get("session_id")
                            exists = data.get("exist", False)
                            with state.state_lock:
                                active = state.session_active and state.current_session_id == sid
                            if not active:
                                continue
                            if exists:
                                bottle = data.get("bottle", {})
                                material = bottle.get("material", "plastic")
                                if material.lower() == "plastic":
                                    send_arduino("P")
                                elif material.lower() == "aluminum":
                                    send_arduino("A")
                                else:
                                    send_arduino("R")
                                state.outbox.put({
                                    "type": "BOTTLE_ACCEPTED",
                                    "session_id": sid,
                                    "code": _gen_bottle_code(fandomat_id),
                                    "material": material,
                                    "timestamp": _dt.datetime.utcnow().isoformat() + "Z",
                                })
                            else:
                                log_session.info("bottle not found, rejected")
                                send_arduino("R")
                        else:
                            pass
                finally:
                    sender_task.cancel()
                    with contextlib.suppress(Exception):
                        await sender_task
                    if session_timeout_task and not session_timeout_task.done():
                        session_timeout_task.cancel()
        except Exception as e:
            log_ws.error(f"disconnected/error: {e}")
            with state.state_lock:
                state.ws_connected = False
        if not stop_event.is_set():
            await asyncio.sleep(5)


def ws_thread_runner(stop_event) -> None:
    try:
        asyncio.run(_ws_run_forever(stop_event))
    except Exception as e:
        log_ws.critical(f"thread crashed: {e}")
