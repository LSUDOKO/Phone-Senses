#!/usr/bin/env python3
"""Word-timed captions for the film from the script + whisper word times.

    whisper-ctranslate2 --model small.en --language en --word_timestamps True --output_format json \
        --output_dir demo/film/.tts/words demo/film/studio/public/audio/vo/*.wav
    demo/film/.venv/bin/python demo/film/make_captions.py

The script text is the source of truth (spelling, names); whisper only supplies the timing.
Writes studio/src/data/captions.json: pages of up to 5 words, each word with film-time start/end.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORDS = HERE / ".tts" / "words"
DATA = HERE / "studio" / "src" / "data"
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())


def line_words(text: str, wid: str, start: float, end: float) -> list[dict]:
    tokens = text.split()
    heard = []
    path = WORDS / f"{wid}.json"
    if path.exists():
        for seg in json.loads(path.read_text())["segments"]:
            heard += [{"w": w["word"].strip(), "s": w["start"], "e": w["end"]} for w in seg.get("words", [])]
    out = [None] * len(tokens)
    m = difflib.SequenceMatcher(a=[norm(t) for t in tokens], b=[norm(h["w"]) for h in heard], autojunk=False)
    for a, b, n in m.get_matching_blocks():
        for k in range(n):
            out[a + k] = (heard[b + k]["s"], heard[b + k]["e"])
    # fill the gaps by interpolating between known neighbours (by character count)
    dur = end - start
    known = [(i, t) for i, t in enumerate(out) if t]
    chars = [len(t) + 1 for t in tokens]
    for i, t in enumerate(out):
        if t:
            continue
        prev = max((k for k in known if k[0] < i), default=None, key=lambda k: k[0])
        nxt = min((k for k in known if k[0] > i), default=None, key=lambda k: k[0])
        lo, li = (prev[1][1], prev[0] + 1) if prev else (0.0, 0)
        hi, hi_i = (nxt[1][0], nxt[0]) if nxt else (dur, len(tokens))
        span = sum(chars[li:hi_i]) or 1
        s = lo + (hi - lo) * sum(chars[li:i]) / span
        out[i] = (s, s + (hi - lo) * chars[i] / span)
    return [{"text": tok, "start": round(start + s, 3), "end": round(min(start + e, end + 0.05), 3)} for tok, (s, e) in zip(tokens, out)]


def pages(words: list[dict], max_words: int = 5) -> list[dict]:
    """Split at sentence ends, then into balanced chunks of at most max_words (no one-word orphans)."""
    sentences, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.?!:]$", w["text"]):
            sentences.append(cur)
            cur = []
    if cur:
        sentences.append(cur)
    out = []
    for sent in sentences:
        n = -(-len(sent) // max_words)
        size = -(-len(sent) // n)
        out += [sent[i:i + size] for i in range(0, len(sent), size)]
    return [{"start": p[0]["start"], "end": p[-1]["end"], "words": p} for p in out]


def main() -> int:
    vo = json.loads((DATA / "vo.json").read_text())
    result = []
    for sec in vo["sections"]:
        for line in sec["lines"]:
            result += pages(line_words(line["text"], line["id"], line["start"], line["end"]))
    (DATA / "captions.json").write_text(json.dumps({"pages": result}, indent=1, ensure_ascii=False))
    print(f"{len(result)} caption pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
