# 09: Claude Code prompts (copy and paste, one per phase)

How to use:
- Run `claude` in the project root. `CLAUDE.md` loads automatically.
- Paste one prompt, let it finish, check the checkpoint in `08-build-plan.md`, then commit.
- Start a fresh session (`/clear`) before the next phase.
- If Claude asks a question, answer it; if it wants to skip tests, say no.

---

## Prompt 0: Orientation
```
Read CLAUDE.md and every file in docs/ carefully. Then:
1. Summarise the project in 5 lines so I know you understood it.
2. Check my environment: python version, whether `hermes` is installed and its version
   (`hermes --version`), `hermes plugins --help`, git status. Tell me what's missing.
3. List the exact files you will create, phase by phase, matching docs/04-architecture.md.
4. List every item marked VERIFY in the docs and how you'll verify each (fetch the Hermes docs
   URL given next to it).
Do not write code yet. Wait for my OK.
```

## Prompt 1: Phone helper
```
Build Phase 1 from docs/08-build-plan.md: the phone helper in phone_helper/.
Follow docs/04-architecture.md exactly for the HTTP API, HMAC signing, error codes, rate limits and
validation, and docs/10-security-and-privacy.md for the safety rules.
Requirements:
- Python standard library only (it runs in Termux on Android).
- ThreadingHTTPServer; endpoints from the table (P0 and P1 now; P2 endpoints stubbed to return
  not_supported).
- --pair generates and stores the secret (~/.phone-senses/secret, chmod 600) and prints it once.
- --mock serves synthetic data from phone_helper/mock_data/ (create realistic, clearly fake data:
  fake names, +91 9000000xxx numbers, example bank SMS from docs/11-testing.md).
- subprocess with fixed argv, shell=False, timeouts; never pass unvalidated input.
- Also write a tiny tests/sign_util or reuse client code so tests can make signed requests.
- Tests in tests/test_helper.py: good signature passes, bad signature, skew > 60 s, nonce replay,
  invalid phone number, text too long, mock endpoints return the expected shape.
Run the tests until green. Then show me the exact commands to run the helper in mock mode on my
laptop and for real in Termux, and a curl or Python one-liner to test /v1/ping.
```

## Prompt 1b: Match real phone output (after you test on the phone)
```
I ran these Termux commands on my real phone. Here is the output with private values replaced:
<paste outputs of termux-battery-status, termux-notification-list (1 item), termux-sms-list -l 1,
termux-call-log -l 1, termux-location, and termux-sms-list -h>
Update phone_helper/commands.py flags and phone_helper/mock_data/ so the mock matches these exact
shapes. Keep all data fake. Re-run the tests.
```

## Prompt 2: Plugin skeleton + status + ring
```
Build Phase 2 from docs/08-build-plan.md.
Read docs/05-hermes-plugin-reference.md first. Before using any API marked VERIFY, fetch the
official Hermes docs page given there and confirm the exact names and signatures; tell me what you found.
Create plugin.yaml, __init__.py (register), schemas.py, tools.py, client.py, approvals.py and
skills/phone-senses/SKILL.md (stub). Implement phone_status and phone_ring.
- client.py: stdlib urllib, HMAC signing identical to the helper, timeouts, friendly errors.
- Settings via ctx.get_config("helper_url"); secret via agent.secret_scope.get_secret("PHONE_SENSES_TOKEN"),
  with a safe fallback for unit tests (inject the client).
- Handlers never raise and always return JSON strings.
- plugin.yaml provides_tools must list exactly the registered tools.
Tests: tests/test_client.py and tests/test_tools.py using a mock helper started in a background
thread. Run pytest. If hermes is installed, run `hermes plugins doctor . --ci` and fix every issue.
Finally tell me how to enable the plugin in Hermes and what to ask Hermes to test it.
```

## Prompt 3: Notifications, SMS, contacts, calls, OTP masking, approvals
```
Build Phase 3 from docs/08-build-plan.md, following docs/03 (F2, F3, F4, F6, F7, F12) and docs/10.
- parsers/otp.py: detect and mask OTPs; thorough tests including tricky cases (amounts and dates
  must NOT be masked; "Your OTP is 482913" must be).
- Tools: phone_notifications, phone_sms_list, phone_contacts, phone_calls, phone_sms_send.
- phone_sms_send resolves contact names; if several numbers match, return the choices instead of
  sending. Max 480 chars.
- approvals.py: pre_tool_call returns {"action": "approve", "message": ..., "rule_key": tool_name}
  for phone_sms_send (and later phone_call, phone_photo, phone_otp_reveal). The message shows the
  recipient name, masked-middle number and full text.
- Notification noise filter and the notifications_exclude_apps setting.
- Update plugin.yaml provides_tools and the SKILL.md.
Run pytest and doctor. Then give me a manual test checklist for the real phone.
```

