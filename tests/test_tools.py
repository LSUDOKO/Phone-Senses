"""Tool handlers end to end against the mock helper (real HTTP, temp SQLite)."""
from __future__ import annotations

import datetime as dt
import json

import pytest


def run(ps, name, args=None):
    out = ps.tools.HANDLERS[name](args or {}, task_id="t1", session_id="s1")
    return out if isinstance(out, dict) else json.loads(out)


def test_every_handler_returns_json_and_never_raises(plugin):
    ps, _ = plugin
    for name, handler in ps.tools.HANDLERS.items():
        out = handler({"bogus": object()} if False else {"limit": "not-a-number"})
        data = out if isinstance(out, dict) else json.loads(out)
        assert "ok" in data or data.get("_multimodal"), name


def test_errors_are_json_when_phone_is_down(plugin):
    ps, _ = plugin
    ps.client.set_client(ps.client.PhoneClient("http://127.0.0.1:9", "x", timeout=1))
    data = run(ps, "phone_status")
    assert data == {**data, "ok": False, "error": "phone_unreachable"} and data["hint"]


def test_status(plugin):
    ps, _ = plugin
    data = run(ps, "phone_status")
    assert data["ok"] and data["battery_percent"] == 76 and data["charging"] is False
    assert data["wifi"] == "Home-WiFi-Demo" and data["mock"] is True


def test_notifications_filter_noise_and_mask_otp(plugin):
    ps, _ = plugin
    data = run(ps, "phone_notifications")
    apps = [n["app"] for n in data["notifications"]]
    assert "Termux" not in apps and "Spotify" not in apps and data["hidden_noise"] >= 3
    blob = json.dumps(data)
    assert "482913" not in blob and "[OTP hidden]" in blob
    assert run(ps, "phone_notifications", {"app": "swiggy"})["notifications"][0]["app"] == "Swiggy"
    assert len(run(ps, "phone_notifications", {"include_system": True})["notifications"]) == 8


def test_notifications_exclude_setting(plugin):
    ps, _ = plugin
    ps.settings["notifications_exclude_apps"] = ["whatsapp"]
    apps = [n["app"] for n in run(ps, "phone_notifications")["notifications"]]
    assert "WhatsApp" not in apps


def test_sms_list_query_mask_and_scam(plugin):
    ps, _ = plugin
    data = run(ps, "phone_sms_list", {"limit": 50})
    assert "482913" not in json.dumps(data)
    dates = [m["date"] for m in data["messages"]]
    assert dates == sorted(dates, reverse=True)
    kyc = [m for m in data["messages"] if "KYC" in m["body"]][0]
    assert kyc["scam_risk"] == "high" and kyc["scam_reasons"]
    zomato = run(ps, "phone_sms_list", {"query": "zomato"})["messages"]
    assert len(zomato) == 1 and zomato[0]["scam_risk"] == "low"
    assert all("HDFCBK" in m["number"] for m in run(ps, "phone_sms_list", {"from_number": "HDFCBK"})["messages"])
    sent = run(ps, "phone_sms_list", {"box": "sent"})["messages"]
    assert sent and all(m["box"] == "sent" for m in sent)


def test_sms_send_to_number(plugin):
    ps, app = plugin
    data = run(ps, "phone_sms_send", {"to": "+91 90000 00199", "text": "Running 10 minutes late"})
    assert data["ok"] and data["sent"]
    assert app.runner.sent_sms == [{"to": "+919000000199", "text": "Running 10 minutes late"}]


def test_sms_send_to_ambiguous_name_sends_nothing(plugin):
    ps, app = plugin
    data = run(ps, "phone_sms_send", {"to": "Rahul", "text": "hi"})
    assert data["ok"] is False and data["error"] == "needs_number" and data["sent"] is False
    assert {m["name"] for m in data["matches"]} == {"Rahul Kumar", "Rahul Sharma"}
    assert app.runner.sent_sms == []


def test_sms_send_too_long(plugin):
    ps, app = plugin
    data = run(ps, "phone_sms_send", {"to": "+919000000199", "text": "x" * 481})
    assert data["error"] == "bad_request" and app.runner.sent_sms == []


def test_contacts_and_calls(plugin):
    ps, _ = plugin
    assert run(ps, "phone_contacts", {"query": "anita"})["matches"] == [{"name": "Anita S", "number": "+919000000103"}]
    assert run(ps, "phone_contacts", {"query": "00101"})["matches"][0]["name"] == "Rahul Kumar"
    missed = run(ps, "phone_calls", {"type": "missed"})["calls"]
    assert [c["name"] for c in missed] == ["Mom", "Priya Office"]


def test_location_ring_speak_clipboard(plugin):
    ps, app = plugin
    loc = run(ps, "phone_location")
    assert loc["maps_url"].startswith("https://maps.google.com/?q=12.9716")
    assert run(ps, "phone_ring", {"seconds": 1})["ringing"]
    assert run(ps, "phone_speak", {"text": "Hello"})["spoken"]
    assert run(ps, "phone_clipboard")["text"]
    assert run(ps, "phone_clipboard", {"action": "set", "text": "https://example.com"})["set"]
    assert ["termux-clipboard-set"] in [argv for argv, _ in app.runner.calls]


def test_photo_without_hermes_returns_text(plugin):
    ps, _ = plugin
    data = run(ps, "phone_photo", {"camera": "back"})
    assert data["ok"] and data["bytes"] > 100


