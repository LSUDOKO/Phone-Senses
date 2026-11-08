# Phone Senses: shot list (3:20, 56 shots)

Times are film times and match `SCRIPT.md`. Recording IDs (`R##`) match `RECORDING_PLAN.md`.

**Tags**
- `[NEW]`: the shot depends on a feature still being built. Cut it if the feature isn't working on the real phone.
- `90s`: the shot is in the ≤90 s submission cut (assembly at the end).

## Global spec
**Canvas and type**
- 1920×1080, 30 fps. Title-safe inset is 96 px.
- Headlines: Archivo ExtraBold, width 112–125 %, 96–140 px, Paper `#F1F1EE` on Ink `#050507`, at most 6 words.
- Labels: Geist Mono, 14–18 px, uppercase, +8 % tracking, Mist `#9AA0B4`. Corner labels sit 48 px from the frame edges.
- Source lines: Geist Mono, 14 px, Mist, bottom-left. Hold them for at least 2.5 s.

**Colour and texture**
- Ultramarine `#1F2BFF` only marks the answer or action: Hermes replies, highlight boxes, the reconnected line, "Allow once".
- Never use red. Alarm is shown with motion (glitch, shake), not colour.
- Background: Ink, an ultramarine blur field at 6–12 % opacity, film grain at 4 %, and a dashed grid of 1 px Mist lines at 15 % opacity on a 120 px spacing.

**Motion**
- Easing is always `cubic-bezier(0.16, 1, 0.3, 1)`.
  - Word reveal: 450 ms per word, 60 ms stagger, a mask rising from the baseline.
  - Mask wipe: 600 ms.
  - Zoom-through: 700 ms.
  - Number roll: 900 ms.
  - No bounce, no overshoot.
- Holds: every headline stays fully readable for at least 1.2 s.

**Screen footage**
- Hermes TUI at 20–22 pt font, dark theme. The phone comes in through the scrcpy mirror and is placed in a phone frame drawn from `brand/mark.svg` proportions, with a 2 px ultramarine rim light.
- On real-recording shots, place the corner label `REAL PHONE · MOTO G34` at top right.
- On self-sent texts, add `RE-CREATED · SENT TO MY OWN NUMBER` at bottom left.

**Speed**
- Raw Hermes replies take 10–60 s. Cut them with speed ramps: typing at 1.5–2×, the thinking spinner at 8–16× or a jump cut, the answer streaming at 3–6×.
- The **approval panel always plays at 1×**.
- Never speed up across a tool's visible result. Freeze and highlight instead.

**Captions**: burned in. Archivo SemiBold, 44 px, Paper, bottom-centre, max 2 lines. The current word turns Ultramarine.

**SFX**: use CC0 sources only (freesound.org filtered to CC0, or self-recorded). Avoid Apple, Google or Motorola trademark sounds. Record the phone's real ring in R12.

---

## 1. Cold open (0:00–0:10)

### S01 · 0:00.0–0:02.5 · Cold open · `90s`
- **Source:** real recording: phone screen (R14-a), plus motion graphics.
- **Visual:**
  - The real lock screen, with "sensitive content" hidden so only app names and counts show. Notifications flood upward; a 4–6× ramp of the real scroll.
  - A Geist Mono counter in the corner races 0 → 200.
- **On screen:** label `NOTIFICATIONS TODAY: 200`. Use the real Digital Wellbeing count.
- **Motion:** slow push-in of 3 %. The counter rolls on the brand ease.
- **Transition:** hard cut on the SFX hit.
- **SFX:** layered soft notification ticks build to a sub-hit at 2.5 s.

### S02 · 0:02.5–0:05.0 · Cold open · `90s`
- **Source:** real recording: phone screen (R14-b).
- **Visual:** a macro push into the missed-call notification `Mom · 3 missed calls`. The number is never visible.
- **On screen:** none. The VO carries it.
- **Motion:** 115 % scale-in over 2.5 s on the brand ease.
- **Transition:** hard cut.
- **SFX:** a muted ringtone stab, played backwards, into a hit.

### S03 · 0:05.0–0:08.2 · Cold open · `90s`
- **Source:** real recording: phone screen (R01).
- **Visual:**
  - The KYC scam SMS arrives as a heads-up notification.
  - Freeze on "BLOCKED". An RGB-split glitch runs for 6 frames, in ink and ultramarine only.
