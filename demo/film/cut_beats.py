#!/usr/bin/env python3
"""Cut the walkthrough beats from the prepared clips, speed-ramped to fit the voice-over.

Reads beats.json (edit decision list) + studio/src/data/vo.json (line times) + each scene's
studio/public/footage/<scene>/{term,phone,webcam}.mp4. Writes studio/public/beats/<beat>/*.mp4
(term and phone get the identical time map, so they stay in sync) and studio/src/data/beats.json
with each beat's film start, length, label/zoom/callout times and the zoom target row.

    demo/film/.venv/bin/python demo/film/cut_beats.py            # all beats
    demo/film/.venv/bin/python demo/film/cut_beats.py b07-text-mom
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pyte

HERE = Path(__file__).resolve().parent
FOOT = HERE / "studio" / "public" / "footage"
OUT = HERE / "studio" / "public" / "beats"
DATA = HERE / "studio" / "src" / "data"
FPS = 30
FIX = "setparams=colorspace=bt709:color_trc=bt709:color_primaries=bt709:range=tv"


def plan(segments: list[dict], length: float) -> list[dict]:
    """Resolve segments into [{a, b, out, t0}] pieces; the hold gets whatever time is left."""
    pieces, used = [], 0.0
    for s in segments:
        if "speed" in s:
            a, b = s["speed"]
            out = (b - a) / s["rate"]
        elif "squeeze" in s:
            (a, b), out = s["squeeze"], s["out"]
        elif "freeze" in s:      # hold one frame mid-beat (e.g. under the Hermes welcome screen)
            a, b, out = s["freeze"], None, s["out"]
        else:
            continue
        pieces.append({"a": a, "b": b, "out": out, "t0": used, **{k: s[k] for k in ("mark", "label") if k in s}})
        used += out
    hold = [s for s in segments if "hold" in s]
    rest = length - used
    if rest < 0.4:
        raise SystemExit(f"segments use {used:.2f}s of a {length:.2f}s beat: shorten them")
    if hold:
        pieces.append({"a": hold[0]["hold"], "b": None, "out": rest, "t0": used, "mark": "hold"})
    return pieces


def chain(label: str, pieces: list[dict], fix: str) -> tuple[str, str]:
    """ffmpeg filter graph: split one input into retimed pieces and concat them."""
    parts, names = [f"[{label}]{fix}fps={FPS},split={len(pieces)}" + "".join(f"[s{i}]" for i in range(len(pieces)))], []
    for i, p in enumerate(pieces):
        n = f"p{i}"
        if p["b"] is None:   # freeze frame
            parts.append(f"[s{i}]trim=start={p['a']:.3f}:duration={1 / FPS:.4f},setpts=PTS-STARTPTS,"
                         f"tpad=stop_mode=clone:stop_duration={p['out']:.3f},trim=duration={p['out']:.3f},setpts=PTS-STARTPTS[{n}]")
        else:
            f = p["out"] / (p["b"] - p["a"])
            parts.append(f"[s{i}]trim=start={p['a']:.3f}:end={p['b']:.3f},setpts=(PTS-STARTPTS)*{f:.6f},"
                         f"fps={FPS},tpad=stop_mode=clone:stop_duration=0.1,trim=duration={p['out']:.3f},setpts=PTS-STARTPTS[{n}]")
        names.append(f"[{n}]")
    parts.append("".join(names) + f"concat=n={len(pieces)}:v=1:a=0,format=yuv420p[vout]")
    return ";".join(parts), "[vout]"


def cut(src: Path, dst: Path, pieces: list[dict], fix: str = "") -> None:
    graph, out = chain("0:v", pieces, fix)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-filter_complex", graph, "-map", out, "-an",
                    "-c:v", "libx264", "-crf", "15", "-preset", "medium", "-movflags", "+faststart", str(dst)], check=True)


def find_row(scene: str, clip_t: float, needle: str) -> int | None:
    """Screen row (0-based) showing `needle` at clip time clip_t, from the original cast."""
    log = json.loads((HERE / "footage" / scene / "log.json").read_text())
    start = max(0.0, log["events"].get("rolling", 0) - 1.0)
    lines = (HERE / "footage" / scene / "term.cast").read_text(encoding="utf-8").splitlines()
    h = json.loads(lines[0])
    screen = pyte.Screen(h["width"], h["height"])
    stream = pyte.Stream(screen)
    for line in lines[1:]:
        t, kind, data = json.loads(line)
        if t > clip_t + start:
            break
        if kind == "o":
            stream.feed(data)
    hits = [i for i, row in enumerate(screen.display) if needle.lower() in row.lower()]
    return hits[-1] if hits else None


# Moments with no event in log.json (clip seconds), shown as extra steps
EXTRA_STEPS = {"r12-ring": [(20.6, "The phone rings, speaks and flashes")],
               "r02b-otp": [(48.6, "Revealing the code needs your OK")]}


# When Hermes's answer appears, for beats whose last real-time stretch starts before it
ANSWER_AT = {"r12-ring": 26.5}


def to_out(pieces: list[dict], t: float) -> float | None:
    """Map a clip time to beat time through the retimed pieces."""
    for p in pieces:
        if p["b"] is not None and p["a"] <= t <= p["b"]:
            return p["t0"] + (t - p["a"]) * p["out"] / (p["b"] - p["a"])
    return None


def steps_for(scene: str, pieces: list[dict], allow: bool) -> list[dict]:
    """You ask -> Hermes reads your phone -> (asks first -> verdict) -> answer, from the session's events."""
    ev = json.loads((FOOT / scene / "clip.json").read_text())["events"]
    m = lambda k: to_out(pieces, ev[k]) if k in ev else None   # noqa: E731
    first = next((p["t0"] for p in pieces if p.get("mark") != "banner"), 0.0)
    steps = [{"label": "You ask Hermes", "from": 0.0}]
    steps.append({"label": "Hermes reads your phone", "from": m("sent") or first + 1.0})
    if m("approval_shown") is not None:
        steps.append({"label": "Hermes asks you first", "from": m("approval_shown")})
        steps.append({"label": "Allowed once" if allow else "Denied: nothing sent",
                      "from": (m("approval_answered") or m("approval_shown")) + 0.2})
    for at, label in EXTRA_STEPS.get(scene, []):
        if (w := to_out(pieces, at)) is not None:
            steps.append({"label": label, "from": w})
    sp = next((p for p in pieces if p.get("mark") == "speech"), None)
    if sp:
        steps.append({"label": "The phone warns you out loud", "from": sp["t0"]})
    answer = to_out(pieces, ANSWER_AT[scene]) if scene in ANSWER_AT else (pieces[-2]["t0"] if len(pieces) > 1 else 0.0)
    steps.append({"label": "The answer", "from": max(answer, steps[-1]["from"] + 0.6)})
    return [{**x, "from": round(x["from"], 3)} for x in sorted(steps, key=lambda x: x["from"])]


