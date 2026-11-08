"""Find upcoming bills and dues in SMS.

Input: sender id (e.g. ``VM-BESCOM``), the SMS timestamp and the body. ``parse`` returns
``{"biller", "amount_paise", "due_date", "kind", "source_sender"}`` for a bill, statement, EMI or
premium that is due, or ``None``. ``due_date`` is ``YYYY-MM-DD`` or ``None`` when the message has no
readable date. Payment confirmations, OTPs, promos, scams and texts from personal numbers return
``None``; ``paid_biller`` recognises the confirmations so a later "thank you for your payment" can
cancel an earlier due. Pure functions: nothing is stored.
"""
from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal, InvalidOperation

from . import money, scam

I = re.IGNORECASE
PAID = re.compile(r"\bthank(?:s|\s+you)\s+for\s+(?:your\s+|the\s+)?payment|\bpayment\s+(?:of\s+.{0,40}?)?"
                  r"(?:has\s+been\s+|is\s+|was\s+)?(?:received|successful|credited|realised|realized)|"
                  r"\bsuccessfully\s+paid\b|\bpaid\s+successfully\b|\breceived\s+(?:your\s+|the\s+)?payment\b|"
                  r"\b(?:bill|dues?|emi|premium)\s+(?:has\s+been\s+|is\s+|was\s+)?paid\b|"
                  r"\b(?:has\s+been|was)\s+(?:auto[\s-]?)?debited\b", I)   # not "will be / is debited on"
OTP = re.compile(r"\b(?:otp|one[\s-]?time\s+password|verification\s+code)\b", I)   # same test as the money parser
DUE_WORD = re.compile(r"\b(?:due|pay(?:able)?\s+(?:by|before)|last\s+date)\b", I)
KINDS = [   # first match wins: a card statement can mention "gas" or "mobile" in passing
    ("credit_card", r"credit\s*card|card\s+statement|total\s+amount\s+due|minimum\s+amount\s+due|min(?:imum)?\s+due"),
    ("emi", r"\bemi\b|\bloan\b|\binstal+ment\b"),
    ("insurance", r"insurance|\bpremium\b|\bpolicy\b|\blic\b"),
    ("electricity", r"electricity|power\s+bill|\bkwh\b|bescom|tneb|tangedco|msedcl|tata\s*power|adani\s*electricity|"
                    r"\bcesc\b|\bbses\b|torrent\s*power|uppcl|\bkseb\b|energy\s+bill"),
    ("water", r"water\s+(?:bill|charges|tax)|bwssb|jal\s+board|water\s+supply"),
    ("gas", r"\bgas\b|\blpg\b|\bpng\b|indane|bharat\s*gas|mahanagar|\bmgl\b|\bigl\b"),
    ("broadband", r"broadband|fib(?:er|re)|fibernet|\bftth\b|internet\s+bill|hathway|excitel|xstream"),
    ("mobile", r"postpaid|mobile\s+bill|phone\s+bill|\bairtel\b|\bjio\b|\bvi\b|vodafone|\bbsnl\b"),
]
KIND_RES = [(name, re.compile(pat, I)) for name, pat in KINDS]
BILLERS = [   # display names; checked against the body, then the sender id
    ("BESCOM", r"bescom"), ("TANGEDCO", r"tneb|tangedco"), ("MSEDCL", r"msedcl|mahadiscom"),
    ("Tata Power", r"tata\s*power"), ("Adani Electricity", r"adani\s*electricity"), ("BSES", r"\bbses"),
    ("BWSSB", r"bwssb"), ("Delhi Jal Board", r"jal\s+board"), ("Indane", r"indane"), ("HP Gas", r"hp\s*gas"),
    ("Bharat Gas", r"bharat\s*gas"), ("Mahanagar Gas", r"mahanagar|\bmgl\b"), ("IGL", r"\bigl\b"),
    ("ACT Fibernet", r"\bact\s*fib|actfbr"), ("Hathway", r"hathway"), ("Excitel", r"excitel"),
    ("JioFiber", r"jio\s*fib"), ("Airtel", r"airtel"), ("Jio", r"\bjio\b"), ("Vi", r"\bvi\b|vodafone|vilpre"),
    ("BSNL", r"bsnl"), ("LIC", r"\blic\b"), ("HDFC Life", r"hdfc\s*life"), ("ICICI Prudential", r"icici\s*pru"),
    ("Bajaj Finserv", r"bajaj\s*fin"), ("SBI Card", r"sbi\s*card|sbicrd"), ("HDFC Bank", r"hdfc"),
    ("ICICI Bank", r"icici"), ("Axis Bank", r"\baxis"), ("Kotak", r"kotak"), ("American Express", r"amex|american\s+express"),
    ("IDFC First Bank", r"idfc"), ("SBI", r"\bsbi"),
]
BILLER_RES = [(name, re.compile(pat, I)) for name, pat in BILLERS]
TOTAL = re.compile(r"total|amount\s+due|bill\s+amount|outstanding|payable|bill\s+of|premium\s+of|emi\s+of", I)
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
DATE = re.compile(
    r"(?<!\d)(?P<iy>20\d\d)-(?P<im>\d{1,2})-(?P<id>\d{1,2})(?!\d)"
    r"|(?<!\d)(?P<d>\d{1,2})[-/.](?P<m>\d{1,2})[-/.](?P<y>\d{4}|\d{2})(?!\d)"
    r"|(?<!\d)(?P<d2>\d{1,2})(?:st|nd|rd|th)?[-\s]?(?P<mon>" + MONTHS + r")[a-z]*\.?(?:[-\s,']*(?P<y2>\d{4}|\d{2})(?!\d))?"
    r"|\b(?P<mon3>" + MONTHS + r")[a-z]*\.?\s+(?P<d3>\d{1,2})(?:st|nd|rd|th)?(?!\d)(?:,?\s*(?P<y3>\d{4}))?", I)


