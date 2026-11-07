#!/usr/bin/env python3
"""Phone Senses helper: a tiny HMAC-signed JSON API over Termux:API.

Runs on your Android phone inside Termux (standard library only):

    python phone_helper/helper.py --pair            # first time: prints the pairing code once
    python phone_helper/helper.py --host 0.0.0.0    # serve on your Wi-Fi / Tailscale address

On a laptop, ``--mock`` serves synthetic fixture data instead of running termux-* commands.

Every request except an anonymous ping must carry X-PS-Timestamp, X-PS-Nonce and
X-PS-Signature = hex(HMAC_SHA256(secret, METHOD\\nPATH_WITH_QUERY\\nTIMESTAMP\\nNONCE\\nSHA256_HEX(BODY))).
The secret itself is never sent. See docs/04-architecture.md.
"""
from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import commands  # noqa: E402  (sibling module; this file runs as a script)
from commands import HelperError  # noqa: E402

VERSION = "0.1.0"
MAX_SKEW_S = 60
NONCE_CACHE = 1000
MAX_BODY = 64 * 1024
GENERAL_RATE = (10, 1.0)      # 10 requests per second
SENSITIVE_RATE = (5, 60.0)    # 5 per minute for sms/send and call
DEFAULT_SECRET_FILE = Path.home() / ".phone-senses" / "secret"
MOCK_DIR = Path(__file__).resolve().parent / "mock_data"


def sign(secret: str, method: str, path: str, timestamp: str, nonce: str, body: bytes) -> str:
    """Signature shared with the plugin's client.py (keep the two identical)."""
    msg = "\n".join([method.upper(), path, timestamp, nonce, hashlib.sha256(body).hexdigest()])
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


class Auth:
    """Checks signature, timestamp skew and nonce reuse."""

    def __init__(self, secret: str, clock: Callable[[], float] = time.time):
        self.secret = secret
        self.clock = clock
        self._nonces: collections.OrderedDict[str, None] = collections.OrderedDict()
        self._lock = threading.Lock()

    def check(self, method: str, path: str, headers: Any, body: bytes) -> str | None:
        """Return None when the request is authentic, else a short reason."""
        ts = headers.get("X-PS-Timestamp") or ""
        nonce = headers.get("X-PS-Nonce") or ""
        sig = headers.get("X-PS-Signature") or ""
        if not (ts and nonce and sig):
            return "missing signature headers"
        try:
            skew = abs(self.clock() - int(ts))
        except ValueError:
            return "bad timestamp"
        if skew > MAX_SKEW_S:
            return "timestamp skew too large (check the phone and laptop clocks)"
        if len(nonce) > 64:
            return "bad nonce"
        expected = sign(self.secret, method, path, ts, nonce, body)
        if not hmac.compare_digest(expected, sig):
            return "bad signature"
        with self._lock:
            if nonce in self._nonces:
                return "nonce reused"
            self._nonces[nonce] = None
            while len(self._nonces) > NONCE_CACHE:
                self._nonces.popitem(last=False)
        return None


class RateLimiter:
    """Sliding-window limits: one general bucket, one for sensitive endpoints."""

    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self.clock = clock
        self._hits: dict[str, collections.deque] = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    def allow(self, bucket: str, limit: int, window: float) -> bool:
        now = self.clock()
        with self._lock:
            hits = self._hits[bucket]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True


