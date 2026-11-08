# Changelog

All notable changes to Phone Senses are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### In progress
- **Bills due:** spot upcoming bill and EMI due dates in SMS and include them in the brief.
- **Deliveries:** track "out for delivery" and "delivered" messages for orders.
- **Subscriptions:** find recurring charges (streaming, cloud, autopay) in the money tracker.
- **Battery watch:** a watch rule that alerts when the phone battery drops below a level.

## [0.1.0] - 2026-11-08

First release.

### Added
- **Phone helper** (`phone_helper/helper.py`): a standard-library HTTP server for Termux that
  wraps fixed `termux-*` commands behind an HMAC-SHA256 signed JSON API. It has a pairing command
  (`--pair`), rate limits, and a `--mock` mode with synthetic data for laptops and demos.
- **Hermes plugin** (`plugin/`) with 22 tools:
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
- `scripts/try_tool.py` to call tools without Hermes; 129 unit tests that need no phone.

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

[Unreleased]: https://github.com/LSUDOKO/Phone-Senses/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/LSUDOKO/Phone-Senses/releases/tag/v0.1.0