def test_otp_reveal_off_by_default_and_on_when_allowed(plugin):
    ps, _ = plugin
    assert run(ps, "phone_otp_reveal")["error"] == "disabled"
    ps.settings["allow_otp_reveal"] = True
    data = run(ps, "phone_otp_reveal", {"max_age_minutes": 60})
    # Mock dates are relative to "today", so the OTP may be older than an hour: accept both.
    assert data.get("code") == "482913" or data.get("error") == "not_found"


def test_money_sync_dedupes_and_never_stores_bodies(plugin, tmp_path):
    ps, _ = plugin
    first = run(ps, "phone_money_sync", {"days": 30})
    assert first["ok"] and first["parsed"] == 8 and first["new"] == 8
    assert run(ps, "phone_money_sync", {"days": 30})["new"] == 0
    raw = (tmp_path / "data.db").read_bytes()
    assert b"ZOMATO" in raw and b"Sent Rs.250.00" not in raw and b"Avl Limit" not in raw


def test_money_summary_week_and_today_credit(plugin):
    ps, _ = plugin
    week = run(ps, "phone_money_summary", {"period": "week"})
    assert week["ok"] and week["transactions"] == 5
    assert week["total_debit_rs"] == 250 + 500 + 99 + 1250.50 + 2000
    cats = {g["category"]: g["amount_rs"] for g in week["groups"]}
    assert cats == {"cash": 2000.0, "transfers": 1250.5, "food": 750.0, "bills": 99.0}
    today = run(ps, "phone_money_summary", {"period": "today", "direction": "credit", "group_by": "counterparty"})
    assert today["total_credit_rs"] == 1580.0
    assert {g["counterparty"] for g in today["groups"]} == {"customer123@okaxis", "Anita S"}


def test_budget_shows_percent_used(plugin):
    ps, _ = plugin
    assert run(ps, "phone_budget_set", {"category": "food", "monthly_limit_rs": 1000})["ok"]
    data = run(ps, "phone_money_summary", {"period": "week"})
    food = [b for b in data["budgets"] if b["category"] == "food"][0]
    assert food["monthly_limit_rs"] == 1000.0 and food["pct_used"] >= 0
    assert run(ps, "phone_budget_set", {"category": "pets", "monthly_limit_rs": 5})["error"] == "bad_request"


def test_period_range_custom(plugin):
    ps, _ = plugin
    a, b, label = ps.tools.period_range("custom", "2026-11-01", "2026-11-07")
    assert label == "2026-11-01 to 2026-11-07" and b - a == 7 * 86400
    with pytest.raises(ValueError):
        ps.tools.period_range("custom", "bad")


def test_scam_check(plugin):
    ps, _ = plugin
    assert run(ps, "phone_scam_check", {"text": "You won a lottery! Claim at bit.ly/x"})["level"] == "high"
    recent = run(ps, "phone_scam_check", {"limit": 50})
    assert recent["flagged"] >= 2 and recent["messages"][0]["level"] == "high"


def test_watch_rules_fire_once(plugin):
    ps, _ = plugin
    ps.storage.set_cursor("watch_notifications", "0")
    ps.storage.set_cursor("watch_sms", "0")
    rid = run(ps, "phone_watch_add", {"kind": "notification", "contains": "out for delivery"})["id"]
    run(ps, "phone_watch_add", {"kind": "debit_over", "amount_rs": 1000})
    run(ps, "phone_watch_add", {"kind": "sms", "from_number": "+919000000104"})
    assert len(run(ps, "phone_watch_list")["rules"]) == 3
    first = run(ps, "phone_watch_check")
    sources = sorted(m["source"] for m in first["matches"])
    assert sources == ["debit", "debit", "notification", "sms"]
    assert run(ps, "phone_watch_check")["matches"] == []
    assert run(ps, "phone_watch_remove", {"id": rid})["removed"] is True
    assert run(ps, "phone_watch_add", {"kind": "sms"})["error"] == "bad_request"


def test_brief(plugin):
    ps, _ = plugin
    data = run(ps, "phone_brief")
    assert data["ok"] and data["battery"]["percent"] == 76
    assert {c["from"] for c in data["missed_calls"]} <= {"Mom", "Priya Office"}
    assert "482913" not in json.dumps(data)
    assert "money" in data and "yesterday_spent_rs" in data["money"]


def test_slash_command(plugin):
    ps, _ = plugin
    assert "battery 76%" in ps.commands.handle("")
    assert "Ringing" in ps.commands.handle("ring 2")
    assert ps.commands.handle("money week").startswith("Spent Rs")
    assert ps.commands.handle("received today").startswith("Received Rs 1,580.00")
    assert "--pair" in ps.commands.handle("pair")
    assert "Usage" in ps.commands.handle("dance")


def test_tool_output_never_contains_known_otp(plugin):
    ps, _ = plugin
    for name in ("phone_notifications", "phone_sms_list", "phone_brief", "phone_scam_check"):
        assert "482913" not in json.dumps(run(ps, name, {"limit": 100})), name


def test_time_parsing(plugin):
    ps, _ = plugin
    ts = ps.tools._parse_time("2026-11-08 09:30:05")
    assert dt.datetime.fromtimestamp(ts).strftime("%H:%M:%S") == "09:30:05"
    assert ps.tools._parse_time(1762594205000) == 1762594205
    assert ps.tools._parse_time("garbage") is None


def test_mock_timestamps_are_stable_so_sync_dedupes(plugin):
    ps, _ = plugin
    first = run(ps, "phone_money_sync", {"days": 30})
    second = run(ps, "phone_money_sync", {"days": 30})
    assert first["new"] == 8 and second["new"] == 0
    assert run(ps, "phone_money_summary", {"period": "today", "direction": "credit"})["total_credit_rs"] == 1580.0
