"""Tool handlers. Each returns a JSON string (or a multimodal dict for photos) and never raises.

Every result passes through OTP masking before it reaches the model, except the one field
``phone_otp_reveal`` returns after the user approved it.
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import logging
import re
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable

from . import client, storage, watch
from .client import PhoneError
from .parsers import money, otp, scam

log = logging.getLogger("phone_senses")

PHONE_RE = re.compile(r"^\+?[0-9]{6,15}$")
SMS_MAX = 480
BODY_CAP = 500
CATEGORIES = ("food", "travel", "shopping", "bills", "transfers", "cash", "other")

SYSTEM_PACKAGES = {
    "android", "com.android.systemui", "com.termux", "com.termux.api", "com.termux.boot",
    "com.android.providers.downloads", "com.google.android.gms", "com.android.vending",
    "com.android.settings", "com.android.phone", "com.android.server.telecom", "com.android.bluetooth",
    "com.miui.securitycenter", "com.coloros.safecenter", "com.samsung.android.lool",
    "com.tailscale.ipn",
}
MEDIA_PACKAGES = {
    "com.spotify.music", "com.google.android.apps.youtube.music", "com.google.android.youtube",
    "com.jio.media.jiobeats", "com.gaana", "in.startv.hotstar", "com.amazon.mp3", "com.wynk.music",
    "com.apple.android.music", "app.revanced.android.youtube",
}
NOISE_TITLES = re.compile(r"usb debugging|charging|battery is|running in the background|is running|"
                          r"wireless debugging|vpn (?:is )?(?:active|connected)|screen ?shot|"
                          r"syncing|downloading|uploading", re.IGNORECASE)
APP_NAMES = {
    "com.whatsapp": "WhatsApp", "com.whatsapp.w4b": "WhatsApp Business", "org.telegram.messenger": "Telegram",
    "com.google.android.apps.messaging": "Messages", "com.google.android.gm": "Gmail",
    "in.swiggy.android": "Swiggy", "com.application.zomato": "Zomato", "in.amazon.mShop.android.shopping": "Amazon",
    "com.flipkart.android": "Flipkart", "net.one97.paytm": "Paytm", "com.phonepe.app": "PhonePe",
    "com.google.android.apps.nbu.paisa.user": "Google Pay", "com.instagram.android": "Instagram",
    "com.slack": "Slack", "com.microsoft.teams": "Teams", "com.linkedin.android": "LinkedIn",
    "com.ubercab": "Uber", "com.olacabs.customer": "Ola", "com.spotify.music": "Spotify",
    "com.google.android.calendar": "Calendar", "com.android.chrome": "Chrome",
    "com.google.android.googlequicksearchbox": "Google", "com.discord": "Discord",
    "com.google.android.apps.photos": "Google Photos", "com.truecaller": "Truecaller",
}

# ---------------------------------------------------------------------------
# Result helpers


def _dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def tool(fn: Callable[[dict], Any] | None = None, *, mask: bool = True):
    """Wrap a handler: catch everything, return JSON, mask OTPs, accept Hermes kwargs."""
    def deco(inner: Callable[[dict], Any]):
        @functools.wraps(inner)
        def handler(args: dict | None = None, **kwargs) -> Any:
            try:
                result = inner(dict(args or {}))
            except PhoneError as exc:
                result = exc.to_result()
            except ValueError as exc:
                result = {"ok": False, "error": "bad_request", "message": str(exc)[:300]}
            except Exception as exc:   # never raise into Hermes; never include message bodies
                log.warning("phone-senses: %s failed: %s", inner.__name__, type(exc).__name__)
                result = {"ok": False, "error": "internal", "message": f"unexpected error ({type(exc).__name__})"}
            if mask:
                result = otp.mask_obj(result)
            return _dumps(result)
        return handler
    return deco(fn) if fn else deco


def _ok(**data: Any) -> dict:
    return {"ok": True, **data}


def _int_arg(args: dict, key: str, default: int, lo: int, hi: int) -> int:
    value = args.get(key)
    if value is None or value == "":
        return default
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be an integer")
    return max(lo, min(hi, n))


def _bool_setting(key: str, default: bool) -> bool:
    value = client.setting(key, default)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _parse_time(value: Any) -> int | None:
    """Termux dates are local 'YYYY-MM-DD HH:MM:SS' strings; some fields are epoch ms."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return int(value / 1000) if value > 10**11 else int(value)
    text = str(value).strip()
    if text.isdigit():
        return _parse_time(int(text))
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return int(time.mktime(time.strptime(text[:19], fmt)))
        except ValueError:
            continue
    return None


