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
    assert len(run(ps, "phone_notifications", {"include_system": True})["notifications"]) == 9   # all mock notifications


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
    first = run(ps, "phone_money_sync", {"days": 30})   # 9 = 8 demo transactions + Spotify 12 days ago
    assert first["ok"] and first["parsed"] == 9 and first["new"] == 9
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
    assert sources == ["debit", "debit", "notification", "notification", "sms"]   # Swiggy + Amazon "out for delivery"
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
    assert first["new"] == 9 and second["new"] == 0
    assert run(ps, "phone_money_summary", {"period": "today", "direction": "credit"})["total_credit_rs"] == 1580.0


# --- bills, deliveries, subscriptions, battery watch -------------------------


def test_bills_from_mock_sms(plugin):
    ps, _ = plugin
    data = run(ps, "phone_bills")
    assert data["ok"] and [b["biller"] for b in data["bills"]] == [
        "ACT Fibernet", "Airtel", "BESCOM", "ICICI Bank credit card"]   # gas bill left out: a later SMS says paid
    assert [b["days_left"] for b in data["bills"]] == [-1, 2, 6, 12]
    assert data["overdue"] == 1 and data["total_due_rs"] == 1059 + 799 + 1240 + 4820
    assert data["bills"][3] == {**data["bills"][3], "kind": "credit_card", "amount_rs": 4820.0, "status": "upcoming"}
    soon = run(ps, "phone_bills", {"days_ahead": 7, "include_overdue": False})
    assert [b["biller"] for b in soon["bills"]] == ["Airtel", "BESCOM"]


def test_due_bills_paid_confirmation_and_old_undated(plugin):
    ps, _ = plugin
    now = int(dt.datetime.now().timestamp())

    def sms(sender, body, days_ago):
        return {"number": sender, "ts": now - days_ago * 86400, "_full_body": body}

    in3 = (dt.date.today() + dt.timedelta(days=3)).strftime("%d-%m-%y")
    act = sms("VM-ACTFBR", f"ACT Fibernet: your broadband bill of Rs 1,059.00 is due on {in3}.", 5)
    paid = sms("VM-ACTFBR", "Thank you for your payment of Rs 1,059.00 towards your ACT Fibernet broadband account.", 1)
    airtel = [sms("AX-AIRTEL", "Your Airtel postpaid bill of Rs 799 is due. Pay now.", 2),
              sms("AX-AIRTEL", "Your Airtel postpaid bill of Rs 650 is due. Pay now.", 40)]   # undated and old: dropped
    assert [b["biller"] for b in ps.tools.due_bills([act] + airtel)] == ["ACT Fibernet", "Airtel"]
    due = ps.tools.due_bills([act, paid] + airtel)
    assert [(b["biller"], b["amount_rs"], b["status"]) for b in due] == [("Airtel", 799.0, "no_date")]
    ago20, in10 = ((dt.date.today() + dt.timedelta(days=d)).strftime("%d-%m-%y") for d in (-20, 10))
    cycles = [sms("AX-AIRTEL", f"Your Airtel postpaid bill of Rs 650 is due on {ago20}.", 45),
              sms("AX-AIRTEL", f"Your Airtel postpaid bill of Rs 720 is due on {in10}.", 15),
              sms("AX-AIRTEL", "Reminder: your Airtel postpaid bill of Rs 720 is due. Pay now.", 3)]
    due = ps.tools.due_bills(cycles)   # this month's bill replaces last month's; the undated reminder keeps the date
    assert [(b["amount_rs"], b["days_left"]) for b in due] == [(720.0, 10)]


def test_deliveries_merge_sms_and_notifications(plugin):
    ps, _ = plugin
    data = run(ps, "phone_deliveries")
    assert data["ok"] and data["count"] == 5 and data["active"] == 3
    amazon = [d for d in data["deliveries"] if d["item"] == "Demo Phone Case"]
    assert len(amazon) == 1 and amazon[0] == {**amazon[0], "status": "out_for_delivery",
                                              "order_id": "403-1234567-1234567", "eta": "today by 8 PM"}
    statuses = {d["merchant"]: d["status"] for d in data["deliveries"] if d["merchant"] != "Amazon"}
    assert statuses == {"Swiggy": "out_for_delivery", "Delhivery": "out_for_delivery", "Flipkart": "delivered"}
    active = run(ps, "phone_deliveries", {"active_only": True})["deliveries"]
    assert len(active) == 3 and all(d["status"] == "out_for_delivery" for d in active)


def test_subscriptions_from_mock_debits(plugin):
    ps, _ = plugin
    data = run(ps, "phone_subscriptions")
    subs = {s["merchant"]: s for s in data["subscriptions"]}
    assert set(subs) == {"Netflix", "Spotify"} and data["monthly_total_rs"] == 218.0
    assert subs["Spotify"] == {**subs["Spotify"], "typical_amount_rs": 119.0, "cadence": "monthly", "charges": 3,
                               "status": "active"}
    assert subs["Netflix"]["next_expected"] > dt.date.today().isoformat()
    ps.settings["money_enabled"] = False
    assert run(ps, "phone_subscriptions")["error"] == "disabled"


