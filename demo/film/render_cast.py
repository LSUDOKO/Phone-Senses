#!/usr/bin/env python3
"""Render a recorded Hermes session (asciicast v2) into a brand-styled video.

Replays the exact bytes `hermes chat` printed through a terminal emulator (pyte), and draws every
frame with Pillow in the Phone Senses look: Ink background, Paper text, Geist Mono, Hermes's own
colours kept for its UI. Only frames where the screen changed are drawn; ffmpeg holds the rest.

    demo/film/.venv/bin/python demo/film/render_cast.py footage/brief/term.cast footage/brief/term.mp4
    options: --fps 30  --font-size 24  --from 5.5 --to 40  (seconds in the cast)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import pyte
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT_CHAIN = [HERE / ".fonts" / "GeistMono.ttf", Path("/usr/share/fonts/noto/NotoSansMono-Regular.ttf"),
              Path("/usr/share/fonts/noto/NotoSansSymbols2-Regular.ttf"),
              Path("/usr/share/fonts/noto/NotoSansSymbols-Regular.ttf")]
EMOJI_FONT = Path("/usr/share/fonts/noto/NotoColorEmoji.ttf")

INK, PAPER, TEXT = (5, 5, 7), (241, 241, 238), (230, 230, 234)
NAMED = {
    "black": (91, 95, 110), "red": (255, 138, 138), "green": (124, 242, 177), "brown": (242, 193, 78),
    "yellow": (242, 193, 78), "blue": (139, 147, 255), "magenta": (195, 139, 255), "cyan": (127, 215, 255),
    "white": (230, 230, 234), "brightblack": (110, 115, 132), "brightred": (255, 160, 160),
    "brightgreen": (150, 247, 196), "brightbrown": (255, 214, 110), "brightyellow": (255, 214, 110),
    "brightblue": (170, 177, 255), "brightmagenta": (214, 170, 255), "brightcyan": (160, 228, 255),
    "brightwhite": (241, 241, 238),
}


def color(value: str, default: tuple) -> tuple:
    if value == "default":
        return default
    if value in NAMED:
        return NAMED[value]
    if len(value) == 6:
        try:
            return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default


class Glyphs:
    def __init__(self, size: int):
        self.size = size
        self.fonts, self.cmaps = [], []
        for path in FONT_CHAIN:
            if not path.exists():
                continue
            self.fonts.append(ImageFont.truetype(str(path), size))
            self.cmaps.append(set(TTFont(str(path)).getBestCmap()))
        self.bold = ImageFont.truetype(str(FONT_CHAIN[0]), size)
        try:
            self.bold.set_variation_by_axes([640])
        except Exception:
            pass
        self.cell_w = round(self.fonts[0].getlength("M"))
        self.cell_h = round(size * 1.42)
        self.emoji_cmap = set(TTFont(str(EMOJI_FONT)).getBestCmap()) if EMOJI_FONT.exists() else set()

    def font_for(self, ch: str, bold: bool) -> ImageFont.FreeTypeFont | None:
        cp = ord(ch[0])
        for i, cmap in enumerate(self.cmaps):
            if cp in cmap:
                return self.bold if (bold and i == 0) else self.fonts[i]
        return None

    @lru_cache(maxsize=256)
    def emoji(self, ch: str) -> Image.Image | None:
        if ord(ch[0]) not in self.emoji_cmap:
            return None
        f = ImageFont.truetype(str(EMOJI_FONT), 109)
        img = Image.new("RGBA", (136, 128), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((0, 0), ch, font=f, embedded_color=True)
        img = img.crop(img.getbbox() or (0, 0, 136, 128))
        target = round(self.cell_h * 0.78)
        return img.resize((max(1, round(img.width * target / img.height)), target), Image.LANCZOS)


REDACT: list[re.Pattern] = []


def redacted_cells(row, columns: int) -> set[int]:
    """Columns covered by any privacy pattern on this row (phone numbers, amounts, names)."""
    if not REDACT:
        return set()
    cols, text = [], []
    for x in range(columns):
        data = row[x].data
        if data:
            cols.append(x)
            text.append(data[0])
    s = "".join(text)
    hit: set[int] = set()
    for rx in REDACT:
        for m in rx.finditer(s):
            for i in range(m.start(), m.end()):
                hit.add(cols[i])
    return hit


def draw(screen: pyte.Screen, g: Glyphs, pad: int) -> Image.Image:
    w, h = screen.columns * g.cell_w + pad * 2, screen.lines * g.cell_h + pad * 2
    img = Image.new("RGB", (w, h), INK)
    d = ImageDraw.Draw(img)
    baseline = round(g.cell_h * 0.76)
    for y in range(screen.lines):
        row = screen.buffer[y]
        py = pad + y * g.cell_h
        hidden = redacted_cells(row, screen.columns)
        runs, start = [], None
        for x in range(screen.columns + 1):
            if x in hidden and start is None:
                start = x
            elif x not in hidden and start is not None:
                runs.append((start, x))
                start = None
        for a, b in runs:   # soft privacy block, drawn instead of the text
            d.rounded_rectangle([pad + a * g.cell_w - 2, py + 6, pad + b * g.cell_w + 2, py + g.cell_h - 6],
                                radius=8, fill=(46, 49, 72))
        x = 0
        while x < screen.columns:
            if x in hidden:
                x += 1
                continue
            ch = row[x]
            fg, bg = color(ch.fg, TEXT), color(ch.bg, INK)
            if ch.reverse:
                fg, bg = bg if bg != INK else TEXT, fg
            px = pad + x * g.cell_w
            if bg != INK:
                d.rectangle([px, py, px + g.cell_w, py + g.cell_h], fill=bg)
            data = ch.data
            if data and data != " ":
                if ord(data[0]) >= 0x1F000 or data[0] in "⚡⏱⏲⚙":
                    em = g.emoji(data)
                    if em is not None:
                        img.paste(em, (px, py + (g.cell_h - em.height) // 2), em)
                        x += 1
                        continue
                f = g.font_for(data, ch.bold)
                if f is not None:
                    if data[0] in "─━═│║╭╮╰╯┌┐└┘├┤┬┴┼╔╗╚╝" :   # box drawing: stretch to the cell so lines join
                        d.text((px, py + baseline), data, font=f, fill=fg, anchor="ls")
                    else:
                        d.text((px, py + baseline), data, font=f, fill=fg, anchor="ls")
            x += 1
    if not screen.cursor.hidden:
        cx, cy = pad + screen.cursor.x * g.cell_w, pad + screen.cursor.y * g.cell_h
        d.rectangle([cx, cy + 3, cx + g.cell_w - 1, cy + g.cell_h - 3], fill=(31, 43, 255))
    return img


def render(cast: Path, out: Path, fps: int, font_size: int, start: float, end: float | None) -> None:
    lines = cast.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    events = [json.loads(l) for l in lines[1:] if l.strip()]
    events = [(t, data) for t, kind, data in events if kind == "o"]
    screen = pyte.Screen(header["width"], header["height"])
    stream = pyte.Stream(screen)
    g = Glyphs(font_size)
    pad = 28
    end = end if end is not None else (events[-1][0] + 1.0 if events else 1.0)
    size = draw(screen, g, pad).size
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-", "-vf", "format=yuv420p",
                            "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-movflags", "+faststart", str(out)],
                           stdin=subprocess.PIPE)
    i, last_sig, frame_bytes, drawn, t = 0, None, b"", 0, 0.0
    step = 1.0 / fps
    n_frames = 0
    while t <= end + 1e-9:
        changed = False
        while i < len(events) and events[i][0] <= t:
            stream.feed(events[i][1])
            i += 1
            changed = True
        if t >= start:
            if changed or not frame_bytes:
                sig = (tuple(screen.display), screen.cursor.x, screen.cursor.y, screen.cursor.hidden)
                if sig != last_sig:
                    frame_bytes = draw(screen, g, pad).tobytes()
                    last_sig = sig
                    drawn += 1
            enc.stdin.write(frame_bytes)   # every frame at a constant rate: exact timing
            n_frames += 1
        t += step
    enc.stdin.close()
    enc.wait()
    print(f"{out}  frames={n_frames} drawn={drawn}  duration={n_frames / fps:.1f}s  size={size}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cast", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--font-size", type=int, default=24)
    ap.add_argument("--from", dest="start", type=float, default=0.0)
    ap.add_argument("--to", dest="end", type=float, default=None)
    ap.add_argument("--redact", action="append", default=[], help="regex to hide (repeatable)")
    a = ap.parse_args()
    REDACT.extend(re.compile(r) for r in a.redact)
    render(a.cast, a.out, a.fps, a.font_size, a.start, a.end)


if __name__ == "__main__":
    main()
