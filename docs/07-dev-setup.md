# 07: Developer setup (your computer)

Works on macOS, Linux, or Windows (WSL recommended on Windows, since Hermes and Claude Code both
work well there; native Windows also works).

## 1. Basics
- **Python 3.11+**: `python3 --version` (Windows: `py --version`)
- **Git**: `git --version`
- **GitHub account**, logged in with git (HTTPS plus a token, or SSH). Optional: GitHub CLI `gh`.
- **pytest**: `python3 -m pip install --user pytest`

## 2. Hermes Agent
1. Install from https://hermes-agent.nousresearch.com (Install button; terminal, macOS, Windows and Linux options).
2. Run `hermes` once and finish setup (pick a model provider).
3. Note your version: `hermes --version`. Use it for `requires_hermes: ">=<that version>"`.
4. Check the plugin commands exist: `hermes plugins --help` (you'll use `doctor`, `validate`,
   `list`, `enable`).

## 3. Claude Code
Official docs: https://code.claude.com/docs/en/overview

Install:
- macOS / Linux / WSL: `curl -fsSL https://claude.ai/install.sh | bash`
- Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
- Windows CMD: `curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd`
- Or Homebrew: `brew install --cask claude-code`, or WinGet: `winget install Anthropic.ClaudeCode`

Open a **new** terminal and check: `claude --version`.
Most surfaces need a Claude subscription or an Anthropic Console account; Claude Code asks you to log
in on first run.

Claude Code automatically reads `CLAUDE.md` at the start of each session; this kit's `CLAUDE.md`
carries the project rules.

## 4. Project repo
```bash
mkdir phone-senses && cd phone-senses
git init
# copy this kit's CLAUDE.md, README.md (rename to KIT_README.md) and docs/ here
git add . && git commit -m "Project kit: plan and docs"
```
Create a **public** GitHub repo `phone-senses` (empty, no README) and push:
```bash
git branch -M main
git remote add origin https://github.com/<you>/phone-senses.git
git push -u origin main
```
The final plugin README replaces the kit's README; keep the kit's README as `KIT_README.md` or delete
it before release.

## 5. Make Hermes load your working copy
Hermes discovers plugins in `~/.hermes/plugins/<name>/`. During development, link your repo there so
edits are picked up without copying:
```bash
# macOS / Linux / WSL
ln -s "$(pwd)/plugin" ~/.hermes/plugins/phone-senses
hermes plugins enable phone-senses
HERMES_PLUGINS_DEBUG=1 hermes plugins list    # should show phone-senses and its tools
```
If the symlink is not discovered (VERIFY), copy the folder instead, or check `hermes plugins --help`
for a local-path install. Restart Hermes after code changes.

## 6. Daily loop
```bash
python -m pytest -q                                   # unit tests
python phone_helper/helper.py --mock --port 8765 &    # mock phone on the laptop
hermes plugins doctor plugin --ci                          # Hermes checks
hermes                                                # try: "what's my phone battery?"
```

## 7. Optional tools
- **Tailscale** on laptop and phone (see 06).
- A screen recorder for the demo (OBS Studio, or the built-in macOS/Windows recorder) and a phone
  stand to film the phone.
