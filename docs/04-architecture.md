# 04: Architecture

```
┌──────────────────────────── Laptop / PC ───────────────────────────┐        ┌────────── Android phone ──────────┐
│ Hermes Agent                                                        │        │ Termux                             │
│  └─ phone-senses plugin                                             │  HTTP  │  └─ phone_helper/helper.py          │
│      ├─ tools (phone_*) ──► client.py ── HMAC-signed JSON ─────────────────────►     (stdlib http.server)          │
│      ├─ pre_tool_call hook (approvals)                              │ LAN or │        └─ subprocess (no shell) ──►  │
│      ├─ parsers: otp, money, scam                                   │Tailscale│           termux-* (Termux:API)     │
│      ├─ storage: plugin_db (SQLite): transactions, watch rules      │        │              └─ Android APIs        │
│      ├─ /phone command, bundled skill                               │        │                                     │
│      └─ (P2) Desktop pane                                           │        │                                     │
└─────────────────────────────────────────────────────────────────────┘        └─────────────────────────────────────┘
```

Design principles:
- **Thin helper, smart plugin.** The phone side only runs whitelisted `termux-*` commands and
  returns their JSON. Parsing, masking, money logic, scam scoring and storage live in the plugin,
  where they are easy to test.
- **Mock first.** `helper.py --mock` serves fixture data for every endpoint so the plugin can be
  developed and tested without a phone.
- **Fail clearly.** Every failure becomes a helpful JSON error the agent can explain to the user.

## Repository layout
> **As built:** the plugin files below live in `plugin/` (catalog `subdir: plugin`), and
> `phone_helper/`, `tests/`, `scripts/` and `docs/` sit at the repo root, outside the install tree.

```
phone-senses/                    # repo root = plugin root
├── plugin.yaml                  # manifest (see 05-hermes-plugin-reference.md)
├── __init__.py                  # register(ctx): tools, hook, command, skill
├── schemas.py                   # tool JSON schemas (what the model reads)
├── tools.py                     # tool handlers (never raise; return JSON strings)
├── client.py                    # HTTP client to the helper: signing, timeouts, errors
├── approvals.py                 # pre_tool_call hook logic
├── parsers/
│   ├── __init__.py
│   ├── otp.py                   # detect + mask OTPs
│   ├── money.py                 # bank/UPI SMS → Transaction
│   └── scam.py                  # scam risk scoring
├── storage.py                   # plugin_db tables + queries
├── watch.py                     # watch rules engine
├── commands.py                  # /phone slash command
├── skills/phone-senses/SKILL.md # bundled skill
├── desktop/                     # (P2) Desktop pane, only if the SDK is verified
├── phone_helper/
│   ├── helper.py                # runs in Termux on the phone (stdlib only)
│   ├── commands.py              # endpoint → fixed argv mapping + validation
│   ├── mock_data/               # synthetic fixture JSON for --mock
│   └── README.md                # phone-side install and run steps
├── tests/
│   ├── fixtures/                # synthetic SMS / notification samples
│   ├── test_otp.py  test_money.py  test_scam.py  test_client.py  test_tools.py  test_helper.py
├── assets/                      # banner.png (1200x600), screenshots for README/catalog
├── README.md
└── LICENSE                      # MIT
```
Note: `tests/`, `phone_helper/` and `assets/` live inside the plugin directory. That is fine, but
the `hermes plugins validate` security scan reads everything, so keep it clean (no binaries).

## Phone helper HTTP API (v1)

