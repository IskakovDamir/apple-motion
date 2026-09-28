#!/usr/bin/env python3
"""Human-in-the-loop role review: one tile per text event (context crop at its settled frame),
labelled with id + automatic role, 6 x 8 tiles per sheet -> data/<slug>/review/review_NN.png

The reviewer lists the ids that are designer-set typography (type laid over the picture, not text
inside UI screens, on products or in the player chrome) in reference/labels/<slug>.json:
  {"typography": [{"ref_frame": 993, "text": "Longest battery life", "cx": 1180, "cy": 330}, ...]}
apply_labels() matches labels back to events by settled frame (+-20) and position (< 1 box height),
so labels survive re-runs that renumber events.
"""
import json
import sys

import cv2
import numpy as np

from common import DATA, ROOT, iter_frames, load_json, meta

TW, TH = 320, 180
COLS, ROWS = 6, 8


def crop_ctx(img, b, W, H):
    cx, cy = b["x"] + b["w"] / 2, b["y"] + b["h"] / 2
    w = max(b["w"] * 1.6, b["h"] * 4 * 16 / 9)
    h = w * 9 / 16
    w, h = min(w, W), min(h, H)
    x0 = int(np.clip(cx - w / 2, 0, W - w)); y0 = int(np.clip(cy - h / 2, 0, H - h))
    c = img[y0:y0 + int(h), x0:x0 + int(w)].copy()
    s = c.shape[1] / w
    cv2.rectangle(c, (int((b["x"] - x0) * s), int((b["y"] - y0) * s)),
                  (int((b["x"] + b["w"] - x0) * s), int((b["y"] + b["h"] - y0) * s)), (0, 0, 255), 2)
    return c


def run(slug):
    m = meta(slug)
    W, H = m["width"], m["height"]
    ev = load_json(DATA / slug / "text_events.json")["events"]
    need = {}
    for e in ev:
        need.setdefault(e["ref_frame"], []).append(e)
    tiles = {}
    for f, img in iter_frames(slug, min(need), max(need) + 1):
        for e in need.get(f, []):
            t = cv2.resize(crop_ctx(img, e["bbox_ref"], W, H), (TW, TH), interpolation=cv2.INTER_AREA)
            cv2.rectangle(t, (0, 0), (TW, 20), (0, 0, 0), -1)
            cv2.putText(t, f"e{e['id']} {e.get('role', '')[:6]} f{e['ref_frame']}", (4, 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
            tiles[e["id"]] = t
    out = DATA / slug / "review"
    out.mkdir(exist_ok=True)
    ids = [e["id"] for e in ev]
    per = COLS * ROWS
    for k in range(0, len(ids), per):
        chunk = ids[k:k + per]
        canvas = np.zeros((ROWS * TH, COLS * TW, 3), np.uint8)
        for i, eid in enumerate(chunk):
            r, c = divmod(i, COLS)
            canvas[r * TH:(r + 1) * TH, c * TW:(c + 1) * TW] = tiles[eid]
        cv2.imwrite(str(out / f"review_{k // per + 1:02d}.png"), canvas)
    print(f"[{slug}] {len(ids)} events -> {int(np.ceil(len(ids) / per))} review sheets", flush=True)


REVIEWED_ROLES = ("typography", "caption")


def apply_labels(slug, events):
    """Override automatic roles with reviewed labels (if present). Returns {role: (matched, labelled)}."""
    p = ROOT / "reference" / "labels" / f"{slug}.json"
    if not p.exists():
        return None
    lab = json.loads(p.read_text())
    stats = {}
    for e in events:
        e.setdefault("role_auto", e.get("role"))
        e["role_source"] = "reviewed"
        if e["role"] in REVIEWED_ROLES:
            e["role"] = "other_text"
    for role in REVIEWED_ROLES:
        items = lab.get(role, [])
        hit_n = 0
        for l in items:
            best, bd = None, None
            for e in events:
                b = e["bbox_ref"]
                d = np.hypot(l["cx"] - (b["x"] + b["w"] / 2), l["cy"] - (b["y"] + b["h"] / 2))
                if abs(l["ref_frame"] - e["ref_frame"]) <= 20 and d < max(40, b["h"]) and (bd is None or d < bd):
                    best, bd = e, d
            if best is not None:
                best["role"] = role
                hit_n += 1
        stats[role] = (hit_n, len(items))
    return stats


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
