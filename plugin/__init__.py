"""Phone Senses: give Hermes the senses of your own Android phone through Termux:API.

The plugin talks only to the user's own phone helper (``phone_helper/helper.py`` running in
Termux) over an HMAC-signed HTTP API. ``register()`` does no I/O: settings, secrets and storage
are read lazily when a tool runs.
"""
from __future__ import annotations

import logging
from pathlib import Path

from . import approvals, client, commands, schemas, tools

log = logging.getLogger("phone_senses")

TOOLSET = "phone-senses"
SKILL_PATH = Path(__file__).resolve().parent / "skills" / "phone-senses" / "SKILL.md"
SKILL_DESCRIPTION = ("How to use the Phone Senses tools: reading notifications and SMS, the money "
                     "tracker, bills, subscriptions and deliveries, sending with approval, scam checks "
                     "and privacy etiquette.")

# Tool name -> schema, in the order shown to the model.
TOOL_SCHEMAS = {
    "phone_status": schemas.PHONE_STATUS,
    "phone_notifications": schemas.PHONE_NOTIFICATIONS,
    "phone_sms_list": schemas.PHONE_SMS_LIST,
    "phone_sms_send": schemas.PHONE_SMS_SEND,
    "phone_calls": schemas.PHONE_CALLS,
    "phone_contacts": schemas.PHONE_CONTACTS,
    "phone_location": schemas.PHONE_LOCATION,
    "phone_ring": schemas.PHONE_RING,
    "phone_speak": schemas.PHONE_SPEAK,
    "phone_clipboard": schemas.PHONE_CLIPBOARD,
    "phone_photo": schemas.PHONE_PHOTO,
    "phone_call": schemas.PHONE_CALL,
    "phone_otp_reveal": schemas.PHONE_OTP_REVEAL,
    "phone_money_sync": schemas.PHONE_MONEY_SYNC,
    "phone_money_summary": schemas.PHONE_MONEY_SUMMARY,
    "phone_budget_set": schemas.PHONE_BUDGET_SET,
    "phone_subscriptions": schemas.PHONE_SUBSCRIPTIONS,
    "phone_bills": schemas.PHONE_BILLS,
    "phone_deliveries": schemas.PHONE_DELIVERIES,
    "phone_scam_check": schemas.PHONE_SCAM_CHECK,
    "phone_watch_add": schemas.PHONE_WATCH_ADD,
    "phone_watch_list": schemas.PHONE_WATCH_LIST,
    "phone_watch_remove": schemas.PHONE_WATCH_REMOVE,
    "phone_watch_check": schemas.PHONE_WATCH_CHECK,
    "phone_brief": schemas.PHONE_BRIEF,
}


def _register_skill(ctx) -> None:
    if not SKILL_PATH.is_file():
        return
    try:
        ctx.register_skill("phone-senses", SKILL_PATH, description=SKILL_DESCRIPTION)
    except TypeError:   # older Hermes builds take only (name, path)
        ctx.register_skill("phone-senses", SKILL_PATH)


def register(ctx) -> None:
    client.configure(ctx)
    for name, schema in TOOL_SCHEMAS.items():
        ctx.register_tool(name=name, toolset=TOOLSET, schema=schema, handler=tools.HANDLERS[name],
                          emoji="📱")
    ctx.register_hook("pre_tool_call", approvals.on_pre_tool_call)
    ctx.register_command("phone", commands.handle,
                         description="Phone Senses: status, ring, money, bills, deliveries, brief, pair",
                         args_hint="[status|ring|money|received|bills|deliveries|brief|pair]")
    try:
        _register_skill(ctx)
    except Exception as exc:   # a missing skill must not stop the tools from loading
        log.warning("phone-senses: could not register the skill: %s", exc)