### Transport and auth
- Plain HTTP on a private network (`--host` = the phone's LAN or Tailscale IP, `--port` default 8765).
  Recommend **Tailscale** (encrypted, works outside home Wi-Fi).
- **Pairing:** on first run `helper.py --pair` generates a 32-byte random secret, stores it in
  `~/.phone-senses/secret` (mode 600) and prints it once as a pairing code. The user pastes it into
  the plugin setting `helper_token` (a `secret` field).
- **Request signing (HMAC-SHA256), the secret is never sent:**
  - Headers: `X-PS-Timestamp` (unix seconds), `X-PS-Nonce` (random hex 16), `X-PS-Signature`.
  - `signature = hex(HMAC_SHA256(secret, METHOD + "\n" + PATH_WITH_QUERY + "\n" + TIMESTAMP + "\n" + NONCE + "\n" + SHA256_HEX(BODY)))`
  - Helper rejects requests with timestamp skew > 60 s, reused nonces (keep the last 1,000), or a
    bad signature (constant-time compare).
- All responses: `{"ok": true, "data": ...}` or `{"ok": false, "error": "code", "message": "..."}`.
- Error codes: `unauthorized`, `bad_request`, `permission_denied` (Android permission missing),
  `termux_api_missing`, `timeout`, `not_supported` (e.g. no IR blaster), `internal`.
- Rate limit: 10 requests per second; `sms/send` and `call` max 5 per minute.

### Endpoints
| Method | Path | Termux command (fixed argv) | Notes |
|---|---|---|---|
| GET | `/v1/ping` | none | `{helper_version, device_model, features[]}`; unauthenticated ping returns only `{ok}` |
| GET | `/v1/status` | `termux-battery-status`, `termux-wifi-connectioninfo` | merged JSON |
| GET | `/v1/notifications` | `termux-notification-list` | needs Notification access |
| GET | `/v1/sms?limit=&offset=&box=` | `termux-sms-list -l N -o N -t inbox` | VERIFY flags with `termux-sms-list -h` |
| POST | `/v1/sms/send` `{to, text}` | `termux-sms-send -n <to> <text>` | `to` must match `^\+?[0-9]{6,15}$`; text ≤ 480 chars |
| GET | `/v1/calls?limit=` | `termux-call-log -l N` | |
| GET | `/v1/contacts` | `termux-contact-list` | plugin filters by query |
| GET | `/v1/location?provider=network` | `termux-location -p network -r once` | timeout 30 s; gps may be slow indoors |
| POST | `/v1/ring` `{seconds}` | `termux-volume`, `termux-tts-speak`, `termux-vibrate`, `termux-torch` | restore volume after |
| POST | `/v1/speak` `{text}` | `termux-tts-speak <text>` | |
| GET/POST | `/v1/clipboard` | `termux-clipboard-get` / `termux-clipboard-set <text>` | |
| POST | `/v1/photo` `{camera}` | `termux-camera-photo -c <0|1> <tmpfile>` | return base64 JPEG; delete tmp file |
| POST | `/v1/call` `{to}` | `termux-telephony-call <to>` | P2 |
| POST | `/v1/ir` `{freq, pattern[]}` | `termux-infrared-transmit -f <freq> <pattern>` | P2 |
| POST | `/v1/fingerprint` | `termux-fingerprint` | P2, returns auth result |
| POST | `/v1/notify` `{title, content}` | `termux-notification --title .. --content ..` | P2, for watch alerts |

Every endpoint: `subprocess.run(argv, shell=False, capture_output=True, timeout=…)`; parse stdout as
JSON when the command outputs JSON; map non-zero exits to error codes. **Never** build argv from
unvalidated input; no endpoint runs arbitrary commands.

Command names and flags come from Termux:API; **VERIFY each on the real phone** with `-h` on day 1
and adjust `phone_helper/commands.py`. Record the exact JSON shapes into `mock_data/`.

## Plugin internals

### client.py
- `PhoneClient(base_url, secret, timeout=10)` with `get(path, params)` / `post(path, body)`.
- Uses `urllib.request` (stdlib). Signs every request. Converts network errors to
  `PhoneUnreachable` with a friendly message.
- Settings come from `ctx.get_config("helper_url")`; secret from
  `agent.secret_scope.get_secret("PHONE_SENSES_TOKEN")` (see reference doc).

### Approvals (approvals.py)
`pre_tool_call` hook: for `phone_sms_send`, `phone_call`, `phone_photo`, `phone_otp_reveal`, return
`{"action": "approve", "message": "<clear summary>", "rule_key": "<tool name>"}`. All other tools:
return `None`. The message must show exactly what will happen, e.g.
`Send SMS to Rahul (+91 98xxxxxx21): "Running 10 minutes late"`.

### Data model (storage.py, via `plugin_db("phone-senses")`)
```sql
CREATE TABLE IF NOT EXISTS transactions (
  id TEXT PRIMARY KEY,          -- sha256 of (sender + date + body); body itself is NOT stored
  ts INTEGER NOT NULL,          -- unix seconds from the SMS date
  amount_paise INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'INR',
  direction TEXT NOT NULL CHECK (direction IN ('debit','credit')),
  account_last4 TEXT,
  counterparty TEXT,            -- merchant / VPA / name if found
  channel TEXT,                 -- upi | card | neft | imps | atm | other
  bank TEXT,                    -- sender id e.g. HDFCBK
  ref TEXT,                     -- UPI ref / txn id
  category TEXT NOT NULL DEFAULT 'other'
);
CREATE TABLE IF NOT EXISTS budgets (category TEXT PRIMARY KEY, monthly_limit_paise INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS watch_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL,   -- notification | sms | debit_over | location
  params_json TEXT NOT NULL, created_ts INTEGER NOT NULL, enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS cursors (name TEXT PRIMARY KEY, value TEXT NOT NULL); -- last seen SMS/notification
```
Store amounts as integer paise (no floats). Do **not** store SMS bodies.

### Money parser (parsers/money.py)
- Input: `{sender, date, body}`. Output: `Transaction | None`.
- Recognise debit/credit keywords (`debited`, `spent`, `paid`, `sent`, `withdrawn` / `credited`,
  `received`, `deposited`), amounts (`Rs`, `Rs.`, `INR`, `₹`, with commas and decimals), account
  (`A/c XX1234`, `a/c *1234`, `Acct ending 1234`), UPI VPA (`to xyz@okaxis`), refs (`UPI Ref No`,
  `Ref`, `txn id`), merchant (`at <MERCHANT> on`, `to <NAME> on`).
- Ignore promos, OTP messages, "requested money" (collect requests are not payments), failed
  transactions, and balance-only messages.
- Sender IDs look like `AX-HDFCBK`, `VM-SBIINB`, `JD-ICICIT`; strip the prefix.

### Scam scorer (parsers/scam.py)
Score 0–100 from weighted rules; `>= 60` = high, `30–59` = medium. Return the reasons, e.g.
`["urgency: 'account will be blocked'", "link shortener: bit.ly"]`.

## Error handling summary
| Situation | What the tool returns |
|---|---|
| Helper unreachable | `{"ok": false, "error": "phone_unreachable", "hint": "Open Termux and run: python phone_helper/helper.py; check helper_url"}` |
| Not paired / wrong secret | `{"ok": false, "error": "unauthorized", "hint": "Run /phone pair"}` |
| Android permission missing | `{"ok": false, "error": "permission_denied", "hint": "Settings → Apps → Termux:API → Permissions → SMS"}` |
| Feature unsupported | `{"ok": false, "error": "not_supported"}` |