def _fmt_time(ts: int | None) -> str | None:
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else None


def _ssid(value: Any) -> str | None:
    """Android reports '<unknown ssid>' when not on Wi-Fi (or without location permission)."""
    text = str(value or "").strip().strip('"')
    return None if not text or text.lower() == "<unknown ssid>" else text


def _rs(paise: int) -> float:
    return round(paise / 100, 2)


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def _cap(text: Any, n: int = BODY_CAP) -> str:
    text = str(text or "")
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------------------------------------------------------------------------
# Normalisers for helper data


def app_name(package: str) -> str:
    if package in APP_NAMES:
        return APP_NAMES[package]
    tail = (package or "").split(".")[-1]
    return tail[:1].upper() + tail[1:] if tail else "Unknown"


def _is_noise(n: dict) -> bool:
    pkg = n.get("packageName") or ""
    if not str(n.get("title") or "").strip() and not str(n.get("content") or "").strip():
        return True   # empty placeholders (e.g. a search widget) carry no information
    return pkg in SYSTEM_PACKAGES or pkg in MEDIA_PACKAGES or bool(NOISE_TITLES.search(n.get("title") or ""))


def _norm_notification(n: dict) -> dict:
    pkg = str(n.get("packageName") or "")
    ts = _parse_time(n.get("when"))
    return {"app": app_name(pkg), "package": pkg, "title": _cap(n.get("title"), 200),
            "text": _cap(n.get("content"), BODY_CAP), "time": _fmt_time(ts), "ts": ts}


def _norm_sms(m: dict) -> dict:
    ts = _parse_time(m.get("received") or m.get("date"))
    number = str(m.get("number") or m.get("address") or "")
    return {"from": m.get("sender") or number, "number": number, "date": _fmt_time(ts), "ts": ts,
            "body": _cap(m.get("body")), "thread_id": m.get("threadid"), "box": m.get("type"),
            "read": m.get("read"), "_full_body": str(m.get("body") or "")}


def fetch_notifications() -> list[dict]:
    raw = client.get_client().get("/v1/notifications") or []
    return [n for n in raw if isinstance(n, dict)]


def fetch_sms(limit: int, box: str = "inbox", offset: int = 0) -> list[dict]:
    raw = client.get_client().get("/v1/sms", {"limit": limit, "offset": offset, "box": box}) or []
    items = [_norm_sms(m) for m in raw if isinstance(m, dict)]
    items.sort(key=lambda m: m["ts"] or 0, reverse=True)
    return items


def _public_sms(m: dict, with_scam: bool) -> dict:
    out = {k: v for k, v in m.items() if not k.startswith("_") and k != "ts"}
    if with_scam:
        risk = scam.score(m["_full_body"])
        out["scam_risk"] = risk["level"]
        if risk["level"] != "low":
            out["scam_reasons"] = risk["reasons"]
    return out


# ---------------------------------------------------------------------------
# Level 1: read the phone


@tool
def phone_status(args: dict) -> dict:
    c = client.get_client()
    data = c.get("/v1/status") or {}
    try:
        ping = c.get("/v1/ping") or {}
    except PhoneError:
        ping = {}
    bat = data.get("battery") or {}
    return _ok(battery_percent=bat.get("percentage"), charging=(bat.get("status") == "CHARGING"
               or (bat.get("plugged") not in (None, "UNPLUGGED", "PLUGGED_NONE"))),
               battery_status=bat.get("status"), temperature_c=bat.get("temperature"),
               battery_health=bat.get("health"), wifi=_ssid((data.get("wifi") or {}).get("ssid")),
               device=ping.get("device_model"), helper_version=ping.get("helper_version"),
               mock=ping.get("mock", False), last_seen=_fmt_time(int(time.time())))


