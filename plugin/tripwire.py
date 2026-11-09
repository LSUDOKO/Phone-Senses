"""Scam tripwire: spot a phone scam while it is happening, from several signals at once.

Indian phone frauds ("KYC update", "digital arrest", fake bank support) follow a sequence:

    unknown caller  ->  remote-access / screen-sharing app  ->  OTP SMS  ->  money leaves

No single message gives it away; the order and timing do. This module turns call-log entries,
notifications, SMS and parsed transactions into timeline events and assesses the latest window.
Pure functions only (no I/O); tools.py fetches the data and decides how to alert.
"""
from __future__ import annotations

import re

from .parsers import otp, scam

# Apps a scammer asks the victim to install so they can watch the screen and read OTPs.
REMOTE_APPS = {
    "com.anydesk.anydeskandroid": "AnyDesk",
    "com.teamviewer.quicksupport.market": "TeamViewer QuickSupport",
    "com.teamviewer.teamviewer.market.mobile": "TeamViewer",
    "com.teamviewer.host.market": "TeamViewer Host",
    "com.carriez.flutter_hbb": "RustDesk",
    "com.sand.airdroid": "AirDroid",
    "com.sand.airdroidbiz": "AirDroid Business",
    "com.zoho.assist.agent": "Zoho Assist",
    "com.splashtop.streamer.addon.knox": "Splashtop",
    "com.rsupport.mobizen.mirroring": "Mobizen",
    "net.screenmeet.support": "ScreenMeet",
}
REMOTE_TEXT = re.compile(
    r"\b(anydesk|teamviewer|quick ?support|rustdesk|airdroid|zoho assist|splashtop|screenmeet)\b|"
    r"screen (?:is being )?shar(?:e|ed|ing)|sharing your screen|screen ?cast(?:ing)?|"
    r"start(?:ed)? (?:recording or )?casting|remote (?:access|control|support|session)|"
    r"(?:is )?(?:viewing|controlling) (?:your|this) (?:screen|device)", re.IGNORECASE)
# The installer's "installed" notification, e.g. Play Store: "AnyDesk installed".
INSTALLED = re.compile(r"\binstalled\b", re.IGNORECASE)
# A UPI collect request: approving it *sends* money (the classic "enter PIN to receive" trick).
COLLECT = re.compile(r"collect request|requested (?:rs\.?|inr|₹) ?[\d,]+|has requested (?:money|a payment)|"
                     r"payment request (?:of|for)|request(?:ed)? you to pay|approve (?:the )?(?:payment )?request",
                     re.IGNORECASE)
CHAT_PACKAGES = {"com.whatsapp", "com.whatsapp.w4b", "org.telegram.messenger", "com.google.android.apps.messaging",
                 "com.google.android.gm", "com.instagram.android", "com.discord", "com.slack"}
LONG_CALL_SECONDS = 30
HELPLINE = "1930"
REPORT_URL = "https://cybercrime.gov.in"


def _seconds(duration) -> int:
    """'04:12' / '1:02:03' / '252' -> seconds."""
    text = str(duration or "").strip()
    if not text:
        return 0
    try:
        parts = [int(p) for p in text.split(":")]
    except ValueError:
        return 0
    total = 0
    for p in parts:
        total = total * 60 + p
    return total


def call_event(call: dict) -> dict | None:
    """An unsaved number that talked to the user (or rang them). Calls from contacts are ignored."""
    if call.get("name") or not call.get("ts"):
        return None
    ctype = str(call.get("type") or "").lower()
    if ctype not in ("incoming", "outgoing", "missed", "rejected"):
        return None
    secs = _seconds(call.get("duration"))
    number = str(call.get("number") or "")
    talked = ctype in ("incoming", "outgoing") and secs >= LONG_CALL_SECONDS
    detail = {"number": number, "type": ctype, "seconds": secs,
              "international": number.startswith("+") and not number.startswith("+91")}
    return {"kind": "unknown_call" if talked else "unknown_ring", "ts": call["ts"], "detail": detail}


def notification_events(item: dict) -> list[dict]:
    """item: normalised notification {"app", "package", "title", "text", "ts"}."""
    if not item.get("ts"):
        return []
    pkg = item.get("package") or ""
    text = f"{item.get('title') or ''} {item.get('text') or ''}"
    out = []
    app = REMOTE_APPS.get(pkg)
    # Chat apps only count via the app itself: a friend writing "anydesk" is not a session.
    hit = None if pkg in CHAT_PACKAGES else REMOTE_TEXT.search(text)
    if app or hit:
        out.append({"kind": "remote_access", "ts": item["ts"],
                    "detail": {"app": app or (hit.group(0).strip() if hit and hit.group(1) else item.get("app")),
                               "state": "installed" if INSTALLED.search(text) else "active",
                               "title": item.get("title")}})
    if COLLECT.search(text):
        out.append({"kind": "collect_request", "ts": item["ts"], "detail": {"app": item.get("app")}})
    return out


