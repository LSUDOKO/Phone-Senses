# CLAUDE.md: Phone Senses (Hermes Agent plugin)

You are helping build **Phone Senses**, a Hermes Agent plugin for the Hermes Agent Plugin Hackathon.
Hard deadline: **Nov 11, 2026, 5 PM EST (Nov 12, 3:30 AM IST)**. Target: submitted by Nov 11, 8 PM IST.

## Read these first
Before writing code in a new session, read the doc(s) relevant to the task:
- `docs/02-idea-and-problem.md`: what we are building and why
- `docs/03-features-and-use-cases.md`: features, priorities, acceptance criteria
- `docs/04-architecture.md`: repo layout, phone-helper API, data model (**source of truth for design**)
- `docs/05-hermes-plugin-reference.md`: Hermes plugin APIs and catalog rules (**must follow**)
- `docs/10-security-and-privacy.md`: safety requirements (**non-negotiable**)
- `docs/11-testing.md`: how to test, fixtures, mock phone

## What the project is
Two parts in one repo:
1. **Phone helper** (`phone_helper/`): a small Python 3 HTTP server that runs **on the Android phone
   inside Termux**. It wraps `termux-*` commands (Termux:API) behind an HMAC-signed JSON API.
   Standard library only. Has a `--mock` mode that serves fixtures, so it also runs on a laptop.
2. **Hermes plugin** (repo root): `plugin.yaml` + `__init__.py` with `register(ctx)`. Registers
   tools that call the helper, a `pre_tool_call` hook for approvals, a `/phone` slash command, a
   bundled skill, and (stretch) a Desktop pane.

## Non-negotiable rules
1. **Follow the Hermes catalog admission rules** in `docs/05-hermes-plugin-reference.md`. In short:
   public plugin surfaces only (no monkey-patching Hermes), declared capabilities must match what
   `register()` registers, no self-updating code, no compiled binaries or `.pyc`, secrets only via
   `agent.secret_scope.get_secret()`, never read `.env` / `auth.json` directly, respect approvals,
   fail cleanly when unattended, disclose risky behavior.
2. **Approvals:** `phone_sms_send`, `phone_call`, `phone_otp_reveal` and `phone_photo` must go
   through Hermes's approval prompt via the `pre_tool_call` hook (see reference doc for the exact
   return value). Never add any auto-approve path.
3. **Privacy:** OTP codes are masked in every tool output by default. Never log message bodies.
   Never write real personal data into tests, fixtures, docs or commits.
4. **No new runtime dependencies** unless truly needed. Prefer the standard library (`urllib`,
   `http.server`, `hmac`, `hashlib`, `json`, `sqlite3`, `re`). If a dependency is unavoidable,
   give it a floor **and** an upper bound and explain why in the commit.
5. **Tool handlers never raise.** Signature `def handler(args: dict, **kwargs) -> str`; always
   return a JSON string, including errors (`{"ok": false, "error": "..."}`).
6. **Phone helper never uses a shell.** `subprocess.run([...], shell=False)` with a fixed argv per
   endpoint, validated inputs, timeouts.
7. **Everything must work against the mock helper** before touching the real phone.
8. **If a Hermes API detail is marked `VERIFY`** in the docs, check the official docs URL given
   there (WebFetch) or an open-source plugin that uses it before relying on it. If you cannot
   verify, implement defensively (try/except, feature probe) and tell the user.

## Commands
```bash
# Unit tests (fast, no phone needed)
python -m pytest -q

# Run the mock phone helper on the laptop
python phone_helper/helper.py --mock --host 127.0.0.1 --port 8765

# Hermes checks (run from repo root)
hermes plugins doctor . --ci
hermes plugins validate . --install-deps
HERMES_PLUGINS_DEBUG=1 hermes plugins list
```

## Coding conventions
- Python 3.11+, type hints, small modules, docstrings on public functions.
- Plugin code uses relative imports inside the package (`from . import client`).
- Tool names are prefixed `phone_`; toolset is `phone-senses`.
- Keep every tool's JSON result compact; truncate long lists; include `"ok": true|false`.
- Write tests alongside each module (`tests/test_<module>.py`).
- After each phase: run tests, run `hermes plugins doctor . --ci` if Hermes is installed, then
  summarise what changed and what the user should check manually.

## Definition of done (for the hackathon)
- Must-have features in `docs/03-features-and-use-cases.md` work end to end on a real phone.
- `pytest` green, `hermes plugins doctor . --ci` green, `hermes plugins validate . --install-deps`
  green with warnings reviewed.
- README has install steps, phone setup, a feature list, screenshots and the disclosure section.
- `plugin.yaml` capabilities, `provides_tools` and `requires_hermes` are accurate.