## Prompt 4: Money tracker
```
Build Phase 4 from docs/08-build-plan.md: the money tracker (docs/03 F13, F14; docs/04 data model).
- parsers/money.py parsing Indian bank, card and UPI SMS. Use every fixture in docs/11-testing.md
  and add more of your own synthetic variants (different banks, amount formats like Rs.1,250.50,
  INR 500, ₹99). Ignore promos, OTPs, failed transactions, collect requests and balance-only SMS.
- storage.py with plugin_db tables from docs/04 (amounts in paise; never store SMS bodies;
  dedupe by id).
- Tools: phone_money_sync (args: days, default 30), phone_money_summary (period, group_by,
  direction), phone_budget_set. Keyword-based categories.
- Output a compact table-like JSON the model can present nicely.
Tests first for the parser, then storage and tools. Run pytest and doctor.
```

## Prompt 5: Scam check, watch rules, brief, /phone, skill
```
Build Phase 5 from docs/08-build-plan.md (docs/03 F15, F16, F17, F20, F21).
- parsers/scam.py with weighted rules and reasons; scam_risk field added to phone_sms_list;
  phone_scam_check tool.
- watch.py + phone_watch_add/list/remove/check with cursors so each item matches only once.
- phone_brief combining status, missed calls, recent SMS (OTP-masked), important notifications and
  yesterday's spending.
- /phone command: status | ring | money today|week | brief | pair (pairing instructions).
- Complete skills/phone-senses/SKILL.md: when to use each tool, privacy etiquette, ask before
  sending, summarise rather than dump.
Check the Hermes docs for how a cron job can call phone_watch_check and deliver results to
Telegram; document it in the README (do not build a background daemon unless I approve).
Run pytest and doctor.
```

## Prompt 6 (stretch): Desktop phone card
```
Read https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk fully first.
If a Desktop pane can show data from our plugin within the SDK rules (catalog rule 8: SDK only,
no eval, no reaching into app markup), build a small "Phone" pane: battery, last 5 important
notifications (OTP-masked), and this week's spending by category. Otherwise tell me it isn't
feasible and stop. Keep it simple and robust; run doctor/validate afterwards.
```

## Prompt 7: Polish, README, compliance
```
Build Phase 7 from docs/08-build-plan.md.
1. Write README.md for users (replacing the kit README): what it is, a demo GIF/screenshot
   placeholder, features, requirements, phone setup (from docs/06), laptop setup, settings, example
   prompts, privacy and disclosures (from docs/10), limitations, research (docs/02), license.
2. Make sure plugin.yaml lists every registered tool and hook; requires_hermes is set to my Hermes
   version floor; version 0.1.0.
3. Run `hermes plugins validate . --install-deps`. Fix all failures; show me every warning with your
   opinion on each.
4. Search the repo for anything that looks like real personal data, secrets or tokens.
5. Create assets/ placeholders and tell me which screenshots to take (using the mock helper).
6. Add an MIT LICENSE with my name.
```

## Prompt 8: Release and catalog PR
```
Help me release and submit (docs/08 Phase 8, docs/12).
1. Confirm tests, doctor and validate are green. Commit and push. Print the full 40-char SHA.
2. Tag v0.1.0 and push the tag.
3. Draft plugin-catalog/phone-senses.yaml using the template in docs/05 with the real SHA, the image
   URL pinned to that SHA, and the exact provides_tools list.
4. Draft the PR title and description from docs/12 (disclosures, surfaces used, screenshots).
5. Walk me through forking NousResearch/hermes-agent and opening the PR (use gh if it's installed and
   logged in; otherwise give me the exact web steps).
Do not open the PR without showing me the final text first.
```

## Handy one-liners during development
- "Run the full test suite and doctor, then fix anything failing."
- "Explain what changed since the last commit in plain words."
- "Review the code for any way an SMS could be sent without approval."
- "Review the code for anything that could leak an OTP or message body into logs."
- "Make the error messages friendlier for a non-technical user."
