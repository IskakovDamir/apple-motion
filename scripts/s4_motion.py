#!/usr/bin/env python3
"""STEP 4: non-text motion per shot -> data/<slug>/motion.json

Dense Farneback flow on 480x270 gray, every consecutive frame pair inside each shot.
Per pair a similarity model is fitted to the flow: u = tx + a*x - b*y, v = ty + b*x + a*y
(x, y centred): tx/ty = translation, a = zoom rate per frame, b = rotation per frame.
Per shot:
  dominant move  static | pan | tilt | push (zoom in) | pull (zoom out) | whip | local (subject/UI moves)
  speed curve    |global velocity| in % of frame width per frame (zoom converted at the frame edge)
  accel / peak / decel frames (10% of peak thresholds), fitted spring + bezier of the cumulative move
  element entries per second: grid cells (40 px) that switch from empty to edge-dense and stay
  occupied >= 6 frames, clustered; motion-compensated for global translation
"""
import sys

import cv2
import numpy as np

import motionfit as mf
from common import DATA, iter_frames, meta, read_shots, save_json

FW, FH = 480, 270
CELL = 16            # px at 480 wide = 64 px at 1920


def fit_similarity(flow, xs, ys):
    u = flow[..., 0].ravel()
    v = flow[..., 1].ravel()
    x, y = xs.ravel(), ys.ravel()
    n = len(u)
    A = np.zeros((2 * n, 4), np.float32)
    A[:n, 0] = 1; A[:n, 2] = x; A[:n, 3] = -y
    A[n:, 1] = 1; A[n:, 2] = y; A[n:, 3] = x
    bvec = np.concatenate([u, v])
    sol, *_ = np.linalg.lstsq(A, bvec, rcond=None)
    pred = A @ sol
    resid = float(np.sqrt(((bvec - pred) ** 2).reshape(2, n).sum(0)).mean())
    return sol, resid


