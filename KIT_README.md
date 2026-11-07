# Phone Senses: Hackathon Project Kit

Everything you need to build **Phone Senses**, a Hermes Agent plugin, with Claude Code for the
Hermes Agent Plugin Hackathon (submissions due **Nov 11, 5 PM EST = Nov 12, 3:30 AM IST**).

Phone Senses connects Hermes to **your own Android phone** through Termux:API. Hermes can read
notifications and SMS, send texts from your own SIM (after you approve), track spending from bank
and UPI SMS, warn about scam texts, find your phone and more.

---

## What is in this kit

| File | What it is for |
|---|---|
| `CLAUDE.md` | Instructions Claude Code reads automatically at the start of every session. **Keep it in the project root.** |
| `docs/01-hackathon.md` | Hackathon rules, prizes, deadline, judging, how to submit |
| `docs/02-idea-and-problem.md` | The problem, the solution, research backing, why it is unique |
| `docs/03-features-and-use-cases.md` | Every feature with priority and acceptance criteria, plus use cases |
| `docs/04-architecture.md` | Components, repo layout, phone-helper HTTP API, data model |
| `docs/05-hermes-plugin-reference.md` | The Hermes plugin APIs this project uses, and the catalog rules |
| `docs/06-phone-setup-termux.md` | Setting up Termux and Termux:API on your Android phone |
| `docs/07-dev-setup.md` | Setting up your computer: Hermes, Python, Git, Claude Code |
| `docs/08-build-plan.md` | Day-by-day plan with phases and checkpoints |
| `docs/09-claude-code-prompts.md` | Ready-to-paste prompts for Claude Code, one per phase |
| `docs/10-security-and-privacy.md` | Threat model, safety rules, disclosure text |
| `docs/11-testing.md` | Test strategy, mock phone, sample SMS fixtures, manual checklist |
| `docs/12-demo-and-submission.md` | 90-second demo script, X post, PR and catalog entry templates |

---

## Step by step: building this with Claude Code

### Step 1: Install the tools (tonight, about 30 minutes)
Follow `docs/07-dev-setup.md`. In short:
1. Install **Python 3.11+**, **Git**, and a **GitHub** account.
2. Install **Hermes Agent** from https://hermes-agent.nousresearch.com and run `hermes` once.
3. Install **Claude Code**:
   - macOS / Linux / WSL: `curl -fsSL https://claude.ai/install.sh | bash`
   - Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
   - Then open a new terminal and run `claude --version`.

### Step 2: Set up your phone (tonight, about 20 minutes)
Follow `docs/06-phone-setup-termux.md`: install F-Droid, Termux, Termux:API, grant permissions,
and test a few `termux-*` commands.

### Step 3: Create the project folder
```bash
mkdir phone-senses && cd phone-senses
git init
```
Copy this kit into that folder so `CLAUDE.md` sits at the root and the docs are in `docs/`.
Rename this file to `KIT_README.md` (the plugin will get its own `README.md` later). Then commit,
create an empty public GitHub repo named `phone-senses`, and connect it:
```bash
git add . && git commit -m "Project kit: plan and docs"
git branch -M main
git remote add origin https://github.com/<your-username>/phone-senses.git
git push -u origin main
```

### Step 4: Start Claude Code
```bash
claude
```
Log in when asked. Then paste **Prompt 0** from `docs/09-claude-code-prompts.md`. It makes Claude
read every doc and confirm the plan before writing code.

### Step 5: Build phase by phase
Work through the phases in `docs/08-build-plan.md`. For each phase:
1. Paste the matching prompt from `docs/09-claude-code-prompts.md`.
2. Let Claude write the code **and run the tests**.
3. Check the phase's checkpoint yourself (they are listed in the build plan).
4. Commit: ask Claude to "commit this phase with a clear message".
5. Start the next phase in a fresh session (`/clear`) so the context stays focused; `CLAUDE.md`
   and the docs carry everything Claude needs.

### Step 6: Test on your real phone
After phases 2 and 3, run the helper on your phone and try the tools from Hermes (see
`docs/11-testing.md`, manual checklist).

### Step 7: Submit (Nov 11)
Follow `docs/12-demo-and-submission.md`: tag a release, open the catalog PR, record the demo, post
on X, fill in the form. **Aim to submit by 8 PM IST on Nov 11**, well before the 3:30 AM cutoff.

---

## Golden rules
- **The phone helper and plugin must work with the mock phone first.** That way Claude can test
  everything without your phone, and you can rehearse the demo safely.
- **Never commit real SMS, contacts, tokens or screenshots with private data.** Test fixtures are
  synthetic only.
- **Things marked `VERIFY` in the docs** were not confirmed against the live Hermes docs. Claude
  must check them (the docs URL is given next to each) before relying on them.
- **Must-have features first.** A polished small plugin beats a half-working big one.