def beat_lengths(beats: list[dict], vo: dict) -> dict[str, tuple[float, float]]:
    walk = next(s for s in vo["sections"] if s["id"] == "walk")
    line = {l["id"]: l for l in walk["lines"]}
    starts = []
    for b in beats:
        starts.append(line[b["lines"][0]]["start"] if b["lines"] else None)
    out, i = {}, 0
    for i, b in enumerate(beats):
        nxt = next((s for s in starts[i + 1:] if s is not None), walk["end"])
        if starts[i] is None:   # second half of a split slot, laid out by its partner
            continue
        span = nxt - starts[i]
        if "split" in b:
            first = round(span * b["split"] * FPS) / FPS
            out[b["id"]] = (starts[i], first)
            out[beats[i + 1]["id"]] = (starts[i] + first, span - first)
        else:
            out[b["id"]] = (starts[i], span)
    return out


def main(only: list[str]) -> int:
    cfg = json.loads((HERE / "beats.json").read_text())
    vo = json.loads((DATA / "vo.json").read_text())
    slots = beat_lengths(cfg["beats"], vo)
    data_path = DATA / "beats.json"
    result = {b["id"]: b for b in json.loads(data_path.read_text())["beats"]} if data_path.exists() else {}
    for b in cfg["beats"]:
        start, length = slots[b["id"]]
        length = round(length * FPS) / FPS
        pieces = plan(b["segments"], length)
        if only and b["id"] not in only:
            continue
        dst = OUT / b["id"]
        dst.mkdir(parents=True, exist_ok=True)
        src = FOOT / b["scene"]
        cut(src / "term.mp4", dst / "term.mp4", pieces)
        if b.get("phone_scene"):   # phone side comes from another take, played into its key frame
            hold = b["phone_hold"]
            play = min(b.get("phone_play", length * 0.6), length - 0.4)
            cut(FOOT / b["phone_scene"] / "phone.mp4", dst / "phone.mp4",
                [{"a": hold - play, "b": hold, "out": play, "t0": 0}, {"a": hold, "b": None, "out": length - play, "t0": play}])
        elif b.get("phone_off"):   # phone footage doesn't show this moment: terminal only
            (dst / "phone.mp4").unlink(missing_ok=True)
        elif (src / "phone.mp4").exists():
            cut(src / "phone.mp4", dst / "phone.mp4", pieces)
        if b.get("webcam") and (src / "webcam.mp4").exists():
            # webcam_start: webcam second shown at beat time 0 (picked so the torch flashes start as the insert appears)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{b['webcam_start']:.3f}",
                            "-i", str(src / "webcam.mp4"), "-t", "24", "-c:v", "libx264", "-crf", "17", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", str(dst / "webcam.mp4")], check=True)
        speech = next((p for p in pieces if p.get("mark") == "speech"), None)
        if speech and (src / "phone.mp4").exists():
            # the phone's own voice for this stretch, cleaned up and made loud enough to hear over the music
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{speech['a']:.3f}", "-t", f"{speech['b'] - speech['a']:.3f}",
                            "-i", str(src / "phone.mp4"), "-vn", "-af",
                            "highpass=f=120,lowpass=f=9000,acompressor=threshold=-24dB:ratio=3:attack=5:release=120,"
                            "loudnorm=I=-15:TP=-1.5:LRA=7,afade=t=in:d=0.05,afade=t=out:st=" + f"{speech['b'] - speech['a'] - 0.15:.3f}" + ":d=0.15",
                            "-ar", "48000", "-ac", "1", str(dst / "speech.wav")], check=True)
        z = b.get("zoom")
        info = {"id": b["id"], "scene": b["scene"], "tag": b["tag"], "start": round(start, 3), "duration": length,
                "phone": (dst / "phone.mp4").exists(), "webcam": (dst / "webcam.mp4").exists(),
                "blur": b.get("phone_blur", []),
                "speech": ({"at": round(speech["t0"], 3), "dur": round(speech["out"], 3), "text": b.get("speech_text", "")}
                           if speech and (dst / "speech.wav").exists() else None),
                "pieces": [{k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()} for p in pieces]}
        marks = {p["mark"]: (p["t0"], p["t0"] + p["out"]) for p in pieces if "mark" in p}
        info["steps"] = steps_for(b["scene"], pieces, "allow" in b["id"] or "mom" in b["id"])
        if b.get("banner"):   # still of the Hermes welcome screen shown over the first seconds
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "0.1", "-i", str(HERE / "footage" / b["scene"] / "term-hermes.mp4"),
                            "-frames:v", "1", str(dst / "banner.png")], check=True)
            info["banner"] = b["banner"]
        info["labels"] = [{"text": p["label"], "from": round(p["t0"], 3), "to": round(p["t0"] + p["out"], 3)} for p in pieces if "label" in p]
        if z:
            row = find_row(b["scene"], z["at"], z["find"])
            frm = marks.get(z["from"], (length - 1.5, length))[0]
            to = {"allowed_end": marks.get("allowed", (0, length))[1], "panel_end": marks.get("panel", (0, length))[1]}.get(z.get("to"), length)
            info["zoom"] = {"row": row, "rows": z["rows"], "scale": z["scale"], "from": round(frm, 3), "to": round(to, 3),
                            "anchor": z.get("anchor", "center")}
            if row is None:
                print(f"  ! {b['id']}: '{z['find']}' not on screen at {z['at']}")
        if b.get("callout"):
            c = b["callout"]
            info["callout"] = {"text": c["text"], "at": round(marks.get(c["at"], (length - 1.5,))[0] + 0.25, 3)}
        result[b["id"]] = info
        print(f"{b['id']:<20} start {start:6.2f}  len {length:5.2f}  pieces {len(pieces)}  zoom row {info.get('zoom', {}).get('row')}")
    order = [b["id"] for b in cfg["beats"] if b["id"] in result]
    data_path.write_text(json.dumps({"fps": FPS, "beats": [result[i] for i in order]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
