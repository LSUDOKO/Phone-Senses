"""pre_tool_call hook: every action that sends, calls, photographs or reveals asks the user first.

Returning ``{"action": "approve", "message": ..., "rule_key": ...}`` makes Hermes show its own
approval prompt (once / session / always / deny). Under cron or a gateway with nobody to answer,
Hermes fails closed. There is no auto-approve path in this plugin.
"""
from __future__ import annotations

from typing import Any

NEEDS_APPROVAL = frozenset({"phone_sms_send", "phone_call", "phone_photo", "phone_otp_reveal"})


def summary(tool_name: str, args: dict) -> str:
    """Human-readable description of exactly what the tool call will do."""
    if tool_name == "phone_sms_send":
        to, text = str(args.get("to") or "").strip(), str(args.get("text") or "")
        return f'Send SMS from your phone to {to or "(no recipient)"} ({len(text)} chars): "{text}"'
    if tool_name == "phone_call":
        return f"Place a phone call from your SIM to {str(args.get('to') or '').strip() or '(no number)'}"
    if tool_name == "phone_photo":
        return f"Take a photo with the phone's {args.get('camera') or 'back'} camera and show it to the assistant"
    if tool_name == "phone_otp_reveal":
        return "Reveal the latest one-time code (OTP) from your phone to the assistant"
    return f"Run {tool_name}"


def on_pre_tool_call(tool_name: str = "", args: dict | None = None, task_id: str = "", **kwargs: Any):
    if tool_name not in NEEDS_APPROVAL:
        return None
    return {"action": "approve", "message": summary(tool_name, args or {}), "rule_key": tool_name}
