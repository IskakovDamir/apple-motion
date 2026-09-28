#!/usr/bin/env python3
"""STEP 1: shot boundaries + transition type guess -> data/<slug>/shots.csv (+ shots_debug.json).

PySceneDetect ContentDetector (lowered threshold, min_scene_len 3) catches hard cuts and whips.
A windowed pass over the same content_val stats catches fast dissolves / wipes that never spike
on a single frame. Each boundary is then classified from 160x90 thumbnails around it:
  cut        single-frame change, neighbours still
  whip       large global translation (phase correlation) and/or motion blur spike at the boundary
  dissolve   multi-frame, intermediate frames = linear blend of A and B, alpha monotonic
  mask wipe  multi-frame, each pixel is either ~A or ~B, B-area grows monotonically
  scale through  strong zoom (flow divergence) into the boundary, then change
  match cut  hard cut whose structure (edges/layout) is preserved across the boundary
"""
import csv
import sys

import cv2
import numpy as np
from scenedetect import ContentDetector, SceneManager, StatsManager, open_video

from common import DATA, meta, out_dir, save_json, slugs, video_path, iter_frames

CONTENT_THRESHOLD = 22.0   # PySceneDetect default is 27; lower catches soft cuts on flat backgrounds
MIN_SCENE_LEN = 3
WINDOW = 6                 # frames summed for soft-transition detection
WINDOW_THRESHOLD = 40.0    # summed content_val over WINDOW frames
THUMB = (160, 90)
GRAY = (320, 180)


def detect(slug):
    video = open_video(str(video_path(slug)), backend="opencv")
    stats = StatsManager()
    sm = SceneManager(stats_manager=stats)
    sm.add_detector(ContentDetector(threshold=CONTENT_THRESHOLD, min_scene_len=MIN_SCENE_LEN))
    sm.detect_scenes(video=video, show_progress=False)
    scenes = sm.get_scene_list(start_in_scene=True)
    n = int(meta(slug)["nb_frames"]) or int(video.duration.get_frames())
    cv = np.zeros(n)
    for i in range(n):
        try:
            m = stats.get_metrics(i, ["content_val"])
            cv[i] = m[0] if m and m[0] is not None else 0.0
        except Exception:
            cv[i] = 0.0
    cuts = sorted({int(s[0].frame_num) for s in scenes if int(s[0].frame_num) > 0})
    return cuts, cv, n


