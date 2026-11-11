#!/usr/bin/env python3
"""Build the README / landing-page GIFs from recorded Hermes sessions.

Each GIF replays one real `hermes chat` session (query, tool calls, approval panel, answer) in the
Phone Senses brand: ink background, ultramarine accents, Geist Mono. Text comes from transcripts
captured with Hermes v0.23.0; only personal phone numbers are masked.

    python scripts/make_gifs.py <transcripts-dir> <out-dir>

Needs rsvg-convert and ffmpeg. Set FONTCONFIG_FILE to a config that provides "Geist Mono" and
"Archivo" if they are not installed.
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

W, PAD, LH, FS = 1000, 36, 24, 15
INK, PAPER, BLUE, BLUE_TEXT, MIST, CHROME = "#050507", "#F1F1EE", "#1F2BFF", "#8B93FF", "#9AA0B4", "#E6E6EA"
MAX_LINES = 22
WRAP = 104

NOISE = re.compile(
    r"redirect this turn|longcat-2\.5:free|^\s*[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏\d]*\s*$|Working…|Preparing|Thought for|"
    r"Reading tool details|^\s*─|─{6,}|↑/↓ to select|^Query:|^\$ hermes|^Resume|^Session:|^Duration:|"
    r"^Messages:|^Title:|hermes (--resume|-c)|Goodbye|^\s*>\s|Shutting down|^\s*☤ ❯|tip\)")
MASKS = [(re.compile(r"/home/[^/\s]+"), "~"),
         (re.compile(r"\+?91[\s-]?[6-9]\d{4}[\s-]?\d{5}|(?<!\d)[6-9]\d{9}(?!\d)"), "+91 ••••• •••••"),   # any Indian mobile
         (re.compile(r"\+91\d\*{4}\d{4}"), "+91 ••••• •••••")]


def clean(text: str) -> str:
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", text)
    for rx, repl in MASKS:
        text = rx.sub(repl, text)
    return text.rstrip()


def unglue(line: str) -> list[str]:
    """Hermes's -q renderer sometimes drops newlines between markdown blocks; split them back."""
    line = re.sub(r"(?<=[^\s-])- (?=[A-Z0-9])", "\n- ", line)
    line = re.sub(r"(?<=[a-z0-9%)])(?=[A-Z][a-z]+(?: [a-z]+)?:)", "\n", line)
    line = re.sub(r"(?<=[a-z0-9%,)])(?=[A-Z]{4,}\b)", "\n", line)
    return line.split("\n")


def wrap(line: str) -> list[str]:
    out = []
    while len(line) > WRAP:
        cut = line.rfind(" ", 0, WRAP)
        cut = cut if cut > 40 else WRAP
        out.append(line[:cut])
        line = "  " + line[cut:].lstrip()
    return out + [line]


def extract(path: Path) -> dict:
    """Pull query, tool lines, approval panel, approval result and the final answer from a transcript."""
    raw = [clean(l) for l in path.read_text(errors="replace").splitlines()]
    query = next((re.sub(r'^\$ hermes chat -q "|"$', "", l) for l in raw if l.startswith("$ hermes chat -q")), None)
    if query is None:
        query = next((l[2:] for l in raw if l.startswith("> ")), "")
    tools, box, result, answer, seen = [], [], None, [], set()
    cur: list[str] | None = None
    for l in raw:
        s = l.strip()
        if "╭" in s:
            s = s[s.index("╭"):]
        if s.startswith("╭"):
            cur = []
        if cur is not None:
            cur.append(s)
            if s.startswith("╰"):
                if any("Allow once" in c for c in cur) and not box:
                    box = cur          # the approval panel, not the startup banner
                cur = None
            continue
        m = re.search(r"[⚡📱⏰📚👁️]+\s*(Phone[_ ]\w+[^·]*?|Skill [\w:-]+|Cron create[^·]*?)(?:\s{2,}([\d.]+s))?\s*$", l)
        if m and "──" not in l:
            name = m.group(1).strip()
            tm = re.match(r"Phone_(\w+)(.*)", name)
            if name.startswith("Phone ") and not tm:
                continue                     # display-name duplicate ("Phone Watch Add")
            if tm:
                args = tm.group(2).strip()
                name = f"phone_{tm.group(1)}" + (f"  {args[:40]}" if args else "")
            key = name.split()[0]
            if key not in seen:
                seen.add(key)
                tools.append(f"▸ {name[:60]}" + (f"  {m.group(2)}" if m.group(2) else ""))
        if "Approval:" in l and "→" in l:
            result = s
    # answer: unique clean lines after the last "☤ Hermes" header
    idx = max((i for i, l in enumerate(raw) if l.strip() == "☤ Hermes"), default=None)
    if idx is not None:
        for l in raw[idx + 1:]:
            if re.match(r"\s*(⚙️\s*)?/(exit|new)\b", l) or l.startswith("[<") or re.search(r"☤ ❯ (?!type to redirect)\S", l) or "Redirected" in l:
                break
            if re.search(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]|· \d+[ms].*tok|tok ─", l):
                continue
            if NOISE.search(l) or not l.strip() or l.strip() in answer:
                continue
            if l.startswith(("│", "╭", "╰", "⚠", "❯")):
                continue
            answer.append(l.strip() if not l.startswith("  ") else l)
    return {"query": query, "tools": tools, "box": box, "result": result, "answer": answer}