- **On screen:** label `RE-CREATED · SENT TO MY OWN NUMBER`.
- **Motion:** 2-frame shake on the glitch.
- **Transition:** hard cut.
- **SFX:** glitch tick, then a hit.

### S04 · 0:08.2–0:10.0 · Cold open · `90s`
- **Source:** motion graphics.
- **Visual:** kinetic type over the ink grain field.
- **On screen:** headline `EXAM WEEK.`
- **Motion:** word reveal with a 60 ms stagger; tracking tightens by 4 % during the hold.
- **Transition:** 4 frames of black.
- **SFX:** silence after a tape-stop.

## 2. Title reveal (0:10–0:18)

### S05 · 0:10.0–0:12.8 · Title
- **Source:** motion graphics.
- **Visual:** notification "blocks" fall and stack into the block-built phone mark (`brand/mark.svg`).
- **On screen:** headline `HIS PHONE KNEW ALL OF IT.`
- **Motion:** blocks drop with the brand ease on a 70 ms stagger; the headline reveals word by word.
- **Transition:** the mark slides left as a match move into S06.
- **SFX:** soft wooden clicks for each block.

### S06 · 0:12.8–0:15.6 · Title
- **Source:** motion graphics.
- **Visual:** a laptop outline in dashed Mist lines. An empty Hermes prompt `☤ ❯ _` blinks.
- **On screen:** headline `HIS AGENT KNEW NOTHING.`. It slams in on the bass entry at ~0:13.5.
- **Motion:** the headline scales from 104 % to 100 % in 300 ms on the hit, then holds.
- **Transition:** match cut. The phone mark's top-corner block lifts away.
- **SFX:** the music's bass entry plus a sub-hit.

### S07 · 0:15.6–0:18.0 · Title · `90s`
- **Source:** motion graphics.
- **Visual:**
  - On the VO word "now" ("Until now.", 0:16.2–0:17.4), the top corner of the mark breaks off and becomes the sensing pixel, which floats and pulses once.
  - The chrome-gradient wordmark `PHONE SENSES` reveals with a left-to-right mask.
- **On screen:** wordmark, plus the label `A PLUGIN FOR HERMES AGENT`.
- **Motion:** 600 ms mask wipe. The pixel drifts 24 px up and right.
- **Transition:** the wordmark dissolves into grain, then a hard cut.
- **SFX:** a high "ping" for the pixel, then a riser tail.

## 3. The problem (0:18–0:50)
*Music is low-passed to about 600 Hz throughout.*

### S08 · 0:18.0–0:21.5 · Problem
- **Source:** camera insert (R14-d). Fallback: a still photo of Arpit with a slow push.
- **Visual:** Arpit at his desk in Hamirpur with exam notes, the phone face-down and buzzing. Tripod, handheld feel, warm practical light.
- **On screen:** label `ARPIT SINGH · HAMIRPUR, HP · FINAL YEAR`.
- **Motion:** 2 % push-in.
- **Transition:** a whip-blur into S09.
- **SFX:** room tone, plus the phone's buzz on the desk.

### S09 · 0:21.5–0:25.3 · Problem
- **Source:** motion graphics.
- **Visual:** ₹, parcel, phone-call and bell glyphs, drawn in line style, rain into the phone mark.
- **On screen:** headline `IT ALL LANDS HERE.`
- **Motion:** glyphs fall with a 40 ms stagger and the brand ease; the mark glows a little brighter with each glyph.
- **Transition:** the mark zooms through into S10.
- **SFX:** soft impacts for each glyph.

### S10 · 0:25.3–0:29.5 · Problem
- **Source:** motion graphics.
- **Visual:** a stat card.
- **On screen:**
  - Headline `25.47 BILLION`.
  - Sub `UPI PAYMENTS · OCTOBER 2026`.
  - Source line `NPCI, UPI Product Statistics, Oct 2026`.
- **Motion:** 900 ms number roll; the sub reveals 200 ms later.
- **Transition:** cut.
- **SFX:** a mechanical counter tick that stops on the final value.

### S11 · 0:29.5–0:32.5 · Problem
- **Source:** real recording: phone screen (R14-c).
- **Visual:** his bank's real SMS thread scrolling fast, in a 6× ramp. **Blur the amounts, account digits, balances and reference numbers.**
- **On screen:** label `REAL PHONE · MOTO G34`.
- **Motion:** speed ramp 6× → 1×, landing on one SMS with its amount blurred.
- **Transition:** cut.
- **SFX:** a scroll whoosh.