def thumbs(slug, n):
    th = np.zeros((n, THUMB[1], THUMB[0], 3), np.uint8)
    gr = np.zeros((n, GRAY[1], GRAY[0]), np.uint8)
    last = 0
    for i, f in iter_frames(slug):
        if i >= n:
            break
        th[i] = cv2.resize(f, THUMB, interpolation=cv2.INTER_AREA)
        gr[i] = cv2.cvtColor(cv2.resize(f, GRAY, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        last = i
    return th[: last + 1], gr[: last + 1]


def phase_shift(a, b):
    win = cv2.createHanningWindow(a.shape[::-1], cv2.CV_32F)
    (dx, dy), resp = cv2.phaseCorrelate(a.astype(np.float32), b.astype(np.float32), win)
    return dx, dy, resp


def lapvar(g):
    return float(cv2.Laplacian(g, cv2.CV_32F).var())


def zoom_rate(a, b):
    """Scale change a->b from dense flow divergence (1.0 = none)."""
    flow = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    h, w = a.shape
    ys, xs = np.mgrid[0:h, 0:w]
    xc, yc = xs - w / 2, ys - h / 2
    num = (flow[..., 0] * xc + flow[..., 1] * yc).sum()
    den = (xc ** 2 + yc ** 2).sum()
    return 1.0 + num / den


def soft_boundaries(cv, cuts, n):
    """Windows where content changes steadily over several frames without a single spike."""
    out = []
    csum = np.convolve(cv, np.ones(WINDOW), mode="same")
    i = 0
    while i < n:
        if csum[i] > WINDOW_THRESHOLD and cv[max(0, i - WINDOW):i + WINDOW].max() < CONTENT_THRESHOLD:
            j = i
            while j < n and csum[j] > WINDOW_THRESHOLD * 0.6:
                j += 1
            a = i
            while a > 0 and csum[a - 1] > WINDOW_THRESHOLD * 0.6:
                a -= 1
            mid = (a + j) // 2
            if all(abs(mid - c) > WINDOW for c in cuts):
                out.append((a, j, mid))
            i = j + 1
        else:
            i += 1
    return out


def side_motion(gr, b, n):
    """Max global shift (fraction of width) over frame pairs that do NOT straddle boundary b."""
    pairs = [(k - 1, k) for k in range(max(1, b - 3), b)] + [(k, k + 1) for k in range(b, min(n - 1, b + 2))]
    best = 0.0
    for a, c in pairs:
        dx, dy, r = phase_shift(gr[a], gr[c])
        if r > 0.05:
            best = max(best, float(np.hypot(dx, dy)) / GRAY[0])
    return best


def continuity(ga, gb):
    """Max normalised cross-correlation between two gray frames after best global alignment
    (translation via phase correlation, then affine ECC). ~1.0 = same shot continuing."""
    a = cv2.GaussianBlur(ga.astype(np.float32), (5, 5), 0)
    b = cv2.GaussianBlur(gb.astype(np.float32), (5, 5), 0)

    def ncc(x, y, m=None):
        if m is not None:
            x, y = x[m], y[m]
        x = x - x.mean(); y = y - y.mean()
        d = np.sqrt((x * x).sum() * (y * y).sum()) + 1e-6
        return float((x * y).sum() / d)

    best = ncc(a, b)
    dx, dy, _ = phase_shift(ga, gb)
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    h, w = a.shape
    bw = cv2.warpAffine(b, M, (w, h), flags=cv2.INTER_LINEAR, borderValue=-1)
    mask = bw >= 0
    if mask.mean() > 0.5:
        best = max(best, ncc(a, bw, mask))
    try:
        warp = np.eye(2, 3, dtype=np.float32)
        warp[0, 2], warp[1, 2] = dx, dy
        sa = cv2.resize(a, (160, 90)); sb = cv2.resize(b, (160, 90))
        warp[:, 2] /= 2
        cc, warp = cv2.findTransformECC(sa, sb, warp, cv2.MOTION_AFFINE,
                                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 1e-4), None, 5)
        best = max(best, float(cc))
    except cv2.error:
        pass
    return best


def classify(th, gr, b, span=None):
    """Classify transition at boundary b (first frame of new shot). span=(a, j) for soft windows.
    Returns (type or None, feats). None = soft window rejected (in-shot animation, not an edit)."""
    n = len(th)
    feats = {}
    if span:
        a0, j0 = max(0, span[0] - 1), min(n - 1, span[1] + 1)
    else:
        a0, j0 = max(0, b - 1), min(n - 1, b)
    A = th[a0].astype(np.float32)
    B = th[j0].astype(np.float32)
    diffAB = float(np.abs(A - B).mean())
    feats["diffAB"] = round(diffAB, 2)
    feats["side_shift_frac"] = round(side_motion(gr, b if not span else span[0], n), 3)
    lv = [lapvar(gr[k]) for k in range(max(0, b - 3), min(n, b + 3)) if gr[k].std() > 10]
    lv_ref = np.median([lapvar(gr[k]) for k in (max(0, b - 10), min(n - 1, b + 10))]) + 1e-6
    feats["blur_dip"] = round(float(min(lv) / lv_ref), 3) if lv else 1.0
    zb = span[0] if span else b
    zr = [zoom_rate(gr[k - 1], gr[k]) for k in range(max(1, zb - 4), zb)] if zb > 1 else [1.0]
    feats["zoom_rate_max"] = round(float(np.max(np.abs(np.array(zr) - 1.0))), 4)

    if span:
        blend_res, mix_res, alphas, fracs = [], [], [], []
        d = B - A
        dd = (d ** 2).sum() + 1e-3
        for k in range(span[0], min(n, span[1] + 1)):
            F = th[k].astype(np.float32)
            al = float(np.clip(((F - A) * d).sum() / dd, 0, 1))
            alphas.append(al)
            blend_res.append(np.abs(F - (A + al * d)).mean())
            ea = np.abs(F - A).mean(-1)
            eb = np.abs(F - B).mean(-1)
            mix_res.append(np.minimum(ea, eb).mean())
            fracs.append(float((eb < ea).mean()))
        mid = [a for a in alphas if 0.15 < a < 0.85]
        feats.update(blend_res=round(float(np.mean(blend_res)), 2), mix_res=round(float(np.mean(mix_res)), 2),
                     alphas=[round(a, 2) for a in alphas],
                     alpha_monotonic=bool(np.all(np.diff(alphas) >= -0.08)),
                     frac_monotonic=bool(np.all(np.diff(fracs) >= -0.05)),
                     frac_span=round(max(fracs) - min(fracs), 2) if fracs else 0)
        feats["continuity_AB"] = round(continuity(gr[a0], gr[j0]), 3)
        if diffAB < 10 or feats["continuity_AB"] > 0.8:
            return None, feats
        if feats["side_shift_frac"] > 0.05 and feats["blur_dip"] < 0.6:
            return "whip", feats
        if feats["zoom_rate_max"] > 0.05 and feats["blur_dip"] < 0.7:
            return "scale through", feats
        if feats["frac_monotonic"] and feats["frac_span"] > 0.6 and feats["mix_res"] < 0.5 * feats["blend_res"]:
            return "mask wipe", feats
        steps = np.diff(alphas) if len(alphas) > 1 else np.array([1.0])
        if (feats["alpha_monotonic"] and len(set(round(a, 1) for a in mid)) >= 2
                and steps.max() < 0.6 and feats["blend_res"] < 0.3 * diffAB):
            return "dissolve", feats
        return None, feats

    # single-frame boundary: reject detector hits inside a continuous shot (fast pans, flashes of light)
    feats["continuity"] = round(continuity(gr[max(0, b - 1)], gr[b]), 3)
    if feats["continuity"] > 0.85:
        # continuous frames, but a fast blurred slide/pan is still an edit-level whip in motion graphics
        if feats["side_shift_frac"] > 0.08 and feats["blur_dip"] < 0.3:
            return "whip", feats
        return None, feats
    if feats["side_shift_frac"] > 0.05 and feats["blur_dip"] < 0.6:
        return "whip", feats
    if feats["zoom_rate_max"] > 0.05 and feats["blur_dip"] < 0.7:
        return "scale through", feats
    # match cut: structure preserved across the hard cut
    ea = cv2.Canny(gr[max(0, b - 1)], 50, 150)
    eb = cv2.Canny(gr[b], 50, 150)
    ea = cv2.dilate(ea, np.ones((5, 5), np.uint8)) > 0
    eb = cv2.dilate(eb, np.ones((5, 5), np.uint8)) > 0
    inter, union = (ea & eb).sum(), (ea | eb).sum() + 1
    feats["edge_iou"] = round(float(inter / union), 3)
    ga, gb = gr[max(0, b - 1)].astype(np.float32), gr[b].astype(np.float32)
    ga, gb = cv2.resize(ga, (64, 36)), cv2.resize(gb, (64, 36))
    corr = np.corrcoef(ga.ravel() - ga.mean(), gb.ravel() - gb.mean())[0, 1]
    feats["layout_corr"] = round(float(np.nan_to_num(corr)), 3)
    if feats["edge_iou"] > 0.45 and feats["layout_corr"] > 0.6 and diffAB > 12 and feats["continuity"] < 0.75:
        return "match cut", feats
    return "cut", feats


def run(slug):
    cuts, cv, n = detect(slug)
    th, gr = thumbs(slug, n)
    n = len(th)
    cv = cv[:n]
    soft = soft_boundaries(cv, cuts, n)
    # snap each detector hit to the frame pair with the largest change within +-1 frame
    snapped = set()
    for c in cuts:
        cand = [k for k in (c - 1, c, c + 1) if 0 < k < n]
        k = max(cand, key=lambda k: float(np.abs(th[k].astype(np.int16) - th[k - 1]).mean()))
        snapped.add(k)
    bounds = [{"frame": c, "span": None} for c in sorted(snapped)]
    for a, j, mid in soft:
        bounds.append({"frame": mid, "span": (a, j)})
    bounds.sort(key=lambda x: x["frame"])

    shots, debug, kept = [], [], []
    types = ["start"]
    for b in bounds:
        t, f = classify(th, gr, b["frame"], b["span"])
        debug.append({"frame": b["frame"], "span": b["span"], "type": t or ("rejected_soft" if b["span"] else "rejected_continuous"), **f})
        if t is None:
            continue
        kept.append(b["frame"])
        types.append(t)
    starts = [0] + kept
    for k, s in enumerate(starts):
        e = (starts[k + 1] - 1) if k + 1 < len(starts) else n - 1
        shots.append({"index": k, "start_frame": s, "end_frame": e, "length_frames": e - s + 1,
                      "transition": types[k]})
    od = out_dir(slug)
    with open(od / "shots.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["index", "start_frame", "end_frame", "length_frames", "transition"])
        w.writeheader()
        w.writerows(shots)
    save_json(od / "shots_debug.json", {"params": {"content_threshold": CONTENT_THRESHOLD,
                                                    "min_scene_len": MIN_SCENE_LEN, "window": WINDOW,
                                                    "window_threshold": WINDOW_THRESHOLD},
                                         "n_frames": n, "boundaries": debug,
                                         "content_val": np.round(cv, 2)})
    lens = [s["length_frames"] for s in shots]
    from collections import Counter
    print(f"[{slug}] {len(shots)} shots, median {np.median(lens):.0f} fr, types {dict(Counter(types[1:]))}")


if __name__ == "__main__":
    for s in (sys.argv[1:] or slugs()):
        run(s)
