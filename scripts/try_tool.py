#!/usr/bin/env python3
"""Call a Phone Senses tool from the terminal, without Hermes (for testing and demos).

    python scripts/try_tool.py phone_status
    python scripts/try_tool.py phone_money_summary period=week
    python scripts/try_tool.py phone_sms_list query=swiggy limit=5
    python scripts/try_tool.py /phone money week          # the slash command

Options come from the environment:
    PHONE_SENSES_URL     helper address (default http://127.0.0.1:8765)
    PHONE_SENSES_SECRET  path to the pairing secret file (default ~/.phone-senses/secret)
Data (transactions, watch rules) goes to a scratch SQLite file, ./.try_tool.db, not to Hermes.
Note: approval prompts exist only inside Hermes; this script calls tools directly.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_plugin():
    spec = importlib.util.spec_from_file_location("phone_senses", ROOT / "plugin" / "__init__.py",
                                                  submodule_search_locations=[str(ROOT / "plugin")])
    module = importlib.util.module_from_spec(spec)
    sys.modules["phone_senses"] = module
    spec.loader.exec_module(module)
    return module


def parse_value(raw: str):
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    ps = load_plugin()
    secret_file = Path(os.environ.get("PHONE_SENSES_SECRET", Path.home() / ".phone-senses" / "secret"))
    secret = secret_file.read_text().strip() if secret_file.exists() else ""
    url = os.environ.get("PHONE_SENSES_URL", "http://127.0.0.1:8765")
    ps.client.set_client(ps.client.PhoneClient(url, secret))
    db = ROOT / ".try_tool.db"
    ps.storage.set_connector(lambda: sqlite3.connect(db))
    if argv[0] == "/phone":
        print(ps.commands.handle(" ".join(argv[1:])))
        return 0
    name, args = argv[0], dict(a.split("=", 1) for a in argv[1:])
    if name not in ps.tools.HANDLERS:
        print(f"Unknown tool {name}. Tools: {', '.join(ps.tools.HANDLERS)}")
        return 1
    if name in ps.approvals.NEEDS_APPROVAL:
        print(f"[Hermes would ask first] {ps.approvals.summary(name, args)}")
    out = ps.tools.HANDLERS[name]({k: parse_value(v) for k, v in args.items()})
    data = out if isinstance(out, dict) else json.loads(out)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