### S12 · 0:32.5–0:36.5 · Problem
- **Source:** motion graphics.
- **Visual:** 13 grey message bubbles stack in a column and jitter.
- **On screen:**
  - Headline `13 SCAM MESSAGES A DAY`.
  - Source line `Average in India, across text, email and social · McAfee State of the Scamiverse, Feb 2026`.
- **Motion:** the bubbles pop in on a 50 ms stagger, with a 1 px jitter at 12 fps.
- **Transition:** the bubbles collapse into a ₹ glyph, matching into S13.
- **SFX:** 13 quick ticks.

### S13 · 0:36.5–0:42.0 · Problem
- **Source:** motion graphics.
- **Visual:** a stat card.
- **On screen:**
  - Headline `₹55,050 CRORE+ REPORTED`.
  - Sub `IN CYBER FRAUD · 2021–2025`.
  - Source line `65.9 lakh+ financial-fraud complaints · MHA / I4C via PIB, 21 Jul 2026`.
- **Motion:** number roll; the sub reveals after it.
- **Transition:** cut to real footage.
- **SFX:** low drone swell.

### S14 · 0:42.0–0:45.8 · Problem
- **Source:** real recording: laptop Hermes (R14-e), or a camera insert of the desk.
- **Visual:** Hermes TUI with an idle prompt. The camera or a digital push racks focus to the phone lying next to the laptop.
- **On screen:** none.
- **Motion:** rack focus, or a 1:1 digital push.
- **Transition:** freeze, then the dashed line draws in (S15).
- **SFX:** keyboard room tone.

### S15 · 0:45.8–0:50.0 · Problem
- **Source:** motion graphics over the frozen S14.
- **Visual:** a dashed Mist line from the laptop to the phone snaps in the middle, and the two halves sag.
- **On screen:** headline `IT CAN'T SEE ANY OF IT.`
- **Motion:** the line draws on over 500 ms, then the break, then the halves fall 8 px.
- **Transition:** 0.5 s hold, then the music filter opens at 0:50.
- **SFX:** a small snap, then silence.

## 4. The painkiller (0:50–1:10)
*The music filter opens over one bar.*

### S16 · 0:50.0–0:52.8 · Painkiller
- **Source:** motion graphics.
- **Visual:** the two halves of the broken line pull together and fuse in Ultramarine, and light travels along it.
- **On screen:** a flash of the wordmark `PHONE SENSES`, held for 0.8 s.
- **Motion:** 400 ms snap on the brand ease, then a light sweep.
- **Transition:** the line extends into the S17 diagram.
- **SFX:** a riser resolving into a clean chime.

### S17 · 0:52.8–0:58.0 · Painkiller
- **Source:** motion graphics.
- **Visual:**
  - Three nodes: `HERMES` (laptop) → `PHONE SENSES` → `YOUR PHONE`.
  - Six sense icons light up in turn along the line: bell, SMS, ₹, call log, battery, location.
- **On screen:** headline `YOUR PHONE'S SENSES, FOR HERMES`.
- **Motion:** the nodes reveal left to right; icons pulse on a 200 ms stagger.
- **Transition:** wipe into the split screen.
- **SFX:** six soft ticks, tuned to the track's key.

### S18 · 0:58.0–1:02.5 · Painkiller · `90s`
- **Source:** motion graphics.
- **Visual:** split screen.
  - Left: a ghost hand taps a phone wireframe, with a step counter climbing to 18.6.
  - Right: one Ultramarine line from the laptop to the phone, with a counter at 10.7.
- **On screen:**
  - Headline `NO SCREEN TAPPING.`
  - Labels `SCREEN AGENTS: 18.6 STEPS` and `COMMAND-LINE: 10.7`.
  - Source line `Mean steps per task, CLI-Advantage Suite · Gu et al., arXiv 2606.19388, 2026`.
- **Motion:** the counters roll; the left side flickers once per tap.
- **Transition:** the right half takes over the frame.
- **SFX:** tap clicks on the left; one clean whoosh on the right.

### S19 · 1:02.5–1:06.0 · Painkiller
- **Source:** motion graphics.
- **Visual:** the outline of the approval panel draws itself in Ultramarine: a box with four options and the `1. Allow once` row highlighted. It is stylised, not a screenshot.
- **On screen:** headline `IT ASKS FIRST.`
- **Motion:** stroke draw-on over 700 ms.
- **Transition:** the panel shrinks into the sensing pixel.
- **SFX:** a soft lock "click".

