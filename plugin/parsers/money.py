"""Parse Indian bank, card and UPI SMS into transactions.

Input: sender id (e.g. ``AX-HDFCBK``), the SMS timestamp and the body.
Output: a ``Transaction`` or ``None``. OTPs, failed payments, collect requests, promos and
balance-only messages return ``None``. The SMS body itself is never stored: the transaction id is
a hash, and only amount, direction, account last 4, counterparty, channel, bank, ref and
category are kept.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation


@dataclass
class Transaction:
    id: str
    ts: int
    amount_paise: int
    direction: str            # debit | credit
    currency: str = "INR"
    account_last4: str | None = None
    counterparty: str | None = None
    channel: str = "other"    # upi | card | neft | imps | atm | other
    bank: str | None = None
    ref: str | None = None
    category: str = "other"

    def to_dict(self) -> dict:
        return asdict(self)


I = re.IGNORECASE
IGNORE = [
    re.compile(r"\b(otp|one[\s-]?time\s+password|verification\s+code)\b", I),
    re.compile(r"\b(failed|declined|unsuccessful|not\s+successful|could\s+not\s+be\s+processed)\b", I),
    re.compile(r"\b(has\s+requested|requested\s+money|collect\s+request|payment\s+request)\b", I),
    re.compile(r"\b(will\s+be\s+debited|is\s+due|due\s+on|auto[\s-]?debit\s+of\s+.*\s+scheduled)\b", I),
]
DEBIT = re.compile(r"\b(debited|spent|paid|sent|withdrawn|purchase\s+of|txn\s+of|debit\s+of|deducted)\b", I)
CREDIT = re.compile(r"\b(credited|received|deposited|refunded|refund\s+of|credit\s+of)\b", I)
AMOUNT = re.compile(r"(?:rs\.?|inr|₹)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", I)
AMOUNT_AFTER_VERB = re.compile(r"\b(?:debited|credited)\s+(?:by|with|for)\s+([0-9][0-9,]*(?:\.[0-9]{1,2})?)", I)
ACCOUNT = re.compile(r"\b(?:a/c|acct|account|card)(?:\s*no\.?)?(?:\s*ending(?:\s*with)?)?\s*[x*]*\s*(\d{3,6})", I)
VPA = re.compile(r"\b([a-z0-9][a-z0-9.\-_]{1,60}@[a-z][a-z0-9]{1,30})\b", I)
REF = re.compile(r"\b(?:upi\s*ref(?:\s*no)?|ref\s*no|refno|ref|txn\s*id|utr(?:\s*no)?)\.?\s*:?\s*([0-9A-Z]{6,22})\b", I)
UPI_PATH = re.compile(r"\bupi/[a-z0-9]+/(\d{6,22})/([a-z0-9][a-z0-9 .&'\-]{1,40}?)(?=[.,]|\s+not\b|\s*$)", I)
_STOP = r"(?=\s+(?:on|ref\w*|via|avl|not|if|info|at|for|using|upi)\b|\s*[.,(/]|\s*$)"
NAME = r"([a-z][a-z0-9 .&'\-]{0,40}?)"
TO_NAME = re.compile(r"\b(?:to|trf\s+to|transfer\s+to)\s+" + NAME + _STOP, I)
FROM_NAME = re.compile(r"\b(?:from|transfer\s+from)\s+" + NAME + _STOP, I)
AT_NAME = re.compile(r"\b(?:at|on)\s+" + NAME + r"(?=\s+(?:on|from|for|ref\w*)\b|\s*[.,]|\s*$)", I)
NOT_PARTY = re.compile(r"\b(bank|a/c|account|card|your|you|upi|vpa|date|ac)\b|^(mr|ms|rs|inr)$", I)

CATEGORIES = [
    ("food", r"zomato|swiggy|domino|pizza|mcdonald|kfc|burger|restaurant|cafe|starbucks|eats|biryani|"
             r"blinkit|zepto|bigbasket|instamart|grocer|dunzo|chai"),
    ("travel", r"uber|ola\b|rapido|irctc|metro|indigo|air\s?india|vistara|makemytrip|redbus|fuel|petrol|"
               r"hpcl|bpcl|iocl|fastag|parking|cab"),
    ("shopping", r"amazon|flipkart|myntra|ajio|meesho|nykaa|bigbazaar|dmart|reliance|decathlon|croma|mall|store"),
    ("bills", r"electricity|bescom|tneb|msedcl|recharge|airtel|jio|\bvi\b|bsnl|broadband|dth|tatasky|gas|"
              r"water|netflix|spotify|prime|hotstar|youtube|insurance|lic\b|emi|rent\b|bill"),
    ("cash", r"\batm\b"),
    ("transfers", r"\btrf\b|transfer|p2p|neft|imps|rtgs"),
]
CATEGORY_RES = [(name, re.compile(r"\b(?:" + pat + r")", I)) for name, pat in CATEGORIES]


def bank_from_sender(sender: str) -> str | None:
    """``AX-HDFCBK`` -> ``HDFCBK``; phone numbers -> None."""
    s = (sender or "").strip().upper()
    if not s or re.fullmatch(r"\+?\d+", s):
        return None
    return re.sub(r"^[A-Z]{2}-", "", s)[:12] or None


def _amount_paise(text: str) -> int | None:
    m = AMOUNT.search(text) or AMOUNT_AFTER_VERB.search(text)
    if not m:
        return None
    try:
        value = Decimal(m.group(1).replace(",", ""))
    except InvalidOperation:
        return None
    paise = int((value * 100).to_integral_value())
    return paise if paise > 0 else None


def _clean_party(value: str | None) -> str | None:
    if not value:
        return None
    value = re.sub(r"\s+", " ", value).strip(" .-'&")
    if len(value) < 2 or NOT_PARTY.search(value):
        return None
    return value[:40]


def _counterparty(body: str, direction: str) -> tuple[str | None, str | None]:
    """Return (counterparty, ref-from-upi-path)."""
    m = UPI_PATH.search(body)
    if m:
        return _clean_party(m.group(2)), m.group(1)
    vpa = VPA.search(body)
    if vpa:
        return vpa.group(1).lower(), None
    order = (TO_NAME, AT_NAME, FROM_NAME) if direction == "debit" else (FROM_NAME, TO_NAME)
    for rx in order:
        pos = 0
        while (match := rx.search(body, pos)) is not None:   # overlapping: "on Card ... at BLINKIT"
            party = _clean_party(match.group(1))
            if party:
                return party, None
            pos = match.start() + 1
    return None, None


def _channel(body: str, has_vpa: bool) -> str:
    low = body.lower()
    if re.search(r"\batm\b", low):
        return "atm"
    if re.search(r"\b(card|pos)\b", low) and "upi" not in low:
        return "card"
    if "upi" in low or has_vpa:
        return "upi"
    for name in ("neft", "imps", "rtgs"):
        if name in low:
            return "neft" if name == "rtgs" else name
    return "other"


def categorize(counterparty: str | None, body: str, channel: str) -> str:
    hay = f"{counterparty or ''} {body}"
    if channel == "atm":
        return "cash"
    for name, rx in CATEGORY_RES:
        if rx.search(counterparty or "") and name not in ("transfers",):
            return name
    for name, rx in CATEGORY_RES:
        if rx.search(hay):
            return name
    return "other"


def transaction_id(sender: str, ts: int, body: str) -> str:
    return hashlib.sha256(f"{sender}\n{ts}\n{body}".encode("utf-8")).hexdigest()[:32]


def parse(sender: str, ts: int, body: str) -> Transaction | None:
    """Parse one SMS. Returns None for anything that is not a completed debit or credit."""
    if not body or not isinstance(body, str):
        return None
    if bank_from_sender(sender) is None:   # banks use sender ids (AX-HDFCBK); people's texts are not transactions
        return None
    if any(rx.search(body) for rx in IGNORE):
        return None
    d, c = DEBIT.search(body), CREDIT.search(body)
    if not d and not c:
        return None   # promos and balance-only messages have no transaction verb
    direction = "debit" if d and (not c or d.start() < c.start()) else "credit"
    amount = _amount_paise(body)
    if amount is None:
        return None
    party, upi_ref = _counterparty(body, direction)
    acct = ACCOUNT.search(body)
    ref = upi_ref
    if ref is None:
        rm = REF.search(body)
        ref = rm.group(1) if rm and any(ch.isdigit() for ch in rm.group(1)) else None
    channel = _channel(body, bool(VPA.search(body)))
    return Transaction(
        id=transaction_id(sender, ts, body), ts=int(ts), amount_paise=amount, direction=direction,
        account_last4=acct.group(1)[-4:] if acct else None, counterparty=party, channel=channel,
        bank=bank_from_sender(sender), ref=ref, category=categorize(party, body, channel),
    )
