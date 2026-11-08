# Contributing to Phone Senses

Thanks for helping. Phone Senses handles very private data (SMS, calls, contacts, bank messages),
so the rules below are strict. Most of them are checked by the tests.

Security problems go through [SECURITY.md](SECURITY.md), not public issues.

## Repository layout
- `plugin/`: the Hermes plugin (published to the catalog with `subdir: plugin`).
- `phone_helper/`: the helper that runs on the phone in Termux. Standard library only.
- `tests/`: unit tests and synthetic fixtures. No phone needed.
- `scripts/`: `try_tool.py` (call tools without Hermes), `make_gifs.py`.
- `docs/`: design docs. `docs/04-architecture.md` is the source of truth for the design and
  `docs/10-security-and-privacy.md` for the security rules.

## Dev setup
You need Python **3.11 or newer**. The plugin has no runtime dependencies. The tests need
`pytest`, and `pyyaml` for the manifest checks.

```bash
git clone https://github.com/LSUDOKO/Phone-Senses.git && cd Phone-Senses
python -m venv .venv && . .venv/bin/activate
pip install pytest pyyaml
python -m pytest -q          # about a second, no phone needed
```

### Mock phone
The helper's `--mock` mode serves synthetic data, so you can work without a phone:

```bash
python phone_helper/helper.py --pair --secret-file /tmp/ps-secret     # once: creates a secret
python phone_helper/helper.py --mock --secret-file /tmp/ps-secret &    # mock helper on 127.0.0.1:8765

PHONE_SENSES_SECRET=/tmp/ps-secret python scripts/try_tool.py phone_status
PHONE_SENSES_SECRET=/tmp/ps-secret python scripts/try_tool.py phone_sms_list query=swiggy limit=5
PHONE_SENSES_SECRET=/tmp/ps-secret python scripts/try_tool.py /phone money week
```

`try_tool.py` calls tool handlers directly. It stores data in `./.try_tool.db`, not in Hermes.
Approval prompts only exist inside Hermes, so test approval-gated tools there as well.

Everything must work against the mock helper before you try it on a real phone.

### Hermes checks
If Hermes Agent (0.23.0 or newer) is installed, run these from the repo root before opening a PR:

```bash
hermes plugins validate plugin --install-deps
hermes plugins doctor plugin --ci
```

## Project rules
1. **No new runtime dependencies.** Use the standard library (`urllib`, `http.server`, `hmac`,
   `hashlib`, `json`, `sqlite3`, `re`). If something truly cannot be done without a package,
   explain why in the PR and pin it with a lower and an upper bound.
2. **Tool handlers never raise.** A handler is `def handler(args: dict, **kwargs) -> str` and
   always returns a JSON string, including errors: `{"ok": false, "error": "..."}`.
   Keep results compact and truncate long lists.
3. **No shell on the phone.** The helper runs `subprocess.run([...], shell=False)` with a fixed
   argv per endpoint, validated input and a timeout. Free text goes on stdin, never as an argument.
   No `eval`, `exec` or dynamic imports.
4. **Never commit real personal data.** Tests, fixtures, docs, screenshots, GIFs and commit
   messages use made-up names, `+91 9000000xxx` numbers and `1800-000-000x` helplines.
   Never log message bodies.
5. **Approvals are not optional.** `phone_sms_send`, `phone_call`, `phone_photo` and
   `phone_otp_reveal` go through Hermes's approval prompt via the `pre_tool_call` hook
   (`NEEDS_APPROVAL` in `plugin/approvals.py`). Any new tool that sends, calls, records or reveals
   secrets joins that list. Never add an auto-approve path or setting.
6. **OTPs stay masked** in every text field returned to the model.
7. **Public Hermes surfaces only.** No monkey-patching Hermes, no self-updating code, no compiled
   files or `.pyc`. Read secrets only through `agent.secret_scope.get_secret()`; never read
   `.env` or `auth.json`.
8. The plugin talks **only** to the user's own helper URL. No telemetry or third-party calls.

Code style: Python 3.11+, type hints, small modules, docstrings on public functions, relative
imports inside `plugin/` (`from . import client`).

## Adding a tool
1. **Schema:** add it to `plugin/schemas.py`. The name starts with `phone_`; the description says
   when to use it (at least a sentence).
2. **Handler:** add the function to `plugin/tools.py` and its entry in `HANDLERS`.
3. **Register:** add `"phone_<name>": schemas.PHONE_<NAME>` to `TOOL_SCHEMAS` in
   `plugin/__init__.py`. `register()` loops over it.
4. **Approval:** if the tool acts on the phone or reveals something sensitive, add it to
   `NEEDS_APPROVAL` in `plugin/approvals.py` and cover it in `tests/test_approvals.py`.
5. **Manifest:** add the name to `provides_tools` in `plugin/plugin.yaml`.
6. **Catalog entry:** add the same name, in the same position, to `capabilities.provides_tools`
   in `docs/catalog-entry.yaml`.
7. **Helper:** if it needs a new phone endpoint, add it to `phone_helper/commands.py` with a
   fixed argv, input validation and a mock response (`MockRunner` and `phone_helper/mock_data/`).
8. **Tests:** add tests in `tests/test_tools.py` (the `plugin` fixture wires the plugin to a mock
   helper). `tests/test_manifest.py` already fails if `register()`, `plugin.yaml` and the catalog
   entry disagree.
9. **Skill and docs:** teach the agent when to use it in
   `plugin/skills/phone-senses/SKILL.md`, then update the README tool table and `CHANGELOG.md`.

## Adding a bank SMS format
The money parser is `plugin/parsers/money.py`. Unknown formats are skipped, never guessed.

1. Write a **synthetic** example of the message. Change the amount, account digits, reference
   number, names and phone numbers. Keep the structure (word order, punctuation, sender ID shape).
2. Add a row to `tests/fixtures/sms_money.json` under `debits`, `credits` or `ignored`:
   ```json
   ["D9", "AX-ABCBNK", "Rs.120.00 debited from A/C XX1234 to FAKE STORE on 08-11-26. Ref 512300000001",
    {"amount_paise": 12000, "account_last4": "1234", "counterparty": "FAKE STORE", "ref": "512300000001"}]
   ```
   Rows are `[id, sender, body, expected fields]`; `ignored` rows have no expected fields.
   `tests/test_parsers.py` runs every row, so you do not need a new test function.
3. Run `python -m pytest -q tests/test_parsers.py`, then change the regexes in `money.py` until
   the new row passes and no old one breaks.
4. Scam patterns work the same way with `tests/fixtures/sms_scam.json` and `plugin/parsers/scam.py`.

## Commits and pull requests
- Commit messages are a short, sentence-case summary of what changed, often with a scope prefix:
  `Photo: use public surfaces only`, `Docs: Android 14/15 setup notes`, `Site: compressed social image`.
  Add a body when the reason is not obvious.
- Keep one topic per PR and fill in the PR checklist.
- CI runs the tests on Python 3.11 and 3.13 and checks that `plugin.yaml` and the catalog entry
  match. It must be green before merge.

By contributing you agree that your work is released under the [MIT License](LICENSE) and that
you follow the [Code of Conduct](CODE_OF_CONDUCT.md).