### S20 · 1:06.0–1:10.0 · Painkiller
- **Source:** motion graphics into real recording: phone screen (R14-a lock screen).
- **Visual:** match cut. The sensing pixel becomes the phone's front camera hole, and a zoom-through lands on the real lock screen at about 7:00.
- **On screen:** label `REAL PHONE · MOTO G34 · ANDROID 15`.
- **Motion:** 700 ms zoom-through on the brand ease.
- **Transition:** the lock screen slides left to make room for the laptop; the side-by-side layout starts.
- **SFX:** a whoosh, then quiet room tone.

## 5. Product walkthrough (1:10–2:25)
**Layout for every real shot here**
- The laptop (Hermes TUI) fills the left 64 %. The phone mirror sits at the right, 36 % wide, in the brand phone frame.
- A highlight box (2 px Ultramarine, 8 px radius) marks the line the VO is talking about. Everything else dims to 40 %.

### S21 · 1:10.0–1:14.3 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes plus real recording: phone screen (R02).
- **Hermes question (type exactly):** `Good morning, give me my phone brief.`
- **Phone must show:**
  - Before Enter, the notification shade pulled down on the real notifications.
  - Visible in the shade: the Mom missed-call notification and the OTP SMS notification, with its digits blurred in post.
- **On screen:** label `REAL PHONE · MOTO G34`.
- **Motion:** typing at 1.5×. Push-in of 4 % on the laptop.
- **Transition:** jump cut past the spinner.
- **SFX:** real keystrokes.
- **Raw → cut:** ~45–90 s raw → 4.3 s.

### S22 · 1:14.3–1:18.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes plus phone (R02).
- **Visual:** the brief streams in at 4×, then freezes. The highlight box snaps around `[OTP hidden]` in the Hermes output.
- **Phone must show:** the same OTP SMS, digits blurred in post. The viewer sees that the code exists on the phone and is hidden in Hermes.
- **On screen:** label `OTPS HIDDEN BY DEFAULT`. Don't use an absolute claim like "never reaches the model": the masking is pattern-based.
- **Motion:** freeze-frame, then the highlight box scales from 96 % to 100 %.
- **Transition:** the dim deepens as we move to the next line.
- **SFX:** a UI tick on the box.

### S23 · 1:18.0–1:22.5 · Walkthrough · `90s` · **AHA**
- **Source:** real recording: laptop Hermes plus phone (R02).
- **Visual:**
  - The whole brief dims except the missed-calls line, `Mom … 3 missed calls`.
  - Match cut: the line slides right onto the phone, where the call log is open showing the same three missed calls from Mom.
- **Phone must show:** after the brief, Arpit opens Phone → Recents. Mom's three missed calls are at the top. No numbers are visible; the contact name is "Mom".
- **How the brief gets this:** `phone_brief` lists every missed call from the last 24 h with its contact name. If Termux:API can't read contacts, it shows the number instead. Hermes then summarises the list.
  - **VERIFY** the summary wording in the R02 dry run, and highlight whatever line Hermes actually prints.
  - If it shows numbers, grant Termux:API the Contacts permission, or blur the numbers and add the follow-up `Who called me this morning?`.
- **On screen:** headline `3 MISSED CALLS. FROM MOM.`
- **Motion:** match move of the highlighted line onto the call-log row.
- **Transition:** cut.
- **SFX:** music sits on a held chord; a soft heartbeat thump.

### S24 · 1:22.5–1:25.5 · Walkthrough · `[NEW]`
- **Source:** real recording: laptop Hermes (R02).
- **Visual:** the brief's bills line is highlighted: biller, amount (blurred if he likes) and `due tomorrow`.
- **Phone must show:** optional. The biller's real SMS, with the amount and account digits blurred.
- **On screen:** headline `DUE TOMORROW.`
- **Motion:** highlight box.
- **Transition:** cut.
- **SFX:** tick.
- **Fallback:** if `phone_brief` has no bills line, hold S23 for 3 s with the headline `HE'D NEVER HAVE SEEN IT.`

### S25 · 1:25.5–1:30.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes (R03).
- **Hermes question (type exactly):** `Where did my money go this week? Sync my bank SMS first.`
- **Phone must show:** nothing new. Optionally, keep the bank SMS thread open, with amounts blurred.
- **Visual:** the spending-by-category table streams in. On the freeze, the rows morph into Ultramarine horizontal bars, with the category names kept.
- **On screen:** label `FROM BANK + UPI SMS`.
- **Motion:** table-to-bars morph over 600 ms.
- **Transition:** cut.
- **SFX:** bar "fills".
- **Raw → cut:** ~30–60 s → 4.5 s.

