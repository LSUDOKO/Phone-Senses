"""OTP masking, money parsing and scam scoring against the synthetic fixtures."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from phone_senses.parsers import bills, deliveries, money, otp, scam

FIX = Path(__file__).parent / "fixtures"
MONEY = json.loads((FIX / "sms_money.json").read_text(encoding="utf-8"))
SCAM = json.loads((FIX / "sms_scam.json").read_text(encoding="utf-8"))
BILLS = json.loads((FIX / "sms_bills.json").read_text(encoding="utf-8"))
DELIVERIES = json.loads((FIX / "sms_deliveries.json").read_text(encoding="utf-8"))
BILL_TS = int(dt.datetime.strptime(BILLS["sms_date"] + " 10:00", "%Y-%m-%d %H:%M").timestamp())


@pytest.mark.parametrize("text, expected", [
    ("Your OTP is 482913. Do not share.", "Your OTP is [OTP hidden]. Do not share."),
    ("482913 is your verification code for Swiggy", "[OTP hidden] is your verification code for Swiggy"),
    ("Use code 7781 to log in", "Use code [OTP hidden] to log in"),
    ("G-551234 is your Google verification code.", "G-[OTP hidden] is your Google verification code."),
    ("Your one-time password: 90817265", "Your one-time password: [OTP hidden]"),
])
def test_otp_masked(text, expected):
    assert otp.mask_text(text) == expected


@pytest.mark.parametrize("text", [
    "Rs.1250 debited on 08/11/26",
    "Order #4829135 shipped",
    "Call 1800 000 0003",
    "Meeting at 14:30 in room 2026",
    "INR 4500 sent, your code word is 'blue'",
])
def test_otp_untouched(text):
    assert otp.mask_text(text) == text


def test_mask_obj_nested():
    data = {"a": ["Your OTP is 123456", {"b": "PIN 4321 for card"}], "n": 5}
    assert otp.mask_obj(data) == {"a": ["Your OTP is [OTP hidden]", {"b": "PIN [OTP hidden] for card"}], "n": 5}


def test_find_otps():
    assert otp.find_otps("482913 is your OTP. Rs 250 txn.") == ["482913"]


@pytest.mark.parametrize("case", MONEY["debits"], ids=lambda c: c[0])
def test_debits(case):
    _, sender, body, expected = case
    tx = money.parse(sender, 1_762_600_000, body)
    assert tx is not None and tx.direction == "debit"
    for key, value in expected.items():
        assert getattr(tx, key) == value, key


@pytest.mark.parametrize("case", MONEY["credits"], ids=lambda c: c[0])
def test_credits(case):
    _, sender, body, expected = case
    tx = money.parse(sender, 1_762_600_000, body)
    assert tx is not None and tx.direction == "credit"
    for key, value in expected.items():
        assert getattr(tx, key) == value, key


@pytest.mark.parametrize("case", MONEY["ignored"], ids=lambda c: c[0])
def test_ignored(case):
    _, sender, body = case
    assert money.parse(sender, 1_762_600_000, body) is None


def test_id_is_hash_not_body():
    tx = money.parse("AX-HDFCBK", 1, MONEY["debits"][0][2])
    assert len(tx.id) == 32 and "ZOMATO" not in tx.id
    assert "body" not in tx.to_dict()


@pytest.mark.parametrize("body", SCAM["high"])
def test_scam_high(body):
    result = scam.score(body)
    assert result["level"] == "high", result


@pytest.mark.parametrize("body", [c[2] for c in MONEY["debits"] + MONEY["credits"]] + SCAM["low_extra"])
def test_normal_not_flagged(body):
    result = scam.score(body)
    assert result["level"] == "low", result


@pytest.mark.parametrize("case", BILLS["bills"], ids=lambda c: c[0])
def test_bills(case):
    _, sender, body, expected = case
    bill = bills.parse(sender, BILL_TS, body)
    assert bill is not None
    for key, value in expected.items():
        assert bill[key] == value, key


@pytest.mark.parametrize("case", BILLS["paid"], ids=lambda c: c[0])
def test_bill_payment_confirmations(case):
    _, sender, body, biller = case
    assert bills.paid_biller(sender, body) == biller and bills.parse(sender, BILL_TS, body) is None


@pytest.mark.parametrize("case", BILLS["ignored"], ids=lambda c: c[0])
def test_bills_ignored(case):
    _, sender, body = case
    assert bills.parse(sender, BILL_TS, body) is None


def test_bill_due_date_year_rollover():
    dec28 = int(dt.datetime(2026, 12, 28, 10).timestamp())
    assert bills.due_date("Your bill is due on 05 Jan. Pay soon", dec28) == "2027-01-05"
    assert bills.due_date("Your bill is due on 15 Nov", BILL_TS) == "2026-11-15"
    assert bills.due_date("Pay by 31/04/26 please", BILL_TS) is None   # no such date: None, never a crash


def test_bill_sms_are_not_transactions():
    for _, sender, body, _ in BILLS["bills"]:
        assert money.parse(sender, BILL_TS, body) is None, body


@pytest.mark.parametrize("case", DELIVERIES["parsed"], ids=lambda c: c[0])
def test_deliveries(case):
    _, sender, text, expected = case
    update = deliveries.parse(sender, text)
    assert update is not None
    for key, value in expected.items():
        assert update[key] == value, key


@pytest.mark.parametrize("case", DELIVERIES["ignored"], ids=lambda c: c[0])
def test_deliveries_ignored(case):
    _, sender, text = case
    assert deliveries.parse(sender, text) is None


def test_delivery_updates_group_by_order():
    p = {c[0]: {**deliveries.parse(c[1], c[2]), "ts": i} for i, c in enumerate(DELIVERIES["parsed"])}
    shipped, ofd, usb = p["D1"], {**p["D2"], "ts": 100}, {**p["D6"], "ts": 50}
    groups = deliveries.group_updates([ofd, usb, shipped])
    assert [(g["item"], g["status"]) for g in groups] == [("Demo Phone Case", "out_for_delivery"),
                                                         ("Demo USB-C cable", "delivered")]
    food = [{"merchant": "Swiggy", "status": s, "item": None, "order_id": None, "eta": None, "ts": t}
            for t, s in enumerate(["ordered", "out_for_delivery", "delivered", "ordered"])]
    assert [g["status"] for g in deliveries.group_updates(food)] == ["delivered", "ordered"]   # 2nd order is new
