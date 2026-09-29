#!/usr/bin/env python3
"""STEP 2b: OCR tracks -> text events with frame-accurate timing.

  data/<slug>/text_events.json   one entry per word/phrase block (timing, geometry, colour)
  data/<slug>/text_measure.json  per-frame pixel measurements used by step 3

Timing definitions (all frames, source fps):
  appear_frame      first frame whose ink mass >= 5% of the settled mass (continuous up to settle)
  full_frame        first frame from which scale/offset/opacity/blur stop changing faster than
                    the settle tolerances (the hold may still drift slowly; drift is reported)
  exit_start_frame  first frame after the hold where change resumes and leads to the exit
  gone_frame        first frame with ink mass < 5% (or the cut that removes the text)
"""
import difflib
import json
import re
import sys
from collections import defaultdict

import cv2
import numpy as np

import textmeasure as tm
from common import DATA, iter_frames, meta, read_shots, save_json, shot_of, hexcol, luminance

MIN_EVENT_H = 0.022
MIN_CONF = 0.3
DENSE = 45          # frames stored densely before first / after last OCR detection
HOLD_STEP = 3       # hold frames sampled every Nth frame
MAX_CROP_PX = 300_000

# settle tolerances per frame (rates)
TOL = {"scale": 0.004, "pos": 0.0012, "opacity": 0.02, "blur": 0.6}


def norm_text(t):
    return re.sub(r"\s+", " ", t).strip()