### S26 · 1:30.0–1:33.3 · Walkthrough
- **Source:** real recording: laptop Hermes (R03).
- **Hermes question:** `How much did I receive by UPI this week?`
- **Visual:** the answer total is highlighted.
- **On screen:** label `UPI RECEIVED`.
- **Motion and transition:** jump cut; highlight.
- **SFX:** a coin-like soft chime (CC0).

### S27 · 1:33.3–1:36.0 · Walkthrough · `[NEW]`
- **Fallback for S27–S29:** if none of bills, parcels or subscriptions ships, replace all three with one shot, 1:33.3–1:42.2.
  - Show `Set a monthly food budget of 3000 rupees and tell me how much I've used.`, the budget set and percent used (from `phone_budget_set`).
  - Read the FALLBACK VO line from `SCRIPT.md`.
- **Source:** real recording: laptop Hermes (R04).
- **Hermes question:** `What bills are due soon?`
- **Visual:** the list of dues with dates. Blur amounts if he wants.
- **On screen:** label `BILLS`.
- **Motion:** one bar long (~1.9 s) plus a 0.8 s hold. Cut on the downbeat.
- **SFX:** tick.

### S28 · 1:36.0–1:38.6 · Walkthrough · `[NEW]`
- **Source:** real recording: laptop Hermes (R10).
- **Hermes question:** `Where are my parcels?`
- **Visual:** the order statuses. The re-created Amazon "delivered" line shows, plus any real orders.
- **On screen:** label `PARCELS`.
- **Motion:** cut on the downbeat.
- **SFX:** tick.

### S29 · 1:38.6–1:42.2 · Walkthrough · `[NEW]`
- **Source:** real recording: laptop Hermes (R05).
- **Hermes question:** `What subscriptions am I paying for, and what's the monthly total?`
- **Visual:** the list plus monthly total; the total is highlighted.
- **On screen:** label `SUBSCRIPTIONS / MONTH`.
- **Motion:** cut. The hats drop out of the music here, leading into the breakdown.
- **SFX:** a reverse swell into the breakdown.

### S30 · 1:42.2–1:46.3 · Walkthrough · `90s`
- **Source:** real recording: phone screen (R01).
- **Visual:** the breakdown begins. Full-frame phone: the Messages app with the KYC text open.
- **Phone must show:** `Dear customer your SBI account will be BLOCKED today. Update KYC immediately: http://sbi-kyc-update.co/in`. The sender is his own number, so blur it.
- **On screen:** label `RE-CREATED · SENT TO MY OWN NUMBER`.
- **Motion:** slow 2 % push; a 1-frame glitch on "BLOCKED".
- **Transition:** the phone slides right and the laptop slides in.
- **SFX:** music breakdown (no bass), plus a low pulse.

### S31 · 1:46.3–1:51.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes (R06).
- **Hermes question (type exactly):** `I got a weird SMS about my KYC. Is it a scam?`
- **Visual:**
  - The answer shows `high` risk.
  - Three reasons reveal one by one with highlight boxes: `urgency: 'will be BLOCKED'` · `kyc / identity update: 'Update KYC'` · `look-alike or risky link: sbi-kyc-update.co`.
- **On screen:** headline `SCAM. HERE'S WHY.`
- **Motion:** three boxes on a 400 ms stagger.
- **Transition:** cut.
- **SFX:** three UI ticks, rising in pitch.
- **Raw → cut:** ~30 s → 4.7 s.

### S32 · 1:51.0–1:54.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes (R07).
- **Hermes question (type exactly):** `Text Mom: I'll call you after the exam.`
- **Visual:** typing at 1.5×, then a jump cut past any contact lookup.
- **On screen:** none.
- **SFX:** keys.

### S33 · 1:54.0–1:57.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes (R07). **Play at 1×.**
- **Visual:** the real Hermes approval panel:
  - `⚠️ Dangerous Command` / `<phone_sms_send> (plugin approval rule)`
  - `❯ 1. Allow once` · `2. Allow for this session` · `3. Add to permanent allowlist` · `4. Deny`
  - `Send SMS from your phone to +91X****XXXX (…chars): "I'll call you after the exam."`
  - Everything except the panel dims to 30 %.
