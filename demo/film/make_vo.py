#!/usr/bin/env python3
"""Generate the voice-over line by line with Kokoro (local, open-source) and lay out the timeline.

Reads vo_lines.json, writes studio/public/audio/vo/<line>.wav (48 kHz mono, lightly processed)
and studio/src/data/vo.json with each line's start/end in seconds on the film timeline. The film
builds its sections from those times, so the picture locks to the voice.

    demo/film/.venv/bin/python demo/film/make_vo.py            # all lines
    demo/film/.venv/bin/python demo/film/make_vo.py w3 w8      # regenerate some lines only
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent
OUT = HERE / "studio" / "public" / "audio" / "vo"
DATA = HERE / "studio" / "src" / "data"
# Pronunciation fixes for names Kokoro may misread.
SAY = {"Hermes": "Hermes", "Termux": "Term mux", "UPI": "U P I", "SIM": "sim", "Hamirpur": "Hameerpur",
       "Himachal": "Himaachal", "Arpit": "Arpit"}


def spoken(text: str) -> str:
    for word, say in SAY.items():
        text = text.replace(word, say)
    return text


def main(only: list[str]) -> int:
    cfg = json.loads((HERE / "vo_lines.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    k = Kokoro(str(HERE / ".tts" / "kokoro-v1.0.onnx"), str(HERE / ".tts" / "voices-v1.0.bin"))
    t = 0.0
    timeline = {"voice": cfg["voice"], "sections": []}
    for sec in cfg["sections"]:
        s_start = t
        lines = []
        for line in sec["lines"]:
            wav = OUT / f"{line['id']}.wav"
            if not only or line["id"] in only or not wav.exists():
                samples, sr = k.create(spoken(line["text"]), voice=cfg["voice"], speed=cfg["speed"], lang="en-us")
                raw = OUT / f"{line['id']}.raw.wav"
                sf.write(raw, samples, sr)
                # trim edge silence, gentle EQ + compression, 48 kHz
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af",
                                "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                                "silenceremove=start_periods=1:start_threshold=-50dB,areverse,"
                                "highpass=f=80,equalizer=f=3500:t=q:w=1.2:g=2,"
                                "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,aresample=48000",
                                "-ac", "1", str(wav)], check=True)
                raw.unlink()
            dur = sf.info(str(wav)).duration
            lines.append({"id": line["id"], "text": line["text"], "dur": dur, "pause": line.get("pause", 0.3),
                          "hold": line.get("hold", 0.0)})
        # stretch the section to its minimum length by spreading extra silence across its pauses
        # "hold": fixed extra silence after a line (e.g. the phone's own voice plays there); it takes no share
        # of the stretch, so adding one doesn't move the other lines' pauses
        natural = sum(l["dur"] + l["pause"] + l["hold"] for l in lines)
        extra = max(0.0, sec.get("min", 0) - natural)
        weight = sum(l["pause"] for l in lines) or 1.0
        for l in lines:
            l["start"], l["end"] = round(t, 3), round(t + l["dur"], 3)
            t += l["dur"] + l["pause"] + l["hold"] + extra * l["pause"] / weight
            del l["dur"], l["pause"], l["hold"]
        timeline["sections"].append({"id": sec["id"], "title": sec["title"], "start": round(s_start, 3),
                                     "end": round(t, 3), "lines": lines})
    timeline["duration"] = round(t, 3)
    (DATA / "vo.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False))
    for s in timeline["sections"]:
        print(f"{s['id']:<8} {s['start']:6.1f} → {s['end']:6.1f}  ({s['end'] - s['start']:.1f}s, {len(s['lines'])} lines)")
    print(f"total {t:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
