# Phone Senses: launch film script (3:20)

**Voice:** warm, energetic, female. She is telling a friend's story: third person about Arpit,
second person only in the outro. Unhurried, with a smile on "Allow once".

**How to read this file**
- A line starting with `VO:` is spoken. Everything else is direction.
- Numbers are spelled the way they are said, so the TTS read and the word count stay honest.
- Each VO line's visual sits under it. Shot IDs (`S##`) match `SHOTLIST.md`.
- Recording IDs (`R##`) match `RECORDING_PLAN.md`.

**Tags**
- `[NEW]` means the line depends on a feature still being built: bills, deliveries, subscriptions or battery watch. If that feature isn't merged and working on the real phone by recording day, use the fallback given under that line.
- `[VERIFY]` means Arpit must confirm the line is true for him.

**Pacing check:** `python demo/film/vo_check.py` counts the VO words and flags any line over 2.6 words per second. Add `--fallback` to check the no-`[NEW]`-features version.

**Music:** `audio/music.mp3` ("Space Voyage", CC0). The cue times below are track times. The track starts at film 0:00. See `audio/LICENSE-music.md`.

---

## 1. Cold open: 0:00–0:10 (kinetic hook)
*Music: intro pads, no bass. Each line lands on a hard SFX hit.*

- **0:00.0–0:02.5** · VO: Two hundred notifications today.
  - Visual (S01): the real lock screen floods with notifications; a mono counter races to `200`. `[VERIFY]` Use the real count from Digital Wellbeing on recording day, in both the VO and the counter.
- **0:02.5–0:05.0** · VO: Three missed calls from Mom.
  - Visual (S02): macro push into the real missed-call notification: `Mom · 3 missed calls`.
- **0:05.0–0:08.2** · VO: A text that says his account is blocked.
  - Visual (S03): the KYC scam SMS drops in as a heads-up. A glitch on the word "BLOCKED", in ink and ultramarine only, no red. Tiny corner label: `RE-CREATED · SENT TO MY OWN NUMBER`.
- **0:08.2–0:10.0** · VO: All in exam week.
  - Visual (S04): kinetic type `EXAM WEEK.` slams over the ink grain field. Cut to black for 4 frames.

## 2. Title reveal: 0:10–0:18
*Music: bass and kick enter at ~0:13.5. The title locks there.*

- **0:10.0–0:10.4** · PAUSE (section turn)
- **0:10.4–0:12.8** · VO: His phone knew all of it.
  - Visual (S05): the block-built phone mark assembles from falling notification blocks. Headline: `HIS PHONE KNEW ALL OF IT.`
- **0:12.8–0:15.6** · VO: His AI agent knew none of it.
  - Visual (S06): a laptop outline with an empty Hermes prompt, cursor blinking. On the bass hit (~0:13.5) the headline `HIS AGENT KNEW NOTHING.` slams in, word by word.
- **0:15.6–0:16.2** · PAUSE (beat)
- **0:16.2–0:17.4** · VO: Until now.
  - Visual (S07): on "now", the mark's top corner breaks off as the sensing pixel. The chrome wordmark `PHONE SENSES` reveals left to right. Mono label: `A PLUGIN FOR HERMES AGENT`.
- **0:17.4–0:18.0** · PAUSE (title holds)

## 3. The problem: 0:18–0:50
*Music: full groove, but low-passed to about 600 Hz and −6 dB. Muffled tension. Every stat carries its source line on screen (see `RESEARCH.md`).*

- **0:18.0–0:21.5** · VO: Meet Arpit. Final-year student in Hamirpur, Himachal Pradesh.
  - Visual (S08): camera insert of Arpit at his desk with notes and the phone face-down. Corner label: `ARPIT SINGH · HAMIRPUR, HP · FINAL YEAR`.
- **0:21.5–0:25.3** · VO: Everything in his life lands on his phone first.
  - Visual (S09): ₹, parcel, phone and bell glyphs rain into the phone mark. Headline: `IT ALL LANDS HERE.`
- **0:25.3–0:29.5** · VO: In October, India made over twenty-five billion UPI payments.
  - Visual (S10): a number roll to `25.47 BILLION`. Sub: `UPI PAYMENTS · OCTOBER 2026`. Source: `NPCI, UPI Product Statistics, Oct 2026`.
- **0:29.5–0:32.5** · VO: His bank texts him for each one.
  - Visual (S11): his real bank SMS thread scrolls fast. Amounts, account digits and balances are blurred. `[VERIFY]` His bank really sends an SMS per UPI payment.
- **0:32.5–0:36.5** · VO: The average Indian gets thirteen scam messages a day.
  - Visual (S12): 13 message bubbles stack and jitter. Headline: `13 SCAM MESSAGES A DAY`. Source: `Average in India, across text, email and social · McAfee State of the Scamiverse, Feb 2026`.
