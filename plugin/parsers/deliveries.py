"""Read order and parcel status from shopping, food-delivery and courier SMS or notifications.

``parse(sender, text)`` takes an SMS sender id (``AX-AMAZON``) or a notification's package and title,
plus the text, and returns ``{"merchant", "status", "item", "order_id", "eta"}`` or ``None``.
Statuses: ordered, shipped, out_for_delivery, delivered, failed_attempt, cancelled. Promos, OTPs
without a status, payments and scam "parcel fee" texts return ``None``. Pure functions.
"""
from __future__ import annotations

import re

from . import scam

I = re.IGNORECASE
MERCHANTS = [   # matched against the sender / package first, then the text
    ("Amazon", r"amazon|amzn"), ("Flipkart", r"flipkart|flpkrt|flipkt"), ("Myntra", r"myntra"),
    ("Meesho", r"meesho"), ("Swiggy", r"swiggy|instamart"), ("Zomato", r"zomato"), ("Zepto", r"zepto"),
    ("Blinkit", r"blinkit|blinkt|grofers"), ("Delhivery", r"delhivery|dlhvry|delhvy"),
    ("Blue Dart", r"blue\s?dart|bludrt|bldart"), ("Ekart", r"ekart"),
    ("India Post", r"india\s?post|indpst|speed\s?post"), ("DTDC", r"dtdc"), ("Shadowfax", r"shadowfax|shdwfx"),
]
MERCHANT_RES = [(name, re.compile(pat, I)) for name, pat in MERCHANTS]
ACTIVE = ("ordered", "shipped", "out_for_delivery", "failed_attempt")
FUTURE = re.compile(r"\b(?:will|to|would|should|shall)\s+(?:be|get)\s+delivered\b|\bdelivered\s+by\b|"
                    r"\bgetting\s+delivered\b", I)
STATUSES = [   # first match wins (checked on the text with future "will be delivered" removed)
    ("cancelled", r"\bcancel+ed\b|\bcancellation\s+(?:is\s+)?(?:confirmed|successful)"),
    ("failed_attempt", r"\bdelivery\s+attempt(?:ed)?\b|\battempted\s+delivery|\b(?:could\s+not|couldn'?t|unable\s+to|"
                       r"failed\s+to)\s+(?:be\s+)?deliver|\bdelivery\s+(?:has\s+)?failed|\bundelivered\b|"
                       r"\bmissed\s+(?:your|the)\s+delivery|\baddressee\s+(?:not\s+available|absent)"),
    ("delivered", r"\bdelivered\b"),
    ("out_for_delivery", r"\bout\s+for\s+delivery\b|\barriving\s+(?:today|now|soon|in\s+\d+)|"
                         r"\b(?:is|are)\s+on\s+(?:the|their|his|her)\s+way\b|\bwill\s+reach\s+you\s+(?:today|in|shortly|soon)|"
                         r"\breaching\s+you\b|\bdelivery\s+partner\s+(?:is|has)\b"),
    ("shipped", r"\bshipped\b|\bdispatched\b|\bin\s+transit\b|\bon\s+its\s+way\b|\bhas\s+left\b|\bpicked\s+up\b|"
                r"\barriving\s+(?:on|by|tomorrow)\b|\bexpected\s+delivery\b|\bdelivery\s+by\b|\bwill\s+be\s+delivered\b"),
    ("ordered", r"\border\s+(?:has\s+been\s+|is\s+|was\s+)?(?:placed|confirmed|received)\b|\breceived\s+your\s+order\b|"
                r"\bthank(?:s|\s+you)\s+for\s+(?:your\s+)?(?:order|ordering|shopping)\b|\bpreparing\s+your\s+order\b"),
]
STATUS_RES = [(name, re.compile(pat, I)) for name, pat in STATUSES]
ORDER_ID = re.compile(r"\b(?:order|ord|awb|tracking|shipment|consignment|article)\s*(?:id|no\.?|number)?\s*[:#]?\s*#?\s*"
                      r"([A-Z0-9][A-Z0-9-]{5,24})\b", I)
