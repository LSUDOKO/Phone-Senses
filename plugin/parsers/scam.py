"""Score SMS for scam risk with simple, explainable weighted rules.

Score 0-100. ``>= 60`` is high, ``30-59`` medium, otherwise low. Every hit adds a reason so the
user can see *why* a message was flagged. Rules target the common Indian SMS scams: fake KYC /
account blocking, electricity disconnection, lottery prizes, parcel re-delivery fees, refund
apps, and look-alike links.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

I = re.IGNORECASE
URL = re.compile(r"\b((?:https?://|www\.)[^\s]+|(?:bit\.ly|tinyurl\.com|goo\.gl|t\.ly|cutt\.ly|is\.gd|rb\.gy|"
                 r"shorturl\.at|tiny\.cc|ow\.ly)/[^\s]*)", I)
SHORTENERS = ("bit.ly", "tinyurl.com", "goo.gl", "t.ly", "cutt.ly", "is.gd", "rb.gy", "shorturl.at",
              "tiny.cc", "ow.ly")
BRANDS = ("sbi", "hdfc", "icici", "axis", "kotak", "paytm", "phonepe", "gpay", "indiapost", "amazon",
          "flipkart", "bescom", "electricity", "income-tax", "incometax", "npci", "uidai", "aadhaar", "kyc")
OFFICIAL = ("onlinesbi.sbi", "sbi.co.in", "hdfcbank.com", "icicibank.com", "axisbank.com", "kotak.com",
            "paytm.com", "phonepe.com", "indiapost.gov.in", "amazon.in", "amazon.com", "flipkart.com",
            "incometax.gov.in", "npci.org.in", "uidai.gov.in")
RISKY_TLDS = (".xyz", ".top", ".site", ".club", ".online", ".info", ".live", ".icu", ".buzz", ".shop",
              ".click", ".link", ".rest", ".co", ".ly", ".cc", ".tk", ".ml", ".ga", ".cf")

RULES: list[tuple[str, int, re.Pattern]] = [
    ("urgency", 25, re.compile(r"\b(blocked|suspended|deactivated|disconnected|will\s+be\s+(?:closed|"
                               r"blocked|suspended|disconnected)|immediately|urgent(?:ly)?|within\s+24\s+h(?:ou)?rs?|"
                               r"tonight|expires?\s+today|last\s+warning|final\s+notice)\b", I)),
    ("kyc / identity update", 30, re.compile(r"\b(kyc|pan\s*card|aadha?ar)\b.{0,40}\b(update|verify|"
                                             r"verification|expired?|pending|link)\b|\bupdate\s+(?:your\s+)?(kyc|pan)\b", I)),
    ("electricity disconnection", 30, re.compile(r"\belectricity\b.{0,80}\b(disconnect|cut|bill\s+not\s+"
                                                 r"(?:paid|updated))", I | re.S)),
    ("prize / lottery", 35, re.compile(r"\b(congratulations|you\s+(?:have\s+)?won|lucky\s+draw|lottery|"
                                       r"jackpot|kbc|prize|winner|claim\s+your)\b", I)),
    ("parcel / delivery fee", 20, re.compile(r"\b(parcel|package|shipment|courier)\b.{0,80}\b(not\s+be\s+"
                                             r"delivered|could\s+not|undelivered|re-?delivery|held|address)", I | re.S)),
    ("refund bait", 20, re.compile(r"\b(refund|cashback\s+of|tax\s+refund)\b.{0,60}\b(claim|click|install|"
                                   r"get|link)\b|\bto\s+get\s+your\s+refund\b", I | re.S)),
    ("asks to install an app", 35, re.compile(r"\.apk\b|\b(install|download)\s+(?:this|the|our)?\s*app\b|"
                                              r"\b(anydesk|teamviewer|quicksupport|rustdesk)\b", I)),
    ("asks for OTP / PIN", 30, re.compile(r"\b(share|send|tell|forward)\b.{0,20}\b(otp|pin|cvv|password)\b", I)),
]
CALL_NUMBER = re.compile(r"\b(?:call|contact|whatsapp|dial)\b[^0-9+]{0,25}(\+?\d[\d\s-]{8,14}\d)", I)
PAY_WITH_LINK = re.compile(r"\b(pay|fee|charges?|penalty)\b", I)
DO_NOT_SHARE = re.compile(r"\b(do\s+not|don't|never)\s+share\b", I)


def _domain(url: str) -> str:
    if not re.match(r"https?://", url, I):
        url = "http://" + url
    try:
        return (urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def score(body: str) -> dict:
    """Return {"score": 0-100, "level": "low|medium|high", "reasons": [...]} for one message."""
    text = body or ""
    total, reasons = 0, []
    for name, weight, rx in RULES:
        m = rx.search(text)
        if not m:
            continue
        if name == "asks for OTP / PIN" and DO_NOT_SHARE.search(text):
            continue
        total += weight
        reasons.append(f"{name}: '{m.group(0)[:40].strip()}'")

    urls = [u.rstrip(".,)") for u in URL.findall(text)]
    domains = [d for d in (_domain(u) for u in urls) if d]
    flagged_domain = False
    for d in domains:
        if any(d == s or d.endswith("." + s) for s in SHORTENERS):
            total += 25
            reasons.append(f"link shortener: {d}")
            break
    for d in domains:
        if any(d == o or d.endswith("." + o) for o in OFFICIAL + SHORTENERS):
            continue
        brand = next((b for b in BRANDS if b in d), None)
        if brand or d.endswith(RISKY_TLDS):
            total += 30
            reasons.append(f"look-alike or risky link: {d}" if brand else f"risky link domain: {d}")
            flagged_domain = True
            break
    if urls and not flagged_domain and any(u.lower().startswith("http://") for u in urls):
        total += 10
        reasons.append("unencrypted http link")
    if urls and PAY_WITH_LINK.search(text):
        total += 20
        reasons.append("asks for payment through a link")

    m = CALL_NUMBER.search(text)
    if m:
        digits = re.sub(r"\D", "", m.group(1))
        if not digits.startswith(("1800", "1860")) and total >= 20:   # toll-free bank lines are normal
            total += 20
            reasons.append(f"asks you to call a personal number: {m.group(1).strip()}")

    total = min(total, 100)
    level = "high" if total >= 60 else "medium" if total >= 30 else "low"
    return {"score": total, "level": level, "reasons": reasons}
