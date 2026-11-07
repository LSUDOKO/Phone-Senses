"""Detect and mask one-time codes (OTPs) in text.

A 4 to 8 digit number is treated as an OTP when an OTP-style keyword (OTP, code, verification,
passcode, PIN ...) appears near it. Amounts (Rs 1250), dates (08/11/26), times, account fragments
(XX1111) and long numbers (order or phone numbers) are left alone. When in doubt we mask: hiding
a harmless number is better than showing a real code.
"""
from __future__ import annotations

import re
from typing import Any

MASK = "[OTP hidden]"

KEYWORDS = re.compile(
    r"\b(otp|one[\s-]?time|passcode|pass\s?code|verification|verify|code|pin|2fa|"
    r"security\s+key|login\s+key|auth(?:entication)?)\b",
    re.IGNORECASE,
)
# A standalone run of 4-8 digits (not glued to letters or other digits).
CANDIDATE = re.compile(r"(?<![\w])(\d{4,8})(?![\w])")
CURRENCY_BEFORE = re.compile(r"(rs\.?|inr|₹|\$|usd|amount|amt)\s*$", re.IGNORECASE)
WINDOW = 60


def _is_otp_at(text: str, start: int, end: int) -> bool:
    before, after = text[max(0, start - WINDOW):start], text[end:end + WINDOW]
    if not (KEYWORDS.search(before) or KEYWORDS.search(after)):
        return False
    if CURRENCY_BEFORE.search(text[max(0, start - 8):start]):
        return False
    prev_c = text[start - 1] if start > 0 else ""
    next2 = text[end:end + 2]
    # Part of a date, time, decimal or grouped number: 08/11, 14:02, 1,250.50, 1800-000-0001
    if prev_c in "/:.,-" and start > 1 and text[start - 2].isdigit():
        return False
    if len(next2) == 2 and next2[0] in "/:.,-" and next2[1].isdigit():
        return False
    return True


def find_otps(text: str) -> list[str]:
    """Return the OTP-like codes found in ``text`` (in order)."""
    if not text:
        return []
    return [m.group(1) for m in CANDIDATE.finditer(text) if _is_otp_at(text, m.start(1), m.end(1))]


def mask_text(text: str) -> str:
    """Replace every OTP-like code in ``text`` with ``[OTP hidden]``."""
    if not text or not isinstance(text, str):
        return text
    out, last = [], 0
    for m in CANDIDATE.finditer(text):
        if _is_otp_at(text, m.start(1), m.end(1)):
            out.append(text[last:m.start(1)])
            out.append(MASK)
            last = m.end(1)
    out.append(text[last:])
    return "".join(out)


def mask_obj(obj: Any) -> Any:
    """Mask OTPs in every string inside a JSON-like structure (dicts, lists, strings)."""
    if isinstance(obj, str):
        return mask_text(obj)
    if isinstance(obj, list):
        return [mask_obj(v) for v in obj]
    if isinstance(obj, dict):
        return {k: mask_obj(v) for k, v in obj.items()}
    return obj


if __name__ == "__main__":
    assert mask_text("Your OTP is 482913. Do not share.") == "Your OTP is [OTP hidden]. Do not share."
    assert mask_text("Rs.1250 debited on 08/11/26") == "Rs.1250 debited on 08/11/26"
    print("otp ok")