ETA = re.compile(r"\b(?:arriving|arrives|expected\s+delivery|estimated\s+delivery|delivery\s+expected|deliver(?:ed|y)?\s+by|"
                 r"will\s+be\s+delivered|will\s+reach\s+you|re-?attempted)\b(?:\s+(?:by|on))?\s*:?\s*([^.;!\n]{2,30})", I)
ITEMS = [
    re.compile(r"(?:^|[.!]\s+)(?:shipped|delivered|dispatched|out\s+for\s+delivery|cancel+ed)\s*:\s*([^.!\n|]{2,60})", I),
    re.compile(r"\b(?:order|package|parcel|shipment)\s+(?:for|of|containing|with)\s+([^.,;!\n]{2,60}?)\s+"
               r"(?:has|have|is|are|was|were|will)\b", I),
]
GENERIC = {"your", "the", "order", "orders", "package", "parcel", "shipment", "item", "items", "product", "products",
           "food", "a", "an", "new", "my"}


def merchant(sender: str, text: str) -> str | None:
    for hay in (sender or "", text or ""):
        name = next((n for n, rx in MERCHANT_RES if rx.search(hay)), None)
        if name:
            return name
    return None


def status(text: str) -> str | None:
    plain = FUTURE.sub(" ", text)
    for name, rx in STATUS_RES:
        if rx.search(plain if name in ("delivered", "failed_attempt", "cancelled") else text):
            return name
    return None


def _item(text: str, shop: str) -> str | None:
    for rx in ITEMS:
        m = rx.search(text)
        if m:
            item = re.sub(r"\s+", " ", m.group(1)).strip(" '\"-,")
            if set(re.findall(r"[a-z]+", item.lower())) - GENERIC - {shop.lower()}:
                return item[:40]
    return None


def _order_id(text: str) -> str | None:
    return next((m.group(1).upper() for m in ORDER_ID.finditer(text) if any(c.isdigit() for c in m.group(1))), None)


def parse(sender: str, text: str) -> dict | None:
    """Parse one SMS or notification into a delivery update, or None."""
    if not text or not isinstance(text, str):
        return None
    shop = merchant(sender, text)
    state = status(text) if shop else None
    if not state or scam.score(text)["level"] == "high":
        return None   # "your parcel is held, pay a fee" scams name India Post too
    eta = ETA.search(text) if state in ACTIVE else None
    return {"merchant": shop, "status": state, "item": _item(text, shop), "order_id": _order_id(text),
            "eta": eta.group(1).strip(" ,-")[:30] if eta else None}


def same_order(group: dict, update: dict) -> bool:
    """Whether ``update`` belongs to an earlier ``group`` (same merchant, and id or item agree)."""
    if group["merchant"] != update["merchant"]:
        return False
    if group["status"] in ("delivered", "cancelled") and update["status"] == "ordered":
        return False   # a new order from the same shop
    if group.get("order_id") and update.get("order_id"):
        return group["order_id"] == update["order_id"]
    if group.get("item") and update.get("item"):
        return group["item"].lower() == update["item"].lower()
    return True   # ponytail: id-less, item-less updates join the shop's latest order; fine for food apps


def group_updates(updates: list[dict]) -> list[dict]:
    """Merge updates (each with a ``ts``) into one entry per order holding the latest status."""
    groups: list[dict] = []
    for u in sorted(updates, key=lambda u: u["ts"]):
        g = next((g for g in reversed(groups) if same_order(g, u)), None)
        if g is None:
            groups.append(dict(u))
            continue
        for key in ("order_id", "item"):
            g[key] = g.get(key) or u.get(key)
        g.update(status=u["status"], ts=u["ts"], source=u.get("source", g.get("source")),
                 eta=u.get("eta") if u["status"] in ACTIVE else None)
    return groups