def test_subscription_detection_rules(plugin):
    ps, _ = plugin
    find = ps.subscriptions.find
    today = dt.date(2026, 11, 8)

    def tx(party, rs, days_ago, channel="upi"):
        ts = int(dt.datetime.combine(today - dt.timedelta(days=days_ago), dt.time(9)).timestamp())
        return {"ts": ts, "amount_paise": int(rs * 100), "counterparty": party, "channel": channel, "direction": "debit"}

    txs = [tx("RENT LANDLORD", 15000, d) for d in (65, 35, 5)] + [tx("RENT LANDLORD", 900, 20)]   # outlier dropped
    txs += [tx("CHAI POINT", 60, d) for d in (30, 20, 10)]        # regular but not monthly: not a subscription
    txs += [tx("VIN*HOTSTAR", 299, 12)]                            # known service, one charge
    txs += [tx("ATM S1AW", 2000, d, "atm") for d in (60, 30)]      # cash withdrawals never count
    txs += [tx("gym.demo@okaxis", 1500, d) for d in (100, 70)]     # stopped two cycles ago
    subs = {s["merchant"]: s for s in find(txs, today)}
    assert set(subs) == {"RENT LANDLORD", "Disney+ Hotstar", "Gym"}
    assert subs["RENT LANDLORD"] == {**subs["RENT LANDLORD"], "cadence": "monthly", "charges": 3,
                                     "typical_amount_rs": 15000.0, "next_expected": "2026-12-03"}
    assert subs["Disney+ Hotstar"]["cadence"] == "unknown" and subs["Disney+ Hotstar"]["next_expected"] is None
    assert subs["Gym"]["status"] == "maybe_stopped"
    assert ps.subscriptions.monthly_total_rs(list(subs.values())) == 15000.0
    assert ps.subscriptions.add_month(dt.date(2027, 1, 31)) == dt.date(2027, 2, 28)


def _battery(app, level, status="DISCHARGING"):
    """Make the mock phone report this battery level (only termux-battery-status changes)."""
    real = type(app.runner).run.__get__(app.runner)

    def run(argv, timeout=15, stdin=None):
        if argv[0] == "termux-battery-status":
            app.runner.calls.append((list(argv), stdin))
            return json.dumps({"percentage": level, "status": status,
                               "plugged": "PLUGGED_AC" if status == "CHARGING" else "UNPLUGGED"})
        return real(argv, timeout, stdin)

    app.runner.run = run


def test_battery_watch_fires_once_and_rearms(plugin):
    ps, app = plugin
    app.limiter.allow = lambda *a, **k: True   # many quick checks; the rate limit is tested in test_helper
    rid = run(ps, "phone_watch_add", {"kind": "battery_below", "percent": 20})["id"]
    assert run(ps, "phone_watch_list")["rules"][0]["rule"] == "battery below 20%"
    fired = []
    for level in (30, 15, 12, 22, 25, 26, 14):
        _battery(app, level)
        data = run(ps, "phone_watch_check")
        assert data["checked"]["battery_percent"] == level
        fired += [(level, m["source"], m["rule_id"]) for m in data["matches"]]
    assert fired == [(15, "battery", rid), (14, "battery", rid)]   # re-armed only after rising above 25%
    _battery(app, 40)
    run(ps, "phone_watch_check")
    _battery(app, 10, "CHARGING")
    assert run(ps, "phone_watch_check")["matches"] == []          # plugged in: no alert
    _battery(app, 10)
    data = run(ps, "phone_watch_check", {"notify_phone": True})
    assert data["matches"][0]["text"].startswith("Phone battery is at 10%")
    notify = [argv for argv, _ in app.runner.calls if argv[0] == "termux-notification"]
    assert notify and "Phone Senses: battery below 20%" in notify[-1] and "Phone battery is at 10%. Plug it in soon." in notify[-1]


def test_battery_rule_validation(plugin):
    ps, _ = plugin
    for bad in ({}, {"percent": 0}, {"percent": 100}, {"percent": "low"}):
        assert run(ps, "phone_watch_add", {"kind": "battery_below", **bad})["error"] == "bad_request", bad


def test_brief_bills_and_deliveries(plugin):
    ps, _ = plugin
    data = run(ps, "phone_brief")
    assert [b["biller"] for b in data["bills_due_soon"]] == ["Airtel", "BESCOM"]
    assert {d["merchant"] for d in data["deliveries_today"]} == {"Swiggy", "Delhivery", "Amazon"}


def test_brief_sections_survive_errors(plugin, monkeypatch):
    ps, _ = plugin

    def boom(*a, **k):
        raise ps.client.PhoneError("timeout", "slow phone")

    monkeypatch.setattr(ps.tools.deliveries, "group_updates", boom)
    monkeypatch.setattr(ps.tools, "inbox_since", boom)
    data = run(ps, "phone_brief")
    assert data["ok"] and data["battery"]["percent"] == 76
    assert data["bills_due_soon"] == {"error": "timeout"} and data["deliveries_today"] == {"error": "timeout"}


def test_slash_bills_and_deliveries(plugin):
    ps, _ = plugin
    bills_text = ps.commands.handle("bills")
    assert bills_text.startswith("Bills due: Rs 7,918.00 in 4 bill(s)") and "overdue by 1 day(s)" in bills_text
    assert "ICICI" not in ps.commands.handle("bills 7")
    deliveries_text = ps.commands.handle("deliveries")
    assert deliveries_text.startswith("Deliveries (3 on the way):")
    assert "Amazon: out for delivery (Demo Phone Case, ETA today by 8 PM)" in deliveries_text
    assert "bills" in ps.commands.USAGE and "deliveries" in ps.commands.USAGE
