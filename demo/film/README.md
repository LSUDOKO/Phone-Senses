# The Phone Senses film

The demo film (3:21) and the hackathon cut (under 90 s), built from real recordings.
Planning docs: `BRIEF.md`, `SCRIPT.md`, `SHOTLIST.md`, `RECORDING_PLAN.md`, `RESEARCH.md` (sources for every stat).

## Pipeline

| Step | Script | Output (git-ignored) |
|---|---|---|
| 1. Record real scenes: `hermes chat` in a hidden pty (asciicast) + the phone via scrcpy | `record_scene.py scenes.json <ids>` | `footage/<scene>/` |
| 2. Render the terminal in brand style, redact numbers, amounts and names; sync the phone video | `prep_footage.py` (uses `render_cast.py`) | `studio/public/footage/` |
| 3. Voice-over, one file per line (Kokoro, voice `af_heart`), and the film timeline | `make_vo.py` | `studio/public/audio/vo/`, `studio/src/data/vo.json` |
| 4. Word-timed captions (whisper word times on the script text) | `make_captions.py` | `studio/src/data/captions.json` |
| 5. Cut each walkthrough beat to its voice line, with speed ramps | `cut_beats.py` (edit list: `beats.json`) | `studio/public/beats/`, `studio/src/data/beats.json` |
| 6. Sound effects (synthesised, no samples) | `make_sfx.sh` | `studio/public/audio/sfx/` |
| 7. Compose and render (Remotion) | `cd studio && npx remotion render Film` (also `Cut`, `Social`, `npx remotion still Thumbnail`) | `studio/out/` |
| 8. Loudness master: -14 LUFS, true peak under -1 dBTP | `master.sh <raw.mp4> <final.mp4>` | `studio/out/` |

Compositions in `studio/src/Root.tsx`: `Film` (3:21 master), `Cut` (86 s hackathon cut), `Social` (54 s, 9:16),
`Thumbnail` (1280×720), plus `Walkthrough`, `Sections` and `StyleFrames` for previewing parts.

## Honesty rules in the edit
- Every walkthrough shot is a real Hermes session. Compressed waiting time shows a "▸▸ N× real time" chip.
- Bills and subscriptions ran on the mock phone (no real bills existed): those shots say **DEMO PHONE · SYNTHETIC DATA**.
- Texts that look like they came from someone else were sent to the author's own number: labelled **RE-CREATED**.
- Phone numbers, rupee amounts, merchant and people names, tracking and passport numbers are redacted at render time; phone-screen blur boxes hide OTP codes and other messages.

Music: "Space Voyage" by Ekilorea Sound, CC0 (`audio/LICENSE-music.md`).
