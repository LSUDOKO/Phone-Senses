#!/usr/bin/env python3
"""VO pacing check for SCRIPT.md.

    python demo/film/vo_check.py            # checks demo/film/SCRIPT.md
    python demo/film/vo_check.py --fallback # as if no [NEW] feature ships: FALLBACK VO lines replace them
    python demo/film/vo_check.py --test     # self-test of the parser

Reads lines like  `- **0:12.8–0:15.6** · VO: His AI agent knew none of it.`
Counts only the VO text (not visuals, timestamps or [TAGS]), prints words per second per line,
flags lines faster than MAX_WPS, overlapping timings, a total outside 430–500 words, or an end
time outside 3:00–3:30. Exit code 1 when anything is flagged.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

LINE = re.compile(r"^- \*\*(\d+):(\d{2}(?:\.\d+)?)–(\d+):(\d{2}(?:\.\d+)?)\*\* · (FALLBACK )?VO: (.+)$")
MAX_WPS = 2.6           # warm, unhurried read; ~2.3 is the target average
WORDS = (430, 500)
END = (180.0, 210.0)


def words(text: str) -> list[str]:
    text = re.sub(r"\[[^\]]*\]", " ", text)                  # drop [NEW] and other tags
    return re.findall(r"[A-Za-z0-9₹][\w'’.\-]*", text)


def parse(md: str, fallback: bool = False) -> list[tuple[float, float, str]]:
    """Main VO lines; with fallback=True, FALLBACK lines replace the [NEW] lines they overlap."""
    main, alt = [], []
    for line in md.splitlines():
        m = LINE.match(line.strip())
        if m:
            row = (int(m[1]) * 60 + float(m[2]), int(m[3]) * 60 + float(m[4]), m[6])
            (alt if m[5] else main).append(row)
    if not fallback:
        return main
    keep = [r for r in main if "[NEW]" not in r[2] or not any(a < r[1] and r[0] < b for a, b, _ in alt)]
    return sorted(keep + alt)


def check(rows: list[tuple[float, float, str]]) -> list[str]:
    problems, last_end, total = [], 0.0, 0
    for a, b, text in rows:
        n, dur = len(words(text)), b - a
        wps = n / dur if dur > 0 else 99
        total += n
        flag = ""
        if wps > MAX_WPS:
            flag = f"  <-- {wps:.2f} wps > {MAX_WPS}"
            problems.append(f"too fast at {a:.1f}s")
        if a < last_end - 1e-6:
            flag += "  <-- overlaps previous line"
            problems.append(f"overlap at {a:.1f}s")
        last_end = b
        print(f"{a:6.1f}-{b:6.1f}s {n:3d}w {wps:4.2f}wps  {text[:70]}{flag}")
    end = max((b for _, b, _ in rows), default=0)
    print(f"\nVO words: {total}  ·  last VO line ends {int(end // 60)}:{end % 60:04.1f}  ·  "
          f"average {total / end:.2f} wps over the film" if end else "\nno VO lines found")
    if not WORDS[0] <= total <= WORDS[1]:
        problems.append(f"total {total} words outside {WORDS}")
    if not END[0] <= end <= END[1]:
        problems.append(f"last VO line ends at {end:.1f}s, outside {END}")
    return problems


def _selftest() -> None:
    md = ("- **0:00.0–0:02.0** · VO: Two hundred notifications.\n"
          "  - Visual: not counted\n"
          "- **0:02.0–0:03.0** · VO: Bills, before they're late. [NEW]\n"
          "- **0:02.0–0:03.0** · FALLBACK VO: Budgets instead.\n")
    rows = parse(md)
    assert [len(words(t)) for _, _, t in rows] == [3, 4], rows
    assert rows[1][:2] == (2.0, 3.0)
    assert [t for _, _, t in parse(md, fallback=True)] == ["Two hundred notifications.", "Budgets instead."]
    assert words("Seven a.m., twenty-five") == ["Seven", "a.m.", "twenty-five"]
    assert check([(0.0, 1.0, "one two three four")]) != []    # 4 wps and too few words get flagged
    print("selftest ok")


if __name__ == "__main__":
    if "--test" in sys.argv:
        _selftest()
        sys.exit(0)
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = Path(paths[0]) if paths else Path(__file__).with_name("SCRIPT.md")
    issues = check(parse(path.read_text(encoding="utf-8"), fallback="--fallback" in sys.argv))
    if issues:
        print("FLAGGED:", "; ".join(issues))
    sys.exit(1 if issues else 0)