def _kind(body: str) -> str | None:
    return next((name for name, rx in KIND_RES if rx.search(body)), None)


def _biller(sender: str, body: str, kind: str | None) -> str | None:
    name = next((n for n, rx in BILLER_RES if rx.search(body)), None)
    name = name or next((n for n, rx in BILLER_RES if rx.search(sender or "")), None)
    name = name or money.bank_from_sender(sender)
    if name and kind == "credit_card" and "card" not in name.lower():
        name += " credit card"   # ponytail: no card last-4 in the name, so two cards of one bank merge
    return name


def _paise(raw: str) -> int | None:
    try:
        paise = int((Decimal(raw.replace(",", "")) * 100).to_integral_value())
    except InvalidOperation:
        return None
    return paise if paise > 0 else None


def _amount(body: str) -> int | None:
    """The bill total: skip 'minimum due' amounts, prefer one labelled total / amount due."""
    first, prev_end = None, 0
    for m in money.AMOUNT.finditer(body):
        label = body[max(prev_end, m.start() - 30):m.start()]
        prev_end = m.end()
        if re.search(r"\bmin", label, I):
            continue
        paise = _paise(m.group(1))
        if paise and TOTAL.search(label):
            return paise
        first = first or paise
    return first


def _to_date(m: re.Match, base: dt.date) -> dt.date | None:
    g = m.groupdict()
    try:
        if g["iy"]:
            return dt.date(int(g["iy"]), int(g["im"]), int(g["id"]))
        if g["d"]:
            y = int(g["y"])
            return dt.date(y + 2000 if y < 100 else y, int(g["m"]), int(g["d"]))
        mon = (g["mon"] or g["mon3"]).lower()[:3]
        day, year = int(g["d2"] or g["d3"]), g["y2"] or g["y3"]
        month = MONTHS.split("|").index(mon) + 1
        if year:
            y = int(year)
            return dt.date(y + 2000 if y < 100 else y, month, day)
        when = dt.date(base.year, month, day)
        return when.replace(year=base.year + 1) if when < base - dt.timedelta(days=60) else when
    except ValueError:   # 31-02-26 and friends: no date rather than a crash
        return None


def due_date(body: str, ts: int) -> str | None:
    """The date written right after 'due' / 'pay by' / 'last date', as YYYY-MM-DD."""
    base = dt.date.fromtimestamp(ts) if ts else dt.date.today()
    for kw in DUE_WORD.finditer(body):
        window = re.split(r"\.\s|;|\n", body[kw.end():kw.end() + 40])[0]
        for m in DATE.finditer(window):
            when = _to_date(m, base)
            if when and 2000 <= when.year <= 2100:
                return when.isoformat()
    return None


def paid_biller(sender: str, body: str) -> str | None:
    """Biller name when this SMS confirms a bill payment, else None."""
    if not body or money.bank_from_sender(sender) is None or not PAID.search(body):
        return None
    kind = _kind(body)
    return _biller(sender, body, kind) if kind else None


def parse(sender: str, ts: int, body: str) -> dict | None:
    """Parse one SMS into a due bill, or None."""
    if not body or not isinstance(body, str) or money.bank_from_sender(sender) is None:
        return None   # billers use sender ids; a "bill" from a personal number is not one
    if PAID.search(body) or OTP.search(body) or not DUE_WORD.search(body):
        return None
    kind = _kind(body)
    amount = _amount(body)
    if not kind or amount is None or scam.score(body)["level"] == "high":
        return None
    return {"biller": _biller(sender, body, kind), "amount_paise": amount, "due_date": due_date(body, ts),
            "kind": kind, "source_sender": money.bank_from_sender(sender)}
