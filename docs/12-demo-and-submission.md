# 12: Demo video and submission

## Demo video (under 90 seconds; aim for 75)
Rules from the hackathon: under 90 s, **show the plugin working**.

### Setup
- Split view: laptop screen recording (Hermes Desktop or terminal) **plus** the phone filmed on a
  stand, or a phone screen mirror (e.g. scrcpy) placed beside Hermes.
- Use a **demo SIM or a clean phone** if possible, or seed it with harmless messages. Hide real
  notifications (turn on a work profile or clear them first). **Blur anything private.**
- Pre-load data: send yourself 2 to 3 fake bank-style SMS from another phone (fixtures D1, D4, C1)
  and one scam-like SMS (S1). Make sure the money sync has run once.
- Large font in Hermes. Practise 3 times. Record in one take or cut cleanly.

### Script
| Time | On screen | Narration (or captions) |
|---|---|---|
| 0–8 s | Title card: "Phone Senses: give Hermes your phone's senses" | "Your phone knows everything about your day. Your AI agent knows none of it." |
| 8–22 s | Ask: *"Anything important on my phone?"* → digest appears; the OTP shows as `[OTP hidden]` | "Phone Senses reads notifications and SMS through Android's own APIs, with no screen tapping, and hides OTPs by default." |
| 22–40 s | Ask: *"How much did I spend this week?"* → spending table by category; then *"How much did I receive today?"* | "It turns bank and UPI SMS into a money tracker: great for students and for shopkeepers counting UPI sales." |
| 40–55 s | Ask: *"Text Rahul I'm 10 minutes late"* → approval prompt with the full text → approve → phone shows the sent SMS | "Anything that acts on your phone asks you first. The SMS goes from your own SIM." |
| 55–65 s | Show the scam flag on the KYC SMS | "And it warns you about scam texts." |
| 65–80 s | *"Find my phone"* → the phone rings, vibrates and flashes on camera | "Lost your phone? Just ask Hermes." |
| 80–88 s | End card: repo URL, "Install: hermes plugins install phone-senses", @NousResearch | "Phone Senses, open source, in the Hermes Marketplace." |

Note: only show `hermes plugins install phone-senses` once the catalog PR is merged; before that,
show the GitHub URL.

## X (Twitter) post template
```
📱 Phone Senses: give @NousResearch Hermes Agent the senses of your own Android phone.

• Notification + SMS digests (OTPs hidden)
• Money tracker from bank/UPI SMS
• Send SMS from your own SIM, with approval
• Scam SMS warnings
• "Find my phone"

No screen tapping: direct Android APIs via Termux. Open source.
#HermesAgent hackathon entry 👇
<github link>
```
Attach the demo video directly (not a link) so it autoplays.

## Catalog PR

### Steps
1. In your repo: tests, doctor and validate green; README final; screenshots in `assets/`.
2. `git push`, then `git rev-parse HEAD` → copy the 40-character SHA.
3. `git tag v0.1.0 && git push origin v0.1.0`.
4. Fork https://github.com/NousResearch/hermes-agent → in your fork add
   `plugin-catalog/phone-senses.yaml` (template in `05-hermes-plugin-reference.md`).
   - `sha` = the full SHA; `version: "0.1.0"`; `image` and `screenshots` URLs pinned to that SHA.
   - `capabilities.provides_tools` = the exact list from `plugin.yaml`.
5. Open the PR to `NousResearch/hermes-agent:main`.
6. Wait for the catalog CI (it starts when a maintainer triggers it). If it fails, fix, push, update
   the SHA in the PR.

### PR title
`plugin-catalog: add phone-senses (Android phone senses via Termux:API)`

### PR description template
```markdown
## Phone Senses

Gives Hermes the senses of the user's own Android phone through Termux:API: notification and SMS
digests, sending SMS from the user's SIM (with approval), a bank/UPI money tracker, scam SMS warnings
and find my phone. Hackathon entry for the Hermes Agent Plugin Hackathon.

Repo: https://github.com/<you>/phone-senses (pinned at <sha>)
Demo: <X post link>

### Hermes surfaces used
- `ctx.register_tool` (toolset `phone-senses`): <list tools>
- `pre_tool_call` hook: approval prompt for phone_sms_send, phone_call, phone_photo, phone_otp_reveal
- `ctx.register_command("phone")`, `ctx.register_skill`
- `config_schema` settings, including one `secret` (pairing code, read via `get_secret`)
- `plugin_db` for parsed transactions, budgets and watch rules
- <Desktop SDK pane, if built>

### Disclosures
- Network: only to the user-configured phone helper URL (LAN or Tailscale); no third parties; no telemetry.
- The phone helper (in this repo, stdlib Python) runs inside Termux, executes fixed termux-* argv
  (no shell), and serves an HMAC-signed API.
- Reads notifications, SMS, call log, contacts, location and battery on the phone. OTPs masked by default.
- Sending SMS, calls, photos and OTP reveal always go through Hermes's approval prompt.
- Stores parsed transactions (no message text), budgets and watch rules in the plugin data dir.
- Background process: only the user-started phone helper; nothing on the Hermes host.

### Validation
`hermes plugins validate plugin --install-deps` passes at the pinned commit (output attached).

### Screenshots
<2–4 images>
```
Add at the end, if you used Claude Code to write the PR:
`🤖 Generated with [Claude Code](https://claude.com/claude-code)` (optional, your choice).

## Hackathon form
https://form.typeform.com/to/FwJLvOln
Have ready: the PR link, the X post link, your name/handle, and email.

## Final checklist (Nov 11)
- [ ] Repo public; README complete with disclosures; LICENSE
- [ ] `hermes plugins validate` green at the tagged commit
- [ ] Catalog PR open with the correct SHA
- [ ] Demo video < 90 s posted on X, tagging @NousResearch
- [ ] Form submitted (screenshot the confirmation)
- [ ] Join the Nous Discord to answer questions on your entry's thread
