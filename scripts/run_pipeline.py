#!/usr/bin/env python3
"""Idempotent, resumable runner for steps 2b..9 (OCR, step 2a, runs in its own worker).

A step is done when .cache/done/<slug>/<step>.ok exists; delete the marker to force a re-run.
Safe to kill at any moment (the USB drive drops out): the next start resumes at the first
missing marker. Usage: run_pipeline.py [slug ...]
"""
import json
import subprocess
import sys
import time
from pathlib import Path

from common import DATA, ROOT

STEPS = ["s2b_text_events", "s3_text_anim", "s4_motion", "s7_audio", "s5_color_layout", "s6_frames", "s8_sync",
         "s9_summary", "review_sheet"]
ORDER = ["sept26-event-recap", "wwdc23-17things", "wwdc22-day1-recap", "wwdc25-welcome", "wwdc26-sotu-recap",
         "ios26-liquid-glass"]
DONE = ROOT / ".cache" / "done"
LOGS = ROOT / ".cache" / "logs"


def ocr_done(slug):
    p = DATA / slug / "ocr_summary.json"
    if not p.exists():
        return False
    running = subprocess.run(["pgrep", "-f", f"s2a_ocr.py {slug}"], capture_output=True).returncode == 0
    return not running


def marker(slug, step):
    return DONE / slug / f"{step}.ok"


def run(slug, step):
    log = LOGS / f"post_{slug}.log"
    with open(log, "a") as fh:
        fh.write(f"== {time.strftime('%H:%M:%S')} {step}\n")
        fh.flush()
        r = subprocess.run([sys.executable, f"{step}.py", slug], cwd=ROOT / "scripts", stdout=fh, stderr=subprocess.STDOUT)
    if r.returncode == 0:
        marker(slug, step).parent.mkdir(parents=True, exist_ok=True)
        marker(slug, step).write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
        return True
    with open(log, "a") as fh:
        fh.write(f"FAILED {step} rc={r.returncode}\n")
    return False


def main():
    pid = ROOT / ".cache" / "run" / "pipeline.pid"
    pid.parent.mkdir(parents=True, exist_ok=True)
    pid.write_text(str(__import__("os").getpid()))
    slugs = sys.argv[1:] or ORDER
    pending = True
    while pending:
        pending = False
        for slug in slugs:
            if not ocr_done(slug):
                pending = True
                continue
            for step in STEPS:
                if marker(slug, step).exists():
                    continue
                if not run(slug, step):
                    break  # later steps depend on this one; retry on the next start
        if pending:
            time.sleep(60)
    missing = [f"{s}:{st}" for s in slugs for st in STEPS if not marker(s, st).exists()]
    status = {"slugs": slugs, "t": time.strftime("%H:%M:%S"), "missing": missing}
    (DONE / ("ALL.ok" if not missing else "RUN_INCOMPLETE.json")).write_text(json.dumps(status))


if __name__ == "__main__":
    main()
