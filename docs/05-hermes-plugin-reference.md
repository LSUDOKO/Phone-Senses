# 05: Hermes plugin reference (what this project needs)

Collected from the official Hermes docs and an existing catalog plugin (phone-harness) on Nov 7, 2026.
Items marked **VERIFY** were not fully confirmed; check the linked page before relying on them.

Main docs:
- Build a plugin: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- Catalog submission + rules: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission
- Hooks: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- Plugin LLM access: https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access
- Desktop SDK: https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk
- Real example: https://github.com/phone-harness/phone-harness/tree/main/integrations/hermes

## Plugin layout and discovery
- User plugins live in `~/.hermes/plugins/<plugin-name>/` with `plugin.yaml` + `__init__.py`.
- Plugins are opt-in: `hermes plugins enable <name>`.
- Debug discovery: `HERMES_PLUGINS_DEBUG=1 hermes plugins list`; logs in `~/.hermes/logs/agent.log`.
- Test in isolation: `hermes plugins doctor <path> --ci`.
- Same check as catalog CI: `hermes plugins validate <path> --install-deps`.

## plugin.yaml (manifest) for this project
Based on the docs and phone-harness's manifest:
```yaml
name: phone-senses
version: 0.1.0
manifest_version: 2
description: Give Hermes your Android phone's senses through Termux:API (notifications, SMS, money tracking, find my phone) with approvals for every send
author: <Your Name>
license: MIT
homepage: https://github.com/<you>/phone-senses
tags: [phone, android, termux, sms, notifications, finance]
requires_hermes: ">=X.Y.Z"      # SemVer floor = the Hermes version you test on (hermes --version). Never newer than the current release.
provides_tools:                 # MUST list every tool register() registers (validate fails otherwise)
  - phone_status
  - phone_notifications
  - phone_sms_list
  - phone_sms_send
  - phone_ring
  - phone_money_sync
  - phone_money_summary
  # ...add each new tool here as you add it
provides_hooks:
  - pre_tool_call
config_schema:
  helper_url: {type: str, default: "http://127.0.0.1:8765", label: "Phone helper URL", description: "Address shown by the helper on your phone, e.g. http://100.101.102.103:8765"}
  helper_token: {type: secret, env: PHONE_SENSES_TOKEN, label: "Pairing code", description: "Shown once by the helper when you run it with --pair"}
  allow_otp_reveal: {type: bool, default: false, label: "Allow OTP reveal", description: "Let Hermes read one OTP at a time, after you approve each request"}
  money_enabled: {type: bool, default: true, label: "Money tracker"}
  scam_check_enabled: {type: bool, default: true, label: "Scam SMS warnings"}
  notifications_exclude_apps: {type: list, default: [], label: "Apps to ignore in notification digests"}
```
- `config_schema` keys render as a settings form in Desktop **Settings → Plugins**. `secret` values
  are stored in `.env` under the `env` name, never in `config.yaml`.
- Unknown manifest fields are ignored, so older Hermes versions still load it.

## register(ctx): APIs we use
```python
def register(ctx):
    ctx.register_tool(name="phone_status", toolset="phone-senses",
                      schema=schemas.PHONE_STATUS, handler=tools.phone_status,
                      check_fn=None)          # check_fn returning False hides the tool
    ctx.register_hook("pre_tool_call", approvals.on_pre_tool_call)
    ctx.register_command("phone", lambda raw: commands.handle(ctx, raw),
                         description="Phone Senses: status, ring, money, pair")
    ctx.register_skill("phone-senses", skill_md_path)   # VERIFY signature; phone-harness wraps it in try/except TypeError
```
Other documented helpers:
- `ctx.get_config("key", default=...)` / `ctx.set_config("key", value)`: this plugin's settings
  (`plugins.entries.<id>.settings`).
- `ctx.state.get(...)` / `ctx.state.set(...)`: small profile-scoped plugin state (≤10 MiB).
- `ctx.dispatch_tool(name, args)`: call another tool through the normal approval pipeline.
- `ctx.llm.complete(messages=..., purpose=...)`: host-owned LLM call (optional, P2 categorisation).
- `ctx.has_capability("...")`: probe declared and consented capabilities.

### Tool handler rules (from the docs)
1. Signature `def handler(args: dict, **kwargs) -> str`.
2. **Always return a JSON string**, for success and errors.
3. **Never raise**; catch everything and return error JSON.
4. Accept `**kwargs`; Hermes passes context such as `task_id`, `session_id`, `conversation_id`.
5. Key per-conversation state on `conversation_id`, not `session_id`.

