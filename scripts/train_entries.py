#!/usr/bin/env python3
"""Train ENTRY_TIME: fit each KineticText entry's spring time scale so that its entry length, measured
by the extraction pipeline, matches Apple's median for the same entry type.

  python train_entries.py demo/out/entry_lab.mp4          (render the EntryLab composition first)

Writes skill/apple-motion/references/entry_time.json and reports/eval/entry-training.md.
Then run build_skill_refs.py to put ENTRY_TIME into tokens.ts.
"""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from common import DATA, ROOT, load_json
import eval_render as ev

SLUG = "render-entry-lab"
LAB = ROOT / "demo" / "src" / "entry_lab.json"
# KineticText entry -> Apple entry style(s) whose measured median is the target
TARGET_STYLE = {"fade": ["fade"], "slideUp": ["slide"], "slideUpMask": ["slide up with mask", "slide down with mask", "slide"],
                "scaleDown": ["scale down from large"], "scaleUp": ["scale up from small"], "blurIn": ["blur in"]}


def apple_targets():
    by = defaultdict(list)
    for f in DATA.glob("*/text_anim.json"):
        if f.parent.name.startswith("render-"):
            continue
        te = {e["id"]: e for e in load_json(f.parent / "text_events.json")["events"]}
        for a in load_json(f)["events"]:
            if te[a["id"]].get("role") == "typography" and a["entry_frames"] >= 2:
                by[a["entry_style"]].append(a["entry_frames"])
    out = {}
    for k, styles in TARGET_STYLE.items():
        vals = sum((by[s] for s in styles), [])
        if len(vals) < 3:  # too few: fall back to the pooled animated-entry median
            vals = sum(by.values(), [])
        out[k] = (float(np.median(vals)), len(vals))
    return out


def main():
    video = Path(sys.argv[1]).resolve()
    lab = json.loads(LAB.read_text())
    truth = ROOT / ".cache" / "tmp" / "entry_lab.truth.json"
    truth.write_text(json.dumps({"fps": 30, "cards": lab["cards"]}))
    log = ROOT / ".cache" / "logs" / f"eval_{SLUG}.log"
    if "--fit-only" not in sys.argv:
        ev.ingest(video, SLUG)
        py = sys.executable
        for args in (["s1_shots.py", SLUG], ["s2a_oracle.py", SLUG, "--truth", str(truth)], ["s2b_text_events.py", SLUG]):
            ev.sh([py, *args], log)
        ev.label_all(SLUG, str(truth))
        ev.sh([py, "relabel.py", SLUG], log)
        ev.sh([py, "s3_text_anim.py", SLUG], log)
    anim = load_json(DATA / SLUG / "text_anim.json")["events"]
    measured = defaultdict(list)  # entry -> [(timeScale, frames)]
    rows = []
    for c in lab["cards"]:
        cand = [a for a in anim if abs(a["appear_frame"] - c["start"]) <= 8]
        if not cand:
            rows.append((c["entry"], c["timeScale"], None))
            continue
        a = min(cand, key=lambda a: abs(a["appear_frame"] - c["start"]))
        measured[c["entry"]].append((c["timeScale"], a["entry_frames"]))
        rows.append((c["entry"], c["timeScale"], a["entry_frames"]))
    targets = apple_targets()
    fit = {}
    for e, pts in measured.items():
        pts = sorted(pts)
        ts = np.array([p[0] for p in pts])
        fr = np.array([p[1] for p in pts], float)
        tgt = targets[e][0]
        # measured frames grow ~linearly with the time scale: least-squares line, solve for the target
        if len(pts) >= 2 and np.ptp(fr) > 0:
            k, b = np.polyfit(ts, fr, 1)
            s = (tgt - b) / k if k > 0 else 1.0
        else:
            s = 1.0
        # few Apple samples (n < 8) -> the target is uncertain: cap the slow-down at 2x
        fit[e] = float(np.clip(s, 1.0, 4.0 if targets[e][1] >= 8 else 2.0))
    (ROOT / "skill" / "apple-motion" / "references" / "entry_time.json").write_text(json.dumps(
        {"time_scale": fit, "targets_frames": {k: v[0] for k, v in targets.items()},
         "targets_n": {k: v[1] for k, v in targets.items()}, "measured": {k: v for k, v in measured.items()}}, indent=1))
    L = ["# Entry training", "", "Targets with fewer than 8 Apple samples are uncertain; their slow-down is capped at 2x.", "", "EntryLab renders every KineticText entry at spring time scales 1 / 1.5 / 2 / 2.75; the extraction",
         "pipeline measures each entry's length (appear -> settled); a line fitted through those points gives the time",
         "scale at which the measured length equals Apple's median for that entry type.", "",
         "| entry | Apple target (median frames, n) | measured at 1 / 1.5 / 2 / 2.75 | trained time scale |", "|---|---|---|---|"]
    for e in TARGET_STYLE:
        m = " / ".join(str(f) for _, f in sorted(measured.get(e, []))) or "missed"
        L.append(f"| {e} | {targets[e][0]:g} ({targets[e][1]}) | {m} | {fit.get(e, 1.0):.2f} |")
    (ROOT / "reports" / "eval" / "entry-training.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