@tool
def phone_notifications(args: dict) -> dict:
    limit = _int_arg(args, "limit", 30, 1, 100)
    include_system = bool(args.get("include_system"))
    app = str(args.get("app") or "").strip().lower()
    since = args.get("since_minutes")
    exclude = [str(a).lower() for a in (client.setting("notifications_exclude_apps", []) or []) if a]
    raw = fetch_notifications()
    hidden = 0
    items = []
    for n in raw:
        if not include_system and _is_noise(n):
            hidden += 1
            continue
        item = _norm_notification(n)
        if any(e in item["package"].lower() or e == item["app"].lower() for e in exclude):
            hidden += 1
            continue
        if app and app not in item["package"].lower() and app not in item["app"].lower():
            continue
        if since and item["ts"] and item["ts"] < time.time() - int(since) * 60:
            continue
        items.append(item)
    items.sort(key=lambda i: i["ts"] or 0, reverse=True)
    out = _ok(count=min(len(items), limit), total=len(items), hidden_noise=hidden,
              notifications=[{k: v for k, v in i.items() if k not in ("ts", "package")} for i in items[:limit]])
    if not raw:
        out["note"] = ("No notifications. If you expected some, enable Notification access for "
                       "Termux:API in Android settings.")
    return out


@tool
def phone_sms_list(args: dict) -> dict:
    limit = _int_arg(args, "limit", 20, 1, 100)
    box = str(args.get("box") or "inbox").lower()
    if box not in ("inbox", "sent", "all"):
        raise ValueError("box must be inbox, sent or all")
    query = str(args.get("query") or "").strip().lower()
    from_number = str(args.get("from_number") or "").strip()
    since_days = args.get("since_days")
    filtering = bool(query or from_number or since_days)
    items = fetch_sms(200 if filtering else limit, box)
    if since_days:
        cutoff = time.time() - int(since_days) * 86400
        items = [m for m in items if (m["ts"] or 0) >= cutoff]
    if from_number:
        params = {"from_number": from_number}
        items = [m for m in items if watch.matches_sms(params, m)]
    if query:
        items = [m for m in items if query in m["_full_body"].lower() or query in str(m["from"]).lower()]
    with_scam = _bool_setting("scam_check_enabled", True)
    return _ok(count=min(len(items), limit), messages=[_public_sms(m, with_scam) for m in items[:limit]])


