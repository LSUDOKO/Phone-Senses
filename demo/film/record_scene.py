#!/usr/bin/env python3
"""Record one real scene for the film: the real Hermes session + the real phone screen.

The laptop side is captured at the terminal level, not as screen pixels: `hermes chat` runs in
a hidden pseudo-terminal (fixed size), every byte it prints is saved with its timestamp
(asciicast v2, `term.cast`), and render_cast.py later replays it through a terminal emulator in
the brand colours and fonts. Nothing else on the laptop screen is ever captured.

The phone is recorded with scrcpy (no mirror window). Scripted like a Playwright run:
human-paced typing, the approval panel is detected from the emulated screen, then answered with
"Allow once" (Enter) or "Deny" (three Down arrows + Enter), phone actions run via adb, and every
moment is logged to log.json so the film can zoom and add callouts in sync.

    demo/film/.venv/bin/python demo/film/record_scene.py demo/film/scenes.json brief
    demo/film/.venv/bin/python demo/film/record_scene.py demo/film/scenes.json --all

Queries use $MY_NUMBER and $MOM, filled from the environment so no personal data lives in scenes.json:
    MY_NUMBER=+91XXXXXXXXXX MOM="Mom" demo/film/.venv/bin/python demo/film/record_scene.py ...

Needs: hermes, scrcpy, adb on PATH; phone connected; helper running; adb forward tcp:8765.
Output: demo/film/footage/<scene>/{term.cast, phone.mkv, log.json} (git-ignored).
"""
from __future__ import annotations

import fcntl
import json
import os
import pty
import random
import re
import select
import signal
import string
import struct
import subprocess
import sys
import termios
import time
from pathlib import Path

import pyte

HERE = Path(__file__).resolve().parent
FOOTAGE = HERE / "footage"
COLS, ROWS = 118, 34
HERMES = os.path.expanduser("~/.local/bin/hermes")
BUSY = re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]|Working…|Preparing|Searching tools")

