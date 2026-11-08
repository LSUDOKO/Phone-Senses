# Phone Senses: recording plan (real footage)

Record these in the order below. Each recording captures the laptop and the phone at the same time,
on one OBS canvas. Shot IDs (`S##`) refer to `SHOTLIST.md`. Questions in `code` must be typed exactly.

**Time needed:** about 70–80 min of raw footage, in a 3–4 hour session plus a 1-hour rehearsal.
R11 (battery) needs the battery to drain to about 20%, so start it early.

---

## 0. Before the day

### 0.1 Check the data the film depends on
The money and bills parsers **ignore texts from personal numbers**. Only real sender IDs such as
`AX-HDFCBK` count (`plugin/parsers/money.py`, `bills.py`). Anything you text to your own number
will **not** show up in money, bills or subscriptions. Those scenes need your real SMS.

| Scene | Needs on the phone | If it's missing |
|---|---|---|
| Money (R03) | Real bank or UPI debit SMS from this week | Ask about "this month" instead. Change the VO to "this month". |
| UPI received (R03) | At least one real UPI credit SMS | If you have two bank accounts, send ₹1 from one to the other the day before. Otherwise cut S26. |
| Bills [NEW] (R04, S24) | A real biller SMS that is due soon: card statement, postpaid, electricity, EMI | Cut S24 and S27. The VO fallback is in `SCRIPT.md`. |
| Subscriptions [NEW] (R05) | Recurring debits in the bank SMS (Spotify, Netflix, Google One, a Jio/Airtel autopay…) | Cut S29. |
| Deliveries [NEW] (R10) | A real Amazon/Flipkart/Swiggy/courier SMS is best. The re-created "delivered" text from R09 also parses (checked against `plugin/parsers/deliveries.py`). | Use only the R09 text. |
| Mom's 3 missed calls (R02) | Three **real** missed calls in the call log, from the contact saved as **Mom** | See 0.3. |

### 0.2 Dry-run everything against the mock helper, then the real phone
```bash
python phone_helper/helper.py --pair --secret-file /tmp/ps-secret
python phone_helper/helper.py --mock --secret-file /tmp/ps-secret &
PHONE_SENSES_SECRET=/tmp/ps-secret python scripts/try_tool.py phone_scam_check \
  text="Dear customer your SBI account will be BLOCKED today. Update KYC immediately: http://sbi-kyc-update.co/in"
PHONE_SENSES_SECRET=/tmp/ps-secret python scripts/try_tool.py phone_brief
PHONE_SENSES_SECRET=/tmp/ps-secret python scripts/try_tool.py /phone money week
```
- **Expected scam result:** `high`, with the reasons `urgency: 'will be BLOCKED'`, `kyc / identity update: 'Update KYC'` and `look-alike or risky link: sbi-kyc-update.co`. The VO and S31 rely on these.
- **Questions:** put every exact question from this plan to Hermes once, with **the model you will record with**. Some models think out loud for a long time; the earlier captures with `meituan/longcat-2.5:free` took 6–60 s per reply. Pick a fast model that calls the right tool on the first try.
- **New features:** for each `[NEW]` feature, confirm it is merged, is in `plugin.yaml`, and answers its question on the real phone. If not, cut its shots.

### 0.3 Ask Mom (the night before)
- Ask her to call you **three times** between about 6:30 and 6:50 a.m. on recording day, and don't pick up. Those become the real missed calls in the brief.
- Tell her she will get one real text from you, "I'll call you after the exam", and then **call her back**.

### 0.4 Count your notifications
- On recording day, read **Settings → Digital Wellbeing & parental controls → Notifications**. Use that exact number wherever the script says "two hundred".
- If you record the brief at another time than 7 a.m., change "Seven a.m." in the VO.

---

## 1. Privacy prep (do all of this before the first take)
**Phone**
- [ ] **Lock screen:** turn off sensitive content on the lock screen. On Android 15 it's under Settings → Notifications, as "Sensitive notifications" or "Show sensitive content"; the wording varies by build. The lock screen then shows app names with "Contents hidden". This is the S01 flood shot. Check it on the lock screen before you rely on it.
- [ ] **Focus mode** (Digital Wellbeing): pause WhatsApp, Instagram, Telegram (unless you use it for the cron alert), Snapchat and any family or friends chat app for the session. This keeps private chats out of the shade **and** out of Hermes's notification digest.
  - Leave Phone, Messages and your bank apps unpaused.