def sms_events(m: dict) -> list[dict]:
    """m: normalised SMS with "_full_body". The OTP itself never leaves this function."""
    if not m.get("ts"):
        return []
    body = m.get("_full_body") or m.get("body") or ""
    out = []
    if otp.find_otps(body):
        out.append({"kind": "otp", "ts": m["ts"], "detail": {"from": m.get("from")}})
    if COLLECT.search(body):
        out.append({"kind": "collect_request", "ts": m["ts"], "detail": {"from": m.get("from")}})
    risk = scam.score(body)
    if risk["level"] == "high":
        out.append({"kind": "scam_text", "ts": m["ts"], "detail": {"from": m.get("from"), "why": risk["reasons"][:2]}})
    return out


def debit_event(tx: dict) -> dict | None:
    if tx.get("direction") != "debit" or not tx.get("ts"):
        return None
    return {"kind": "debit", "ts": tx["ts"],
            "detail": {"amount_paise": int(tx.get("amount_paise") or 0), "counterparty": tx.get("counterparty"),
                       "channel": tx.get("channel")}}


LABELS = {
    "unknown_call": "Call with an unsaved number",
    "unknown_ring": "Missed or rejected call from an unsaved number",
    "remote_access": "Screen-sharing / remote-access app",
    "otp": "OTP SMS arrived",
    "collect_request": "UPI payment (collect) request",
    "scam_text": "Scam-style SMS",
    "debit": "Money debited",
}


def assess(events: list[dict], now: int, window_minutes: int = 30) -> dict:
    """Assess the events of the last ``window_minutes``.

    Levels: "clear" (nothing), "low" (one ordinary signal: an OTP alone is normal), "high" (a
    pattern is forming: warn now) and "critical" (the screen is being shared while codes or money
    move, or money left after a stranger's call).
    """
    since = now - window_minutes * 60
    recent = sorted((e for e in events if since <= e["ts"] <= now + 60), key=lambda e: e["ts"])
    kinds = {e["kind"] for e in recent}
    call = "unknown_call" in kinds
    stranger = call or "unknown_ring" in kinds
    remote = "remote_access" in kinds
    money_move = bool(kinds & {"debit", "collect_request"})
    codes = "otp" in kinds
    scam_text = "scam_text" in kinds

    if remote and (codes or money_move) or (call and money_move and (codes or remote or scam_text)):
        level = "critical"
    elif remote or (call and (codes or money_move or scam_text)) or (stranger and scam_text and (codes or money_move)):
        level = "high"
    elif recent:
        level = "low"
    else:
        level = "clear"

    advice: list[str] = []
    if level in ("high", "critical"):
        if stranger:
            advice.append("If you are on a call with someone claiming to be a bank, police, courier or KYC team: hang up.")
        advice.append("Never share an OTP, UPI PIN, CVV or your screen with anyone. Banks never ask for them.")
        if remote:
            advice.append("Stop screen sharing and uninstall the remote-access app now.")
        if "collect_request" in kinds:
            advice.append("Decline the payment request: entering your UPI PIN sends money, it never receives it.")
    if level == "critical":
        advice.append(f"If money left your account, call {HELPLINE} (National Cyber Crime Helpline) and your bank "
                      f"right away to block UPI and cards, and report at {REPORT_URL}.")

    timeline = [{**{k: v for k, v in e["detail"].items() if v not in (None, "", False)},
                 "kind": e["kind"], "what": LABELS[e["kind"]], "ts": e["ts"]} for e in recent]
    incident = f"{recent[0]['ts']}" if level in ("high", "critical") else None
    return {"level": level, "alert": level in ("high", "critical"), "signals": sorted(kinds),
            "timeline": timeline, "advice": advice, "incident": incident, "window_minutes": window_minutes}


def spoken_warning(result: dict) -> str:
    """Short, calm text for the phone to say out loud."""
    if result["level"] == "critical":
        extra = (" Stop screen sharing." if "remote_access" in result["signals"] else "") + \
                f" If money left your account, call {' '.join(HELPLINE)} and your bank now."
        return "Warning. This looks like a scam in progress. Do not share any O T P or U P I PIN." + extra
    return ("Careful. This looks like a scam call. Never share an O T P, PIN or your screen. "
            "Banks never ask for them. Hang up if in doubt.")
