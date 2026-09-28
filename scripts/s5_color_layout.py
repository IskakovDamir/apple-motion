#!/usr/bin/env python3
"""STEP 5: colour + layout per shot -> data/<slug>/color_layout.json

Per shot (first / middle / last frame at 480x270):
  background hex   median of the 6 px border ring
  frame class      pure black | pure white | gradient | ui screenshot | product | footage
  accent hexes     k-means (k=5) over saturated pixels (HSV S > 0.35, V > 0.25), top 3 by area
  text hex         from typography events visible in the shot (text_events.json)
  text layout      3x3 grid cell of each typography block, alignment, cap height
Class rules (middle frame): black = >=70% px luma < 16 and border < 16; white = >=70% px > 240;
gradient = edge density < 0.8% and colour std > 6; ui screenshot = >= 8 OCR boxes in the shot's
middle frame (any size) or dense small text; product = uniform border (std < 10) with a
non-uniform centre; otherwise footage.
"""
import json
import sys
from collections import Counter

import cv2
import numpy as np

from common import DATA, hexcol, iter_frames, load_json, meta, read_shots, save_json

W, H = 480, 270


def ocr_counts(slug):
    counts = {}
    p = DATA / slug / "ocr_raw.jsonl"
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
            counts[r["f"]] = sum(1 for _, _, c in r["det"] if c >= 0.3)
        except Exception:
            pass
    return counts


def classify(img, n_ocr):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    border = np.concatenate([img[:6].reshape(-1, 3), img[-6:].reshape(-1, 3), img[:, :6].reshape(-1, 3),
                             img[:, -6:].reshape(-1, 3)])
    bl = float(np.median(cv2.cvtColor(border[None].astype(np.uint8), cv2.COLOR_BGR2GRAY)))
    if (gray < 16).mean() >= 0.7 and bl < 16:
        return "pure black"
    if (gray > 240).mean() >= 0.7 and bl > 235:
        return "pure white"
    if n_ocr is not None and n_ocr >= 8:
        return "ui screenshot"
    edges = cv2.Canny(gray, 60, 160)
    ed = float((edges > 0).mean())
    if ed < 0.008 and img.reshape(-1, 3).std(0).mean() > 6:
        return "gradient"
    bstd = float(border.std(0).mean())
    c = gray[H // 4: 3 * H // 4, W // 4: 3 * W // 4]
    if bstd < 10 and c.std() > 18:
        return "product"
    return "footage"


def accents(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    m = (hsv[..., 1] > 90) & (hsv[..., 2] > 64)
    px = img[m].astype(np.float32)
    if len(px) < 200:
        return []
    k = min(5, len(px) // 40)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, lab, cen = cv2.kmeans(px, k, None, crit, 2, cv2.KMEANS_PP_CENTERS)
    cnt = Counter(lab.ravel().tolist())
    total = m.size
    return [{"hex": hexcol(cen[i]), "area_pct": round(cnt[i] / total * 100, 2)} for i, _ in cnt.most_common(3)]


def run(slug):
    m = meta(slug)
    shots = read_shots(slug)
    counts = ocr_counts(slug)
    te = load_json(DATA / slug / "text_events.json")["events"] if (DATA / slug / "text_events.json").exists() else []
    typo = [e for e in te if e.get("role") == "typography"]
    want = {}
    for s in shots:
        mid = (s["start_frame"] + s["end_frame"]) // 2
        for tag, f in (("first", s["start_frame"]), ("mid", mid), ("last", s["end_frame"])):
            want.setdefault(f, []).append((s["index"], tag))
    imgs = {}
    for i, f in iter_frames(m["slug"] if "slug" in m else slug, scale=(W, H)):
        if i in want:
            for si, tag in want[i]:
                imgs[(si, tag)] = f
    out = []
    for s in shots:
        mid = (s["start_frame"] + s["end_frame"]) // 2
        near = [counts[f] for f in range(mid - 3, mid + 4) if f in counts]
        n_ocr = max(near) if near else None
        rec = {"shot": s["index"], "start_frame": s["start_frame"], "end_frame": s["end_frame"]}
        per = {}
        for tag in ("first", "mid", "last"):
            img = imgs.get((s["index"], tag))
            if img is None:
                continue
            border = np.concatenate([img[:6].reshape(-1, 3), img[-6:].reshape(-1, 3),
                                     img[:, :6].reshape(-1, 3), img[:, -6:].reshape(-1, 3)])
            per[tag] = {"background_hex": hexcol(np.median(border, 0)),
                        "frame_class": classify(img, n_ocr if tag == "mid" else None),
                        "mean_luma": round(float(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()), 1)}
        rec.update(per.get("mid", {}))
        rec["frames"] = per
        mid_img = imgs.get((s["index"], "mid"))
        rec["accents"] = accents(mid_img) if mid_img is not None else []
        ev = [e for e in typo if e["appear_frame"] <= s["end_frame"] and e["gone_frame"] > s["start_frame"]]
        rec["text"] = [{"event": e["id"], "text": e["text"], "hex": e["color_hex"], "grid_cell": e["grid_cell"],
                        "alignment": e["alignment"], "cap_height_pct": e["cap_height_pct"],
                        "center_pct": e["center_pct"]} for e in ev]
        rec["text_hex"] = Counter(e["color_hex"] for e in ev).most_common(1)[0][0] if ev else None
        out.append(rec)
    classes = Counter(r.get("frame_class") for r in out)
    frames_by_class = Counter()
    for r in out:
        frames_by_class[r.get("frame_class")] += r["end_frame"] - r["start_frame"] + 1
    cells = Counter(t["grid_cell"] for r in out for t in r["text"])
    save_json(DATA / slug / "color_layout.json", {
        "slug": slug, "shot_classes": dict(classes), "frame_share_by_class": {k: round(v / m["nb_frames"], 3) for k, v in frames_by_class.items()},
        "text_grid_cells": dict(cells), "shots": out})
    print(f"[{slug}] classes {dict(classes)} text cells {dict(cells)}", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
