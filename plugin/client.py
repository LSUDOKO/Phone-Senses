"""HTTP client for the phone helper: HMAC signing, timeouts and friendly errors.

Settings come from the plugin's ``config_schema`` (``helper_url``); the pairing secret comes from
Hermes secret storage via ``agent.secret_scope.get_secret("PHONE_SENSES_TOKEN")``. Nothing is
read at import time, so ``register()`` stays I/O-free.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Callable
from urllib.parse import urlencode, urlsplit

SECRET_ENV = "PHONE_SENSES_TOKEN"
DEFAULT_URL = "http://127.0.0.1:8765"
DEFAULT_TIMEOUT = 10

HINTS = {
    "phone_unreachable": "Open Termux on the phone and run: python phone_helper/helper.py --host 0.0.0.0. "
                         "Check that helper_url matches the address it prints and that both devices are "
                         "on the same Wi-Fi or Tailscale network.",
    "not_paired": "Run 'python phone_helper/helper.py --pair' in Termux, then paste the pairing code into "
                  "the Phone Senses setting 'helper_token'. Type /phone pair for help.",
    "unauthorized": "The pairing code does not match the phone, or the clocks differ by over a minute. "
                    "Run /phone pair for help.",
    "permission_denied": "Grant the permission in Android Settings > Apps > Termux:API > Permissions "
                         "(for notifications: Settings > Notification access > Termux:API).",
    "termux_api_missing": "Install the Termux:API app from F-Droid and run 'pkg install termux-api' in Termux.",
    "timeout": "The phone took too long. A missing Android permission often causes this.",
    "rate_limited": "Too many requests to the phone. Wait a moment and try again.",
    "not_supported": "This phone does not support that feature.",
}


class PhoneError(Exception):
    """A helper or network failure with a stable code and a user-facing hint."""

    def __init__(self, code: str, message: str = ""):
        super().__init__(message or code)
        self.code = code
        self.message = message or code

    def to_result(self) -> dict:
        out = {"ok": False, "error": self.code, "message": self.message}
        if self.code in HINTS:
            out["hint"] = HINTS[self.code]
        return out


def sign(secret: str, method: str, path: str, timestamp: str, nonce: str, body: bytes) -> str:
    """Must stay identical to ``phone_helper/helper.py:sign``."""
    msg = "\n".join([method.upper(), path, timestamp, nonce, hashlib.sha256(body).hexdigest()])
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


class PhoneClient:
    """Signed JSON requests to the phone helper."""

    def __init__(self, base_url: str, secret: str, timeout: float = DEFAULT_TIMEOUT,
                 opener: Callable[..., Any] = urllib.request.urlopen):
        parts = urlsplit((base_url or "").strip())
        if parts.scheme not in ("http", "https") or not parts.hostname:
            raise PhoneError("bad_config", f"helper_url must look like {DEFAULT_URL}")
        self.base_url = f"{parts.scheme}://{parts.netloc}"
        self.secret = secret
        self.timeout = timeout
        self._open = opener

    def request(self, method: str, path: str, params: dict | None = None, body: dict | None = None,
                timeout: float | None = None) -> Any:
        """Send a signed request and return the response ``data``; raise PhoneError on failure."""
        query = urlencode(sorted((k, str(v)) for k, v in (params or {}).items() if v is not None))
        full_path = f"{path}?{query}" if query else path
        raw = json.dumps(body).encode("utf-8") if body is not None else b""
        ts, nonce = str(int(time.time())), secrets.token_hex(16)
        headers = {
            "X-PS-Timestamp": ts, "X-PS-Nonce": nonce,
            "X-PS-Signature": sign(self.secret, method, full_path, ts, nonce, raw),
            "Content-Type": "application/json", "User-Agent": "phone-senses-plugin/0.1",
        }
        req = urllib.request.Request(self.base_url + full_path, data=raw if method == "POST" else None,
                                     headers=headers, method=method)
        try:
            with self._open(req, timeout=timeout or self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8") or "{}")
            except (ValueError, OSError):
                payload = {}
            raise PhoneError(payload.get("error") or "internal",
                             payload.get("message") or f"helper returned HTTP {exc.code}")
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            raise PhoneError("phone_unreachable",
                             f"phone not reachable at {self.base_url}: is Termux running and on the same "
                             f"network? ({type(reason).__name__})")
        except ValueError:
            raise PhoneError("internal", "the helper sent a response that is not JSON")
        if not isinstance(payload, dict) or not payload.get("ok"):
            raise PhoneError(str(payload.get("error") or "internal"), str(payload.get("message") or ""))
        return payload.get("data")

    def get(self, path: str, params: dict | None = None, timeout: float | None = None) -> Any:
        return self.request("GET", path, params=params, timeout=timeout)

    def post(self, path: str, body: dict | None = None, timeout: float | None = None) -> Any:
        return self.request("POST", path, body=body or {}, timeout=timeout)


# ---------------------------------------------------------------------------
# Runtime wiring: set by register(); tests inject a client directly.

_ctx: Any = None
_client_override: PhoneClient | None = None


def configure(ctx: Any) -> None:
    global _ctx
    _ctx = ctx


def set_client(client: PhoneClient | None) -> None:
    """Test hook: use this client instead of building one from settings."""
    global _client_override
    _client_override = client


def setting(key: str, default: Any = None) -> Any:
    """Read a plugin setting (``plugins.entries.phone-senses.settings.<key>``)."""
    if _ctx is None:
        return default
    try:
        value = _ctx.get_config(key, default)
    except Exception:
        return default
    return default if value is None else value


def _secret() -> str | None:
    try:
        from agent.secret_scope import get_secret
    except ImportError:   # outside Hermes (unit tests inject a client instead)
        return None
    try:
        return get_secret(SECRET_ENV)
    except Exception:
        return None


def get_client() -> PhoneClient:
    """Build a client from the current settings (they can change between calls)."""
    if _client_override is not None:
        return _client_override
    secret = (_secret() or "").strip()
    if not secret:
        raise PhoneError("not_paired", "Phone Senses is not paired with a phone yet.")
    return PhoneClient(str(setting("helper_url", DEFAULT_URL)), secret)
