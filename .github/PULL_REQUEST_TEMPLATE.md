## What this changes
<!-- One or two sentences. Link the issue if there is one. -->

## How I tested it
<!-- e.g. pytest, mock helper + scripts/try_tool.py, real phone (model / Android version), Hermes version -->

## Checklist
- [ ] `python -m pytest -q` passes
- [ ] No real personal data anywhere: tests, fixtures, docs, screenshots, GIFs and commit messages use synthetic names and `+91 9000000xxx` numbers
- [ ] Approvals are not bypassed: anything that sends, calls, takes a photo or reveals an OTP is in `NEEDS_APPROVAL` and goes through the `pre_tool_call` hook; no auto-approve path
- [ ] Tool handlers never raise; they return a JSON string with `"ok": true|false`
- [ ] Phone helper changes use a fixed argv with `shell=False`, validated input, a timeout, and stdin for free text
- [ ] No new runtime dependencies (or explained here, with a version floor and upper bound)
- [ ] `plugin/plugin.yaml` `provides_tools` / `provides_hooks` and `docs/catalog-entry.yaml` are in sync
- [ ] Docs updated where needed (README, `plugin/skills/phone-senses/SKILL.md`, `CHANGELOG.md`)
- [ ] `hermes plugins validate plugin --install-deps` passes (if Hermes is installed)
