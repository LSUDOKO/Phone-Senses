"""Durable storage in Hermes's plugin data folder (``plugin_db("phone-senses")``).

Stores parsed transactions (no SMS text), budgets, watch rules and "last seen" cursors.
Amounts are integer paise. A connection is opened per operation, because ``plugin_db`` follows
the active Hermes profile and must not be cached across profile switches.
"""
from __future__ import annotations

import contextlib
import json
import sqlite3
import time
from typing import Any, Callable, Iterator

PLUGIN = "phone-senses"

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
  id TEXT PRIMARY KEY,
  ts INTEGER NOT NULL,
  amount_paise INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'INR',
  direction TEXT NOT NULL CHECK (direction IN ('debit','credit')),
  account_last4 TEXT,
  counterparty TEXT,
  channel TEXT,
  bank TEXT,
  ref TEXT,
  category TEXT NOT NULL DEFAULT 'other'
);
CREATE INDEX IF NOT EXISTS transactions_ts ON transactions(ts);
CREATE TABLE IF NOT EXISTS budgets (category TEXT PRIMARY KEY, monthly_limit_paise INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS watch_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,
  params_json TEXT NOT NULL, created_ts INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS cursors (name TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

TX_COLUMNS = ("id", "ts", "amount_paise", "currency", "direction", "account_last4", "counterparty",
              "channel", "bank", "ref", "category")

_connect_override: Callable[[], sqlite3.Connection] | None = None


def set_connector(factory: Callable[[], sqlite3.Connection] | None) -> None:
    """Test hook: supply connections (e.g. a temp-file database)."""
    global _connect_override
    _connect_override = factory


def _open() -> sqlite3.Connection:
    if _connect_override is not None:
        return _connect_override()
    from plugins.plugin_storage import plugin_db   # Hermes public storage helper
    return plugin_db(PLUGIN)


@contextlib.contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = _open()
    try:
        conn.executescript(SCHEMA)
        with conn:   # commit on success, roll back on error
            yield conn
    finally:
        conn.close()


# --- transactions -----------------------------------------------------------

def add_transactions(txs: list[dict]) -> int:
    """Insert new transactions; duplicates (same id) are skipped. Returns how many were new."""
    if not txs:
        return 0
    with connect() as conn:
        before = conn.total_changes
        conn.executemany(
            f"INSERT OR IGNORE INTO transactions ({', '.join(TX_COLUMNS)}) "
            f"VALUES ({', '.join('?' * len(TX_COLUMNS))})",
            [tuple(tx.get(c) for c in TX_COLUMNS) for tx in txs],
        )
        return conn.total_changes - before


def transactions(start_ts: int, end_ts: int, direction: str = "both") -> list[dict]:
    sql = f"SELECT {', '.join(TX_COLUMNS)} FROM transactions WHERE ts >= ? AND ts < ?"
    args: list[Any] = [start_ts, end_ts]
    if direction in ("debit", "credit"):
        sql += " AND direction = ?"
        args.append(direction)
    with connect() as conn:
        rows = conn.execute(sql + " ORDER BY ts DESC", args).fetchall()
    return [dict(zip(TX_COLUMNS, row)) for row in rows]


def recent_debits(counterparty: str | None, since_ts: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            f"SELECT {', '.join(TX_COLUMNS)} FROM transactions WHERE direction='debit' AND ts >= ? "
            "AND (counterparty IS ? OR counterparty = ?) ORDER BY ts DESC LIMIT 200",
            (since_ts, counterparty, counterparty)).fetchall()
    return [dict(zip(TX_COLUMNS, row)) for row in rows]


def median_debit(since_ts: int) -> int | None:
    with connect() as conn:
        rows = [r[0] for r in conn.execute(
            "SELECT amount_paise FROM transactions WHERE direction='debit' AND ts >= ? ORDER BY amount_paise",
            (since_ts,))]
    return rows[len(rows) // 2] if len(rows) >= 5 else None


# --- budgets ----------------------------------------------------------------

def set_budget(category: str, monthly_limit_paise: int) -> None:
    with connect() as conn:
        if monthly_limit_paise <= 0:
            conn.execute("DELETE FROM budgets WHERE category = ?", (category,))
        else:
            conn.execute("INSERT INTO budgets (category, monthly_limit_paise) VALUES (?, ?) "
                         "ON CONFLICT(category) DO UPDATE SET monthly_limit_paise = excluded.monthly_limit_paise",
                         (category, monthly_limit_paise))


def budgets() -> dict[str, int]:
    with connect() as conn:
        return dict(conn.execute("SELECT category, monthly_limit_paise FROM budgets").fetchall())


# --- watch rules ------------------------------------------------------------

def add_rule(kind: str, params: dict) -> int:
    with connect() as conn:
        cur = conn.execute("INSERT INTO watch_rules (kind, params_json, created_ts) VALUES (?, ?, ?)",
                           (kind, json.dumps(params, ensure_ascii=False), int(time.time())))
        return int(cur.lastrowid)


def rules(enabled_only: bool = False) -> list[dict]:
    sql = "SELECT id, kind, params_json, created_ts, enabled FROM watch_rules"
    if enabled_only:
        sql += " WHERE enabled = 1"
    with connect() as conn:
        rows = conn.execute(sql + " ORDER BY id").fetchall()
    return [{"id": r[0], "kind": r[1], "params": json.loads(r[2]), "created_ts": r[3], "enabled": bool(r[4])}
            for r in rows]


def remove_rule(rule_id: int) -> bool:
    with connect() as conn:
        return conn.execute("DELETE FROM watch_rules WHERE id = ?", (rule_id,)).rowcount > 0


# --- cursors ----------------------------------------------------------------

def get_cursor(name: str, default: str | None = None) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT value FROM cursors WHERE name = ?", (name,)).fetchone()
    return row[0] if row else default


def set_cursor(name: str, value: str) -> None:
    with connect() as conn:
        conn.execute("INSERT INTO cursors (name, value) VALUES (?, ?) "
                     "ON CONFLICT(name) DO UPDATE SET value = excluded.value", (name, value))
