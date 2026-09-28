#!/usr/bin/env python3
"""Debug strip of transition boundaries: python debug_bounds.py <slug> <out.jpg> [types,comma]"""
import json, sys, cv2, numpy as np
from common import iter_frames, DATA
slug, out = sys.argv[1], sys.argv[2]
want = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
dbg = json.load(open(DATA / slug / "shots_debug.json"))
B = [b for b in dbg["boundaries"] if not want or b["type"] in want][:24]
need = {k for b in B for k in range(b["frame"] - 4, b["frame"] + 3)}
fr = {i: f for i, f in iter_frames(slug, scale=(160, 90)) if i in need}
rows = []
for b in B:
    row = np.hstack([fr.get(k, np.zeros((90, 160, 3), np.uint8)) for k in range(b["frame"] - 4, b["frame"] + 3)])
    lab = np.zeros((90, 260, 3), np.uint8)
    cv2.putText(lab, f'{b["frame"]} {b["type"]}', (4, 25), 0, 0.55, (255, 255, 255), 1)
    cv2.putText(lab, f'sh{b.get("side_shift_frac")} bl{b.get("blur_dip")} z{b.get("zoom_rate_max")}', (4, 50), 0, 0.4, (200, 200, 200), 1)
    cv2.putText(lab, f'e{b.get("edge_iou","")} l{b.get("layout_corr","")} br{b.get("blend_res","")}', (4, 75), 0, 0.4, (200, 200, 200), 1)
    rows.append(np.hstack([lab, row]))
cv2.imwrite(out, np.vstack(rows) if rows else np.zeros((10, 10, 3), np.uint8))
print(len(rows), "rows")
