"""Phone helper: auth, replay protection, validation, rate limits, mock endpoints."""
from __future__ import annotations

import json
import secrets
import time
import urllib.request

import pytest

SECRET = "ab" * 32


class Clock:
    def __init__(self, t: float = 1_800_000_000.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def headers_for(helper, method, path, body=b"", secret=SECRET, ts=None, nonce=None):
    ts = str(int(ts if ts is not None else time.time()))
    nonce = nonce or secrets.token_hex(16)
    return {"X-PS-Timestamp": ts, "X-PS-Nonce": nonce,
            "X-PS-Signature": helper.sign(secret, method, path, ts, nonce, body)}


@pytest.fixture()
def app(helper):
    clock = Clock()
    a = helper.App(SECRET, helper.MockRunner(), mock=True, clock=clock, monotonic=Clock(0))
    a.clock = clock
    return a


def call(helper, app, method, path, body=None, **kw):
    raw = json.dumps(body).encode() if body is not None else b""
    hdrs = headers_for(helper, method, path, raw, ts=kw.pop("ts", app.clock.t), **kw)
    return app.handle(method, path, hdrs, raw)


def test_anonymous_ping_reveals_nothing(helper, app):
    assert app.handle("GET", "/v1/ping", {}, b"") == (200, {"ok": True})


def test_signed_ping_has_version(helper, app):
    status, payload = call(helper, app, "GET", "/v1/ping")
    assert status == 200 and payload["data"]["helper_version"] == helper.VERSION
    assert "sms/send" in payload["data"]["features"]


def test_unsigned_request_rejected(helper, app):
    status, payload = app.handle("GET", "/v1/status", {}, b"")
    assert status == 401 and payload["error"] == "unauthorized"


def test_bad_signature_rejected(helper, app):
    status, payload = call(helper, app, "GET", "/v1/status", secret="cd" * 32)
    assert status == 401 and payload["message"] == "bad signature"


def test_signature_covers_query_and_body(helper, app):
    raw = json.dumps({"seconds": 5}).encode()
    hdrs = headers_for(helper, "POST", "/v1/ring", raw, ts=app.clock.t)
    tampered = json.dumps({"seconds": 60}).encode()
    assert app.handle("POST", "/v1/ring", hdrs, tampered)[0] == 401
    hdrs = headers_for(helper, "GET", "/v1/sms?limit=1", ts=app.clock.t)
    assert app.handle("GET", "/v1/sms?limit=100", hdrs, b"")[0] == 401


def test_timestamp_skew_rejected(helper, app):
    status, payload = call(helper, app, "GET", "/v1/status", ts=app.clock.t - 61)
    assert status == 401 and "skew" in payload["message"]
    assert call(helper, app, "GET", "/v1/status", ts=app.clock.t - 59)[0] == 200


def test_nonce_replay_rejected(helper, app):
    hdrs = headers_for(helper, "GET", "/v1/status", ts=app.clock.t)
    assert app.handle("GET", "/v1/status", hdrs, b"")[0] == 200
    status, payload = app.handle("GET", "/v1/status", hdrs, b"")
    assert status == 401 and payload["message"] == "nonce reused"


@pytest.mark.parametrize("to", ["12345", "+91 abc", "9" * 16, "", "+91-9000;rm", None])
def test_invalid_phone_number(helper, app, to):
    status, payload = call(helper, app, "POST", "/v1/sms/send", {"to": to, "text": "hi"})
    assert status == 400 and payload["error"] == "bad_request"


def test_sms_text_too_long(helper, app):
    status, payload = call(helper, app, "POST", "/v1/sms/send", {"to": "+919000000101", "text": "x" * 481})
    assert status == 400 and "too long" in payload["message"]


def test_sms_send_uses_stdin_not_argv(helper, app):
    status, payload = call(helper, app, "POST", "/v1/sms/send", {"to": "+91 90000 00101", "text": "-h --oops"})
    assert status == 200 and payload["data"]["to"] == "+919000000101"
    argv, stdin = app.runner.calls[-1]
    assert argv == ["termux-sms-send", "-n", "+919000000101"] and stdin == "-h --oops"


def test_sensitive_rate_limit(helper, app):
    for _ in range(5):
        assert call(helper, app, "POST", "/v1/sms/send", {"to": "+919000000101", "text": "hi"})[0] == 200
    status, payload = call(helper, app, "POST", "/v1/sms/send", {"to": "+919000000101", "text": "hi"})
    assert status == 429 and payload["error"] == "rate_limited"


def test_general_rate_limit(helper, app):
    results = [call(helper, app, "GET", "/v1/status")[0] for _ in range(11)]
    assert results[:10] == [200] * 10 and results[10] == 429


def test_bad_enum_and_int(helper, app):
    assert call(helper, app, "GET", "/v1/sms?box=spam")[0] == 400
    assert call(helper, app, "GET", "/v1/sms?limit=0")[0] == 400
    assert call(helper, app, "GET", "/v1/location?provider=satellite")[0] == 400
    assert call(helper, app, "POST", "/v1/ring", {"seconds": 61})[0] == 400


def test_unknown_endpoint(helper, app):
    assert call(helper, app, "GET", "/v1/shell")[0] == 404


def test_mock_shapes(helper, app):
    st = call(helper, app, "GET", "/v1/status")[1]["data"]
    assert st["battery"]["percentage"] == 76 and st["wifi"]["ssid"]
    sms = call(helper, app, "GET", "/v1/sms?limit=5&box=inbox")[1]["data"]
    assert len(sms) == 5 and {"number", "received", "body", "threadid"} <= set(sms[0])
    assert sms[-1]["received"] >= sms[0]["received"]   # newest last, like Termux:API
    assert all(m["type"] == "inbox" for m in sms)
    notes = call(helper, app, "GET", "/v1/notifications")[1]["data"]
    assert {"packageName", "title", "content", "when"} <= set(notes[0])
    assert not notes[0]["when"].startswith("@")
    loc = call(helper, app, "GET", "/v1/location")[1]["data"]
    assert "latitude" in loc
    photo = call(helper, app, "POST", "/v1/photo", {"camera": "front"})[1]["data"]
    assert photo["mime"] == "image/jpeg" and photo["bytes"] > 100


def test_ring_restores_volume(helper):
    commands = __import__("commands")
    runner = helper.MockRunner()
    commands.ring(runner, {"seconds": 1}, start_thread=False)
    sets = [argv for argv, _ in runner.calls if argv[0] == "termux-volume" and len(argv) == 3]
    assert ["termux-volume", "music", "15"] in sets
    assert sets[-4:] == [["termux-volume", s, v] for s, v in
                         (("music", "4"), ("alarm", "9"), ("notification", "6"), ("ring", "6"))]
    assert runner.calls[-5][0] == ["termux-torch", "off"]


def test_ir_validation(helper, app):
    assert call(helper, app, "POST", "/v1/ir", {"freq": 38000, "pattern": [9000, 4500, 560]})[0] == 200
    assert call(helper, app, "POST", "/v1/ir", {"freq": 38000, "pattern": ["1;ls"]})[0] == 400


def test_pair_writes_private_secret(helper, tmp_path):
    path = tmp_path / "ps" / "secret"
    secret = helper.pair(path)
    assert len(secret) == 64 and helper.load_secret(path) == secret
    assert (path.stat().st_mode & 0o777) == 0o600


def test_http_round_trip(helper, mock_server):
    url, secret, _ = mock_server
    path = "/v1/status"
    req = urllib.request.Request(url + path, headers=headers_for(helper, "GET", path, secret=secret))
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert json.loads(resp.read())["data"]["battery"]["percentage"] == 76