class MockRunner:
    """Answers termux-* argv with synthetic fixtures from mock_data/. Never runs anything."""

    def __init__(self, data_dir: Path = MOCK_DIR):
        self.data_dir = data_dir
        self.calls: list[tuple[list[str], str | None]] = []   # recorded for tests
        self.sent_sms: list[dict] = []
        # Pinned at start so fixture timestamps (and transaction ids) are stable across requests.
        self.started = datetime.datetime.now().replace(microsecond=0)

    def sleep(self, seconds: float) -> None:  # ring loop runs instantly in mock mode
        return None

    def clock(self) -> float:   # each look at the clock moves it 5 s, so a ring lasts a few loops
        self._t = getattr(self, "_t", 0.0) + 5.0
        return self._t

    def _fixture(self, name: str) -> str:
        """Fixture text with relative dates ("@2d 14:02:00" = two days ago) made absolute."""
        text = (self.data_dir / f"{name}.json").read_text(encoding="utf-8")
        now = self.started
        midnight = now.replace(hour=0, minute=0, second=0)

        def absolute(m: re.Match) -> str:
            days = int(m.group(1))
            h, mi, se = (int(x) for x in m.group(2).split(":"))
            secs = h * 3600 + mi * 60 + se
            if days == 0:   # squeeze "today" into midnight..now so nothing is in the future
                when = midnight + datetime.timedelta(seconds=int(secs * (now - midnight).total_seconds() / 86400))
            else:
                when = midnight - datetime.timedelta(days=days) + datetime.timedelta(seconds=secs)
            return f'"{when:%Y-%m-%d %H:%M:%S}"'

        return re.sub(r'"@(\d+)d (\d\d:\d\d:\d\d)"', absolute, text)

    def run(self, argv: list[str], timeout: float = 15, stdin: str | None = None) -> str:
        self.calls.append((list(argv), stdin))
        cmd = argv[0]
        if cmd == "getprop":
            return "Mock Phone (Phone Senses)\n"
        if cmd == "termux-sms-list":
            items = json.loads(self._fixture("sms"))
            opts, rest = {}, argv[1:]
            while rest:
                flag = rest.pop(0)
                opts[flag] = rest.pop(0) if flag in ("-l", "-o", "-t", "-f") and rest else "true"
            box = opts.get("-t", "inbox")
            if box != "all":
                items = [m for m in items if m.get("type") == box]
            if "-f" in opts:
                items = [m for m in items if m.get("number") == opts["-f"]]
            items.sort(key=lambda m: m.get("received", ""), reverse=True)
            off, lim = int(opts.get("-o", 0)), int(opts.get("-l", 10))
            page = items[off:off + lim]
            page.reverse()  # Termux:API prints the newest entry last
            return json.dumps(page)
        if cmd == "termux-sms-send":
            self.sent_sms.append({"to": argv[2], "text": stdin})
            return ""
        if cmd == "termux-call-log":
            items = json.loads(self._fixture("calls"))
            return json.dumps(items[: int(argv[2])])
        if cmd == "termux-volume":
            return self._fixture("volume") if len(argv) == 1 else ""
        if cmd == "termux-clipboard-get":
            return "Mock clipboard text from the phone"
        if cmd == "termux-fingerprint":
            return json.dumps({"errors": [], "failed_attempts": 0, "auth_result": "AUTH_RESULT_SUCCESS"})
        if cmd == "termux-camera-photo":
            Path(argv[-1]).write_bytes((self.data_dir / "photo.jpg").read_bytes())
            return ""
        fixtures = {
            "termux-battery-status": "battery", "termux-wifi-connectioninfo": "wifi",
            "termux-notification-list": "notifications", "termux-contact-list": "contacts",
            "termux-location": "location",
        }
        if cmd in fixtures:
            return self._fixture(fixtures[cmd])
        return ""   # vibrate, torch, tts, clipboard-set, call, ir, notify: no output


