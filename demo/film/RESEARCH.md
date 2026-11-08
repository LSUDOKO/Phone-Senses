# Research for the Phone Senses launch film

Checked on 2026-11-08. Every number below was read on its primary source, or on the paper
itself. If a number is not in this file, it does not go on screen.

## Use on screen (problem section, 0:18–0:50)
On-screen source lines use Geist Mono, 14–16 px at 1080p, bottom-left, Mist `#9AA0B4`.

### 1. UPI volume: 25,466.70 million transactions in October 2026
- **Source:** NPCI, "Unified Payments Interface (UPI) Product Statistics", monthly table.
  https://www.npci.org.in/product/upi/product-statistics/
- **Quote (table row):** `October-2026 | 758 | 25,466.70 | 31,52,929.46`
  (columns: banks live on UPI | volume in Mn | value in Cr).
- **On screen:** `25.47 BILLION UPI PAYMENTS · OCT 2026` and source line
  `NPCI, UPI Product Statistics, Oct 2026 · npci.org.in`
- **VO wording:** "over twenty-five billion UPI payments". Rounding down is safe.
- **Do not say** that every UPI payment sends an SMS. That is not a universal fact. The VO says
  *his* bank texts him for every payment. Arpit must confirm that this is true for his bank.

### 2. Scam messages: 13 a day for the average Indian (text, email and social media combined)
- **Source:** McAfee, "2026 State of the Scamiverse" India press release, Feb 5, 2026 (a consumer survey).
  https://www.mcafee.com/en-in/consumer-corporate/newsroom/press-releases/2026/20260204-1.html
- **Quote:** "Indians receive 13 scam messages per day on average across text, email, and social media."
- **Supporting quote, same release, useful for the bills/deliveries story:** "Routine messages like
  delivery notices, subscription renewals, and bank alerts have become commonplace tactics scammers
  use to gain trust."
- **On screen:** `13 SCAM MESSAGES A DAY` with the small line
  `Average in India, across text, email and social · McAfee State of the Scamiverse, Feb 2026`
- **Rule:** never caption this as "13 scam SMS". The number covers all channels.