- **On screen:** label `NOTHING SENT YET`.
- **Motion:** push-in to 112 % on the panel over 3 s.
- **Transition:** none. Hold until the drop.
- **SFX:** music in its last breakdown bar; a soft clock tick.

### S34 · 1:57.0–2:00.5 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes plus real recording: phone screen (R07).
- **Visual:**
  - `1. Allow once` is selected and Enter is pressed **on the music drop**.
  - The Hermes log line `⚠ Approval: <phone_sms_send> (plugin approval rule) → allowed once` flashes.
  - Hard cut to the phone: Mom's Messages thread, with the new outgoing bubble `I'll call you after the exam.` and its "Sent" status.
- **Phone must show:** the sent bubble arriving. Crop to the last bubble and **blur every older message**.
- **On screen:** headline `ALLOW ONCE.` with "ONCE" in Ultramarine. Label `FROM HIS OWN SIM`.
- **Motion:** the Enter press syncs to the bass drop at ~1:57.
- **Transition:** hard cut, laptop to phone.
- **SFX:** the drop, plus the SMS "sent" whoosh (CC0).

### S35 · 2:00.5–2:06.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes (R08). The panel plays at 1×.
- **Hermes question (type exactly):** `Also text Mom that I skipped lunch.`
- **Visual:** the panel appears with the exact text. The cursor moves down to `4. Deny` and Enter is pressed.
- **On screen:** headline `DENY.` Label `NOTHING LEAVES THE PHONE`.
- **Motion:** typing at 2×, then the panel at 1×.
- **SFX:** a cursor tick for each move; a muted "thunk" on Deny.

### S36 · 2:06.0–2:08.5 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes plus phone (R08).
- **Visual:**
  - Hermes's reply confirms it did not send.
  - The phone's Messages thread is unchanged: the last bubble is still "I'll call you after the exam."
- **Phone must show:** open Mom's thread after the Deny. No new bubble.
- **On screen:** label `NO RETRY`.
- **Transition:** whip to the library insert.
- **SFX:** whoosh.

### S37 · 2:08.5–2:13.0 · Walkthrough · `90s`
- **Source:** camera insert (library), plus real recording: phone screen and laptop Hermes (R09).
- **Visual:**
  - 1.0 s: the library, the phone face-down on a book.
  - Then the phone mirror: the SMS `Your Amazon order for Casio fx-991ES Plus has been delivered.` arrives.
  - Then Hermes: `Any watch alerts on my phone?` with the match highlighted.
  - Optional: a Telegram alert from a Hermes cron job, if it's configured.
- **Phone must show:** the "delivered" SMS heads-up. It's self-sent, so label it.
- **On screen:** label `WATCH RULE · "DELIVERED" · ALERTS ONCE` and `RE-CREATED · SENT TO MY OWN NUMBER`.
- **Motion:** three quick cuts on the beat.
- **SFX:** a library hush, then the notification tick.

### S38 · 2:13.0–2:16.0 · Walkthrough · `[NEW]`
- **Source:** real recording: laptop Hermes or Telegram on the phone (R11).
- **Visual:** the battery-below watch alert, e.g. `Battery at 19 %, below your 20 % rule`.
- **On screen:** label `BATTERY < 20%`.
- **Fallback:** if battery watch isn't shipped, use a `debit_over` watch rule, which exists today. Set it low (e.g. ₹100) and make one real payment above it, then show the match. Read the FALLBACK VO line in `SCRIPT.md`. Label: `DEBIT > ₹100`.
- **SFX:** a low-battery-style blip (CC0, not the Android sound).

### S39 · 2:16.0–2:19.8 · Walkthrough
- **Source:** camera insert (R12).
- **Visual:** a dark room at night. Arpit pats the duvet and checks his pockets, frustrated. Lamp light.
- **On screen:** none.
- **Motion:** handheld.
- **Transition:** cut to the laptop.
- **SFX:** room tone, fabric rustle.

### S40 · 2:19.8–2:24.0 · Walkthrough · `90s`
- **Source:** real recording: laptop Hermes (R12) plus camera insert (the laptop webcam pointing under the bed, recorded in OBS).
- **Hermes question (type exactly):** `I can't find my phone, make it ring for 15 seconds.`
- **Phone must show (on the webcam):** under the bed, the phone rings at full volume, speaks, vibrates and strobes its torch.
- **On screen:** label `RING · SPEAK · VIBRATE · TORCH`.
- **Motion:** typing at 2×. Cut to the webcam on the first torch flash.
- **SFX:** the **real ring and voice from the phone**. Pull the music down 6 dB here.

