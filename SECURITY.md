# Security policy

Phone Senses gives an AI agent access to a person's SMS, calls, contacts, location and bank
messages. Security reports are welcome and taken seriously.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x | Yes |
| < 0.1 | No |

Fixes go into the latest 0.1.x release. Please test against `main` before reporting.

## Reporting a vulnerability

**Do not open a public issue, discussion or pull request for a security problem.**

1. Go to the repository's **Security** tab and click **Report a vulnerability**
   (GitHub private vulnerability reporting). This opens a private security advisory that only
   the maintainer can see.
2. If that button is not available, open an issue with the **Private contact request** form,
   pick "Security vulnerability" and put **no details** in it. The maintainer will reply with a
   private channel.

Please include:
- the affected component (`plugin/` or `phone_helper/`) and version or commit,
- steps to reproduce, ideally against the mock helper (`--mock`),
- what an attacker can do and what they need first (same Wi-Fi, a malicious SMS, a web page the
  agent reads, and so on).

**Never include real personal data** in a report: no real phone numbers, message text, OTPs,
account numbers, locations or pairing codes. Use synthetic values such as `+91 9000000xxx`.

What to expect:
- an acknowledgement within 3 days,
- an assessment and a plan within 10 days,
- credit in the advisory and `CHANGELOG.md` when the fix ships, unless you prefer not to be named.

## In scope

- **Helper authentication bypass:** any way to get phone data or make the helper act without a
  valid HMAC signature, including replaying a captured request or forging a timestamp.
- **Approval bypass:** any way to send an SMS, place a call, take a photo or reveal an OTP without
  Hermes's approval prompt, or with a prompt that hides or misstates what will happen.
- **OTP leakage:** a one-time code reaching the model, a log, storage or tool output without an
  approved `phone_otp_reveal`.
- **Command injection on the phone:** any input that changes the `termux-*` command the helper
  runs, adds arguments, or reaches a shell.
- **Data leaving the device:** the plugin or helper sending data anywhere except the user's own
  helper URL, storing SMS bodies, or logging message text.
- **Prompt injection that leads to action:** an SMS, notification or web page that makes the agent
  act on the phone without the user approving that exact action.
- Rate limits that can be bypassed, or secrets printed in errors or logs.

## Out of scope

- The unsigned `GET /v1/ping`. It is intentional and returns only `{"ok": true}`. The signed
  ping is the one that returns helper details.
- Attacks that start with the pairing secret, the user's unlocked phone, or a shell on the
  user's laptop.
- Hermes's own approval behaviour, such as answering **always** in the prompt. Report that to
  [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent).
- Bugs in Termux, Termux:API, Android or the phone vendor's software.
- Scam-check false negatives or false positives. The scam score is a rule-based warning, not a
  guarantee. Please open a normal issue with a synthetic example instead.
- Money parser mistakes on unusual bank SMS formats (open a normal issue).
- Passive sniffing on a shared network. Requests are signed, so they cannot be forged or replayed,
  but the helper speaks plain HTTP, so traffic on a shared Wi-Fi is not encrypted. This is a known
  limitation. Use Tailscale (or bind the helper to its Tailscale IP) to encrypt it.

## Security model

**Phone helper (`phone_helper/`, runs in Termux, standard library only)**
- Every request except the anonymous ping is signed:
  `HMAC-SHA256(secret, METHOD \n PATH \n TIMESTAMP \n NONCE \n SHA256(BODY))`.
  The secret itself is never sent.
- The timestamp must be within **±60 seconds**. Each nonce can be used once (replay cache).
  Signatures are compared in constant time.
- **No shell.** Each endpoint runs one fixed `termux-*` argv with `shell=False` and a timeout.
  Inputs are validated (phone number pattern, length caps, enum values).
- Free text (SMS body, text-to-speech, clipboard) goes in on **stdin**, never as a command argument.
- **Rate limits:** 10 requests per second overall, and at most 5 per minute for SMS sending and
  5 per minute for calls.
- Logs show request paths and status codes only, never message text.
- The pairing secret is stored in `~/.phone-senses/secret` with mode 600. Run `--pair` again to rotate it.

**Hermes plugin (`plugin/`)**
- Talks **only** to the helper URL the user configured. No telemetry, no analytics, no
  third-party calls.
- `phone_sms_send`, `phone_call`, `phone_photo` and `phone_otp_reveal` always go through Hermes's
  approval prompt via the `pre_tool_call` hook. The prompt shows the exact number and text. There is
  no auto-approve option. In unattended runs (cron, `-q`) nobody can approve, so these tools are refused.
- `phone_otp_reveal` is off by default and needs the `allow_otp_reveal` setting as well as approval.
- OTP codes are masked (`[OTP hidden]`) in every text field returned to the model.
- **No SMS bodies are stored.** The money tracker keeps amount, date, counterparty and the last 4
  digits of the account. Transaction IDs are hashes, not message text.
- The pairing secret is stored by Hermes as a secret setting (`PHONE_SENSES_TOKEN`) and read with
  Hermes's secret API, never from `.env` directly.
- The bundled skill tells the model to treat message text as data, never as instructions.

The full threat model is in [`docs/10-security-and-privacy.md`](docs/10-security-and-privacy.md).

**Use Phone Senses only on your own phone.**