### Durable storage
```python
from plugins.plugin_storage import plugin_data_dir, plugin_db
conn = plugin_db("phone-senses")          # SQLite at <HERMES_HOME>/plugin-data/phone-senses/data.db (WAL)
conn.execute("CREATE TABLE IF NOT EXISTS ...")
```
Never write state into the plugin directory (updates replace it).

### Secrets
```python
from agent.secret_scope import get_secret
secret = get_secret("PHONE_SENSES_TOKEN")    # honours the active profile
```
Never use `os.environ` directly for it, and never read `.env` files yourself (catalog rule 11).

### Thread-safe singletons (for the HTTP client)
```python
from plugins.plugin_utils import lazy_singleton
@lazy_singleton
def get_client(): ...
```

## Approvals: the pattern that works (from phone-harness)
```python
def on_pre_tool_call(tool_name: str = "", args: dict | None = None, task_id: str = "", **kwargs):
    if tool_name not in NEEDS_APPROVAL:
        return None
    return {"action": "approve", "message": summary(tool_name, args or {}), "rule_key": tool_name}
```
Returning this dict makes Hermes show its approval prompt. The user can approve once, for the
session, or always (per `rule_key`). Unattended runs (cron, gateway with nobody answering) follow
Hermes's approval policy and must not hang. VERIFY: how a denied approval is reported back to the
model, so the tool result explains it clearly.

## Hooks we may use (names and payloads from the hooks reference)
- `pre_tool_call`: `tool_name`, `args`, `task_id`, … (approvals)
- `pre_llm_call`: `session_id`, `user_message`, `conversation_history`, `is_first_turn`, `model`,
  `platform`; returning a string or `{"context": "..."}` appends text to the current user message
  (P2: e.g. "phone battery is 8%")
- `post_llm_call`: `session_id`, `user_message`, `assistant_response`, … (return value ignored)
- `on_session_start`, `on_session_end`
Every hook callback must accept `**kwargs`.

## Catalog admission rules (summary of the 18 rules)
1. Entries only via a PR to `NousResearch/hermes-agent`, merged by a maintainer.
2. Pin an exact 40-character commit SHA.
3. **No self-updating code.**
4. SHA bumps are new PRs.
5. Submit as the repo owner or major contributor.
6. **Declared capabilities must match** what the plugin registers.
7. The install security scan runs: `dangerous` fails; `caution` is shown to reviewers.
8. Desktop plugins use only the SDK (no prototype patching, no `eval`, no reaching into app markup).
9. **No runtime overrides of Hermes core** (no monkey-patching, no `setattr` on core modules).
10. Dependencies: oldest compatible floor plus an upper bound.
11. **Credentials only through Hermes** (`get_secret`, `config_schema` secrets); never read
    `.env`, `auth.json` or other tools' credential stores.
12. **Respect approvals**; never auto-approve; anything waiting for a person must fail or time out
    cleanly under cron or gateway runs.
13. **Disclose risky behaviour** in README and PR: network calls, reads outside plugin data, shell
    commands, background processes, stored credentials. Telemetry is opt-in only (we have none).
14. `requires_hermes` is a truthful SemVer floor, declared in both `plugin.yaml` and the catalog
    entry; `version` matches the pinned code.
15. No skins or forks of bundled plugins.
16. One listing per plugin lineage.
17. **No unscannable binaries** (no ELF/Mach-O/PE/wasm, no `.pyc`, no opaque archives).
18. Password-manager backends are vendor-only (not relevant to us).

Full text: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission

## Catalog entry file (for the PR): `plugin-catalog/phone-senses.yaml`
```yaml
name: phone-senses
repo: https://github.com/<you>/phone-senses
sha: <40-hex commit sha of your release commit>
subdir: ""
title: Phone Senses
description: "<one line>. Disclosure — <see 10-security-and-privacy.md>"
maintainer: <YourGitHubName>
tier: community
category: tools
requires_hermes: ">=X.Y.Z"
docs_url: https://github.com/<you>/phone-senses#readme
version: "0.1.0"
image: https://raw.githubusercontent.com/<you>/phone-senses/<sha>/assets/banner.png   # 2:1, e.g. 1200x600
screenshots: []                                                                         # up to 6, raw.githubusercontent.com, pinned to the sha
platforms: []
capabilities:
  provides_tools: [phone_status, phone_notifications, ...]   # same list as plugin.yaml
  provides_hooks: [pre_tool_call]
  provides_middleware: []
  requires_env: []
```
Allowed categories: desktop, memory, platform, web, tools, voice, automation, models, general.
