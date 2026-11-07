# 08: Build plan (Nov 8 to Nov 11)

Deadline: Nov 12, 3:30 AM IST. Target: everything submitted by **Nov 11, 8 PM IST**.
Each phase has a matching prompt in `09-claude-code-prompts.md`.

| Day | Phases | Goal by end of day |
|---|---|---|
| Nov 7 (tonight) | Setup | Tools installed, phone commands tested, repo created |
| Nov 8 | 0, 1, 2 | Helper works (mock + real phone); plugin loads; status and ring work from Hermes |
| Nov 9 | 3, 4 | Notifications, SMS read/send with approval, OTP masking, money tracker |
| Nov 10 | 5, 6, 7 | Scam check, watch rules, brief, `/phone`, skill, (Desktop card), README, validate green |
| Nov 11 | 8 | Release, catalog PR, demo video, X post, form |

---

## Phase 0: Orientation (30 min)
Claude reads all docs, checks the environment (Python, Hermes version, git), and proposes the exact
file list and the order of work.
**Checkpoint:** you agree with the plan; `requires_hermes` value decided.

## Phase 1: Phone helper (3 to 4 h)
- `phone_helper/helper.py`: stdlib `http.server` (ThreadingHTTPServer), HMAC auth, nonce cache,
  rate limit, JSON responses, `--pair`, `--mock`, `--host`, `--port`.
- `phone_helper/commands.py`: endpoint → fixed argv + input validation + timeouts.
- `phone_helper/mock_data/*.json`: synthetic data for every endpoint.
- Tests: signature check, replay rejection, validation, mock responses.

**Checkpoints:**
- `python -m pytest -q` green.
- Mock: `python phone_helper/helper.py --mock --port 8765`, and a signed request from a small test
  script returns battery JSON.
- Real phone: run in Termux; laptop reaches `/v1/ping` and `/v1/status`.

## Phase 2: Plugin skeleton + first tools (3 h)
- `plugin.yaml`, `__init__.py`, `schemas.py`, `tools.py`, `client.py`, `approvals.py` (empty list for now).
- Tools: `phone_status`, `phone_ring`.
- Settings via `config_schema`; secret via `get_secret`.
- Friendly errors (unreachable, unauthorized).
- Bundled skill stub.

**Checkpoints:**
- `hermes plugins doctor . --ci` green.
- In Hermes: "what's my phone battery?" works against the mock, then the real phone.
- "Find my phone" makes the real phone ring, vibrate and flash.

## Phase 3: Read + send (4 h)
- `parsers/otp.py` + tests.
- Tools: `phone_notifications`, `phone_sms_list`, `phone_contacts`, `phone_sms_send` (approval),
  `phone_calls`.
- `approvals.py`: approval for `phone_sms_send` with a clear summary.

**Checkpoints:**
- OTPs masked in all outputs (tests and a manual check).
- "Text <you> 'test from Hermes'" shows the approval prompt; approve sends it, deny sends nothing.
- "Anything important on my phone?" gives a good digest.

## Phase 4: Money tracker (3 to 4 h)
- `parsers/money.py` + many fixtures (see `11-testing.md`).
- `storage.py` (plugin_db tables), `phone_money_sync`, `phone_money_summary`, `phone_budget_set`.

**Checkpoints:**
- All money fixtures parse correctly; promos, OTPs, failed and collect-request messages are ignored.
- "How much did I spend this week?" gives a correct table on the real phone.
- "How much did I receive today?" works.

## Phase 5: Scam check, watch rules, brief, /phone (3 h)
- `parsers/scam.py` + tests; `scam_risk` field in `phone_sms_list`; `phone_scam_check`.
- `watch.py` + `phone_watch_add/list/remove/check`.
- `phone_brief`.
- `/phone` command.
- Finish `skills/phone-senses/SKILL.md`.

**Checkpoints:** scam fixtures flagged and bank fixtures not flagged; a watch rule fires on a test
notification; `/phone money today` works.

## Phase 6 (stretch): Desktop phone card (2 to 3 h, only if Phase 5 done by Nov 10 afternoon)
Read the Desktop SDK docs first. Pane shows battery, latest important notifications and a weekly
spending chart. If the SDK is unclear, **skip it** and spend the time on README screenshots instead.

## Phase 7: Polish + compliance (3 h)
- README (install, phone setup, features, screenshots, privacy and disclosure, limitations, research).
- `assets/banner.png` (1200x600) and 3 to 6 screenshots (from the mock, so no private data).
- `plugin.yaml`: every tool in `provides_tools`; `requires_hermes` set; version `0.1.0`.
- `hermes plugins validate . --install-deps` green; read every warning.
- Fresh-install test: remove the symlink, install as a user would, follow the README exactly.
- LICENSE (MIT).

**Checkpoint:** a friend could install it from the README alone.

## Phase 8: Release and submit (Nov 11)
1. Final commit, push, and note the full 40-char SHA: `git rev-parse HEAD`.
2. Tag `v0.1.0` and push the tag.
3. Fork `NousResearch/hermes-agent`, add `plugin-catalog/phone-senses.yaml` (template in 05/12),
   open the PR with the description template from `12-demo-and-submission.md`.
4. Record the demo (script in 12), under 90 s.
5. Post on X, tag @NousResearch, include the repo link.
6. Submit the PR link and X link: https://form.typeform.com/to/FwJLvOln
7. Re-check: PR open, video public, form confirmation received.

## If you fall behind
Cut in this order: Desktop card → fingerprint/IR/OTP reveal → watch rules → brief → scam check.
**Never cut:** approvals, OTP masking, money tracker, find my phone, README disclosures, validate green.
