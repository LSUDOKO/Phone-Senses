"""Endpoint -> fixed termux-* argv mapping, input validation and execution.

Runs on the phone inside Termux. Standard library only. No shell is ever used:
every endpoint builds a fixed argv list from validated values, and free text
(SMS body, TTS text, clipboard text) is passed on stdin, never as arguments,
so it can never be parsed as a command-line option.

A *runner* executes argv. ``SubprocessRunner`` runs real Termux:API commands;
the mock runner in ``helper.py`` returns fixture output for the same argv, so
validation and argv building are exercised in mock mode too.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import time
from typing import Any, Callable

PHONE_RE = re.compile(r"^\+?[0-9]{6,15}$")
SMS_MAX = 480
SPEAK_MAX = 500
CLIPBOARD_MAX = 4000
NOTIFY_MAX = 300
SMS_BOXES = ("inbox", "sent", "all")
LOCATION_PROVIDERS = ("network", "gps", "passive")
CAMERAS = {"back": "0", "front": "1"}
VOLUME_STREAMS = ("music", "alarm", "notification", "ring")

DEFAULT_TIMEOUT = 15
LOCATION_TIMEOUT = 35
PHOTO_TIMEOUT = 30
PHOTO_MAX_BYTES = 6 * 1024 * 1024


class HelperError(Exception):
    """An error with a stable code from the helper API (see docs/04-architecture.md)."""

    def __init__(self, code: str, message: str = "", status: int = 400):
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.status = status


def bad_request(message: str) -> HelperError:
    return HelperError("bad_request", message, 400)


class SubprocessRunner:
    """Runs a fixed argv with no shell and a timeout; returns stdout text."""

    def run(self, argv: list[str], timeout: float = DEFAULT_TIMEOUT, stdin: str | None = None) -> str:
        try:
            proc = subprocess.run(
                argv, shell=False, capture_output=True, text=True,
                timeout=timeout, input=stdin if stdin is not None else "",
            )
        except FileNotFoundError:
            raise HelperError("termux_api_missing",
                              f"{argv[0]} not found: run 'pkg install termux-api' and install the Termux:API app",
                              503)
        except subprocess.TimeoutExpired:
            raise HelperError("timeout",
                              f"{argv[0]} timed out (a missing Android permission often causes this)", 504)
        out = proc.stdout or ""
        if proc.returncode != 0:
            raise HelperError("internal", f"{argv[0]} exited with {proc.returncode}", 500)
        _raise_if_api_error(argv[0], out)
        return out


def _raise_if_api_error(cmd: str, out: str) -> None:
    """Termux:API reports some failures as JSON {"error": ...} on stdout."""
    text = out.strip()
    if not text.startswith("{") or '"error"' not in text:
        return
    try:
        payload = json.loads(text)
    except ValueError:
        return
    if isinstance(payload, dict) and payload.get("error"):
        msg = str(payload["error"])
        code = "permission_denied" if "permission" in msg.lower() else "internal"
        raise HelperError(code, f"{cmd}: {msg[:200]}", 403 if code == "permission_denied" else 500)


def _json(out: str, default: Any = None) -> Any:
    text = out.strip()
    if not text:
        return default
    try:
        return json.loads(text)
    except ValueError:
        raise HelperError("internal", "unexpected non-JSON output from Termux:API", 500)


# ---------------------------------------------------------------------------
# Validation helpers

def int_param(value: Any, name: str, default: int, lo: int, hi: int) -> int:
    if value is None or value == "":
        return default
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise bad_request(f"{name} must be an integer")
    if not lo <= n <= hi:
        raise bad_request(f"{name} must be between {lo} and {hi}")
    return n


def choice_param(value: Any, name: str, default: str, choices: tuple[str, ...]) -> str:
    if value is None or value == "":
        return default
    value = str(value).lower()
    if value not in choices:
        raise bad_request(f"{name} must be one of {', '.join(choices)}")
    return value


def phone_number(value: Any) -> str:
    number = re.sub(r"[\s\-()]", "", str(value or ""))
    if not PHONE_RE.match(number):
        raise bad_request("to must be a phone number: digits only, optional leading +, 6 to 15 digits")
    return number


def text_param(value: Any, name: str, max_len: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise bad_request(f"{name} must be a non-empty string")
    if len(value) > max_len:
        raise bad_request(f"{name} is too long (max {max_len} characters)")
    if "\x00" in value:
        raise bad_request(f"{name} contains invalid characters")
    return value


# ---------------------------------------------------------------------------
# Endpoints. Each takes (runner, params) and returns JSON-serialisable data.

def ping_info(runner) -> dict:
    try:
        model = runner.run(["getprop", "ro.product.model"], timeout=5).strip()
    except HelperError:
        model = "unknown"
    return {"device_model": model[:80] or "unknown"}


def status(runner, params: dict) -> dict:
    battery = _json(runner.run(["termux-battery-status"]), {}) or {}
    try:
        wifi = _json(runner.run(["termux-wifi-connectioninfo"]), {}) or {}
    except HelperError:
        wifi = {}
    return {
        "battery": {k: battery.get(k) for k in ("percentage", "status", "plugged", "temperature", "health")},
        "wifi": {"ssid": wifi.get("ssid"), "ip": wifi.get("ip"), "rssi": wifi.get("rssi")},
    }


def notifications(runner, params: dict) -> list:
    data = _json(runner.run(["termux-notification-list"]), [])
    return data if isinstance(data, list) else []


def sms_list(runner, params: dict) -> list:
    limit = int_param(params.get("limit"), "limit", 20, 1, 500)
    offset = int_param(params.get("offset"), "offset", 0, 0, 100000)
    box = choice_param(params.get("box"), "box", "inbox", SMS_BOXES)
    argv = ["termux-sms-list", "-l", str(limit), "-o", str(offset), "-t", box]
    if params.get("from"):
        argv += ["-f", phone_number(params.get("from"))]
    data = _json(runner.run(argv), [])
    return data if isinstance(data, list) else []


def sms_send(runner, body: dict) -> dict:
    to = phone_number(body.get("to"))
    text = text_param(body.get("text"), "text", SMS_MAX)
    runner.run(["termux-sms-send", "-n", to], stdin=text)
    return {"sent": True, "to": to, "chars": len(text)}


def calls(runner, params: dict) -> list:
    limit = int_param(params.get("limit"), "limit", 20, 1, 200)
    offset = int_param(params.get("offset"), "offset", 0, 0, 100000)
    data = _json(runner.run(["termux-call-log", "-l", str(limit), "-o", str(offset)]), [])
    return data if isinstance(data, list) else []


def contacts(runner, params: dict) -> list:
    data = _json(runner.run(["termux-contact-list"], timeout=30), [])
    return data if isinstance(data, list) else []


def location(runner, params: dict) -> dict:
    provider = choice_param(params.get("provider"), "provider", "network", LOCATION_PROVIDERS)
    data = _json(runner.run(["termux-location", "-p", provider, "-r", "once"], timeout=LOCATION_TIMEOUT), {})
    if not isinstance(data, dict) or "latitude" not in data:
        raise HelperError("timeout", "no location fix: try provider=network, or go near a window for gps", 504)
    return data


def speak(runner, body: dict) -> dict:
    text = text_param(body.get("text"), "text", SPEAK_MAX)
    runner.run(["termux-tts-speak"], stdin=text, timeout=60)
    return {"spoken": True, "chars": len(text)}


def clipboard_get(runner, params: dict) -> dict:
    return {"text": runner.run(["termux-clipboard-get"])[:CLIPBOARD_MAX]}


def clipboard_set(runner, body: dict) -> dict:
    text = text_param(body.get("text"), "text", CLIPBOARD_MAX)
    runner.run(["termux-clipboard-set"], stdin=text)
    return {"set": True, "chars": len(text)}


def photo(runner, body: dict) -> dict:
    camera = choice_param(body.get("camera"), "camera", "back", tuple(CAMERAS))
    fd, path = tempfile.mkstemp(prefix="ps-photo-", suffix=".jpg")
    os.close(fd)
    try:
        runner.run(["termux-camera-photo", "-c", CAMERAS[camera], path], timeout=PHOTO_TIMEOUT)
        data = _read(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if not data:
        raise HelperError("permission_denied", "camera returned no image: grant Camera permission to Termux:API", 403)
    if len(data) > PHOTO_MAX_BYTES:
        raise HelperError("internal", "photo too large", 500)
    import base64
    return {"camera": camera, "mime": "image/jpeg", "bytes": len(data),
            "jpeg_b64": base64.b64encode(data).decode("ascii")}


def _read(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def call(runner, body: dict) -> dict:
    to = phone_number(body.get("to"))
    runner.run(["termux-telephony-call", to])
    return {"calling": True, "to": to}


def ir(runner, body: dict) -> dict:
    freq = int_param(body.get("freq"), "freq", 38000, 15000, 60000)
    pattern = body.get("pattern")
    if not isinstance(pattern, list) or not 1 <= len(pattern) <= 400:
        raise bad_request("pattern must be a list of 1 to 400 integers")
    try:
        values = [int(v) for v in pattern]
    except (TypeError, ValueError):
        raise bad_request("pattern must contain integers only")
    if any(v <= 0 or v > 100000 for v in values) or sum(values) > 2_000_000:
        raise bad_request("pattern values must be positive microseconds, total under 2 seconds")
    runner.run(["termux-infrared-transmit", "-f", str(freq), ",".join(map(str, values))])
    return {"sent": True, "freq": freq, "pulses": len(values)}


def fingerprint(runner, body: dict) -> dict:
    data = _json(runner.run(["termux-fingerprint"], timeout=60), {}) or {}
    return {"auth_result": data.get("auth_result"), "ok": data.get("auth_result") == "AUTH_RESULT_SUCCESS"}


def notify(runner, body: dict) -> dict:
    title = text_param(body.get("title"), "title", 100)
    content = text_param(body.get("content"), "content", NOTIFY_MAX)
    # Values follow fixed option flags; Termux's getopt treats them as option arguments.
    runner.run(["termux-notification", "--id", "phone-senses-watch", "--title", title, "--content", content])
    return {"posted": True}


# ---------------------------------------------------------------------------
# Find my phone (runs in the background so the HTTP request returns at once)

def _volumes(runner) -> dict[str, int]:
    data = _json(runner.run(["termux-volume"]), []) or []
    return {str(s.get("stream")): int(s.get("volume", 0)) for s in data if isinstance(s, dict)} | {
        f"{s.get('stream')}:max": int(s.get("max_volume", 15)) for s in data if isinstance(s, dict)}


def ring_loop(runner, seconds: int, sleep: Callable[[float], None] = time.sleep,
              clock: Callable[[], float] = time.monotonic) -> None:
    """Max volume, then speak + vibrate + blink the torch until time runs out; restore volume."""
    try:
        previous = _volumes(runner)
    except HelperError:
        previous = {}
    try:
        for stream in VOLUME_STREAMS:
            if stream in previous:
                runner.run(["termux-volume", stream, str(previous.get(f"{stream}:max", 15))])
        end = clock() + seconds
        while clock() < end:
            for argv, stdin in ((["termux-vibrate", "-f", "-d", "800"], None),
                                (["termux-torch", "on"], None)):
                _quiet(runner, argv, stdin)
            _quiet(runner, ["termux-tts-speak", "-s", "ALARM"], "I am here. Phone Senses.")
            _quiet(runner, ["termux-torch", "off"], None)
            sleep(0.5)
    finally:
        _quiet(runner, ["termux-torch", "off"], None)
        for stream in VOLUME_STREAMS:
            if stream in previous:
                _quiet(runner, ["termux-volume", stream, str(previous[stream])], None)


def _quiet(runner, argv: list[str], stdin: str | None) -> None:
    try:
        runner.run(argv, stdin=stdin, timeout=20)
    except HelperError:
        pass


_ring_lock = threading.Lock()


def ring(runner, body: dict, start_thread: bool = True) -> dict:
    seconds = int_param(body.get("seconds"), "seconds", 20, 1, 60)
    if not _ring_lock.acquire(blocking=False):
        return {"ringing": True, "seconds": seconds, "already_ringing": True}

    def _run():
        try:
            ring_loop(runner, seconds, sleep=getattr(runner, "sleep", time.sleep),
                      clock=getattr(runner, "clock", time.monotonic))
        finally:
            _ring_lock.release()

    if start_thread:
        threading.Thread(target=_run, name="phone-senses-ring", daemon=True).start()
    else:
        _run()
    return {"ringing": True, "seconds": seconds}


# (method, path) -> (handler, kind). kind: "query" reads URL params, "body" reads JSON body.
ROUTES: dict[tuple[str, str], tuple[Callable, str]] = {
    ("GET", "/v1/status"): (status, "query"),
    ("GET", "/v1/notifications"): (notifications, "query"),
    ("GET", "/v1/sms"): (sms_list, "query"),
    ("POST", "/v1/sms/send"): (sms_send, "body"),
    ("GET", "/v1/calls"): (calls, "query"),
    ("GET", "/v1/contacts"): (contacts, "query"),
    ("GET", "/v1/location"): (location, "query"),
    ("POST", "/v1/ring"): (ring, "body"),
    ("POST", "/v1/speak"): (speak, "body"),
    ("GET", "/v1/clipboard"): (clipboard_get, "query"),
    ("POST", "/v1/clipboard"): (clipboard_set, "body"),
    ("POST", "/v1/photo"): (photo, "body"),
    ("POST", "/v1/call"): (call, "body"),
    ("POST", "/v1/ir"): (ir, "body"),
    ("POST", "/v1/fingerprint"): (fingerprint, "body"),
    ("POST", "/v1/notify"): (notify, "body"),
}

# Endpoints limited to 5 per minute (runaway sending protection).
SENSITIVE_PATHS = {"/v1/sms/send", "/v1/call"}

FEATURES = sorted({path.split("/", 2)[2] for _, path in ROUTES})