class App:
    """Routing, auth and rate limits, independent of the HTTP server (easy to test)."""

    def __init__(self, secret: str, runner: Any, mock: bool = False,
                 clock: Callable[[], float] = time.time,
                 monotonic: Callable[[], float] = time.monotonic):
        self.auth = Auth(secret, clock)
        self.limiter = RateLimiter(monotonic)
        self.runner = runner
        self.mock = mock
        self._ping_info: dict | None = None

    def handle(self, method: str, raw_path: str, headers: Any, body: bytes) -> tuple[int, dict]:
        try:
            return self._handle(method, raw_path, headers, body)
        except HelperError as exc:
            return exc.status, {"ok": False, "error": exc.code, "message": exc.message}
        except Exception:  # never leak internals or message bodies
            return 500, {"ok": False, "error": "internal", "message": "unexpected helper error"}

    def _handle(self, method: str, raw_path: str, headers: Any, body: bytes) -> tuple[int, dict]:
        parts = urlsplit(raw_path)
        path = parts.path
        if not self.limiter.allow("all", *GENERAL_RATE):
            return 429, {"ok": False, "error": "rate_limited", "message": "too many requests"}
        signed = bool(headers.get("X-PS-Signature"))
        if method == "GET" and path == "/v1/ping" and not signed:
            return 200, {"ok": True}
        reason = self.auth.check(method, raw_path, headers, body)
        if reason:
            return 401, {"ok": False, "error": "unauthorized", "message": reason}
        if path == "/v1/ping":
            if self._ping_info is None:
                self._ping_info = commands.ping_info(self.runner)
            return 200, {"ok": True, "data": {"helper_version": VERSION, "mock": self.mock,
                                              "features": commands.FEATURES, **self._ping_info}}
        route = commands.ROUTES.get((method, path))
        if route is None:
            known = any(p == path for _, p in commands.ROUTES)
            return (405 if known else 404), {"ok": False, "error": "bad_request",
                                             "message": "unknown endpoint"}
        if path in commands.SENSITIVE_PATHS and not self.limiter.allow(path, *SENSITIVE_RATE):
            return 429, {"ok": False, "error": "rate_limited", "message": "max 5 per minute"}
        handler, kind = route
        if kind == "query":
            params = {k: v[0] for k, v in parse_qs(parts.query).items()}
        else:
            try:
                params = json.loads(body.decode("utf-8") or "{}")
            except ValueError:
                raise commands.bad_request("body must be JSON")
            if not isinstance(params, dict):
                raise commands.bad_request("body must be a JSON object")
        return 200, {"ok": True, "data": handler(self.runner, params)}


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = f"PhoneSenses/{VERSION}"
        sys_version = ""

        def _serve(self, method: str) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                status, payload = 413, {"ok": False, "error": "bad_request", "message": "body too large"}
            else:
                body = self.rfile.read(length) if length > 0 else b""
                status, payload = app.handle(method, self.path, self.headers, body)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            self._serve("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._serve("POST")

        def log_message(self, fmt: str, *args: Any) -> None:
            # Log method, path (no query: it may contain numbers) and status only. Never bodies.
            line = (args[0] if args else "").split(" ")
            path = urlsplit(line[1]).path if len(line) > 1 else "?"
            status = args[1] if len(args) > 1 else "?"
            sys.stderr.write(f"[phone-senses] {line[0]} {path} {status}\n")

    return Handler


def pair(secret_file: Path) -> str:
    """Create a new random secret (rotating any old one) and return it."""
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(secret_file.parent, 0o700)
    secret = secrets.token_hex(32)
    fd = os.open(secret_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(secret + "\n")
    os.chmod(secret_file, 0o600)
    return secret


def load_secret(secret_file: Path) -> str | None:
    try:
        value = secret_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Phone Senses helper (runs in Termux)")
    ap.add_argument("--host", default="127.0.0.1",
                    help="address to listen on: your phone's Wi-Fi or Tailscale IP, or 0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--pair", action="store_true", help="generate a new pairing code and exit")
    ap.add_argument("--mock", action="store_true", help="serve synthetic data (for laptops and demos)")
    ap.add_argument("--secret-file", type=Path, default=DEFAULT_SECRET_FILE)
    args = ap.parse_args(argv)

    if args.pair:
        secret = pair(args.secret_file)
        print("Phone Senses pairing code (shown once; paste it into the Hermes plugin setting 'helper_token'):")
        print()
        print(f"    {secret}")
        print()
        print(f"Saved to {args.secret_file} (mode 600). Run --pair again to rotate it.")
        return 0

    secret = load_secret(args.secret_file)
    if not secret:
        print(f"No pairing secret at {args.secret_file}. Run: python phone_helper/helper.py --pair",
              file=sys.stderr)
        return 2

    runner = MockRunner() if args.mock else commands.SubprocessRunner()
    app = App(secret, runner, mock=args.mock)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(app))
    mode = "MOCK data" if args.mock else "Termux:API"
    print(f"Phone Senses helper {VERSION} ({mode}) listening on http://{args.host}:{args.port}")
    print("Set the Hermes plugin setting helper_url to this phone's address. Ctrl+C to stop.")
    if not args.mock:
        try:  # visible reminder on the phone that the helper is running
            runner.run(["termux-notification", "--id", "phone-senses-helper", "--ongoing",
                        "--title", "Phone Senses helper running",
                        "--content", f"Listening on port {args.port}. Stop it in Termux with Ctrl+C."])
        except HelperError:
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if not args.mock:
            try:
                runner.run(["termux-notification-remove", "phone-senses-helper"])
            except HelperError:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
