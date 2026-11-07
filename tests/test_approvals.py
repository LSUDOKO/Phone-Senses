"""The approval hook must cover every tool that sends, calls, photographs or reveals."""
from __future__ import annotations

import re

import phone_senses
from phone_senses import approvals


def test_sensitive_tools_need_approval():
    for name in ("phone_sms_send", "phone_call", "phone_photo", "phone_otp_reveal"):
        result = approvals.on_pre_tool_call(tool_name=name, args={"to": "+919000000101", "text": "hi"})
        assert result["action"] == "approve" and result["rule_key"] == name and result["message"]


def test_sms_message_shows_exact_number_and_full_text():
    text = "Running 10 minutes late, start without me. " * 5
    msg = approvals.on_pre_tool_call(tool_name="phone_sms_send",
                                     args={"to": "+919000000101", "text": text})["message"]
    assert "+919000000101" in msg and text in msg


def test_name_recipient_still_asks():
    msg = approvals.on_pre_tool_call(tool_name="phone_sms_send", args={"to": "Rahul", "text": "hi"})
    assert msg["action"] == "approve" and "Rahul" in msg["message"]


def test_other_tools_pass_through():
    for name in phone_senses.TOOL_SCHEMAS:
        if name not in approvals.NEEDS_APPROVAL:
            assert approvals.on_pre_tool_call(tool_name=name, args={}) is None
    assert approvals.on_pre_tool_call(tool_name="terminal", args={}) is None


def test_no_risky_tool_slips_past_the_hook():
    risky = re.compile(r"send|call$|photo|otp|dial|camera|transmit", re.I)
    for name in phone_senses.TOOL_SCHEMAS:
        if risky.search(name) and name not in ("phone_calls",):
            assert name in approvals.NEEDS_APPROVAL, f"{name} must go through the approval hook"


def test_hook_accepts_extra_kwargs():
    assert approvals.on_pre_tool_call(tool_name="phone_call", args={"to": "1"}, task_id="t",
                                      session_id="s", future_field=1)["action"] == "approve"
