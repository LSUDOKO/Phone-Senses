"""Print every distinct line a recorded Hermes session showed (in order), from term.cast."""
import json, re, sys
import pyte
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
h = json.loads(lines[0])
screen = pyte.Screen(h["width"], h["height"])
stream = pyte.Stream(screen)
seen, order = set(), []
noise = re.compile(r"redirect this turn|longcat|^─+|^\s*$|[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]|Type / to browse|Ctrl\+P|Working…")
for l in lines[1:]:
    t, k, d = json.loads(l)
    stream.feed(d)
    for row in screen.display:
        r = row.rstrip()
        if r and r not in seen and not noise.search(r):
            seen.add(r); order.append(f"{t:7.1f}  {r}")
print("\n".join(order))
