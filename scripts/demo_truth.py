#!/usr/bin/env python3
"""Ground truth of a demo render from demo/src/cards.json (+ tokens.ts entry length).
Usage: demo_truth.py OUT.json   (same beat math as demo/src/Recap.tsx)"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) > 2 and sys.argv[2] == "calibration":
    src = (ROOT / "demo" / "src" / "Calibration.tsx").read_text()
    card = int(re.search(r"CAL_CARD = (\d+)", src).group(1))
    weights = [int(x) for x in re.search(r"CAL_WEIGHTS = \[([^\]]+)\]", src).group(1).split(",")]
    entries = re.findall(r"\{entry: '(\w+)', frames: (\d+)\}", src)
    cards = [{"i": i, "start": i * card, "frames": card, "lines": [f"Weight {w}"], "weight": w, "entry": "cut",
              "entry_frames": 0} for i, w in enumerate(weights)]
    for j, (e, fr) in enumerate(entries):
        i = len(weights) + j
        cards.append({"i": i, "start": i * card, "frames": card, "entry": e, "entry_frames": int(fr),
                      "lines": ["Every word counts"] if e == "perWord" else [f"Entry {e}"],
                      "spring": "tokens SPRING.textIn stretched to entry_frames"})
    Path(sys.argv[1]).write_text(json.dumps({"fps": 30, "cards": cards}, indent=1))
    print(f"calibration truth: {len(cards)} cards")
    sys.exit(0)
data = json.loads((ROOT / "demo" / "src" / "cards.json").read_text())
tokens = (ROOT / "skill" / "apple-motion" / "templates" / "remotion" / "tokens.ts").read_text()
text_in = int(re.search(r"textInFrames:\s*(\d+)", tokens).group(1))
fps, bpm = 30, data["bpm"]
beat = 60 / bpm * fps
cur = data["offsetFrames"]
out = []
for i, c in enumerate(data["cards"]):
    lines = c.get("lines") or ([f"{c['counter']['to']}", c["counter"].get("caption", "")] if c.get("counter") else [])
    entry = "counter" if c.get("counter") else c.get("entry", "scaleDown")
    ef = 0 if entry == "cut" else (4 if entry == "counter" else text_in)
    out.append({"i": i, "start": cur, "frames": round(c["beats"] * beat), "lines": lines, "entry": entry,
                "entry_frames": ef, "transition": c.get("transition", "cut"), "size": c.get("size")})
    cur += round(c["beats"] * beat)
Path(sys.argv[1]).write_text(json.dumps({"bpm": bpm, "fps": fps, "cards": out}, indent=1))
print(f"{len(out)} cards, {cur} frames")