- [ ] **Clear the shade** an hour before R02. Let normal notifications (bank, shopping, news, college) build up again.
- [ ] **Messages:** archive (don't delete) personal threads so the inbox shows only bank, biller and self threads.
  - Mom's thread stays. In post, crop to the newest bubble and **blur every older message**.
- [ ] **Messages → Settings → Automatic previews: off.** The scam text contains a link; don't let the phone fetch it. **Never tap the link.**
- [ ] **Contacts:** Mom is saved as "Mom".
  - The Hermes approval panel already shows the number part-masked (`+91X****XXXX` in Hermes 0.23). Still blur it in post.
- [ ] **Developer options:**
  - Turn on "Show taps" (this is the sync marker).
  - Turn on "Stay awake" while charging.
  - Turn off auto-rotate.
  - Set brightness to max.
- [ ] **Termux:** start the helper before recording. Crop out the start line that shows the IP and port.
  - Never run `--pair` on camera.
  - Never `cat ~/.phone-senses/secret`.

**Laptop**
- [ ] **Desktop:** turn on Do Not Disturb. Close the browser, chat apps and file manager. Use a plain wallpaper.
- [ ] **Terminal:** run `hermes chat` at a 20–22 pt font with a dark theme. Clear the shell history from the screen.
  - Never show `config.yaml`, the secrets settings, `.env` or the pairing code.
- [ ] **Env vars for R13:** set `PHONE_SENSES_URL` and `PHONE_SENSES_SECRET` in the shell *before* recording, then run `clear`. Never type the IP on camera.

**In post, blur:**
- Account digits, balances, UPI reference numbers.
- Friends' names in UPI transfers.
- OTP digits on the phone.
- The Wi-Fi SSID and IP in `phone_status` output.
- Mom's number.
- Older messages in Mom's thread.

---

## 2. Approval-state rules (most likely way to ruin a take)
- **Only ever choose `1. Allow once` or `4. Deny`.** Never `2. Allow for this session` or `3. Add to permanent allowlist`.
  - "Session" silences the panel for the rest of that Hermes session.
  - "Permanent" silences it forever, and R07/R08 would show no panel.
- **Setup sends run in a separate Hermes session.** Do R01 and R09 in their own sessions, then quit (`/exit` or Ctrl+C). Start a fresh `hermes chat` for each recorded take.
- **Before R07, test the panel:** in a throwaway session, ask Hermes to text your own number and check that the panel appears. Then press Deny.
  - If no panel appears, a permanent allowlist entry exists for `phone_sms_send`. Remove it in Hermes's approval settings (VERIFY where Hermes 0.23 stores the permanent allowlist) before recording.
- **Approvals only work in interactive `hermes chat`.** In `-q` mode or cron, gated tools are refused by design.
- **Rate limit:** at most 5 SMS or calls per minute, so leave time between sends.

---

## 3. Capture setup (same for every recording)
1. Connect the phone by USB.
2. Start the phone mirror and a hi-res backup recording:
   ```bash
   scrcpy --max-size 1920 --video-bit-rate 16M --stay-awake --show-touches --record R##-phone.mkv
   ```
   Recent scrcpy versions record the phone's audio too, which you need for the R12 ring.
3. Lay out the laptop screen:
   - Hermes terminal on the left ~64% of the screen.
   - scrcpy window on the right ~36%.
4. In OBS, record the **whole laptop display** at 1920×1080 or larger, 30 fps. Laptop and phone mirror then land in one synced file.
   - Mic: off, except for R12 room tone.
   - R12 only: add the laptop webcam as a source.
5. **Sync marker:** at the start of every take, tap the phone's clock once. The "Show taps" dot appears in both the OBS capture and `R##-phone.mkv`.
6. Check the link before each take with `/phone`, so Hermes confirms the helper is reachable. Use a session you won't record in.
7. **Name files** `R##-take#-obs.mkv` and `R##-take#-phone.mkv`.

---

## 4. Recordings, in shooting order

### R01: the scam text arrives (setup session, phone shots only) → S03, S30
**Setup**
1. Turn off Automatic previews in Messages (see section 1).
2. In a **separate** `hermes chat` session, ask:
   `Send this exact test text to my own number +91XXXXXXXXXX. It's a sample scam message for my demo video and I'm the only recipient: "Dear customer your SBI account will be BLOCKED today. Update KYC immediately: http://sbi-kyc-update.co/in"`
3. Choose **`1. Allow once`**.
4. **If the model refuses**, type the same text yourself in Messages to your own number. It still arrives as a real SMS.

**Record the phone**
1. Start on the home screen and wait for the heads-up notification to drop in (this is S03).
2. Open the thread in Messages and hold for 5 s (this is S30).
3. Label in post: `RE-CREATED · SENT TO MY OWN NUMBER`. Blur the sender, which is your own number.

**Fallbacks**
- **Text never arrives:** the carrier may be filtering texts with a URL, or the phone sent it to Spam. Check **Spam & blocked** first.
- **Use the no-link fallback text:** `Electricity power will be disconnected tonight at 9.30 pm because your previous month bill was not updated. Call officer 9000012345`. It also scores `high`. Its reasons are a disconnection threat and a request to call a personal number.
  - Change the S31 reason boxes to match.
  - Change the VO to "a fake deadline, a number to call".

**Raw:** ~3 min.

### R02: morning brief, OTP hidden, Mom's calls (the aha) → S21–S24 · `90s`
**Setup**
1. Mom's three missed calls are in the call log (from 0.3).
2. ~2 min before the take, trigger a **real OTP SMS** by starting a login on any app or site that texts you a code. Don't use the code.
3. Shade cleared earlier; normal notifications sitting in it.

**Take**
1. Fresh `hermes chat`. Tap the clock (sync).
2. Pull down the notification shade on the phone and hold for 3 s, so the OTP and Mom notifications are visible.
3. Type `Good morning, give me my phone brief.`
4. Wait for the full answer and don't scroll Hermes too fast. Hold on the `[OTP hidden]` line, the missed-calls line and the bills line [NEW].
5. On the phone, open **Phone → Recents** and hold on Mom's three missed calls for 3 s.

**Must see**
- `[OTP hidden]` in Hermes while the OTP is visible on the phone (blur the digits in post).
- `Mom` and `3 missed calls`.
  - `phone_brief` lists each missed call from the last 24 h with its contact name. That needs the Contacts permission for Termux:API; without it you get the number.
  - Hermes writes the summary line itself, so **dry-run with your recording model** and check that it says Mom and three.
  - If it doesn't, add the follow-up `Who called me this morning?` in the same take.
- [NEW] A bill due line.

**Raw:** ~3 min per take × 3 takes = ~10 min.

### R03: money and UPI received → S25, S26 · `90s`
**Take** (fresh session)
1. Type `Where did my money go this week? Sync my bank SMS first.` and wait for the category table.
2. Type `How much did I receive by UPI this week?`

**Phone (B-roll in the same take):** open the bank's SMS thread and scroll slowly for 5 s (S11 uses a 6× ramp of this).

**Blur:** account digits, balances, refs, friends' names.

**Raw:** ~3 min × 2 takes = ~6 min.

### R04: bills due [NEW] → S27 (and the S24 brief line)
**Take:** type `What bills are due soon?`

**Phone:** optionally show the biller's real SMS. Blur the account and amount if you want.

**Raw:** ~2 min × 2 takes. **Skip** if the bills feature isn't merged.

### R05: subscriptions [NEW] → S29
**Take:** type `What subscriptions am I paying for, and what's the monthly total?`

**Raw:** ~2 min × 2 takes. **Skip** if the feature isn't merged or there are no recurring debits.

### R06: scam check with reasons → S31 · `90s`
**Take** (fresh session): type `I got a weird SMS about my KYC. Is it a scam?`

**Must see:** `high` risk and the three reasons (see 0.2).

**Phone:** keep the KYC thread open in the mirror.

**Raw:** ~2 min × 2 takes.

### R07: text Mom, then Allow once → S32–S34 · `90s`
This sends a **real SMS to Mom**. Rehearse first, then do the real take.

**Rehearsal** (fresh session):
1. Do the same flow to your own number: `Text +91XXXXXXXXXX: I'll call you after the exam.`
2. Choose `1. Allow once`.
3. Check the panel layout and the speed.

**Take** (a new fresh session):
1. Tap the clock (sync).
2. Type `Text Mom: I'll call you after the exam.`
3. If Hermes asks which Mom number, pick the right one. That moment is cut in the edit.
4. When the panel appears, **wait 3 full seconds**, then select `1. Allow once` and press Enter. S33 needs the panel at 1×.
5. On the phone, open Messages → Mom and hold on the new sent bubble for 4 s.

**Must see**
- The panel text `Send SMS from your phone to +91X****XXXX (… chars): "I'll call you after the exam."`.
- The line `⚠ Approval: <phone_sms_send> (plugin approval rule) → allowed once`.
- The bubble in Mom's thread.

**Raw:** ~3 min. One real take. A second take sends Mom a second text.

### R08: Deny → S35, S36 · `90s`
**Take** (same session as R07 or a fresh one):
1. Type `Also text Mom that I skipped lunch.`
2. When the panel appears, wait 2 s, move to `4. Deny` and press Enter.
3. Let Hermes reply that it didn't send.
4. On the phone, open Mom's thread and show that no new bubble arrived.

**Must see:** Deny selected, no retry by Hermes, and the thread unchanged.

**Raw:** ~2 min × 2 takes. Safe to repeat, because nothing is sent.

### R09: watch rule catches "delivered" → S37 · `90s`
**How the watch check behaves** (from `plugin/tools.py` `phone_watch_check`):
- Adding a rule does **not** set a starting point.
- The **first check ever** looks at the last hour.
- Every later check looks only at SMS and notifications **newer than the last check**. That cursor is shared by all SMS rules.
- Each item matches **once**.

So run one check *before* the test text arrives. That clears older matches, such as a real "delivered" text from today, so the on-camera check shows exactly one match.

**Choose one alert path** before you start:
- **Path A, Hermes check (simplest):** no cron. Ask on camera.
- **Path B, Telegram:** a Hermes cron job delivers the alert to Telegram. Then do **not** also ask Hermes on camera, because the cron run will already have used up the match.

**Setup**
1. In a setup session, add the rule: `Watch my SMS for the word delivered.` (Record it; it's useful B-roll.)
2. In the same setup session, clear the old matches: `Any watch alerts on my phone?`. Ignore what it finds; this only moves the cursor to now.
3. Path B only: create the job from the README, `hermes cron create "every 15m" "Run phone_watch_check and tell me about any matches. Say nothing if there are none." --deliver telegram`. Telegram must be set up in Hermes first.
4. In a **separate setup session**, ask:
   `Send this exact test text to my own number +91XXXXXXXXXX: "Your Amazon order for Casio fx-991ES Plus has been delivered."`
5. Choose `1. Allow once`. This text parses as `Amazon · delivered · Casio fx-991ES Plus` and scores `low` on the scam check. Both were checked against the parsers.

**Record**
1. The phone mirror shows the "delivered" SMS heads-up arriving. Label it RE-CREATED.
2. Path A: a fresh session, then `Any watch alerts on my phone?`. The match appears.
3. Path B: record the Telegram notification arriving on the phone, then open the bot chat. Hide the chat list.

**Camera insert:** 5 s of the library with the phone face-down on a book. Shoot it on another day if needed, with the phone mirror cut in.

**Raw:** ~6 min, plus up to 15 min waiting for Path B. Re-doing the take needs a new SMS.

### R10: parcels [NEW] → S28
**Take** (after R09): type `Where are my parcels?`

**Must see:** Amazon · delivered (from R09), plus any real orders.

**Raw:** ~2 min × 2 takes. **Skip** if the deliveries feature isn't merged.

### R11: battery below 20% watch [NEW] → S38
**Setup**
1. Early in the day, add the rule: `Tell me when my phone battery drops below 20%.` It should create a `battery_below` rule with `percent: 20`; that kind already exists in `plugin/watch.py`. VERIFY the tool accepts it.
   - **How it fires:** once, on a check where the level is **below** 20% **and not charging**. It stays quiet until the battery climbs above 25% again.
   - If it already fired during a rehearsal, charge above 25% to re-arm it.
2. Unplug the phone, raise the brightness and play a video to drain it.
3. Watch the level. Recording only takes the moment of the alert.

**Record:** when the battery is at 19% **and unplugged**, either ask `Any watch alerts on my phone?` (Path A) or record the Telegram alert (Path B).

**Fallback, if battery watch isn't shipped:**
1. Add `Alert me when any debit is over 100 rupees.` (`debit_over`, which exists today).
2. Make one real UPI payment over ₹100.
3. Wait for the bank SMS, then check.

**Raw:** ~2 min of recording after a 30–90 min drain. **Skip** if the feature isn't merged.

### R12: find my phone under the bed → S39–S41 · `90s`
**Setup**
1. Night, lamp on. Put the phone **face-up, under the edge of the bed**, in the frame.
2. Put the laptop on the floor or a stool with its **webcam pointing under the bed**, and add the webcam to OBS.
3. Check the helper is running and the volume isn't on silent. The ring restores the volume afterwards anyway.

**Camera insert (S39):** a 15 s clip of you searching the bed and patting your pockets. Use the webcam or a second device if you have one. **Skippable:** if you can't shoot it, use S40 alone and extend it 3 s.

**Take**
1. Type `I can't find my phone, make it ring for 15 seconds.`
2. Let it ring, speak "I am here", vibrate and flash the torch for the full 15 s.
3. Reach in and pull it out (S41).

**Audio:** the scrcpy/phone recording plus the webcam mic, for the real ring.

**Raw:** ~2 min × 3 takes = ~6 min.

### R13: under the hood, a timed real request → S42, S46, S47
**Setup**
1. In Termux, the helper is running and its log is visible in the phone mirror. Crop out the start line with the IP.
2. Laptop shell: `PHONE_SENSES_URL` and `PHONE_SENSES_SECRET` already exported, then `clear`.

**Take 1 (Hermes):** fresh session, `What's my phone battery?`. The phone mirror shows the log line `[phone-senses] GET /v1/status 200` arriving.

**Take 2 (timing):** in a second terminal, from the repo root:
```bash
python - <<'EOF'
import os, sys, time
sys.path.insert(0, "scripts")
import try_tool
ps = try_tool.load_plugin()
secret = open(os.path.expanduser(os.environ["PHONE_SENSES_SECRET"])).read().strip()
c = ps.client.PhoneClient(os.environ["PHONE_SENSES_URL"], secret)
for _ in range(5):
    t = time.perf_counter(); data = c.request("GET", "/v1/status"); dt = time.perf_counter() - t
    print(f"round trip {dt:.2f} s · battery {data['battery']['percentage']}%")
EOF
```
- This times **only the signed request**: HMAC signing, Wi-Fi, the helper and `termux-battery-status`.
- It prints only the battery %, so no SSID or IP appears.
- **Tested** against the mock helper on 2026-11-08.
- Don't use `time python scripts/try_tool.py phone_status`: it also counts Python start-up and the plugin import, so it overstates the round trip.
- The on-screen `0.9–2 S` has to match these five runs. If it doesn't, change the headline and the VO line "Back in under two seconds".

**Raw:** ~4 min.

### R14: B-roll (any time, phone only unless noted) → S01, S02, S08, S11, S14, S20
| Clip | Shot | How |
|---|---|---|
| a | S01, S20 | Lock screen with sensitive content hidden, flooded with notifications. Slow scroll for 10 s. Also a clean lock screen at ~7:00. |
| b | S02 | Close-up of the `Mom · 3 missed calls` notification, 5 s. Record right after Mom's calls, before you clear anything. |
| c | S11 | The bank SMS thread scrolling, 10 s. Blur in post. |
| d | S08 | Camera insert: you at your desk with exam notes and the phone face-down, buzzing. 20 s, tripod. |
| e | S14 | Laptop with Hermes idle, phone beside it. 10 s, camera or OBS. |
| f | S37 | Library: phone face-down on a book. 5 s. |

**Raw:** ~15 min.

---

## 5. Summary
| # | What | Shots | Real-time must-haves | Raw (approx.) | Tag |
|---|---|---|---|---|---|
| R01 | Scam text arrives (setup) | S03, S30 | Heads-up, thread open, Automatic previews off | 3 min | `90s` |
| R02 | Morning brief + OTP + Mom's calls | S21–S24 | OTP visible on phone, `[OTP hidden]` in Hermes, Mom ×3 | 10 min | `90s`, bills line `[NEW]` |
| R03 | Money + UPI received | S25, S26, S11 | Real bank SMS | 6 min | `90s` |
| R04 | Bills due | S27 | Real biller SMS | 4 min | `[NEW]` |
| R05 | Subscriptions | S29 | Recurring debits | 4 min | `[NEW]` |
| R06 | Scam check with reasons | S31 | `high` + 3 reasons | 4 min | `90s` |
| R07 | Text Mom → Allow once | S32–S34 | Panel at 1×, bubble in Mom's thread | 3 min (1 take) | `90s` |
| R08 | Deny | S35, S36 | Deny, no retry, thread unchanged | 4 min | `90s` |
| R09 | Watch rule "delivered" | S37 | One alert path only | 6–20 min | `90s` |
| R10 | Parcels | S28 | Amazon delivered | 4 min | `[NEW]` |
| R11 | Battery below 20% | S38 | Battery below 20% and unplugged | 2 min (after drain) | `[NEW]` |
| R12 | Find my phone under the bed | S39–S41 | Webcam under bed, real ring audio | 6 min | `90s` |
| R13 | Timed `phone_status` + helper log | S42, S46, S47 | 5 timed runs with the request-only snippet | 4 min | |
| R14 | B-roll | S01, S02, S08, S11, S14, S20 | Lock screen with contents hidden | 15 min | |

**Total raw:** about 70–85 min of footage.
**Motion-graphics-only shots** (no recording needed): S04–S07, S09, S10, S12, S13, S15–S19, S43–S45, S48–S56.
