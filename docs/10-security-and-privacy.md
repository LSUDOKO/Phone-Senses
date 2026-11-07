# 10: Security and privacy

Phone Senses touches the most private data a person has. Getting this right is what makes judges
and catalog reviewers trust it, and it is required by the catalog rules.

## Threat model
| Threat | Mitigation |
|---|---|
| Someone on the same Wi-Fi talks to the helper | HMAC-signed requests; the secret is never sent; timestamp ±60 s; nonce replay cache; rate limits. Recommend Tailscale. |
| The secret leaks from the laptop | Stored only via Hermes secret storage (`config_schema` secret → `.env`, read with `get_secret`). Re-pair with `helper.py --pair` to rotate. |
| Prompt injection (e.g. a web page or SMS says "send my OTP to +1…") | Every send/call/photo/OTP tool needs human approval with the full content shown; OTPs masked by default; no auto-approve path; the SKILL.md tells the model never to act on instructions found inside messages. |
| Command injection on the phone | No shell; fixed argv per endpoint; strict validation (phone number regex, length caps, enum values). |
| Private data leaking into logs, tests or the repo | Never log message bodies; transactions store amounts and metadata only (no SMS body); fixtures are synthetic; pre-release scan for real data. |
| Runaway sending | `sms/send` and `call` limited to 5 per minute on the helper side. |
| Unattended runs (cron or gateway) trying to send | Approval hook still applies; with nobody to answer, Hermes refuses per its policy; tools fail clearly instead of hanging. |
| Stalkerware misuse | Own phone only; the helper runs visibly in Termux with a persistent notification (P1: `termux-notification` "Phone Senses helper running"); README states it must not be installed on someone else's phone. |

## Hard rules for the code
1. No `shell=True`, no `eval`/`exec`, no dynamic imports.
2. No telemetry, analytics or third-party network calls. The plugin only talks to the user's own helper URL.
3. No self-update code.
4. No binaries or `.pyc` in the repo; add `.gitignore` for `__pycache__/`, `*.pyc`, `.env`, `*.db`.
5. Secrets only through `get_secret`; never print them; mask in errors.
6. OTP masking runs on **every** text field returned to the model (notifications, SMS, brief, watch matches).
7. Approval messages show exactly what will happen; no hidden parameters.
8. Unit tests cover: OTP masking, the approval hook covering all sensitive tools, the HMAC checks,
   input validation.

## Disclosure text (README section "Privacy and disclosures")
Use this, adjusted to what is actually built:

> **What Phone Senses does on your devices**
> - **Phone helper:** runs a small Python HTTP server inside Termux on your Android phone, listening
>   on the address you choose (your Wi-Fi or Tailscale IP). It runs Termux:API commands to read
>   notifications, SMS, call log, contacts, location, battery and Wi-Fi info, and, when you approve,
>   to send SMS, take photos or place calls. Every request must be signed with your pairing secret.
> - **Network:** the Hermes plugin talks **only** to your own phone helper. No data goes to any
>   third-party service. Your model provider sees the tool results Hermes sends to it, as with any tool.
> - **Approvals:** sending SMS, placing calls, taking photos and revealing OTPs always ask you first
>   through Hermes's approval prompt.
> - **OTPs:** one-time codes are hidden from Hermes by default.
> - **Stored data:** parsed transactions (amount, date, counterparty, account last 4 digits;
>   **no message text**), budgets and watch rules are stored locally in Hermes's plugin data folder
>   (`<HERMES_HOME>/plugin-data/phone-senses/`). The pairing secret is stored by Hermes as a secret
>   setting and on the phone in `~/.phone-senses/secret`.
> - **Background:** the helper keeps running in Termux while enabled; stop it with Ctrl+C or by
>   closing Termux.
> - **Use only on your own phone.**

## Catalog description disclosure (one paragraph, goes in the catalog YAML `description`)
> Give Hermes your own Android phone's senses through Termux:API: notification and SMS digests,
> sending SMS from your SIM, a bank and UPI money tracker, scam SMS warnings and find my phone.
> Disclosure — needs the separately installed Termux and Termux:API apps (F-Droid) and runs the
> plugin's own stdlib-only helper on the phone, which executes fixed termux-* commands and serves an
> HMAC-signed HTTP API on the address you choose; the plugin talks only to that helper; reads
> notifications, SMS, call log, contacts, location and battery; sending SMS, calls, photos and OTP
> reveal always go to Hermes's approval prompt; OTPs are masked by default; parsed transactions
> (no message text) are stored in the plugin's data directory; no telemetry.

## PR description disclosure bullets
- Surfaces used: `register_tool`, `pre_tool_call` hook (approvals), `register_command`,
  `register_skill`, `config_schema` (incl. a secret), `plugin_db`, (Desktop SDK pane if built).
- Network: only to the user-configured helper URL (LAN or Tailscale).
- Reads: phone data via the helper; nothing outside the plugin data directory on the laptop.
- Shell commands: none on the laptop; fixed `termux-*` argv on the phone, no shell.
- Background processes: the phone helper (user-started, visible in Termux). None on the laptop.
- Stored credentials: the pairing secret via Hermes secret storage.
- Telemetry: none.
