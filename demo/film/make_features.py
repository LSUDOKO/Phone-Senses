#!/usr/bin/env python3
"""Side-by-side feature clips for the README and the website: the real Hermes session on the left
(Hermes's own colours, starting on its gold banner) and the real phone on the right, step by step.

    demo/film/.venv/bin/python demo/film/make_features.py render     # Hermes-coloured terminal renders (slow, once)
    demo/film/.venv/bin/python demo/film/make_features.py cut        # per-feature clips + src/data/features.json
    cd demo/film/studio && npx remotion render Feature --props '{"id":"brief"}' ...   (see export())
    demo/film/.venv/bin/python demo/film/make_features.py export     # render all, then GIF + MP4 into site/media/

Reuses the walkthrough edit (beats.json, cut_beats.py): same timing, same redaction, same phone blur.
"""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from cut_beats import FPS, cut, plan
from prep_footage import PRIVACY

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FOOT = HERE / "footage"
STUDIO = HERE / "studio"
OUT = STUDIO / "public" / "features"
DATA = STUDIO / "src" / "data"
MEDIA = ROOT / "site" / "media"
# Moments that have no event in log.json (clip seconds, from keytimes.py), shown as extra steps
EXTRA_STEPS = {"ring": [(20.6, "The phone rings, speaks and flashes")],
               "otp": [(48.6, "Revealing the code needs your OK")]}
BANNER = 1.6        # seconds on Hermes's welcome screen before the question
MIN_HOLD = 3.5      # time to read the answer at the end

# feature id -> (beat id, title, what you ask)
FEATURES = {
    "brief": ("b01-brief", "Morning brief", "Good morning, give me my phone brief."),
    "otp": ("b02-otp", "OTP codes stay hidden", "Read me my latest SMS that has a code in it."),
    "money": ("b03-money", "Where did my money go?", "Where did my money go this week?"),
    "upi": ("b04-upi", "UPI received", "How much did I receive by UPI this week?"),
    "bills": ("b05a-bills", "Bills due", "What bills are due soon?"),
    "subscriptions": ("b05b-subscriptions", "Subscriptions", "What subscriptions am I paying for?"),
    "scam": ("b06-scam", "Is this SMS a scam?", "I got a weird SMS about my KYC. Is it a scam?"),
    "sms-allow": ("b07-text-mom", "Send an SMS: allow once", "Text Mom: I'll call you after the exam."),
    "sms-deny": ("b08-deny", "Send an SMS: deny", "Also text Mom that I skipped lunch."),
    "tripwire": ("b08b-tripwire", "Scam tripwire", "A caller from my bank asked me to install AnyDesk."),
    "watch": ("b09-watch", "Watch rules", "Any watch alerts on my phone?"),
    "battery": ("b10-battery", "Battery watch", "Tell me when my battery drops below 20%."),
    "ring": ("b11-ring", "Find my phone", "I can't find my phone, make it ring."),
}


def beats() -> dict:
    cfg = {b["id"]: b for b in json.loads((HERE / "beats.json").read_text())["beats"]}
    data = {b["id"]: b for b in json.loads((DATA / "beats.json").read_text())["beats"]}
    return {k: (cfg[k], data[k]) for k in cfg if k in data}


def shift(scene: str) -> tuple[float, float]:
    """(render start in cast time, offset to add to old clip times)."""
    ev = json.loads((FOOT / scene / "log.json").read_text())["events"]
    start = max(0.0, ev.get("ready", ev.get("rolling", 1.0)) - 0.25)
    old = max(0.0, ev.get("rolling", 0) - 1.0)
    return start, old - start


def render_one(scene: str) -> str:
    start, _ = shift(scene)
    end = json.loads((FOOT / scene / "log.json").read_text())["events"]["end"]
    out = FOOT / scene / "term-hermes.mp4"
    redact = [] if scene.startswith("demo-") else [a for rx in PRIVACY for a in ("--redact", rx)]
    subprocess.run([sys.executable, str(HERE / "render_cast.py"), str(FOOT / scene / "term.cast"), str(out),
                    "--from", f"{start:.3f}", "--to", f"{end:.3f}", "--font-size", "26", "--fps", "15",
                    "--theme", "hermes", *redact], check=True, capture_output=True)
    return scene


def render_all() -> None:
    scenes = sorted({b[0]["scene"] for k, b in beats().items() if k in {v[0] for v in FEATURES.values()}})
    with ThreadPoolExecutor(5) as pool:
        for scene in pool.map(render_one, scenes):
            print("rendered", scene, flush=True)


def to_out(pieces: list[dict], t: float) -> float | None:
    """Map a source clip time to output time through the retimed pieces."""
    for p in pieces:
        if p["b"] is None:
            continue
        if p["a"] <= t <= p["b"]:
            return p["t0"] + (t - p["a"]) * p["out"] / (p["b"] - p["a"])
    return None


