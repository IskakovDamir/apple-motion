#!/usr/bin/env python3
"""Oracle 'OCR' for our own flat-background renders: text boxes from contrast against the card
background, strings from the ground-truth file. Writes data/<slug>/ocr_raw.jsonl in the same format
as s2a_ocr.py, so steps 2b/3 can be calibrated without spending GPU time on OCR.

  python s2a_oracle.py render-cal --truth demo/out/calibration.truth.json
"""
import argparse
import json

import cv2
import numpy as np

from common import DATA, iter_frames, load_json, meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--truth", required=True)
    a = ap.parse_args()
    m = meta(a.slug)
    H = m["height"]
    T = load_json(a.truth)["cards"]
    out = open(DATA / a.slug / "ocr_raw.jsonl", "w")
    for f, img in iter_frames(a.slug):
        card = next((c for c in T if c["start"] <= f < c["start"] + c["frames"]), None)
        dets = []
        if card and card.get("lines"):
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            bg = int(np.median(np.concatenate([g[:8].ravel(), g[-8:].ravel()])))
            mask = (np.abs(g.astype(np.int16) - bg) > 60).astype(np.uint8)
            mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (int(H * 0.04), 3)))
            n, lab, st, _ = cv2.connectedComponentsWithStats(mask, 8)
            boxes = [st[i] for i in range(1, n) if st[i][3] >= 0.022 * H and st[i][2] >= 0.03 * H]
            boxes.sort(key=lambda s: s[1])
            for li, (x, y, w, h, area) in enumerate(boxes[: len(card["lines"])]):
                text = card["lines"][min(li, len(card["lines"]) - 1)]
                dets.append([[int(x), int(y), int(x + w), int(y + h)], text, 0.99])
        out.write(json.dumps({"f": f, "det": dets, "reused": False}) + "\n")
    out.close()
    (DATA / a.slug / "ocr_summary.json").write_text(json.dumps({"oracle": True, "truth": a.truth}))
    print(f"[{a.slug}] oracle OCR written")


if __name__ == "__main__":
    main()