@tool
def phone_contacts(args: dict) -> dict:
    query = str(args.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    return _ok(matches=find_contacts(query))


def find_contacts(query: str, limit: int = 10) -> list[dict]:
    raw = client.get_client().get("/v1/contacts") or []
    q, qd = query.lower(), _digits(query)
    seen, out = set(), []
    for c in raw:
        if not isinstance(c, dict):
            continue
        name, number = str(c.get("name") or ""), str(c.get("number") or "")
        hit = q in name.lower() or (len(qd) >= 4 and qd in _digits(number))
        key = (name, _digits(number)[-10:])
        if hit and key not in seen:
            seen.add(key)
            out.append({"name": name, "number": re.sub(r"[\s\-()]", "", number)})
    return out[:limit]


@tool
def phone_calls(args: dict) -> dict:
    limit = _int_arg(args, "limit", 20, 1, 100)
    kind = str(args.get("type") or "all").lower()
    if kind not in ("missed", "incoming", "outgoing", "all"):
        raise ValueError("type must be missed, incoming, outgoing or all")
    raw = client.get_client().get("/v1/calls", {"limit": 100 if kind != "all" else limit}) or []
    calls = []
    for c in raw:
        ctype = str(c.get("type") or "").lower()
        if kind != "all" and ctype != kind:
            continue
        ts = _parse_time(c.get("date"))
        name = c.get("name")
        calls.append({"name": None if name in (None, "", "UNKNOWN_CALLER") else name,
                      "number": c.get("phone_number"), "type": ctype, "time": _fmt_time(ts), "ts": ts,
                      "duration": c.get("duration")})
    calls.sort(key=lambda c: c["ts"] or 0, reverse=True)
    return _ok(count=min(len(calls), limit), calls=[{k: v for k, v in c.items() if k != "ts"} for c in calls[:limit]])


@tool
def phone_location(args: dict) -> dict:
    provider = str(args.get("provider") or "network").lower()
    if provider not in ("network", "gps"):
        raise ValueError("provider must be network or gps")
    loc = client.get_client().get("/v1/location", {"provider": provider}, timeout=40) or {}
    lat, lon = loc.get("latitude"), loc.get("longitude")
    return _ok(latitude=lat, longitude=lon, accuracy_m=loc.get("accuracy"), provider=loc.get("provider"),
               time=_fmt_time(int(time.time())), maps_url=f"https://maps.google.com/?q={lat},{lon}")


# ---------------------------------------------------------------------------
# Level 2: act on the phone


def is_phone_number(value: Any) -> bool:
    return bool(PHONE_RE.match(re.sub(r"[\s\-()]", "", str(value or ""))))


@tool
def phone_sms_send(args: dict) -> dict:
    to = str(args.get("to") or "").strip()
    text = args.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text is required")
    if len(text) > SMS_MAX:
        raise ValueError(f"text is too long ({len(text)} characters, max {SMS_MAX})")
    if not is_phone_number(to):
        matches = find_contacts(to) if to else []
        return {"ok": False, "error": "needs_number", "sent": False, "matches": matches,
                "message": ("Nothing was sent. " + (
                    "Several contacts match: ask the user which one, then call again with the number."
                    if len(matches) > 1 else
                    "Call again with this contact's number." if matches else
                    "No contact matches that name. Ask the user for the number."))}
    data = client.get_client().post("/v1/sms/send", {"to": to, "text": text}) or {}
    return _ok(sent=True, to=data.get("to", to), chars=len(text))


@tool
def phone_call(args: dict) -> dict:
    to = str(args.get("to") or "").strip()
    if not is_phone_number(to):
        return {"ok": False, "error": "needs_number", "matches": find_contacts(to) if to else [],
                "message": "Nothing was dialled. Call again with a phone number."}
    client.get_client().post("/v1/call", {"to": to})
    return _ok(calling=to)


@tool
def phone_ring(args: dict) -> dict:
    seconds = _int_arg(args, "seconds", 20, 1, 60)
    data = client.get_client().post("/v1/ring", {"seconds": seconds}) or {}
    return _ok(ringing=True, seconds=seconds, already_ringing=bool(data.get("already_ringing")))


@tool
def phone_speak(args: dict) -> dict:
    text = args.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text is required")
    if len(text) > 500:
        raise ValueError("text is too long (max 500 characters)")
    client.get_client().post("/v1/speak", {"text": text}, timeout=70)
    return _ok(spoken=True, chars=len(text))


@tool
def phone_clipboard(args: dict) -> dict:
    action = str(args.get("action") or "get").lower()
    c = client.get_client()
    if action == "get":
        return _ok(text=_cap((c.get("/v1/clipboard") or {}).get("text"), 4000))
    if action == "set":
        text = args.get("text")
        if not isinstance(text, str) or not text:
            raise ValueError("text is required for action=set")
        c.post("/v1/clipboard", {"text": text})
        return _ok(set=True, chars=len(text))
    raise ValueError("action must be get or set")


def _photo_dir() -> Path | None:
    try:
        from plugins.plugin_storage import plugin_data_dir
    except ImportError:
        return None
    path = plugin_data_dir(storage.PLUGIN) / "photos"
    path.mkdir(parents=True, exist_ok=True)
    return path


@tool
def phone_photo(args: dict) -> dict:
    import base64

    camera = str(args.get("camera") or "back").lower()
    if camera not in ("back", "front"):
        raise ValueError("camera must be back or front")
    data = client.get_client().post("/v1/photo", {"camera": camera}, timeout=45) or {}
    jpeg = base64.b64decode(data.get("jpeg_b64") or "")
    if not jpeg:
        raise PhoneError("internal", "the phone returned no image")
    result = _ok(camera=camera, bytes=len(jpeg))
    folder = _photo_dir()
    if folder is None:
        result["note"] = "Photo taken, but no Hermes data folder is available to save it."
        return result
    path = folder / f"photo-{int(time.time())}-{camera}.jpg"
    path.write_bytes(jpeg)
    result["saved_to"] = str(path)
    result["next_step"] = "Run vision_analyze on saved_to to see the photo."
    return result


@tool(mask=False)
def phone_otp_reveal(args: dict) -> dict:
    if not _bool_setting("allow_otp_reveal", False):
        return {"ok": False, "error": "disabled",
                "message": "OTP reveal is off. The user can turn on 'Allow OTP reveal' in the Phone Senses settings."}
    max_age = _int_arg(args, "max_age_minutes", 10, 1, 60)
    cutoff = time.time() - max_age * 60
    candidates = [(m["ts"] or 0, m["from"], m["_full_body"]) for m in fetch_sms(15, "inbox")]
    try:
        candidates += [(_parse_time(n.get("when")) or 0, app_name(str(n.get("packageName") or "")),
                        f"{n.get('title') or ''} {n.get('content') or ''}") for n in fetch_notifications()]
    except PhoneError:
        pass
    for ts, source, body in sorted(candidates, key=lambda c: c[0], reverse=True):
        if ts < cutoff:
            break
        codes = otp.find_otps(body)
        if codes:
            return _ok(code=codes[0], source=otp.mask_text(str(source)), received=_fmt_time(ts))
    return {"ok": False, "error": "not_found", "message": f"No OTP received in the last {max_age} minutes."}


# ---------------------------------------------------------------------------
# Level 3: money tracker


def _money_enabled() -> None:
    if not _bool_setting("money_enabled", True):
        raise PhoneError("disabled", "The money tracker is turned off in the Phone Senses settings.")


def _parse_messages(items: list[dict]) -> list[dict]:
    txs = []
    for m in items:
        tx = money.parse(m["number"], m["ts"] or 0, m["_full_body"]) if m["ts"] else None
        if tx:
            txs.append(tx.to_dict())
    return txs


def sync_sms(days: int, max_messages: int = 2000) -> dict:
    """Read inbox SMS back to ``days`` ago, store new transactions, return counts and warnings."""
    cutoff = time.time() - days * 86400
    scanned, offset, txs = 0, 0, []
    page = 200
    while scanned < max_messages:
        items = fetch_sms(page, "inbox", offset)
        if not items:
            break
        scanned += len(items)
        recent = [m for m in items if (m["ts"] or 0) >= cutoff]
        txs.extend(_parse_messages(recent))
        if len(items) < page or len(recent) < len(items):
            break
        offset += page
    unique = list({t["id"]: t for t in txs}.values())
    added = storage.add_transactions(unique)
    warnings = _warnings(unique) if added else []
    storage.set_cursor("money_last_sync", str(int(time.time())))
    return {"scanned": scanned, "parsed": len(txs), "new": added, "warnings": warnings}


def _warnings(txs: list[dict]) -> list[str]:
    """Possible duplicate debits (same amount and counterparty within 10 min) and unusually big ones."""
    out: list[str] = []
    debits = sorted((t for t in txs if t["direction"] == "debit"), key=lambda t: t["ts"])
    for a, b in zip(debits, debits[1:]):
        if (a["amount_paise"] == b["amount_paise"] and a["counterparty"] == b["counterparty"]
                and b["ts"] - a["ts"] <= 600):
            out.append(f"Possible duplicate: Rs {_rs(a['amount_paise']):,.2f} to {a['counterparty'] or 'unknown'} "
                       f"twice within 10 minutes ({_fmt_time(a['ts'])})")
    median = storage.median_debit(int(time.time()) - 90 * 86400)
    if median:
        for t in debits:
            if t["amount_paise"] > 3 * median and t["amount_paise"] >= 100000:
                out.append(f"Unusually large debit: Rs {_rs(t['amount_paise']):,.2f} to "
                           f"{t['counterparty'] or 'unknown'} on {_fmt_time(t['ts'])}")
    return out[:5]


@tool
def phone_money_sync(args: dict) -> dict:
    _money_enabled()
    days = _int_arg(args, "days", 30, 1, 365)
    return _ok(period_days=days, **sync_sms(days))


def period_range(period: str, start: str | None = None, end: str | None = None,
                 now: dt.datetime | None = None) -> tuple[int, int, str]:
    now = now or dt.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "today":
        a, b = midnight, now + dt.timedelta(seconds=1)
    elif period == "yesterday":
        a, b = midnight - dt.timedelta(days=1), midnight
    elif period == "week":
        a, b = midnight - dt.timedelta(days=6), now + dt.timedelta(seconds=1)
    elif period == "month":
        a, b = midnight.replace(day=1), now + dt.timedelta(seconds=1)
    elif period == "custom":
        try:
            a = dt.datetime.strptime(str(start), "%Y-%m-%d")
            b = dt.datetime.strptime(str(end or start), "%Y-%m-%d") + dt.timedelta(days=1)
        except ValueError:
            raise ValueError("custom period needs start and end as YYYY-MM-DD")
        if b <= a:
            raise ValueError("end must be on or after start")
    else:
        raise ValueError("period must be today, yesterday, week, month or custom")
    label = f"{a:%Y-%m-%d} to {(b - dt.timedelta(seconds=1)):%Y-%m-%d}"
    return int(a.timestamp()), int(b.timestamp()), label


def summarize(period: str = "week", group_by: str = "category", direction: str = "debit",
              start: str | None = None, end: str | None = None) -> dict:
    if group_by not in ("category", "counterparty", "day"):
        raise ValueError("group_by must be category, counterparty or day")
    if direction not in ("debit", "credit", "both"):
        raise ValueError("direction must be debit, credit or both")
    a, b, label = period_range(period, start, end)
    txs = storage.transactions(a, b, direction)
    debit = sum(t["amount_paise"] for t in txs if t["direction"] == "debit")
    credit = sum(t["amount_paise"] for t in txs if t["direction"] == "credit")
    groups: OrderedDict[str, list[int]] = OrderedDict()
    for t in txs:
        if group_by == "day":
            key = _fmt_time(t["ts"])[:10]
        elif group_by == "counterparty":
            key = t["counterparty"] or "unknown"
        else:
            key = t["category"]
        groups.setdefault(key, [0, 0])
        groups[key][0] += t["amount_paise"]
        groups[key][1] += 1
    total = sum(v[0] for v in groups.values()) or 1
    ordered = sorted(groups.items(), key=(lambda kv: kv[0]) if group_by == "day" else (lambda kv: -kv[1][0]))
    out = {"period": label, "direction": direction, "transactions": len(txs),
           "total_debit_rs": _rs(debit), "total_credit_rs": _rs(credit),
           "groups": [{group_by: k, "amount_rs": _rs(v[0]), "count": v[1], "pct": round(100 * v[0] / total)}
                      for k, v in ordered[:15]],
           "top": [{"amount_rs": _rs(t["amount_paise"]), "direction": t["direction"],
                    "counterparty": t["counterparty"], "category": t["category"], "channel": t["channel"],
                    "time": _fmt_time(t["ts"])}
                   for t in sorted(txs, key=lambda t: -t["amount_paise"])[:5]]}
    limits = storage.budgets()
    if limits and direction in ("debit", "both"):
        ma, mb, _ = period_range("month")
        month = storage.transactions(ma, mb, "debit")
        out["budgets"] = []
        for cat, limit in sorted(limits.items()):
            spent = sum(t["amount_paise"] for t in month if t["category"] == cat)
            out["budgets"].append({"category": cat, "monthly_limit_rs": _rs(limit), "spent_this_month_rs": _rs(spent),
                                   "pct_used": round(100 * spent / limit)})
    if not txs:
        out["note"] = "No bank or UPI transactions found for this period."
    return out


@tool
def phone_money_summary(args: dict) -> dict:
    _money_enabled()
    sync_note = None
    try:   # quick sync of the newest SMS so the answer is current
        days = 40 if args.get("period") in ("month", "custom") else 8
        sync_sms(days, max_messages=400)
    except PhoneError as exc:
        sync_note = f"Could not read new SMS from the phone ({exc.code}); showing stored data."
    out = summarize(str(args.get("period") or "week"), str(args.get("group_by") or "category"),
                    str(args.get("direction") or "debit"), args.get("start"), args.get("end"))
    if sync_note:
        out["sync_note"] = sync_note
    return _ok(**out)


@tool
def phone_budget_set(args: dict) -> dict:
    category = str(args.get("category") or "").lower()
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {', '.join(CATEGORIES)}")
    try:
        limit = float(args.get("monthly_limit_rs"))
    except (TypeError, ValueError):
        raise ValueError("monthly_limit_rs must be a number")
    if limit < 0:
        raise ValueError("monthly_limit_rs cannot be negative")
    storage.set_budget(category, int(round(limit * 100)))
    return _ok(category=category, monthly_limit_rs=round(limit, 2), removed=limit == 0)


# ---------------------------------------------------------------------------
# Scam check, watch rules, brief


@tool
def phone_scam_check(args: dict) -> dict:
    text = args.get("text")
    if isinstance(text, str) and text.strip():
        return _ok(**scam.score(text))
    limit = _int_arg(args, "limit", 30, 1, 100)
    flagged = []
    for m in fetch_sms(limit, "inbox"):
        risk = scam.score(m["_full_body"])
        if risk["level"] != "low":
            flagged.append({"from": m["from"], "date": m["date"], "body": m["body"], **risk})
    flagged.sort(key=lambda f: -f["score"])
    return _ok(checked=limit, flagged=len(flagged), messages=flagged[:10])


@tool
def phone_watch_add(args: dict) -> dict:
    kind, params = watch.build_rule(args)
    rule_id = storage.add_rule(kind, params)
    return _ok(id=rule_id, kind=kind, rule=watch.describe(kind, params),
               tip="Run phone_watch_check (for example from a Hermes cron job) to get matches.")


@tool
def phone_watch_list(args: dict) -> dict:
    rules = storage.rules()
    return _ok(rules=[{"id": r["id"], "kind": r["kind"], "rule": watch.describe(r["kind"], r["params"]),
                       "enabled": r["enabled"]} for r in rules])


@tool
def phone_watch_remove(args: dict) -> dict:
    try:
        rule_id = int(args.get("id"))
    except (TypeError, ValueError):
        raise ValueError("id must be an integer")
    return _ok(removed=storage.remove_rule(rule_id), id=rule_id)


def _cursor_ts(name: str) -> int:
    value = storage.get_cursor(name)
    return int(value) if value and value.isdigit() else int(time.time()) - 3600   # first run: last hour


@tool
def phone_watch_check(args: dict) -> dict:
    rules = storage.rules(enabled_only=True)
    if not rules:
        return _ok(matches=[], note="No watch rules yet. Add one with phone_watch_add.")
    matches: list[dict] = []
    checked = {}
    kinds = {r["kind"] for r in rules}
    if "notification" in kinds:
        since = _cursor_ts("watch_notifications")
        newest = since
        items = [_norm_notification(n) for n in fetch_notifications() if not _is_noise(n)]
        fresh = [i for i in items if (i["ts"] or 0) > since]
        checked["notifications"] = len(fresh)
        for item in fresh:
            newest = max(newest, item["ts"])
            for r in rules:
                if r["kind"] == "notification" and watch.matches_notification(r["params"], item):
                    matches.append({"rule_id": r["id"], "rule": watch.describe(r["kind"], r["params"]),
                                    "source": "notification", "app": item["app"], "title": item["title"],
                                    "text": item["text"], "time": item["time"]})
        storage.set_cursor("watch_notifications", str(newest))
    if kinds & {"sms", "debit_over"}:
        since = _cursor_ts("watch_sms")
        newest = since
        fresh = [m for m in fetch_sms(50, "inbox") if (m["ts"] or 0) > since]
        checked["sms"] = len(fresh)
        txs = {t["id"]: t for t in _parse_messages(fresh)} if "debit_over" in kinds else {}
        for m in fresh:
            newest = max(newest, m["ts"])
            for r in rules:
                if r["kind"] == "sms" and watch.matches_sms(r["params"], m):
                    matches.append({"rule_id": r["id"], "rule": watch.describe(r["kind"], r["params"]),
                                    "source": "sms", "from": m["from"], "text": m["body"], "time": m["date"]})
        for t in txs.values():
            for r in rules:
                if r["kind"] == "debit_over" and watch.matches_debit(r["params"], t):
                    matches.append({"rule_id": r["id"], "rule": watch.describe(r["kind"], r["params"]),
                                    "source": "debit", "amount_rs": _rs(t["amount_paise"]),
                                    "counterparty": t["counterparty"], "time": _fmt_time(t["ts"])})
        if txs and _bool_setting("money_enabled", True):
            storage.add_transactions(list(txs.values()))
        storage.set_cursor("watch_sms", str(newest))
    if matches and args.get("notify_phone"):
        c = client.get_client()
        for match in matches[:5]:
            try:
                c.post("/v1/notify", {"title": f"Phone Senses: {match['rule']}"[:100],
                                      "content": otp.mask_text(str(match.get("title") or match.get("text")
                                                                   or match.get("counterparty") or "match"))[:300]})
            except PhoneError:
                break
    return _ok(checked=checked, matches=matches[:20], match_count=len(matches))


@tool
def phone_brief(args: dict) -> dict:
    brief: dict[str, Any] = {}
    day_ago = time.time() - 86400

    def section(name: str, fn: Callable[[], Any]) -> None:
        try:
            brief[name] = fn()
        except PhoneError as exc:
            brief[name] = {"error": exc.code}
            if exc.code in ("phone_unreachable", "not_paired", "unauthorized"):
                raise

    def battery():
        data = client.get_client().get("/v1/status") or {}
        bat = data.get("battery") or {}
        return {"percent": bat.get("percentage"), "status": bat.get("status")}

    def missed():
        raw = client.get_client().get("/v1/calls", {"limit": 30}) or []
        out = []
        for c in raw:
            ts = _parse_time(c.get("date"))
            if str(c.get("type") or "").lower() == "missed" and ts and ts >= day_ago:
                name = c.get("name")
                out.append({"from": name if name not in (None, "", "UNKNOWN_CALLER") else c.get("phone_number"),
                            "time": _fmt_time(ts)})
        return out

    sms_cache: list[dict] = []

    def messages():
        sms_cache.extend(fetch_sms(40, "inbox"))
        recent = [m for m in sms_cache if (m["ts"] or 0) >= day_ago]
        people, seen = [], set()
        bank = 0
        for m in recent:
            if money.bank_from_sender(m["number"]) and not m["number"].startswith("+"):
                bank += 1
                continue
            key = m["_full_body"][:80]
            if key in seen:
                continue
            seen.add(key)
            people.append({"from": m["from"], "time": m["date"], "text": _cap(m["body"], 160)})
        return {"from_people": people[:6], "bank_or_service_sms": bank}

    def notes():
        items = [_norm_notification(n) for n in fetch_notifications() if not _is_noise(n)]
        items.sort(key=lambda i: i["ts"] or 0, reverse=True)
        return [{"app": i["app"], "title": i["title"], "text": _cap(i["text"], 160)} for i in items[:8]]

    def scams():
        flagged = [{"from": m["from"], "level": r["level"], "why": r["reasons"][:2]}
                   for m in sms_cache[:40] if (m["ts"] or 0) >= time.time() - 3 * 86400
                   for r in [scam.score(m["_full_body"])] if r["level"] == "high"]
        return flagged[:3]

    def spending():
        if not _bool_setting("money_enabled", True):
            return {"disabled": True}
        sync_sms(3, max_messages=200)
        y = summarize("yesterday", "category", "debit")
        t = summarize("today", "category", "both")
        return {"yesterday_spent_rs": y["total_debit_rs"],
                "yesterday_by_category": {g["category"]: g["amount_rs"] for g in y["groups"]},
                "today_spent_rs": t["total_debit_rs"], "today_received_rs": t["total_credit_rs"]}

    try:
        section("battery", battery)
        section("missed_calls", missed)
        section("sms", messages)
        section("notifications", notes)
        if _bool_setting("scam_check_enabled", True):
            section("scam_alerts", scams)
        section("money", spending)
    except PhoneError as exc:
        return exc.to_result()
    return _ok(**brief)


# Name -> handler, used by register() and tests.
HANDLERS: dict[str, Callable[..., Any]] = {
    "phone_status": phone_status,
    "phone_notifications": phone_notifications,
    "phone_sms_list": phone_sms_list,
    "phone_sms_send": phone_sms_send,
    "phone_calls": phone_calls,
    "phone_contacts": phone_contacts,
    "phone_location": phone_location,
    "phone_ring": phone_ring,
    "phone_speak": phone_speak,
    "phone_clipboard": phone_clipboard,
    "phone_photo": phone_photo,
    "phone_call": phone_call,
    "phone_otp_reveal": phone_otp_reveal,
    "phone_money_sync": phone_money_sync,
    "phone_money_summary": phone_money_summary,
    "phone_budget_set": phone_budget_set,
    "phone_scam_check": phone_scam_check,
    "phone_watch_add": phone_watch_add,
    "phone_watch_list": phone_watch_list,
    "phone_watch_remove": phone_watch_remove,
    "phone_watch_check": phone_watch_check,
    "phone_brief": phone_brief,
}