- **0:36.5–0:42.0** · VO: Since twenty twenty-one, Indians have reported over fifty-five thousand crore in cyber fraud.
  - Visual (S13): headline `₹55,050 CRORE+ REPORTED`. Source: `Financial cyber-fraud complaints 2021–2025 · MHA / I4C via PIB, 21 Jul 2026`.
- **0:42.0–0:45.8** · VO: His agent lives on his laptop, a foot away.
  - Visual (S14): the real laptop running Hermes, idle prompt. Rack focus to the phone lying next to it.
- **0:45.8–0:49.0** · VO: And it can't see any of it.
  - Visual (S15): a dashed line from the laptop to the phone breaks in the middle. Headline: `IT CAN'T SEE ANY OF IT.`
- **0:49.0–0:50.0** · PAUSE (section turn)

## 4. The painkiller: 0:50–1:10
*Music: the filter opens over one bar at 0:50. This is the lift.*

- **0:50.0–0:52.8** · VO: So Arpit built the fix: Phone Senses.
  - Visual (S16): the broken dashed line snaps shut in Ultramarine. The wordmark flashes once.
- **0:52.8–0:58.0** · VO: A Hermes plugin that lends his agent the senses of his own phone.
  - Visual (S17): a three-node diagram: `HERMES` → `PHONE SENSES` → `YOUR PHONE`. Sense icons (bell, SMS, ₹, call log, battery, location) light up along the line. Headline: `YOUR PHONE'S SENSES, FOR HERMES`.
- **0:58.0–1:02.5** · VO: No screen tapping. It talks to Android directly, through Termux.
  - Visual (S18): split screen. Left: a ghost hand taps a phone screen over and over (`SCREEN AGENTS: 18.6 STEPS`). Right: one clean Ultramarine line (`COMMAND-LINE: 10.7`). Source: `Mean steps per task, CLI-Advantage Suite · Gu et al., arXiv 2606.19388, 2026`. Headline: `NO SCREEN TAPPING.`
- **1:02.5–1:06.0** · VO: And it always asks before it touches anything.
  - Visual (S19): an outline of the approval panel draws itself in Ultramarine. Headline: `IT ASKS FIRST.`
- **1:06.0–1:09.5** · VO: Here's his real day, on his real phone.
  - Visual (S20): match cut. The sensing pixel becomes the phone's front camera, and a zoom-through lands on the real lock screen. Corner label: `REAL PHONE · MOTO G34 · ANDROID 15`.
- **1:09.5–1:10.0** · PAUSE (section turn)

## 5. Product walkthrough: 1:10–2:25
*Music:*
- *1:10–1:28: full drive.*
- *1:29–1:42: hats drop out.*
- *1:43–1:56: breakdown, no bass.*
- *~1:57: the drop.*

*Every Hermes reply is real and sped up; see the cut notes in `SHOTLIST.md`.*

### Morning brief (the aha)
- **1:10.0–1:14.3** · VO: Seven a.m., exam day. One question: give me my phone brief.
  - Visual (S21, R02): Arpit types `Good morning, give me my phone brief.` The phone beside him shows the notification shade pulled down. `[VERIFY]` Record around 7 a.m., or change "Seven a.m." to "Morning".
- **1:14.3–1:18.0** · VO: Hermes reads what his phone sees. Codes stay hidden.
  - Visual (S22, R02): the brief streams in. An Ultramarine box snaps around `[OTP hidden]`. On the phone, the OTP notification has its digits blurred.
- **1:18.0–1:22.5** · VO: Buried under two hundred notifications: three missed calls from Mom.
  - Visual (S23, R02): **the aha.** Everything dims except the brief's missed-calls line, `Mom · 3 missed calls`. Match cut to the phone's call log with the same three red entries.
- **1:22.5–1:25.5** · VO: And a bill due tomorrow he forgot. [NEW]
  - Visual (S24, R02): the brief's bills line lights up, `<biller> · ₹<amount> · due tomorrow`. Biller real, amount blurred if he wants. **Fallback if bills aren't in the brief:** hold S23 for 3 s with the headline `HE'D NEVER HAVE SEEN IT.` and read:
- **1:22.5–1:25.5** · FALLBACK VO: Things he'd never have spotted himself.

### Money
- **1:25.5–1:30.0** · VO: Where did his money go? Every bank SMS, sorted by category.
  - Visual (S25, R03): the question `Where did my money go this week?`. The spending table streams in, then morphs into Ultramarine category bars.
- **1:30.0–1:33.3** · VO: Plus every rupee that came in by UPI.
  - Visual (S26, R03): `How much did I receive by UPI this week?` and its answer.

### Bills, parcels, subscriptions
All three lines in this beat are `[NEW]`. Fast montage, one bar each.

