# 01: Hermes Agent Plugin Hackathon: details

Source: the Nous Research announcement on X (@NousResearch) and the Hermes docs.

## Key facts
- **Organiser:** Nous Research
- **Length:** 7 days
- **Deadline:** **Nov 11, 2026, 5:00 PM EST**
  - = **Nov 11, 22:00 UTC**
  - = **Nov 12, 3:30 AM IST**
  - Our own target: **submit by Nov 11, 8 PM IST**.
- **Total prizes:** $20,000 in cash plus extras.
- **Every kind of plugin is eligible.** Accepted entries get listed in the new Hermes Marketplace,
  where every Hermes user can install them.

## Prizes
| Place | Prize |
|---|---|
| 1st | $10,000 + neon sign + merch + $1,000 credits |
| 2nd | $5,000 + neon sign + merch + $1,000 credits |
| 3rd | $2,500 + neon sign + merch + $1,000 credits |
| 4th | $1,500 + merch + $500 credits |
| 5th | $1,000 + merch + $500 credits |
| Runners-up (x5) | merch + $250 credits |

## How judging works
- **Your entry is the plugin itself.**
- Judges score on **usefulness, reliability, polish and creativity**.
- They **favor plugins that do more than a prompt or a skill could**.
- The demo video must be **under 90 seconds** and **show the plugin working**.

How Phone Senses scores on each:
- **Usefulness:** everyone has a phone; notifications, SMS, money and find-my-phone are daily needs.
- **Reliability:** direct Android APIs instead of screen tapping; signed requests; tests; mock phone.
- **Polish:** clean tools, approval prompts, Desktop phone card, good README with screenshots.
- **Creativity:** the phone's senses for an agent; UPI money tracking; scam warnings; fingerprint approval.

## How to enter (3 steps)
1. **Open a pull request** that adds your plugin to the Hermes plugin catalog:
   https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission
   (one file, `plugin-catalog/phone-senses.yaml`, in `NousResearch/hermes-agent`).
2. **Post a demo video on X** (under 90 s) and tag **@NousResearch**.
3. **Submit both links** through the form: https://form.typeform.com/to/FwJLvOln

Notes from the announcement:
- You can submit the form **as soon as your pull request is open**; it does not need to be merged.
- Catalog CI checks run **once a maintainer starts them**; entries are reviewed every few days.
- After submissions close, Nous opens a thread for every entry in the Nous Research Discord.

## Useful links
- Plugin developer guide: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins
- Catalog submission rules: https://hermes-agent.nousresearch.com/docs/developer-guide/plugins/catalog-submission
- Catalog README (entry schema): https://github.com/NousResearch/hermes-agent/blob/main/plugin-catalog/README.md
- Hooks reference: https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks
- Plugin LLM access: https://hermes-agent.nousresearch.com/docs/developer-guide/plugin-llm-access
- Desktop plugin SDK: https://hermes-agent.nousresearch.com/docs/developer-guide/desktop-plugin-sdk
- Marketplace: https://hermes-agent.nousresearch.com/marketplace
- Discord (questions): https://discord.gg/nousresearch

## Competitive landscape (checked Nov 7, 2026, 1,064 catalog entries)
Phone-related plugins that already exist, and how Phone Senses differs:
| Existing plugin | What it does | Difference |
|---|---|---|
| `phone-harness` (4.6k stars) | Drives a phone by screenshots and taps (iPhone Mirroring, adb, cloud phone) | We use direct Android APIs: faster, cheaper, more reliable for data tasks. Complementary. |
| `0bull` | Controls rented cloud iPhones | Not your own phone or data |
| `android-emulator` | Controls an emulator | Not a real phone |
| `call-me` | Rings your iPhone via a hosted service | Single purpose, third-party service |
| `inkbox`, `sendblue`, `artil` | Cloud phone numbers / iMessage services | Paid numbers, mostly US; not your SIM |
| `ntfy-approval`, `pushary` | Approval prompts on your phone | We add fingerprint approval as a stretch only |

No catalog entry mentions Termux or reads your own phone's SMS, notifications, location or sensors.
**Re-check the marketplace before opening the PR** in case someone submits something similar.
