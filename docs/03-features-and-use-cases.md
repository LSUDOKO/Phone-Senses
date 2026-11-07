# 03: Features and use cases

Priorities: **P0 = must have** (demo depends on it), **P1 = should have**, **P2 = stretch**.
Build P0 first, polish it, then P1. Only start P2 if P0 and P1 are solid by Nov 10 evening.

Tool names are what the model sees. Every tool returns compact JSON with `"ok"`.

---

## Level 1: Read the phone

### F1. Phone status (P0): `phone_status`
Battery %, charging, temperature, Wi-Fi network name, helper version, last-seen time.
- Accept: returns within 3 s on a real phone; clear error JSON if the helper is unreachable
  ("phone not reachable: is Termux running and on the same network?").

### F2. Notifications digest (P0): `phone_notifications`
Current notifications: app, title, text, time. Args: `limit` (default 30), `app` filter,
`since_minutes`.
- Removes noise: ongoing/system notifications (e.g. Termux itself, "USB debugging", media
  controls) unless `include_system=true`.
- OTP codes masked (see F12).
- Accept: works with Notification access granted; explains how to grant it if not.

### F3. SMS search (P0): `phone_sms_list`
Args: `limit` (default 20, max 100), `box` (inbox|sent|all), `query` (substring), `from_number`,
`since_days`. Returns sender, date, body (OTP-masked), thread id.
- Accept: `query="Swiggy"` finds the right messages; bodies are OTP-masked.

### F4. Missed calls and call log (P1): `phone_calls`
Args: `limit`, `type` (missed|incoming|outgoing|all). Matches numbers to contact names when the
contacts permission is granted.

### F5. Location (P1): `phone_location`
Args: `provider` (network default, gps for precise). Returns lat, lon, accuracy, time and a
Google Maps link.

### F6. Contacts lookup (P1): `phone_contacts`
Args: `query`. Used by SMS/call tools to turn "Rahul" into a number. Returns up to 10 matches.

---

## Level 2: Act on the phone

### F7. Send SMS (P0): `phone_sms_send`, **approval required**
Args: `to` (number or contact name), `text` (max 480 chars).
- `pre_tool_call` hook asks the user, showing recipient and full text.
- If the contact name matches several numbers, return the options instead of guessing.
- Accept: approval prompt appears; on approve the SMS is sent; on deny nothing is sent.

### F8. Find my phone (P0): `phone_ring`
Args: `seconds` (default 20, max 60). Sets volume high, plays an alarm or speaks "I am here",
vibrates, and blinks the torch. Restores the previous volume afterwards.
- Accept: the phone is clearly findable in a room; volume restored.

### F9. Speak aloud (P1): `phone_speak`
Args: `text` (max 500). Phone reads text aloud (driving/cooking use case).

### F10. Clipboard bridge (P1): `phone_clipboard`
Args: `action` (get|set), `text`. Copy between laptop and phone.

### F11. Take photo (P1): `phone_photo`, **approval required**
Args: `camera` (back|front). Returns the image (resized, max ~1280 px) for vision models.

### F11b. Place a call (P2): `phone_call`, **approval required**

### F11c. TV remote via IR blaster (P2): `phone_ir`
Only on phones with an IR blaster (common on Xiaomi/Redmi). Ship 3 to 5 common TV power codes.

---

## Level 3: Smart features (the real value)

### F12. OTP masking (P0, built into every read tool)
Detect one-time codes (4 to 8 digits near words like OTP, code, verification, passcode, PIN) and
replace them with `[OTP hidden]`.
- `phone_otp_reveal` (P2): returns the latest OTP only when the setting `allow_otp_reveal` is on
  **and** the user approves this call.

### F13. Money tracker (P0)
- `phone_money_sync`: reads recent SMS, parses bank/UPI debit and credit messages, stores
  transactions in the plugin database (deduplicated).
- `phone_money_summary`: args `period` (today|week|month|custom), `group_by`
  (category|counterparty|day), `direction` (debit|credit|both). Returns totals and top items.
- `phone_budget_set` (P1): monthly budget per category; summary shows % used.
- Categories via keyword rules (food, travel, shopping, bills, transfers, other). Optional LLM
  categorisation of "other" via `ctx.llm` is P2.
- Duplicate or unusual debit warnings (same amount and counterparty within 10 min, or > 3x the
  usual size) are P1.
- Accept: parses all P0 fixture formats in `docs/11-testing.md`; "how much did I spend this week"
  gives a correct table.

### F14. UPI sales counter for shops (P1)
`phone_money_summary` with `direction=credit` and `period=today` gives "received today". Mention
this use case in README and demo narration.

### F15. Scam SMS warning (P1): `phone_scam_check`
Scores messages using rules: urgency words (KYC update, account blocked, electricity disconnection
tonight, lottery/prize, refund), link shorteners, look-alike domains, requests to call a number or
install an APK. Also applied automatically in `phone_sms_list` (adds a `"scam_risk"` field).
- Accept: flags the scam fixtures and does not flag the normal bank fixtures.

### F16. Watch rules (P1): `phone_watch_add`, `phone_watch_list`, `phone_watch_remove`, `phone_watch_check`
Rules like "notification from Swiggy containing 'out for delivery'" or "debit over 5000".
`phone_watch_check` evaluates new notifications and SMS since the last check and returns matches.
Run it from a Hermes scheduled (cron) job so results reach the user's chat or Telegram.
Optional (P2): post a phone notification on match via `termux-notification`.
- VERIFY: how Hermes cron jobs deliver results to messaging platforms (Hermes docs, cron section).

### F17. Morning brief (P1): `phone_brief`
One call: battery, missed calls, unread or recent SMS (deduplicated, OTP-masked), important
notifications, yesterday's spending. Users can schedule it daily with Hermes cron.

### F18. Fingerprint approval (P2)
Ask for a fingerprint on the phone (`termux-fingerprint`) as an extra confirmation for sensitive
tools (OTP reveal, SMS to new numbers). Existing plugins already send approvals to phones, so present
this as an extra, not the core.

### F19. Location reminders (P2)
"When I reach college, remind me…". Uses `phone_watch_check` with a location rule (radius). Warn
about battery use.

---

## Interfaces

### F20. `/phone` slash command (P1)
`/phone` shows status; `/phone ring`; `/phone money today`; `/phone pair` shows pairing help.

### F21. Bundled skill (P0)
`skills/phone-senses/SKILL.md` teaches the agent when to use which tool, to prefer summaries, to
never reveal private content unnecessarily, and to ask before acting.

### F22. Desktop phone card (P2, but strong for polish)
A Hermes Desktop pane: battery, location, latest important notifications, spending chart for the
week. VERIFY the Desktop plugin SDK first:
https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk

### F23. Settings (P0) via `config_schema` (rendered in Desktop Settings → Plugins)
`helper_url`, `helper_token` (secret), `allow_otp_reveal` (bool, default false), `money_enabled`
(bool, default true), `scam_check_enabled` (bool, default true), `notifications_exclude_apps` (list).

---

## Use cases (for README and demo narration)
| Person | Use |
|---|---|
| Student | Pocket-money tracker, morning brief before class, location reminder at college |
| Working professional | "What did I miss in the meeting?" (calls + SMS + notifications), text "running late" without touching the phone |
| Small shop owner | "How much did I receive by UPI today?", alert on big payments, scam warnings |
| Developer | Clipboard bridge, send files or links to phone, OTP on approval for logins |
| Traveller | "Where am I?", low-battery reminder, photo of a sign or ticket for Hermes to read |
| Driver / cook | Important messages read aloud |
| Everyone | Find my phone, one digest instead of 200 notifications |
