"""Scam tripwire: correlation levels (pure) and the full tool against the mock 'scam' scenario."""
from __future__ import annotations

import json
import secrets
import sqlite3
import threading
from http.server import ThreadingHTTPServer

import pytest

import phone_senses
from phone_senses import tripwire

NOW = 1_800_000_000


def ev(kind: str, minutes_ago: float, **detail) -> dict:
    return {"kind": kind, "ts": int(NOW - minutes_ago * 60), "detail": detail}


@pytest.mark.parametrize("events, level", [
    ([], "clear"),
    ([ev("otp", 2)], "low"),                                        # an OTP on its own is normal
    ([ev("unknown_ring", 5)], "low"),
    ([ev("unknown_call", 10), ev("otp", 3)], "high"),               # stranger talks, then a code arrives
    ([ev("unknown_call", 10), ev("scam_text", 12)], "high"),
    ([ev("remote_access", 4)], "high"),                             # screen sharing alone is a warning
    ([ev("remote_access", 6), ev("otp", 2)], "critical"),           # screen shared while a code arrives
    ([ev("remote_access", 6), ev("collect_request", 1)], "critical"),
    ([ev("unknown_call", 15), ev("otp", 8), ev("debit", 2)], "critical"),
    ([ev("unknown_call", 50), ev("otp", 3)], "low"),                # call is outside the 30 min window
    ([ev("debit", 2)], "low"),                                      # an ordinary payment
])
def test_levels(events, level):
    assert tripwire.assess(events, NOW, 30)["level"] == level


def test_advice_matches_signals():
    r = tripwire.assess([ev("unknown_call", 12), ev("remote_access", 9), ev("collect_request", 2)], NOW, 30)
    text = " ".join(r["advice"])
    assert r["alert"] and "hang up" in text and "screen sharing" in text and "UPI PIN sends money" in text
    assert "1930" in text and "cybercrime.gov.in" in text
    assert [e["kind"] for e in r["timeline"]] == ["unknown_call", "remote_access", "collect_request"]
    assert "1930" not in " ".join(tripwire.assess([ev("remote_access", 3)], NOW, 30)["advice"])


def test_call_event_rules():
    base = {"number": "+917000000999", "ts": NOW}
    assert tripwire.call_event({**base, "name": "Mom", "type": "incoming", "duration": "05:00"}) is None
    assert tripwire.call_event({**base, "type": "incoming", "duration": "04:10"})["kind"] == "unknown_call"
    assert tripwire.call_event({**base, "type": "incoming", "duration": "00:12"})["kind"] == "unknown_ring"
    assert tripwire.call_event({**base, "type": "missed", "duration": "00:00"})["kind"] == "unknown_ring"
    intl = tripwire.call_event({**base, "number": "+447700900123", "type": "incoming", "duration": "1:00"})
    assert intl["detail"]["international"] is True


def test_notification_and_sms_events():
    remote = tripwire.notification_events({"package": "com.anydesk.anydeskandroid", "app": "AnyDesk",
                                           "title": "AnyDesk", "text": "Session active", "ts": NOW})
    assert remote[0]["kind"] == "remote_access"
    cast = tripwire.notification_events({"package": "com.android.systemui", "app": "Systemui",
                                         "title": "Started casting", "text": "your screen", "ts": NOW})
    assert cast and cast[0]["kind"] == "remote_access"
    chat = tripwire.notification_events({"package": "com.whatsapp", "app": "WhatsApp", "title": "Rahul",
                                         "text": "install anydesk na, I'll fix your laptop", "ts": NOW})
    assert chat == []   # a friend's chat message is not a remote session
    sms = tripwire.sms_events({"from": "VM-DEMOBK", "ts": NOW,
                               "_full_body": "731904 is the OTP to reset your UPI PIN. Do not share it."})
    assert [e["kind"] for e in sms] == ["otp"] and "731904" not in json.dumps(sms)
    collect = tripwire.sms_events({"from": "AX-DEMOBK", "ts": NOW,
                                   "_full_body": "SUPPORT DESK has requested Rs 4,999 from you on UPI. Approve the request in your app."})
    assert "collect_request" in [e["kind"] for e in collect]


def test_spoken_warning_is_short_and_safe():
    crit = tripwire.assess([ev("remote_access", 6), ev("otp", 2)], NOW, 30)
    text = tripwire.spoken_warning(crit)
    assert "scam" in text and "1 9 3 0" in text and len(text) < 300
    assert "Hang up" in tripwire.spoken_warning(tripwire.assess([ev("unknown_call", 9), ev("otp", 2)], NOW, 30))


# ---------------------------------------------------------------------------
# End to end against the mock helper with the "scam" scenario


