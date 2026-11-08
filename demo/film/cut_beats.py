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
        z = b.get("zoom")
        info = {"id": b["id"], "scene": b["scene"], "tag": b["tag"], "start": round(start, 3), "duration": length,
                "phone": (dst / "phone.mp4").exists(), "webcam": (dst / "webcam.mp4").exists(),
                "blur": b.get("phone_blur", []),
                "pieces": [{k: round(v, 3) if isinstance(v, float) else v for k, v in p.items()} for p in pieces]}
        marks = {p["mark"]: (p["t0"], p["t0"] + p["out"]) for p in pieces if "mark" in p}
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