PHONE_ACTIONS = {
    "home": [["adb", "shell", "input", "keyevent", "KEYCODE_HOME"]],
    "shade": [["adb", "shell", "cmd", "statusbar", "expand-notifications"]],
    "collapse": [["adb", "shell", "cmd", "statusbar", "collapse"]],
    "messages": [["adb", "shell", "am", "start", "-a", "android.intent.action.MAIN",
                  "-c", "android.intent.category.APP_MESSAGING"]],
    "recents": [["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW", "-t", "vnd.android.cursor.dir/calls"]],
    "maps": [["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "geo:0,0?q=Hamirpur"]],
    "website": [["adb", "shell", "am", "start", "-a", "android.intent.action.VIEW",
                 "-d", "https://phone-senses.pages.dev"]],
}


class Session:
    """`hermes chat` in a pty, mirrored into a pyte screen and an asciicast file."""

    def __init__(self, cast_path: Path):
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(os.path.expanduser("~"))
            os.environ.update(TERM="xterm-256color", COLUMNS=str(COLS), LINES=str(ROWS), COLORTERM="truecolor")
            os.execvp(HERMES, [HERMES, "chat"])
        self.pid, self.fd = pid, fd
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        self.t0 = time.time()
        self.cast = open(cast_path, "w", encoding="utf-8")
        self.cast.write(json.dumps({"version": 2, "width": COLS, "height": ROWS, "timestamp": int(self.t0),
                                    "env": {"TERM": "xterm-256color"}}) + "\n")

    def pump(self, seconds: float = 0.1) -> bool:
        """Read output for up to `seconds`; return True if anything arrived."""
        end, got = time.time() + seconds, False
        while True:
            left = end - time.time()
            if left <= 0:
                break
            r, _, _ = select.select([self.fd], [], [], left)
            if not r:
                break
            try:
                data = os.read(self.fd, 65536)
            except OSError:
                break
            if not data:
                break
            got = True
            self.stream.feed(data)
            self.cast.write(json.dumps([round(time.time() - self.t0, 4), "o",
                                        data.decode("utf-8", "replace")]) + "\n")
        return got

    def text(self) -> str:
        return "\n".join(self.screen.display)

    def wait_for(self, pattern: str, timeout: float) -> bool:
        rx, end = re.compile(pattern), time.time() + timeout
        while time.time() < end:
            self.pump(0.3)
            if rx.search(self.text()):
                return True
        return False

    def wait_idle(self, quiet: float, timeout: float) -> None:
        """Return once nothing is busy and the screen has not changed for `quiet` seconds."""
        end, since = time.time() + timeout, time.time()
        while time.time() < end:
            changed = self.pump(0.4)
            if changed or BUSY.search(self.text()):
                since = time.time()
            elif time.time() - since >= quiet:
                return

    def send(self, data: str) -> None:
        os.write(self.fd, data.encode())
        self.pump(0.02)

    def type(self, text: str) -> None:
        for ch in text:
            self.send(ch)
            self.pump(random.uniform(0.035, 0.085) + (0.12 if ch in ",.?" else 0))

    def close(self) -> None:
        try:
            self.send("/exit\r")
            self.pump(2.0)
        finally:
            self.cast.close()
            try:
                os.kill(self.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def run_phone(actions: list[str]) -> None:
    for name in actions:
        if name.startswith("sleep:"):
            time.sleep(float(name.split(":", 1)[1]))
        else:
            for argv in PHONE_ACTIONS[name]:
                subprocess.run(argv, capture_output=True)


def preflight() -> None:
    """Fail fast if the phone dropped off USB or the helper stopped (a take would be wasted)."""
    subprocess.run(["adb", "forward", "tcp:8765", "tcp:8765"], capture_output=True)
    import urllib.request
    try:
        with urllib.request.urlopen("http://127.0.0.1:8765/v1/ping", timeout=4) as r:
            if b'"ok": true' in r.read():
                return
    except OSError:
        pass
    raise RuntimeError("phone helper not reachable: check USB, then Termux helper")


def record(scene: dict) -> dict:
    if scene.get("phone", True):
        preflight()
    out = FOOTAGE / scene["id"]
    out.mkdir(parents=True, exist_ok=True)
    events: dict[str, float] = {}
    use_phone = scene.get("phone", True)   # demo-phone scenes: Hermes talks to the mock helper; no phone video
    if use_phone:
        run_phone(scene.get("phone_setup", ["home"]))

    scrcpy = ["scrcpy", "--no-window", "--show-touches", "--stay-awake", "--max-size", "1600",
              "--record", str(out / "phone.mkv")]
    if not scene.get("audio"):
        scrcpy.insert(2, "--no-audio")     # the ring scene keeps the phone's real sound
    phone = subprocess.Popen(scrcpy if use_phone else ["sleep", "100000"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    phone_started = time.time()
    webcam = None
    if scene.get("webcam"):
        webcam = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "v4l2", "-framerate", "30",
                                   "-video_size", "1280x720", "-i", "/dev/video0", "-f", "pulse", "-i", "default",
                                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac",
                                   str(out / "webcam.mp4")], stdin=subprocess.PIPE,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    s = Session(out / "term.cast")
    mark = lambda name: events.__setitem__(name, round(time.time() - s.t0, 3))  # noqa: E731
    final = ""
    try:
        if not s.wait_for(r"Type your message|❯", 90):
            raise RuntimeError("Hermes prompt did not appear")
        if "ENTER/SPACE select" in s.text():
            raise RuntimeError("an unexpected picker is on screen; answer it by hand in `hermes chat` first")
        s.pump(1.0)
        mark("ready")
        s.send("\x0c")            # Ctrl+L: clean screen before the scene starts
        s.pump(1.2)
        mark("rolling")
        run_phone(scene.get("phone_before", []))
        mark("typing")
        s.type(scene["query"])
        s.pump(0.5)
        s.send("\r")
        mark("sent")
        approval = scene.get("approval")
        if approval:
            if not s.wait_for(r"Allow once", 300):
                raise RuntimeError("approval panel never appeared")
            mark("approval_shown")
            s.pump(scene.get("approval_hold", 2.5))
            if approval == "deny":
                for _ in range(3):
                    s.send("\x1b[B")
                    s.pump(0.45)
            s.send("\r")
            mark("approval_answered")
            run_phone(scene.get("phone_after_approval", []))
        s.wait_idle(quiet=6, timeout=360)
        mark("answered")
        run_phone(scene.get("phone_after", []))
        s.pump(scene.get("hold", 3.0))
        mark("end")
        final = s.text()
    finally:
        if webcam is not None:
            try:
                webcam.communicate(b"q", timeout=10)
            except Exception:
                webcam.kill()
        phone.send_signal(signal.SIGINT)
        phone_stopped = time.time()
        try:
            phone.wait(timeout=20)
        except subprocess.TimeoutExpired:
            phone.kill()
        s.close()
    log = {"scene": scene["id"], "query": scene["query"], "cols": COLS, "rows": ROWS,
           "term_t0": s.t0, "phone_started": phone_started, "phone_stopped": phone_stopped,
           "events": events, "final_screen": final}
    (out / "log.json").write_text(json.dumps(log, indent=2, ensure_ascii=False))
    return log


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1
    scenes = json.loads(Path(argv[0]).read_text(encoding="utf-8"))["scenes"]
    for scene in [s for s in scenes if "--all" in argv or s["id"] in argv[1:]]:
        scene["query"] = string.Template(scene["query"]).substitute(os.environ)
        print(f"● {scene['id']}: {scene['query']}", flush=True)
        log = record(scene)
        print(f"  done  events={log['events']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