def key(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def sim(a, b):
    ka, kb = key(a), key(b)
    if not ka or not kb:
        return 0.0
    return difflib.SequenceMatcher(None, ka, kb).ratio()


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def load_ocr(slug, H):
    frames, clutter = {}, {}
    for line in (DATA / slug / "ocr_raw.jsonl").read_text().splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        dets = []
        clutter[r["f"]] = sum(1 for _, _, c in r["det"] if c >= 0.3)
        for box, text, conf in r["det"]:
            text = norm_text(text)
            if conf < MIN_CONF or box[3] - box[1] < MIN_EVENT_H * H or sum(c.isalnum() for c in text) < 1:
                continue
            dets.append((box, text, conf))
        frames[r["f"]] = dets
    return frames, clutter


def track(frames, shots):
    tracks, active = [], []
    for f in sorted(frames):
        dets = frames[f]
        active = [t for t in active if f - t["last"] <= 6]
        cands = []
        for di, (box, text, conf) in enumerate(dets):
            for ti, t in enumerate(active):
                lb = t["boxes"][-1][1]
                io = iou(box, lb)
                s = sim(text, t["texts"][-1][1])
                h = lb[3] - lb[1]
                dc = np.hypot((box[0] + box[2]) / 2 - (lb[0] + lb[2]) / 2, (box[1] + box[3]) / 2 - (lb[1] + lb[3]) / 2)
                ok = (io >= 0.3 and s >= 0.5) or io >= 0.6 or (s >= 0.85 and dc < 1.5 * h)
                if ok:
                    cands.append((io + s, di, ti))
        cands.sort(reverse=True)
        used_d, used_t = set(), set()
        for sc, di, ti in cands:
            if di in used_d or ti in used_t:
                continue
            used_d.add(di)
            used_t.add(ti)
            t = active[ti]
            box, text, conf = dets[di]
            t["boxes"].append((f, box))
            t["texts"].append((f, text, conf))
            t["last"] = f
        for di, (box, text, conf) in enumerate(dets):
            if di in used_d:
                continue
            t = {"boxes": [(f, box)], "texts": [(f, text, conf)], "last": f}
            tracks.append(t)
            active.append(t)
    tracks = [piece for t in tracks for piece in split_swaps(t)]
    out = []
    for t in tracks:
        if len(t["boxes"]) < 3:
            continue
        score = defaultdict(float)
        best_form = {}
        for f, text, conf in t["texts"]:
            k = key(text)
            score[k] += conf
            if k not in best_form or conf > best_form[k][1]:
                best_form[k] = (text, conf)
        k = max(score, key=score.get)
        maxc = max(c for _, _, c in t["texts"])
        if maxc < 0.5:
            continue
        distinct = [kk for kk, v in score.items() if v >= 1.0]
        out.append({"text": best_form[k][0], "boxes": t["boxes"], "texts": t["texts"],
                    "first": t["boxes"][0][0], "last": t["boxes"][-1][0], "max_conf": maxc,
                    "distinct_texts": distinct})
    return out


def split_swaps(t, min_run=6):
    """Split a track where the text changes to a different string that then stays stable
    (text swapped in place: 'Weight 400' -> 'Weight 500'). Counters that roll every few frames
    never form two stable runs, so they stay one event."""
    seq = [(f, key(tx)) for f, tx, c in t["texts"] if c >= 0.5 and key(tx)]
    if len(seq) < 2 * min_run:
        return [t]
    runs = []  # [key, first_f, last_f, count]
    for f, k in seq:
        if runs and (k == runs[-1][0] or difflib.SequenceMatcher(None, k, runs[-1][0]).ratio() >= 0.97):
            runs[-1][2] = f
            runs[-1][3] += 1
        else:
            runs.append([k, f, f, 1])
    stable = [r for r in runs if r[3] >= min_run and r[2] - r[1] >= min_run - 1]
    cuts = []
    for a, b in zip(stable[:-1], stable[1:]):
        if a[0] != b[0]:
            cuts.append((a[2] + b[1] + 1) // 2)
    if not cuts:
        return [t]
    pieces, bounds = [], [-10 ** 9] + cuts + [10 ** 9]
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        bx = [(f, b) for f, b in t["boxes"] if lo <= f < hi]
        tx = [(f, x, c) for f, x, c in t["texts"] if lo <= f < hi]
        if bx:
            pieces.append({"boxes": bx, "texts": tx, "last": bx[-1][0]})
    return pieces


def dedupe_tracks(tr):
    """OCR sometimes reports a line twice (whole line + a fragment of it). Drop a track whose box is
    >= 70% inside a longer-text track's box on their common frames."""
    drop = set()
    for i, a in enumerate(tr):
        for j, b in enumerate(tr):
            if i == j or j in drop or len(key(a["text"])) > len(key(b["text"])):
                continue
            fa, fb = dict(a["boxes"]), dict(b["boxes"])
            common = sorted(set(fa) & set(fb))
            if len(common) < max(3, 0.5 * len(fa)):
                continue
            inside = []
            for f in common[:: max(1, len(common) // 10)]:
                A, B = fa[f], fb[f]
                ix = max(0, min(A[2], B[2]) - max(A[0], B[0]))
                iy = max(0, min(A[3], B[3]) - max(A[1], B[1]))
                inside.append(ix * iy / max(1, (A[2] - A[0]) * (A[3] - A[1])))
            if np.median(inside) >= 0.7 and (len(key(a["text"])) < len(key(b["text"])) or i > j):
                drop.add(i)
                break
    return [t for k, t in enumerate(tr) if k not in drop]


def group_lines(tr):
    """Union-find line tracks into blocks (multi-line phrases)."""
    tr[:] = dedupe_tracks(tr)
    parent = list(range(len(tr)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(tr)):
        for j in range(i + 1, len(tr)):
            a, b = tr[i], tr[j]
            ov = min(a["last"], b["last"]) - max(a["first"], b["first"])
            shorter = min(a["last"] - a["first"], b["last"] - b["first"]) + 1
            if ov < 0.5 * shorter:
                continue
            # compare boxes at a common frame
            fa = dict(a["boxes"])
            fb = dict(b["boxes"])
            common = sorted(set(fa) & set(fb))
            if not common:
                continue
            f = common[len(common) // 2]
            A, B = fa[f], fb[f]
            ha, hb = A[3] - A[1], B[3] - B[1]
            if not 0.7 <= ha / max(1, hb) <= 1.43:
                continue
            h = max(ha, hb)
            vgap = max(B[1] - A[3], A[1] - B[3])
            if vgap > 0.8 * h or vgap < -0.3 * h:
                continue
            hover = min(A[2], B[2]) - max(A[0], B[0])
            aligned = min(abs(A[0] - B[0]), abs((A[0] + A[2]) / 2 - (B[0] + B[2]) / 2), abs(A[2] - B[2])) < 0.6 * h
            if hover > 0 or aligned:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i in range(len(tr)):
        groups[find(i)].append(tr[i])
    blocks = []
    for g in groups.values():
        g.sort(key=lambda t: np.median([b[1] for _, b in t["boxes"]]))
        blocks.append(g)
    blocks.sort(key=lambda g: min(t["first"] for t in g))
    return blocks


def block_box_at(block, f):
    boxes = []
    for t in block:
        d = dict(t["boxes"])
        if f in d:
            boxes.append(d[f])
        else:
            nearest = min(d, key=lambda k: abs(k - f))
            boxes.append(d[nearest])
    b = np.array(boxes)
    return [int(b[:, 0].min()), int(b[:, 1].min()), int(b[:, 2].max()), int(b[:, 3].max())], boxes


def plan_event(block, shots, n, W, H):
    first = min(t["first"] for t in block)
    last = max(t["last"] for t in block)
    # reference frame: a frame inside a STABLE part of the hold (box unchanged over +-3 OCR frames),
    # highest confidence, preferring the first half of the span (after the entry, before the exit)
    conf_at = defaultdict(float)
    for t in block:
        for f, _, c in t["texts"]:
            conf_at[f] += c
    main = max(block, key=lambda t: len(t["boxes"]))
    bx = dict(main["boxes"])
    fs_ = sorted(bx)

    def stability(f):
        near = [g for g in fs_ if 0 < abs(g - f) <= 3]
        return min((iou(bx[f], bx[g]) for g in near), default=0.0)
    span = last - first
    cand = [f for f in fs_ if first + 0.15 * span <= f <= last - 0.15 * span] or fs_
    stable = [f for f in cand if stability(f) >= 0.9] or cand
    fref = max(stable, key=lambda f: (round(conf_at[f], 1), -abs(f - (first + 0.4 * span))))
    box, line_boxes = block_box_at(block, fref)
    bw, bh = box[2] - box[0], box[3] - box[1]
    # search region
    rx0 = max(0, int(box[0] - 0.6 * bw)); rx1 = min(W, int(box[2] + 0.6 * bw))
    ry0 = max(0, int(box[1] - 1.0 * bh)); ry1 = min(H, int(box[3] + 1.0 * bh))
    area = (rx1 - rx0) * (ry1 - ry0)
    k = min(1.0, float(np.sqrt(MAX_CROP_PX / max(1, area))))
    s_first = shot_of(first, shots)
    s_last = shot_of(last, shots)
    lo = max(shots[s_first]["start_frame"], first - DENSE)
    hi = min(shots[s_last]["end_frame"], last + DENSE)
    frames = set(range(lo, min(hi, first + DENSE) + 1)) | set(range(max(lo, last - DENSE), hi + 1))
    frames |= set(range(lo, hi + 1, HOLD_STEP)) | {fref}
    return {"first": first, "last": last, "fref": fref, "box": box, "line_boxes": line_boxes,
            "region": [rx0, ry0, rx1, ry1], "k": k, "lo": lo, "hi": hi, "frames": frames,
            "shot_first": s_first, "shot_last": s_last}


def _ckpt_key(p):
    return f"{p['first']}:{p['last']}:{p['fref']}:{','.join(map(str, p['box']))}"


def _to_jsonable(o):
    if isinstance(o, dict):
        return {k: _to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_to_jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def stream_crops(slug, plans, on_done):
    """One linear decode. Stores region crops for planned frames; calls on_done(i) as soon as
    plan i has all its frames, then frees them (keeps memory bounded)."""
    need, ends = defaultdict(list), defaultdict(list)
    for i, p in enumerate(plans):
        p["crops"] = {}
        if p.get("skip"):
            continue
        for f in p["frames"]:
            need[f].append(i)
        ends[max(p["frames"])].append(i)
    if not need:
        return
    lo, hi = min(need), max(need) + 1
    for f, img in iter_frames(slug, lo, hi):
        for i in need.get(f, []):
            p = plans[i]
            x0, y0, x1, y1 = p["region"]
            c = img[y0:y1, x0:x1]
            if p["k"] < 1:
                c = cv2.resize(c, (max(1, int((x1 - x0) * p["k"])), max(1, int((y1 - y0) * p["k"]))),
                               interpolation=cv2.INTER_AREA)
            p["crops"][f] = c
        for i in ends.get(f, []):
            on_done(i)
            plans[i]["crops"] = None


def measure(p, W, H):
    k = p["k"]
    x0, y0 = p["region"][:2]
    ref = p["crops"][p["fref"]]
    bx = [int((p["box"][0] - x0) * k), int((p["box"][1] - y0) * k), int((p["box"][2] - x0) * k),
          int((p["box"][3] - y0) * k)]
    bx = [max(0, bx[0]), max(0, bx[1]), min(ref.shape[1], bx[2]), min(ref.shape[0], bx[3])]
    txt, bg, ring_med, ring_std = tm.settle_colors(ref, bx)
    a_ref = tm.alpha_map(ref, txt, bg)
    glyph = np.zeros(a_ref.shape, bool)
    glyph[bx[1]:bx[3], bx[0]:bx[2]] = a_ref[bx[1]:bx[3], bx[0]:bx[2]] > 0.5
    contrast = abs(luminance(txt) - luminance(bg))
    glyph_std = float(ref[glyph].astype(np.float32).std(axis=0).mean()) if glyph.any() else 99.0
    nonglyph = ~cv2.dilate(glyph.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    ref_gray_ng = cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY).astype(np.float32)[nonglyph]
    # word / letter units + cap height per line
    lh = bx[3] - bx[1]
    rows = tm.line_rows(glyph, max(2, int(0.08 * lh)))
    units_w, units_l, caps = [], [], []
    for (r0, r1) in rows:
        g = glyph[r0:r1]
        lhh = r1 - r0
        if lhh < 4:
            continue
        for c0, c1 in tm.split_units(g, max(2, int(0.28 * lhh))):
            units_w.append((r0, r1, c0, c1))
        for c0, c1 in tm.letter_units(g):
            if c1 - c0 >= 2:
                units_l.append((r0, r1, c0, c1))
        ch, xh = tm.cap_height(g)
        if ch:
            caps.append((ch, xh))
    # stroke weight: 2 x 90th percentile of the distance transform inside the glyphs
    dist = cv2.distanceTransform(glyph.astype(np.uint8), cv2.DIST_L2, 3)
    stroke_px = float(2 * np.percentile(dist[glyph], 90)) / k if glyph.sum() > 30 else None
    trk = tm.TextTracker(a_ref, bx, txt, units_w if 2 <= len(units_w) <= 12 else (), units_l)
    ref_pose = trk.track(a_ref, ref, 1.0, units=True)
    o_ref = ref_pose["opacity"] if ref_pose and np.isfinite(ref_pose["opacity"]) and ref_pose["opacity"] > 0.2 else 1.0
    u_ref = [u if (u is not None and np.isfinite(u) and u > 0.05) else np.nan for u in (ref_pose or {}).get("unit_gain", [])]
    l_ref = [u if (u is not None and np.isfinite(u) and u > 0.05) else np.nan for u in ((ref_pose or {}).get("letter_gain") or [])]
    frames = sorted(p["crops"])
    iref = frames.index(p["fref"])
    out = {}

    unit_frames = set(range(p["first"] - DENSE, p["first"] + DENSE + 1)) | set(range(p["last"] - DENSE, p["last"] + DENSE + 1))

    def one(f, prior):
        crop = p["crops"][f]
        A = tm.alpha_map(crop, txt, bg)
        r = trk.track(A, crop, prior, units=f in unit_frames or f == p["fref"])
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY).astype(np.float32)
        bgd = float(np.abs(gray[nonglyph] - ref_gray_ng).mean()) if nonglyph.any() else 0.0
        if r is None:
            return {"f": f, "mass": 0.0, "scale": np.nan, "dx": np.nan, "dy": np.nan, "opacity": np.nan,
                    "blur_px": np.nan, "ncc": np.nan, "reveal": np.nan, "clip": None, "bbox": None,
                    "bg_diff": round(bgd, 2), "word_mass": [], "letter_mass": None}, None
        op = r["opacity"] / o_ref if np.isfinite(r["opacity"]) else np.nan
        present = r["ncc"] >= 0.3 and (not np.isfinite(op) or op > 0.04)
        pres = (float(np.clip(op, 0, 1.3)) if np.isfinite(op) else float(np.clip(r["ncc"], 0, 1))) if present else 0.0
        sc = r["scale"]
        th, tw = trk._tmpl(sc).shape
        bb = [round(x0 + (r["cx"] - tw / 2) / k), round(y0 + (r["cy"] - th / 2) / k),
              round(x0 + (r["cx"] + tw / 2) / k), round(y0 + (r["cy"] + th / 2) / k)]
        rec = {"f": f, "mass": round(pres, 4),
               "scale": sc if present else np.nan,
               "dx": (r["cx"] - trk.center_ref[0]) / k / H if present else np.nan,
               "dy": (r["cy"] - trk.center_ref[1]) / k / H if present else np.nan,
               "opacity": (float(np.clip(op, 0, 1.3)) if np.isfinite(op) else np.nan) if present else 0.0,
               "blur_px": r["blur"] * 1.0 / k if present else np.nan,
               "ncc": round(r["ncc"], 3), "reveal": r["reveal"] if present else np.nan, "clip": r["clip"],
               "bbox": bb if present else None, "bg_diff": round(bgd, 2),
               "word_mass": [round(float(np.clip(g / u, -0.5, 1.5)), 3) if np.isfinite(u) and g is not None and np.isfinite(g) else None
                             for g, u in zip(r["unit_gain"], u_ref)],
               "letter_mass": [round(float(np.clip(g / u, -0.5, 1.5)), 3) if np.isfinite(u) and g is not None and np.isfinite(g) else None
                               for g, u in zip(r["letter_gain"], l_ref)] if r["letter_gain"] and l_ref else None}
        return rec, (sc if present else None)

    # walk outward from the settled frame, carrying the scale prior; stop after 4 absent frames
    for direction in (-1, 1):
        prior, absent = 1.0, 0
        rng = range(iref, -1, -1) if direction < 0 else range(iref, len(frames))
        for i in rng:
            f = frames[i]
            if f in out:
                continue
            rec, sc = one(f, prior)
            out[f] = rec
            if sc is None:
                absent += 1
                if absent >= 4:
                    break
            else:
                absent = 0
                prior = sc
    series = [out[f] for f in sorted(out)]
    info = {"glyph_std": glyph_std, "text_bgr": txt, "bg_bgr": bg, "ring_med": ring_med, "ring_std": ring_std,
            "contrast": contrast, "units_w": len(units_w), "units_l": len(units_l), "k": k,
            "stroke_px": stroke_px, "cap_px": [c / k for c, _ in caps], "xh_px": [x / k for _, x in caps if x], "n_lines_px": len(rows)}
    return series, info


def _smooth(series, key):
    """3-tap median over consecutive samples (suppresses single-frame estimator noise)."""
    v = np.array([x[key] if x[key] is not None else np.nan for x in series], np.float64)
    out = v.copy()
    for i in range(1, len(v) - 1):
        w = v[i - 1:i + 2]
        w = w[np.isfinite(w)]
        if len(w):
            out[i] = np.median(w)
    return out


def rates(series):
    """Per-frame absolute rate of change of each (median-smoothed) channel, per source frame."""
    f = np.array([x["f"] for x in series], np.float64)
    sm = {k: _smooth(series, k) for k in ("scale", "opacity", "blur_px", "dx", "dy", "mass")}
    out = []
    for i in range(1, len(series)):
        dt = f[i] - f[i - 1]
        r = {}
        for ch, k in (("scale", "scale"), ("opacity", "opacity"), ("blur", "blur_px"), ("mass", "mass")):
            a, b = sm[k][i - 1], sm[k][i]
            r[ch] = abs(b - a) / dt if np.isfinite(a) and np.isfinite(b) else (0.0 if ch == "blur" else np.inf)
        pa = (sm["dx"][i - 1], sm["dy"][i - 1]); pb = (sm["dx"][i], sm["dy"][i])
        r["pos"] = float(np.hypot(pb[0] - pa[0], pb[1] - pa[1]) / dt) if all(np.isfinite(pa + pb)) else np.inf
        out.append((int(f[i]), r))
    return out


def moving(r):
    return (r["scale"] > TOL["scale"] or r["pos"] > TOL["pos"] or r["opacity"] > TOL["opacity"]
            or r["blur"] > TOL["blur"] or r["mass"] > 0.04)


def settle_distance(series, fref, cap_px, first, last):
    """D(f) = max over channels of |value - settled value| / significance, with the settled value
    following the slow hold drift (linear trend fitted on the middle of the OCR span).
    D < 1 means 'looks settled'. Channels: scale, position, opacity, blur, reveal."""
    fs = np.array([x["f"] for x in series], np.float64)
    sm = {k: _smooth(series, k) for k in ("scale", "dx", "dy", "opacity", "blur_px", "reveal", "mass")}
    iref = int(np.argmin(np.abs(fs - fref)))
    sig = {"scale": 0.04, "pos": 0.005, "opacity": 0.15, "blur_px": max(1.5, 0.04 * cap_px), "reveal": 0.15}
    span = last - first
    mid = (fs >= first + 0.2 * span) & (fs <= last - 0.2 * span)
    # over live footage the photometric estimates move with the background: widen their tolerance to
    # 3x the jitter seen while the text is certainly held (middle of the OCR span)
    for k in ("opacity", "blur_px", "reveal"):
        v = sm[k][mid]
        v = v[np.isfinite(v)]
        if len(v) >= 5:
            sig[k] = max(sig[k], 3 * float(np.std(v)))
    trend = {}
    for k in ("scale", "dx", "dy"):
        ok = mid & np.isfinite(sm[k])
        trend[k] = float(np.polyfit(fs[ok], sm[k][ok], 1)[0]) if ok.sum() >= 4 and np.ptp(fs[ok]) >= 6 else 0.0
    # settled reference = median over the certainly-held middle of the span (NOT the reference frame
    # alone: the template matches itself exactly there - blur 0, scale 1.000 - which biased D upward
    # on every other frame; found by rendering known animations and measuring them back)
    ok_mid = mid & np.isfinite(sm["mass"]) & (sm["mass"] >= 0.5)
    t_mid = float(np.median(fs[ok_mid])) if ok_mid.any() else float(fs[iref])
    refv = {}
    for k in ("scale", "dx", "dy", "opacity", "blur_px", "reveal"):
        v = sm[k][ok_mid]
        v = v[np.isfinite(v)]
        refv[k] = float(np.median(v)) if len(v) else sm[k][iref]
    D = np.full(len(fs), np.inf)
    for i in range(len(fs)):
        if not np.isfinite(sm["mass"][i]) or sm["mass"][i] < 0.05:
            continue
        dt = fs[i] - t_mid
        terms = []
        if np.isfinite(sm["scale"][i]) and np.isfinite(refv["scale"]):
            terms.append(abs(sm["scale"][i] - (refv["scale"] + trend["scale"] * dt)) / sig["scale"])
        if np.isfinite(sm["dx"][i]) and np.isfinite(sm["dy"][i]) and np.isfinite(refv["dx"]) and np.isfinite(refv["dy"]):
            ex = sm["dx"][i] - (refv["dx"] + trend["dx"] * dt)
            ey = sm["dy"][i] - (refv["dy"] + trend["dy"] * dt)
            terms.append(np.hypot(ex, ey) / sig["pos"])
        for k in ("opacity", "blur_px", "reveal"):
            if np.isfinite(sm[k][i]) and np.isfinite(refv[k]):
                terms.append(abs(sm[k][i] - refv[k]) / sig[k])
        wm = series[i].get("word_mass") or []
        wv = [w for w in wm if w is not None]
        if len(wv) >= 2:
            terms.append(max(abs(w - 1) for w in wv) / 0.25)  # every word present (per-word entries)
        D[i] = max(terms) if terms else np.inf
    return fs.astype(int), D, sm["mass"], trend


def foreign_frames(p, frames_ocr, block_text):
    """Frames in which OCR confidently read a DIFFERENT string inside this event's box (text swapped
    in place). Presence / settle walks must not cross them."""
    box = p["box"]
    own = key(block_text)
    digits = lambda k: sum(ch.isdigit() for ch in k) >= max(1, len(k) // 2)
    out = set()
    for f in range(p["lo"], p["hi"] + 1):
        for b, t, c in frames_ocr.get(f, []):
            if c < 0.5 or iou(b, box) < 0.3:
                continue
            k = key(t)
            if digits(k) and digits(own):
                continue  # a number rolling in place is the same event (counter)
            if k and difflib.SequenceMatcher(None, k, own).ratio() < 0.5 and k not in own:
                out.add(f)
    return out


def timing(series, fref, shots, p, cap_px):
    fs, D, mass, trend = settle_distance(series, fref, cap_px, p["first"], p["last"])
    iref = int(np.argmin(np.abs(fs - fref)))
    # the walks start from a frame that is itself settled (D < 1): the nearest one to the reference
    if not D[iref] < 1:
        ok = np.where(D < 1)[0]
        if len(ok):
            iref = int(ok[np.argmin(np.abs(ok - iref))])
    # appear / gone: contiguous presence (mass >= 5%) around the settled frame
    cuts = {sh["start_frame"] for sh in shots}
    nccs = {x["f"]: (x.get("ncc") if x.get("ncc") is not None else 0.0) for x in series}

    def crosses_cut(a, b):  # a < b: is there a shot start in (a, b]?
        return any(a < c <= b for c in cuts)
    by_f = {x["f"]: x for x in series}

    foreign = p.get("foreign") or set()

    def other_text(f):
        """Full-opacity, unscaled glyphs that do not match the template = different text in place."""
        if int(f) in foreign:
            return True
        x = by_f.get(int(f), {})
        nc, op, sc = x.get("ncc"), x.get("opacity"), x.get("scale")
        ok = all(v is not None and np.isfinite(v) for v in (nc, op, sc))
        return ok and nc < 0.6 and op >= 0.85 and 0.97 <= sc <= 1.03
    i = iref
    while i > 0 and mass[i - 1] >= 0.05 and fs[i] - fs[i - 1] <= HOLD_STEP:
        if crosses_cut(fs[i - 1], fs[i]) and nccs.get(int(fs[i - 1]), 0.0) < 0.8:
            break  # different text in the same place on the previous shot
        if other_text(fs[i - 1]):
            break
        i -= 1
    appear, appear_at_window_start = int(fs[i]), i == 0
    j = iref
    while j < len(fs) - 1 and mass[j + 1] >= 0.05 and fs[j + 1] - fs[j] <= HOLD_STEP:
        if crosses_cut(fs[j], fs[j + 1]) and nccs.get(int(fs[j + 1]), 0.0) < 0.8:
            break
        if other_text(fs[j + 1]):
            break
        j += 1
    gone, gone_at_window_end = int(fs[j]) + 1, j == len(fs) - 1
    # full: first settled sample after appear that is followed by mostly settled samples;
    # exit start: sample after the last settled one before gone (mirror rule). Tolerant of isolated
    # glitch samples inside the hold (one bad sample must not end the hold).
    S_ = D < 1
    full = None
    for k in range(i, iref + 1):
        nxt = S_[k + 1:k + 4]
        if S_[k] and (len(nxt) == 0 or nxt.sum() >= min(2, len(nxt))):
            full = int(fs[k])
            break
    if full is None:
        full = int(fs[iref])
    exit_start = gone
    for k in range(j, iref - 1, -1):
        prv = S_[max(i, k - 3):k]
        if S_[k] and (len(prv) == 0 or prv.sum() >= min(2, len(prv))):
            exit_start = int(fs[k + 1]) if k < j else gone
            break
    exit_start = max(exit_start, full)
    sa = shots[p["shot_first"]]["start_frame"]
    sb = shots[p["shot_last"]]["end_frame"] + 1
    if full - appear <= 1:
        appear_kind = "cut" if appear == sa else "instant"
    else:
        appear_kind = "animated"
    if gone_at_window_end and gone == sb:
        exit_kind = "cut" if gone - exit_start <= 1 else "animated_then_cut"
    else:
        exit_kind = "animated" if gone - exit_start > 1 else "instant"
    return appear, full, exit_start, gone, appear_kind, exit_kind


def drift(series, full, exit_start, fps):
    hold = [s for s in series if full <= s["f"] <= exit_start and np.isfinite(s["scale"])]
    if len(hold) < 4 or hold[-1]["f"] - hold[0]["f"] < 6:
        return None
    t = np.array([s["f"] for s in hold], np.float32) / fps
    sc = np.array([s["scale"] for s in hold])
    dy = np.array([s["dy"] for s in hold])
    dx = np.array([s["dx"] for s in hold])
    return {"scale_pct_per_s": round(float(np.polyfit(t, sc, 1)[0] * 100), 3),
            "dy_pct_h_per_s": round(float(np.polyfit(t, dy, 1)[0] * 100), 3),
            "dx_pct_h_per_s": round(float(np.polyfit(t, dx, 1)[0] * 100), 3)}


TIMECODE = re.compile(r"^\d{1,2}[.:,]\d{2}([.:,]\d{2})?$")


def classify_role(lines, cap_frac, glyph_std, clutter, locked, bg_change, bg_type, box, W, H, block):
    """typography = designer-set type laid over the picture; the rest is text inside the picture.
      chrome     timecodes / player UI (the recap's scrubber device)
      ui_text    text inside app screens (dense text, small)
      scene_text text on products / signage / in footage (moves or is lit with the scene)"""
    joined = " ".join(lines)
    if all(TIMECODE.match(l.replace(" ", "")) for l in lines):
        return "chrome"
    letters = sum(ch.isalpha() for ch in joined)
    words = [w for w in re.split(r"\W+", joined) if len(w) >= 2]
    if cap_frac >= 0.025 and glyph_std <= 28 and clutter <= 6 and letters >= 3 and (locked or bg_type == "solid"):
        return "typography"
    if cap_frac >= 0.06 and glyph_std <= 28 and letters >= 2 and locked:
        return "typography"
    if clutter > 6 or cap_frac < 0.02:
        return "ui_text"
    return "scene_text"


def grid_cell(cx, cy, W, H):
    col = "left" if cx < W / 3 else ("center" if cx < 2 * W / 3 else "right")
    row = "top" if cy < H / 3 else ("middle" if cy < 2 * H / 3 else "bottom")
    return f"{row}-{col}"


def alignment(line_boxes, W):
    if len(line_boxes) >= 2:
        lb = np.array(line_boxes, np.float32)
        h = np.median(lb[:, 3] - lb[:, 1])
        spreads = {"left": np.ptp(lb[:, 0]), "center": np.ptp((lb[:, 0] + lb[:, 2]) / 2), "right": np.ptp(lb[:, 2])}
        best = min(spreads, key=spreads.get)
        return best if spreads[best] < 0.5 * h else "ragged"
    b = line_boxes[0]
    cx = (b[0] + b[2]) / 2
    if abs(cx - W / 2) < 0.04 * W:
        return "center"
    return "left" if cx < W / 2 else "right"


def run(slug):
    m = meta(slug)
    W, H, fps = m["width"], m["height"], m["fps"]
    shots = read_shots(slug)
    n = shots[-1]["end_frame"] + 1
    frames, clutter = load_ocr(slug, H)
    tr = track(frames, shots)
    blocks = group_lines(tr)
    plans = [plan_event(b, shots, n, W, H) for b in blocks]
    results = {}
    # checkpoint: every measured event is appended at once, so a restart (the USB drive drops out)
    # only measures what is missing
    ck = DATA / slug / "_s2b_checkpoint.jsonl"
    cached = {}
    if ck.exists():
        for line in ck.read_text().splitlines():
            try:
                r = json.loads(line)
                cached[r["key"]] = (r["series"], r["info"])
            except Exception:
                pass
    for i, p in enumerate(plans):
        k = _ckpt_key(p)
        if k in cached:
            results[i] = cached[k]
            p["skip"] = True
    print(f"[{slug}] checkpoint: {len(results)}/{len(plans)} events already measured", flush=True)
    ckf = open(ck, "a")

    def on_done(i):
        try:
            results[i] = measure(plans[i], W, H)
            ckf.write(json.dumps({"key": _ckpt_key(plans[i]), "series": _to_jsonable(results[i][0]),
                                  "info": _to_jsonable(results[i][1])}) + "\n")
            ckf.flush()
        except Exception as ex:  # keep going; record failure
            print(f"[{slug}] event {i} measure failed: {ex!r}", flush=True)

    stream_crops(slug, plans, on_done)
    ckf.close()
    events, measures = [], {}
    for eid, (block, p) in enumerate(zip(blocks, plans)):
        if eid not in results:
            continue
        series, info = results[eid]
        box = p["box"]
        line_texts = [t["text"] for t in block]
        caps = info["cap_px"]
        line_h = float(np.median([b[3] - b[1] for b in p["line_boxes"]]))
        cap_px = float(np.median(caps)) if caps else 0.64 * line_h
        # glow / tight leading can merge lines in the glyph mask; fall back to the OCR line height
        # (cap = 0.64 x EasyOCR line box height, median over clean wwdc22 typography)
        if not 0.4 * line_h <= cap_px <= 0.9 * line_h:
            cap_px = 0.64 * line_h
        p["foreign"] = foreign_frames(p, frames, " ".join(t["text"] for t in block))
        appear, full, exit_start, gone, ak, ek = timing(series, p["fref"], shots, p, cap_px)
        xh = float(np.median(info["xh_px"])) if info["xh_px"] else None
        bb_time, last_bb = [], None
        for s_ in series:
            if s_["bbox"] and appear <= s_["f"] < gone and (last_bb is None or max(abs(a - b) for a, b in zip(s_["bbox"], last_bb)) > 1):
                bb_time.append([s_["f"]] + s_["bbox"])
                last_bb = s_["bbox"]
        ring_hex = hexcol(info["ring_med"])
        bg_type = "solid" if info["ring_std"] < 6 else ("gradient" if info["ring_std"] < 18 else "image")
        numeric = all(sum(ch.isdigit() for ch in d) >= max(1, len(d) // 2) for d in block[0]["distinct_texts"]) \
            if block[0]["distinct_texts"] else False
        hold = [x for x in series if full <= x["f"] <= exit_start]
        bg_change = max((x["bg_diff"] for x in hold), default=0.0)
        hd = drift(series, full, exit_start, fps)
        locked = bool(hd is None or (abs(hd["scale_pct_per_s"]) < 6 and abs(hd["dy_pct_h_per_s"]) < 1.5
                                     and abs(hd["dx_pct_h_per_s"]) < 1.5))
        clut = int(np.median([clutter.get(f, 0) for f in range(p["first"], p["last"] + 1) if f in clutter] or [0]))
        role = classify_role(line_texts, cap_px / H, info["glyph_std"], clut, locked, bg_change,
                             bg_type, box, W, H, block)
        ev = {
            "id": eid, "role": role, "text": " / ".join(line_texts), "lines": line_texts, "line_count": len(block),
            "shot_index": p["shot_first"], "shot_index_last": p["shot_last"],
            "appear_frame": appear, "full_frame": full, "exit_start_frame": exit_start, "gone_frame": gone,
            "entry_frames": full - appear, "hold_frames": exit_start - full, "exit_frames": gone - exit_start,
            "appear_kind": ak, "exit_kind": ek,
            "ocr_first_frame": p["first"], "ocr_last_frame": p["last"], "ref_frame": p["fref"],
            "ocr_max_conf": round(max(t["max_conf"] for t in block), 3),
            "ocr_distinct_texts": sorted({d for t in block for d in t["distinct_texts"]}),
            "numeric": bool(numeric),
            "bbox_ref": {"x": box[0], "y": box[1], "w": box[2] - box[0], "h": box[3] - box[1],
                         "x_pct": round(box[0] / W * 100, 2), "y_pct": round(box[1] / H * 100, 2),
                         "w_pct": round((box[2] - box[0]) / W * 100, 2), "h_pct": round((box[3] - box[1]) / H * 100, 2)},
            "line_boxes": p["line_boxes"],
            "bbox_over_time": bb_time,
            "cap_height_px": round(cap_px, 1), "cap_height_pct": round(cap_px / H * 100, 2),
            "x_height_ratio": round(xh / cap_px, 3) if xh and cap_px else None,
            "stroke_to_cap": round(info["stroke_px"] / cap_px, 3) if info.get("stroke_px") and cap_px else None,
            "line_pitch_to_cap": (round(float(np.median(np.diff(sorted((b[1] + b[3]) / 2 for b in p["line_boxes"])))) / cap_px, 2)
                                  if len(p["line_boxes"]) >= 2 and cap_px else None),
            "alignment": alignment(p["line_boxes"], W),
            "grid_cell": grid_cell((box[0] + box[2]) / 2, (box[1] + box[3]) / 2, W, H),
            "center_pct": [round((box[0] + box[2]) / 2 / W * 100, 1), round((box[1] + box[3]) / 2 / H * 100, 1)],
            "color_hex": hexcol(info["text_bgr"]), "background_hex": ring_hex,
            "background_type": bg_type, "contrast_luma": round(info["contrast"], 1),
            "word_units": info["units_w"], "letter_units": info["units_l"],
            "hold_drift": hd,
            "role_features": {"glyph_color_std": round(info["glyph_std"], 1), "ocr_boxes_in_frame": clut,
                              "screen_locked": locked, "bg_change_during_hold": round(bg_change, 1)},
        }
        events.append(ev)
        measures[eid] = {"k": info["k"], "series": series}
    # swap-in-place: an event that appears within 2 frames of another's exit at the same place
    for a in events:
        for b in events:
            if b is a or b["shot_index"] != a["shot_index"]:
                continue
            A = [a["bbox_ref"][k] for k in ("x", "y", "w", "h")]
            B = [b["bbox_ref"][k] for k in ("x", "y", "w", "h")]
            io = iou([A[0], A[1], A[0] + A[2], A[1] + A[3]], [B[0], B[1], B[0] + B[2], B[1] + B[3]])
            cyA, cyB = A[1] + A[3] / 2, B[1] + B[3] / 2
            if abs(b["appear_frame"] - a["gone_frame"]) <= 3 and (io > 0.2 or abs(cyA - cyB) < 0.5 * A[3]):
                b["replaces_event"] = a["id"]
    from review_sheet import apply_labels
    lab = apply_labels(slug, events)
    if lab:
        print(f"[{slug}] reviewed labels applied: {lab}", flush=True)
    od = DATA / slug
    save_json(od / "text_events.json", {"slug": slug, "fps": fps, "width": W, "height": H,
                                        "params": {"min_event_h": MIN_EVENT_H, "min_conf": MIN_CONF,
                                                   "settle_tolerance_per_frame": TOL, "dense": DENSE,
                                                   "hold_step": HOLD_STEP},
                                        "n_events": len(events), "events": events})
    save_json(od / "text_measure.json", measures)
    ck.unlink(missing_ok=True)  # complete: the checkpoint has served its purpose
    print(f"[{slug}] {len(tr)} line tracks -> {len(events)} events", flush=True)


if __name__ == "__main__":
    for s in sys.argv[1:]:
        run(s)
