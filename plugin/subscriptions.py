"""Find recurring debits (subscriptions, memberships, monthly bills) in stored transactions.

Pure functions over transaction dicts from ``storage.transactions``: no I/O.
A payee counts when it was charged at least twice, about a month apart (25 to 35 days), with
similar amounts (within 15% of the typical one). Well-known subscription services also count
with fewer or irregular charges.
"""
from __future__ import annotations

import datetime as dt
import re
import statistics

I = re.IGNORECASE
KNOWN = [(name, re.compile(pat, I)) for name, pat in (
    ("Netflix", r"netflix"), ("Spotify", r"spotify"), ("Amazon Prime", r"\bprime\b|primevideo"),
    ("Disney+ Hotstar", r"hotstar|disney"), ("YouTube Premium", r"youtube|\byt\s*premium"),
    ("iCloud", r"icloud|apple\.com|apple\s+services"), ("Google One", r"google\s*one|google\s*storage"),
    ("Gym", r"\bgym\b|cult\.?\s?fit|fitness"),
    ("Broadband", r"broadband|fibernet|jio\s*fiber|xstream|hathway|excitel"),
)]
MONTHLY_DAYS = (25, 35)
TOLERANCE = 0.15


def payee_key(counterparty: str) -> tuple[str, bool]:
    """('Netflix', True) for known services, else a normalised payee name and False."""
    low = counterparty.lower()
    for name, rx in KNOWN:
        if rx.search(low):
            return name, True
    base = low.split("@")[0]   # VPA: keep the handle, drop @bank
    return re.sub(r"[^a-z0-9]", "", base) or low, False


def add_month(day: dt.date) -> dt.date:
    year, month = (day.year + 1, 1) if day.month == 12 else (day.year, day.month + 1)
    for d in (day.day, 30, 29, 28):
        try:
            return day.replace(year=year, month=month, day=d)
        except ValueError:
            continue
    return day + dt.timedelta(days=30)


def find(txs: list[dict], today: dt.date | None = None) -> list[dict]:
    """Recurring payees among debit transactions (dicts with ts, amount_paise, counterparty, channel)."""
    today = today or dt.date.today()
    groups: dict[str, dict] = {}
    for t in sorted(txs, key=lambda t: t["ts"]):
        if t.get("direction", "debit") != "debit" or not t.get("counterparty") or t.get("channel") == "atm":
            continue
        key, known = payee_key(t["counterparty"])
        g = groups.setdefault(key, {"name": key if known else t["counterparty"], "known": known, "txs": []})
        g["txs"].append(t)
        if not known:
            g["name"] = t["counterparty"]   # latest spelling
    out = []
    for g in groups.values():
        typical = statistics.median(t["amount_paise"] for t in g["txs"])
        charges = [t for t in g["txs"] if abs(t["amount_paise"] - typical) <= TOLERANCE * typical]
        if not charges:
            continue
        days = [dt.date.fromtimestamp(t["ts"]) for t in charges]
        gaps = [(b - a).days for a, b in zip(days, days[1:]) if (b - a).days >= 5]   # same-week retries are not a cycle
        gap = statistics.median(gaps) if gaps else None
        monthly = gap is not None and MONTHLY_DAYS[0] <= gap <= MONTHLY_DAYS[1]
        if not monthly and not g["known"]:
            continue
        cadence = "monthly" if monthly else "irregular" if len(charges) > 1 else "unknown"
        nxt = add_month(days[-1]) if monthly else None
        stopped = bool(nxt and nxt < today - dt.timedelta(days=10))
        out.append({"merchant": g["name"], "typical_amount_rs": round(statistics.median(
                        t["amount_paise"] for t in charges) / 100, 2),
                    "cadence": cadence, "charges": len(charges), "last_charged": days[-1].isoformat(),
                    "next_expected": nxt.isoformat() if nxt else None,
                    "status": "maybe_stopped" if stopped else "active"})
    out.sort(key=lambda s: -s["typical_amount_rs"])
    return out


def monthly_total_rs(subs: list[dict]) -> float:
    return round(sum(s["typical_amount_rs"] for s in subs if s["cadence"] == "monthly" and s["status"] == "active"), 2)
