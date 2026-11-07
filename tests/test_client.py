"""client.py against a real mock helper over HTTP."""
from __future__ import annotations

import socket

import pytest

import phone_senses
from phone_senses.client import PhoneClient, PhoneError, sign


def test_signature_matches_helper(helper):
    args = ("s" * 64, "POST", "/v1/sms/send?x=1", "1700000000", "abcd", b'{"a":1}')
    assert sign(*args) == helper.sign(*args)


def test_get_and_post(mock_server):
    url, secret, app = mock_server
    c = PhoneClient(url, secret)
    assert c.get("/v1/status")["battery"]["percentage"] == 76
    assert len(c.get("/v1/sms", {"limit": 3})) == 3
    assert c.post("/v1/sms/send", {"to": "+919000000199", "text": "hello"})["sent"] is True
    assert app.runner.sent_sms[-1] == {"to": "+919000000199", "text": "hello"}


def test_wrong_secret_is_unauthorized(mock_server):
    url, _, _ = mock_server
    with pytest.raises(PhoneError) as exc:
        PhoneClient(url, "0" * 64).get("/v1/status")
    assert exc.value.code == "unauthorized"
    assert "pair" in exc.value.to_result()["hint"]


def test_unreachable_is_friendly():
    with socket.socket() as s:   # find a free port with nothing listening
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    with pytest.raises(PhoneError) as exc:
        PhoneClient(f"http://127.0.0.1:{port}", "x", timeout=2).get("/v1/status")
    result = exc.value.to_result()
    assert result["error"] == "phone_unreachable" and "Termux" in result["hint"]


def test_helper_validation_error_passes_through(mock_server):
    url, secret, _ = mock_server
    with pytest.raises(PhoneError) as exc:
        PhoneClient(url, secret).post("/v1/sms/send", {"to": "abc", "text": "hi"})
    assert exc.value.code == "bad_request"


def test_bad_url_rejected():
    with pytest.raises(PhoneError):
        PhoneClient("not a url", "x")


def test_not_paired_without_secret():
    phone_senses.client.set_client(None)
    with pytest.raises(PhoneError) as exc:
        phone_senses.client.get_client()
    assert exc.value.code == "not_paired"