@pytest.fixture()
def scam_plugin(helper, tmp_path):
    secret = secrets.token_hex(32)
    runner = helper.MockRunner(scenario="scam")
    app = helper.App(secret, runner, mock=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), helper.make_handler(app))
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()
    ps = phone_senses
    ps.client.set_client(ps.client.PhoneClient(f"http://127.0.0.1:{server.server_address[1]}", secret, timeout=5))
    ps.storage.set_connector(lambda: sqlite3.connect(tmp_path / "data.db"))
    try:
        yield ps, runner
    finally:
        ps.client.set_client(None)
        ps.storage.set_connector(None)
        server.shutdown()
        server.server_close()


def call(ps, name, **args):
    return json.loads(ps.tools.HANDLERS[name](args))


def test_unknown_scenario_rejected(helper):
    with pytest.raises(ValueError):
        helper.MockRunner(scenario="nope")


def test_scam_guard_finds_the_scam_in_progress(scam_plugin):
    ps, runner = scam_plugin
    r = call(ps, "phone_scam_guard")
    assert r["ok"] and r["level"] == "critical" and r["alert"]
    kinds = [e["kind"] for e in r["timeline"]]
    assert kinds == ["scam_text", "unknown_call", "remote_access", "remote_access", "otp", "debit"]
    assert r["timeline"][-1]["amount_rs"] == 24999.0
    assert "731904" not in json.dumps(r)            # the OTP never reaches the model
    assert "incident" not in r and "phone_alerted" not in r
    assert not [c for c, _ in runner.calls if c[0] in ("termux-tts-speak", "termux-notification")]


def test_scam_guard_alerts_the_phone(scam_plugin):
    ps, runner = scam_plugin
    r = call(ps, "phone_scam_guard", alert_phone=True)
    assert r["phone_alerted"] == ["notification", "spoken"]
    spoken = [stdin for c, stdin in runner.calls if c[0] == "termux-tts-speak"]
    assert spoken and "scam" in spoken[0] and "731904" not in spoken[0]


def test_scam_guard_window(scam_plugin):
    ps, _ = scam_plugin
    assert call(ps, "phone_scam_guard", minutes=5)["level"] == "low"         # only the debit is that recent
    assert call(ps, "phone_scam_guard", minutes=1000)["window_minutes"] == 180   # clamped to the maximum


def test_scam_guard_watch_rule_alerts_once(scam_plugin):
    ps, runner = scam_plugin
    added = call(ps, "phone_watch_add", kind="scam_guard")
    assert added["ok"] and "scam" in added["rule"]
    first = call(ps, "phone_watch_check", notify_phone=True)
    guard = [m for m in first["matches"] if m["source"] == "scam_guard"]
    assert len(guard) == 1 and guard[0]["level"] == "critical" and guard[0]["phone_alerted"]
    assert first["checked"]["scam_guard"] == "critical"
    again = call(ps, "phone_watch_check", notify_phone=True)
    assert not [m for m in again["matches"] if m["source"] == "scam_guard"]     # same incident: no repeat
    assert len([c for c, _ in runner.calls if c[0] == "termux-tts-speak"]) == 1


def test_scam_guard_quiet_on_an_ordinary_day(plugin):
    ps, _ = plugin
    r = call(ps, "phone_scam_guard")
    assert r["ok"] and not r["alert"] and r["level"] in ("clear", "low")


def test_phone_guard_command(scam_plugin):
    ps, runner = scam_plugin
    text = ps.commands.handle("guard")
    assert text.startswith("⚠ Scam guard: CRITICAL") and "1930" in text and "warned out loud" in text
    assert "731904" not in text


def test_phone_guard_command_quiet(plugin):
    ps, _ = plugin
    assert ps.commands.handle("guard").startswith("Scam guard: ")


def test_own_alert_never_counts_as_a_signal(scam_plugin, monkeypatch):
    ps, _ = scam_plugin
    own = [{"packageName": "com.termux", "title": "Phone Senses: possible scam in progress",
            "content": "Stop screen sharing and uninstall the remote-access app now.", "when": None}]
    import time as _t
    own[0]["when"] = _t.strftime("%Y-%m-%d %H:%M:%S")
    monkeypatch.setattr(ps.tools, "fetch_notifications", lambda: own)
    monkeypatch.setattr(ps.tools, "fetch_sms", lambda *a, **k: [])
    monkeypatch.setattr(ps.client.PhoneClient, "get", lambda self, path, params=None, **kw: [])
    r = call(ps, "phone_scam_guard")
    assert r["level"] == "clear" and "remote_access" not in r["signals"]
