"""OTP masking, money parsing and scam scoring against the synthetic fixtures."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from phone_senses.parsers import money, otp, scam

FIX = Path(__file__).parent / "fixtures"
MONEY = json.loads((FIX / "sms_money.json").read_text(encoding="utf-8"))
SCAM = json.loads((FIX / "sms_scam.json").read_text(encoding="utf-8"))


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
