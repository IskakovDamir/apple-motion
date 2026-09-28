#!/usr/bin/env python3
"""Quick self-check of a rendered video against the measured Apple ranges (references/fingerprint.json).

  python check_render.py out.mp4 [--fingerprint ../references/fingerprint.json]

Measures: cut rate and shot lengths (frame-difference cut detector), share of pure black / pure
white frames, integrated loudness and true peak (ffmpeg ebur128). Prints each metric next to the
Apple p10-p90 range. Needs numpy, opencv-python and ffmpeg on PATH. The full forensic pipeline
(OCR-based typography timing, springs, beat sync) lives in the repository's scripts/ folder.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

import cv2
import numpy as np


def shots(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    prev, diffs, black, white, n = None, [], 0, 0, 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (160, 90), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.int16)
        black += (g < 16).mean() > 0.7
        white += (g > 240).mean() > 0.7
        if prev is not None:
            diffs.append(float(np.abs(g - prev).mean()))
        prev = g
        n += 1
    d = np.array(diffs)
    thr = max(18.0, float(np.median(d) + 6 * np.median(np.abs(d - np.median(d)))))
    cuts = [i + 1 for i, v in enumerate(d) if v > thr and (i == 0 or d[i - 1] < thr)]
    bounds = [0] + cuts + [n]
    lens = np.diff(bounds)
    return {"fps": fps, "frames": n, "cuts": len(cuts), "cuts_per_10s": len(cuts) / (n / fps) * 10,
            "shot_median": float(np.median(lens)), "black_share": black / n, "white_share": white / n}


def loudness(path):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    t = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", t)
    p = re.search(r"Peak:\s+(-?[\d.inf]+) dBFS", t)
    return (float(i.group(1)) if i else None), (float(p.group(1)) if p else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--fingerprint", default=str(Path(__file__).resolve().parents[1] / "references" / "fingerprint.json"))
    a = ap.parse_args()
    P = json.loads(Path(a.fingerprint).read_text())["pooled"]
    s = shots(a.video)
    lufs, tp = loudness(a.video)
    fs = P.get("frame_share_by_class", {})
    rows = [
        ("cuts per 10 s", s["cuts_per_10s"], P["cuts_per_10s"]),
        ("median shot (frames)", s["shot_median"], P["shot_length_frames"]),
        ("integrated LUFS", lufs, P["lufs"]),
        ("true peak dBTP", tp, P["true_peak_dbtp"]),
    ]
    print(f"{a.video}: {s['frames']} frames @ {s['fps']:.2f} fps, {s['cuts']} cuts")
    print(f"{'metric':24} {'yours':>9}   apple p10..p90   ")
    for name, v, q in rows:
        if v is None or not q:
            print(f"{name:24} {'n/a':>9}")
            continue
        ok = q["p10"] <= v <= q["p90"]
        print(f"{name:24} {v:9.2f}   {q['p10']:>6} .. {q['p90']:<6}  {'ok' if ok else 'OUTSIDE'}")
    print(f"{'pure black share':24} {s['black_share']:9.2f}   apple mean {fs.get('pure black', 0):.2f}")
    print(f"{'pure white share':24} {s['white_share']:9.2f}   apple mean {fs.get('pure white', 0):.2f}")


if __name__ == "__main__":
    main()
