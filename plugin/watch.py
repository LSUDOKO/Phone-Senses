"""Watch rules: validation and matching (pure functions; storage lives in storage.py)."""
from __future__ import annotations

import re

KINDS = ("notification", "sms", "debit_over", "battery_below", "scam_guard")
REARM_MARGIN = 5   # battery_below fires again only after the level rose above percent + this


def build_rule(args: dict) -> tuple[str, dict]:
    """Validate tool args into (kind, params). Raises ValueError with a user-facing message."""
    kind = str(args.get("kind") or "").strip()
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}")
    label = str(args.get("label") or "").strip()[:60]
    if kind == "notification":
        params = {k: str(args[k]).strip()[:80] for k in ("app", "contains") if str(args.get(k) or "").strip()}
        if not params:
            raise ValueError("a notification rule needs 'app' and/or 'contains'")
    elif kind == "sms":
        params = {k: str(args[k]).strip()[:80] for k in ("from_number", "contains") if str(args.get(k) or "").strip()}
        if not params:
            raise ValueError("an sms rule needs 'from_number' and/or 'contains'")
    elif kind == "scam_guard":
        params = {}
    elif kind == "battery_below":
        try:
            percent = int(args.get("percent"))
        except (TypeError, ValueError):
            raise ValueError("a battery_below rule needs percent (1-99)")
        if not 1 <= percent <= 99:
            raise ValueError("percent must be between 1 and 99")
        params = {"percent": percent}
    else:
        try:
            amount = float(args.get("amount_rs"))
        except (TypeError, ValueError):
            raise ValueError("a debit_over rule needs amount_rs (rupees)")
        if amount <= 0:
            raise ValueError("amount_rs must be positive")
        params = {"amount_paise": int(round(amount * 100))}
    if label:
        params["label"] = label
    return kind, params


def describe(kind: str, params: dict) -> str:
    if params.get("label"):
        return params["label"]
    if kind == "debit_over":
        return f"debit over Rs {params['amount_paise'] / 100:,.2f}"
    if kind == "battery_below":
        return f"battery below {params['percent']}%"
    if kind == "scam_guard":
        return "scam in progress (call + screen sharing + OTP + money)"
    bits = [f"{k.replace('_number', '')} '{v}'" for k, v in params.items() if k != "label"]
    return f"{kind}: " + " and ".join(bits)


def _contains(hay: str, needle: str | None) -> bool:
    return not needle or needle.lower() in (hay or "").lower()


def _digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def matches_notification(params: dict, item: dict) -> bool:
    """item: {"app", "package", "title", "text"}"""
    app = params.get("app")
    if app and not (_contains(item.get("app", ""), app) or _contains(item.get("package", ""), app)):
        return False
    return _contains(f"{item.get('title', '')} {item.get('text', '')}", params.get("contains"))


def matches_sms(params: dict, item: dict) -> bool:
    """item: {"number", "from", "body"}"""
    want = params.get("from_number")
    if want:
        num, label = item.get("number", ""), item.get("from", "")
        dw = _digits(want)
        ok = (dw and len(dw) >= 6 and dw[-10:] in _digits(num)) or _contains(num, want) or _contains(label, want)
        if not ok:
            return False
    return _contains(item.get("body", ""), params.get("contains"))


def matches_debit(params: dict, tx: dict) -> bool:
    return tx.get("direction") == "debit" and int(tx.get("amount_paise") or 0) > int(params["amount_paise"])


def battery_step(params: dict, percent: int | None, charging: bool, fired: bool) -> tuple[bool, bool]:
    """One battery_below check. Returns (alert now, fired state to store).

    Alerts once when the level drops below ``percent`` (not while charging), then stays quiet until
    the level rises above ``percent + REARM_MARGIN``.
    """
    if percent is None:
        return False, fired
    if fired:
        return False, percent <= params["percent"] + REARM_MARGIN
    if percent < params["percent"] and not charging:
        return True, True
    return False, False
