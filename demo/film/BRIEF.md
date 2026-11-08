# Phone Senses: launch film brief

**Format:** 3:20 cinematic launch film, 16:9 at 1920×1080, 30 fps. English female voice-over (VO) with burned-in captions.
**Cut-down:** a ≤90 s version for the hackathon submission and the X post. The hackathon rule is "under 90 s, show the plugin working". The shots for it are tagged `90s` in `SHOTLIST.md`.
**Deliverables in this folder:** `SCRIPT.md` (VO and visuals), `SHOTLIST.md`, `RECORDING_PLAN.md`, `RESEARCH.md` (sources), `audio/music.mp3` with `audio/LICENSE-music.md`, and `vo_check.py` (VO pacing check).

## Logline
Arpit's phone knows his whole day: the bank debit, the scam text, the courier, Mom's missed calls.
His AI agent knew none of it. Phone Senses gives Hermes the phone's senses, and it still asks
before it touches anything.

## Audience
- **Hermes Agent Plugin Hackathon judges.** They score usefulness, reliability, polish and creativity, and favour plugins that do more than a prompt or a skill could.
- **Hermes users browsing the plugin catalog.**
- **Developers on X.**

## The one thing to remember
Your agent can finally see your real phone, through Android's own APIs, with no screen tapping. It
never acts without your OK.

## Three messages, in order
1. **It sees your real phone.** Notifications, SMS, calls, money, parcels and bills, read through Termux:API rather than screenshots.
2. **Safe by design.**
   - Every send, call, photo and OTP reveal opens Hermes's approval panel.
   - OTPs are hidden by default.
   - Requests are signed (HMAC-SHA256, timestamp, one-time nonce), and the secret is never sent.
3. **Real daily use.** It is one student's actual exam-week day, on his actual moto g34, with nothing staged in the UI.

## Arc
**Overwhelm → relief → control and trust.** The music follows the same arc: tension (filtered bed),
lift (filter opens), drive (walkthrough), a breakdown for the scam and the approval stop, the drop on
"Allow once", a hush for "under the hood", then triumph and resolve.

## Protagonist
Arpit Singh is a final-year student in Hamirpur, Himachal Pradesh. It is exam week. He uses a real
moto g34 (Android 15). His bad day:
- Hundreds of notifications (use his real count from Digital Wellbeing).
- Three missed calls from Mom.
- A "KYC blocked" text that almost works.
- No idea where his money went.
- A bill due that he forgot.
- A parcel arriving while he's in the library.
- His phone lost under the bed.

## Tone and voice
- **Voice:** warm, energetic, female. It sounds like a founder telling a friend's story: short sentences, specific nouns, no buzzwords.
- **Avoid:** "revolutionary", "seamless", "AI-powered", "unlock", "supercharge".
- **Pacing:** VO at no more than ~2.5 words per second. Pause at every section turn.
- **Honesty rules:**
  - Real recordings are labelled `REAL PHONE · MOTO G34` in a corner.
  - Any text Arpit sent to his own number is labelled `RE-CREATED · SENT TO MY OWN NUMBER`.
  - Every stat carries its source on screen.

## Look
- **Colours:** Ink `#050507` base. Ultramarine `#1F2BFF` marks the answer or action: the solution, Hermes's reply, the approval. Paper `#F1F1EE` for headlines. Mist `#9AA0B4` for labels and sources. The chrome gradient is for the wordmark only.
- **Type:** Archivo ExtraBold, slightly expanded, for headlines and captions. Geist Mono for tiny uppercase corner labels, sources, the canonical string and code.
- **Texture:** a grainy ultramarine/ink blur field, dashed grid lines, and the block-built phone mark whose top corner breaks off as the "sensing pixel" (`brand/mark.svg`, `brand/banner.svg`).
- **Motion:**
  - Brand easing is `cubic-bezier(0.16, 1, 0.3, 1)`.
  - Use mask and word reveals, match cuts on the sensing pixel, and zoom-throughs from the phone screen into the laptop.
  - Nothing bounces. Holds are long enough to read.
- **Screen footage:**
  - Hermes runs in the terminal TUI (`hermes chat`) at a large font. The phone is mirrored with scrcpy.
  - Show laptop and phone side by side, or the phone floating over the laptop, with ultramarine rim light.

## Mandatories
- Phone Senses wordmark and mark.
- "Built for Hermes Agent". Nous Research is mentioned as Hermes's maker only, with no logo misuse.
- `phone-senses.pages.dev` · `github.com/LSUDOKO/Phone-Senses` · Arpit Singh.
- Music credit: optional (CC0), but nice to include.

## Do not
- Show OTP digits, account numbers, balances, Mom's number, the pairing code or the real HMAC secret.
- Imply the Gu et al. paper tested Phone Senses.
- Caption the McAfee figure as "SMS". It covers text, email and social combined.
- Show `hermes plugins install phone-senses` until the catalog PR is merged. Before that, show the GitHub URL.
- Present features that are still being built as shipped:
  - The features are bills, deliveries, subscriptions and battery watch.
  - The script marks them `[NEW]`.
  - If a feature isn't merged and working on the real phone by recording day, cut its shot. The VO has a fallback line.

## Success
- A judge can repeat the three messages after one viewing.
- The approval panel and the "Allow once" moment read clearly at 1080p on a phone screen.
- Every number is sourced and true.
