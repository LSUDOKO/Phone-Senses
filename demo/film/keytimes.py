"""Clip-relative times: when each answer line first appears (after '☤ Hermes'), plus tool lines and approvals."""
import json, re, sys
import pyte
SPIN = re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]|redirect this turn|longcat|^─|Type / to|Ctrl\+P")
for scene in sys.argv[1:]:
    log = json.load(open(f"footage/{scene}/log.json"))
    start = max(0.0, log["events"]["rolling"] - 1.0)
    lines = open(f"footage/{scene}/term.cast", encoding="utf-8").read().splitlines()
    h = json.loads(lines[0]); screen = pyte.Screen(h["width"], h["height"]); st = pyte.Stream(screen)
    seen, out, on = set(), [], False
    for l in lines[1:]:
        t, k, d = json.loads(l); st.feed(d)
        if t - start > log["events"]["end"] - start: break
        for row in screen.display:
            r = row.strip()
            if not r or r in seen or SPIN.search(r): continue
            seen.add(r)
            if r.startswith("☤ Hermes"): on = True
            if on or re.search(r"^(📱|⚡ )|Approval:|Allow once", r):
                out.append(f"{t-start:7.2f}  {r[:100]}")
    ev = {k: round(v-start,2) for k,v in log["events"].items() if k!='ready'}
    print(f"### {scene}  {ev}"); print("\n".join(out[:16]))
