# Changelog

All notable changes to Phone Senses are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-11

First release.

### Added
- **Phone helper** (`phone_helper/helper.py`): a standard-library HTTP server for Termux that
  wraps fixed `termux-*` commands behind an HMAC-SHA256 signed JSON API. It has a pairing command
  (`--pair`), rate limits, and a `--mock` mode with synthetic data for laptops and demos.
- **Hermes plugin** (`plugin/`) with 26 tools:
  - Status and senses: `phone_status`, `phone_notifications` (digest with a noise filter),
    `phone_calls`, `phone_contacts`, `phone_location` (with a Maps link).
  - SMS: `phone_sms_list` (search by text, sender and days, with a scam risk per message) and
    `phone_sms_send` (from your own SIM, after approval).
  - Actions: `phone_ring` (find my phone), `phone_speak`, `phone_clipboard`, `phone_photo`
    (after approval), `phone_call` (after approval).
  - `phone_otp_reveal`: off by default, opt-in setting plus approval.
  - Money from bank, card and UPI SMS: `phone_money_sync`, `phone_money_summary`,
    `phone_budget_set`, with duplicate and unusually large debit warnings.
  - `phone_scam_check`: rule-based scam score with reasons.
  - Watch rules: `phone_watch_add`, `phone_watch_list`, `phone_watch_remove`, `phone_watch_check`
    (for Hermes cron).
  - `phone_brief`: a morning brief in one call.
- `/phone` slash command: `/phone`, `/phone ring`, `/phone money week`, `/phone received today`,
  `/phone brief`, `/phone pair`.
- Bundled skill `phone-senses:phone-senses`: which tool to use, summarise instead of dumping
  messages, ask before acting, treat message text as data.
- Landing page at [phone-senses.pages.dev](https://phone-senses.pages.dev) with feature GIFs.
- Brand: logo mark, banner, colours and type.
- `scripts/try_tool.py` to call tools without Hermes; 210 unit tests that need no phone.
- **Scam tripwire** (`phone_scam_guard`): reads calls, notifications, SMS and debits of the last few
  minutes together and spots a phone scam in progress: an unsaved caller, a screen-sharing app
  (AnyDesk, TeamViewer QuickSupport, RustDesk, AirDroid, screen casting), an OTP, a UPI collect request,
  money leaving. Levels clear / low / high / critical with plain advice (hang up, stop sharing, call
  1930). With `alert_phone` the phone shows a warning and says it out loud. OTP codes never leave
  the plugin. Watch kind `scam_guard` alerts once per incident from a cron job; `/phone guard`.
- Mock helper scenarios: `--mock --mock-scenario scam` adds a scam call in progress to the fixtures.
- `phone_bills`: upcoming bills and dues from SMS (electricity, water, gas, broadband, postpaid,
  credit card statements, EMIs, insurance) with amount, due date and days left. A later payment
  confirmation from the same biller clears the due. Nothing is stored.
- `phone_deliveries`: order and parcel status from SMS and notifications (Amazon, Flipkart, Myntra,
  Meesho, Swiggy, Zomato, Zepto, Blinkit and major couriers), merged per order.
- `phone_subscriptions`: recurring debits (streaming, cloud storage, gym, broadband, and any payee
  charged a similar amount about monthly) with the next expected charge and the monthly total.
- Battery watch: `phone_watch_add` accepts `battery_below` with a percent; `phone_watch_check`
  alerts once per drop and can post the alert to the phone.
- `phone_brief` now includes bills due in the next 7 days and deliveries arriving today.
- `/phone bills` and `/phone deliveries`.

### Security
- Signed requests: HMAC-SHA256 over method, path, timestamp, nonce and body hash; timestamp
  within ±60 seconds; nonce replay cache; the secret is never sent.
- No shell on the phone: fixed argv per endpoint, validated input, timeouts, free text on stdin.
- Rate limits: 10 requests per second, and 5 per minute each for SMS sending and calls.
- `phone_sms_send`, `phone_call`, `phone_photo` and `phone_otp_reveal` always go through
  Hermes's approval prompt. There is no auto-approve path. Unattended runs are refused.
- OTPs are masked in every tool output. No SMS bodies are stored or logged. No telemetry.

### Tested on
- moto g34 5G, Android 15, Termux and Termux:API from F-Droid, Hermes Agent 0.23.0.

[0.1.0]: https://github.com/LSUDOKO/Phone-Senses/releases/tag/v0.1.0