### S41 · 2:24.0–2:25.0 · Walkthrough
- **Source:** camera insert (R12).
- **Visual:** his hand pulls the glowing phone from under the bed.
- **Transition:** a flash on the torch strobe, out to ink.
- **SFX:** the ring cuts off and the music ducks for the hood section.

## 6. Under the hood (2:25–2:45)
*Music: duck −8 dB, low-pass. Diagram shots use dashed grid lines and Geist Mono throughout. No secret, signature or pairing code is ever real.*

### S42 · 2:25.0–2:28.0 · Under the hood
- **Source:** real recording: laptop Hermes (R13), then motion graphics.
- **Hermes question:** `What's my phone battery?`
- **Visual:** freeze on the question. The camera pulls back *through* the screen glass into a dashed-grid space.
- **On screen:** label `ONE REAL REQUEST`.
- **Motion:** 700 ms pull-back zoom-through.
- **SFX:** a glassy whoosh.

### S43 · 2:28.0–2:31.8 · Under the hood
- **Source:** motion graphics.
- **Visual:**
  - Node `pre_tool_call` hook. A token `phone_status` slides through an open gate.
  - A side branch, greyed, shows the four gated tools stacked behind a closed gate: `phone_sms_send · phone_call · phone_photo · phone_otp_reveal → APPROVAL PANEL`.
- **On screen:** label `4 ACTIONS GATED · READS PASS`.
- **Motion:** the gate opens on the brand ease and the token travels.
- **SFX:** a soft latch.

### S44 · 2:31.8–2:36.0 · Under the hood · `90s`
- **Source:** motion graphics.
- **Visual:** Geist Mono types out the canonical string, one field per line, each with a label at right:
  ```
  GET                         METHOD
  /v1/status                  PATH (+QUERY)
  1794274920                  TIMESTAMP
  9f2c1e7a…  (32 hex)         ONE-TIME NONCE
  e3b0c442…7852b855           SHA256(BODY)
  ```
  The block feeds into `HMAC-SHA256( secret )`, which outputs `X-PS-Signature: 4be1…` (a fake value).
- **On screen:** headline `SECRET NEVER SENT`.
- **Motion:** typewriter at 40 chars/s; the arrow draws on.
- **SFX:** soft typewriter ticks.

### S45 · 2:36.0–2:39.0 · Under the hood
- **Source:** motion graphics.
- **Visual:** a copy of the request flies at the phone again and bounces off with `401 · nonce reused`.
- **On screen:** label `±60 S CLOCK WINDOW · ONE-TIME NONCE`.
- **Motion:** a bounce with no overshoot: hit, then a 120 px recoil on the brand ease.
- **SFX:** a dull "denied" thud.

### S46 · 2:39.0–2:42.5 · Under the hood
- **Source:** real recording: phone screen (R13: the Termux helper log), plus motion graphics.
- **Visual:**
  - The Termux helper log scrolling, with the line `[phone-senses] GET /v1/status 200` arriving live.
  - An overlay arrow runs `termux-battery-status` → `ANDROID BATTERY API`.
- **Phone must show:** the Termux session running the helper, with the new log line appearing as the question is asked. Crop out the start line that shows the IP and port.
- **On screen:** label `STDLIB PYTHON · FIXED COMMAND · NO SHELL`.
- **SFX:** a terminal blip.

### S47 · 2:42.5–2:45.0 · Under the hood
- **Source:** real recording: laptop Hermes. It's the terminal beside Hermes, R13 take 2.
- **Visual:** the timing snippet from R13 prints five lines like `round trip 1.12 s · battery 64%`. It times only the signed request. It doesn't print the Wi-Fi SSID or IP.
- **On screen:** headline `0.9–2 S ROUND TRIP`. Label `MEASURED · MOTO G34`.
  - If this take measures outside 0.9–2 s, show the measured range instead and adjust the VO.
- **Motion:** the highlight box sweeps down the five `round trip` values.
- **Transition:** the music filter releases into S48.
- **SFX:** a clean chime.

## 7. Impact (2:45–3:05)

### S48 · 2:45.0–2:49.5 · Impact
- **Source:** motion graphics, with real footage reused from S01.
- **Visual:** split screen. The left half shows the notification flood from S01, desaturated and grey.
- **On screen:** label `BEFORE`.
- **Motion:** the left half slides in.
- **SFX:** a muffled notification bed.