def occupancy(gray):
    e = cv2.Canny(gray, 60, 160)
    h, w = e.shape
    g = e[: h // CELL * CELL, : w // CELL * CELL].reshape(h // CELL, CELL, w // CELL, CELL).mean((1, 3))
    return g > 20


def shot_motion(frames, fps):
    n = len(frames)
    ys, xs = np.mgrid[0:FH:6, 0:FW:6].astype(np.float32)
    xs -= FW / 2
    ys -= FH / 2
    tx, ty, zr, rot, res = [], [], [], [], []
    occ = [occupancy(frames[0])]
    for i in range(1, n):
        flow = cv2.calcOpticalFlowFarneback(frames[i - 1], frames[i], None, 0.5, 4, 21, 3, 5, 1.2, 0)
        sub = flow[0:FH:6, 0:FW:6]
        (a_tx, a_ty, a, b), r = fit_similarity(sub, xs, ys)
        tx.append(a_tx); ty.append(a_ty); zr.append(a); rot.append(b); res.append(r)
        occ.append(occupancy(frames[i]))
    if not tx:
        return None
    tx, ty, zr, rot, res = map(np.array, (tx, ty, zr, rot, res))
    # speed in % of frame width per frame: translation + zoom displacement at the frame edge
    speed = np.hypot(tx, ty) / FW * 100 + np.abs(zr) * (FW / 2) / FW * 100
    cum_tx = float(tx.sum() / FW * 100)
    cum_ty = float(ty.sum() / FH * 100)
    cum_zoom = float((np.prod(1 + zr) - 1) * 100)
    cum_rot = float(np.degrees(rot.sum()))
    peak = float(speed.max())
    local = float(np.median(res) / FW * 100)
    trans_mag = float(np.hypot(cum_tx, cum_ty))
    if peak > 5 and (speed > 2.5).sum() <= max(3, 0.3 * len(speed)):
        dom = "whip"
    elif trans_mag < 2 and abs(cum_zoom) < 2 and peak < 0.3:
        dom = "local" if local > 0.15 else "static"
    elif abs(cum_zoom) >= trans_mag * 0.6 and abs(cum_zoom) >= 2:
        dom = "push" if cum_zoom > 0 else "pull"
    elif trans_mag >= 2:
        dom = "pan" if abs(cum_tx) >= abs(cum_ty) else "tilt"
    else:
        dom = "local" if local > 0.15 else "static"
    rec = {"dominant_move": dom, "cum_translation_pct": [round(cum_tx, 2), round(cum_ty, 2)],
           "cum_zoom_pct": round(cum_zoom, 2), "cum_rotation_deg": round(cum_rot, 2),
           "peak_speed_pct_w_per_frame": round(peak, 3), "mean_speed_pct_w_per_frame": round(float(speed.mean()), 3),
           "local_motion_pct_w": round(local, 3),
           "speed_curve": [round(float(v), 3) for v in speed]}
    # accel / decel around the peak
    if peak > 0.1:
        ip = int(np.argmax(speed))
        thr = 0.1 * peak
        a0 = ip
        while a0 > 0 and speed[a0 - 1] >= thr:
            a0 -= 1
        d1 = ip
        while d1 < len(speed) - 1 and speed[d1 + 1] >= thr:
            d1 += 1
        rec.update({"accel_start_rel": a0, "peak_rel": ip, "decel_end_rel": d1 + 1,
                    "accel_frames": ip - a0, "decel_frames": d1 + 1 - ip})
        seg = speed[a0:d1 + 1]
        if len(seg) >= 3 and seg.sum() > 0:
            cum = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
            fr = np.arange(len(cum), dtype=np.float64)
            rec["spring"] = mf.fit_spring(fr, cum, fps)
            rec["bezier"] = mf.fit_bezier(fr / fr[-1], cum)
    # element entries: a cell is "born" when it was empty for the previous 6 frames and stays
    # occupied for the next 6 (motion-compensated for global translation); births connected in
    # space AND time (3-D labelling) count as one element entering
    from scipy import ndimage
    occ = np.array(occ)
    T = len(occ)
    born = np.zeros_like(occ)
    shift_x = np.concatenate([[0], np.cumsum(np.round(tx / CELL))]).astype(int)
    shift_y = np.concatenate([[0], np.cumsum(np.round(ty / CELL))]).astype(int)
    for i in range(6, T - 6):
        prev = np.zeros_like(occ[i])
        for j in range(i - 6, i):
            prev |= np.roll(np.roll(occ[j], shift_y[i] - shift_y[j], 0), shift_x[i] - shift_x[j], 1)
        born[i] = occ[i] & ~prev & occ[i:i + 6].all(0)
    lab, nlab = ndimage.label(born, structure=np.ones((3, 3, 3)))
    sizes = ndimage.sum(born, lab, range(1, nlab + 1)) if nlab else []
    entries = int(sum(1 for z in sizes if z >= 2))
    dur_s = n / fps
    rec["element_entries"] = int(entries)
    rec["element_entries_per_s"] = round(entries / dur_s, 2) if dur_s > 0 else 0.0
    return rec


def run(slug):
    m = meta(slug)
    fps = m["fps"]
    shots = read_shots(slug)
    out = []
    cur, buf = 0, []
    s = shots[0]
    for i, f in iter_frames(slug, scale=(FW, FH), gray=True):
        while cur < len(shots) and i > shots[cur]["end_frame"]:
            rec = shot_motion(buf, fps) if len(buf) >= 2 else None
            out.append({"shot": shots[cur]["index"], "start_frame": shots[cur]["start_frame"],
                        "end_frame": shots[cur]["end_frame"], **(rec or {"dominant_move": "static", "note": "1 frame"})})
            cur += 1
            buf = []
        buf.append(f)
    if cur < len(shots) and buf:
        rec = shot_motion(buf, fps) if len(buf) >= 2 else None
        out.append({"shot": shots[cur]["index"], "start_frame": shots[cur]["start_frame"],
                    "end_frame": shots[cur]["end_frame"], **(rec or {"dominant_move": "static"})})
    for r in out:
        for k in ("accel_start_rel", "peak_rel", "decel_end_rel"):
            if k in r:
                r[k.replace("_rel", "_frame")] = r["start_frame"] + r.pop(k)
    from collections import Counter
    total_entries = sum(r.get("element_entries", 0) for r in out)
    save_json(DATA / slug / "motion.json", {"slug": slug, "fps": fps, "flow_res": [FW, FH],
                                            "dominant_moves": dict(Counter(r["dominant_move"] for r in out)),
                                            "element_entries_total": total_entries,
                                            "element_entries_per_s": round(total_entries / (m["nb_frames"] / fps), 2),
                                            "shots": out})
    print(f"[{slug}] motion: {dict(Counter(r['dominant_move'] for r in out))}, entries/s "
          f"{total_entries / (m['nb_frames'] / fps):.2f}", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
