#!/usr/bin/env python3
"""Turn recorded scenes into edit-ready clips for Remotion, on one shared time base.

For each demo/film/footage/<scene>/ with term.cast + phone.mkv + log.json:
- term.mp4: the Hermes session rendered in brand style (render_cast.py), from 1 s before
  "rolling" to "end".
- phone.mp4: the scrcpy recording as constant 30 fps, shifted so it lines up with term.mp4
  frame for frame, padded to the same length.
- clip.json: duration + event times relative to the clip start (typing, sent, approval_shown,
  approval_answered, answered), for zooms, callouts and speed ramps.
Outputs go to demo/film/studio/public/footage/<scene>/ (git-ignored).

    demo/film/.venv/bin/python demo/film/prep_footage.py            # all scenes
    demo/film/.venv/bin/python demo/film/prep_footage.py r02-brief  # one scene
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "footage"
DST = HERE / "studio" / "public" / "footage"
# Hidden in every real-phone scene: full phone numbers, rupee amounts, and names of merchants/people.
PRIVACY = [r"\+?91[ -]?[6-9]\d{4}[ -]?\d{5}", r"(?<!\d)[6-9]\d{9}(?!\d)", r"₹ ?[\d,]+(?:\.\d+)?",
           r"Rs\.? ?[\d,]+(?:\.\d+)?", r"\b[A-Z]{2}\d{9}IN\b", r"\b[A-Z]{1,2}\d{6,8}\b"]
# Names of real people and shops to hide live in footage/private-names.txt (git-ignored, one regex per line).
_names = HERE / "footage" / "private-names.txt"
PRIVACY += [line.strip() for line in (_names.read_text(encoding="utf-8").splitlines() if _names.exists() else []) if line.strip()]
FIX = "setparams=colorspace=bt709:color_trc=bt709:color_primaries=bt709:range=tv"


def prep(scene_dir: Path) -> None:
    log = json.loads((scene_dir / "log.json").read_text())
    ev = log["events"]
    start = max(0.0, ev.get("rolling", 0) - 1.0)
    end = ev["end"]
    out = DST / scene_dir.name
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(HERE / "render_cast.py"), str(scene_dir / "term.cast"), str(out / "term.mp4"),
                    "--from", f"{start:.3f}", "--to", f"{end:.3f}", "--font-size", "26",
                    *[arg for rx in ([] if scene_dir.name.startswith("demo-") else PRIVACY) for arg in ("--redact", rx)]],
                   check=True)
    duration = end - start
    # phone.mkv starts at phone_started; cast time 0 is term_t0. Phone second for cast time t:
    offset = (log["term_t0"] - log["phone_started"]) + start
    if (scene_dir / "phone.mkv").exists():
        # Decode from the start and trim in the filter: scrcpy files have sparse keyframes, so input seeking drops frames.
        vf = (f"{FIX},fps=30,trim=start={max(0.0, offset):.3f},setpts=PTS-STARTPTS,"
              f"tpad=stop_mode=clone:stop_duration={duration:.2f},trim=duration={duration:.3f},format=yuv420p")
        audio = ["-map", "0:a?", "-af", f"atrim=start={max(0.0, offset):.3f},asetpts=PTS-STARTPTS,apad,atrim=duration={duration:.3f}",
                 "-c:a", "aac", "-b:a", "192k"]
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(scene_dir / "phone.mkv"),
                        "-map", "0:v:0", "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "medium", *audio,
                        "-movflags", "+faststart", str(out / "phone.mp4")], check=True)
    if (scene_dir / "webcam.mp4").exists():
        subprocess.run(["cp", str(scene_dir / "webcam.mp4"), str(out / "webcam.mp4")], check=True)
    clip = {"scene": scene_dir.name, "query": log["query"], "duration": round(duration, 3),
            "events": {k: round(v - start, 3) for k, v in ev.items() if v >= start}}
    (out / "clip.json").write_text(json.dumps(clip, indent=2, ensure_ascii=False))
    print(f"{scene_dir.name}: {duration:.1f}s  events={clip['events']}")


def main(argv: list[str]) -> int:
    dirs = [SRC / a for a in argv] if argv else sorted(p for p in SRC.iterdir() if (p / "log.json").exists())
    for d in dirs:
        if d.name.startswith("test-"):
            continue
        prep(d)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