### S49 · 2:49.5–2:53.0 · Impact
- **Source:** motion graphics, with real footage reused from S23.
- **Visual:** the right half wipes in, showing one question and one Ultramarine answer card (the brief, with Mom's missed calls).
- **On screen:** label `AFTER`.
- **Motion:** 600 ms mask wipe.
- **SFX:** the music's full return.

### S50 · 2:53.0–2:57.0 · Impact
- **Source:** motion graphics.
- **Visual:** benefit card 1.
- **On screen:**
  - Headline `READS ANDROID, NOT PIXELS`.
  - Sub `Screen agents 18.6 steps · command-line 10.7`.
  - Source line `Gu et al., arXiv 2606.19388, 2026`.
- **Motion:** card rises 40 px and fades in on the brand ease.
- **SFX:** hit.

### S51 · 2:57.0–3:01.0 · Impact
- **Source:** motion graphics.
- **Visual:** benefit card 2, with four small icons for SMS, call, photo and OTP.
- **On screen:** headline `4 ACTIONS ASK FIRST`. Sub `SMS · CALL · PHOTO · OTP REVEAL`.
- **Motion:** the four icons lock in with a 100 ms stagger.
- **SFX:** four soft locks. The bass drops out of the music here (~2:57).

### S52 · 3:01.0–3:05.0 · Impact
- **Source:** motion graphics.
- **Visual:** benefit card 3.
- **On screen:** headline `OTPS HIDDEN BY DEFAULT`. Sub `0 THIRD-PARTY SERVICES · 0 TELEMETRY`.
- **Motion:** card rises in.
- **Transition:** the cards collapse into the mark.
- **SFX:** a resolve chime.

## 8. Outro (3:05–3:20)

### S53 · 3:05.0–3:08.5 · Outro · `90s`
- **Source:** motion graphics.
- **Visual:** the block-built mark rebuilds and the sensing pixel clicks back into its corner. The chrome wordmark `PHONE SENSES` reveals.
- **On screen:** the wordmark.
- **Motion:** pixel return over 500 ms on the brand ease; mask wipe.
- **SFX:** a small "click" and a shimmer.

### S54 · 3:08.5–3:12.5 · Outro · `90s`
- **Source:** motion graphics.
- **Visual:** the tagline under the wordmark.
- **On screen:** headline `IT ASKS BEFORE IT ACTS.`, with "ASKS" in Ultramarine.
- **Motion:** word reveal.
- **SFX:** music pads only.

### S55 · 3:12.5–3:17.0 · Outro · `90s`
- **Source:** motion graphics.
- **Visual:** the end card on Ink with the grain field.
- **On screen:**
  - Label `BUILT FOR HERMES AGENT`.
  - `phone-senses.pages.dev`
  - `github.com/LSUDOKO/Phone-Senses`
  - `ARPIT SINGH`
  - Small print: `Music: "Space Voyage" by Ekilorea Sound (CC0) · Sources: NPCI · McAfee · MHA/PIB · Gu et al. 2026`.
  - Don't show `hermes plugins install phone-senses` until the catalog PR is merged.
- **Motion:** lines reveal on an 80 ms stagger.
- **SFX:** none.

### S56 · 3:17.0–3:20.0 · Outro
- **Source:** motion graphics.
- **Visual:** hold the end card. On "Link below" the `github.com/LSUDOKO/Phone-Senses` line pulses Ultramarine once. The sensing pixel blinks once and goes dark at exactly 3:20.0.
- **SFX:** the music's fade reaches silence.

---

## ≤90 s submission cut (assembly)
The hackathon requires under 90 s that "show the plugin working".

**Shot order**
- S01–S04
- S07
- S18
- S21–S23
- S25
- S30–S31
- S32–S34
- S35–S36
- S37
- S40
- S44
- S53–S55

**Target length:** ~85 s. S34 starts at about 48.7 s.

**Notes**
- Reuse the same VO lines for these shots.
- **Music edit 1:** play the track from 0:00. Remove about 37 bars (~68.8 s at ~129 BPM) from the groove between track ~0:20 and ~1:28, cutting on bar lines. The breakdown then lands on S30 and the drop (track ~1:57) on S34's Enter.
- **Music edit 2:** at S53 (cut ~73 s), jump to the outro pads at track ~2:59 and let them fade out by the end.
- Verify both edits by ear, and read `audio/LICENSE-music.md` first.
- Re-run `vo_check.py` on a copy of the script trimmed to these lines if you re-time them.