def svg_frame(lines: list[tuple[str, str]], label: str, title: str, height: int, cursor: bool) -> str:
    rows = []
    y = 116
    for text, kind in lines:
        color = {"query": PAPER, "tool": BLUE_TEXT, "box": CHROME, "boxhi": PAPER, "ok": "#7CF2B1",
                 "deny": "#FF8A8A", "answer": CHROME, "muted": MIST}[kind]
        weight = "600" if kind in ("query", "boxhi") else "400"
        if kind == "boxhi":
            rows.append(f'<rect x="{PAD + 14}" y="{y - 17}" width="300" height="23" fill="{BLUE}" fill-opacity="0.7"/>')
        rows.append(f'<text x="{PAD}" y="{y}" fill="{color}" font-weight="{weight}" xml:space="preserve">'
                    f'{html.escape(text)}</text>')
        y += LH
    if cursor:
        rows.append(f'<rect x="{PAD}" y="{y - 16}" width="9" height="18" fill="{PAPER}"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}">
<defs><radialGradient id="g" cx="0.92" cy="0.05" r="0.75"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.55"/>
<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient></defs>
<rect width="{W}" height="{height}" fill="{INK}"/><rect width="{W}" height="{height}" fill="url(#g)"/>
<g fill="{PAPER}" transform="translate({PAD} 22) scale(0.42)">
<rect x="12" y="4" width="10" height="56"/><rect x="12" y="4" width="22" height="10"/>
<rect x="12" y="50" width="38" height="10"/><rect x="40" y="24" width="10" height="36"/>
<rect x="42" y="4" width="10" height="10"/><rect x="56" y="0" width="6" height="6"/></g>
<text x="{PAD + 36}" y="42" font-family="Archivo" font-weight="800" font-size="18" fill="{PAPER}">Phone Senses</text>
<text x="{PAD + 172}" y="42" font-family="Geist Mono" font-size="12" fill="{MIST}">{html.escape(title)}</text>
<text x="{W - PAD}" y="42" font-family="Geist Mono" font-size="11" fill="{MIST}" text-anchor="end">{html.escape(label)}</text>
<line x1="{PAD}" y1="66" x2="{W - PAD}" y2="66" stroke="{PAPER}" stroke-opacity="0.25" stroke-dasharray="3 5"/>
<g font-family="Geist Mono" font-size="{FS}">{"".join(rows)}</g>
<line x1="{PAD}" y1="{height - 30}" x2="{W - PAD}" y2="{height - 30}" stroke="{PAPER}" stroke-opacity="0.18" stroke-dasharray="3 5"/>
<text x="{PAD}" y="{height - 12}" font-family="Geist Mono" font-size="11" fill="{MIST}">HERMES AGENT 0.23 · PHONE SENSES 0.1.0</text>
</svg>'''


def build(spec: dict, data: dict, out: Path, tmp: Path) -> None:
    final: list[tuple[str, str]] = []
    timeline: list[tuple[list[tuple[str, str]], float, bool]] = []   # (lines, seconds, cursor)
    q = f"❯ {data['query']}"
    for i in range(1, 9):   # typing
        timeline.append(([(q[: max(2, len(q) * i // 8)], "query")], 0.07, True))
    final.append((q, "query"))
    final.append(("", "muted"))
    timeline.append((list(final), 0.6, False))
    pre_tools = [t for t in data["tools"] if not spec.get("approval")] or data["tools"][:-1]
    for t in (data["tools"] if not spec.get("approval") else pre_tools):
        final.append((t, "tool"))
        timeline.append((list(final), 0.45, False))
    if spec.get("approval") and data["box"]:
        box = [b for b in data["box"] if b.strip("│ ").strip() or True]
        box_lines = []
        for b in box:
            inner = b.strip("│╭╮╰╯─ ").strip()
            if b.startswith("╭") or b.startswith("╰"):
                box_lines.append(("┌" + "─" * 64 + "┐" if b.startswith("╭") else "└" + "─" * 64 + "┘", "box"))
            else:
                inner = inner.replace("⚠️", "!").replace("❯ ", "")
                inner = ("  " + inner) if re.match(r"\d\. ", inner) else inner
                box_lines.append(("│ " + inner[:62].ljust(62) + " │", "box"))
        hi = next(i for i, (t, _) in enumerate(box_lines) if "1. Allow once" in t)
        frames_box = [(t, "boxhi" if i == hi else k) for i, (t, k) in enumerate(box_lines)]
        timeline.append((final + frames_box, 1.8, False))
        if spec["approval"] == "deny":
            for step in range(1, 4):
                timeline.append((final + [(t, "boxhi" if i == hi + step else ("box" if k == "boxhi" else k))
                                          for i, (t, k) in enumerate(frames_box)], 0.35, False))
            timeline.append((timeline[-1][0], 0.8, False))
        else:
            timeline.append((final + frames_box, 0.6, False))
        final += [(t, "box") for t, _ in box_lines]
        if data["result"]:
            final.append((data["result"].replace("⚠ ", "! "), "deny" if "denied" in data["result"] else "ok"))
            timeline.append((list(final), 0.8, False))
        for t in data["tools"][-1:] if spec["approval"] == "allow" else []:
            final.append((t, "tool"))
            timeline.append((list(final), 0.5, False))
    final.append(("", "muted"))
    answer = spec.get("answer") or data["answer"]
    answer = [part for a in answer for part in unglue(a)]
    for a in answer:
        for w in wrap(a):
            final.append((w, "answer"))
    # keep the window to MAX_LINES: drop the box body first, then trim the answer
    while len(final) > MAX_LINES + 18:
        final.pop()
    shown = 0
    for i in range(len(final) - len([1 for a in answer for _ in wrap(a)]), len(final) + 1):
        timeline.append((final[:i], 0.12, False))
        shown += 1
    timeline.append((list(final), 3.5, False))
    height = 116 + LH * max(len(f[0]) for f in timeline) + 40
    files = []
    for n, (lines, secs, cursor) in enumerate(timeline):
        svg = tmp / f"f{n:03d}.svg"
        svg.write_text(svg_frame(lines, spec["label"], spec["title"], height, cursor))
        png = tmp / f"f{n:03d}.png"
        subprocess.run(["rsvg-convert", str(svg), "-o", str(png)], check=True)
        files.append((png, secs))
    concat = tmp / "list.txt"
    concat.write_text("".join(f"file '{p}'\nduration {s}\n" for p, s in files) + f"file '{files[-1][0]}'\n")
    palette = tmp / "pal.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-vf", "scale=860:-1:flags=lanczos,palettegen=max_colors=96", str(palette)], check=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-i", str(palette), "-lavfi", "scale=860:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=none",
                    "-loop", "0", str(out)], check=True)


SPECS = [
    # file stem in transcripts dir, gif name, title, label, approval
    ("04-hermes-battery", "status", "what's my phone battery?", "REAL PHONE · MOTO G34", None),
    ("m-important", "digest", "anything important?", "DEMO PHONE · SYNTHETIC DATA", None),
    ("m-spent", "money", "how much did I spend?", "DEMO PHONE · SYNTHETIC DATA", None),
    ("m-received", "upi", "UPI received today", "DEMO PHONE · SYNTHETIC DATA", None),
    ("m-budget", "budget", "budgets", "DEMO PHONE · SYNTHETIC DATA", None),
    ("m-scam", "scam", "scam check", "DEMO PHONE · SYNTHETIC DATA", None),
    ("m-brief", "brief", "morning brief", "DEMO PHONE · SYNTHETIC DATA", None),
    ("m-location", "location", "where is my phone?", "DEMO PHONE · SYNTHETIC DATA", None),
    ("12-find-my-phone", "ring", "find my phone", "REAL PHONE · MOTO G34", None),
    ("15-speak", "speak", "read it aloud", "REAL PHONE · MOTO G34", None),
    ("16-clipboard", "clipboard", "clipboard bridge", "REAL PHONE · MOTO G34", None),
    ("20-slash-phone", "slash", "/phone", "REAL PHONE · MOTO G34", None),
    ("29-watch-match", "watch", "watch rules", "REAL PHONE · MOTO G34", None),
    ("28-sms-approved-sent", "sms-allow", "send SMS · allowed once", "REAL PHONE · MOTO G34", "allow"),
    ("26-sms-denied", "sms-deny", "send SMS · denied", "REAL PHONE · MOTO G34", "deny"),
    ("30-call-approved", "call", "place a call · allowed once", "REAL PHONE · MOTO G34", "allow"),
    ("25-photo-approved", "photo", "take a photo · allowed once", "REAL PHONE · MOTO G34", "allow"),
    ("23-photo-unattended", "unattended", "nobody to approve", "REAL PHONE · MOTO G34", None),
]


def main(argv: list[str]) -> int:
    src, out = Path(argv[1]), Path(argv[2])
    out.mkdir(parents=True, exist_ok=True)
    for stem, name, title, label, approval in SPECS:
        path = src / f"{stem}.txt"
        if not path.exists():
            print(f"skip {stem} (no transcript)")
            continue
        data = extract(path)
        if name == "photo" and not data["answer"]:   # session was cut before the reply; show the real result
            data["answer"] = ["Photo taken with the back camera and saved to Hermes's plugin data folder:",
                              "  ~/.hermes/plugin-data/phone-senses/photos/photo-1794083134-back.jpg"]
        tmp = Path(tempfile.mkdtemp(prefix="ps-gif-"))
        try:
            build({"title": title, "label": label, "approval": approval}, data, out / f"{name}.gif", tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        print(f"{name}.gif  tools={len(data['tools'])} answer_lines={len(data['answer'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