- **1:33.3–1:36.0** · VO: His bills, before they're late. [NEW]
  - Visual (S27, R04): `What bills are due soon?` and the answer list.
- **1:36.0–1:38.6** · VO: His parcels, across his shopping apps. [NEW]
  - Visual (S28, R10): `Where are my parcels?` and the order statuses.
- **1:38.6–1:42.2** · VO: And his subscriptions, added up for the month. [NEW]
  - Visual (S29, R05): `What subscriptions am I paying for?` and the list plus monthly total.

**Fallback if none of the three ships:** cut S27–S29. Show `Set a monthly food budget of 3000 rupees and tell me how much I've used.` (`phone_budget_set`, which exists today) and read:
- **1:33.3–1:42.2** · FALLBACK VO: A food budget of three thousand rupees, and how much of it is already gone.

### The scam
- **1:42.2–1:46.3** · VO: Then the text that almost got him: update your KYC.
  - Visual (S30, R01): the breakdown hits. The real Messages app shows the KYC text. Corner label: `RE-CREATED · SENT TO MY OWN NUMBER`.
- **1:46.3–1:51.0** · VO: Hermes flags it and shows why: a look-alike link, a fake deadline.
  - Visual (S31, R06): `I got a weird SMS about my KYC. Is it a scam?` The answer: `high risk`. The three reasons reveal one by one: `urgency: 'will be BLOCKED'` · `KYC update` · `look-alike link: sbi-kyc-update.co`.

### Text Mom: the approval
- **1:51.0–1:54.0** · VO: Text Mom: I'll call after the exam.
  - Visual (S32, R07): Arpit types `Text Mom: I'll call you after the exam.`
- **1:54.0–1:57.0** · VO: Hermes stops. It shows the exact words.
  - Visual (S33, R07): the real panel appears: `⚠️ Dangerous Command · <phone_sms_send> (plugin approval rule)`, the four options, and `Send SMS from your phone to +91X****XXXX … "I'll call you after the exam."` Everything else drops to 30 % opacity. Music: last bar of the breakdown. Hold.
- **1:57.0–2:00.5** · VO: Allow once. It goes from his own SIM.
  - Visual (S34, R07): `❯ 1. Allow once` and Enter, **on the drop**. Hard cut to the phone: the sent bubble lands in Mom's thread. Crop or blur all older messages.

### Deny
- **2:00.5–2:06.0** · VO: One more text? He changes his mind. He hits Deny, and nothing is sent.
  - Visual (S35, R08): `Also text Mom that I skipped lunch.` The panel appears, the cursor moves to `4. Deny`, Enter.
- **2:06.0–2:08.5** · VO: And Hermes doesn't try again.
  - Visual (S36, R08): Hermes confirms nothing was sent. The phone's Messages thread is unchanged.

### Watch rules
- **2:08.5–2:13.0** · VO: In the library, a watch rule catches "delivered", just once.
  - Visual (S37, R09): library insert, phone face-down. An SMS containing "delivered" arrives (label `RE-CREATED`). A Hermes watch match, or a Telegram alert from a Hermes cron job if it's set up.
- **2:13.0–2:16.0** · VO: Battery under twenty? He gets a heads-up. [NEW]
  - Visual (S38, R11): the battery-below watch alert. **Fallback:** a `debit_over` watch rule, which exists today. Set it low, for example ₹100, and make one real payment above it. Read:
- **2:13.0–2:16.0** · FALLBACK VO: A big debit? He hears about it.

### Find my phone
- **2:16.0–2:19.8** · VO: That night, the phone is gone. Under the bed.
  - Visual (S39, R12): a dark room. Arpit pats the bed and checks his pockets. Camera insert.
- **2:19.8–2:24.0** · VO: One line to Hermes. It rings, speaks, vibrates and flashes.
  - Visual (S40, R12): `I can't find my phone, make it ring for 15 seconds.` Cut to the webcam under the bed: the torch strobes and the phone rings and buzzes.
- **2:24.0–2:25.0** · PAUSE (let the ring play)
  - Visual (S41, R12): his hand pulls the glowing phone out. Flash to ink.

## 6. Under the hood: 2:25–2:45
*Music: duck −8 dB, low-pass. A hush, "inside the machine". The trace is of `phone_status`, the request the latency was measured on.*

- **2:25.0–2:28.0** · VO: Follow one real request: what's my battery?
  - Visual (S42): a freeze-frame of Hermes with `What's my phone battery?`. The camera pulls back through the screen into a dashed-grid diagram.
- **2:28.0–2:31.8** · VO: The approval hook checks it first. A read passes.
  - Visual (S43):
    - Node `pre_tool_call hook`. `phone_status` slides through an open gate.
    - Side branch, greyed: `SMS · CALL · PHOTO · OTP REVEAL → APPROVAL PANEL`.
    - Label: `4 ACTIONS GATED`.