def cut_one(fid: str, cfg: dict, data: dict, title: str, ask: str) -> dict:
    scene = cfg["scene"]
    _, delta = shift(scene)
    old = plan(cfg["segments"], data["duration"])
    hold = max(old[-1]["out"], MIN_HOLD)
    length = sum(p["out"] for p in old[:-1]) + hold
    pieces = [{"a": 0.1, "b": None, "out": BANNER, "t0": 0.0, "mark": "banner"}]   # Hermes's welcome screen
    t = BANNER
    for p in old:
        out = hold if p["b"] is None else p["out"]
        pieces.append({**p, "a": p["a"] + delta, "b": None if p["b"] is None else p["b"] + delta, "out": out, "t0": t})
        t += out
    dst = OUT / fid
    dst.mkdir(parents=True, exist_ok=True)
    cut(FOOT / scene / "term-hermes.mp4", dst / "term.mp4", pieces)
    total = BANNER + length
    phone = STUDIO / "public" / "beats" / data["id"] / "phone.mp4"
    if phone.exists():   # the walkthrough's phone side, already synced and trimmed: freeze it around the edges
        cut(phone, dst / "phone.mp4", [
            {"a": 0.0, "b": None, "out": BANNER, "t0": 0.0},
            {"a": 0.0, "b": data["duration"], "out": data["duration"], "t0": BANNER},
            {"a": data["duration"] - 0.05, "b": None, "out": total - BANNER - data["duration"], "t0": BANNER + data["duration"]}])
    elif (dst / "phone.mp4").exists():
        (dst / "phone.mp4").unlink()

    # Steps, from the session's own events mapped onto the edited timeline
    ev = json.loads((STUDIO / "public" / "footage" / scene / "clip.json").read_text())["events"]
    m = lambda key: to_out(pieces[1:], ev[key] + delta) if key in ev else None   # noqa: E731
    answer_at = pieces[-2]["t0"]
    steps = [{"label": "You ask Hermes", "from": BANNER - 0.3}]
    sent = m("sent") or pieces[2]["t0"]
    steps.append({"label": "Hermes reads your phone", "from": sent})
    if m("approval_shown") is not None:
        steps.append({"label": "Hermes asks you first", "from": m("approval_shown")})
        verdict = "Allowed once: sent from your SIM" if "allow" in fid else "Denied: nothing is sent"
        steps.append({"label": verdict, "from": (m("approval_answered") or m("approval_shown")) + 0.2})
    for at, label in EXTRA_STEPS.get(fid, []):
        when = to_out(pieces[1:], at + delta)
        if when is not None:
            steps.append({"label": label, "from": when})
    speech = next((p for p in pieces if p.get("mark") == "speech"), None)
    if speech:
        steps.append({"label": "The phone warns you out loud", "from": speech["t0"]})
    steps.append({"label": "The answer", "from": max(answer_at, steps[-1]["from"] + 0.8)})
    blur = [[*b[:4], b[4] + BANNER if len(b) > 4 else BANNER, (b[5] + BANNER) if len(b) > 5 else 1e6]
            for b in data.get("blur", [])]
    return {"id": fid, "title": title, "ask": ask, "tag": data["tag"], "duration": round(total, 3),
            "phone": (dst / "phone.mp4").exists(), "blur": blur, "steps": steps,
            "speech": ({"at": round(speech["t0"], 3), "dur": round(speech["out"], 3), "text": (data.get("speech") or {}).get("text", "")}
                       if speech else None),
            "zoom": {"row": (data.get("zoom") or {}).get("row"), "rows": (data.get("zoom") or {}).get("rows", 6),
                     "from": round(steps[-1]["from"] + 0.4, 3)},
            "real": not data["tag"].startswith("DEMO")}


def cut_all() -> None:
    bs = beats()
    out = []
    for fid, (bid, title, ask) in FEATURES.items():
        cfg, data = bs[bid]
        if not (FOOT / cfg["scene"] / "term-hermes.mp4").exists():
            print("skip (not rendered)", fid)
            continue
        out.append(cut_one(fid, cfg, data, title, ask))
        print(f"{fid:<14} {out[-1]['duration']:5.1f}s  steps={[s['label'][:12] for s in out[-1]['steps']]}")
    (DATA / "features.json").write_text(json.dumps({"features": out}, indent=2, ensure_ascii=False))


def export(only: list[str]) -> None:
    feats = json.loads((DATA / "features.json").read_text())["features"]
    tmp = STUDIO / "out" / "features"
    tmp.mkdir(parents=True, exist_ok=True)
    for f in feats:
        if only and f["id"] not in only:
            continue
        mp4 = tmp / f"{f['id']}.mp4"
        subprocess.run(["npx", "remotion", "render", "Feature", str(mp4), f"--props={json.dumps({'id': f['id']})}",
                        "--codec=h264", "--crf=20", "--log=error"], cwd=STUDIO, check=True)
        web = MEDIA / f"feature-{f['id']}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp4), "-an", "-vf", "scale=1280:-2",
                        "-c:v", "libx264", "-crf", "26", "-preset", "slow", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(web)], check=True)
        gif = MEDIA / f"feature-{f['id']}.gif"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(mp4), "-vf",
                        "fps=10,scale=1280:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];"
                        "[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle", str(gif)], check=True)
        print(f"{f['id']:<14} gif {gif.stat().st_size / 1e6:.1f} MB  mp4 {web.stat().st_size / 1e6:.1f} MB", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "render":
        render_all()
    elif cmd == "cut":
        cut_all()
    elif cmd == "export":
        export(sys.argv[2:])
    else:
        print(__doc__)
