# 02: The idea: Phone Senses

> **One line:** Phone Senses gives Hermes the senses of your own Android phone (notifications,
> SMS, calls, location, battery, camera) through direct Android APIs, so it can understand your day
> and act on your phone safely, without tapping the screen.

Tagline for the demo: *"phone-harness gives Hermes hands on your phone. Phone Senses gives it the
phone's senses."*

## The problems it solves

1. **Your AI agent cannot see your phone.**
   Messages, bank alerts, deliveries, missed calls, location and OTPs all arrive on the phone.
   Hermes runs on the laptop and knows none of it, so you keep checking the phone and retyping.

2. **Existing phone control is slow and fragile.**
   Screen-driving agents take a screenshot for every step, use many tokens, break when an app's
   layout changes, and need USB/adb or a Mac. "Read my latest SMS" should be one call, not 15 taps.

3. **Paid phone services are not your number.**
   Other plugins send SMS through paid cloud numbers (mostly US). People expect messages from
   *your* number. In India, SMS from your own SIM is usually included in your plan.

4. **Money tracking is manual although the data already exists.**
   Every UPI payment and bank debit sends an SMS. People still track expenses by hand, or not at all.

5. **Important alerts drown in notification noise.**
   "Out for delivery" or "Rs 8,000 debited" gets lost among hundreds of notifications.

6. **Approvals need you at the computer.**
   Your phone is always with you; your laptop isn't. (Stretch: approve with your fingerprint.)

## The solution
A Hermes plugin plus a tiny helper that runs on the phone inside **Termux** (a free, open-source
Linux environment for Android) using **Termux:API**, which exposes Android functions such as SMS,
notifications, location, battery, camera, torch, vibration and text-to-speech as command-line tools.

- The **helper** turns those commands into a small, signed JSON API on your private network
  (home Wi-Fi or Tailscale).
- The **plugin** gives Hermes tools like `phone_notifications`, `phone_sms_send` and
  `phone_money_summary`, enforces approvals for risky actions, masks OTPs, and adds smart features
  (money tracker, scam warnings, watch rules, morning brief).

## Research backing
**"Beyond the GUI Paradigm: Do Mobile Agents Need the Phone Screen?"** (Gu et al., arXiv 2606.19388, June 2026):
- Command-line (non-screen) mobile agents scored **60.7–68.9%** on tasks suited to commands, versus
  **22.2–33.3%** for screen-based agents.
- They needed about **10.7 steps vs 18.6**.
- Screen-based agents topped out at **11%** on cross-app workflows.
- On AndroidWorld, a command-line agent (Claude Code with Opus 4.7) scored **71.8%**, ahead of the
  GUI baselines tested.
- Recommendation: command-line access deserves "first-class consideration" alongside GUI agents, and
  hybrid approaches are promising.

**Use in the pitch:** "Research shows agents do data tasks on phones far better through APIs than
through the screen. Phone Senses is that API layer for Hermes, and it pairs with phone-harness for
the visual tasks."

Link: https://www.alphaxiv.org/abs/2606.19388

## Why it is unique
I checked all 1,064 catalog entries (Nov 7, 2026). Nothing reads your own phone's notifications,
SMS, call log, location or sensors, and no entry mentions Termux. See `01-hackathon.md` for the
nearest neighbours and how we differ. The name `phone-senses` was free.

## Who it is for
Students, working professionals, small shop owners (UPI sales), developers, travellers, anyone
with an Android phone. India is a strong story (UPI SMS, own-SIM SMS, scam SMS problem), but every
feature works worldwide.

## Limits (state these honestly in the README)
- Android only (Termux does not exist on iPhone).
- Needs Termux + Termux:API from **F-Droid** and several Android permissions.
- Some phone brands kill background apps; users must disable battery optimisation for Termux.
- Bank SMS formats vary; the money parser covers common formats and improves over time.