- **2:31.8–2:36.0** · VO: The request is signed with a secret that's never sent.
  - Visual (S44): Geist Mono types out the canonical string, one field per line:
    `GET` / `/v1/status` / `1794274920` / `9f2c1e…(32 hex)` / `e3b0c442…7852b855`
    It feeds into `HMAC-SHA256(secret)`, which outputs `X-PS-Signature`. Label: `SECRET NEVER SENT`.
- **2:36.0–2:39.0** · VO: A one-time nonce stops anyone replaying it.
  - Visual (S45): a copy of the request is fired again and bounces: `nonce reused`. Labels: `±60 S CLOCK WINDOW` · `ONE-TIME NONCE`.
- **2:39.0–2:42.5** · VO: In Termux, a tiny helper asks Android directly.
  - Visual (S46, R13): the real Termux helper log, `[phone-senses] GET /v1/status 200`. An overlay shows `termux-battery-status` → `ANDROID BATTERY API`. Label: `STDLIB PYTHON · NO SHELL`.
- **2:42.5–2:44.6** · VO: Back in under two seconds.
  - Visual (S47, R13): the real timed call on the laptop. Headline: `0.9–2 S ROUND TRIP`. Label: `MEASURED · MOTO G34`.
- **2:44.6–2:45.0** · PAUSE (section turn)

## 7. Impact: 2:45–3:05
*Music: the filter releases at 2:45, which reads as triumph. The bass drops out at ~2:57.*

- **2:45.0–2:49.5** · VO: Before: two hundred notifications, and an agent that couldn't see them.
  - Visual (S48): split screen. Left: the grey notification flood, desaturated. Label: `BEFORE`.
- **2:49.5–2:53.0** · VO: Now: one question, and Hermes knows his whole day.
  - Visual (S49): right half wipes in with one question and one Ultramarine answer card. Label: `AFTER`.
- **2:53.0–2:57.0** · VO: It reads the phone itself, not pictures of the screen.
  - Visual (S50): benefit card 1, `READS ANDROID, NOT PIXELS`. Sub: `Screen agents 18.6 steps · command-line 10.7 · Gu et al. 2026`.
- **2:57.0–3:01.0** · VO: Texts, calls, photos and codes: all four ask him first.
  - Visual (S51): benefit card 2, `4 ACTIONS ASK FIRST`. Sub: `SMS · CALL · PHOTO · OTP REVEAL`.
- **3:01.0–3:05.0** · VO: Codes stay hidden. The plugin talks only to his phone.
  - Visual (S52): benefit card 3, `OTPS HIDDEN BY DEFAULT`. Sub: `0 THIRD-PARTY SERVICES · 0 TELEMETRY`. (The model provider still sees tool results, as with any tool. That's why the VO says "the plugin".)

## 8. Outro: 3:05–3:20
*Music: outro pads, then fade to silence by 3:20.*

- **3:05.0–3:05.4** · PAUSE (section turn)
- **3:05.4–3:08.5** · VO: Phone Senses. Your phone's senses, for Hermes.
  - Visual (S53): the mark rebuilds and the sensing pixel clicks back into place. Chrome wordmark.
- **3:08.5–3:12.5** · VO: And it still asks before it touches anything.
  - Visual (S54): tagline `IT ASKS BEFORE IT ACTS.` in Paper, with "ASKS" in Ultramarine.
- **3:12.5–3:17.0** · VO: Built by Arpit Singh, in Hamirpur. Open source, for Hermes Agent.
  - Visual (S55): end card.
    - `BUILT FOR HERMES AGENT`
    - `phone-senses.pages.dev`
    - `github.com/LSUDOKO/Phone-Senses`
    - `ARPIT SINGH`
    - Small print: `Music: "Space Voyage" by Ekilorea Sound (CC0)` and the sources line `Sources: NPCI · McAfee · MHA/PIB · Gu et al. 2026`.
- **3:17.0–3:19.5** · VO: Try it tonight. Link below.
- **3:19.5–3:20.0** · PAUSE (music resolves)
  - Visual (S56): hold the end card. The sensing pixel blinks once and goes dark at 3:20.

---

## Before recording the VO
1. Run `python demo/film/vo_check.py`. It must report no flags.
   - It reports 454 words, the last line ending at 3:19.5.
   - With `--fallback`, every `[NEW]` line is swapped for its `FALLBACK VO` line. That version must pass too; it reports 449 words.
2. Settle every `[VERIFY]` and `[NEW]` line, using the fallbacks where a feature didn't ship.
3. Re-run the check after any edit.

## TTS notes
- Say "UPI" as letters (U-P-I) and "KYC" as letters (K-Y-C).
- "Hamirpur" is *HUM-eer-poor*.
- "crore" rhymes with "core".
- "Termux" is *TER-mux*.
