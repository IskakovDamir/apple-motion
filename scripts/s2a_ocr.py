#!/usr/bin/env python3
"""STEP 2a: raw OCR -> data/<slug>/ocr_raw.jsonl (one line per frame, resumable).

Pass A: every 3rd frame of the whole video -> decides which shots are text-bearing
        (a detection >= MIN_EVENT_H of frame height with conf >= 0.5).
Pass B: every remaining frame of the text-bearing shots.
So every frame of every text-bearing shot gets OCR'd. A frame whose 320x180 gray image is
identical (mean abs diff < 0.6, max < 25) to the last OCR'd frame reuses that result
(logged as "reused": true) - holds on flat backgrounds are pixel-identical.
EasyOCR runs on 1280x720 (MPS). Boxes are stored in 1920x1080 source coordinates.
"""
import json
import os
import sys
import time

import cv2
import numpy as np

from common import DATA, iter_frames, meta, read_shots

MIN_EVENT_H = 0.022      # box height / frame height that counts as typography (not UI micro-text)
WORK_W, WORK_H = 1280, 720


def load_done(path):
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            try:
                r = json.loads(line)
                done[r["f"]] = r
            except Exception:
                pass
    return done


def ocr_frame(reader, img, sx, sy):
    res = reader.readtext(img, min_size=12, text_threshold=0.6, low_text=0.35, link_threshold=0.4,
                          width_ths=0.5, mag_ratio=1.0, canvas_size=WORK_W, batch_size=16)
    out = []
    for box, text, conf in res:
        xs = [p[0] * sx for p in box]
        ys = [p[1] * sy for p in box]
        out.append([[round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))], text, round(float(conf), 3)])
    return out


def run_pass(slug, reader, wanted, path, done, label):
    m = meta(slug)
    sx, sy = m["width"] / WORK_W, m["height"] / WORK_H
    todo = sorted(f for f in wanted if f not in done)
    if not todo:
        return
    t0, n_ocr, n_reuse = time.time(), 0, 0
    last_small, last_res = None, None
    lo, hi = todo[0], todo[-1] + 1
    want = set(todo)
    with open(path, "a") as fh:
        for i, f in iter_frames(slug, lo, hi):
            if i not in want:
                continue
            small = cv2.cvtColor(cv2.resize(f, (320, 180), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            reused = False
            if last_small is not None:
                d = cv2.absdiff(small, last_small)
                if d.mean() < 0.6 and d.max() < 25:
                    reused = True
            if reused:
                res = last_res
                n_reuse += 1
            else:
                res = ocr_frame(reader, cv2.resize(f, (WORK_W, WORK_H), interpolation=cv2.INTER_AREA), sx, sy)
                last_small, last_res = small, res
                n_ocr += 1
            rec = {"f": i, "det": res, "reused": reused}
            fh.write(json.dumps(rec) + "\n")
            done[i] = rec
            if (n_ocr + n_reuse) % 200 == 0:
                fh.flush()
                el = time.time() - t0
                print(f"[{slug}] {label} {n_ocr + n_reuse}/{len(todo)} ocr={n_ocr} reused={n_reuse} "
                      f"{el / max(1, n_ocr):.2f}s/ocr", flush=True)
    print(f"[{slug}] {label} done: {len(todo)} frames, ocr={n_ocr}, reused={n_reuse}, "
          f"{time.time() - t0:.0f}s", flush=True)


def main(slug):
    import easyocr
    m = meta(slug)
    n = m["nb_frames"]
    shots = read_shots(slug)
    n = shots[-1]["end_frame"] + 1
    path = DATA / slug / "ocr_raw.jsonl"
    done = load_done(path)
    reader = easyocr.Reader(["en"], gpu="mps", model_storage_directory=os.environ["EASYOCR_DIR"],
                            download_enabled=True, verbose=False)
    # pass A: every Nth frame (3 for the first two videos, 6 afterwards to fit the time budget;
    # the value actually used is recorded in ocr_summary.json)
    step = int(os.environ.get("OCR_PASS_A_STEP", 6))
    if any(f % 3 == 0 and f % 6 != 0 for f in done):
        step = 3
    run_pass(slug, reader, set(range(0, n, step)), path, done, "passA")
    min_h = MIN_EVENT_H * m["height"]
    text_shots = []
    for s in shots:
        hit = False
        for f in range(s["start_frame"], s["end_frame"] + 1):
            for box, text, conf in done.get(f, {}).get("det", []):
                if box[3] - box[1] >= min_h and conf >= 0.5 and sum(c.isalnum() for c in text) >= 2:
                    hit = True
        if hit:
            text_shots.append(s["index"])
    wanted = set()
    for s in shots:
        if s["index"] in text_shots:
            wanted.update(range(s["start_frame"], s["end_frame"] + 1))
    run_pass(slug, reader, wanted, path, done, "passB")
    tb = sum(shots[i]["length_frames"] for i in text_shots)
    summary = {"text_shots": text_shots, "n_text_shots": len(text_shots), "n_shots": len(shots),
               "text_frames": tb, "n_frames": n, "work_res": [WORK_W, WORK_H], "min_event_h": MIN_EVENT_H,
               "ocr_frames": sum(1 for r in done.values() if not r["reused"]),
               "reused_frames": sum(1 for r in done.values() if r["reused"]),
               "pass_a_step": step}
    (DATA / slug / "ocr_summary.json").write_text(json.dumps(summary, indent=1))
    print(f"[{slug}] text-bearing shots {len(text_shots)}/{len(shots)}, frames {tb}/{n}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