### 3. Financial cyber fraud: ₹55,050 crore+ reported, 65,89,201+ complaints, 2021–2025
- **Source:** Ministry of Home Affairs written reply, published by PIB on 21 Jul 2026 ("national cyber
  crime data").
  https://www.pib.gov.in/PressReleasePage.aspx?lang=1&PRID=2287039&reg=1
- **Quote:** "As per NCRP & CFCFRMS operated by I4C, from the year 2021 to 2025, the total number of
  financial frauds complaints on NCRP are more than 6589201, the total amount reported is more than
  ₹ 55050 Crores, the total amount marked as Lien is more than ₹ 8189 Crores…"
- **On screen:** `₹55,050 CRORE+ REPORTED IN FRAUD` with the small line
  `Financial cyber-fraud complaints 2021–2025 (65.9 lakh+) · MHA / I4C via PIB, 21 Jul 2026`
- **VO wording:** "Since 2021, Indians have reported more than fifty-five thousand crore rupees in
  cyber fraud." The amount is what was *reported*. Don't call it proven losses.

## Use in the painkiller and impact sections: the paper
**Gu et al., "Beyond the GUI Paradigm: Do Mobile Agents Need the Phone Screen?"**, arXiv
2606.19388v1 (cs.SE), 16 Jun 2026. Mila, Concordia, University of Toronto, McMaster.
https://www.alphaxiv.org/abs/2606.19388 (read from the PDF itself.)

| Claim in our docs | What the paper says | Where | Verdict |
|---|---|---|---|
| CLI agents 60.7–68.9% vs GUI 22.2–33.3% on command-suited tasks | "every CLI agent we evaluated outperforms every GUI baseline (60.7–68.9% vs. 22.2–33.3%)" on the **CLI-Advantage Suite** (45 task templates, 5 categories) | §1, §5.3, Table 3 | ✅ exact |
| ~10.7 vs ~18.6 steps | "CLI agents also use substantially fewer steps per task than GUI methods (10.7 vs. 18.6 mean steps)". This is the mean of the three agents' Avg Steps in Table 3 (CLI 5.7 / 15.4 / 11.0; GUI 12.9 / 23.4 / 19.4). | §1, §5.3, Table 3 | ✅ exact. These are **agent steps**, not taps. |
| GUI agents ≤11% on cross-app workflows | "particularly on cross-app workflows where GUI agents cap at ≤11% regardless of model scale" | §1, §5.3 | ✅ exact |
| Claude Code (Opus 4.7) 71.8% on AndroidWorld | "Claude Code (Opus 4.7) reaches 71.8% and 51.9% [AndroidWorld, MobileWorld], outperforming every reproducible GUI baseline" | Abstract, Table 1 | ✅ exact |

**Framing rules**
- The paper's CLI agents drive Android over **ADB**. Phone Senses uses **Termux:API**. The paper
  supports the *approach* (commands and APIs instead of the screen). It never tested Phone Senses.
  Never imply that it did.
- **Don't say** "one question instead of ~18 taps". 18.6 is the mean number of *agent steps* for
  screen-based agents, and even the command-line agents took 10.7 steps. Approved line:
  `SCREEN AGENTS: 18.6 STEPS · COMMAND-LINE: 10.7` with the source line
  `Mean steps per task, CLI-Advantage Suite · Gu et al., arXiv 2606.19388, 2026`.
- The paper's examples match Phone Senses features: "top-3 expense categories this month",
  "did anyone text me during my meetings yesterday?". You can quote these in a lower third if needed.

## Facts from this repo (use freely; re-check before release)
| Fact | Where it comes from |
|---|---|
| 22 tools today (26 once bills, deliveries, subscriptions and battery watch land) | README tool table; brief from Arpit. Re-count `plugin/plugin.yaml` before release. |
| 129 tests | README, "Development" section |
| Tested on Hermes Agent 0.23.0 and a moto g34 5G (Android 15) | README, "Tested on a real phone"; `demo-capture/README.md` |
| `phone_status` round trip 0.9–2 s on the real phone | Arpit's measurement. This number belongs to **`phone_status` only**. Re-measure on camera (Recording R13). |
| 4 approval-gated actions: SMS send, call, photo, OTP reveal | `plugin/approvals.py`, `NEEDS_APPROVAL` |
| The approval panel reads "⚠️ Dangerous Command · <phone_sms_send> (plugin approval rule) · 1. Allow once · 2. Allow for this session · 3. Add to permanent allowlist · 4. Deny", followed by the exact text | `demo-capture/laptop/28-sms-approved-sent.txt`, `26-sms-denied.txt` (Hermes 0.23 TUI). The recipient number is shown part-masked (`+91X****XXXX`). |
| Deny sends nothing and the model does not retry | README, "Tested on a real phone" |
| Canonical signed string: `METHOD\nPATH_WITH_QUERY\nTIMESTAMP\nNONCE\nSHA256_HEX(BODY)`, HMAC-SHA256 with the pairing secret | `phone_helper/helper.py` docstring and `sign()`; `plugin/client.py` `sign()` |
| Nonce is 16 random bytes (32 hex characters). The timestamp skew limit is 60 s. The helper remembers the last 1,000 nonces. | `plugin/client.py` (`secrets.token_hex(16)`), `phone_helper/helper.py` (`MAX_SKEW_S = 60`, `NONCE_CACHE = 1000`) |
| `phone_status` = `GET /v1/status` → `termux-battery-status` + `termux-wifi-connectioninfo`. The body is empty, so the body hash is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. | `phone_helper/commands.py` (`status`, route table), `plugin/tools.py` |
| The helper log prints method, path and status only, never message bodies or query strings | `phone_helper/helper.py` `log_message` |
| Rate limits: 10 requests/s in general, 5 SMS or calls per minute | README, privacy section; `helper.py` |
| No third-party services, no telemetry | README, "Privacy and disclosures" |
| Scam check on the fixture text S1 returns `high` with the reasons: `urgency: 'will be BLOCKED'`, `kyc / identity update: 'Update KYC'`, `look-alike or risky link: sbi-kyc-update.co` | Run locally on 2026-11-08 against `plugin/parsers/scam.py` |
| Money and bills parsers **ignore texts from personal numbers**. Only sender IDs such as `AX-HDFCBK` count. | `plugin/parsers/money.py` `parse()`, `plugin/parsers/bills.py` `parse()` |
| The deliveries parser accepts a self-sent "Your Amazon order … has been delivered" text, because it finds the merchant in the body | Run locally on 2026-11-08 against `plugin/parsers/deliveries.py` |

## Checked and dropped (don't use)
- **Notifications per day for Indian users.** No primary source found. A 180 Degrees Consulting (SRCC)
  blog post had no usable figure. "200 notifications" in the script is **Arpit's own count**.
  Read it from Settings → Digital Wellbeing → Notifications on the recording day and use that exact
  number.
- **Single-year 2025 fraud losses.** Sources disagree: ₹22,495 cr (Reuters/ThePrint, MHA data) vs
  ₹19,813 cr (I4C "fraud and cheating", cited by McAfee). They count different things. The PIB
  five-year total is the only primary-source figure.
- **RBI Annual Report FY26 bank fraud.** The card/internet/digital-payments case count fell to 293
  (from 13,332 in FY25). That undercuts the message and isn't about scam SMS.
- **McAfee 2023/2024 "12 scam messages a day".** Superseded by the 2026 release.
- **YouGov 2023 "30% of urban Indians receive scam messages daily".** Older than the 2026 numbers. Fine as a
  backup only.
