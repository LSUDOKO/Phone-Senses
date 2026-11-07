"""``/phone`` slash command: quick status, ring, money, brief and pairing help."""
from __future__ import annotations

import json
from typing import Any

from . import tools

USAGE = ("Usage: /phone [status] | ring [seconds] | money [today|yesterday|week|month] | received [today|week] "
         "| brief | pair")

PAIR_HELP = """Pair Phone Senses with your Android phone:
1. Install Termux and Termux:API from F-Droid; in Termux run: pkg install -y python termux-api git
2. git clone https://github.com/LSUDOKO/Phone-Senses.git && cd Phone-Senses
3. python phone_helper/helper.py --pair   (copy the pairing code it prints)
4. termux-wake-lock && python phone_helper/helper.py --host 0.0.0.0
5. In Hermes, open the Phone Senses settings: set helper_url to http://<phone-ip>:8765 and paste the
   pairing code into helper_token. Tailscale is recommended outside your home Wi-Fi.
Then try: /phone"""


def _call(name: str, args: dict | None = None) -> dict:
    return json.loads(tools.HANDLERS[name](args or {}))


def _err(res: dict) -> str:
    msg = f"Phone Senses: {res.get('message') or res.get('error')}"
    return f"{msg}\nHint: {res['hint']}" if res.get("hint") else msg


def _money(res: dict, direction: str) -> str:
    if not res.get("ok"):
        return _err(res)
    total = res["total_debit_rs"] if direction == "debit" else res["total_credit_rs"]
    verb = "Spent" if direction == "debit" else "Received"
    lines = [f"{verb} Rs {total:,.2f} ({res['period']}, {res['transactions']} transactions)"]
    key = "category" if direction == "debit" else "counterparty"
    for g in res.get("groups", [])[:8]:
        lines.append(f"  {g[key]:<18} Rs {g['amount_rs']:>10,.2f}  ({g['count']})")
    for b in res.get("budgets", []) or []:
        lines.append(f"  budget {b['category']}: {b['pct_used']}% of Rs {b['monthly_limit_rs']:,.0f} used")
    return "\n".join(lines)


def handle(raw: str = "", **kwargs: Any) -> str:
    """Entry point for ``/phone <args>``. Always returns text; never raises."""
    try:
        parts = (raw or "").strip().split()
        cmd = parts[0].lower() if parts else "status"
        rest = parts[1:]
        if cmd in ("status", ""):
            res = _call("phone_status")
            if not res.get("ok"):
                return _err(res)
            charge = "charging" if res.get("charging") else "not charging"
            mock = " [mock phone]" if res.get("mock") else ""
            return (f"Phone{mock}: battery {res.get('battery_percent')}% ({charge}), "
                    f"{res.get('temperature_c')}°C, Wi-Fi {res.get('wifi') or 'off'}, "
                    f"helper {res.get('helper_version')}")
        if cmd == "ring":
            seconds = int(rest[0]) if rest and rest[0].isdigit() else 20
            res = _call("phone_ring", {"seconds": seconds})
            return f"Ringing your phone for {res['seconds']} s." if res.get("ok") else _err(res)
        if cmd in ("money", "spent", "received"):
            period = rest[0].lower() if rest else ("today" if cmd == "received" else "week")
            direction = "credit" if cmd == "received" else "debit"
            group = "counterparty" if direction == "credit" else "category"
            return _money(_call("phone_money_summary", {"period": period, "direction": direction,
                                                        "group_by": group}), direction)
        if cmd == "brief":
            res = _call("phone_brief")
            if not res.get("ok"):
                return _err(res)
            res.pop("ok", None)
            return "Phone brief:\n" + json.dumps(res, ensure_ascii=False, indent=1)
        if cmd == "pair":
            return PAIR_HELP
        return USAGE
    except Exception as exc:   # a slash command must never crash the session
        return f"Phone Senses: /phone failed ({type(exc).__name__}). {USAGE}"
